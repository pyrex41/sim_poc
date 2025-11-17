"""Common media helpers."""

from __future__ import annotations

import io
from typing import Tuple

from PIL import Image, ImageStat


def extract_dominant_color(image: Image.Image) -> str:
    image = image.convert("RGB")
    stat = ImageStat.Stat(image)
    r, g, b = stat.mean
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def resize_for_analysis(image: Image.Image, max_size: int = 1024) -> Image.Image:
    if max(image.size) > max_size:
        image = image.copy()
        image.thumbnail((max_size, max_size))
    return image


def load_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))

