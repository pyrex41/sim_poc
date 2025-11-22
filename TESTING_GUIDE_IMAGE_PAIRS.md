# Image Pair Selection & Video Generation - Testing Guide

## Overview

This guide provides comprehensive instructions for testing the AI-powered image pair selection and video generation pipeline.

## Feature Summary

**What it does:**
1. Fetches image assets from a campaign
2. Uses xAI Grok-4-fast-1 to intelligently select optimal image pairs based on visual continuity, thematic coherence, and brand consistency
3. Generates videos from each pair in FULL PARALLEL (unlimited concurrency) using Veo3 or Hailuo-2.0
4. Combines all clips into a final video with ffmpeg
5. Stores both individual clips and the combined video
6. Provides detailed sub-job tracking and progress polling

## Prerequisites

### 1. Environment Variables

Add to your `.env` file or environment:

```bash
# Required: xAI API key for Grok model
XAI_API_KEY=your_xai_api_key_here

# Required: Replicate API key for video generation
REPLICATE_API_KEY=your_replicate_api_key_here

# Optional: Choose video generation model (default: veo3)
VIDEO_GENERATION_MODEL=veo3  # or "hailuo-2.0"
```

### 2. Database Migration

Run database migrations to create the `video_sub_jobs` table:

```bash
cd backend
python migrate.py
```

This will:
- Create the `video_sub_jobs` table with all necessary columns
- Add `thumbnail_blob_id` column to `assets` table (for V3 thumbnail storage)

### 3. System Requirements

Ensure `ffmpeg` is installed on your system:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

### 4. Test Data Setup

You need:
- At least one client
- At least one campaign associated with that client
- **At least 2 image assets** uploaded to the campaign (preferably 6-10 for better testing)

## API Endpoints

### 1. Create Job from Image Pairs

**Endpoint:** `POST /api/v3/jobs/from-image-pairs`

**Purpose:** Creates a job that selects image pairs and generates videos

**Request Body:**
```json
{
  "campaignId": "campaign-uuid",
  "clientId": "client-uuid",
  "clipDuration": 5.0,
  "numPairs": 5
}
```

**Parameters:**
- `campaignId` (required): UUID of the campaign with image assets
- `clientId` (optional): UUID of the client (used for brand guidelines)
- `clipDuration` (optional): Duration in seconds for each generated clip (default: 8 for Veo3, 6 for Hailuo-2.0)
- `numPairs` (optional): Target number of image pairs to select (Grok will decide optimal number if not specified)

**Response:**
```json
{
  "data": {
    "jobId": "123",
    "status": "image_pair_selection",
    "totalPairs": 5,
    "message": "Job created with 5 image pairs. Video generation started."
  },
  "error": null,
  "meta": {
    "timestamp": "2025-11-21T20:30:00Z",
    "version": "v3"
  }
}
```

**Workflow:**
1. Fetches image assets from the campaign
2. Calls xAI Grok-4-fast-1 to select optimal pairs
3. Creates main job with status "image_pair_selection"
4. Stores selected pairs in job parameters
5. Launches parallel video generation for ALL pairs (no limit)
6. Returns immediately with job ID for polling

### 2. Get Sub-Job Status

**Endpoint:** `GET /api/v3/jobs/{job_id}/sub-jobs`

**Purpose:** Get detailed progress of all sub-jobs (individual video generations)

**Response:**
```json
{
  "data": {
    "subJobs": [
      {
        "id": "sub-job-uuid-1",
        "jobId": 123,
        "subJobNumber": 1,
        "image1AssetId": "asset-uuid-1",
        "image2AssetId": "asset-uuid-2",
        "replicatePredictionId": "pred-xyz123",
        "modelId": "veo3",
        "status": "completed",
        "progress": 1.0,
        "videoUrl": "/api/v3/videos/123/clips/clip_001.mp4",
        "videoBlobId": "blob-uuid",
        "durationSeconds": 8.0,
        "estimatedCost": 1.20,
        "actualCost": 1.20,
        "errorMessage": null,
        "retryCount": 0,
        "startedAt": "2025-11-21T20:30:05Z",
        "completedAt": "2025-11-21T20:32:15Z",
        "createdAt": "2025-11-21T20:30:00Z",
        "updatedAt": "2025-11-21T20:32:15Z"
      }
    ],
    "summary": {
      "total": 5,
      "pending": 0,
      "processing": 1,
      "completed": 3,
      "failed": 1
    }
  },
  "error": null,
  "meta": {...}
}
```

### 3. Poll Main Job Status

**Endpoint:** `GET /api/v3/jobs/{job_id}`

**Purpose:** Get overall job status and combined video URL

**Response (when completed):**
```json
{
  "data": {
    "id": "123",
    "status": "completed",
    "progress": {
      "selected_pairs": 5,
      "total_clips": 5,
      "successful_clips": 4,
      "failed_clips": 1,
      "clip_urls": [
        "/api/v3/videos/123/clips/clip_001.mp4",
        "/api/v3/videos/123/clips/clip_002.mp4",
        ...
      ],
      "total_cost": 4.80
    },
    "videoUrl": "/api/v3/videos/123/combined",
    "actualCost": 4.80,
    ...
  }
}
```

## Testing Workflow

### Step 1: Upload Test Images

Upload at least 6-10 images to a campaign:

```bash
# Using curl or Postman
POST /api/v3/assets/upload
Content-Type: multipart/form-data

{
  "uploadType": "file",
  "name": "Product Image 1",
  "type": "image",
  "campaignId": "your-campaign-id",
  "tags": ["product", "hero-shot"],
  "file": <binary image data>
}
```

**Tip:** Use images with visual continuity (e.g., product from different angles, sequential scenes) for better pair selection.

### Step 2: Create Job

```bash
curl -X POST http://localhost:8000/api/v3/jobs/from-image-pairs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "campaignId": "your-campaign-id",
    "clientId": "your-client-id",
    "clipDuration": 6.0,
    "numPairs": 3
  }'
```

**Expected Response:**
- Job ID returned immediately
- Status: "image_pair_selection"
- Total pairs count

**Timeline:**
- xAI Grok selection: ~5-15 seconds
- Job creation: <1 second
- Background video generation starts immediately

### Step 3: Monitor Sub-Jobs

Poll the sub-jobs endpoint to track progress:

```bash
curl http://localhost:8000/api/v3/jobs/{job_id}/sub-jobs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Progression:**

1. **Initial state** (after job creation):
   ```json
   {
     "summary": {
       "total": 3,
       "pending": 3,
       "processing": 0,
       "completed": 0,
       "failed": 0
     }
   }
   ```

2. **During generation** (all process in parallel):
   ```json
   {
     "summary": {
       "total": 3,
       "pending": 0,
       "processing": 3,  // ALL running simultaneously
       "completed": 0,
       "failed": 0
     }
   }
   ```

3. **Completion**:
   ```json
   {
     "summary": {
       "total": 3,
       "pending": 0,
       "processing": 0,
       "completed": 3,
       "failed": 0
     }
   }
   ```

**Timeline Expectations:**
- Veo3: ~90-120 seconds per clip (ALL run in parallel)
- Hailuo-2.0: ~120-180 seconds per clip (ALL run in parallel)
- With 3 pairs, expect total time = single clip generation time (due to full parallelism)

### Step 4: Monitor Main Job

Poll the main job endpoint:

```bash
curl http://localhost:8000/api/v3/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Status Progression:**

1. `image_pair_selection` - Grok is selecting pairs
2. `sub_job_processing` - Videos are being generated
3. `video_combining` - ffmpeg is combining clips
4. `completed` - Final video ready

### Step 5: Access Videos

Once completed, access the videos:

**Individual clips:**
```
GET /api/v3/videos/{job_id}/clips/clip_001.mp4
GET /api/v3/videos/{job_id}/clips/clip_002.mp4
GET /api/v3/videos/{job_id}/clips/clip_003.mp4
```

**Combined video:**
```
GET /api/v3/videos/{job_id}/combined
```

**Storage location:**
```
DATA/videos/{job_id}/
├── clips/
│   ├── clip_001.mp4
│   ├── clip_002.mp4
│   └── clip_003.mp4
└── combined.mp4
```

## Expected Behavior

### Parallel Processing

**CRITICAL:** All video generations run simultaneously with NO concurrency limit.

- With 3 pairs: All 3 process at the same time
- With 10 pairs: All 10 process at the same time
- With 50 pairs: All 50 process at the same time

**Why?** This was explicitly requested by the user for maximum speed.

### Cost Tracking

**Veo3 Pricing:**
- $0.15 per second of generated video
- 8-second clip = $1.20
- 10 clips × 8 seconds = $12.00 total

**Hailuo-2.0 Pricing:**
- $0.20 per generation (flat rate)
- 10 clips = $2.00 total

### Error Handling

**Partial failures are supported:**
- If 3/5 sub-jobs succeed, combined video is still created from the 3 successful clips
- Failed sub-jobs are tracked with `errorMessage` field
- Main job status shows both `successful_clips` and `failed_clips` counts

**Complete failures:**
- If ALL sub-jobs fail, main job status = "failed"
- Error message stored in job metadata

## Testing Scenarios

### Scenario 1: Happy Path (3 pairs, all succeed)

1. Upload 6 images to a campaign
2. Create job with `numPairs: 3`
3. Verify Grok selects 3 pairs
4. Monitor sub-jobs: all should move to "processing" simultaneously
5. Wait for all to complete (~90-120 seconds for Veo3)
6. Verify combined video exists and plays correctly
7. Check cost tracking matches expectations

**Expected outcome:**
- ✅ 3 clips generated
- ✅ Combined video created
- ✅ All clips in correct order
- ✅ Cost calculated correctly

### Scenario 2: High Volume (10 pairs)

1. Upload 20 images
2. Create job with `numPairs: 10`
3. Verify ALL 10 sub-jobs process in parallel
4. Monitor resource usage (CPU, memory, network)
5. Verify combined video with 10 clips

**Expected outcome:**
- ✅ All 10 process simultaneously (no queuing)
- ✅ Total time ≈ single clip time (due to parallelism)
- ✅ Combined video length ≈ 10 × clip_duration

### Scenario 3: Partial Failure

Simulate by temporarily making Replicate API unavailable or using invalid asset URLs:

1. Create job with mixed valid/invalid assets
2. Monitor sub-jobs: some succeed, some fail
3. Verify combined video created from successful clips only
4. Check summary shows correct counts

**Expected outcome:**
- ✅ Successful clips combined
- ✅ Failed sub-jobs marked with error messages
- ✅ Main job completes with metadata about failures

### Scenario 4: Different Models

**Test Veo3:**
```bash
# Set in .env
VIDEO_GENERATION_MODEL=veo3
```
- Expect 8-second clips (default)
- Cost: $0.15/second

**Test Hailuo-2.0:**
```bash
# Set in .env
VIDEO_GENERATION_MODEL=hailuo-2.0
```
- Expect 6-second clips (default)
- Cost: $0.20/generation

**Expected outcome:**
- ✅ Model switch reflected in `modelId` field of sub-jobs
- ✅ Different pricing applied correctly
- ✅ Different default durations

### Scenario 5: Custom Clip Duration

Test with various durations:

```bash
# 3-second clips (fast test)
"clipDuration": 3.0

# 10-second clips (longer videos)
"clipDuration": 10.0
```

**Expected outcome:**
- ✅ Generated videos match requested duration
- ✅ Cost scales with duration (for Veo3)

## Debugging

### Enable Debug Logging

Add to your backend startup:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Sub-Job Details

Query database directly:

```sql
SELECT * FROM video_sub_jobs WHERE job_id = 123;
```

### Inspect Replicate Predictions

Check the `replicate_prediction_id` field and visit:
```
https://replicate.com/p/{prediction_id}
```

### Check FFmpeg Output

Look for ffmpeg logs in console output:

```
Running ffmpeg command: ffmpeg -f concat -safe 0 -i /tmp/concat_file.txt ...
```

### Verify File Storage

Check that files are actually written:

```bash
ls -lh DATA/videos/{job_id}/clips/
ls -lh DATA/videos/{job_id}/combined.mp4
```

## Common Issues

### Issue 1: "ffmpeg is not available"

**Solution:** Install ffmpeg (see Prerequisites)

### Issue 2: xAI API key invalid

**Error:** "XAI_API_KEY not configured"

**Solution:**
1. Verify XAI_API_KEY is set in environment
2. Check key validity at https://console.x.ai
3. Ensure key has proper permissions

### Issue 3: Replicate timeout

**Error:** "Prediction timed out"

**Cause:** Replicate can take 90-180 seconds per prediction

**Solution:**
- Increase timeout in replicate_client.py (currently 600s)
- Monitor Replicate dashboard for queue status

### Issue 4: Not enough image assets

**Error:** "Need at least 2 image assets, but campaign has 1"

**Solution:** Upload more images to the campaign

### Issue 5: Combined video corrupted

**Possible causes:**
- Clips have different resolutions/codecs
- ffmpeg command failed
- Partial file writes

**Solution:**
1. Check ffmpeg logs for errors
2. Verify individual clips play correctly
3. Ensure sufficient disk space

## Performance Metrics

Expected performance benchmarks:

| Metric | Value |
|--------|-------|
| xAI Grok selection time | 5-15 seconds |
| Veo3 generation time per clip | 90-120 seconds |
| Hailuo-2.0 generation time per clip | 120-180 seconds |
| FFmpeg combine time (10 clips) | 5-15 seconds |
| **Total time for 10 pairs (Veo3)** | **~110 seconds** (due to parallelism) |

## Success Criteria

A successful end-to-end test should demonstrate:

✅ Image pair selection completes with reasonable pairs
✅ ALL sub-jobs run in parallel (no sequential processing)
✅ Individual clips are generated successfully
✅ Combined video plays correctly
✅ Clips are in the correct order (as determined by Grok)
✅ Cost tracking is accurate
✅ Partial failures are handled gracefully
✅ API responses match expected schemas
✅ Files are stored in correct locations
✅ Sub-job polling shows real-time progress

## Next Steps

After successful testing:

1. **Frontend Integration**: Build polling UI to show sub-job progress
2. **Retry Logic**: Add automatic retry for failed sub-jobs
3. **Cost Estimation**: Add pre-generation cost estimate endpoint
4. **Video Preview**: Add thumbnail extraction for combined video
5. **Notifications**: Add webhook/email notifications on completion
6. **Analytics**: Track success rates, average generation times, costs
7. **Optimization**: Consider caching Grok selections for similar campaigns

## Support

For issues or questions:
- Check backend logs: `tail -f backend.log`
- Review Replicate dashboard: https://replicate.com/predictions
- Test xAI connection: `curl https://api.x.ai/v1/models -H "Authorization: Bearer $XAI_API_KEY"`
- Verify ffmpeg: `ffmpeg -version`
