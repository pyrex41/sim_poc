# Video Renderer Background Task

## Overview

The `video_renderer.py` module implements the background task for rendering the final video from an approved storyboard using the Replicate API. This is **Task 7** in the v2 video generation workflow.

## Workflow

```
Approved Storyboard → Extract Images → Render Video → Download → Store → Complete
```

### Step-by-Step Process

1. **Fetch Job**: Retrieve job from database using `get_job(job_id)`
2. **Validate Approval**: Ensure storyboard is approved (`approved=True`)
3. **Validate Storyboard**: Check that `storyboard_data` exists and has images
4. **Extract URLs**: Extract image URLs from each storyboard entry
5. **Render Video**: Call `ReplicateClient.generate_video(image_urls)`
6. **Poll Completion**: Wait for video generation to complete
7. **Download Video**: Download video from Replicate using `download_video()`
8. **Validate Video**: Check magic bytes to ensure valid video format
9. **Save Video**: Store video to `DATA/videos/{job_id}/final.mp4`
10. **Calculate Cost**: Compute actual cost from usage
11. **Update Database**: Save video URL, actual cost, set status to 'completed'

## Main Functions

### `render_video_task(job_id: int) -> None`

Main background task function for video rendering.

**Parameters:**
- `job_id` (int): The video generation job ID

**Process:**
1. Fetches job from database
2. Validates storyboard is approved and has images
3. Extracts image URLs from storyboard entries
4. Renders video using Replicate API
5. Downloads and validates video
6. Updates job with video URL and actual cost
7. Sets status to 'completed'

**Error Handling:**
- Marks job as failed if storyboard not approved
- Marks job as failed if storyboard data missing
- Marks job as failed if any scene missing image URL
- Marks job as failed if video rendering fails after retries
- Marks job as failed if video download fails

**Example:**
```python
from backend.services import render_video_task

# Called as background task after storyboard approval
render_video_task(job_id=123)
```

---

### `download_video(video_url: str, job_id: int) -> str`

Helper function to download video from Replicate and save locally.

**Parameters:**
- `video_url` (str): URL of the video to download
- `job_id` (int): Job ID for storage organization

**Returns:**
- `str`: Local file path (e.g., `/api/videos/123/data`)

**Process:**
1. Creates directory: `DATA/videos/{job_id}/`
2. Downloads video with streaming (chunk size: 8192 bytes)
3. Validates file size (must be > 1024 bytes)
4. Validates video format using magic bytes:
   - MP4: `\x00\x00\x00\x18ftypmp4` or similar
   - AVI: `RIFF....AVI `
   - WebM/MKV: `\x1a\x45\xdf\xa3`
5. Saves to `final.mp4`
6. Returns API path

**Error Handling:**
- Raises `ValueError` if download is empty (0 bytes)
- Raises `ValueError` if file too small (< 1024 bytes)
- Raises `ValueError` if invalid video format (magic bytes check)
- Raises `ValueError` on network errors with retry context

**Example:**
```python
from backend.services.video_renderer import download_video

video_path = download_video(
    "https://replicate.delivery/video.mp4",
    job_id=123
)
# Returns: "/api/videos/123/data"
```

## Retry Logic

### Exponential Backoff Strategy

Video rendering uses **exponential backoff** with base 30 seconds:

- **Attempt 1**: Initial attempt
- **Attempt 2**: After 30 seconds delay
- **Attempt 3**: After 90 seconds delay (30 × 3)

**Maximum Retries**: 2 (total 3 attempts)

### Retry Conditions

Retries are triggered for:
- Replicate API failures (`success=False`)
- Network timeouts
- Transient errors

Retries are **NOT** triggered for:
- Invalid storyboard data
- Missing approval
- Missing image URLs
- Video validation failures (after download)

### Tracking Retries

Each retry increments the `download_retries` counter in the database using `increment_retry_count(job_id)`.

## Progress Tracking

Progress is updated throughout the rendering process using `VideoProgress`:

```python
{
    "current_stage": "rendering",
    "scenes_total": 0,
    "scenes_completed": 0,
    "current_scene": None,
    "estimated_completion_seconds": None,
    "message": "Rendering video from images..."
}
```

### Status Messages

| Stage | Message |
|-------|---------|
| Initial | "Rendering video from images..." |
| Retry | "Retrying in {delay}s (attempt {n}/{max})..." |
| Download | "Downloading video..." |
| Finalize | "Finalizing..." |
| Complete | "Video rendering complete!" |

## Cost Tracking

### Cost Calculation

Actual cost is calculated using Replicate pricing:

```python
image_cost = num_images × $0.003  # Flux-Schnell
video_cost = duration_seconds × $0.10  # SkyReels-2
total_cost = image_cost + video_cost
```

**Example:**
- 10 images × $0.003 = $0.030
- 20 seconds × $0.10 = $2.00
- **Total**: $2.03

### Cost Variance Logging

If actual cost exceeds estimated cost by **20% or more**, a warning is logged:

```python
if actual_cost > estimated_cost * 1.2:
    logger.warning(f"Actual cost ${actual_cost} exceeds estimate ${estimated_cost}")
```

This helps identify pricing discrepancies or unexpected usage.

### Cost Storage

Both costs are stored in the database:
- `estimated_cost`: Calculated before rendering starts
- `actual_cost`: Calculated after rendering completes

## Error Handling

### Validation Errors

**Storyboard Not Approved:**
```
Status: failed
Error: "Storyboard must be approved before rendering video"
```

**Missing Storyboard Data:**
```
Status: failed
Error: "No storyboard data available"
```

**Missing Image URL:**
```
Status: failed
Error: "Scene {n} is missing generated image"
```

### Rendering Errors

**All Retries Exhausted:**
```
Status: failed
Error: "Video rendering failed after 3 attempts: [original error]"
```

**Timeout:**
```
Status: failed
Error: "Video rendering timeout after 600 seconds"
```

### Download Errors

**Empty File:**
```
Status: failed
Error: "Downloaded file is empty (0 bytes)"
```

**Invalid Format:**
```
Status: failed
Error: "Downloaded file does not appear to be a valid video"
```

**Network Error:**
```
Status: failed
Error: "Network error during video download: [details]"
```

## File Storage

### Directory Structure

```
DATA/
└── videos/
    └── {job_id}/
        └── final.mp4
```

**Example:**
```
DATA/videos/123/final.mp4
DATA/videos/456/final.mp4
DATA/videos/789/final.mp4
```

### Storage Path

Videos are stored using the pattern:
- **Physical path**: `{PROJECT_ROOT}/backend/DATA/videos/{job_id}/final.mp4`
- **API path**: `/api/videos/{job_id}/data`

The API path is stored in the database `video_url` field.

## Database Updates

### Fields Updated

| Field | Value | When |
|-------|-------|------|
| `status` | 'rendering' | Start of rendering |
| `status` | 'completed' | After successful download |
| `status` | 'failed' | On any error |
| `video_url` | '/api/videos/{id}/data' | After successful download |
| `actual_cost` | Calculated value | After successful rendering |
| `download_retries` | Incremented | On each retry |
| `error_message` | Error details | On failure |
| `updated_at` | CURRENT_TIMESTAMP | On each update |
| `progress` | JSON object | Throughout process |

## Integration Example

### Background Task Invocation

```python
from backend.services import render_video_task
import threading

# After user approves storyboard
def on_storyboard_approval(job_id: int):
    # Mark as approved in database
    approve_storyboard(job_id)

    # Trigger background rendering
    thread = threading.Thread(
        target=render_video_task,
        args=(job_id,)
    )
    thread.daemon = True
    thread.start()
```

### Polling for Completion

```python
from backend.database import get_job

def check_video_status(job_id: int):
    job = get_job(job_id)

    if job['status'] == 'completed':
        video_url = job['video_url']
        actual_cost = job['actual_cost']
        return {"status": "ready", "url": video_url, "cost": actual_cost}

    elif job['status'] == 'rendering':
        progress = job['progress']
        return {"status": "processing", "progress": progress}

    elif job['status'] == 'failed':
        error = job['error_message']
        return {"status": "error", "error": error}
```

## Testing

### Unit Tests

Run unit tests:
```bash
python -m pytest backend/services/test_video_renderer.py -v
```

### Test Coverage

Tests cover:
- ✅ Happy path rendering workflow
- ✅ Storyboard not approved
- ✅ Missing storyboard data
- ✅ Missing image URLs
- ✅ Retry logic with exponential backoff
- ✅ Video download and validation
- ✅ Cost calculation
- ✅ Error handling
- ✅ Progress tracking

### Manual Testing

```python
# 1. Create test job with approved storyboard
from backend.database import create_video_job, approve_storyboard, update_storyboard_data

job_id = create_video_job(
    prompt="Test video",
    model_id="test-model",
    parameters={"duration": 10},
    estimated_cost=1.0
)

# 2. Add storyboard data
storyboard = [
    {
        "scene": {
            "scene_number": 1,
            "description": "Test scene",
            "duration": 5.0,
            "image_prompt": "Test prompt"
        },
        "image_url": "https://example.com/test.jpg",
        "generation_status": "completed",
        "error": None
    }
]
update_storyboard_data(job_id, storyboard)

# 3. Approve storyboard
approve_storyboard(job_id)

# 4. Render video
from backend.services import render_video_task
render_video_task(job_id)

# 5. Check result
job = get_job(job_id)
print(f"Status: {job['status']}")
print(f"Video: {job['video_url']}")
print(f"Cost: {job['actual_cost']}")
```

## Configuration

### Timeouts

| Operation | Timeout | Configurable |
|-----------|---------|--------------|
| Video rendering | 600s (10 min) | `TIMEOUT` |
| Download request | 600s (10 min) | `timeout` param |
| Retry backoff base | 30s | `EXPONENTIAL_BACKOFF_BASE` |

### Retry Settings

| Setting | Value | Configurable |
|---------|-------|--------------|
| Max retries | 2 | `MAX_RETRIES` |
| Backoff multiplier | 3 | Hardcoded |
| Backoff sequence | 30s, 90s | Calculated |

### Cost Settings

| Setting | Value | Source |
|---------|-------|--------|
| Image cost | $0.003 | `ReplicateClient.FLUX_SCHNELL_PRICE_PER_IMAGE` |
| Video cost/sec | $0.10 | `ReplicateClient.SKYREELS2_PRICE_PER_SECOND` |
| Variance threshold | 20% | `COST_VARIANCE_THRESHOLD` |

## Dependencies

### Internal Dependencies
- `backend.models.video_generation`: VideoStatus, VideoProgress
- `backend.services.replicate_client`: ReplicateClient
- `backend.database`: get_job, update_job_progress, mark_job_failed, etc.

### External Dependencies
- `requests`: HTTP client for video download
- `pathlib`: File system operations
- `logging`: Structured logging
- `time`: Sleep for retry backoff
- `json`: Storyboard data parsing

## Logging

### Log Levels

**INFO**: Normal workflow progress
```
Job 123: Starting video rendering
Job 123: Extracted 5 image URLs
Job 123: Video rendered successfully
```

**WARNING**: Retries and cost variance
```
Job 123: Rendering attempt 1 failed - Temporary error
Job 123: Actual cost $3.50 exceeds estimate $2.50 by 40.0%
```

**ERROR**: Failures
```
Job 123: Video rendering failed - All retries exhausted
Job 123: Failed to download video - Network timeout
```

**DEBUG**: Detailed information
```
Cost calculation - Images: 10 x $0.003 = $0.030, Video: 20s x $0.10 = $2.00
```

## Performance Considerations

### Memory Usage

- Video downloads use **streaming** (8KB chunks) to minimize memory usage
- Temporary files are created and then deleted
- Only stores API path in database, not video binary data in memory

### Timeouts

- **600 seconds (10 minutes)** for video rendering
- **600 seconds (10 minutes)** for video download
- Prevents hanging jobs and resource exhaustion

### Retry Strategy

- **Exponential backoff** prevents overwhelming the API
- **Max 2 retries** balances reliability with cost control
- Tracks retry count to prevent infinite loops

## Future Enhancements

### Potential Improvements

1. **Parallel Processing**: Generate multiple videos concurrently
2. **Progress Webhooks**: Send real-time updates to client
3. **Video Preview**: Generate low-res preview before full render
4. **Custom Transitions**: Allow user-defined scene transitions
5. **Audio Support**: Add background music or voiceover
6. **Format Options**: Support multiple output formats (MP4, WebM, GIF)
7. **Resolution Control**: Allow HD, 4K, or custom resolutions
8. **Watermarking**: Add client-specific branding
9. **CDN Upload**: Automatically upload to CDN for faster delivery
10. **Cost Optimization**: Batch render jobs to reduce per-second costs

## Troubleshooting

### Common Issues

**Issue: "Storyboard must be approved before rendering"**
- **Cause**: User clicked render before approving storyboard
- **Solution**: Call `approve_storyboard(job_id)` before rendering

**Issue: "Scene X is missing generated image"**
- **Cause**: Storyboard generation failed for some scenes
- **Solution**: Regenerate failed scenes or remove them from storyboard

**Issue: "Downloaded file does not appear to be a valid video"**
- **Cause**: Replicate returned non-video content (error page, etc.)
- **Solution**: Check Replicate API logs, verify image URLs are valid

**Issue: "Video rendering timeout after 600 seconds"**
- **Cause**: Video is too long or Replicate API is slow
- **Solution**: Increase `TIMEOUT` constant or reduce video duration

**Issue: "Actual cost exceeds estimate by X%"**
- **Cause**: Video duration longer than expected
- **Solution**: Review scene durations, adjust cost estimation logic

## Summary

The `video_renderer.py` module provides:

✅ **Robust video rendering** from approved storyboards
✅ **Comprehensive error handling** with retry logic
✅ **Progress tracking** for real-time status updates
✅ **Cost calculation** with variance detection
✅ **Video validation** using magic bytes
✅ **Organized storage** with job-based directories
✅ **Extensive logging** for debugging
✅ **Test coverage** with unit tests

This completes Task 7 of the v2 video generation workflow.
