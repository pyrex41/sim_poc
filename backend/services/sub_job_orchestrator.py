"""
Sub-Job Orchestrator Service.

This module orchestrates parallel video generation from image pairs.
It manages the full workflow:
1. Create sub-jobs for each image pair
2. Launch ALL Replicate predictions in parallel (no limit)
3. Poll all predictions concurrently
4. Download completed videos
5. Combine all clips into final video

Designed for maximum parallelism - all sub-jobs run simultaneously.
"""

import logging
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests

from ..config import get_settings
from ..database import (
    create_sub_job,
    update_sub_job_status,
    get_sub_jobs_by_job,
    get_sub_job_progress_summary,
    update_video_status,
    increment_sub_job_retry_count,
)
from .replicate_client import ReplicateClient
from .video_combiner import combine_video_clips, store_clip_and_combined

logger = logging.getLogger(__name__)
settings = get_settings()


class SubJobOrchestratorError(Exception):
    """Exception raised when sub-job orchestration fails."""
    pass


def _round_duration_for_veo3(duration: Optional[float]) -> int:
    """
    Round duration to valid Veo3 value (4, 6, or 8 seconds).

    Args:
        duration: Requested duration in seconds

    Returns:
        Valid duration (4, 6, or 8)
    """
    requested = float(duration) if duration else 8.0

    if requested <= 5.0:
        return 4
    elif requested <= 7.0:
        return 6
    else:
        return 8


async def process_image_pairs_to_videos(
    job_id: int,
    image_pairs: List[Tuple[str, str, float, str]],
    clip_duration: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Process all image pairs into videos in parallel and combine them.

    This is the main entry point for the sub-job orchestration workflow.

    Args:
        job_id: Parent job ID
        image_pairs: List of (image1_id, image2_id, score, reasoning) tuples
        clip_duration: Optional duration for each clip in seconds

    Returns:
        Dict with status and results:
            {
                "success": bool,
                "total_clips": int,
                "successful_clips": int,
                "failed_clips": int,
                "combined_video_url": str or None,
                "clip_urls": List[str],
                "total_cost": float,
                "error": str or None
            }
    """
    logger.info(
        f"Starting sub-job orchestration for job {job_id} with {len(image_pairs)} pairs"
    )

    # Update main job status
    update_video_status(job_id, "sub_job_processing")

    # Determine video generation model from config
    video_model = settings.VIDEO_GENERATION_MODEL

    try:
        # Round duration to valid Veo3 value
        rounded_duration = _round_duration_for_veo3(clip_duration)
        if clip_duration and clip_duration != rounded_duration:
            logger.info(f"Rounded clip duration from {clip_duration}s to {rounded_duration}s for Veo3 compatibility")

        # Step 1: Create all sub-jobs in database with rounded duration
        sub_job_ids = []
        for i, (image1_id, image2_id, score, reasoning) in enumerate(image_pairs, 1):
            sub_job_id = create_sub_job(
                job_id=job_id,
                sub_job_number=i,
                image1_asset_id=image1_id,
                image2_asset_id=image2_id,
                model_id=video_model,
                input_parameters={
                    "duration": rounded_duration,
                    "score": score,
                    "reasoning": reasoning,
                },
            )
            sub_job_ids.append(sub_job_id)

        logger.info(f"Created {len(sub_job_ids)} sub-jobs for job {job_id}")

        # Step 2: Launch ALL video generations in parallel with rounded duration
        results = await _launch_all_sub_jobs(job_id, sub_job_ids, rounded_duration)

        # Step 3: Analyze results
        successful_clips = [r for r in results if r["success"]]
        failed_clips = [r for r in results if not r["success"]]

        logger.info(
            f"Sub-job results: {len(successful_clips)} succeeded, {len(failed_clips)} failed"
        )

        if not successful_clips:
            update_video_status(job_id, "failed")
            return {
                "success": False,
                "total_clips": len(image_pairs),
                "successful_clips": 0,
                "failed_clips": len(failed_clips),
                "combined_video_url": None,
                "clip_urls": [],
                "total_cost": 0.0,
                "error": "All sub-jobs failed",
            }

        # Step 4: Combine successful clips
        update_video_status(job_id, "video_combining")

        clip_paths = [r["clip_path"] for r in successful_clips]
        clip_urls, combined_url, total_cost = await _combine_clips(
            job_id, clip_paths, successful_clips
        )

        # Step 5: Update main job with results
        update_video_status(
            job_id,
            "completed",
            video_url=combined_url,
            metadata={
                "total_clips": len(image_pairs),
                "successful_clips": len(successful_clips),
                "failed_clips": len(failed_clips),
                "clip_urls": clip_urls,
                "total_cost": total_cost,
            },
        )

        logger.info(
            f"Job {job_id} completed successfully. Combined {len(successful_clips)} clips."
        )

        return {
            "success": True,
            "total_clips": len(image_pairs),
            "successful_clips": len(successful_clips),
            "failed_clips": len(failed_clips),
            "combined_video_url": combined_url,
            "clip_urls": clip_urls,
            "total_cost": total_cost,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Sub-job orchestration failed for job {job_id}: {e}", exc_info=True)
        update_video_status(job_id, "failed", metadata={"error": str(e)})
        raise SubJobOrchestratorError(f"Orchestration failed: {e}")


async def _launch_all_sub_jobs(
    job_id: int, sub_job_ids: List[str], clip_duration: Optional[float]
) -> List[Dict[str, Any]]:
    """
    Launch ALL sub-jobs in parallel (no concurrency limit).

    Args:
        job_id: Parent job ID
        sub_job_ids: List of sub-job IDs to process
        clip_duration: Optional clip duration

    Returns:
        List of result dicts for each sub-job
    """
    logger.info(f"Launching {len(sub_job_ids)} sub-jobs in FULL PARALLEL mode")

    # Create tasks for all sub-jobs
    tasks = [
        _process_single_sub_job(job_id, sub_job_id, clip_duration)
        for sub_job_id in sub_job_ids
    ]

    # Run all tasks concurrently (asyncio.gather runs them in parallel)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Sub-job {sub_job_ids[i]} raised exception: {result}")
            processed_results.append({
                "success": False,
                "sub_job_id": sub_job_ids[i],
                "error": str(result),
                "clip_path": None,
                "cost": 0.0,
            })
        else:
            processed_results.append(result)

    return processed_results


async def _process_single_sub_job(
    job_id: int, sub_job_id: str, clip_duration: Optional[float]
) -> Dict[str, Any]:
    """
    Process a single sub-job: get asset URLs, generate video, download, update status.

    Args:
        job_id: Parent job ID
        sub_job_id: Sub-job ID to process
        clip_duration: Optional clip duration

    Returns:
        Dict with success, clip_path, cost, etc.
    """
    from ..database import get_sub_job_by_id
    from ..database_helpers import get_asset_by_id

    try:
        # Get sub-job details
        sub_job = get_sub_job_by_id(sub_job_id)
        if not sub_job:
            raise ValueError(f"Sub-job {sub_job_id} not found")

        logger.info(
            f"Processing sub-job {sub_job_id} ({sub_job['subJobNumber']}) for job {job_id}"
        )

        # Get asset URLs
        image1 = get_asset_by_id(sub_job["image1AssetId"])
        image2 = get_asset_by_id(sub_job["image2AssetId"])

        if not image1 or not image2:
            raise ValueError(f"Assets not found for sub-job {sub_job_id}")

        # Construct full asset URLs - use NGROK_URL for external services like Replicate
        current_settings = get_settings()
        # Use NGROK_URL if available, otherwise fall back to BASE_URL
        external_url = current_settings.NGROK_URL or current_settings.BASE_URL
        image1_url = f"{external_url}{image1.url}" if not image1.url.startswith('http') else image1.url
        image2_url = f"{external_url}{image2.url}" if not image2.url.startswith('http') else image2.url

        # Debug: Log URLs being sent to Replicate
        logger.error(f"[DEBUG ORCHESTRATOR] NGROK_URL: {current_settings.NGROK_URL}")
        logger.error(f"[DEBUG ORCHESTRATOR] BASE_URL: {current_settings.BASE_URL}")
        logger.error(f"[DEBUG ORCHESTRATOR] Using external_url: {external_url}")
        logger.error(f"[DEBUG ORCHESTRATOR] Image1 URL: {image1_url}")
        logger.error(f"[DEBUG ORCHESTRATOR] Image2 URL: {image2_url}")
        logger.error(f"[DEBUG ORCHESTRATOR] Model: {sub_job['modelId']}, Duration: {clip_duration}")

        # Update status to processing
        update_sub_job_status(sub_job_id, "processing")

        # Generate video using Replicate
        replicate_client = ReplicateClient()
        result = await asyncio.to_thread(
            replicate_client.generate_video_from_pair,
            image1_url,
            image2_url,
            model=sub_job["modelId"],
            duration=clip_duration,
        )

        if not result["success"]:
            # Mark as failed
            update_sub_job_status(
                sub_job_id,
                "failed",
                error_message=result.get("error", "Unknown error"),
            )
            return {
                "success": False,
                "sub_job_id": sub_job_id,
                "error": result.get("error"),
                "clip_path": None,
                "cost": 0.0,
            }

        # Download the generated video
        video_url = result["video_url"]
        clip_path = await _download_video(job_id, sub_job["subJobNumber"], video_url)

        # Calculate cost (estimate based on duration)
        duration = result.get("duration_seconds", clip_duration or 6)
        if sub_job["modelId"] == "veo3":
            cost = duration * ReplicateClient.VEO3_PRICE_PER_SECOND
        else:  # hailuo-2.0
            cost = ReplicateClient.HAILUO2_PRICE_PER_GENERATION

        # Update sub-job as completed
        update_sub_job_status(
            sub_job_id,
            "completed",
            replicate_prediction_id=result.get("prediction_id"),
            video_url=video_url,
            duration_seconds=duration,
            actual_cost=cost,
            progress=1.0,
        )

        logger.info(f"Sub-job {sub_job_id} completed successfully")

        return {
            "success": True,
            "sub_job_id": sub_job_id,
            "clip_path": clip_path,
            "video_url": video_url,
            "cost": cost,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error processing sub-job {sub_job_id}: {e}", exc_info=True)
        update_sub_job_status(sub_job_id, "failed", error_message=str(e))
        return {
            "success": False,
            "sub_job_id": sub_job_id,
            "error": str(e),
            "clip_path": None,
            "cost": 0.0,
        }


async def _download_video(job_id: int, clip_number: int, video_url: str) -> str:
    """
    Download a video from URL to temp file.

    Args:
        job_id: Job ID for naming
        clip_number: Clip number for naming
        video_url: URL to download from

    Returns:
        Path to downloaded file
    """
    # Create temp file
    temp_dir = Path(tempfile.gettempdir()) / f"job_{job_id}"
    temp_dir.mkdir(exist_ok=True)

    temp_path = temp_dir / f"clip_{clip_number:03d}.mp4"

    logger.info(f"Downloading video from {video_url} to {temp_path}")

    # Download with streaming
    response = await asyncio.to_thread(
        requests.get, video_url, stream=True, timeout=300
    )
    response.raise_for_status()

    # Write to file
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Downloaded video to {temp_path} ({temp_path.stat().st_size} bytes)")

    return str(temp_path)


async def _combine_clips(
    job_id: int, clip_paths: List[str], clip_results: List[Dict[str, Any]]
) -> Tuple[List[str], str, float]:
    """
    Combine all clips into final video.

    Args:
        job_id: Job ID
        clip_paths: Paths to individual clips
        clip_results: Results from sub-job processing (for cost calculation)

    Returns:
        Tuple of (clip_urls, combined_url, total_cost)
    """
    logger.info(f"Combining {len(clip_paths)} clips for job {job_id}")

    # Create temp output path
    temp_dir = Path(tempfile.gettempdir()) / f"job_{job_id}"
    combined_temp_path = temp_dir / "combined.mp4"

    # Combine videos
    success, output_path, metadata = await asyncio.to_thread(
        combine_video_clips,
        clip_paths,
        str(combined_temp_path),
        transition_duration=0.0,  # No transitions for now
        output_resolution="1920x1080",
        output_fps=30,
        keep_audio=False,
    )

    if not success:
        raise SubJobOrchestratorError("Failed to combine video clips")

    # Store clips and combined video in organized structure
    clip_urls, combined_url = await asyncio.to_thread(
        store_clip_and_combined,
        job_id,
        clip_paths,
        str(combined_temp_path),
        data_dir=settings.VIDEO_STORAGE_PATH,
    )

    # Calculate total cost
    total_cost = sum(r.get("cost", 0.0) for r in clip_results)

    logger.info(
        f"Combined video created: {combined_url}, total cost: ${total_cost:.2f}"
    )

    return clip_urls, combined_url, total_cost
