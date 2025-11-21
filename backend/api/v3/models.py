"""
Pydantic models for v3 API endpoints.

These models mirror the frontend TypeScript interfaces and provide
strict validation and serialization for the v3 API responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# API Response Envelope
# ============================================================================


class APIResponse(BaseModel):
    """Standard API response envelope matching lib/types/api.ts"""

    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @classmethod
    def success(
        cls, data: Any = None, meta: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """Create a successful response"""
        return cls(data=data, error=None, meta=meta)

    @classmethod
    def create_error(
        cls, error_msg: str, meta: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """Create an error response"""
        return cls(data=None, error=error_msg, meta=meta)


# ============================================================================
# Client Models
# ============================================================================


class BrandGuidelines(BaseModel):
    """Brand guidelines object within client"""

    colors: Optional[List[str]] = None
    fonts: Optional[List[str]] = None
    tone: Optional[str] = None
    restrictions: Optional[List[str]] = None
    examples: Optional[List[str]] = None


class Client(BaseModel):
    """Client model matching lib/types/client.ts"""

    id: str
    name: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    brandGuidelines: Optional[BrandGuidelines] = None
    createdAt: str
    updatedAt: str


class ClientCreateRequest(BaseModel):
    """Request model for creating a client"""

    name: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    brandGuidelines: Optional[BrandGuidelines] = None


class ClientUpdateRequest(BaseModel):
    """Request model for updating a client"""

    name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    brandGuidelines: Optional[BrandGuidelines] = None


# ============================================================================
# Campaign Models
# ============================================================================


class Campaign(BaseModel):
    """Campaign model matching lib/types/campaign.ts"""

    id: str
    clientId: str
    name: str
    goal: str
    status: str
    brief: Optional[Dict[str, Any]] = None
    createdAt: str
    updatedAt: str


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign"""

    clientId: str
    name: str
    goal: str
    status: str = "draft"
    brief: Optional[Dict[str, Any]] = None


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign"""

    name: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    brief: Optional[Dict[str, Any]] = None


# ============================================================================
# Job Models (Generation Workflow)
# ============================================================================


class JobStatus(str, Enum):
    """Job status enum matching frontend expectations"""

    PENDING = "pending"
    STORYBOARD_PROCESSING = "storyboard_processing"
    STORYBOARD_READY = "storyboard_ready"
    VIDEO_PROCESSING = "video_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobContext(BaseModel):
    """Context object for job creation"""

    clientId: str
    campaignId: Optional[str] = None
    userId: Optional[str] = None  # Made optional - can be derived from auth token


class AdBasics(BaseModel):
    """Ad basics object for job creation"""

    product: str
    targetAudience: str
    keyMessage: str
    callToAction: str


class CreativeDirection(BaseModel):
    """Creative direction within creative object"""

    style: str
    tone: Optional[str] = None  # Made optional for flexibility
    visualElements: Optional[List[str]] = None  # Made optional for flexibility
    musicStyle: Optional[str] = None


class VideoSpecs(BaseModel):
    """Video specifications"""

    duration: float  # Duration in seconds
    format: str = "16:9"  # Aspect ratio
    resolution: Optional[str] = None  # e.g., "1080p"


class AssetInput(BaseModel):
    """Asset input for job creation - can be URL or existing asset ID"""

    url: Optional[str] = None  # URL to download asset from
    assetId: Optional[str] = None  # Existing asset ID
    type: Optional[str] = None  # Asset type (image, video, audio)
    name: Optional[str] = None  # Asset name/description
    role: Optional[str] = (
        None  # Optional hint for scene placement (e.g., "product_shot", "background")
    )


class Creative(BaseModel):
    """Creative object for job creation"""

    videoSpecs: VideoSpecs  # Video specifications
    direction: CreativeDirection
    assets: Optional[List[AssetInput]] = None  # Assets to use in generation
    storyboard: Optional[Dict[str, Any]] = None


class AdvancedSettings(BaseModel):
    """Advanced settings object for job creation"""

    duration: Optional[int] = None
    resolution: Optional[str] = None
    modelPreferences: Optional[List[str]] = None


class JobCreateRequest(BaseModel):
    """Request model for creating a job"""

    context: JobContext
    adBasics: AdBasics
    creative: Creative
    advanced: Optional[AdvancedSettings] = None


class Job(BaseModel):
    """Job model for polling and status"""

    id: str
    status: JobStatus
    progress: Optional[Dict[str, Any]] = None
    storyboard: Optional[Dict[str, Any]] = None
    videoUrl: Optional[str] = None
    error: Optional[str] = None
    estimatedCost: Optional[float] = None
    actualCost: Optional[float] = None
    createdAt: str
    updatedAt: str


class JobAction(str, Enum):
    """Job action enum"""

    APPROVE = "approve"
    CANCEL = "cancel"
    REGENERATE_SCENE = "regenerate_scene"


class JobActionRequest(BaseModel):
    """Request model for job actions"""

    action: JobAction
    payload: Optional[Dict[str, Any]] = None


# ============================================================================
# Cost Estimation Models
# ============================================================================


class CostEstimate(BaseModel):
    """Cost estimate response"""

    estimatedCost: float
    currency: str = "USD"
    breakdown: Optional[Dict[str, Any]] = None
    validUntil: Optional[str] = None


class DryRunRequest(BaseModel):
    """Request model for cost estimation (dry run)"""

    context: JobContext
    adBasics: AdBasics
    creative: Creative
    advanced: Optional[AdvancedSettings] = None


# ============================================================================
# Asset Models (Reusing existing schemas)
# ============================================================================

# Import existing asset models
from ...schemas.assets import Asset, UploadAssetInput, UploadAssetFromUrlInput


# ============================================================================
# Unified Asset Upload Models
# ============================================================================


class UnifiedAssetUploadInput(BaseModel):
    """Unified input model for asset upload (supports both file upload and URL)"""

    uploadType: Literal[
        "file", "url"
    ]  # Type of upload: "file" for direct upload, "url" for URL download
    name: str
    type: str  # Asset type: "image", "video", "audio", "document"
    clientId: Optional[str] = None
    campaignId: Optional[str] = None
    tags: Optional[List[str]] = None
    generateThumbnail: bool = (
        True  # Whether to auto-generate thumbnail for images/videos
    )

    # For URL uploads
    sourceUrl: Optional[str] = (
        None  # URL to download asset from (required when uploadType="url")
    )

    # Note: File data is handled separately via FastAPI's UploadFile when uploadType="file"


# Note: Asset models are extended in schemas/assets.py to include thumbnailBlobId and sourceUrl
