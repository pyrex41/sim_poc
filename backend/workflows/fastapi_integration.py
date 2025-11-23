"""
FastAPI integration for Luigi workflows.

This module provides example endpoints showing how to integrate Luigi
workflows with the existing V3 API.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from .runner import (
    run_pipeline_async,
    get_pipeline_status,
    get_all_pipeline_statuses,
    cancel_pipeline,
    retry_failed_pipeline,
)

logger = logging.getLogger(__name__)

# Create router for Luigi workflow endpoints
luigi_router = APIRouter(prefix="/api/v3/luigi", tags=["luigi-workflows"])


@luigi_router.post("/jobs/from-image-pairs")
async def create_job_with_luigi(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Create a new job using Luigi workflow orchestration.

    This is an alternative to the existing /api/v3/jobs/from-image-pairs
    endpoint that uses Luigi for workflow management instead of manual
    asyncio orchestration.

    Request body:
    {
        "campaignId": "campaign-uuid",
        "clientId": "client-uuid" (optional),
        "clipDuration": 5.0 (optional),
        "numPairs": 10 (optional)
    }

    Returns:
    {
        "jobId": 123,
        "status": "pipeline_started",
        "message": "Luigi pipeline initiated",
        "luigiDashboard": "http://localhost:8082/..."
    }
    """
    from ..database import create_video_job

    try:
        campaign_id = request.get("campaignId")
        client_id = request.get("clientId")
        clip_duration = request.get("clipDuration")
        num_pairs = request.get("numPairs")

        if not campaign_id:
            raise HTTPException(status_code=400, detail="campaignId is required")

        # Create job record
        job_id = create_video_job(
            prompt=f"Luigi pipeline for campaign {campaign_id}",
            model_id="luigi-workflow",
            parameters={
                "campaign_id": campaign_id,
                "client_id": client_id,
                "clip_duration": clip_duration,
                "num_pairs": num_pairs,
                "workflow_type": "luigi",
            },
            estimated_cost=0.0,
            client_id=client_id,
            status="pipeline_starting",
        )

        logger.info(f"Created job {job_id} for Luigi pipeline")

        # Launch Luigi workflow in background
        background_tasks.add_task(
            run_pipeline_async,
            job_id,
            campaign_id,
            clip_duration,
            num_pairs,
            workers=10,
            use_local_scheduler=False,  # Use central scheduler
        )

        return {
            "jobId": job_id,
            "status": "pipeline_started",
            "message": "Luigi workflow initiated. Use /luigi/jobs/{job_id} to monitor progress.",
            "luigiDashboard": f"http://localhost:8082/static/visualiser/index.html",
        }

    except Exception as e:
        logger.error(f"Error creating Luigi job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@luigi_router.get("/jobs/{job_id}")
async def get_luigi_job_status(job_id: int) -> Dict[str, Any]:
    """
    Get Luigi pipeline status for a job.

    Returns detailed task-level status information.

    Returns:
    {
        "jobId": 123,
        "status": "running",
        "progress": 45.5,
        "tasks": [
            {
                "name": "AssetCollectionTask",
                "status": "completed",
                "created_at": "2025-01-22T10:00:00Z",
                "completed_at": "2025-01-22T10:01:00Z"
            },
            ...
        ],
        "completed_tasks": 5,
        "total_tasks": 11,
        "luigiDashboard": "http://localhost:8082/..."
    }
    """
    try:
        status = get_pipeline_status(job_id)

        if not status or status.get("status") == "not_started":
            raise HTTPException(status_code=404, detail="Job not found")

        # Add Luigi dashboard link
        status["luigiDashboard"] = (
            f"http://localhost:8082/static/visualiser/index.html#task/job_{job_id}"
        )

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@luigi_router.get("/jobs")
async def list_luigi_jobs(
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List all Luigi pipeline jobs.

    Query parameters:
    - limit: Number of jobs to return (default: 20)
    - offset: Pagination offset (default: 0)

    Returns:
    {
        "jobs": [...],
        "total": 42,
        "limit": 20,
        "offset": 0
    }
    """
    try:
        jobs = get_all_pipeline_statuses(limit=limit, offset=offset)

        return {
            "jobs": jobs,
            "total": len(jobs),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@luigi_router.post("/jobs/{job_id}/cancel")
async def cancel_luigi_job(job_id: int) -> Dict[str, Any]:
    """
    Cancel a running Luigi pipeline.

    This marks all pending/running tasks as cancelled.
    """
    try:
        result = cancel_pipeline(job_id)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to cancel pipeline")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@luigi_router.post("/jobs/{job_id}/retry")
async def retry_luigi_job(
    job_id: int,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Retry a failed Luigi pipeline from the last checkpoint.

    This resets failed tasks to pending and re-runs the pipeline.
    """
    try:
        # Reset failed tasks
        result = retry_failed_pipeline(job_id)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to reset pipeline")
            )

        # Get job details
        from ..database import get_job

        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Extract campaign ID from parameters
        import json

        params = (
            json.loads(job["parameters"])
            if isinstance(job["parameters"], str)
            else job["parameters"]
        )

        campaign_id = params.get("campaign_id")
        if not campaign_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot retry: campaign_id not found in job parameters"
            )

        clip_duration = params.get("clip_duration")
        num_pairs = params.get("num_pairs")

        # Re-run the pipeline in background
        background_tasks.add_task(
            run_pipeline_async,
            job_id,
            campaign_id,
            clip_duration,
            num_pairs,
            workers=10,
            use_local_scheduler=False,
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": "Pipeline retry initiated",
            "reset_tasks": result.get("reset_tasks", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["luigi_router"]
