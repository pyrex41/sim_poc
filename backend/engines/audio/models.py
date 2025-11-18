"""
Audio generation models and request/response schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import Field

from backend.core import BaseRequest, BaseResponse
from backend.core.types import AudioModel


class AudioRequest(BaseRequest):
    """Request model for audio/music generation."""

    prompt: str = Field(..., min_length=1, max_length=5000, description="Text prompt for audio generation")
    model: AudioModel = Field(default=AudioModel.MUSICGEN, description="Audio model to use")

    # Model-specific parameters
    model_version: Optional[str] = Field(default=None, description="Model version (for MusicGen: melody, small, medium, large)")
    duration: Optional[int] = Field(default=8, ge=1, le=30, description="Duration in seconds")
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0, description="Sampling temperature")
    top_k: Optional[int] = Field(default=250, ge=0, description="Top-k sampling")
    top_p: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Top-p sampling")

    # Bark-specific parameters
    text_temp: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Text generation temperature (Bark)")
    waveform_temp: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Waveform generation temperature (Bark)")

    # Standard generation params
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class AudioResponse(BaseResponse):
    """Response model for audio generation."""

    id: str
    created_at: datetime
    updated_at: datetime
    prompt: str
    model: str
    provider: str

    # Audio URLs and metadata
    url: Optional[str] = None
    duration: Optional[float] = None  # seconds
    file_size: Optional[int] = None  # bytes
    format: Optional[str] = None  # mp3, wav, etc.
    sample_rate: Optional[int] = None  # Hz
    channels: Optional[int] = None  # 1=mono, 2=stereo

    # Generation params
    seed: Optional[int] = None
    temperature: Optional[float] = None

    # Context
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    campaign_id: Optional[str] = None

    # Local storage
    local_path: Optional[str] = None


class AudioListItem(BaseResponse):
    """Simplified audio item for list responses."""

    id: str
    created_at: datetime
    prompt: str
    model: str
    url: Optional[str] = None
    duration: Optional[float] = None
    status: str
