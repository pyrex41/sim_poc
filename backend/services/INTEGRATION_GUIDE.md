# Storyboard Generator Integration Guide

## Complete FastAPI Integration

This document shows how to integrate the storyboard generator into the main FastAPI application.

## Step 1: Update main.py Imports

```python
# Add to backend/main.py imports
from .services.storyboard_generator import generate_storyboard_task
from .models.video_generation import (
    GenerationRequest,
    JobResponse,
    VideoStatus,
    VideoProgress,
    StoryboardEntry,
    Scene
)
from .database import (
    save_generated_video,
    get_job,
    update_job_progress,
    approve_storyboard
)
```

## Step 2: Create Video Generation Endpoint

```python
@app.post("/api/v2/generate", response_model=dict)
async def create_video_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_auth)
):
    """Create a new video generation job and start storyboard generation."""
    logger.info(f"Creating video generation job for user {current_user['username']}")

    # Estimate cost
    replicate_client = ReplicateClient()
    num_scenes = max(3, min(10, int(request.duration / 5)))
    estimated_cost = replicate_client.estimate_cost(
        num_images=num_scenes,
        video_duration=request.duration
    )

    # Create job in database
    job_id = save_generated_video(
        prompt=request.prompt,
        video_url="",
        model_id="v2",
        parameters=request.model_dump(),
        status=VideoStatus.PENDING.value
    )

    # Launch background task
    background_tasks.add_task(generate_storyboard_task, job_id)

    return {
        "job_id": job_id,
        "status": VideoStatus.PENDING.value,
        "estimated_cost": estimated_cost
    }
```

## Testing the Integration

### Manual Test

```bash
# Create job
curl -X POST http://localhost:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A robot exploring Mars",
    "duration": 30,
    "style": "cinematic"
  }'

# Poll status
curl http://localhost:8000/api/v2/jobs/1
```

See STORYBOARD_GENERATOR_README.md for complete documentation.
