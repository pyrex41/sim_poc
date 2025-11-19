"""
Asset Entity Types
Pydantic models for asset management, uploads, and metadata
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_serializer


# Format Types
class ImageFormat(str, Enum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    SVG = "svg"


class VideoFormat(str, Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"
    AVI = "avi"
    MKV = "mkv"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    AAC = "aac"
    M4A = "m4a"


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"


# Asset Type Enum
class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


# Base Asset Model - Common fields for all asset types
class BaseAsset(BaseModel):
    """Base asset with all common fields"""
    id: str
    userId: str
    clientId: Optional[str] = None  # OPTIONAL - asset may or may not be associated with a client
    campaignId: Optional[str] = None  # OPTIONAL - asset may be associated with a campaign
    name: str
    url: str
    size: Optional[int] = None  # File size in bytes
    uploadedAt: str  # ISO 8601 timestamp
    tags: Optional[list[str]] = None

    # NOTE: blob_data is stored in DB but NOT exposed in API responses
    # It's only used for internal storage when files are uploaded

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "userId": "1",
                "clientId": "client-uuid",  # Required
                "campaignId": "campaign-uuid",  # Optional
                "name": "example-asset",
                "url": "https://api.example.com/assets/123e4567",
                "size": 1024000,
                "uploadedAt": "2025-01-15T10:30:00Z",
                "tags": ["brand_logo", "product"]
            }
        }
    }


# Image Asset
class ImageAsset(BaseAsset):
    """Image asset with dimensions"""
    type: Literal["image"] = "image"
    format: ImageFormat
    width: int
    height: int

    model_config = {
        "json_schema_extra": {
            "example": {
                **BaseAsset.model_config["json_schema_extra"]["example"],
                "type": "image",
                "format": "png",
                "width": 1920,
                "height": 1080
            }
        }
    }


# Video Asset
class VideoAsset(BaseAsset):
    """Video asset with dimensions, duration, and thumbnail"""
    type: Literal["video"] = "video"
    format: VideoFormat
    width: int
    height: int
    duration: int  # Duration in seconds
    thumbnailUrl: str

    model_config = {
        "json_schema_extra": {
            "example": {
                **BaseAsset.model_config["json_schema_extra"]["example"],
                "type": "video",
                "format": "mp4",
                "width": 1920,
                "height": 1080,
                "duration": 30,
                "thumbnailUrl": "https://api.example.com/assets/123e4567/thumbnail"
            }
        }
    }


# Audio Asset
class AudioAsset(BaseAsset):
    """Audio asset with duration and optional waveform"""
    type: Literal["audio"] = "audio"
    format: AudioFormat
    duration: int  # Duration in seconds
    waveformUrl: Optional[str] = None  # Optional waveform visualization URL

    model_config = {
        "json_schema_extra": {
            "example": {
                **BaseAsset.model_config["json_schema_extra"]["example"],
                "type": "audio",
                "format": "mp3",
                "duration": 180,
                "waveformUrl": "https://api.example.com/assets/123e4567/waveform"
            }
        }
    }


# Document Asset
class DocumentAsset(BaseAsset):
    """Document asset with page count and optional thumbnail"""
    type: Literal["document"] = "document"
    format: DocumentFormat
    pageCount: Optional[int] = None
    thumbnailUrl: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                **BaseAsset.model_config["json_schema_extra"]["example"],
                "type": "document",
                "format": "pdf",
                "pageCount": 10,
                "thumbnailUrl": "https://api.example.com/assets/123e4567/thumbnail"
            }
        }
    }


# Unified Asset Type (Discriminated Union)
Asset = Union[ImageAsset, VideoAsset, AudioAsset, DocumentAsset]


# Asset Tags
class VisualAssetTag(str, Enum):
    """Tags for visual assets (images/videos)"""
    FIRST_FRAME = "first_frame"
    SUBJECT = "subject"
    BRAND_LOGO = "brand_logo"
    PRODUCT_SHOT = "product_shot"
    BACKGROUND = "background"
    TRANSITION = "transition"
    CLOSING_FRAME = "closing_frame"


class AudioAssetTag(str, Enum):
    """Tags for audio assets"""
    USE_FULL_AUDIO = "use_full_audio"
    VOICE_SAMPLE = "voice_sample"


# All possible asset tags (union of visual and audio)
AssetTag = Union[VisualAssetTag, AudioAssetTag]


# Asset with metadata for video generation
class AssetWithMetadata(BaseModel):
    """
    Asset with metadata for video generation
    Includes source, tags, and priority for generation context
    """
    id: str
    url: str
    thumbnailUrl: Optional[str] = None
    type: AssetType
    source: Literal["campaign", "client", "uploaded"]
    name: str
    tags: list[str] = Field(default_factory=list)  # AssetTag values as strings
    priority: int = Field(ge=1)  # Order in the list (1-based)

    # Media-specific fields
    duration: Optional[int] = None  # For audio/video, in seconds
    waveformUrl: Optional[str] = None  # For audio visualization
    fileSize: Optional[int] = None
    mimeType: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "url": "https://api.example.com/assets/123e4567",
                "thumbnailUrl": "https://api.example.com/assets/123e4567/thumbnail",
                "type": "video",
                "source": "campaign",
                "name": "product-demo",
                "tags": ["product_shot", "brand_logo"],
                "priority": 1,
                "duration": 30,
                "fileSize": 5242880,
                "mimeType": "video/mp4"
            }
        }
    }


# Input model for uploading a new asset
class UploadAssetInput(BaseModel):
    """Input model for asset upload requests"""
    name: str
    type: AssetType
    clientId: Optional[str] = None  # OPTIONAL - asset may be associated with a client
    campaignId: Optional[str] = None  # OPTIONAL - asset may be associated with a campaign
    tags: Optional[list[str]] = None

    # Note: File is handled separately via FastAPI's UploadFile
    # This model is for the form data fields


# Input model for uploading asset from URL
class UploadAssetFromUrlInput(BaseModel):
    """Input model for asset upload from URL"""
    name: str
    type: AssetType
    url: str  # URL to download asset from
    clientId: Optional[str] = None
    campaignId: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "product-image",
                "type": "image",
                "url": "https://example.com/images/product.jpg",
                "clientId": "client-uuid",
                "campaignId": "campaign-uuid",
                "tags": ["product", "hero"]
            }
        }
    }

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "product-image",
                "type": "image",
                "clientId": "client-uuid",  # Required
                "campaignId": "campaign-uuid",  # Optional
                "tags": ["brand_logo", "product_shot"]
            }
        }
    }


# Database model (internal use only - includes blob_data)
class AssetDB(BaseModel):
    """
    Internal database model for assets
    Includes blob_data field which is NOT exposed in API responses
    """
    id: str
    user_id: Optional[int] = None
    client_id: Optional[str] = None
    campaign_id: Optional[str] = None
    name: str
    asset_type: str
    url: str
    size: Optional[int] = None
    uploaded_at: datetime
    format: str
    tags: Optional[str] = None  # JSON string in DB
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    waveform_url: Optional[str] = None
    page_count: Optional[int] = None
    blob_data: Optional[bytes] = None  # Binary blob storage

    @field_serializer('uploaded_at')
    def serialize_datetime(self, dt: datetime, _info):
        """Serialize datetime to ISO 8601 string"""
        return dt.isoformat() + 'Z' if dt else None

    @field_serializer('tags')
    def serialize_tags(self, tags: Optional[str], _info):
        """Parse JSON string to list"""
        if not tags:
            return None
        import json
        try:
            return json.loads(tags)
        except:
            return None

    def to_asset_model(self) -> Asset:
        """Convert database model to appropriate Asset type"""
        import json

        # Parse tags from JSON string
        tags_list = None
        if self.tags:
            try:
                tags_list = json.loads(self.tags)
            except:
                pass

        # Common fields
        common = {
            "id": self.id,
            "userId": str(self.user_id) if self.user_id else "",
            "clientId": self.client_id,
            "campaignId": self.campaign_id,
            "name": self.name,
            "url": self.url,
            "size": self.size,
            "uploadedAt": self.uploaded_at.isoformat() + 'Z',
            "tags": tags_list,
            "format": self.format,
        }

        # Type-specific fields
        if self.asset_type == "image":
            return ImageAsset(
                **common,
                width=self.width or 0,
                height=self.height or 0,
            )
        elif self.asset_type == "video":
            return VideoAsset(
                **common,
                width=self.width or 0,
                height=self.height or 0,
                duration=self.duration or 0,
                thumbnailUrl=self.thumbnail_url or "",
            )
        elif self.asset_type == "audio":
            return AudioAsset(
                **common,
                duration=self.duration or 0,
                waveformUrl=self.waveform_url,
            )
        elif self.asset_type == "document":
            return DocumentAsset(
                **common,
                pageCount=self.page_count,
                thumbnailUrl=self.thumbnail_url,
            )
        else:
            raise ValueError(f"Unknown asset type: {self.asset_type}")
