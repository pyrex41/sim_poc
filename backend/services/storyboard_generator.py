"""
Storyboard Generation Background Task.

This module handles the background task for generating a storyboard (scene breakdown
and images) from a user's video prompt. It orchestrates:
1. Prompt parsing into scenes
2. Image generation for each scene
3. Progress tracking
4. Error handling and retries
"""

import logging
import time
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.video_generation import Scene, StoryboardEntry, VideoStatus, VideoProgress
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
MAX_RETRIES = 3
PARSING_TIMEOUT = 30  # seconds
IMAGE_GENERATION_TIMEOUT = 120  # seconds per image
DEFAULT_SCENE_DURATION = 5.0  # seconds per scene


def generate_storyboard_task(job_id: int) -> None:
    """
    Main background task to generate storyboard from video prompt.

    This function orchestrates the entire storyboard generation workflow:
    1. Fetches job from database
    2. Updates status to 'parsing'
    3. Parses prompt into scenes
    4. Generates images for each scene
    5. Updates progress after each image
    6. Stores storyboard data in database
    7. Updates status to 'storyboard_ready'

    Args:
        job_id: The video generation job ID

    Error Handling:
        - Marks job as failed on critical errors
        - Implements retry logic for transient failures
        - Logs all errors for debugging
    """
    logger.info(f"Starting storyboard generation for job {job_id}")

    try:
        # 1. Fetch job from database
        job = get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        prompt = job.get("prompt", "")
        parameters = job.get("parameters", {})
        duration = parameters.get("duration", 30)
        style = parameters.get("style")
        aspect_ratio = parameters.get("aspect_ratio", "16:9")

        logger.info(f"Job {job_id}: prompt='{prompt[:50]}...', duration={duration}s")

        # 2. Update status to 'parsing'
        _update_status(job_id, VideoStatus.PARSING, "Parsing prompt into scenes...")

        # 3. Parse prompt into scenes
        logger.info(f"Job {job_id}: Parsing prompt into scenes")
        start_time = time.time()

        try:
            scenes = parse_prompt_to_scenes(prompt, duration, style)
            parse_duration = time.time() - start_time

            if parse_duration > PARSING_TIMEOUT:
                logger.warning(f"Job {job_id}: Parsing took {parse_duration:.1f}s (timeout: {PARSING_TIMEOUT}s)")

            logger.info(f"Job {job_id}: Parsed into {len(scenes)} scenes")
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to parse prompt: {e}")
            mark_job_failed(job_id, f"Failed to parse prompt: {str(e)}")
            return

        # 4. Update status to 'generating_storyboard'
        _update_status(
            job_id,
            VideoStatus.GENERATING_STORYBOARD,
            f"Generating images for {len(scenes)} scenes..."
        )

        # Initialize storyboard entries
        storyboard: List[StoryboardEntry] = []
        for scene in scenes:
            storyboard.append(StoryboardEntry(
                scene=scene,
                image_url=None,
                generation_status="pending",
                error=None
            ))

        # 5. Generate images for each scene with progress tracking
        image_start_times: List[float] = []
        replicate_client = ReplicateClient()

        for idx, entry in enumerate(storyboard):
            scene_num = idx + 1
            logger.info(f"Job {job_id}: Generating image for scene {scene_num}/{len(scenes)}")

            # Update progress
            _update_progress(
                job_id,
                current_stage=VideoStatus.GENERATING_STORYBOARD,
                scenes_total=len(scenes),
                scenes_completed=idx,
                current_scene=scene_num,
                image_start_times=image_start_times,
                message=f"Generating image for scene {scene_num}/{len(scenes)}"
            )

            # Mark scene as generating
            entry.generation_status = "generating"
            _save_storyboard(job_id, storyboard)

            # Generate image with retry logic
            image_result = _generate_image_with_retry(
                replicate_client,
                entry.scene.image_prompt,
                job_id,
                scene_num,
                max_retries=MAX_RETRIES
            )

            # Track generation time
            if image_result.get("success"):
                if len(image_start_times) > 0:
                    # Calculate actual generation time
                    gen_time = time.time() - max(image_start_times)
                    image_start_times.append(gen_time)
                else:
                    # First image, use default estimate
                    image_start_times.append(IMAGE_GENERATION_TIMEOUT / 2)

            # Update storyboard entry
            if image_result.get("success"):
                entry.image_url = image_result.get("image_url")
                entry.generation_status = "completed"
                entry.error = None
                logger.info(f"Job {job_id}: Scene {scene_num} completed - {entry.image_url}")
            else:
                entry.generation_status = "failed"
                entry.error = image_result.get("error", "Unknown error")[:500]  # Truncate to 500 chars
                logger.error(f"Job {job_id}: Scene {scene_num} failed - {entry.error}")

            # Save updated storyboard after each image
            _save_storyboard(job_id, storyboard)

        # 6. Check if all images were generated successfully
        failed_scenes = [e for e in storyboard if e.generation_status == "failed"]
        completed_scenes = [e for e in storyboard if e.generation_status == "completed"]

        logger.info(
            f"Job {job_id}: Storyboard generation complete - "
            f"{len(completed_scenes)} successful, {len(failed_scenes)} failed"
        )

        # 7. Update final status
        if len(failed_scenes) == len(scenes):
            # All scenes failed
            mark_job_failed(job_id, "All scene images failed to generate")
        elif len(failed_scenes) > 0:
            # Partial failure - still mark as storyboard_ready but with warnings
            _update_status(
                job_id,
                VideoStatus.STORYBOARD_READY,
                f"Storyboard ready ({len(failed_scenes)} scenes failed)"
            )
        else:
            # Complete success
            _update_status(
                job_id,
                VideoStatus.STORYBOARD_READY,
                "Storyboard complete, awaiting approval"
            )

        logger.info(f"Job {job_id}: Storyboard generation task completed")

    except Exception as e:
        logger.exception(f"Job {job_id}: Unexpected error in storyboard generation")
        mark_job_failed(job_id, f"Unexpected error: {str(e)}")


def parse_prompt_to_scenes(
    prompt: str,
    duration: int,
    style: Optional[str] = None
) -> List[Scene]:
    """
    Parse a video prompt into a list of scenes.

    This function breaks down the video prompt into individual scenes with
    descriptions and image generation prompts. It uses a simple rule-based
    approach that can be enhanced with LLM-based parsing later.

    Args:
        prompt: The user's video concept description
        duration: Total video duration in seconds
        style: Optional visual style (e.g., 'cinematic', 'cartoon')

    Returns:
        List of Scene objects with scene_number, description, duration, and image_prompt

    Algorithm:
        1. Determine number of scenes based on duration (1 scene per 5 seconds)
        2. Distribute duration evenly across scenes
        3. Generate scene descriptions and image prompts
        4. Apply style modifiers if specified
    """
    # Determine number of scenes (1 scene per 5 seconds, min 3, max 10)
    num_scenes = max(3, min(10, int(duration / 5)))
    scene_duration = duration / num_scenes

    logger.info(f"Parsing prompt into {num_scenes} scenes ({scene_duration:.1f}s each)")

    scenes: List[Scene] = []

    # Simple rule-based scene generation
    # This can be enhanced with LLM-based parsing in the future
    for i in range(num_scenes):
        scene_num = i + 1

        # Determine scene purpose based on position
        if scene_num == 1:
            purpose = "Opening/Hook"
            scene_desc = f"Opening scene: {prompt[:100]}"
            image_prompt = f"Opening establishing shot, {prompt[:150]}"
        elif scene_num == num_scenes:
            purpose = "Closing/CTA"
            scene_desc = f"Closing scene with call to action"
            image_prompt = f"Closing shot, final moment, {prompt[:150]}"
        elif scene_num == 2:
            purpose = "Context/Setup"
            scene_desc = f"Setting up context for: {prompt[:100]}"
            image_prompt = f"Context establishing shot, {prompt[:150]}"
        else:
            purpose = f"Scene {scene_num}"
            scene_desc = f"Scene {scene_num}: {prompt[:100]}"
            image_prompt = f"Scene {scene_num}, {prompt[:150]}"

        # Apply style modifiers to image prompt
        if style:
            image_prompt = f"{image_prompt}, {style} style"

        # Add cinematic quality descriptors
        image_prompt = f"{image_prompt}, high quality, professional cinematography"

        scenes.append(Scene(
            scene_number=scene_num,
            description=scene_desc,
            duration=round(scene_duration, 2),
            image_prompt=image_prompt[:2000]  # Truncate to max length
        ))

    return scenes


def _generate_image_with_retry(
    client: ReplicateClient,
    prompt: str,
    job_id: int,
    scene_num: int,
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
    """
    Generate an image with retry logic for transient failures.

    Args:
        client: ReplicateClient instance
        prompt: Image generation prompt
        job_id: Job ID for logging
        scene_num: Scene number for logging
        max_retries: Maximum number of retry attempts

    Returns:
        Dict with 'success', 'image_url', and 'error' keys
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Job {job_id}, Scene {scene_num}: Image generation attempt {attempt + 1}/{max_retries}")

            result = client.generate_image(prompt)

            if result.get("success"):
                logger.info(f"Job {job_id}, Scene {scene_num}: Image generated successfully")
                return result
            else:
                error = result.get("error", "Unknown error")
                logger.warning(f"Job {job_id}, Scene {scene_num}: Attempt {attempt + 1} failed - {error}")

                # Check if we should retry
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    backoff_delay = 2 ** (attempt + 1)
                    logger.info(f"Job {job_id}, Scene {scene_num}: Retrying in {backoff_delay}s...")
                    time.sleep(backoff_delay)
                else:
                    # All retries exhausted
                    logger.error(f"Job {job_id}, Scene {scene_num}: All retries exhausted")
                    return result

        except Exception as e:
            logger.error(f"Job {job_id}, Scene {scene_num}: Attempt {attempt + 1} exception - {e}")

            if attempt < max_retries - 1:
                backoff_delay = 2 ** (attempt + 1)
                logger.info(f"Job {job_id}, Scene {scene_num}: Retrying after exception in {backoff_delay}s...")
                time.sleep(backoff_delay)
            else:
                return {
                    "success": False,
                    "image_url": None,
                    "error": f"Exception after {max_retries} retries: {str(e)}"
                }

    # Should not reach here, but just in case
    return {
        "success": False,
        "image_url": None,
        "error": "Max retries exceeded"
    }


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
    scenes_total: int,
    scenes_completed: int,
    current_scene: Optional[int] = None,
    image_start_times: Optional[List[float]] = None,
    message: Optional[str] = None
) -> None:
    """
    Update job progress with detailed tracking information.

    Args:
        job_id: Job ID
        current_stage: Current VideoStatus
        scenes_total: Total number of scenes
        scenes_completed: Number of completed scenes
        current_scene: Currently processing scene number
        image_start_times: List of image generation times for ETA estimation
        message: Optional progress message
    """
    # Estimate completion time
    estimated_seconds = None
    if image_start_times and len(image_start_times) > 0:
        # Calculate average generation time
        avg_time = sum(image_start_times) / len(image_start_times)
        remaining_scenes = scenes_total - scenes_completed
        estimated_seconds = int(avg_time * remaining_scenes)

    progress = VideoProgress(
        current_stage=current_stage,
        scenes_total=scenes_total,
        scenes_completed=scenes_completed,
        current_scene=current_scene,
        estimated_completion_seconds=estimated_seconds,
        message=message
    )

    try:
        update_job_progress(job_id, progress.model_dump())
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to update progress - {e}")


def _save_storyboard(job_id: int, storyboard: List[StoryboardEntry]) -> None:
    """
    Save storyboard data to database as JSON.

    Args:
        job_id: Job ID
        storyboard: List of StoryboardEntry objects
    """
    try:
        # Convert storyboard to JSON-serializable format
        storyboard_data = [entry.model_dump() for entry in storyboard]

        with get_db() as conn:
            conn.execute(
                "UPDATE generated_videos SET storyboard_data = ? WHERE id = ?",
                (json.dumps(storyboard_data), job_id)
            )
            conn.commit()

        logger.debug(f"Job {job_id}: Storyboard data saved")
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to save storyboard - {e}")
