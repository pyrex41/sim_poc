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
    metadata: Optional[Dict[str, Any]] = None
    createdAt: str
    updatedAt: str


class ClientCreateRequest(BaseModel):
    """Request model for creating a client"""

    name: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    brandGuidelines: Optional[BrandGuidelines] = None
    metadata: Optional[Dict[str, Any]] = None


class ClientUpdateRequest(BaseModel):
    """Request model for updating a client"""

    name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    brandGuidelines: Optional[BrandGuidelines] = None
    metadata: Optional[Dict[str, Any]] = None


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
    productUrl: Optional[str] = None
    brief: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    createdAt: str
    updatedAt: str


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign"""

    clientId: str
    name: str
    goal: str
    status: str = "draft"
    productUrl: Optional[str] = None
    brief: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign"""

    name: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    productUrl: Optional[str] = None
    brief: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


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


# ============================================================================
# Audio Generation Models (Scene-based Music Generation)
# ============================================================================


class ScenePrompt(BaseModel):
    """Individual scene prompt for audio generation"""

    scene_number: int
    prompt: str
    duration: Optional[float] = None  # Override default duration

    model_config = {
        "json_schema_extra": {
            "example": {
                "scene_number": 1,
                "prompt": "Cinematic wide shot, low angle. Clear water or reflective surface gently rippling. Subtle, smooth camera push-in (dolly forward). Bright natural lighting with glistening highlights on the water/surface.",
                "duration": 4.0,
            }
        }
    }


class SceneAudioRequest(BaseModel):
    """Request model for generating audio from scene prompts"""

    scenes: list[ScenePrompt]
    default_duration: float = 4.0  # Default seconds per scene
    model_id: str = "meta/musicgen"

    model_config = {
        "json_schema_extra": {
            "example": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "prompt": "Cinematic wide shot, low angle. Clear water or reflective surface gently rippling. Subtle, smooth camera push-in (dolly forward). Bright natural lighting with glistening highlights on the water/surface.",
                        "duration": 4.0,
                    },
                    {
                        "scene_number": 2,
                        "prompt": "Smooth sideways camera truck (left or right – choose direction that creates natural parallax). Luxurious bedroom with large windows or glass walls. Parallax effect: bed and foreground elements move slightly faster than the background view.",
                        "duration": 4.0,
                    },
                ],
                "default_duration": 4.0,
                "model_id": "meta/musicgen",
            }
        }
    }


class SceneAudioResponse(BaseModel):
    """Response model for scene audio generation"""

    audio_id: int
    audio_url: str
    total_duration: float
    scenes_processed: int
    model_used: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "audio_id": 123,
                "audio_url": "/api/audio/123/data",
                "total_duration": 28.0,
                "scenes_processed": 7,
                "model_used": "meta/musicgen",
            }
        }
    }


# ============================================================================
# Image Pair Selection & Video Generation Models (New Feature)
# ============================================================================


class ImagePairJobCreateRequest(BaseModel):
    """Request model for creating a job from image pairs."""

    campaignId: str
    clientId: Optional[str] = None
    clipDuration: Optional[float] = None  # Duration for each clip in seconds
    numPairs: Optional[int] = None  # Optional target number of pairs to select


class SubJobStatus(str, Enum):
    """Sub-job status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SubJob(BaseModel):
    """Sub-job model for individual image pair to video conversion."""

    id: str
    jobId: int
    subJobNumber: int
    image1AssetId: str
    image2AssetId: str
    replicatePredictionId: Optional[str] = None
    modelId: str
    inputParameters: Optional[Dict[str, Any]] = None
    status: SubJobStatus
    progress: float = 0.0
    videoUrl: Optional[str] = None
    videoBlobId: Optional[str] = None
    durationSeconds: Optional[float] = None
    estimatedCost: Optional[float] = None
    actualCost: Optional[float] = None
    errorMessage: Optional[str] = None
    retryCount: int = 0
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    createdAt: str
    updatedAt: str


class SubJobSummary(BaseModel):
    """Summary of sub-job progress."""

    total: int
    pending: int
    processing: int
    completed: int
    failed: int


# ============================================================================
# Property Video Generation Models
# ============================================================================


class PropertyPhoto(BaseModel):
    """Photo from crawled property website with metadata."""

    id: str = Field(..., description="Unique photo identifier")
    filename: Optional[str] = Field(None, description="Photo filename")
    url: str = Field(..., description="URL to photo")
    tags: Optional[List[str]] = Field(None, description="Photo tags")
    dominantColors: Optional[List[str]] = Field(None, description="Dominant colors")
    detectedObjects: Optional[List[str]] = Field(None, description="Detected objects")
    composition: Optional[str] = Field(None, description="Composition style")
    lighting: Optional[str] = Field(None, description="Lighting conditions")
    resolution: Optional[str] = Field(None, description="Image resolution")
    aspectRatio: Optional[str] = Field(None, description="Aspect ratio")


class PropertyInfo(BaseModel):
    """Information about luxury lodging property."""

    name: str = Field(..., description="Property name")
    location: str = Field(..., description="Property location")
    propertyType: str = Field(
        ..., description="Type of property (e.g., boutique hotel, resort)"
    )
    positioning: str = Field(
        ..., description="Brand positioning (e.g., eco-luxury, modern minimalist)"
    )


class PropertyVideoRequest(BaseModel):
    """Request to generate video from property photos."""

    propertyInfo: PropertyInfo = Field(..., description="Property information")
    photos: List[PropertyPhoto] = Field(
        ..., description="List of property photos", min_items=14
    )
    campaignId: str = Field(..., description="Campaign ID for this property")
    clipDuration: Optional[float] = Field(
        6.0, description="Duration per scene in seconds"
    )
    videoModel: Optional[str] = Field(
        "veo3", description="Video generation model (veo3 or hailuo-2.0)"
    )


class SceneImagePair(BaseModel):
    """Image pair selection for a scene."""

    sceneNumber: int
    sceneType: str
    firstImage: Dict[str, Any]
    lastImage: Dict[str, Any]
    transitionAnalysis: Dict[str, Any]


class PropertySelectionResult(BaseModel):
    """Result of Grok's property photo selection."""

    propertyName: str
    selectionMetadata: Dict[str, Any]
    scenePairs: List[SceneImagePair]
    recommendations: Optional[Dict[str, Any]] = None


class PropertyVideoJobResponse(BaseModel):
    """Response after creating property video job."""

    jobId: int
    status: str
    propertyName: str
    totalScenes: int
    selectionMetadata: Dict[str, Any]
    scenePairs: List[SceneImagePair]
