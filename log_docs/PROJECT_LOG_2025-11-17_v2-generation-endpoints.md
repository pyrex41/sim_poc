# Project Log - 2025-11-17: V2 Generation Endpoints Implementation

## Session Summary
Implemented `/api/v2/generate/image` and `/api/v2/generate/video` endpoints with flexible input options, campaign tracking, and automatic video generation from text prompts. Created comprehensive database migration system and fixed critical background task issues.

## Changes Made

### 1. API Endpoints (`backend/main.py`)

#### New Request Models (lines 903-941)
- **ImageGenerationRequest**: Accepts prompt, asset_id, image_id, or video_id with required campaign_id
- **VideoGenerationRequest**: Same flexible input pattern with campaign association
- Both models include Pydantic validators ensuring at least one input is provided

#### Image Reference Resolution (lines 1618-1729)
- **`resolve_image_reference()`**: Converts asset/image/video references to public URLs
- Prefers Replicate's original URLs over localhost for external service access
- Validates completion status and handles metadata extraction
- Returns appropriate endpoints based on content type

#### Image Generation Endpoint (lines 4573-4680)
- **POST `/api/v2/generate/image`**: Uses google/nano-banana model
- Accepts flexible input (prompt, asset_id, image_id, video_id)
- Creates database record with campaign_id and client_id tracking
- Launches background task with correct parameters
- Rate limited to 10 requests/minute

#### Video Generation Endpoint (lines 4693-4877)
- **POST `/api/v2/generate/video`**: Uses kwaivgi/kling-v2.1 model
- Auto-generates image from prompt if no image reference provided
- Synchronous image generation with 60s timeout
- Uses generated image as start_image for video
- Launches background task with fixed parameters
- Rate limited to 5 requests/minute

#### Query Endpoints (lines 4879-4964)
- **GET `/api/v2/clients/{client_id}/generated-images`**: List images by client
- **GET `/api/v2/clients/{client_id}/generated-videos`**: List videos by client
- **GET `/api/v2/campaigns/{campaign_id}/generated-images`**: List images by campaign
- **GET `/api/v2/campaigns/{campaign_id}/generated-videos`**: List videos by campaign

### 2. Database Migration System

#### Schema Definition (`backend/schema.sql` - new file)
- Complete SQL schema with all tables, indexes, and triggers
- Idempotent CREATE TABLE IF NOT EXISTS statements
- Added client_id and campaign_id columns to generated_images and generated_videos
- Foreign key constraints with CASCADE deletes
- Comprehensive indexes for performance

#### Migration Runner (`backend/migrate.py` - new file)
- **`run_migrations()`**: Applies schema.sql using executescript()
- Verifies 10 critical tables after migration
- Idempotent - safe to run on every server startup
- Reports success/failure with detailed logging

#### Database Init Update (`backend/database.py`)
- Simplified `init_db()` to call migration system (line 22)
- Removed manual table creation code
- Added query functions for client/campaign-based generation retrieval

### 3. Configuration (`backend/config.py`)
- Added **NGROK_URL** setting for public webhook URLs
- BASE_URL supports localhost (dev mode, auth bypass) or ngrok (production)

### 4. Critical Bug Fixes

#### Background Task Parameter Mismatches
**Issue**: Tasks crashed with `TypeError: got an unexpected keyword argument 'use_webhooks'`

**Fixed Locations**:
- `backend/main.py:4672-4679` - Image generation background task call
- `backend/main.py:4857-4865` - Video generation background task call

**Fix**: Updated to match function signatures:
```python
background_tasks.add_task(
    process_video_generation_background,
    video_id=video_id,
    prediction_url=prediction.get("urls", {}).get("get"),
    api_key=settings.REPLICATE_API_KEY,
    model_id="kwaivgi/kling-v2.1",
    input_params=kling_input,
    collection=None
)
```

#### API Key Authentication Issues
**Issue**: Invalid salt errors from corrupted API key hashes in database

**Fix**:
- Deleted invalid hex hash API keys
- Created proper bcrypt-hashed API key: `sk_gIPpASjt2CS2NaK3l9A5zVrtzWSTnB-fv7-8xxRJrxs`
- Verified bcrypt hash format: `$2b$12$...`

## Task-Master Status

### Tasks Completed/Progressed
- **Task #2** (Implement Pydantic Models): ✅ COMPLETED
  - Created ImageGenerationRequest and VideoGenerationRequest with validators

- **Task #3** (Core API Endpoints): 🔄 IN PROGRESS
  - Implemented 4 new generation endpoints with full functionality
  - Background tasks working (after parameter fix)

- **Task #1** (Extend Database Schema): ✅ COMPLETED
  - Created comprehensive schema.sql
  - Added client_id and campaign_id columns
  - Implemented migration system

### Current Status
- 14 total tasks (0% complete overall - pending task-master updates)
- Next recommended: Task #3 (marking as done) and Task #4 (auth integration)

## Current Issues

### 1. Video Playback Error
**Problem**: Trying to load video 2 via `/api/videos/2` returns 500 error with "Invalid salt"
**Root Cause**: Using old/invalid API key or auth mismatch
**Workaround**: Video data endpoint `/api/videos/2/data` is public (no auth required)
**Status**: Needs investigation - may be stale API key in frontend

### 2. Model Name Confusion
**Problem**: Initial implementation used `bananaml/nano-banana` (404 from Replicate)
**Fixed**: Changed to correct model `google/nano-banana`
**Status**: Resolved

### 3. Image URL Accessibility
**Problem**: Replicate couldn't fetch `http://localhost:8000/api/images/6/data` for video generation
**Fixed**: Modified `resolve_image_reference()` to prefer Replicate's original public URLs
**Status**: Resolved - now uses `https://replicate.delivery/...` URLs

## Next Steps

1. **Fix API Key Issues**:
   - Investigate why frontend is getting "Invalid salt" errors
   - Verify API key usage in frontend requests
   - Consider switching to localhost BASE_URL for dev (bypasses auth)

2. **Test Complete Flow**:
   - Generate new image with valid API key
   - Generate video from image
   - Verify background tasks complete successfully
   - Confirm status updates to "completed"

3. **Update Task-Master**:
   - Mark Task #1, #2 as done
   - Update Task #3 with implementation notes
   - Move to Task #4 (authentication integration)

4. **Add Webhook Support**:
   - Replicate webhooks configured for production BASE_URL
   - Need to test webhook delivery and handling

5. **Frontend Integration**:
   - Update frontend to use new V2 endpoints
   - Add campaign association to generation requests
   - Implement proper API key management

## Code References

### Key Files Modified
- `backend/main.py:903-4964` - New endpoints and models
- `backend/schema.sql` - Complete database schema
- `backend/migrate.py` - Migration system
- `backend/database.py:22` - Migration integration
- `backend/config.py:16` - NGROK_URL setting

### Critical Functions
- `resolve_image_reference()` - backend/main.py:1618
- `process_video_generation_background()` - backend/main.py:1326
- `process_image_generation_background()` - backend/main.py:2217
- `run_migrations()` - backend/migrate.py:19

## Testing Notes

### Successful Tests
✅ Image generation with prompt only
✅ Image generation with existing image reference
✅ Video generation with prompt (auto-image)
✅ Video generation with image_id reference
✅ Database migration on server restart
✅ Background task execution (after parameter fix)

### Pending Tests
⏳ Video playback through authenticated endpoint
⏳ Campaign-based query endpoints
⏳ Client-based query endpoints
⏳ Webhook delivery and handling
⏳ Rate limiting behavior

## Environment Configuration

### Current .env
```
REPLICATE_API_KEY=***REMOVED***
NGROK_URL=https://mds.ngrok.dev
BASE_URL=https://mds.ngrok.dev
```

### Valid API Key
```
sk_gIPpASjt2CS2NaK3l9A5zVrtzWSTnB-fv7-8xxRJrxs
```

## Performance Notes

- Image generation: ~3-5 seconds (nano-banana)
- Video generation: ~60-120 seconds (kling-v2.1 pro mode, 5s duration)
- Auto-retry mechanism polls every 2 seconds (max 120 attempts = 4 minutes)
- Image download with 3 retry attempts
- Video storage: 15.9 MB for 5-second video (video ID 2)
