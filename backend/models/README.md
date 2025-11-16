# Video Generation API Models

This directory contains Pydantic models for the v2 video generation workflow.

## Files

- `video_generation.py` - Core Pydantic models for video generation API
- `__init__.py` - Package initialization with exports

## Models Overview

### 1. VideoStatus (Enum)
Tracks the lifecycle of a video generation job.

**Values:**
- `pending` - Job created, waiting to start
- `parsing` - Parsing user prompt and extracting requirements
- `generating_storyboard` - Creating scene-by-scene storyboard
- `storyboard_ready` - Storyboard complete, awaiting approval
- `rendering` - Rendering final video
- `completed` - Video generation complete
- `failed` - Job failed with errors
- `canceled` - Job canceled by user

### 2. Scene (BaseModel)
Represents a single scene in the video.

**Fields:**
- `scene_number: int` - Sequential scene number (≥1)
- `description: str` - Narrative description (1-1000 chars)
- `duration: float` - Duration in seconds (0-60s)
- `image_prompt: str` - Image generation prompt (1-2000 chars)

**Validation:**
- Duration must be positive and ≤60 seconds
- Rounded to 2 decimal places

### 3. StoryboardEntry (BaseModel)
Tracks generation progress for a single scene.

**Fields:**
- `scene: Scene` - Scene definition
- `image_url: Optional[str]` - URL to generated image
- `generation_status: str` - Status: pending|generating|completed|failed
- `error: Optional[str]` - Error message if failed (max 500 chars)

### 4. GenerationRequest (BaseModel)
Request payload for initiating video generation.

**Fields:**
- `prompt: str` - Video concept description (10-5000 chars)
- `duration: int` - Total duration in seconds (5-300s, default: 30)
- `style: Optional[str]` - Visual style (max 100 chars)
- `aspect_ratio: Optional[str]` - Ratio: 16:9|9:16|1:1|4:3 (default: 16:9)
- `client_id: Optional[str]` - Client identifier (max 100 chars)
- `brand_guidelines: Optional[dict]` - Client-specific branding

**Validation:**
- Prompt trimmed and validated for minimum length
- Duration must be 5-300 seconds
- Aspect ratio validated against allowed values

### 5. VideoProgress (BaseModel)
Real-time progress tracking.

**Fields:**
- `current_stage: VideoStatus` - Current workflow stage
- `scenes_total: int` - Total scenes (≥0)
- `scenes_completed: int` - Completed scenes (≥0)
- `current_scene: Optional[int]` - Currently processing scene (≥1)
- `estimated_completion_seconds: Optional[int]` - ETA in seconds (≥0)
- `message: Optional[str]` - Human-readable message (max 200 chars)

### 6. JobResponse (BaseModel)
Complete job response with all metadata.

**Fields:**
- `job_id: int` - Unique job ID (≥1)
- `status: VideoStatus` - Current job status
- `progress: VideoProgress` - Detailed progress
- `storyboard: Optional[list[StoryboardEntry]]` - Scene storyboard
- `video_url: Optional[str]` - Final video URL
- `estimated_cost: float` - Estimated cost in USD (≥0)
- `actual_cost: Optional[float]` - Actual cost in USD (≥0)
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last update timestamp
- `approved: bool` - Storyboard approval status (default: False)
- `error_message: Optional[str]` - Error details (max 1000 chars)

**Validation:**
- Costs validated as non-negative and ≤$10,000
- Costs rounded to 2 decimal places
- Datetime fields JSON-serialized to ISO format

## Usage Examples

### Creating a Generation Request
```python
from backend.models import GenerationRequest

request = GenerationRequest(
    prompt="Create a cinematic video about a robot exploring Mars",
    duration=30,
    style="cinematic",
    aspect_ratio="16:9",
    client_id="acme-corp"
)
```

### Building a Job Response
```python
from backend.models import JobResponse, VideoStatus, VideoProgress
from datetime import datetime

response = JobResponse(
    job_id=12345,
    status=VideoStatus.STORYBOARD_READY,
    progress=VideoProgress(
        current_stage=VideoStatus.STORYBOARD_READY,
        scenes_total=6,
        scenes_completed=6,
        message="Storyboard complete, awaiting approval"
    ),
    estimated_cost=15.50,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    approved=False
)
```

### JSON Serialization
```python
# Export to JSON
json_str = response.model_dump_json(indent=2)

# Parse from JSON
from backend.models import JobResponse
response = JobResponse.model_validate_json(json_str)
```

## Validation Features

All models include comprehensive validation:

1. **Type Safety** - Strict type checking via Pydantic
2. **Range Validation** - Min/max constraints on numeric fields
3. **Pattern Matching** - Regex validation for structured fields
4. **Length Limits** - String length constraints
5. **Custom Validators** - Business logic validation
6. **JSON Serialization** - Automatic datetime and enum handling

## Error Handling

Models raise `pydantic.ValidationError` for invalid data:

```python
from pydantic import ValidationError
from backend.models import GenerationRequest

try:
    request = GenerationRequest(
        prompt="Too short",  # Less than 10 chars
        duration=30
    )
except ValidationError as e:
    print(e.errors())
```

## Integration

Import models from the package root:

```python
from backend.models import (
    VideoStatus,
    Scene,
    StoryboardEntry,
    GenerationRequest,
    VideoProgress,
    JobResponse
)
```

## Testing

Run the test suite:
```bash
PYTHONPATH=/path/to/project python3 backend/test_video_models.py
```

## Requirements

- Python 3.10+
- Pydantic 2.0+

See `backend/requirements.txt` for full dependency list.
