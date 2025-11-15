"""Validation and confidence scoring."""

from __future__ import annotations

from typing import Any, Dict, List


def validate_scenes(creative_direction: dict[str, Any], scenes: List[dict[str, Any]]) -> List[str]:
    warnings: List[str] = []
    target_duration = creative_direction.get("technical_specs", {}).get("duration", 30)
    total_duration = sum(scene.get("duration", 0) for scene in scenes)
    if abs(total_duration - target_duration) > 2:
        warnings.append("Scene timing mismatch vs technical specs duration.")

    for scene in scenes:
        if scene.get("duration", 0) < 2 and scene.get("purpose") == "cta":
            warnings.append(f"CTA scene {scene['scene_number']} might be too short.")
    return warnings


def calculate_confidence(parsed_prompt: dict[str, Any], scenes: List[dict[str, Any]], warnings: List[str]) -> Dict[str, float]:
    product_confidence = 0.7 if parsed_prompt.get("product") else 0.4
    style_confidence = 0.9 if parsed_prompt.get("aesthetic_keywords") else 0.6
    feasibility = max(0.5, 1 - len(warnings) * 0.1)
    overall = round((product_confidence * 0.3) + (style_confidence * 0.4) + (feasibility * 0.3), 2)
    return {
        "confidence_score": overall,
        "confidence_breakdown": {
            "product_understanding": round(product_confidence, 2),
            "style_clarity": round(style_confidence, 2),
            "technical_feasibility": round(feasibility, 2),
        },
    }
