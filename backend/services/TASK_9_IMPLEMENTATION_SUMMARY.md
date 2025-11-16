# Task 9 Implementation Summary: Video Export and Storyboard Refinement

## Overview
This implementation adds comprehensive video export capabilities with format conversion, storyboard refinement features, and detailed metadata tracking for video generation jobs.

## Files Created

### 1. `/backend/services/video_exporter.py`
**Purpose:** Video export service with ffmpeg integration for format conversion and quality presets.

**Key Functions:**
- `check_ffmpeg_available()` - Validates ffmpeg installation
- `get_video_info(video_path)` - Retrieves video metadata using ffprobe
- `export_video(input_path, output_path, format, quality)` - Main export function
- `get_export_path(storage_path, job_id, format, quality)` - Generates export file paths
- `cleanup_old_exports(storage_path, job_id)` - Removes old export files

**Supported Formats:**
- MP4 (H.264 video, AAC audio)
- MOV (H.264 video, AAC audio)
- WebM (VP9 video, Opus audio)

**Quality Presets:**
- Low: 480p (854x480), 1000k video bitrate, 128k audio
- Medium: 720p (1280x720), 2500k video bitrate, 192k audio
- High: 1080p (1920x1080), 5000k video bitrate, 256k audio

**Storage Location:**
- Exports stored in: `VIDEO_STORAGE_PATH/exports/{job_id}/{format}_{quality}.{ext}`
- Cached exports are reused if they already exist

## Database Changes

### New Columns Added (in `database.py` init_db())
```sql
ALTER TABLE generated_videos ADD COLUMN download_count INTEGER DEFAULT 0
ALTER TABLE generated_videos ADD COLUMN refinement_count INTEGER DEFAULT 0
```

### New Database Functions (in `database.py`)

1. **Download Tracking:**
   - `increment_download_count(job_id)` - Increments download counter
   - `get_download_count(job_id)` - Retrieves download count

2. **Scene Refinement:**
   - `refine_scene_in_storyboard(job_id, scene_number, new_image_url, new_description, new_image_prompt)` - Updates scene data
   - `get_refinement_count(job_id)` - Gets refinement count
   - `increment_estimated_cost(job_id, additional_cost)` - Adds cost for refinements

3. **Scene Reordering:**
   - `reorder_storyboard_scenes(job_id, scene_order)` - Reorders scenes in storyboard

**Important Behaviors:**
- Refinement and reordering both reset the `approved` flag to 0
- Refinement count is tracked and limited to 5 per job
- Each refinement increments estimated_cost by $0.02 (approximate image generation cost)

## API Endpoints Added

### 1. `GET /api/v2/jobs/{job_id}/export`
**Purpose:** Export completed video in requested format and quality

**Query Parameters:**
- `format`: Output format (mp4, mov, webm) - default: mp4
- `quality`: Quality preset (low, medium, high) - default: medium

**Authentication:** Required (uses `verify_auth` dependency)

**Response:** Returns the exported video file as a download

**Features:**
- Checks ffmpeg availability (returns 503 if not available)
- Validates job exists and is completed
- Caches exports (reuses if already exists)
- Increments download count
- Supports only locally stored videos (not remote URLs in MVP)

**Error Handling:**
- 404: Job not found or video not available
- 400: Video not completed or remote URL
- 503: ffmpeg not installed
- 500: Export failed

---

### 2. `POST /api/v2/jobs/{job_id}/refine`
**Purpose:** Refine a specific scene in the storyboard

**Query Parameters:**
- `scene_number` (required): Scene number to refine (1-indexed, ge=1)
- `new_image_prompt` (optional): New prompt for image regeneration (10-2000 chars)
- `new_description` (optional): New scene description (10-1000 chars)

**Authentication:** Required

**Response:** Updated JobResponse with refined storyboard

**Features:**
- Regenerates scene image using Replicate API if new_image_prompt provided
- Updates scene description if new_description provided
- Enforces maximum 5 refinements per job (returns 429 if exceeded)
- Resets approval flag (requires re-approval before rendering)
- Increments refinement_count and estimated_cost

**Error Handling:**
- 404: Job not found
- 400: No storyboard available, or neither prompt nor description provided
- 429: Maximum refinement limit (5) reached
- 500: Image generation failed or update failed

**Background Process:**
- Image generation happens synchronously (not in background task)
- Uses existing ReplicateClient for image generation
- Preserves aspect ratio from original job parameters

---

### 3. `POST /api/v2/jobs/{job_id}/reorder`
**Purpose:** Reorder scenes in the storyboard

**Query Parameters:**
- `scene_order` (required): List of scene numbers in desired order (e.g., [1, 3, 2, 4])

**Authentication:** Required

**Response:** Updated JobResponse with reordered storyboard

**Features:**
- Validates all scene numbers are present
- Updates scene_number field to match new positions
- Resets approval flag (requires re-approval before rendering)

**Error Handling:**
- 404: Job not found
- 400: No storyboard, empty scene_order, or invalid scene numbers
- 500: Update failed

**Example Usage:**
```
POST /api/v2/jobs/123/reorder?scene_order=1&scene_order=3&scene_order=2&scene_order=4
```

---

### 4. `GET /api/v2/jobs/{job_id}/metadata`
**Purpose:** Get comprehensive metadata for a video generation job

**Authentication:** Not required (public endpoint)

**Response:** Detailed metadata object including:

```json
{
  "job_id": 123,
  "status": "completed",
  "created_at": "2025-11-15T10:00:00",
  "updated_at": "2025-11-15T10:05:00",
  "approved": true,
  "approved_at": "2025-11-15T10:04:00",

  "scenes": {
    "total": 6,
    "completed": 6,
    "failed": 0,
    "details": [
      {
        "scene_number": 1,
        "duration": 5.0,
        "status": "completed",
        "has_image": true
      }
      // ... more scenes
    ]
  },

  "costs": {
    "estimated": 0.15,
    "actual": 0.12,
    "currency": "USD"
  },

  "metrics": {
    "refinement_count": 2,
    "download_count": 5
  },

  "video": {
    "available": true,
    "url": "/data/videos/123/final.mp4",
    "parameters": {
      "duration": 30,
      "aspect_ratio": "16:9",
      "style": "cinematic"
    }
  },

  "error": null
}
```

**Error Handling:**
- 404: Job not found
- 500: Failed to fetch metadata

---

### 5. Updated `GET /api/v2/jobs/{job_id}/video`
**Changes:** Now increments download_count on each video access

**Behavior:**
- Tracks downloads for both direct video access and exports
- Download count includes both `/video` and `/export` endpoint accesses

## Configuration Changes

### `backend/config.py`
Added new configuration setting:
```python
VIDEO_STORAGE_PATH: str = "./DATA/videos"
```

**Environment Variable:** Can be overridden with `VIDEO_STORAGE_PATH` env var

**Default Value:** `./DATA/videos` (relative to backend directory)

**Usage:** Base path for video storage, including exports subdirectory

## Import Updates

### `backend/main.py`
Added imports for new database functions:
```python
from .database import (
    # ... existing imports ...
    increment_download_count,
    get_download_count,
    refine_scene_in_storyboard,
    reorder_storyboard_scenes,
    get_refinement_count,
    increment_estimated_cost
)
```

## Testing Recommendations

### 1. Video Export Testing
```bash
# Test export with different formats and qualities
curl -X GET "http://localhost:8000/api/v2/jobs/1/export?format=mp4&quality=high" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o output.mp4

curl -X GET "http://localhost:8000/api/v2/jobs/1/export?format=webm&quality=low" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o output.webm
```

### 2. Scene Refinement Testing
```bash
# Refine with new image prompt
curl -X POST "http://localhost:8000/api/v2/jobs/1/refine?scene_number=2&new_image_prompt=A%20beautiful%20sunset%20over%20mountains" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Refine with new description
curl -X POST "http://localhost:8000/api/v2/jobs/1/refine?scene_number=3&new_description=Updated%20scene%20description" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test refinement limit (should fail on 6th attempt)
for i in {1..6}; do
  curl -X POST "http://localhost:8000/api/v2/jobs/1/refine?scene_number=1&new_description=Test%20$i" \
    -H "Authorization: Bearer YOUR_TOKEN"
done
```

### 3. Scene Reordering Testing
```bash
# Reorder scenes
curl -X POST "http://localhost:8000/api/v2/jobs/1/reorder?scene_order=1&scene_order=3&scene_order=2&scene_order=4" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Metadata Testing
```bash
# Get comprehensive metadata
curl -X GET "http://localhost:8000/api/v2/jobs/1/metadata"
```

## Dependencies

### System Requirements
- **ffmpeg** must be installed and available in system PATH
- ffmpeg is checked at runtime; endpoint returns 503 if unavailable

### Python Dependencies
All dependencies already present in the project:
- `subprocess` (standard library) - for ffmpeg execution
- `pathlib` (standard library) - for path handling
- `json` (standard library) - for JSON operations

## Production Deployment Checklist

1. **Install ffmpeg in Docker container:**
   ```dockerfile
   RUN apt-get update && apt-get install -y ffmpeg
   ```

2. **Set environment variables:**
   ```bash
   export VIDEO_STORAGE_PATH=/data/videos
   ```

3. **Configure persistent volume for exports:**
   ```yaml
   volumes:
     - video_storage:/data/videos
   ```

4. **Database migration:**
   - The new columns are automatically added via `init_db()`
   - Run application once to apply schema changes
   - Existing rows will have `download_count=0` and `refinement_count=0`

5. **Verify ffmpeg installation:**
   ```bash
   ffmpeg -version
   ```

## Rate Limiting Notes

### Refinement Limit
- Maximum 5 refinements per job (hard limit)
- Enforced at application level
- Returns 429 status code when exceeded
- Tracked via `refinement_count` column

### Download Tracking
- No limit on downloads
- Counter increments on each access
- Used for analytics and metrics

## Cost Tracking

### Refinement Costs
- Each image regeneration: ~$0.02 (added to estimated_cost)
- Cost increment happens when new_image_prompt is provided
- Does not increment for description-only updates

## Error Handling

### Video Export Errors
- Missing source video: 404 error
- ffmpeg unavailable: 503 error
- Export timeout (5 minutes): 500 error
- Disk full: 500 error with OSError details

### Refinement Errors
- Invalid scene number: 400 error
- Image generation failure: 500 error
- Refinement limit exceeded: 429 error

### Reordering Errors
- Invalid scene numbers: 400 error (validation checks all scenes present)
- Duplicate scene numbers: Validation fails
- Missing scenes: Validation fails

## Logging

All endpoints include comprehensive logging:
- Info level: Successful operations
- Error level: Failures with stack traces
- Logs include job_id for traceability

Example log entries:
```
INFO: Exporting job 123 to mp4/high
INFO: Video exported successfully: /data/videos/exports/123/mp4_high.mp4
INFO: Regenerating image for job 123, scene 2
INFO: Generated new image: https://replicate.delivery/...
ERROR: Failed to regenerate image: API timeout
ERROR: Error refining scene for job 123: Scene 10 not found
```

## Security Considerations

1. **Authentication:** All write endpoints (export, refine, reorder) require authentication
2. **Input Validation:** Query parameters validated with Pydantic patterns and constraints
3. **Path Traversal Prevention:** Export paths are generated securely using Path objects
4. **Rate Limiting:** Refinement limit prevents abuse
5. **File Permissions:** Exported files inherit system permissions (default: 0644)

## Future Enhancements (Not Implemented)

1. Remote video export support (currently only local files)
2. Batch export (multiple formats/qualities at once)
3. Export queue for long-running conversions
4. ClamAV scanning for uploaded/exported files
5. Custom quality presets via API
6. Async image regeneration for refinements
7. Refinement history tracking
8. Export format auto-detection from original video

## Summary

This implementation successfully delivers all required functionality for Task 9:

**Part 1: Video Export**
- ✅ GET /api/v2/jobs/{job_id}/export endpoint
- ✅ export_video() helper function
- ✅ ffmpeg integration with quality presets
- ✅ Format conversion (mp4, mov, webm)
- ✅ Export caching

**Part 2: Storyboard Refinement**
- ✅ POST /api/v2/jobs/{job_id}/refine endpoint
- ✅ Scene image regeneration with new prompts
- ✅ Scene description updates
- ✅ Approval reset on refinement
- ✅ Refinement count tracking (max 5)
- ✅ POST /api/v2/jobs/{job_id}/reorder endpoint
- ✅ Scene reordering with validation

**Part 3: Metadata and Downloads**
- ✅ GET /api/v2/jobs/{job_id}/metadata endpoint
- ✅ Download tracking (download_count column)
- ✅ Comprehensive metadata response

**Additional Features:**
- ✅ VIDEO_STORAGE_PATH configuration
- ✅ ffmpeg availability checking
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Cost tracking for refinements
- ✅ All endpoints properly authenticated
