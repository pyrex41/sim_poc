"""
Asset metadata extraction utilities.

This module provides functions to extract metadata from various file types:
- Images: dimensions (width, height)
- Videos: dimensions, duration, thumbnail generation
- Audio: duration, waveform generation (placeholder)
- Documents: page count (PDFs)
"""

import os
import subprocess
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import json


def get_file_format(file_path: str, mime_type: Optional[str] = None) -> str:
    """Get the file format/extension.

    Args:
        file_path: Path to the file
        mime_type: Optional MIME type

    Returns:
        File format (e.g., 'png', 'mp4', 'pdf')
    """
    # Get extension from file path
    ext = Path(file_path).suffix.lower().lstrip('.')

    # Map common extensions
    if ext:
        return ext

    # Fallback to mime type
    if mime_type:
        ext_from_mime = mimetypes.guess_extension(mime_type)
        if ext_from_mime:
            return ext_from_mime.lstrip('.')

    return 'unknown'


def determine_asset_type(mime_type: str, file_format: str) -> str:
    """Determine asset_type from MIME type and format.

    Args:
        mime_type: MIME type string
        file_format: File extension/format

    Returns:
        Asset type: 'image', 'video', 'audio', or 'document'
    """
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'document'
    elif file_format.lower() in ['pdf', 'doc', 'docx', 'txt']:
        return 'document'
    else:
        return 'document'  # Default to document for unknown types


def extract_image_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from an image file.

    Args:
        file_path: Path to image file

    Returns:
        Dict with width and height
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            return {
                'width': width,
                'height': height
            }
    except Exception as e:
        print(f"Error extracting image metadata: {e}")
        return {}


def extract_video_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a video file using ffprobe.

    Args:
        file_path: Path to video file

    Returns:
        Dict with width, height, and duration
    """
    try:
        # Use ffprobe to get video metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print(f"ffprobe error: {result.stderr}")
            return {}

        data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            return {}

        metadata = {}

        # Get dimensions
        if 'width' in video_stream:
            metadata['width'] = video_stream['width']
        if 'height' in video_stream:
            metadata['height'] = video_stream['height']

        # Get duration (prefer from format, fallback to stream)
        duration_str = data.get('format', {}).get('duration') or video_stream.get('duration')
        if duration_str:
            metadata['duration'] = int(float(duration_str))

        return metadata

    except subprocess.TimeoutExpired:
        print(f"ffprobe timed out for {file_path}")
        return {}
    except FileNotFoundError:
        print("ffprobe not found. Install ffmpeg to extract video metadata.")
        return {}
    except Exception as e:
        print(f"Error extracting video metadata: {e}")
        return {}


def generate_video_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """Generate a thumbnail from a video at a specific timestamp.

    Args:
        video_path: Path to video file
        output_path: Path where thumbnail should be saved
        timestamp: Time in seconds to extract frame (default: 1.0)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use ffmpeg to extract a frame
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-q:v', '2',  # Quality (2 is high quality)
            '-y',  # Overwrite output file
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=15)

        if result.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            print(f"ffmpeg thumbnail generation failed: {result.stderr.decode()}")
            return False

    except subprocess.TimeoutExpired:
        print(f"ffmpeg timed out generating thumbnail for {video_path}")
        return False
    except FileNotFoundError:
        print("ffmpeg not found. Install ffmpeg to generate video thumbnails.")
        return False
    except Exception as e:
        print(f"Error generating video thumbnail: {e}")
        return False


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from an audio file.

    Args:
        file_path: Path to audio file

    Returns:
        Dict with duration
    """
    try:
        # Use ffprobe to get audio metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return {}

        data = json.loads(result.stdout)

        metadata = {}

        # Get duration
        duration_str = data.get('format', {}).get('duration')
        if duration_str:
            metadata['duration'] = int(float(duration_str))

        return metadata

    except Exception as e:
        print(f"Error extracting audio metadata: {e}")
        return {}


def extract_document_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a document (PDF).

    Args:
        file_path: Path to document file

    Returns:
        Dict with pageCount (for PDFs)
    """
    try:
        # For now, we'll skip PDF page counting unless PyPDF2 is installed
        # This can be added later if needed
        return {}
    except Exception as e:
        print(f"Error extracting document metadata: {e}")
        return {}


def extract_file_metadata(file_path: str, mime_type: str) -> Dict[str, Any]:
    """Extract all relevant metadata from a file based on its type.

    Args:
        file_path: Path to the file
        mime_type: MIME type of the file

    Returns:
        Dict containing all extracted metadata
    """
    file_format = get_file_format(file_path, mime_type)
    asset_type = determine_asset_type(mime_type, file_format)

    metadata = {
        'asset_type': asset_type,
        'format': file_format,
        'size': os.path.getsize(file_path) if os.path.exists(file_path) else None
    }

    # Extract type-specific metadata
    if asset_type == 'image':
        metadata.update(extract_image_metadata(file_path))

    elif asset_type == 'video':
        video_meta = extract_video_metadata(file_path)
        metadata.update(video_meta)

    elif asset_type == 'audio':
        metadata.update(extract_audio_metadata(file_path))

    elif asset_type == 'document':
        metadata.update(extract_document_metadata(file_path))

    return metadata


if __name__ == "__main__":
    # Test the metadata extraction
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        mime_type = mimetypes.guess_type(test_file)[0] or 'application/octet-stream'
        print(f"File: {test_file}")
        print(f"MIME type: {mime_type}")
        print(f"Metadata: {extract_file_metadata(test_file, mime_type)}")
