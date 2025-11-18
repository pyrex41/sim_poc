"""
Shared type definitions and enums for the generation platform.
"""
from enum import Enum
from typing import Literal


# Generation Engine Types
class EngineType(str, Enum):
    """Types of generation engines available."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PROMPT = "prompt"
    UTILITIES = "utilities"
    VIDEO_ANALYSIS = "video_analysis"


# Provider Types
class ImageProvider(str, Enum):
    """Image generation providers."""
    REPLICATE = "replicate"
    STABILITY = "stability"
    MIDJOURNEY = "midjourney"


class VideoProvider(str, Enum):
    """Video generation providers."""
    REPLICATE = "replicate"
    RUNWAY = "runway"
    PIKA = "pika"


class AudioProvider(str, Enum):
    """Audio generation providers."""
    REPLICATE = "replicate"
    SUNO = "suno"
    ELEVENLABS = "elevenlabs"


class PromptProvider(str, Enum):
    """Prompt parsing providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Task Status
class TaskStatus(str, Enum):
    """Status of a generation task."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


# Image Specific
class ImageModel(str, Enum):
    """Available image generation models."""
    FLUX = "flux"
    FLUX_PRO = "flux-pro"
    FLUX_DEV = "flux-dev"
    FLUX_SCHNELL = "flux-schnell"
    SDXL = "sdxl"
    SD3 = "sd3"


class ImageSize(str, Enum):
    """Standard image sizes."""
    SQUARE_1024 = "1024x1024"
    PORTRAIT_768_1024 = "768x1024"
    LANDSCAPE_1024_768 = "1024x768"
    WIDE_1920_1080 = "1920x1080"
    TALL_1080_1920 = "1080x1920"


class AspectRatio(str, Enum):
    """Standard aspect ratios."""
    SQUARE = "1:1"
    PORTRAIT = "3:4"
    LANDSCAPE = "4:3"
    WIDE = "16:9"
    TALL = "9:16"


# Video Specific
class VideoModel(str, Enum):
    """Available video generation models."""
    MINIMAX = "minimax"
    LUMA_RAY = "luma"
    SKYREELS = "skyreels-2"
    RUNWAY_GEN3 = "runway-gen3"
    PIKA_V1 = "pika-v1"
    KLING = "kling"


class VideoDuration(str, Enum):
    """Standard video durations."""
    SHORT_5S = "5s"
    MEDIUM_10S = "10s"
    LONG_15S = "15s"


# Audio Specific
class AudioModel(str, Enum):
    """Available audio generation models."""
    SUNO_V4 = "suno-v4"
    MUSICGEN = "musicgen"
    STABLE_AUDIO = "stable-audio"


class AudioDuration(int, Enum):
    """Standard audio durations in seconds."""
    SHORT = 30
    MEDIUM = 60
    LONG = 120
    EXTENDED = 180


# Asset Types
class AssetType(str, Enum):
    """Types of assets that can be uploaded or generated."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


# Pipeline Execution
class ExecutionMode(str, Enum):
    """How to execute pipeline steps."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DAG = "dag"


# File Extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

# MIME Types
IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
}

AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
}
