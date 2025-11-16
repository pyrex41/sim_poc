"""Determine primary input modality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..models.request import PromptInput
from .image_processor import process_image_primary
from .video_processor import process_video_input


@dataclass
class InputAnalysis:
    style_source: str
    reference_summary: Dict[str, Any]
    extracted_references: Dict[str, Any]


async def analyze_inputs(prompt: PromptInput) -> Optional[InputAnalysis]:
    if prompt.video_url or prompt.video_base64:
        try:
            video_data = await process_video_input(
                video_url=prompt.video_url,
                video_base64=prompt.video_base64,
            )
            summary = {
                "primary_reference": video_data["reference"],
                "frames": video_data["frames"],
            }
            return InputAnalysis(
                style_source="video",
                reference_summary=summary,
                extracted_references={"videos": [video_data]},
            )
        except Exception:
            pass

    if prompt.image_url or prompt.image_base64:
        try:
            image_data = await process_image_primary(
                image_url=prompt.image_url,
                image_base64=prompt.image_base64,
                text_context=prompt.text,
            )
            summary = {
                "primary_reference": image_data["reference"],
                "analysis": image_data["analysis"],
            }
            return InputAnalysis(
                style_source="image",
                reference_summary=summary,
                extracted_references={"images": [image_data]},
            )
        except Exception:
            pass

    return None
