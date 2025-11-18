"""
Image generation request and response models.
"""
from typing import Optional, List
from pydantic import Field, field_validator

from backend.core import (
    BaseRequest,
    BaseResponse,
    ImageModel,
    ImageSize,
    AspectRatio,
    ImageProvider,
)


class ImageRequest(BaseRequest):
    """Request for image generation."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text prompt describing the image to generate"
    )

    model: ImageModel = Field(
        default=ImageModel.FLUX,
        description="Image generation model to use"
    )

    size: Optional[ImageSize] = Field(
        default=ImageSize.SQUARE_1024,
        description="Output image size"
    )

    aspect_ratio: Optional[AspectRatio] = Field(
        None,
        description="Aspect ratio (alternative to size)"
    )

    provider: ImageProvider = Field(
        default=ImageProvider.REPLICATE,
        description="Provider to use for generation"
    )

    negative_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Negative prompt (things to avoid)"
    )

    num_outputs: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of images to generate"
    )

    guidance_scale: float = Field(
        default=7.5,
        ge=1.0,
        le=20.0,
        description="How strictly to follow the prompt"
    )

    num_inference_steps: int = Field(
        default=50,
        ge=1,
        le=150,
        description="Number of denoising steps"
    )

    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility"
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt is not empty after stripping."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class ImageResponse(BaseResponse):
    """Response for generated image."""

    prompt: str = Field(..., description="The prompt used")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider used")

    # Image data
    url: str = Field(..., description="URL to access the generated image")
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: str = Field(default="png", description="Image format")

    # Generation parameters
    seed: Optional[int] = Field(None, description="Seed used for generation")
    num_inference_steps: int = Field(..., description="Number of inference steps")
    guidance_scale: float = Field(..., description="Guidance scale used")

    # Context
    user_id: str = Field(..., description="User who created this")
    client_id: Optional[str] = Field(None, description="Client ID if applicable")
    campaign_id: Optional[str] = Field(None, description="Campaign ID if applicable")

    # Storage
    local_path: Optional[str] = Field(None, description="Local file path if downloaded")


class ImageListItem(BaseResponse):
    """Lightweight image item for list responses."""

    prompt: str = Field(..., description="The prompt used")
    model: str = Field(..., description="Model used")
    url: str = Field(..., description="Image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    user_id: str = Field(..., description="Owner user ID")
    client_id: Optional[str] = Field(None, description="Client ID")
    campaign_id: Optional[str] = Field(None, description="Campaign ID")
