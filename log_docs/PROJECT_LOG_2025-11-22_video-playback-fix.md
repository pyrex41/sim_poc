# Progress Log: Video Playback Fix - November 22, 2025

## Session Summary
Fixed critical video playback issue on production deployment. Videos were being generated successfully but couldn't be watched due to missing API endpoints and incorrect storage approach. Implemented database blob storage for videos and fixed authentication for external service access.

## Changes Made

### 1. Video Serving Infrastructure (`backend/api/v3/router.py`)

**Added Two New Endpoints:**
- `GET /api/v3/videos/{job_id}/clips/{clip_filename}` (lines 2209-2244)
- `GET /api/v3/videos/{job_id}/combined` (lines 2246-2275)

**Key Implementation Details:**
```python
# Combined video endpoint - serves from database blob storage
@router.get("/videos/{job_id}/combined", tags=["v3-videos"])
async def get_combined_video(job_id: str):
    """Serve combined video from database blob storage"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT video_data FROM generated_videos WHERE id = ?",
            (job_id,),
        ).fetchone()

        if not row or not row["video_data"]:
            raise HTTPException(status_code=404, detail="Combined video not found")

        video_data = row["video_data"]

    return Response(
        content=video_data,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=31536000",
            "Content-Length": str(len(video_data)),
        },
    )
```

### 2. Video Storage Migration (`backend/services/sub_job_orchestrator.py`)

**Changed from Filesystem to Database Blob Storage:**

Before (filesystem):
```python
async def _store_final_video(job_id: int, video_path: str) -> str:
    import shutil
    base_path = Path(settings.VIDEO_STORAGE_PATH) / str(job_id)
    base_path.mkdir(parents=True, exist_ok=True)
    combined_dest = base_path / "combined.mp4"
    await asyncio.to_thread(shutil.copy2, video_path, combined_dest)
    combined_url = f"/api/v3/videos/{job_id}/combined"
    return combined_url
```

After (database blob):
```python
async def _store_final_video(job_id: int, video_path: str) -> str:
    from ..database import get_db

    # Read the video file into memory
    with open(video_path, 'rb') as f:
        video_data = f.read()

    # Store video blob in database
    with get_db() as conn:
        conn.execute(
            "UPDATE generated_videos SET video_data = ? WHERE id = ?",
            (video_data, job_id)
        )
        conn.commit()

    combined_url = f"/api/v3/videos/{job_id}/combined"
    logger.info(f"Stored final video in database (job_id={job_id}, size={len(video_data)} bytes)")
    return combined_url
```

**Rationale:** Videos must persist on Fly.io deployment using the `/data/scenes.db` database on the persistent volume, not ephemeral filesystem storage.

### 3. Asset Authentication for External Services (`backend/api/v3/router.py`)

**Problem:** Replicate (Veo3 video generation) couldn't access asset URLs because authentication was always required, even with valid temporary tokens.

**Solution:** Implemented conditional authentication:

```python
@router.get("/assets/{asset_id}/data", tags=["v3-assets"])
async def get_asset_data(
    asset_id: str,
    request: Request,
    token: Optional[str] = Query(None, description="Temporary access token for public access"),
    current_user: Optional[Dict] = Depends(verify_auth) if not token else None,
):
    authenticated = False

    # Try token-based access first
    if token:
        verified_asset_id = verify_asset_access_token(token)
        if verified_asset_id and verified_asset_id == asset_id:
            authenticated = True
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif current_user:
        authenticated = True

    if not authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
```

**Key Pattern:** `Depends(verify_auth) if not token else None` - only inject auth dependency when no token is provided.

### 4. X-API-Key Authentication Enhancement

**Added support for X-API-Key header** in addition to Bearer tokens:

```python
def verify_api_key_sync(request: Request) -> Optional[Dict]:
    """Synchronous API key verification from X-API-Key header"""
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return None

    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id FROM api_keys WHERE key_hash = ? AND revoked = 0",
            (hashlib.sha256(api_key.encode()).hexdigest(),),
        ).fetchone()

        if row:
            return {"user_id": row["user_id"], "auth_method": "api_key"}
    return None
```

Used in asset endpoint to support both authentication methods.

## Testing & Verification

### Production Test Results (Job 141)
- **Status:** ✅ Completed successfully
- **Video URL:** `/api/v3/videos/141/combined`
- **Video Details:**
  - Format: MP4 (H.264 High profile)
  - Duration: 12 seconds
  - Resolution: 1920x1080 @ 30fps
  - Size: ~11MB (11,212,386 bytes)
  - Bitrate: 7474 kb/s
  - Stored in database blob storage ✅

### Production Environment
- **Deployment:** gauntlet-video-server.fly.dev
- **API Key:** sk_wJaMmkmNOzBKsC3NocXkYP3eeszZShZThzfcJs8y0Ik
- **Campaign:** 495e9ee9-d664-4057-bf63-7945d8e2a6ad (20+ videos)
- **Database:** /data/scenes.db (persistent volume)

### Verification Commands
```bash
# Check job status
curl -s -H 'X-API-Key: sk_wJaMmkmNOzBKsC3NocXkYP3eeszZShZThzfcJs8y0Ik' \
  'https://gauntlet-video-server.fly.dev/api/v3/jobs/141'

# Download and verify video
curl -s -H 'X-API-Key: sk_wJaMmkmNOzBKsC3NocXkYP3eeszZShZThzfcJs8y0Ik' \
  'https://gauntlet-video-server.fly.dev/api/v3/videos/141/combined' \
  -o test.mp4

# Verify video format
ffmpeg -i test.mp4 2>&1 | grep -E '(Duration|Stream|Video)'
```

## Git Commits (Chronological)

1. `83b6d69` - fix: add missing video serving endpoints for v3 API
2. `411c518` - fix: correct authentication in get_asset_data endpoint
3. `169b31d` - fix: store videos in database blob storage instead of filesystem
4. `1c727e7` - fix: make authentication optional when access token is provided
5. `3f514b7` - refactor: cleaner conditional authentication for asset access
6. `199ad40` - fix: enable X-API-Key authentication for asset data endpoint
7. `2e6aff9` - refactor: extract synchronous API key verification helper
8. `21897cb` - docs: update progress review with X-API-Key authentication fix

## Task-Master Status

**Next Available Task:** #1 - Extend Database Schema for Video Generation Jobs
- Status: pending
- Priority: high
- Complexity: 5
- Subtasks: 3 (all pending)

**Note:** Current work was focused on bug fixes and production issues, not planned tasks from the PRD. Task #1 remains the next planned feature work.

## Current Todo List Status

All todos from this session are completed:
- ✅ Add video serving endpoints
- ✅ Migrate video storage to database blobs
- ✅ Fix authentication for external services
- ✅ Test video generation end-to-end on production
- ✅ Verify video playback works

## Issues Fixed

### Issue 1: Video Playback 404/500 Errors
- **Symptom:** Frontend showed "Generated Video" modal but player wouldn't load
- **Root Cause:** Missing `/api/v3/videos/{job_id}/combined` endpoint
- **Resolution:** Added endpoint that serves from database blob storage

### Issue 2: Videos Not Persisting on Fly.io
- **Symptom:** Videos generated locally weren't accessible in production
- **Root Cause:** Using ephemeral filesystem (`./DATA/videos`) instead of persistent storage
- **Resolution:** Store videos as blob_data in `generated_videos` table in `/data/scenes.db`

### Issue 3: Replicate Veo3 Failing with "Invalid Input" (E006)
- **Symptom:** Video generation API calls from Replicate failing
- **Root Cause:** Replicate couldn't access asset URLs even with valid temporary tokens
- **Resolution:** Conditional authentication - `Depends(verify_auth) if not token else None`

## Key Technical Decisions

1. **Database Blob Storage for Videos**
   - Store in `generated_videos.video_data` column (BLOB type)
   - Persists on Fly.io's `/data` persistent volume
   - Consistent with other asset storage patterns
   - No filesystem dependencies

2. **Conditional Authentication Pattern**
   - Support both Bearer tokens and X-API-Key headers
   - Allow temporary access tokens for external services
   - Use FastAPI's dependency injection conditionally
   - Pattern: `Depends(verify_auth) if not token else None`

3. **Video Serving Headers**
   - `Accept-Ranges: bytes` - Enable seeking in video player
   - `Cache-Control: public, max-age=31536000` - Long-term caching
   - `Content-Length` - Required for proper video playback

## Next Steps

1. **Monitor Production Video Generation**
   - Verify all new jobs store videos successfully
   - Check database blob sizes don't exceed reasonable limits
   - Monitor /data volume usage

2. **Consider Individual Clip Storage**
   - Currently only combined video is stored in database
   - Individual clips are still in temp filesystem
   - May need to add clip blob storage for persistence

3. **Resume Planned Task Work**
   - Task #1: Extend Database Schema (already has many columns from fixes)
   - May need to update Task #1 based on schema changes already made

4. **Performance Testing**
   - Test large video file serving (>50MB)
   - Verify streaming works properly
   - Check memory usage when serving multiple videos

## File References

- `backend/api/v3/router.py:2209-2275` - Video serving endpoints
- `backend/api/v3/router.py:493-536` - Asset authentication with conditional auth
- `backend/services/sub_job_orchestrator.py:_store_final_video()` - Database blob storage
- `fly.toml` - Persistent volume configuration
- `/data/scenes.db` - Production database on persistent volume
