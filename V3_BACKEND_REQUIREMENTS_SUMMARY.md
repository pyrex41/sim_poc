# V3 Backend Requirements - Quick Summary

**Date:** 2025-11-19
**Full Details:** See `V3_BACKEND_REQUIREMENTS.md`

---

## TL;DR - What We Need

### 1. Asset URL Handling ⭐ HIGH PRIORITY
**Goal:** Frontend passes asset URLs → Backend downloads and stores as blobs

**What to implement:**
- Accept `url` field in `POST /api/v3/assets`
- Accept asset URLs in job creation creative.assets array
- Download assets from URLs automatically
- Store as blobs in database (new `asset_blobs` table)
- Serve blobs via `GET /api/v3/assets/{id}/data`
- Return V3 URLs instead of V2 URLs

**Example Request:**
```json
POST /api/v3/jobs
{
  "context": {"clientId": "123"},
  "adBasics": {...},
  "creative": {
    "direction": {"style": "Modern"},
    "assets": [
      {
        "url": "https://example.com/product.jpg",
        "type": "image",
        "name": "Product Shot",
        "role": "hero"
      }
    ]
  }
}
```

**What happens:**
1. Backend downloads `product.jpg`
2. Stores as blob with UUID
3. Creates asset record
4. Uses asset in scene generation
5. Returns asset with V3 URL: `/api/v3/assets/{uuid}/data`

---

### 2. Scene Generation ⭐ HIGH PRIORITY
**Goal:** Generate video scenes automatically when job is created

**What to implement:**
- Generate 3-7 scenes on job creation using AI/LLM
- Store scenes in new `job_scenes` table
- Include scenes in job status response
- Implement scene regeneration endpoint
- Support storyboard approval workflow

**Example Response:**
```json
GET /api/v3/jobs/{id}
{
  "data": {
    "id": "job-123",
    "status": "storyboard_review",
    "scenes": [
      {
        "id": "scene-1",
        "sceneNumber": 1,
        "duration": 6.0,
        "description": "Wide shot of urban environment",
        "script": "Life moves fast in the city.",
        "assets": ["asset-uuid-1"]
      }
    ]
  }
}
```

**Scene Regeneration:**
```json
POST /api/v3/jobs/{id}/actions
{
  "action": "regenerate_scene",
  "sceneNumber": 2,
  "feedback": "Make it more energetic"
}
```

---

## Database Schema Changes

### New Tables

**asset_blobs:**
```sql
CREATE TABLE asset_blobs (
    id UUID PRIMARY KEY,
    data BYTEA NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**job_scenes:**
```sql
CREATE TABLE job_scenes (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    scene_number INTEGER NOT NULL,
    duration_seconds DECIMAL(5,2),
    description TEXT,
    script TEXT,
    shot_type VARCHAR(50),
    transition VARCHAR(50),
    assets JSONB,  -- Array of asset IDs
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, scene_number)
);
```

**Update assets table:**
```sql
ALTER TABLE assets
    ADD COLUMN blob_id UUID REFERENCES asset_blobs(id),
    ADD COLUMN source_url TEXT;
```

---

## New Endpoints Required

### Asset Blob Serving
- `GET /api/v3/assets/{id}/data` - Serve actual blob data

### Scene Management
- `GET /api/v3/jobs/{job_id}/scenes` - List all scenes
- `GET /api/v3/jobs/{job_id}/scenes/{scene_number}` - Get specific scene
- `PUT /api/v3/jobs/{job_id}/scenes/{scene_number}` - Update scene

### Job Actions (Enhanced)
- `POST /api/v3/jobs/{id}/actions` with:
  - `action: "regenerate_scene"` + `sceneNumber`
  - `action: "regenerate_all_scenes"` + `feedback`
  - `action: "approve_storyboard"`
  - `action: "reject_storyboard"` + `feedback`

---

## Implementation Phases

### Phase 1: Asset Handling (Week 1-2)
1. Add asset URL download functionality
2. Implement blob storage (Postgres BYTEA or S3)
3. Create asset blob serving endpoint
4. Update job creation to accept asset URLs
5. Test with various asset types

**Deliverable:** Assets can be provided via URL and are stored as blobs

### Phase 2: Scene Generation (Week 3-4)
1. Integrate AI/LLM service (OpenAI GPT-4 or Claude)
2. Implement scene generation logic
3. Create scene database schema
4. Add scenes to job creation flow
5. Implement regeneration endpoints

**Deliverable:** Jobs automatically generate scenes for approval

### Phase 3: Workflow (Week 5)
1. Implement storyboard approval actions
2. Add scene management endpoints
3. Complete job progress tracking
4. End-to-end testing

**Deliverable:** Complete job workflow operational

---

## Critical Dependencies

### Must Have:
- AI/LLM API key (OpenAI or Anthropic)
- HTTP client library for downloads (`httpx` or `aiohttp`)
- Database support for BYTEA or S3 credentials

### Nice to Have:
- Media processing libraries (Pillow, ffmpeg)
- CDN for asset serving
- Caching layer

---

## Environment Variables Needed

```bash
# Asset handling
MAX_ASSET_DOWNLOAD_SIZE_MB=100
ASSET_DOWNLOAD_TIMEOUT_SECONDS=60

# Scene generation
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4
SCENES_PER_VIDEO_MIN=3
SCENES_PER_VIDEO_MAX=7

# Storage (if using S3)
BLOB_STORAGE_TYPE=postgres  # or s3
S3_BUCKET_NAME=...
S3_REGION=...
```

---

## Testing Checklist

### Asset URL Tests:
- [ ] Download and store image from URL
- [ ] Download and store video from URL
- [ ] Handle invalid URLs gracefully
- [ ] Serve blob data via V3 endpoint
- [ ] Support large file downloads

### Scene Generation Tests:
- [ ] Generate scenes on job creation
- [ ] Scenes include all required fields
- [ ] Regenerate single scene with feedback
- [ ] Regenerate all scenes
- [ ] Scenes reference correct assets

### Workflow Tests:
- [ ] Job enters storyboard_review state
- [ ] User can approve storyboard
- [ ] User can reject with feedback
- [ ] Progress tracking updates correctly

---

## Success Criteria

**Phase 1 Success:**
- ✅ Can create job with asset URLs
- ✅ Assets downloaded and stored as blobs
- ✅ Assets served via `/api/v3/assets/{id}/data`
- ✅ No V2 URLs in responses

**Phase 2 Success:**
- ✅ Jobs automatically generate 3-7 scenes
- ✅ Scenes have descriptions, scripts, assets
- ✅ Can regenerate individual scenes
- ✅ Job status includes scenes array

**Phase 3 Success:**
- ✅ Storyboard approval workflow works
- ✅ Scene management endpoints functional
- ✅ Complete job workflow end-to-end

---

## Questions for Backend Team

1. **When can Phase 1 start?** (Asset URL handling)
2. **Which AI provider?** (OpenAI vs Anthropic vs Custom)
3. **Blob storage preference?** (Postgres vs S3)
4. **Existing video pipeline?** (To integrate scene generation)
5. **Resource constraints?** (API limits, storage limits)

---

## Next Steps

1. Backend team reviews requirements
2. Backend team provides timeline estimate
3. Backend team identifies any blockers
4. Coordinate Phase 1 implementation
5. Frontend prepares UI for scene management

---

**Full Details:** See `V3_BACKEND_REQUIREMENTS.md` for:
- Complete API specifications
- Detailed Pydantic models
- SQL migration scripts
- Example requests/responses
- Edge case handling

---

**Contact:** Frontend team ready to assist with integration testing
**Timeline Target:** Complete Phase 1 & 2 within 4 weeks
