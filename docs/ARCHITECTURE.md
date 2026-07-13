# Architecture

Hermes Video Agent is deliberately a thin plugin around Hermes-owned model, approval, configuration, and transcription services.

## Workflow

~~~text
source video
    |
    v
inspect -> asset catalog
    |
    +--> proxy and storyboard frames
    |
    +--> optional audio extraction and Hermes STT transcript
    |
    v
Hermes active multimodal model
    |
    v
editable timeline -> validation -> approved preview and JSON/EDL export
~~~

## Boundaries

The plugin accepts media only below the configured workspace root. It resolves every path before checking containment so that symlinks cannot escape the workspace. All ffmpeg and ffprobe calls use argument arrays, not shell interpolation.

The planner receives selected storyboard frames and optional transcript text. It does not receive the source video bytes. Hermes owns provider authentication and model calls through its LLM and STT facades; the plugin does not hold provider secrets.

## Persistence

Source assets are indexed in the active Hermes profile's video-agent data directory. Proxies, frame evidence, transcripts, edit plans, previews, and exports are created there as well. The source file remains unchanged.

## Approval model

Inspection and timeline validation are read-only. Operations that generate files or may transfer evidence to a cloud provider return through Hermes's pre-tool-call approval hook. The user retains control over each side effect.
