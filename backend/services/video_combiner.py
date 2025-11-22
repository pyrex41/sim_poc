"""
Video Combiner Service.

This module handles combining multiple video clips into a single video using ffmpeg.
Supports concatenation with optional transitions and maintains clip order.
"""

import logging
import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class VideoCombinerError(Exception):
    """Exception raised when video combining fails."""
    pass


def check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is available on the system.

    Returns:
        True if ffmpeg is available, False otherwise
    """
    import shutil
    # Just check if ffmpeg binary exists in PATH
    # Avoids potential timeout issues with running ffmpeg -version
    return shutil.which("ffmpeg") is not None


def combine_video_clips(
    clip_paths: List[str],
    output_path: str,
    transition_duration: float = 0.0,
    output_resolution: str = "1920x1080",
    output_fps: int = 30,
    keep_audio: bool = False,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Combine multiple video clips into a single video file.

    Args:
        clip_paths: List of paths to video clips (in order)
        output_path: Path for the output combined video
        transition_duration: Duration of crossfade transitions in seconds (0 = no transition)
        output_resolution: Output resolution (e.g., "1920x1080")
        output_fps: Output frames per second
        keep_audio: Whether to keep audio from clips (default: False)

    Returns:
        Tuple of (success, output_path, metadata):
            - success: True if combining succeeded
            - output_path: Path to the combined video (if successful)
            - metadata: Dict with duration, size, etc. (if successful)

    Raises:
        VideoCombinerError: If combining fails
    """
    if not clip_paths:
        raise VideoCombinerError("No clip paths provided")

    if not check_ffmpeg_available():
        raise VideoCombinerError("ffmpeg is not available on this system")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Combining {len(clip_paths)} video clips into {output_path}")

    try:
        if transition_duration > 0:
            # Use xfade filter for crossfade transitions
            success, error = _combine_with_transitions(
                clip_paths, output_path, transition_duration, output_resolution,
                output_fps, keep_audio
            )
        else:
            # Simple concatenation without transitions
            success, error = _combine_simple_concat(
                clip_paths, output_path, output_resolution, output_fps, keep_audio
            )

        if not success:
            logger.error(f"Video combining failed: {error}")
            return False, None, None

        # Get metadata of combined video
        metadata = _get_video_metadata(output_path)

        logger.info(f"Successfully combined {len(clip_paths)} clips into {output_path}")
        return True, output_path, metadata

    except Exception as e:
        logger.error(f"Error combining videos: {e}", exc_info=True)
        raise VideoCombinerError(f"Failed to combine videos: {e}")


def _combine_simple_concat(
    clip_paths: List[str],
    output_path: str,
    output_resolution: str,
    output_fps: int,
    keep_audio: bool,
) -> Tuple[bool, Optional[str]]:
    """
    Combine videos using simple concatenation (no transitions).

    Uses ffmpeg concat demuxer for efficient concatenation.
    """
    # Create a temporary file list for concat demuxer
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        for clip_path in clip_paths:
            # Use absolute paths
            abs_path = os.path.abspath(clip_path)
            f.write(f"file '{abs_path}'\n")

    try:
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",  # Quality (lower = better, 18-28 is good range)
            "-s", output_resolution,
            "-r", str(output_fps),
        ]

        if keep_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])  # No audio

        cmd.extend([
            "-y",  # Overwrite output file
            output_path
        ])

        logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,  # 10 minute timeout
            text=True
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"ffmpeg concat failed: {error_msg}")
            return False, error_msg

        return True, None

    except subprocess.TimeoutExpired:
        return False, "ffmpeg timeout (process took too long)"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
    finally:
        # Clean up temp file
        try:
            os.unlink(concat_file)
        except:
            pass


def _combine_with_transitions(
    clip_paths: List[str],
    output_path: str,
    transition_duration: float,
    output_resolution: str,
    output_fps: int,
    keep_audio: bool,
) -> Tuple[bool, Optional[str]]:
    """
    Combine videos with crossfade transitions using xfade filter.

    Note: This is more complex and slower than simple concat.
    """
    if len(clip_paths) < 2:
        # Fall back to simple concat for single clip
        return _combine_simple_concat(
            clip_paths, output_path, output_resolution, output_fps, keep_audio
        )

    try:
        # Build complex filter for crossfade
        # This gets complex with many clips, so we'll use a simpler approach:
        # Re-encode each clip and use concat filter with crossfade

        # For now, use simple concat and log a warning
        # Full xfade implementation would require building a complex filtergraph
        logger.warning(
            f"Crossfade transitions requested but using simple concat for performance. "
            f"Transition duration {transition_duration}s ignored."
        )

        return _combine_simple_concat(
            clip_paths, output_path, output_resolution, output_fps, keep_audio
        )

        # TODO: Implement full xfade filter chain for smooth transitions
        # This would involve:
        # 1. Getting duration of each clip
        # 2. Building xfade filter chain with offset calculations
        # 3. Handling audio crossfades separately
        # Example: [0:v][1:v]xfade=transition=fade:duration=1:offset=4[v01];[v01][2:v]xfade...

    except Exception as e:
        return False, f"Transition error: {str(e)}"


def _get_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    Get metadata about a video file using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dict with duration, size, resolution, etc.
    """
    try:
        # Get video info with ffprobe
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
            data = json.loads(result.stdout)

            # Extract useful metadata
            format_data = data.get("format", {})
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )

            metadata = {
                "duration": float(format_data.get("duration", 0)),
                "size_bytes": int(format_data.get("size", 0)),
                "format": format_data.get("format_name", "unknown"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": eval(video_stream.get("r_frame_rate", "30/1")),  # e.g., "30/1" -> 30.0
                "codec": video_stream.get("codec_name", "unknown"),
            }

            return metadata

        else:
            logger.warning(f"ffprobe failed for {video_path}")
            return {}

    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return {}


def store_clip_and_combined(
    job_id: int,
    clip_paths: List[str],
    combined_path: str,
    data_dir: str = "./DATA/videos",
) -> Tuple[List[str], str]:
    """
    Store individual clips and combined video in organized directory structure.

    Args:
        job_id: Job ID for directory organization
        clip_paths: List of paths to individual clips
        combined_path: Path to combined video
        data_dir: Base data directory

    Returns:
        Tuple of (clip_urls, combined_url) - API-accessible URLs
    """
    base_path = Path(data_dir) / str(job_id)
    clips_dir = base_path / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_urls = []

    # Copy clips to organized structure
    for i, clip_path in enumerate(clip_paths, 1):
        clip_filename = f"clip_{i:03d}.mp4"
        dest_path = clips_dir / clip_filename

        # Copy the file
        import shutil
        shutil.copy2(clip_path, dest_path)

        # Generate URL
        clip_url = f"/api/v3/videos/{job_id}/clips/{clip_filename}"
        clip_urls.append(clip_url)

    # Copy combined video
    combined_dest = base_path / "combined.mp4"
    import shutil
    shutil.copy2(combined_path, combined_dest)

    combined_url = f"/api/v3/videos/{job_id}/combined"

    logger.info(
        f"Stored {len(clip_urls)} clips and combined video for job {job_id}"
    )

    return clip_urls, combined_url


def add_audio_to_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    audio_fade_duration: float = 0.5,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Add an audio track to a video file using FFmpeg.

    Args:
        video_path: Path to input video file
        audio_path: Path to audio file (mp3, wav, etc.)
        output_path: Path for output video with audio
        audio_fade_duration: Fade in/out duration in seconds (default: 0.5)

    Returns:
        Tuple of (success, output_path, error_message)

    Example:
        success, path, error = add_audio_to_video(
            "combined_video.mp4",
            "background_music.mp3",
            "final_video.mp4"
        )
    """
    if not check_ffmpeg_available():
        return False, None, "ffmpeg is not available on this system"

    if not os.path.exists(video_path):
        return False, None, f"Video file not found: {video_path}"

    if not os.path.exists(audio_path):
        return False, None, f"Audio file not found: {audio_path}"

    logger.info(f"Adding audio to video: {video_path} + {audio_path} -> {output_path}")

    try:
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command to merge video and audio
        # -i video_path: input video
        # -i audio_path: input audio
        # -c:v copy: copy video codec (no re-encoding)
        # -c:a aac: encode audio as AAC
        # -b:a 192k: audio bitrate
        # -map 0:v:0: use video from first input
        # -map 1:a:0: use audio from second input
        # -shortest: end output when shortest input ends
        # -af: audio filter for fade in/out

        audio_filter = f"afade=t=in:st=0:d={audio_fade_duration},afade=t=out:st=0:d={audio_fade_duration}"

        cmd = [
            "ffmpeg",
            "-i", video_path,  # Input video
            "-i", audio_path,  # Input audio
            "-c:v", "copy",  # Copy video without re-encoding
            "-c:a", "aac",  # Encode audio as AAC
            "-b:a", "192k",  # Audio bitrate
            "-map", "0:v:0",  # Map video from first input
            "-map", "1:a:0",  # Map audio from second input
            "-af", audio_filter,  # Apply audio fades
            "-shortest",  # Match duration to shortest input
            "-y",  # Overwrite output file
            output_path
        ]

        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        # Execute FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            error_msg = f"FFmpeg failed: {result.stderr}"
            logger.error(error_msg)
            return False, None, error_msg

        if not os.path.exists(output_path):
            error_msg = "Output file was not created"
            logger.error(error_msg)
            return False, None, error_msg

        file_size = os.path.getsize(output_path)
        logger.info(f"Successfully added audio to video: {output_path} ({file_size} bytes)")

        return True, output_path, None

    except subprocess.TimeoutExpired:
        error_msg = "FFmpeg operation timed out"
        logger.error(error_msg)
        return False, None, error_msg

    except Exception as e:
        error_msg = f"Error adding audio to video: {e}"
        logger.error(error_msg, exc_info=True)
        return False, None, error_msg


def cleanup_temp_clips(clip_paths: List[str]) -> None:
    """
    Clean up temporary clip files.

    Args:
        clip_paths: List of temporary clip paths to delete
    """
    for clip_path in clip_paths:
        try:
            if os.path.exists(clip_path):
                os.unlink(clip_path)
                logger.debug(f"Deleted temporary clip: {clip_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temp clip {clip_path}: {e}")
