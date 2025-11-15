"""Cost estimation fallback."""

from __future__ import annotations

from typing import Any, Dict, List

DEFAULT_VIDEO_SCENE_COST = 0.3
DEFAULT_AUDIO_COST = 0.1


def estimate_cost(scenes: List[dict[str, Any]], include_audio: bool = True) -> Dict[str, Any]:
    total_video = len(scenes) * DEFAULT_VIDEO_SCENE_COST
    total_audio = DEFAULT_AUDIO_COST if include_audio else 0

    return {
        "total_usd": round(total_video + total_audio, 2),
        "breakdown": {
            "video_generation": round(total_video, 2),
            "audio_generation": round(total_audio, 2),
        },
        "assumptions": [
            f"{len(scenes)} scenes at ${DEFAULT_VIDEO_SCENE_COST:.2f} each",
            "Audio placeholder cost added" if include_audio else "Audio cost omitted",
        ],
        "confidence": "low",
    }

