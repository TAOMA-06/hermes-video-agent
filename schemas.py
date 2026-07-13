"""Schemas for the Hermes video rough-cut plugin."""

from __future__ import annotations

from typing import Any


def _tool(description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


TIMELINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source_asset_id", "title", "summary", "segments", "warnings"],
    "properties": {
        "source_asset_id": {
            "type": "string",
            "description": "The asset identifier supplied in the evidence.",
        },
        "title": {
            "type": "string",
            "description": "A short working title for the rough cut.",
        },
        "summary": {
            "type": "string",
            "description": "A concise editorial summary.",
        },
        "segments": {
            "type": "array",
            "minItems": 1,
            "maxItems": 48,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["in_seconds", "out_seconds", "label", "reason", "confidence"],
                "properties": {
                    "in_seconds": {"type": "number", "minimum": 0},
                    "out_seconds": {"type": "number", "minimum": 0},
                    "label": {"type": "string"},
                    "reason": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 16,
        },
    },
}


VIDEO_INSPECT_SCHEMA = _tool(
    "Read video metadata from a media file inside the configured video workspace. This is read-only.",
    {
        "source_path": {
            "type": "string",
            "description": "A workspace-relative path to the source media file.",
        },
    },
    ["source_path"],
)

VIDEO_CREATE_PROXY_SCHEMA = _tool(
    "Create a low-resolution local proxy for a previously inspected asset.",
    {
        "asset_id": {
            "type": "string",
            "description": "The identifier returned for the inspected asset.",
        },
        "max_height": {
            "type": "integer",
            "minimum": 144,
            "maximum": 1080,
            "description": "Maximum proxy height in pixels. Defaults to 720.",
        },
    },
    ["asset_id"],
)

VIDEO_EXTRACT_STORYBOARD_SCHEMA = _tool(
    "Create evenly spaced local image frames that represent a previously inspected video.",
    {
        "asset_id": {
            "type": "string",
            "description": "The identifier returned for the inspected asset.",
        },
        "frame_count": {
            "type": "integer",
            "minimum": 1,
            "maximum": 12,
            "description": "How many representative frames to create. Defaults to 8.",
        },
    },
    ["asset_id"],
)

VIDEO_TRANSCRIBE_SCHEMA = _tool(
    "Extract the audio track and transcribe it through Hermes's configured speech-to-text provider.",
    {
        "asset_id": {
            "type": "string",
            "description": "The identifier returned for the inspected asset.",
        },
    },
    ["asset_id"],
)

VIDEO_DRAFT_EDIT_SCHEMA = _tool(
    "Use the active Hermes multimodal model to turn local storyboard and transcript evidence into an editable rough-cut timeline.",
    {
        "asset_id": {
            "type": "string",
            "description": "The identifier returned for the inspected asset.",
        },
        "brief": {
            "type": "string",
            "description": "The intended audience, pacing, target duration, and editorial goal.",
        },
    },
    ["asset_id", "brief"],
)

VIDEO_VALIDATE_TIMELINE_SCHEMA = _tool(
    "Validate a rough-cut timeline against the source asset's duration and return a normalized timeline.",
    {
        "timeline": {
            "type": "object",
            "description": "The timeline object to validate.",
        },
    },
    ["timeline"],
)

VIDEO_RENDER_PREVIEW_SCHEMA = _tool(
    "Render a local MP4 preview from a validated rough-cut timeline.",
    {
        "asset_id": {
            "type": "string",
            "description": "The identifier returned for the inspected asset.",
        },
        "timeline": {
            "type": "object",
            "description": "The validated timeline object to render.",
        },
        "output_name": {
            "type": "string",
            "description": "Optional artifact file name ending in .mp4.",
        },
    },
    ["asset_id", "timeline"],
)

VIDEO_EXPORT_TIMELINE_SCHEMA = _tool(
    "Write a validated rough-cut timeline as JSON or a CMX-style EDL artifact.",
    {
        "timeline": {
            "type": "object",
            "description": "The validated timeline object to export.",
        },
        "format": {
            "type": "string",
            "enum": ["json", "edl"],
            "description": "The export format.",
        },
        "output_name": {
            "type": "string",
            "description": "Optional artifact file name with the selected extension.",
        },
    },
    ["timeline", "format"],
)
