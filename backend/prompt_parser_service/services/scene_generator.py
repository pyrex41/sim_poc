"""Scene generator for creative direction."""

from __future__ import annotations

from typing import Any, List


def generate_scenes(creative_direction: dict[str, Any]) -> List[dict[str, Any]]:
    specs = creative_direction.get("technical_specs", {})
    total_duration = specs.get("duration", 30)
    scene_count = max(3, min(8, int(total_duration // 5) or 3))
    duration_per_scene = total_duration / scene_count

    scenes: List[dict[str, Any]] = []
    for idx in range(scene_count):
        scenes.append(
            {
                "id": f"scene_{idx + 1}",
                "scene_number": idx + 1,
                "purpose": _purpose_for_index(idx, scene_count),
                "duration": round(duration_per_scene, 2),
                "visual": {
                    "shot_type": "close_up" if idx == 0 else "medium",
                    "subject": "product",
                    "generation_prompt": f"Scene {idx + 1} for {creative_direction.get('product', {}).get('name', 'product')}",
                },
            }
        )
    return scenes


def _purpose_for_index(index: int, total: int) -> str:
    if index == 0:
        return "hook"
    if index == total - 1:
        return "cta"
    if index == 1:
        return "context"
    return "product_showcase"
