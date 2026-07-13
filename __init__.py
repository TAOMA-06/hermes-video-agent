"""Hermes plugin entry point for the local video rough-cut workflow."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .schemas import (
    VIDEO_CREATE_PROXY_SCHEMA,
    VIDEO_DRAFT_EDIT_SCHEMA,
    VIDEO_EXPORT_TIMELINE_SCHEMA,
    VIDEO_EXTRACT_STORYBOARD_SCHEMA,
    VIDEO_INSPECT_SCHEMA,
    VIDEO_RENDER_PREVIEW_SCHEMA,
    VIDEO_TRANSCRIBE_SCHEMA,
    VIDEO_VALIDATE_TIMELINE_SCHEMA,
)
from .workflow import VideoWorkflow, WorkflowError, check_media_requirements


logger = logging.getLogger(__name__)
_WORKFLOW = VideoWorkflow()

_LOCAL_WRITE_APPROVALS = {
    "video_create_proxy": "Create a local proxy-video artifact under the active Hermes profile.",
    "video_extract_storyboard": "Create local storyboard-frame artifacts under the active Hermes profile.",
    "video_transcribe": (
        "Extract audio locally and send it to Hermes's configured speech-to-text provider; "
        "the provider may be cloud-hosted."
    ),
    "video_draft_edit": (
        "Send local storyboard frames and transcript evidence to Hermes's configured "
        "multimodal model for editorial planning."
    ),
    "video_render_preview": "Render a new local MP4 preview under the active Hermes profile.",
    "video_export_timeline": "Write a local timeline export under the active Hermes profile.",
}


def _pre_tool_call(*, tool_name: str, **_: Any) -> dict[str, str] | None:
    """Route state-changing or cloud-bound operations through Hermes approval."""

    reason = _LOCAL_WRITE_APPROVALS.get(tool_name)
    if not reason:
        return None
    return {
        "action": "approve",
        "message": reason,
        "rule_key": f"hermes_video_agent:{tool_name}",
    }


def _handler(method_name: str) -> Callable[..., str]:
    def invoke(args: dict[str, Any], **_: Any) -> str:
        from tools.registry import tool_error, tool_result

        if not isinstance(args, dict):
            return tool_error("Tool arguments must be an object.", code="invalid_arguments")
        try:
            payload = getattr(_WORKFLOW, method_name)(args)
            return tool_result({"success": True, **payload})
        except WorkflowError as exc:
            return tool_error(str(exc), code=exc.code)
        except Exception:
            logger.exception("hermes_video_agent unexpected failure in %s", method_name)
            return tool_error("Video workflow failed unexpectedly.", code="internal_error")

    return invoke


_TOOLS = (
    ("video_inspect", VIDEO_INSPECT_SCHEMA, "inspect", "🔎", check_media_requirements),
    ("video_create_proxy", VIDEO_CREATE_PROXY_SCHEMA, "create_proxy", "🎞️", check_media_requirements),
    ("video_extract_storyboard", VIDEO_EXTRACT_STORYBOARD_SCHEMA, "extract_storyboard", "🖼️", check_media_requirements),
    ("video_transcribe", VIDEO_TRANSCRIBE_SCHEMA, "transcribe", "📝", check_media_requirements),
    ("video_draft_edit", VIDEO_DRAFT_EDIT_SCHEMA, "draft_edit", "✂️", None),
    ("video_validate_timeline", VIDEO_VALIDATE_TIMELINE_SCHEMA, "validate_timeline", "✅", None),
    ("video_render_preview", VIDEO_RENDER_PREVIEW_SCHEMA, "render_preview", "🎬", check_media_requirements),
    ("video_export_timeline", VIDEO_EXPORT_TIMELINE_SCHEMA, "export_timeline", "📦", None),
)


def register(ctx: Any) -> None:
    """Register a fixed tool surface once at Hermes startup."""

    _WORKFLOW.llm = ctx.llm
    for name, schema, method, emoji, check_fn in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="video_rough_cut",
            schema=schema,
            handler=_handler(method),
            check_fn=check_fn,
            emoji=emoji,
        )
    ctx.register_hook("pre_tool_call", _pre_tool_call)
