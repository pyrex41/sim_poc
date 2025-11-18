"""
Video generation models and request/response schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import Field

from backend.core import BaseRequest, BaseResponse
from backend.core.types import VideoModel


class VideoRequest(BaseRequest):
    """Request model for video generation."""

    prompt: str = Field(..., min_length=1, max_length=5000, description="Text prompt for video generation")
    model: VideoModel = Field(default=VideoModel.MINIMAX, description="Video model to use")

    # Optional parameters (model-specific)
    first_frame_image: Optional[str] = Field(default=None, description="URL or path to first frame image")
    image: Optional[str] = Field(default=None, description="URL or path to image for image-to-video")
    duration: Optional[int] = Field(default=None, ge=1, le=10, description="Video duration in seconds")
    loop: Optional[bool] = Field(default=None, description="Whether video should loop")
    prompt_optimizer: Optional[bool] = Field(default=True, description="Use prompt optimization")

    # For stitching multiple images
    images: Optional[List[str]] = Field(default=None, description="List of image URLs for stitching")
    fps: Optional[int] = Field(default=None, ge=1, le=60, description="Frames per second")

    # Standard generation params
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class VideoResponse(BaseResponse):
    """Response model for video generation."""

    id: str
    created_at: datetime
    updated_at: datetime
    prompt: str
    model: str
    provider: str

    # Video URLs and metadata
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None  # seconds
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    file_size: Optional[int] = None  # bytes
    format: Optional[str] = None  # mp4, webm, etc.

    # Generation params
    seed: Optional[int] = None

    # Context
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    campaign_id: Optional[str] = None

    # Local storage
    local_path: Optional[str] = None


class VideoListItem(BaseResponse):
    """Simplified video item for list responses."""

    id: str
    created_at: datetime
    prompt: str
    model: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    status: str
