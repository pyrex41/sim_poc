"""Video analysis models for video-to-text generation."""
from typing import Optional
from pydantic import Field, BaseModel
from backend.core.models import BaseRequest, BaseResponse


class VideoAnalysisRequest(BaseRequest):
    """Request model for video analysis."""

    video: str = Field(..., description="URL to the video file")
    prompt: Optional[str] = Field(
        default="Describe this video in detail",
        description="Question or instruction for the model"
    )
    model: str = Field(default="qwen2-vl", description="Video analysis model to use")

    # Common optional parameters
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens in response")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")
    top_p: Optional[float] = Field(default=None, description="Nucleus sampling parameter")

    # Caption overlay parameters (for caption models)
    font: Optional[str] = Field(default=None, description="Font for captions")
    font_size: Optional[int] = Field(default=None, description="Font size for captions")
    font_color: Optional[str] = Field(default=None, description="Font color for captions")
    stroke_width: Optional[int] = Field(default=None, description="Stroke width for captions")


class VideoAnalysisResponse(BaseResponse):
    """Response model for video analysis."""

    text: Optional[str] = Field(None, description="Generated text description/caption")
    video_url: Optional[str] = Field(None, description="Video URL (for caption overlay models)")
