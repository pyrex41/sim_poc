"""
Utilities engine models for image/video processing tools.
"""
from typing import Optional
from datetime import datetime
from pydantic import Field

from backend.core import BaseRequest, BaseResponse


class UtilityRequest(BaseRequest):
    """Request model for utility processing."""

    # Tool selection
    tool: str = Field(..., description="Utility tool to use (upscale, remove-background, restore-face, etc.)")

    # Input content
    image: Optional[str] = Field(default=None, description="URL or path to input image")
    video: Optional[str] = Field(default=None, description="URL or path to input video")

    # Upscaler parameters
    scale: Optional[int] = Field(default=2, ge=1, le=4, description="Upscale factor")
    dynamic: Optional[int] = Field(default=6, ge=0, le=10, description="Dynamic range (clarity upscaler)")
    sharpen: Optional[float] = Field(default=0, ge=0, le=10, description="Sharpening amount")
    creativity: Optional[float] = Field(default=0.35, ge=0, le=1, description="AI creativity level")
    resemblance: Optional[float] = Field(default=0.6, ge=0, le=1, description="Resemblance to original")
    sd_model: Optional[str] = Field(default=None, description="SD model for upscaling")

    # Background removal parameters
    model: Optional[str] = Field(default="u2net", description="Model for background removal")
    return_mask: Optional[bool] = Field(default=False, description="Return mask instead of image")

    # Face restoration parameters
    version: Optional[str] = Field(default="v1.4", description="GFPGAN version")

    # Standard generation params
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class UtilityResponse(BaseResponse):
    """Response model for utility processing."""

    id: str
    created_at: datetime
    updated_at: datetime
    tool: str
    provider: str

    # Input/output URLs
    input_url: Optional[str] = None
    output_url: Optional[str] = None

    # Metadata
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None

    # Processing params
    parameters: Optional[dict] = None

    # Context
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    campaign_id: Optional[str] = None

    # Local storage
    local_path: Optional[str] = None


class UtilityListItem(BaseResponse):
    """Simplified utility item for list responses."""

    id: str
    created_at: datetime
    tool: str
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    status: str
