"""
V3 API - Unified generation endpoint.

This module provides the /api/v3/generate endpoints that route requests
to the appropriate generation engine based on the engine type.
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import Annotated, Union
import logging

from backend.core import (
    EngineType,
    Task,
    ValidationError,
    DatabaseManager,
    get_db_manager,
)
from backend.engines.image import (
    ImageEngine,
    ImageRequest,
    ImageResponse,
)
from backend.engines.video import (
    VideoEngine,
    VideoRequest,
    VideoResponse,
)
from backend.engines.audio import (
    AudioEngine,
    AudioRequest,
    AudioResponse,
)
from backend.engines.utilities import (
    UtilitiesEngine,
    UtilityRequest,
    UtilityResponse,
)
# from backend.engines.video_analysis import (
#     VideoAnalysisEngine,
#     VideoAnalysisRequest,
#     VideoAnalysisResponse,
# )


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3", tags=["generation"])

# Engine singletons
_image_engine = None
_video_engine = None
_audio_engine = None
_utilities_engine = None
_video_analysis_engine = None


def get_image_engine() -> ImageEngine:
    """Get or create image engine singleton."""
    global _image_engine
    if _image_engine is None:
        _image_engine = ImageEngine()
    return _image_engine


def get_video_engine() -> VideoEngine:
    """Get or create video engine singleton."""
    global _video_engine
    if _video_engine is None:
        _video_engine = VideoEngine()
    return _video_engine


def get_audio_engine() -> AudioEngine:
    """Get or create audio engine singleton."""
    global _audio_engine
    if _audio_engine is None:
        _audio_engine = AudioEngine()
    return _audio_engine


def get_utilities_engine() -> UtilitiesEngine:
    """Get or create utilities engine singleton."""
    global _utilities_engine
    if _utilities_engine is None:
        _utilities_engine = UtilitiesEngine()
    return _utilities_engine


# def get_video_analysis_engine() -> VideoAnalysisEngine:
#     """Get or create video analysis engine singleton."""
#     global _video_analysis_engine
#     if _video_analysis_engine is None:
#         _video_analysis_engine = VideoAnalysisEngine()
#     return _video_analysis_engine


def get_engine_by_task_id(task_id: str) -> Union[ImageEngine, VideoEngine, AudioEngine, UtilitiesEngine]:
    """
    Get the appropriate engine for a task by looking up its engine type.

    Args:
        task_id: Task ID

    Returns:
        The appropriate engine instance

    Raises:
        HTTPException: If task not found or engine type unknown
    """
    # Query database to determine engine type
    db = get_db_manager()
    row = db.execute_query(
        "SELECT engine FROM generation_tasks WHERE id = ?",
        (task_id,),
        fetch_one=True
    )

    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    engine_type = row['engine']

    if engine_type == EngineType.IMAGE.value:
        return get_image_engine()
    elif engine_type == EngineType.VIDEO.value:
        return get_video_engine()
    elif engine_type == EngineType.AUDIO.value:
        return get_audio_engine()
    elif engine_type == EngineType.UTILITIES.value:
        return get_utilities_engine()
    # elif engine_type == EngineType.VIDEO_ANALYSIS.value:
    #     return get_video_analysis_engine()
    else:
        raise HTTPException(status_code=500, detail=f"Unknown engine type: {engine_type}")


# Dependency to get user (auth disabled for testing)
def get_current_user() -> str:
    """Get current user ID. Returns test user for now (auth disabled)."""
    return "test-user-1"


@router.post("/generate/image")
async def generate_image(
    request: ImageRequest,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Task:
    """
    Generate an image using AI.

    This endpoint submits an image generation task and returns immediately
    with a task ID. The actual generation happens asynchronously.

    Use GET /api/v3/tasks/{task_id} to check status and get results.
    """
    logger.info(f"Image generation request from user {user_id}: {request.prompt[:50]}...")

    try:
        engine = get_image_engine()
        task = await engine.generate(request, user_id=user_id)
        logger.info(f"Created image task {task.id} for user {user_id}")
        return task

    except Exception as e:
        logger.error(f"Error creating image task: {e}", exc_info=True)
        raise


@router.post("/generate/video")
async def generate_video(
    request: VideoRequest,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Task:
    """
    Generate a video using AI.

    This endpoint submits a video generation task and returns immediately
    with a task ID. The actual generation happens asynchronously.

    Use GET /api/v3/tasks/{task_id} to check status and get results.
    """
    logger.info(f"Video generation request from user {user_id}: {request.prompt[:50]}...")

    try:
        engine = get_video_engine()
        task = await engine.generate(request, user_id=user_id)
        logger.info(f"Created video task {task.id} for user {user_id}")
        return task

    except Exception as e:
        logger.error(f"Error creating video task: {e}", exc_info=True)
        raise


@router.post("/generate/audio")
async def generate_audio(
    request: AudioRequest,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Task:
    """
    Generate audio/music using AI.

    This endpoint submits an audio generation task and returns immediately
    with a task ID. The actual generation happens asynchronously.

    Use GET /api/v3/tasks/{task_id} to check status and get results.
    """
    logger.info(f"Audio generation request from user {user_id}: {request.prompt[:50]}...")

    try:
        engine = get_audio_engine()
        task = await engine.generate(request, user_id=user_id)
        logger.info(f"Created audio task {task.id} for user {user_id}")
        return task

    except Exception as e:
        logger.error(f"Error creating audio task: {e}", exc_info=True)
        raise


@router.post("/process/utility")
async def process_utility(
    request: UtilityRequest,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Task:
    """
    Process image/video with utility tools.

    Supports: upscaling, background removal, face restoration, etc.

    This endpoint submits a utility processing task and returns immediately
    with a task ID. The actual processing happens asynchronously.

    Use GET /api/v3/tasks/{task_id} to check status and get results.
    """
    logger.info(f"Utility processing request from user {user_id}: {request.tool}")

    try:
        engine = get_utilities_engine()
        task = await engine.generate(request, user_id=user_id)
        logger.info(f"Created utility task {task.id} for user {user_id}")
        return task

    except Exception as e:
        logger.error(f"Error creating utility task: {e}", exc_info=True)
        raise


# @router.post("/analyze/video")
# async def analyze_video(
#     request: VideoAnalysisRequest,
#     user_id: Annotated[str, Depends(get_current_user)],
# ) -> Task:
#     """
#     Analyze video content and generate descriptions/captions.

#     Supports: video captioning, video-to-text, TikTok-style captions, etc.

#     This endpoint submits a video analysis task and returns immediately
#     with a task ID. The actual analysis happens asynchronously.

#     Use GET /api/v3/tasks/{task_id} to check status and get results.
#     """
#     logger.info(f"Video analysis request from user {user_id}: {request.model}")

#     try:
#         engine = get_video_analysis_engine()
#         task = await engine.generate(request, user_id=user_id)
#         logger.info(f"Created video analysis task {task.id} for user {user_id}")
#         return task

#     except Exception as e:
#         logger.error(f"Error creating video analysis task: {e}", exc_info=True)
#         raise


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Task:
    """
    Get the status of a generation task.

    Returns the current state of the task including:
    - Current status (pending, processing, succeeded, failed, canceled)
    - Result data (if succeeded)
    - Error message (if failed)
    - Timestamps

    **Task Statuses:**
    - `pending`: Task submitted but not started
    - `processing`: Task is currently being processed
    - `succeeded`: Task completed successfully, result available
    - `failed`: Task failed, error message available
    - `canceled`: Task was canceled
    """
    logger.info(f"Task status request: {task_id} from user {user_id}")

    try:
        engine = get_engine_by_task_id(task_id)
        task = await engine.get_task(task_id, user_id=user_id)
        return task

    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
) -> Union[ImageResponse, VideoResponse, AudioResponse, UtilityResponse]:
    """
    Get the result of a completed generation task.

    This endpoint returns the full result object (ImageResponse, VideoResponse, etc.)
    for a completed task.

    **Note:** Task must be in "succeeded" status, otherwise this will return an error.

    **Errors:**
    - 404: Task not found
    - 202: Task not ready yet (still processing)
    - 410: Task failed or was canceled
    """
    logger.info(f"Task result request: {task_id} from user {user_id}")

    try:
        engine = get_engine_by_task_id(task_id)
        result = await engine.get_result(task_id, user_id=user_id)
        return result

    except Exception as e:
        logger.error(f"Error fetching result for task {task_id}: {e}")
        raise


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
) -> dict:
    """
    Cancel a running generation task.

    Attempts to cancel the task on the provider (Replicate, etc.).
    Already completed tasks cannot be canceled.

    **Returns:**
    - `{"success": true}` if canceled
    - `{"success": false}` if already completed or failed to cancel
    """
    logger.info(f"Cancel task request: {task_id} from user {user_id}")

    try:
        engine = get_engine_by_task_id(task_id)
        canceled = await engine.cancel(task_id, user_id=user_id)
        return {"success": canceled}

    except Exception as e:
        logger.error(f"Error canceling task {task_id}: {e}")
        raise
