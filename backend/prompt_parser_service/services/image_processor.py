"""Image processing for style extraction."""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, Optional

import httpx
from PIL import Image

from .media_utils import extract_dominant_color, resize_for_analysis


async def _load_image_bytes(image_url: Optional[str], image_base64: Optional[str]) -> bytes:
    if image_base64:
        return base64.b64decode(image_base64)
    if image_url:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            return response.content
    raise ValueError("No image data provided")


async def process_image_primary(
    *,
    image_url: Optional[str] = None,
    image_base64: Optional[str] = None,
    text_context: Optional[str] = None,
) -> Dict[str, Any]:
    image_bytes = await _load_image_bytes(image_url, image_base64)
    image = Image.open(io.BytesIO(image_bytes))
    image = resize_for_analysis(image)

    dominant = extract_dominant_color(image)
    width, height = image.size
    mode = "RGB" if image.mode == "RGB" else image.mode

    analysis = {
        "dominant_colors": [dominant],
        "dimensions": {"width": width, "height": height},
        "mode": mode,
        "text_context": text_context,
    }

    return {
        "source": "image_url" if image_url else "image_base64",
        "reference": image_url or "inline_base64_image",
        "analysis": analysis,
    }
