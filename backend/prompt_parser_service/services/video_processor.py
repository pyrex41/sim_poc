"""Video frame extraction for style guidance."""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, Optional
import tempfile
import os

import cv2
import httpx

from backend.prompt_parser_service.services.media_utils import extract_dominant_color
from PIL import Image


async def _load_video_bytes(video_url: Optional[str], video_base64: Optional[str]) -> bytes:
    if video_base64:
        return base64.b64decode(video_base64)
    if video_url:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            return response.content
    raise ValueError("No video data provided")


def _frame_to_image(frame) -> Image.Image:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


async def process_video_input(
    *,
    video_url: Optional[str] = None,
    video_base64: Optional[str] = None,
) -> Dict[str, Any]:
    video_bytes = await _load_video_bytes(video_url, video_base64)
    tmp_path = None
    video = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp.flush()
            tmp_path = tmp.name
        video = cv2.VideoCapture(tmp_path)
        if not video.isOpened():
            raise ValueError("Unable to read video data")

        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_extract = [0, max(total_frames - 1, 0)]
        extracted = []

        for idx, frame_index in enumerate(frames_to_extract):
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = video.read()
            if not ret:
                continue
            image = _frame_to_image(frame)
            dominant = extract_dominant_color(image)
            extracted.append(
                {
                    "source": "video_frame",
                    "frame_type": "first" if idx == 0 else "last",
                    "analysis": {
                        "dominant_color": dominant,
                    },
                }
            )
    finally:
        if video is not None:
            video.release()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "source": "video_url" if video_url else "video_base64",
        "reference": video_url or "inline_video",
        "frames": extracted,
        "video_metadata": {
            "total_frames": total_frames,
        },
    }
