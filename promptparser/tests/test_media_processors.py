import base64
import io

import pytest
from PIL import Image

from app.services.image_processor import process_image_primary


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _small_png_base64(color) -> str:
    image = Image.new("RGB", (2, 2), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


SAMPLE_IMAGE_B64 = _small_png_base64((255, 0, 0))


@pytest.mark.anyio
async def test_process_image_primary_base64():
    result = await process_image_primary(image_base64=SAMPLE_IMAGE_B64, text_context="red style")
    assert result["analysis"]["dominant_colors"][0].startswith("#")
    assert result["analysis"]["text_context"] == "red style"

