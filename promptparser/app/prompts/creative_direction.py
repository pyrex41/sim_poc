"""Prompt templates for creative direction generation."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any


CREATIVE_DIRECTION_SYSTEM_PROMPT = dedent(
    """
    You are an award-winning ad creative director.
    Always respond with valid JSON matching the creative_direction schema:
    {
      "product": {"name": "", "category": "", "description": "", "price_tier": ""},
      "technical_specs": {"duration": 0, "aspect_ratio": "", "platform": "", "resolution": "", "fps": 30},
      "visual_direction": {
        "aesthetic": "",
        "style_source": "",
        "color_palette": [{"hex": "", "role": ""}],
        "lighting_style": "",
        "camera_style": "",
        "scene_types": []
      },
      "audio_direction": {
        "music_genre": "",
        "mood": [],
        "tempo": "",
        "intensity_curve": "",
        "instruments": []
      },
      "text_strategy": {
        "overlays": [],
        "font_family": "",
        "text_color": "",
        "outline_color": ""
      },
      "pacing": {
        "overall": "",
        "scene_duration_avg": 0,
        "transition_style": "",
        "cuts_per_minute": 0,
        "energy_curve": ""
      },
      "cta": {"text": "", "start_time": 0, "duration": 0, "style": "", "action": ""}
    }
    Include a "scenes" array (5-8 scenes) with id, purpose, timing, visual/audio/text details,
    and a "metadata" section containing warnings, defaults_used, and reasoning summaries.
    """
).strip()


def build_creative_direction_prompt(
    user_prompt: str,
    *,
    extracted_parameters: dict[str, Any],
    applied_defaults: dict[str, Any],
    visual_context: dict[str, Any] | None = None,
    previous_config: dict[str, Any] | None = None,
) -> str:
    """Return user prompt for LLM completion."""
    previous_section = ""
    if previous_config:
        previous_section = f"""
        Previous creative direction to update:
        {json.dumps(previous_config, indent=2)}
        """
    visual_section = ""
    if visual_context:
        visual_section = f"""
        Visual references summary:
        {json.dumps(visual_context, indent=2)}
        """

    return dedent(
        f"""
        User prompt:
        \"\"\"{user_prompt}\"\"\"

        Extracted parameters:
        {json.dumps(extracted_parameters, indent=2)}

        Defaults applied:
        {json.dumps(applied_defaults, indent=2)}

        {visual_section}
        {previous_section}

        Instructions:
        - Merge the extracted parameters with defaults intelligently.
        - Fill in missing details while staying faithful to user intent.
        - Produce coherent scene order with hooks, product showcase, benefits, CTA.
        - Include confidence rationale in metadata.confidence_breakdown.
        - Mention any assumptions in metadata.warnings or defaults_used.
        """
    ).strip()
