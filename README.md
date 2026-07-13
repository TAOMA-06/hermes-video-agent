# Hermes Video Agent

[![CI](https://github.com/TAOMA-06/hermes-video-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/TAOMA-06/hermes-video-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hermes Video Agent is a standalone [Hermes Agent](https://github.com/NousResearch/hermes-agent) user plugin for evidence-based local video rough cuts. It turns a natural-language edit request into an editable timeline and an approved local preview:

1. inspect a source video;
2. create a proxy and storyboard evidence;
3. transcribe its audio through Hermes's configured STT provider;
4. ask Hermes's active multimodal model, such as Grok 4.5, to draft a timeline;
5. validate, render, and export the result.

This is a community plugin, not an official Hermes or xAI project.

## What it does

- Keeps source media local and never overwrites it.
- Sends the planner only locally generated storyboard frames and optional transcript text, never the raw video file.
- Uses Hermes-owned LLM and STT integrations, so the plugin does not read, store, or configure model-provider credentials.
- Requires Hermes's existing approval flow before operations that write files or send frames/audio to a cloud provider.
- Produces an editable JSON or EDL timeline plus an MP4 preview.

It is intentionally a single-source rough-cut workflow, not a full nonlinear editor or an automatic publishing tool.

## Requirements

- A working Hermes installation with user plugins enabled.
- ffmpeg and ffprobe on PATH.
- An absolute workspace directory containing the videos you want to process.
- A configured Hermes multimodal model. Grok 4.5 is a supported deployment choice because planning goes through Hermes's active model facade.
- Optional: an enabled Hermes STT provider. xAI/Grok STT can be selected in standard Hermes configuration.

## Install

Clone this repository, then copy the plugin runtime files into your Hermes user-plugin directory:

~~~sh
git clone https://github.com/TAOMA-06/hermes-video-agent.git
cd hermes-video-agent

if [ -z "$HERMES_HOME" ]; then
  HERMES_HOME="$HOME/.hermes"
fi

mkdir -p "$HERMES_HOME/plugins/hermes_video_agent"
cp plugin.yaml __init__.py schemas.py workflow.py config.example.yaml \
  "$HERMES_HOME/plugins/hermes_video_agent/"
~~~

Merge the relevant block from [config.example.yaml](config.example.yaml) into the active Hermes profile configuration. At minimum, set an absolute <code>workspace_root</code>. Keep keys and tokens in Hermes's normal authentication flow, never in this plugin configuration.

Restart Hermes, then confirm discovery with:

~~~sh
hermes plugins list
~~~

## Example request

After Hermes loads the plugin, ask for a rough cut in normal language:

> From interview.mp4, make a fast-paced 45-second Chinese short that keeps the central conclusion and removes pauses and repetition.

The agent can use these tools:

| Tool | Purpose |
| --- | --- |
| <code>video_inspect</code> | Read media metadata and create a local asset ID. |
| <code>video_create_proxy</code> | Create a lower-resolution working proxy. |
| <code>video_extract_storyboard</code> | Generate local key-frame evidence. |
| <code>video_transcribe</code> | Extract audio and use Hermes's configured STT route. |
| <code>video_draft_edit</code> | Ask the active Hermes model for a structured rough-cut timeline. |
| <code>video_validate_timeline</code> | Check ordering, overlap, and source-duration bounds. |
| <code>video_render_preview</code> | Render an approved local MP4 preview. |
| <code>video_export_timeline</code> | Export JSON or EDL for continued editing. |

## Security and data handling

- Every supplied path must resolve within <code>workspace_root</code>, including after symlink resolution.
- ffmpeg and ffprobe are invoked with argument arrays; the plugin does not build shell command strings.
- Proposed clips must be in source bounds and may not overlap.
- The active model receives only selected evidence. Audio transcription follows the configured Hermes STT provider's data path.
- Generated proxies, storyboards, transcripts, plans, previews, and exports are stored under the active Hermes profile's <code>video-agent</code> directory.

Please read [SECURITY.md](SECURITY.md) before reporting a vulnerability.

## Development and verification

The integration test installs the plugin into a temporary Hermes home and replaces ffmpeg, STT, and the LLM with fakes. It does not read a developer's real Hermes profile, media, or credentials.

~~~sh
git clone https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent
cd /tmp/hermes-agent
scripts/run_tests.sh /absolute/path/to/hermes-video-agent/tests/test_hermes_video_agent.py
~~~

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the workflow design.

## 中文简介

这是一个 Hermes 用户插件，用于把“分析素材、抽取关键帧、转写、让 Grok 4.5 规划粗剪、导出可编辑时间线和预览”连成可审批工作流。它不修改 Hermes 核心、不覆盖原视频，也不会把原始视频传给规划模型；模型仅接收本地生成的关键帧和可选转写文本。安装时请将 [config.example.yaml](config.example.yaml) 合并到 Hermes 的活动 profile，并设置素材工作目录。

## License

MIT. See [LICENSE](LICENSE).
