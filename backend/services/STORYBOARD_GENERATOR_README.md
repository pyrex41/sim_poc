# Storyboard Generator Background Task

## Overview

The Storyboard Generator is a background task service that generates storyboards (scene breakdowns with images) from user video prompts. It orchestrates the entire workflow from prompt parsing to image generation, with comprehensive progress tracking and error handling.

## Architecture

### Main Components

1. **`generate_storyboard_task(job_id: int)`** - Main background task entry point
2. **`parse_prompt_to_scenes(prompt, duration, style)`** - Prompt parsing logic
3. **Helper functions** - Status updates, progress tracking, retry logic

### Workflow

```
1. Fetch job from database
   ↓
2. Update status to 'parsing'
   ↓
3. Parse prompt into scenes
   ↓
4. Update status to 'generating_storyboard'
   ↓
5. For each scene:
   - Generate image (with retries)
   - Update progress
   - Save storyboard data
   ↓
6. Update status to 'storyboard_ready'
```

## Implementation Details

### Prompt Parsing

The `parse_prompt_to_scenes()` function uses a rule-based approach:

- **Scene Count**: 1 scene per 5 seconds of video (min 3, max 10 scenes)
- **Duration Distribution**: Evenly distributed across scenes
- **Scene Types**:
  - Scene 1: Opening/Hook
  - Scene 2: Context/Setup
  - Middle Scenes: Content/Product showcase
  - Last Scene: Closing/CTA

**Example:**
```python
scenes = parse_prompt_to_scenes(
    prompt="A robot exploring Mars",
    duration=30,
    style="cinematic"
)
# Returns: 6 scenes, 5 seconds each
```

### Image Generation with Retry Logic

Each scene image is generated using `ReplicateClient.generate_image()` with automatic retry logic:

- **Max Retries**: 3 attempts per scene
- **Backoff Strategy**: Exponential (2s, 4s, 8s)
- **Timeout**: 120 seconds per image
- **Partial Failures**: Job continues even if some scenes fail

**Success Flow:**
```
Attempt 1 → Success → Continue to next scene
```

**Retry Flow:**
```
Attempt 1 → Fail → Wait 2s
Attempt 2 → Fail → Wait 4s
Attempt 3 → Success → Continue to next scene
```

### Progress Tracking

Progress is updated after each scene using `VideoProgress` model:

```python
{
    "current_stage": "generating_storyboard",
    "scenes_total": 6,
    "scenes_completed": 3,
    "current_scene": 4,
    "estimated_completion_seconds": 240,
    "message": "Generating image for scene 4/6"
}
```

**ETA Calculation:**
- Tracks generation time for each completed image
- Calculates average generation time
- Estimates remaining time: `avg_time * remaining_scenes`

### Storyboard Data Structure

Storyboard is stored as JSON in the `storyboard_data` column:

```json
[
  {
    "scene": {
      "scene_number": 1,
      "description": "Opening scene: A robot exploring Mars",
      "duration": 5.0,
      "image_prompt": "Opening establishing shot, A robot exploring Mars, cinematic style, high quality"
    },
    "image_url": "https://replicate.delivery/pbxt/xyz123.jpg",
    "generation_status": "completed",
    "error": null
  },
  {
    "scene": {
      "scene_number": 2,
      "description": "Setting up context for: A robot exploring Mars",
      "duration": 5.0,
      "image_prompt": "Context establishing shot, A robot exploring Mars, cinematic style, high quality"
    },
    "image_url": "https://replicate.delivery/pbxt/abc456.jpg",
    "generation_status": "completed",
    "error": null
  }
]
```

### Error Handling

**Types of Errors:**

1. **Job Not Found**
   - Logs error and returns silently
   - No database updates

2. **Prompt Parsing Failure**
   - Marks job as failed
   - Error message: "Failed to parse prompt: {error}"

3. **Individual Scene Failures**
   - Marks scene as failed in storyboard
   - Continues with remaining scenes
   - Job still completes if at least one scene succeeds

4. **Complete Failure**
   - All scenes failed to generate
   - Job status: 'failed'
   - Error message: "All scene images failed to generate"

5. **Partial Failure**
   - Some scenes succeeded, some failed
   - Job status: 'storyboard_ready'
   - Message: "Storyboard ready (N scenes failed)"

## Database Schema

Required columns in `generated_videos` table:

```sql
ALTER TABLE generated_videos ADD COLUMN progress TEXT;
ALTER TABLE generated_videos ADD COLUMN storyboard_data TEXT;
ALTER TABLE generated_videos ADD COLUMN approved BOOLEAN DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN approved_at TIMESTAMP;
ALTER TABLE generated_videos ADD COLUMN estimated_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN actual_cost REAL;
ALTER TABLE generated_videos ADD COLUMN error_message TEXT;
ALTER TABLE generated_videos ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

## Usage Examples

### Background Task Integration

```python
from backend.services import generate_storyboard_task
from threading import Thread

# Create job in database
job_id = save_generated_video(
    prompt="A robot exploring Mars",
    video_url="",  # Empty initially
    model_id="v2",
    parameters={"duration": 30, "style": "cinematic"},
    status="pending"
)

# Launch background task
thread = Thread(target=generate_storyboard_task, args=(job_id,))
thread.daemon = True
thread.start()
```

### FastAPI Integration

```python
from fastapi import BackgroundTasks

@app.post("/api/v2/generate")
async def generate_video(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    # Create job
    job_id = save_generated_video(
        prompt=request.prompt,
        video_url="",
        model_id="v2",
        parameters=request.model_dump(),
        status="pending"
    )

    # Add background task
    background_tasks.add_task(generate_storyboard_task, job_id)

    # Return immediately
    return {"job_id": job_id, "status": "pending"}
```

### Polling for Progress

```python
@app.get("/api/v2/jobs/{job_id}")
async def get_job_status(job_id: int):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = json.loads(job.get("progress", "{}"))
    storyboard = json.loads(job.get("storyboard_data", "null"))

    return JobResponse(
        job_id=job["id"],
        status=job["status"],
        progress=VideoProgress(**progress),
        storyboard=[StoryboardEntry(**entry) for entry in storyboard] if storyboard else None,
        video_url=job.get("video_url"),
        estimated_cost=job.get("estimated_cost", 0.0),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        approved=job.get("approved", False),
        error_message=job.get("error_message")
    )
```

## Configuration

### Constants

```python
MAX_RETRIES = 3                    # Max retry attempts per image
PARSING_TIMEOUT = 30               # Seconds for prompt parsing
IMAGE_GENERATION_TIMEOUT = 120     # Seconds per image
DEFAULT_SCENE_DURATION = 5.0       # Default scene length
```

### Environment Variables

```bash
REPLICATE_API_KEY=r8_xxx...    # Required for image generation
DATA=/path/to/DATA             # Database directory
```

## Testing

### Unit Tests

Run the test suite:

```bash
python3 backend/services/test_storyboard_generator.py
```

**Test Coverage:**
- ✓ Prompt parsing with various durations
- ✓ Scene count and duration distribution
- ✓ Style modifier application
- ✓ Image generation with retries
- ✓ Exponential backoff timing
- ✓ Complete success workflow
- ✓ Partial failure handling
- ✓ Complete failure handling
- ✓ Progress tracking
- ✓ Storyboard data serialization

### Manual Testing

```python
# Test prompt parsing
from backend.services import parse_prompt_to_scenes

scenes = parse_prompt_to_scenes(
    prompt="A futuristic city with flying cars",
    duration=30,
    style="cyberpunk"
)

for scene in scenes:
    print(f"Scene {scene.scene_number}: {scene.description}")
    print(f"  Duration: {scene.duration}s")
    print(f"  Prompt: {scene.image_prompt[:100]}...")
    print()
```

## Performance Metrics

**Typical Performance:**
- Prompt Parsing: < 1 second
- Image Generation: 15-30 seconds per scene
- Total Time (6 scenes): 2-3 minutes
- Database Updates: < 100ms each

**Cost Estimation:**
- Flux-Schnell: $0.003 per image
- 6 scenes = $0.018 for storyboard
- Video generation (separate): $3-5 depending on duration

## Future Enhancements

### LLM-Based Prompt Parsing

Replace rule-based parsing with LLM:

```python
def parse_prompt_to_scenes_llm(prompt: str, duration: int) -> List[Scene]:
    """Use LLM to intelligently break down prompt into scenes."""
    # Use Claude/GPT to analyze prompt
    # Extract key moments, transitions, narrative beats
    # Generate optimized scene descriptions and image prompts
    pass
```

### Advanced Image Prompts

Enhance image prompt generation:

- Shot composition analysis (rule of thirds, framing)
- Lighting direction and mood
- Camera movement descriptors
- Continuity across scenes
- Brand guideline integration

### Parallel Image Generation

Generate multiple images concurrently:

```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(client.generate_image, scene.image_prompt)
        for scene in scenes
    ]
    results = [f.result() for f in futures]
```

### Caching and Deduplication

- Cache similar image prompts
- Reuse images from previous generations
- Reduce API costs for similar requests

## Troubleshooting

### Common Issues

**Issue: Job stuck in 'parsing' status**
- Check logs for parsing errors
- Verify prompt is not empty
- Ensure duration is valid (5-300 seconds)

**Issue: All scenes failing**
- Verify REPLICATE_API_KEY is set
- Check Replicate API status
- Review image prompt length (max 2000 chars)

**Issue: Slow generation**
- Check network connectivity
- Review Replicate API rate limits
- Consider implementing parallel generation

**Issue: Storyboard data not saving**
- Check database column exists: `storyboard_data TEXT`
- Verify JSON serialization of Scene/StoryboardEntry models
- Check database write permissions

## Logging

All operations are logged with appropriate levels:

```
INFO: Starting storyboard generation for job 123
INFO: Job 123: Parsing prompt into scenes
INFO: Job 123: Parsed into 6 scenes
INFO: Job 123: Generating image for scene 1/6
INFO: Job 123: Scene 1 completed - https://...
WARNING: Job 123: Attempt 1 failed - Temporary error
ERROR: Job 123: Scene 3 failed - All retries exhausted
```

## Dependencies

```
pydantic>=2.0.0          # Data validation and models
requests>=2.31.0         # HTTP client for Replicate API
```

## Migration

Run database migration before using:

```bash
python3 -m backend.migrations.add_video_job_fields
```

This adds required columns to the `generated_videos` table.

## Support

For issues or questions:
1. Check logs in application output
2. Review database state with SQL queries
3. Test individual functions in isolation
4. Verify Replicate API connectivity

## License

Internal use only - Part of video generation MVP platform.
