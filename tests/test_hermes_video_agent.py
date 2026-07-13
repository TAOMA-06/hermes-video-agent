"""Hermes sandbox integration test for the standalone video rough-cut plugin."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

from hermes_cli.plugins import PluginManager
from tools.registry import registry


PLUGIN_SOURCE = Path(__file__).resolve().parents[1]


class FakeRunner:
    """Pretend ffmpeg/ffprobe runner that never touches a real media binary."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def run(self, args: list[str], *, timeout: int) -> SimpleNamespace:
        self.commands.append(list(args))
        if args[0] == "ffprobe":
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "format": {"duration": "12.0"},
                        "streams": [
                            {
                                "codec_type": "video",
                                "codec_name": "h264",
                                "width": 1920,
                                "height": 1080,
                                "avg_frame_rate": "30/1",
                            },
                            {"codec_type": "audio", "codec_name": "aac"},
                        ],
                    }
                ),
                stderr="",
            )

        output = Path(args[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() in {".jpg", ".jpeg"}:
            output.write_bytes(b"fake-jpeg-frame")
        elif output.suffix.lower() == ".wav":
            output.write_bytes(b"fake-wav-audio")
        else:
            output.write_bytes(b"fake-video-output")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


class FakeLlm:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete_structured(self, **kwargs):
        self.calls.append(kwargs)
        evidence = json.loads(kwargs["input"][0]["text"])
        return SimpleNamespace(
            parsed={
                "source_asset_id": evidence["asset"]["asset_id"],
                "title": "Short interview cut",
                "summary": "A concise edit built from the supplied evidence.",
                "segments": [
                    {
                        "in_seconds": 1.0,
                        "out_seconds": 4.0,
                        "label": "Hook",
                        "reason": "The opening answer establishes the thesis.",
                        "confidence": 0.94,
                    },
                    {
                        "in_seconds": 6.0,
                        "out_seconds": 10.0,
                        "label": "Conclusion",
                        "reason": "The final statement closes the argument.",
                        "confidence": 0.89,
                    },
                ],
                "warnings": ["Frame evidence cannot prove every spoken transition."],
            },
            provider="xai",
            model="grok-4.5",
            usage=SimpleNamespace(total_tokens=321),
        )


def _install_plugin(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    hermes_home = tmp_path / "hermes-home"
    media_root = tmp_path / "media"
    media_root.mkdir()
    (media_root / "interview.mp4").write_bytes(b"not-a-real-video")
    (tmp_path / "outside.mp4").write_bytes(b"outside-workspace")

    target = hermes_home / "plugins" / "hermes_video_agent"
    shutil.copytree(
        PLUGIN_SOURCE,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    config = {
        "plugins": {
            "enabled": ["hermes_video_agent"],
            "entries": {
                "hermes_video_agent": {
                    "workspace_root": str(media_root),
                    "max_storyboard_frames": 4,
                    "planner_timeout_seconds": 60,
                    "planner_max_tokens": 1000,
                }
            },
        }
    }
    (hermes_home / "config.yaml").parent.mkdir(parents=True, exist_ok=True)
    (hermes_home / "config.yaml").write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home, media_root


def _call(name: str, args: dict) -> dict:
    payload = json.loads(registry.dispatch(name, args))
    assert "error" not in payload, payload
    assert payload["success"] is True
    return payload


def test_standalone_plugin_loads_and_runs_the_safe_rough_cut_workflow(tmp_path, monkeypatch):
    hermes_home, _ = _install_plugin(tmp_path, monkeypatch)

    manager = PluginManager()
    manager.discover_and_load()
    loaded = manager._plugins["hermes_video_agent"]
    assert loaded.enabled is True
    assert {
        "video_inspect",
        "video_create_proxy",
        "video_extract_storyboard",
        "video_transcribe",
        "video_draft_edit",
        "video_validate_timeline",
        "video_render_preview",
        "video_export_timeline",
    }.issubset(set(loaded.tools_registered))
    assert "pre_tool_call" in loaded.hooks_registered

    plugin_module = loaded.module
    assert plugin_module is not None
    workflow_module = sys.modules[f"{plugin_module.__name__}.workflow"]
    monkeypatch.setattr(workflow_module.shutil, "which", lambda _: "/sandbox/bin/media")
    fake_runner = FakeRunner()
    fake_llm = FakeLlm()
    plugin_module._WORKFLOW.runner = fake_runner
    plugin_module._WORKFLOW.transcriber = lambda _: {
        "success": True,
        "provider": "xai",
        "transcript": "这是一个用于隔离测试的转写文本。",
    }
    plugin_module._WORKFLOW.llm = fake_llm

    definitions = registry.get_definitions({"video_inspect", "video_render_preview"})
    assert {item["function"]["name"] for item in definitions} == {
        "video_inspect",
        "video_render_preview",
    }

    inspected = _call("video_inspect", {"source_path": "interview.mp4"})
    asset_id = inspected["asset"]["asset_id"]
    assert inspected["asset"]["duration_seconds"] == 12.0

    proxy = _call("video_create_proxy", {"asset_id": asset_id, "max_height": 720})
    assert Path(proxy["proxy_path"]).is_file()

    storyboard = _call("video_extract_storyboard", {"asset_id": asset_id, "frame_count": 3})
    assert len(storyboard["frames"]) == 3

    transcript = _call("video_transcribe", {"asset_id": asset_id})
    assert transcript["provider"] == "xai"

    drafted = _call(
        "video_draft_edit",
        {"asset_id": asset_id, "brief": "做一个 8 秒的中文访谈精华短片。"},
    )
    timeline = drafted["timeline"]
    assert drafted["planner"] == {
        "provider": "xai",
        "model": "grok-4.5",
        "total_tokens": 321,
    }
    assert len(fake_llm.calls) == 1
    assert any(item["type"] == "image" for item in fake_llm.calls[0]["input"])
    assert not any(item.get("type") == "video_url" for item in fake_llm.calls[0]["input"])

    validated = _call("video_validate_timeline", {"timeline": timeline})
    assert validated["valid"] is True

    preview = _call(
        "video_render_preview",
        {"asset_id": asset_id, "timeline": validated["timeline"]},
    )
    assert Path(preview["preview_path"]).is_file()
    assert Path(preview["preview_path"]).is_relative_to(hermes_home)

    exported_json = _call(
        "video_export_timeline",
        {"timeline": validated["timeline"], "format": "json"},
    )
    exported_edl = _call(
        "video_export_timeline",
        {"timeline": validated["timeline"], "format": "edl"},
    )
    assert Path(exported_json["timeline_path"]).is_file()
    assert "FCM: NON-DROP FRAME" in Path(exported_edl["timeline_path"]).read_text(encoding="utf-8")

    rejected = json.loads(registry.dispatch("video_inspect", {"source_path": "../outside.mp4"}))
    assert rejected["code"] == "source_outside_workspace"

    approval = manager.invoke_hook("pre_tool_call", tool_name="video_draft_edit", args={})
    assert any(item.get("action") == "approve" for item in approval)
    assert manager.invoke_hook("pre_tool_call", tool_name="video_inspect", args={}) == []
