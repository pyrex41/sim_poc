"""
Luigi workflow runner for FastAPI integration.

Provides utilities for running Luigi workflows from FastAPI endpoints
and monitoring their progress.
"""

import luigi
import logging
import asyncio
import subprocess
import json
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .campaign_pipeline import CampaignPipelineWorkflow

logger = logging.getLogger(__name__)

# Thread pool for running Luigi workflows
_luigi_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="luigi")


def run_pipeline_sync(
    job_id: int,
    campaign_id: str,
    clip_duration: Optional[float] = None,
    num_pairs: Optional[int] = None,
    workers: int = 10,
    use_local_scheduler: bool = True,  # No separate daemon needed
) -> Dict[str, Any]:
    """
    Run the campaign pipeline workflow synchronously via subprocess.

    This runs Luigi as a separate process to avoid signal handler conflicts
    when called from FastAPI background tasks.

    Args:
        job_id: Parent job ID
        campaign_id: Campaign ID
        clip_duration: Optional clip duration in seconds
        num_pairs: Optional target number of image pairs
        workers: Number of Luigi workers (default: 10)
        use_local_scheduler: Use local scheduler instead of central (default: False)

    Returns:
        Dict with success status and details
    """
    logger.info(
        f"Starting Luigi pipeline for job {job_id}, campaign {campaign_id}"
    )

    try:
        # Build Luigi command-line arguments
        cmd = [
            "python", "-m", "luigi",
            "--module", "backend.workflows.campaign_pipeline",
            "CampaignPipelineWorkflow",
            "--job-id", str(job_id),
            "--campaign-id", campaign_id,
            "--workers", str(workers),
        ]

        if clip_duration is not None:
            cmd.extend(["--clip-duration", str(clip_duration)])

        if num_pairs is not None:
            cmd.extend(["--num-pairs", str(num_pairs)])

        if use_local_scheduler:
            cmd.append("--local-scheduler")

        # Run Luigi as subprocess
        logger.info(f"Running Luigi command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hours timeout for large campaigns
        )

        if result.returncode == 0:
            logger.info(f"Luigi pipeline completed successfully for job {job_id}")
            logger.debug(f"Luigi stdout: {result.stdout}")
            return {
                "success": True,
                "job_id": job_id,
                "message": "Pipeline completed successfully",
            }
        else:
            logger.error(f"Luigi pipeline failed for job {job_id}")
            logger.error(f"Luigi stderr: {result.stderr}")
            logger.error(f"Luigi stdout: {result.stdout}")
            return {
                "success": False,
                "job_id": job_id,
                "message": f"Pipeline failed with exit code {result.returncode}",
                "error": result.stderr,
            }

    except subprocess.TimeoutExpired:
        logger.error(f"Luigi pipeline timed out for job {job_id}")
        return {
            "success": False,
            "job_id": job_id,
            "error": "Pipeline execution timed out after 1 hour",
        }
    except Exception as e:
        logger.error(f"Error running Luigi pipeline for job {job_id}: {e}", exc_info=True)
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
        }


async def run_pipeline_async(
    job_id: int,
    campaign_id: str,
    clip_duration: Optional[float] = None,
    num_pairs: Optional[int] = None,
    workers: int = 10,
    use_local_scheduler: bool = True,  # No separate daemon needed
) -> Dict[str, Any]:
    """
    Run the campaign pipeline workflow asynchronously.

    This is the recommended way to run Luigi workflows from FastAPI.
    It runs the workflow in a thread pool so it doesn't block the event loop.

    Args:
        job_id: Parent job ID
        campaign_id: Campaign ID
        clip_duration: Optional clip duration in seconds
        num_pairs: Optional target number of image pairs
        workers: Number of Luigi workers (default: 10)
        use_local_scheduler: Use local scheduler instead of central (default: False)

    Returns:
        Dict with success status and details
    """
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        _luigi_executor,
        run_pipeline_sync,
        job_id,
        campaign_id,
        clip_duration,
        num_pairs,
        workers,
        use_local_scheduler,
    )

    return result


def get_pipeline_status(job_id: int) -> Dict[str, Any]:
    """
    Get the current status of a Luigi pipeline.

    Queries the database for Luigi task states and computes overall progress.

    Args:
        job_id: Job ID to check

    Returns:
        Dict with pipeline status information
    """
    from ..database import get_db

    try:
        with get_db() as conn:
            # Get all task states for this job
            rows = conn.execute(
                """
                SELECT task_name, status, created_at, completed_at, output_data
                FROM luigi_task_state
                WHERE job_id = ?
                ORDER BY created_at ASC
                """,
                (job_id,),
            ).fetchall()

            if not rows:
                return {
                    "job_id": job_id,
                    "status": "not_started",
                    "tasks": [],
                    "progress": 0.0,
                }

            # Process task states
            tasks = []
            completed_count = 0
            total_count = len(rows)

            for row in rows:
                task_info = {
                    "name": row["task_name"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "completed_at": row["completed_at"],
                }

                if row["status"] == "completed":
                    completed_count += 1

                tasks.append(task_info)

            # Compute overall status
            if completed_count == total_count:
                overall_status = "completed"
            elif any(t["status"] == "failed" for t in tasks):
                overall_status = "failed"
            elif any(t["status"] == "running" for t in tasks):
                overall_status = "running"
            else:
                overall_status = "pending"

            # Compute progress
            progress = (completed_count / total_count) * 100 if total_count > 0 else 0.0

            return {
                "job_id": job_id,
                "status": overall_status,
                "tasks": tasks,
                "progress": round(progress, 2),
                "completed_tasks": completed_count,
                "total_tasks": total_count,
            }

    except Exception as e:
        logger.error(f"Error getting pipeline status for job {job_id}: {e}")
        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
        }


def get_all_pipeline_statuses(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get statuses for all recent pipelines.

    Args:
        limit: Maximum number of pipelines to return
        offset: Offset for pagination

    Returns:
        List of pipeline status dicts
    """
    from ..database import get_db

    try:
        with get_db() as conn:
            # Get unique job IDs
            rows = conn.execute(
                """
                SELECT DISTINCT job_id
                FROM luigi_task_state
                ORDER BY job_id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

            job_ids = [row["job_id"] for row in rows]

            # Get status for each job
            statuses = [get_pipeline_status(job_id) for job_id in job_ids]

            return statuses

    except Exception as e:
        logger.error(f"Error getting all pipeline statuses: {e}")
        return []


def cancel_pipeline(job_id: int) -> Dict[str, Any]:
    """
    Cancel a running pipeline.

    Marks all pending/running tasks as cancelled.

    Args:
        job_id: Job ID to cancel

    Returns:
        Dict with cancellation result
    """
    from ..database import get_db

    try:
        with get_db() as conn:
            # Update all non-completed tasks to cancelled
            cursor = conn.execute(
                """
                UPDATE luigi_task_state
                SET status = 'cancelled'
                WHERE job_id = ?
                AND status IN ('pending', 'running')
                """,
                (job_id,),
            )
            conn.commit()

            cancelled_count = cursor.rowcount

            logger.info(f"Cancelled {cancelled_count} tasks for job {job_id}")

            return {
                "success": True,
                "job_id": job_id,
                "cancelled_tasks": cancelled_count,
            }

    except Exception as e:
        logger.error(f"Error cancelling pipeline for job {job_id}: {e}")
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
        }


def retry_failed_pipeline(job_id: int) -> Dict[str, Any]:
    """
    Retry a failed pipeline from the last successful checkpoint.

    Marks all failed tasks as pending so Luigi will retry them.

    Args:
        job_id: Job ID to retry

    Returns:
        Dict with retry result
    """
    from ..database import get_db

    try:
        with get_db() as conn:
            # Reset failed tasks to pending
            cursor = conn.execute(
                """
                UPDATE luigi_task_state
                SET status = 'pending'
                WHERE job_id = ?
                AND status = 'failed'
                """,
                (job_id,),
            )
            conn.commit()

            reset_count = cursor.rowcount

            logger.info(f"Reset {reset_count} failed tasks for job {job_id}")

            return {
                "success": True,
                "job_id": job_id,
                "reset_tasks": reset_count,
                "message": f"Reset {reset_count} tasks to pending. Re-run the pipeline to retry.",
            }

    except Exception as e:
        logger.error(f"Error retrying pipeline for job {job_id}: {e}")
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
        }


# Export public API
__all__ = [
    "run_pipeline_sync",
    "run_pipeline_async",
    "get_pipeline_status",
    "get_all_pipeline_statuses",
    "cancel_pipeline",
    "retry_failed_pipeline",
]
