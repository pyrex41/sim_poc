"""
Video Rendering Background Task.

This module handles the background task for rendering the final video from an approved
storyboard using the Replicate API. It orchestrates:
1. Extracting image URLs from storyboard
2. Generating video from images using Replicate
3. Downloading and saving the video
4. Progress tracking and cost calculation
5. Error handling with retry logic
"""

import logging
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.video_generation import VideoStatus, VideoProgress
from ..services.replicate_client import ReplicateClient
from ..database import (
    get_job,
    update_job_progress,
    mark_job_failed,
    increment_retry_count,
    get_db
)

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 2  # Max 2 retries for video rendering
TIMEOUT = 600  # 10 minutes timeout for video rendering
EXPONENTIAL_BACKOFF_BASE = 30  # 30s, 90s for retries
COST_VARIANCE_THRESHOLD = 1.2  # Log if actual cost > estimated * 1.2


def render_video_task(job_id: int) -> None:
    """
    Main background task to render video from approved storyboard.

    This function orchestrates the complete video rendering workflow:
    1. Fetches job from database
    2. Validates storyboard is approved
    3. Extracts image URLs from storyboard
    4. Calls Replicate API to generate video
    5. Polls for video completion
    6. Downloads and saves video locally
    7. Updates job with video URL
    8. Calculates and stores actual cost
    9. Updates status to 'completed'

    Args:
        job_id: The video generation job ID

    Error Handling:
        - Marks job as failed on critical errors
        - Implements retry logic with exponential backoff (30s, 90s)
        - Tracks retry attempts
        - Updates progress throughout the process
    """
    logger.info(f"Starting video rendering for job {job_id}")

    try:
        # 1. Fetch job from database
        job = get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # 2. Validate storyboard is approved
        if not job.get("approved"):
            logger.error(f"Job {job_id}: Storyboard not approved, cannot render video")
            mark_job_failed(job_id, "Storyboard must be approved before rendering video")
            return

        # 3. Validate storyboard_data exists and has images
        storyboard_data = job.get("storyboard_data")
        if not storyboard_data:
            logger.error(f"Job {job_id}: No storyboard data found")
            mark_job_failed(job_id, "No storyboard data available")
            return

        # Parse storyboard data (it's stored as JSON string)
        import json
        if isinstance(storyboard_data, str):
            storyboard_data = json.loads(storyboard_data)

        if not isinstance(storyboard_data, list) or len(storyboard_data) == 0:
            logger.error(f"Job {job_id}: Storyboard data is empty or invalid")
            mark_job_failed(job_id, "Storyboard data is empty or invalid")
            return

        # 4. Extract image URLs from storyboard
        logger.info(f"Job {job_id}: Extracting image URLs from storyboard")
        image_urls = []
        for idx, entry in enumerate(storyboard_data):
            image_url = entry.get("image_url")
            if not image_url:
                logger.error(f"Job {job_id}: Scene {idx + 1} is missing image_url")
                mark_job_failed(job_id, f"Scene {idx + 1} is missing generated image")
                return
            image_urls.append(image_url)

        logger.info(f"Job {job_id}: Extracted {len(image_urls)} image URLs")

        # 5. Update status to 'rendering'
        _update_status(job_id, VideoStatus.RENDERING, "Rendering video from images...")

        # 6. Generate video with retry logic
        video_result = _render_video_with_retry(
            job_id,
            image_urls,
            max_retries=MAX_RETRIES
        )

        if not video_result.get("success"):
            error_msg = video_result.get("error", "Video rendering failed")
            logger.error(f"Job {job_id}: Video rendering failed - {error_msg}")
            mark_job_failed(job_id, error_msg)
            return

        video_url = video_result.get("video_url")
        duration_seconds = video_result.get("duration_seconds", 0)

        logger.info(f"Job {job_id}: Video rendered successfully - {video_url}")

        # 7. Download and save video
        _update_progress(
            job_id,
            current_stage=VideoStatus.RENDERING,
            message="Downloading video..."
        )

        try:
            local_video_path = download_video(video_url, job_id)
            logger.info(f"Job {job_id}: Video downloaded to {local_video_path}")
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to download video - {e}")
            mark_job_failed(job_id, f"Failed to download video: {str(e)}")
            return

        # 8. Calculate actual cost
        actual_cost = _calculate_actual_cost(len(image_urls), duration_seconds)
        estimated_cost = job.get("estimated_cost", 0.0)

        # Log variance if actual cost significantly exceeds estimate
        if actual_cost > estimated_cost * COST_VARIANCE_THRESHOLD:
            variance_pct = ((actual_cost - estimated_cost) / estimated_cost) * 100
            logger.warning(
                f"Job {job_id}: Actual cost ${actual_cost:.2f} exceeds estimate "
                f"${estimated_cost:.2f} by {variance_pct:.1f}%"
            )

        logger.info(
            f"Job {job_id}: Cost - Estimated: ${estimated_cost:.2f}, "
            f"Actual: ${actual_cost:.2f}"
        )

        # 9. Update job with video URL and cost
        _update_status(job_id, VideoStatus.RENDERING, "Finalizing...")

        with get_db() as conn:
            conn.execute(
                """
                UPDATE generated_videos
                SET video_url = ?, actual_cost = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (local_video_path, actual_cost, job_id)
            )
            conn.commit()

        # 10. Update final progress
        _update_progress(
            job_id,
            current_stage=VideoStatus.COMPLETED,
            message="Video rendering complete!"
        )

        logger.info(f"Job {job_id}: Video rendering task completed successfully")

    except Exception as e:
        logger.exception(f"Job {job_id}: Unexpected error in video rendering")
        mark_job_failed(job_id, f"Unexpected error: {str(e)}")


def _render_video_with_retry(
    job_id: int,
    image_urls: list[str],
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
    """
    Generate video with retry logic and exponential backoff.

    Args:
        job_id: Job ID for logging and retry tracking
        image_urls: List of image URLs to stitch into video
        max_retries: Maximum number of retry attempts

    Returns:
        Dict with 'success', 'video_url', 'duration_seconds', and 'error' keys
    """
    replicate_client = ReplicateClient()

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Job {job_id}: Video rendering attempt {attempt + 1}/{max_retries + 1}"
            )

            # Update progress
            _update_progress(
                job_id,
                current_stage=VideoStatus.RENDERING,
                message=f"Rendering video (attempt {attempt + 1})..."
            )

            # Call Replicate API
            result = replicate_client.generate_video(image_urls)

            if result.get("success"):
                logger.info(f"Job {job_id}: Video rendering succeeded")
                return result
            else:
                error = result.get("error", "Unknown error")
                logger.warning(
                    f"Job {job_id}: Rendering attempt {attempt + 1} failed - {error}"
                )

                # Check if we should retry
                if attempt < max_retries:
                    # Exponential backoff: 30s, 90s
                    backoff_delay = EXPONENTIAL_BACKOFF_BASE * (3 ** attempt)
                    logger.info(
                        f"Job {job_id}: Retrying in {backoff_delay}s..."
                    )

                    # Track retry count in database
                    increment_retry_count(job_id)

                    # Update progress with retry info
                    _update_progress(
                        job_id,
                        current_stage=VideoStatus.RENDERING,
                        message=f"Retrying in {backoff_delay}s (attempt {attempt + 2}/{max_retries + 1})..."
                    )

                    time.sleep(backoff_delay)
                else:
                    # All retries exhausted
                    logger.error(f"Job {job_id}: All rendering retries exhausted")
                    return result

        except Exception as e:
            logger.error(
                f"Job {job_id}: Rendering attempt {attempt + 1} exception - {e}"
            )

            if attempt < max_retries:
                backoff_delay = EXPONENTIAL_BACKOFF_BASE * (3 ** attempt)
                logger.info(
                    f"Job {job_id}: Retrying after exception in {backoff_delay}s..."
                )

                increment_retry_count(job_id)

                _update_progress(
                    job_id,
                    current_stage=VideoStatus.RENDERING,
                    message=f"Retrying after error in {backoff_delay}s..."
                )

                time.sleep(backoff_delay)
            else:
                return {
                    "success": False,
                    "video_url": None,
                    "error": f"Exception after {max_retries + 1} attempts: {str(e)}",
                    "duration_seconds": 0
                }

    # Should not reach here, but just in case
    return {
        "success": False,
        "video_url": None,
        "error": "Max retries exceeded",
        "duration_seconds": 0
    }


def download_video(video_url: str, job_id: int) -> str:
    """
    Download video from Replicate and save to local storage.

    This function:
    1. Creates storage directory: DATA/videos/{job_id}/
    2. Downloads video with streaming
    3. Validates video format using magic bytes
    4. Saves video as final.mp4
    5. Returns local file path

    Args:
        video_url: URL of the video to download
        job_id: Job ID for storage organization

    Returns:
        Local file path to the downloaded video

    Raises:
        ValueError: If video validation fails
        requests.RequestException: If download fails
    """
    logger.info(f"Job {job_id}: Downloading video from {video_url}")

    # Create job-specific video directory
    video_dir = Path(__file__).parent.parent / "DATA" / "videos" / str(job_id)
    video_dir.mkdir(parents=True, exist_ok=True)

    # Save as final.mp4
    video_path = video_dir / "final.mp4"

    try:
        # Download with timeout and streaming
        response = requests.get(video_url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()

        # Write to temporary file first
        temp_path = video_path.with_suffix(".tmp")
        bytes_downloaded = 0

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)

        # Validate download
        if bytes_downloaded == 0:
            raise ValueError("Downloaded file is empty (0 bytes)")

        if bytes_downloaded < 1024:  # Less than 1KB is suspicious
            raise ValueError(f"Downloaded file is too small ({bytes_downloaded} bytes)")

        # Validate file is a video by checking magic bytes
        with open(temp_path, 'rb') as f:
            header = f.read(12)
            is_video = False

            # Check common video file signatures
            if header.startswith(b'\x00\x00\x00\x18ftypmp4') or \
               header.startswith(b'\x00\x00\x00\x1cftypisom') or \
               header.startswith(b'\x00\x00\x00\x14ftyp') or \
               header[4:8] == b'ftyp':  # Generic MP4/MOV
                is_video = True
            elif header.startswith(b'RIFF') and header[8:12] == b'AVI ':  # AVI
                is_video = True
            elif header.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/MKV
                is_video = True

            if not is_video:
                raise ValueError(
                    f"Downloaded file does not appear to be a valid video "
                    f"(header: {header.hex()})"
                )

        # Move from temp to final location
        temp_path.replace(video_path)

        logger.info(
            f"Job {job_id}: Video downloaded successfully "
            f"({bytes_downloaded} bytes) to {video_path}"
        )

        # Return relative path from backend directory
        return f"/api/videos/{job_id}/data"

    except requests.exceptions.Timeout:
        logger.error(f"Job {job_id}: Video download timeout")
        raise ValueError(f"Video download timeout after {TIMEOUT} seconds")

    except requests.exceptions.RequestException as e:
        logger.error(f"Job {job_id}: Network error during video download - {e}")
        raise ValueError(f"Network error during video download: {str(e)}")

    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error during video download - {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise


def _calculate_actual_cost(num_images: int, video_duration: int) -> float:
    """
    Calculate actual cost from Replicate API usage.

    Uses the same pricing as ReplicateClient:
    - Flux-Schnell: $0.003 per image
    - SkyReels-2: $0.10 per second of video

    Args:
        num_images: Number of images generated
        video_duration: Duration of video in seconds

    Returns:
        Total actual cost in USD
    """
    # Import pricing from ReplicateClient
    image_cost = num_images * ReplicateClient.FLUX_SCHNELL_PRICE_PER_IMAGE
    video_cost = video_duration * ReplicateClient.SKYREELS2_PRICE_PER_SECOND
    total_cost = image_cost + video_cost

    logger.debug(
        f"Cost calculation - Images: {num_images} x ${ReplicateClient.FLUX_SCHNELL_PRICE_PER_IMAGE} = ${image_cost:.3f}, "
        f"Video: {video_duration}s x ${ReplicateClient.SKYREELS2_PRICE_PER_SECOND} = ${video_cost:.2f}, "
        f"Total: ${total_cost:.2f}"
    )

    return round(total_cost, 2)


def _update_status(job_id: int, status: VideoStatus, message: str) -> None:
    """
    Update job status and progress message.

    Args:
        job_id: Job ID
        status: New VideoStatus
        message: Progress message
    """
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE generated_videos SET status = ? WHERE id = ?",
                (status.value, job_id)
            )
            conn.commit()

        # Update progress
        update_job_progress(job_id, {
            "current_stage": status.value,
            "message": message
        })

        logger.info(f"Job {job_id}: Status updated to {status.value}")
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to update status - {e}")


def _update_progress(
    job_id: int,
    current_stage: VideoStatus,
    message: Optional[str] = None
) -> None:
    """
    Update job progress with detailed tracking information.

    Args:
        job_id: Job ID
        current_stage: Current VideoStatus
        message: Optional progress message
    """
    progress = VideoProgress(
        current_stage=current_stage,
        scenes_total=0,
        scenes_completed=0,
        current_scene=None,
        estimated_completion_seconds=None,
        message=message
    )

    try:
        update_job_progress(job_id, progress.model_dump())
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to update progress - {e}")
