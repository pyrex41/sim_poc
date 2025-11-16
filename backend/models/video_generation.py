"""
Video Generation API Models.

This module contains Pydantic models for the v2 video generation workflow,
including request/response models, status tracking, and progress monitoring.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class VideoStatus(str, Enum):
    """
    Video generation workflow status.

    Tracks the current state of a video generation job through its lifecycle.
    """
    PENDING = "pending"
    PARSING = "parsing"
    GENERATING_STORYBOARD = "generating_storyboard"
    STORYBOARD_READY = "storyboard_ready"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Scene(BaseModel):
    """
    Individual scene definition within a video.

    Represents a single scene with its narrative description and visual prompt
    for image generation.
    """
    scene_number: int = Field(..., ge=1, description="Sequential scene number starting from 1")
    description: str = Field(..., min_length=1, max_length=1000, description="Narrative description of the scene")
    duration: float = Field(..., gt=0, le=60, description="Scene duration in seconds")
    image_prompt: str = Field(..., min_length=1, max_length=2000, description="Detailed prompt for image generation")

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: float) -> float:
        """Ensure duration is positive and reasonable."""
        if v <= 0:
            raise ValueError("Scene duration must be greater than 0 seconds")
        if v > 60:
            raise ValueError("Scene duration cannot exceed 60 seconds")
        return round(v, 2)  # Round to 2 decimal places


class StoryboardEntry(BaseModel):
    """
    Storyboard entry tracking scene generation progress.

    Links a scene definition with its generated image and tracks the
    generation status and any errors encountered.
    """
    scene: Scene = Field(..., description="Scene definition")
    image_url: Optional[str] = Field(None, description="URL to generated image (if completed)")
    generation_status: str = Field(
        default="pending",
        pattern="^(pending|generating|completed|failed)$",
        description="Current status of image generation"
    )
    error: Optional[str] = Field(None, max_length=500, description="Error message if generation failed")

    @field_validator('generation_status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is one of the allowed values."""
        allowed_statuses = {"pending", "generating", "completed", "failed"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class GenerationRequest(BaseModel):
    """
    Video generation request payload.

    Contains all parameters needed to initiate a video generation job,
    including the concept prompt, duration, style preferences, and optional
    client-specific branding guidelines.
    """
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Video concept description or narrative"
    )
    duration: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Total video duration in seconds (5-300s)"
    )
    style: Optional[str] = Field(
        None,
        max_length=100,
        description="Visual style (e.g., 'cinematic', 'cartoon', 'documentary')"
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        pattern="^(16:9|9:16|1:1|4:3)$",
        description="Video aspect ratio"
    )
    client_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Client identifier for multi-tenant support"
    )
    brand_guidelines: Optional[dict[str, Any]] = Field(
        None,
        description="Client-specific brand guidelines and style preferences"
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt has meaningful content."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Prompt must be at least 10 characters long")
        return v

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Ensure duration is within acceptable range."""
        if v < 5:
            raise ValueError("Video duration must be at least 5 seconds")
        if v > 300:
            raise ValueError("Video duration cannot exceed 300 seconds (5 minutes)")
        return v

    @field_validator('aspect_ratio')
    @classmethod
    def validate_aspect_ratio(cls, v: Optional[str]) -> str:
        """Validate and normalize aspect ratio."""
        if v is None:
            return "16:9"

        allowed_ratios = {"16:9", "9:16", "1:1", "4:3"}
        if v not in allowed_ratios:
            raise ValueError(f"Aspect ratio must be one of: {', '.join(allowed_ratios)}")
        return v


class VideoProgress(BaseModel):
    """
    Real-time progress tracking for video generation.

    Provides detailed information about the current state of the generation
    process, including scene completion counts and time estimates.
    """
    current_stage: VideoStatus = Field(..., description="Current workflow stage")
    scenes_total: int = Field(default=0, ge=0, description="Total number of scenes in the video")
    scenes_completed: int = Field(default=0, ge=0, description="Number of scenes completed")
    current_scene: Optional[int] = Field(None, ge=1, description="Currently processing scene number")
    estimated_completion_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated seconds until completion"
    )
    message: Optional[str] = Field(
        None,
        max_length=200,
        description="Human-readable progress message"
    )

    @field_validator('scenes_completed')
    @classmethod
    def validate_scenes_completed(cls, v: int, info) -> int:
        """Ensure scenes_completed doesn't exceed scenes_total."""
        # Note: We can't access scenes_total here in field_validator
        # This will be validated in model_validator if needed
        if v < 0:
            raise ValueError("scenes_completed cannot be negative")
        return v


class JobResponse(BaseModel):
    """
    Complete video generation job response.

    Comprehensive response model containing job metadata, status, progress,
    storyboard, final video URL, and cost information.
    """
    job_id: int = Field(..., ge=1, description="Unique job identifier")
    status: VideoStatus = Field(..., description="Current job status")
    progress: VideoProgress = Field(..., description="Detailed progress information")
    storyboard: Optional[list[StoryboardEntry]] = Field(
        None,
        description="Scene-by-scene storyboard with generated images"
    )
    video_url: Optional[str] = Field(
        None,
        description="URL to final rendered video (when completed)"
    )
    estimated_cost: float = Field(
        ...,
        ge=0,
        description="Estimated cost in USD for the generation job"
    )
    actual_cost: Optional[float] = Field(
        None,
        ge=0,
        description="Actual cost in USD (populated after completion)"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    approved: bool = Field(default=False, description="Whether the storyboard has been approved")
    error_message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Error details if job failed"
    )

    @field_validator('estimated_cost', 'actual_cost')
    @classmethod
    def validate_cost(cls, v: Optional[float]) -> Optional[float]:
        """Ensure costs are non-negative and reasonable."""
        if v is not None:
            if v < 0:
                raise ValueError("Cost cannot be negative")
            if v > 10000:  # Sanity check for maximum cost
                raise ValueError("Cost exceeds maximum allowed value")
            return round(v, 2)  # Round to 2 decimal places
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True
