# Video Renderer - Quick Start Guide

## 1-Minute Overview

The video renderer takes an **approved storyboard** with generated images and renders them into a final video using the Replicate API.

## Quick Usage

### Start Video Rendering

```python
from backend.services import render_video_task

# After user approves storyboard
render_video_task(job_id=123)
```

### Check Status

```python
from backend.database import get_job

job = get_job(123)
status = job['status']  # 'rendering', 'completed', or 'failed'
video_url = job['video_url']  # '/api/videos/123/data'
cost = job['actual_cost']  # e.g., 2.03
```

## Workflow

```
Approved Storyboard → Extract Images → Render Video → Download → Complete
       (5 images)      [image1.jpg,      (Replicate)     (validate)   (update DB)
                        image2.jpg,
                        ...]
```

## Prerequisites

Before calling `render_video_task()`:

1. ✅ **Storyboard Generated**: Job must have `storyboard_data`
2. ✅ **Images Generated**: All scenes must have `image_url`
3. ✅ **Storyboard Approved**: `approved=True` in database

```python
from backend.database import approve_storyboard

# User approves storyboard
approve_storyboard(job_id=123)

# Now you can render
render_video_task(job_id=123)
```

## What It Does

1. **Validates** storyboard is approved
2. **Extracts** image URLs from storyboard entries
3. **Calls** Replicate API to generate video
4. **Polls** for completion (automatic)
5. **Downloads** video to local storage
6. **Validates** video format (magic bytes)
7. **Calculates** actual cost
8. **Updates** database with video URL and cost

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Storyboard must be approved" | `approved=False` | Call `approve_storyboard(job_id)` |
| "No storyboard data available" | Missing `storyboard_data` | Generate storyboard first |
| "Scene X is missing image" | `image_url=None` | Regenerate failed scenes |

### Automatic Retries

- **Max Retries**: 2 (total 3 attempts)
- **Backoff**: 30s, 90s (exponential)
- **Tracks**: `download_retries` in database

## Progress Tracking

```python
from backend.database import get_job

job = get_job(123)
progress = job['progress']

# Example progress:
# {
#     "current_stage": "rendering",
#     "message": "Rendering video from images...",
#     "scenes_total": 0,
#     "scenes_completed": 0
# }
```

## Cost Calculation

```python
# Formula:
image_cost = num_images × $0.003     # Flux-Schnell
video_cost = duration_seconds × $0.10 # SkyReels-2
total_cost = image_cost + video_cost

# Example (5 images, 10 second video):
# 5 × $0.003 = $0.015
# 10 × $0.10 = $1.00
# Total: $1.015 → $1.02
```

## File Storage

Videos are saved to:
```
backend/DATA/videos/{job_id}/final.mp4
```

API path stored in database:
```
/api/videos/{job_id}/data
```

## Complete Example

```python
from backend.database import (
    create_video_job,
    update_storyboard_data,
    approve_storyboard,
    get_job
)
from backend.services import render_video_task
import threading

# 1. Create job (already done in your workflow)
job_id = 123

# 2. Ensure storyboard is generated and approved
approve_storyboard(job_id)

# 3. Start rendering in background
def start_rendering():
    render_video_task(job_id)

thread = threading.Thread(target=start_rendering)
thread.daemon = True
thread.start()

# 4. Poll for completion
import time
while True:
    job = get_job(job_id)
    if job['status'] == 'completed':
        print(f"✓ Video ready: {job['video_url']}")
        print(f"✓ Cost: ${job['actual_cost']:.2f}")
        break
    elif job['status'] == 'failed':
        print(f"✗ Error: {job['error_message']}")
        break
    else:
        print(f"⏳ {job['progress']['message']}")
        time.sleep(5)
```

## API Integration

### Approve Storyboard Endpoint

```python
@app.post("/api/v2/jobs/{job_id}/approve")
async def approve_job_storyboard(job_id: int):
    # Approve storyboard
    approve_storyboard(job_id)

    # Start rendering in background
    threading.Thread(
        target=render_video_task,
        args=(job_id,),
        daemon=True
    ).start()

    return {"status": "rendering_started", "job_id": job_id}
```

### Check Status Endpoint

```python
@app.get("/api/v2/jobs/{job_id}")
async def get_job_status(job_id: int):
    job = get_job(job_id)

    if job['status'] == 'completed':
        return {
            "status": "completed",
            "video_url": job['video_url'],
            "actual_cost": job['actual_cost']
        }
    elif job['status'] == 'rendering':
        return {
            "status": "rendering",
            "progress": job['progress']
        }
    elif job['status'] == 'failed':
        return {
            "status": "failed",
            "error": job['error_message']
        }
```

## Troubleshooting

### Video Not Rendering

```bash
# Check job status
python -c "
from backend.database import get_job
job = get_job(123)
print(f'Status: {job[\"status\"]}')
print(f'Approved: {job[\"approved\"]}')
print(f'Storyboard: {len(job[\"storyboard_data\"]) if job[\"storyboard_data\"] else 0} bytes')
"
```

### Check Logs

```python
import logging
logging.basicConfig(level=logging.INFO)

# Run renderer
from backend.services import render_video_task
render_video_task(123)
```

### Manual Download Test

```python
from backend.services.video_renderer import download_video

video_path = download_video(
    "https://replicate.delivery/test.mp4",
    job_id=123
)
print(f"Downloaded to: {video_path}")
```

## Performance

| Metric | Value |
|--------|-------|
| Typical Time | 2-5 minutes |
| Max Timeout | 10 minutes |
| Memory Usage | < 50 MB |
| Storage | ~5-50 MB per video |

## Next Steps

1. ✅ **Implemented**: Video rendering task
2. ⏭️ **Next**: Integrate with API endpoints
3. ⏭️ **Next**: Add webhook notifications
4. ⏭️ **Next**: Implement video preview

## Documentation

- **Full Docs**: `VIDEO_RENDERER_README.md`
- **Implementation**: `TASK_7_IMPLEMENTATION_SUMMARY.md`
- **Tests**: `test_video_renderer.py`
- **Code**: `video_renderer.py`

---

**Ready to use!** Call `render_video_task(job_id)` after approving the storyboard.
