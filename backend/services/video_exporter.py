"""
Video Export Service.

This module handles video export functionality with ffmpeg for format conversion
and quality presets. Supports multiple output formats and quality settings.
"""

import logging
import subprocess
import os
from pathlib import Path
from typing import Optional, Literal, Tuple

logger = logging.getLogger(__name__)

# Quality presets (width x height, bitrate)
QUALITY_PRESETS = {
    "low": {
        "resolution": "854x480",
        "video_bitrate": "1000k",
        "audio_bitrate": "128k"
    },
    "medium": {
        "resolution": "1280x720",
        "video_bitrate": "2500k",
        "audio_bitrate": "192k"
    },
    "high": {
        "resolution": "1920x1080",
        "video_bitrate": "5000k",
        "audio_bitrate": "256k"
    }
}

# Format configurations
FORMAT_CONFIGS = {
    "mp4": {
        "codec": "libx264",
        "audio_codec": "aac",
        "ext": "mp4"
    },
    "mov": {
        "codec": "libx264",
        "audio_codec": "aac",
        "ext": "mov"
    },
    "webm": {
        "codec": "libvpx-vp9",
        "audio_codec": "libopus",
        "ext": "webm"
    }
}


def check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is available on the system.

    Returns:
        True if ffmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Get video information using ffprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary with video metadata or None if failed
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ],
            capture_output=True,
            timeout=10,
            text=True
        )

        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return None
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def export_video(
    input_path: str,
    output_path: str,
    format: Literal["mp4", "mov", "webm"] = "mp4",
    quality: Literal["low", "medium", "high"] = "medium",
    overwrite: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Export video with specified format and quality using ffmpeg.

    Args:
        input_path: Path to the input video file
        output_path: Path where the output video will be saved
        format: Output format (mp4, mov, webm)
        quality: Quality preset (low, medium, high)
        overwrite: Whether to overwrite existing output file

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    # Validate inputs
    if not os.path.exists(input_path):
        return False, f"Input video not found: {input_path}"

    if format not in FORMAT_CONFIGS:
        return False, f"Unsupported format: {format}"

    if quality not in QUALITY_PRESETS:
        return False, f"Invalid quality preset: {quality}"

    # Check ffmpeg availability
    if not check_ffmpeg_available():
        return False, "ffmpeg is not available on this system"

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Get format and quality settings
    fmt_config = FORMAT_CONFIGS[format]
    quality_preset = QUALITY_PRESETS[quality]

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", fmt_config["codec"],
        "-b:v", quality_preset["video_bitrate"],
        "-vf", f"scale={quality_preset['resolution']}",
        "-c:a", fmt_config["audio_codec"],
        "-b:a", quality_preset["audio_bitrate"],
    ]

    if overwrite:
        cmd.append("-y")

    cmd.append(output_path)

    logger.info(f"Exporting video: {input_path} -> {output_path} ({format}, {quality})")

    try:
        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300,  # 5 minutes max
            text=True
        )

        if result.returncode == 0:
            if os.path.exists(output_path):
                logger.info(f"Video exported successfully: {output_path}")
                return True, None
            else:
                error_msg = "Export command succeeded but output file not found"
                logger.error(error_msg)
                return False, error_msg
        else:
            error_msg = f"ffmpeg error: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = "Video export timed out (exceeded 5 minutes)"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during export: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_export_path(
    storage_path: str,
    job_id: int,
    format: str,
    quality: str
) -> str:
    """
    Generate the export file path for a job.

    Args:
        storage_path: Base storage path for videos
        job_id: Job ID
        format: Output format
        quality: Quality preset

    Returns:
        Full path to the export file
    """
    exports_dir = Path(storage_path) / "exports" / str(job_id)
    exports_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{format}_{quality}.{FORMAT_CONFIGS[format]['ext']}"
    return str(exports_dir / filename)


def cleanup_old_exports(storage_path: str, job_id: int) -> None:
    """
    Clean up old export files for a job.

    Args:
        storage_path: Base storage path for videos
        job_id: Job ID
    """
    exports_dir = Path(storage_path) / "exports" / str(job_id)

    if exports_dir.exists():
        for file in exports_dir.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                    logger.info(f"Deleted old export: {file}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file}: {e}")
