"""
Asset Downloader Service.

This module handles downloading assets from URLs, validating them, and storing
them as blobs in the database for V3 API asset handling.
"""

import logging
import uuid
import requests
import mimetypes
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PIL import Image
import io

# Optional: python-magic for file type validation (falls back to mimetypes if not available)
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from ..database_helpers import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MAX_DOWNLOAD_SIZE_MB = 100  # Maximum file size to download
DOWNLOAD_TIMEOUT_SECONDS = 60  # Timeout for download requests
ALLOWED_ASSET_DOMAINS = ["*"]  # Allow all domains for now

# Supported content types
SUPPORTED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
]

SUPPORTED_VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
]

SUPPORTED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/webm",
]

SUPPORTED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


class AssetDownloadError(Exception):
    """Exception raised when asset download fails."""

    pass


def download_asset_from_url(
    url: str, asset_type: str, expected_content_type: Optional[str] = None
) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Download an asset from a URL and validate it.

    Args:
        url: The URL to download from
        asset_type: Expected asset type ("image", "video", "audio", "document")
        expected_content_type: Optional expected MIME type

    Returns:
        Tuple of (data, content_type, metadata)

    Raises:
        AssetDownloadError: If download fails or validation fails
    """
    logger.info(f"Downloading asset from URL: {url[:100]}...")

    try:
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            raise AssetDownloadError("URL must start with http:// or https://")

        # TODO: Add domain validation if ALLOWED_ASSET_DOMAINS is not ["*"]

        # Make HEAD request first to check size
        try:
            head_response = requests.head(
                url,
                timeout=10,
                allow_redirects=True,
                headers={"User-Agent": "AdVideoGeneration/1.0"},
            )
            content_length = head_response.headers.get("Content-Length")

            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > MAX_DOWNLOAD_SIZE_MB:
                    raise AssetDownloadError(
                        f"File too large: {size_mb:.1f}MB (max: {MAX_DOWNLOAD_SIZE_MB}MB)"
                    )
        except requests.RequestException as e:
            logger.warning(f"HEAD request failed: {e}, proceeding with GET")

        # Download the asset
        response = requests.get(
            url,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            stream=True,
            headers={"User-Agent": "AdVideoGeneration/1.0"},
        )
        response.raise_for_status()

        # Check Content-Length from response headers
        content_length = response.headers.get("Content-Length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > MAX_DOWNLOAD_SIZE_MB:
                raise AssetDownloadError(
                    f"File too large: {size_mb:.1f}MB (max: {MAX_DOWNLOAD_SIZE_MB}MB)"
                )

        # Download in chunks with size limit
        data = bytearray()
        max_size_bytes = MAX_DOWNLOAD_SIZE_MB * 1024 * 1024

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                data.extend(chunk)
                if len(data) > max_size_bytes:
                    raise AssetDownloadError(
                        f"File exceeds maximum size of {MAX_DOWNLOAD_SIZE_MB}MB"
                    )

        data = bytes(data)
        logger.info(f"Downloaded {len(data)} bytes from {url[:50]}...")

        # Get content type
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type:
            # Try to guess from URL extension
            content_type, _ = mimetypes.guess_type(url)
            if not content_type:
                # Try magic library for file type detection if available
                if MAGIC_AVAILABLE:
                    try:
                        mime = magic.Magic(mime=True)
                        content_type = mime.from_buffer(data)
                    except Exception as e:
                        logger.warning(f"Failed to detect content type with magic: {e}")
                        content_type = "application/octet-stream"
                else:
                    logger.warning(
                        "Content type detection: python-magic not available, using fallback"
                    )
                    content_type = "application/octet-stream"

        # Validate content type matches asset type
        _validate_content_type(content_type, asset_type)

        # Extract metadata based on asset type
        metadata = _extract_metadata(data, content_type, asset_type)

        logger.info(f"Successfully downloaded and validated asset: {content_type}")
        return data, content_type, metadata

    except requests.RequestException as e:
        logger.error(f"Failed to download asset from {url}: {e}")
        raise AssetDownloadError(f"Download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading asset: {e}")
        raise AssetDownloadError(f"Unexpected error: {str(e)}")


def store_blob(data: bytes, content_type: str) -> str:
    """
    Store asset data as a blob in the database.

    Args:
        data: The asset data as bytes
        content_type: The MIME type of the asset

    Returns:
        The blob ID (UUID)

    Raises:
        Exception: If storage fails
    """
    blob_id = str(uuid.uuid4())
    size_bytes = len(data)

    logger.info(f"Storing blob {blob_id} ({size_bytes} bytes, {content_type})")

    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO asset_blobs (id, data, content_type, size_bytes)
                VALUES (?, ?, ?, ?)
                """,
                (blob_id, data, content_type, size_bytes),
            )
            conn.commit()

        logger.info(f"Successfully stored blob {blob_id}")
        return blob_id

    except Exception as e:
        logger.error(f"Failed to store blob: {e}")
        raise


def get_blob_by_id(blob_id: str) -> Optional[Tuple[bytes, str]]:
    """
    Retrieve a blob from the database.

    Args:
        blob_id: The blob UUID

    Returns:
        Tuple of (data, content_type) or None if not found
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT data, content_type FROM asset_blobs WHERE id = ?", (blob_id,)
            )
            row = cursor.fetchone()

            if row:
                return bytes(row["data"]), row["content_type"]
            return None

    except Exception as e:
        logger.error(f"Failed to retrieve blob {blob_id}: {e}")
        return None


def _validate_content_type(content_type: str, asset_type: str) -> None:
    """
    Validate that content type matches expected asset type.

    Args:
        content_type: The MIME type
        asset_type: Expected asset type ("image", "video", "audio", "document")

    Raises:
        AssetDownloadError: If content type doesn't match asset type
    """
    content_type_lower = content_type.lower()

    if asset_type == "image":
        if content_type_lower not in SUPPORTED_IMAGE_TYPES:
            raise AssetDownloadError(
                f"Invalid image type: {content_type}. Supported: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )
    elif asset_type == "video":
        if content_type_lower not in SUPPORTED_VIDEO_TYPES:
            raise AssetDownloadError(
                f"Invalid video type: {content_type}. Supported: {', '.join(SUPPORTED_VIDEO_TYPES)}"
            )
    elif asset_type == "audio":
        if content_type_lower not in SUPPORTED_AUDIO_TYPES:
            raise AssetDownloadError(
                f"Invalid audio type: {content_type}. Supported: {', '.join(SUPPORTED_AUDIO_TYPES)}"
            )
    elif asset_type == "document":
        if content_type_lower not in SUPPORTED_DOCUMENT_TYPES:
            raise AssetDownloadError(
                f"Invalid document type: {content_type}. Supported: {', '.join(SUPPORTED_DOCUMENT_TYPES)}"
            )
    else:
        raise AssetDownloadError(f"Unknown asset type: {asset_type}")


def _extract_metadata(
    data: bytes, content_type: str, asset_type: str
) -> Dict[str, Any]:
    """
    Extract metadata from asset data.

    Args:
        data: The asset data
        content_type: The MIME type
        asset_type: The asset type

    Returns:
        Dictionary of metadata (width, height, duration, etc.)
    """
    metadata: Dict[str, Any] = {"size": len(data)}

    try:
        if asset_type == "image":
            # Extract image dimensions
            image = Image.open(io.BytesIO(data))
            metadata["width"] = image.width
            metadata["height"] = image.height
            metadata["format"] = image.format.lower() if image.format else "unknown"

        elif asset_type == "video":
            # For now, just extract format from content type
            # TODO: Use ffprobe for video metadata extraction
            format_map = {
                "video/mp4": "mp4",
                "video/webm": "webm",
                "video/quicktime": "mov",
                "video/x-msvideo": "avi",
                "video/x-matroska": "mkv",
            }
            metadata["format"] = format_map.get(content_type.lower(), "unknown")
            # Placeholder values - would need ffprobe for real extraction
            metadata["width"] = None
            metadata["height"] = None
            metadata["duration"] = None

        elif asset_type == "audio":
            # Extract format from content type
            format_map = {
                "audio/mpeg": "mp3",
                "audio/mp3": "mp3",
                "audio/wav": "wav",
                "audio/ogg": "ogg",
                "audio/webm": "webm",
            }
            metadata["format"] = format_map.get(content_type.lower(), "unknown")
            metadata["duration"] = None  # Would need audio library for real extraction

        elif asset_type == "document":
            # Extract format from content type
            format_map = {
                "application/pdf": "pdf",
                "application/msword": "doc",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            }
            metadata["format"] = format_map.get(content_type.lower(), "unknown")
            metadata["page_count"] = None  # Would need PDF library for real extraction

    except Exception as e:
        logger.warning(f"Failed to extract metadata: {e}")
        # Return basic metadata even if extraction fails
        # Handle special cases like svg+xml -> svg
        format_str = content_type.split("/")[-1] if "/" in content_type else "unknown"
        # Clean up compound formats (e.g., svg+xml -> svg)
        if "+" in format_str:
            format_str = format_str.split("+")[0]
        metadata["format"] = format_str

    return metadata


def generate_thumbnail(
    asset_data: bytes, content_type: str, asset_type: str, max_size: int = 128
) -> Optional[bytes]:
    """
    Generate a thumbnail for an asset.

    Args:
        asset_data: The asset binary data
        content_type: MIME type of the asset
        asset_type: Asset type ("image", "video", "audio", "document")
        max_size: Maximum dimension for thumbnail (default 128px)

    Returns:
        Thumbnail data as bytes, or None if generation fails
    """
    try:
        if asset_type == "image" and content_type.startswith("image/"):
            # Generate thumbnail for images using PIL
            image = Image.open(io.BytesIO(asset_data))

            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode in ("RGBA", "LA", "P"):
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            # Generate thumbnail
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save as JPEG
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85)
            return output.getvalue()

        elif asset_type == "video" and content_type.startswith("video/"):
            # Generate thumbnail for videos using ffmpeg
            # Write asset data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_file.write(asset_data)
                temp_input = temp_file.name

            try:
                # Create temporary output file for thumbnail
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as temp_output:
                    temp_thumb = temp_output.name

                # Use ffmpeg to extract frame at 1 second
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_input,
                    "-ss",
                    "00:00:01",
                    "-vframes",
                    "1",
                    "-vf",
                    f"scale='min({max_size},iw)':'min({max_size},ih)':force_original_aspect_ratio=decrease",
                    "-q:v",
                    "3",
                    temp_thumb,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and os.path.exists(temp_thumb):
                    with open(temp_thumb, "rb") as f:
                        return f.read()
                else:
                    logger.warning(
                        f"ffmpeg thumbnail generation failed: {result.stderr}"
                    )
                    return None

            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_input)
                    if "temp_thumb" in locals():
                        os.unlink(temp_thumb)
                except:
                    pass

        elif asset_type == "document" and content_type == "application/pdf":
            # For PDFs, we could generate a thumbnail of the first page
            # This would require additional libraries like PyPDF2 + PIL
            # For now, return None
            logger.info("PDF thumbnail generation not implemented yet")
            return None

        else:
            # No thumbnail generation for audio or other types
            return None

    except Exception as e:
        logger.warning(f"Failed to generate thumbnail: {e}")
        return None


def generate_and_store_thumbnail(
    asset_data: bytes, content_type: str, asset_type: str, max_size: int = 128
) -> Optional[str]:
    """
    Generate a thumbnail and store it as a blob.

    Args:
        asset_data: The asset binary data
        content_type: MIME type of the asset
        asset_type: Asset type ("image", "video", "audio", "document")
        max_size: Maximum dimension for thumbnail

    Returns:
        Blob ID of the stored thumbnail, or None if generation fails
    """
    thumbnail_data = generate_thumbnail(asset_data, content_type, asset_type, max_size)
    if thumbnail_data:
        try:
            blob_id = store_blob(thumbnail_data, "image/jpeg")
            logger.info(f"Generated and stored thumbnail blob {blob_id}")
            return blob_id
        except Exception as e:
            logger.error(f"Failed to store thumbnail blob: {e}")
            return None
    return None
