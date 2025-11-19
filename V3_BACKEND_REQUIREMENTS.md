# V3 Backend Requirements - Complete Integration

**Date:** 2025-11-19
**Purpose:** Detailed requirements for complete V3 API integration
**Priority:** High

---

## Overview

This document outlines the additional backend features required for complete V3 API integration, focusing on:
1. Asset URL handling with automatic download and blob storage
2. Scene generation functionality
3. Complete job workflow implementation

---

## 1. Asset URL Handling & Blob Storage

### Current Behavior
- Frontend passes asset URLs
- Backend stores URL references
- Assets served from V2 endpoint: `http://localhost:8000/api/v2/assets/{id}`

### Required Behavior
When an asset URL is provided (either in job creation or asset upload):

#### 1.1 Asset Upload via URL

**Endpoint:** `POST /api/v3/assets`

**Current Request Body:**
```json
{
  "name": "Product Image",
  "type": "image",
  "clientId": "client-123",
  "campaignId": "campaign-456",
  "tags": ["product", "hero"]
}
```

**Required Enhancement:**
```json
{
  "name": "Product Image",
  "type": "image",
  "url": "https://example.com/images/product.jpg",  // NEW: Optional URL field
  "clientId": "client-123",
  "campaignId": "campaign-456",
  "tags": ["product", "hero"]
}
```

**Backend Processing:**
1. **If `url` is provided:**
   - Download the asset from the URL
   - Validate file type matches `type` field
   - Extract metadata (size, dimensions for images/videos, duration for audio)
   - Store as blob in database (recommended: separate `asset_blobs` table)
   - Generate internal asset ID
   - Create asset record with metadata

2. **If `url` is NOT provided:**
   - Expect multipart/form-data file upload (existing behavior)

#### 1.2 Job Creation with Asset URLs

**Endpoint:** `POST /api/v3/jobs`

**Current Request:**
```json
{
  "context": {
    "clientId": "client-123"
  },
  "adBasics": {
    "product": "Smart Watch",
    "targetAudience": "Tech enthusiasts",
    "keyMessage": "Stay connected",
    "callToAction": "Buy Now"
  },
  "creative": {
    "direction": {
      "style": "Modern"
    }
  }
}
```

**Required Enhancement:**
```json
{
  "context": {
    "clientId": "client-123"
  },
  "adBasics": {
    "product": "Smart Watch",
    "targetAudience": "Tech enthusiasts",
    "keyMessage": "Stay connected",
    "callToAction": "Buy Now"
  },
  "creative": {
    "direction": {
      "style": "Modern"
    },
    "assets": [  // NEW: Asset URLs or IDs
      {
        "url": "https://example.com/product-hero.jpg",
        "type": "image",
        "name": "Hero Image",
        "role": "product_shot"  // Optional: hint for scene placement
      },
      {
        "url": "https://example.com/lifestyle.mp4",
        "type": "video",
        "name": "Lifestyle Clip",
        "role": "background"
      }
    ]
  }
}
```

**Backend Processing:**
1. For each asset in `creative.assets`:
   - Download asset from URL
   - Store as blob
   - Create asset record linked to job
   - Return asset ID in response
   - Use asset ID in scene generation

#### 1.3 Database Schema Changes

**Recommended Structure:**

```sql
-- New table for blob storage
CREATE TABLE asset_blobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data BYTEA NOT NULL,  -- Actual blob data
    content_type VARCHAR(100) NOT NULL,  -- MIME type
    size_bytes BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Update existing assets table
ALTER TABLE assets
    ADD COLUMN blob_id UUID REFERENCES asset_blobs(id),
    ADD COLUMN source_url TEXT,  -- Original URL if downloaded
    ALTER COLUMN url SET DEFAULT NULL;  -- Internal URL can be generated

-- Index for performance
CREATE INDEX idx_assets_blob_id ON assets(blob_id);
```

#### 1.4 Asset Retrieval Endpoint

**Enhanced:** `GET /api/v3/assets/{id}`

**Current Response:**
```json
{
  "data": {
    "id": "f1e22bde-b57e-4006-bb30-7b8a507809e2",
    "userId": "1",
    "clientId": null,
    "name": "Test Image",
    "url": "http://localhost:8000/api/v2/assets/bd95a463-2538-447d-ab05-f737c5de2364",
    "type": "image",
    "format": "png",
    "size": 286
  }
}
```

**Required Response:**
```json
{
  "data": {
    "id": "f1e22bde-b57e-4006-bb30-7b8a507809e2",
    "userId": "1",
    "clientId": null,
    "name": "Test Image",
    "url": "http://localhost:8000/api/v3/assets/f1e22bde-b57e-4006-bb30-7b8a507809e2/data",  // NEW: V3 blob endpoint
    "sourceUrl": "https://original-domain.com/image.png",  // NEW: Original URL if applicable
    "type": "image",
    "format": "png",
    "size": 286,
    "blobId": "blob-uuid-123"  // NEW: Reference to blob storage
  }
}
```

**New Endpoint:** `GET /api/v3/assets/{id}/data`
- Serves the actual blob data
- Sets appropriate Content-Type header
- Supports range requests for video streaming
- Returns raw binary data

---

## 2. Scene Generation Functionality

### Current Status
- Scene regeneration endpoint exists but returns placeholder response
- No actual scene generation implementation

### Required Implementation

#### 2.1 Initial Scene Generation (Job Creation)

**Endpoint:** `POST /api/v3/jobs`

**Backend Processing:**
1. **Analyze Input:**
   - Product description from `adBasics.product`
   - Target audience from `adBasics.targetAudience`
   - Key message and CTA
   - Creative direction (style, tone, visual elements)
   - Available assets

2. **Generate Scene Plan:**
   - Use AI/LLM to generate scene descriptions
   - Determine optimal number of scenes (typically 3-5 for 30-second ad)
   - Assign assets to scenes
   - Create shot descriptions
   - Generate script/voiceover text per scene

3. **Create Scene Records:**
   ```sql
   CREATE TABLE job_scenes (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
       scene_number INTEGER NOT NULL,
       duration_seconds DECIMAL(5,2) NOT NULL,
       description TEXT NOT NULL,
       script TEXT,
       shot_type VARCHAR(50),  -- 'wide', 'close-up', 'product', etc.
       transition VARCHAR(50),  -- 'cut', 'fade', 'dissolve', etc.
       assets JSONB,  -- Array of asset IDs used in this scene
       metadata JSONB,  -- Additional scene configuration
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(job_id, scene_number)
   );
   ```

4. **Response Format:**
   ```json
   {
     "data": {
       "id": "job-uuid",
       "status": "storyboard_review",
       "scenes": [
         {
           "id": "scene-1-uuid",
           "sceneNumber": 1,
           "duration": 6.0,
           "description": "Wide shot of person checking smart watch in urban environment",
           "script": "Life moves fast in the city.",
           "shotType": "wide",
           "transition": "fade",
           "assets": ["asset-uuid-1"],
           "metadata": {
             "timeOfDay": "golden hour",
             "setting": "urban street"
           }
         },
         {
           "id": "scene-2-uuid",
           "sceneNumber": 2,
           "duration": 8.0,
           "description": "Close-up of smart watch display showing notifications",
           "script": "Stay connected to what matters most.",
           "shotType": "close-up",
           "transition": "cut",
           "assets": ["asset-uuid-2"],
           "metadata": {
             "focus": "product detail"
           }
         }
       ]
     }
   }
   ```

#### 2.2 Scene Regeneration

**Endpoint:** `POST /api/v3/jobs/{job_id}/actions`

**Request Body:**
```json
{
  "action": "regenerate_scene",
  "sceneNumber": 2,
  "feedback": "Make it more energetic, add motion",  // Optional user feedback
  "constraints": {  // Optional constraints
    "duration": 10.0,
    "mustIncludeAssets": ["asset-uuid-3"]
  }
}
```

**Backend Processing:**
1. Retrieve existing scene
2. Regenerate scene description using:
   - Original job context
   - User feedback
   - Constraints
   - AI/LLM with creative direction
3. Update scene record
4. Return updated scene in response

**Response:**
```json
{
  "data": {
    "jobId": "job-uuid",
    "scene": {
      "id": "scene-2-uuid",
      "sceneNumber": 2,
      "duration": 10.0,
      "description": "Dynamic tracking shot following watch wearer jogging through park",
      "script": "Energy meets technology. Move with purpose.",
      "shotType": "tracking",
      "transition": "cut",
      "assets": ["asset-uuid-3"],
      "metadata": {
        "motion": "high-energy",
        "setting": "outdoor park"
      }
    }
  }
}
```

#### 2.3 Bulk Scene Regeneration

**Endpoint:** `POST /api/v3/jobs/{job_id}/actions`

**Request Body:**
```json
{
  "action": "regenerate_all_scenes",
  "feedback": "Overall direction: make it more inspiring and aspirational"
}
```

**Backend Processing:**
1. Regenerate all scenes for the job
2. Maintain scene count and overall flow
3. Apply user feedback to creative direction
4. Return complete updated scene list

#### 2.4 Scene Approval Workflow

**Current Job Status Flow:**
```
pending → storyboard_review → in_progress → rendering → completed
```

**Required Status Transitions:**

1. **Storyboard Review State:**
   - Job enters this state after initial scene generation
   - User can regenerate scenes
   - User can provide feedback

2. **Approve Storyboard:**
   ```json
   POST /api/v3/jobs/{job_id}/actions
   {
     "action": "approve_storyboard"
   }
   ```
   - Moves job to `in_progress` status
   - Locks scenes (no more regeneration)
   - Begins video rendering

3. **Reject Storyboard:**
   ```json
   POST /api/v3/jobs/{job_id}/actions
   {
     "action": "reject_storyboard",
     "feedback": "Needs more product focus"
   }
   ```
   - Triggers bulk scene regeneration
   - Stays in `storyboard_review` status

---

## 3. Complete Job Workflow Implementation

### 3.1 Job Creation Endpoint Enhancement

**Endpoint:** `POST /api/v3/jobs`

**Complete Flow:**
1. ✅ Validate input (DONE)
2. ✅ Create job record (DONE)
3. **NEW:** Download and store asset URLs
4. **NEW:** Generate initial scenes using AI
5. **NEW:** Set status to `storyboard_review`
6. **NEW:** Return job with scenes

### 3.2 Job Status Endpoint Enhancement

**Endpoint:** `GET /api/v3/jobs/{job_id}`

**Required Response:**
```json
{
  "data": {
    "id": "job-uuid",
    "status": "storyboard_review",
    "progress": {
      "currentStep": "Storyboard Review",
      "percentage": 25,
      "estimatedCompletion": "2025-11-19T22:00:00Z"
    },
    "context": {
      "clientId": "client-123",
      "campaignId": "campaign-456",
      "userId": "user-789"
    },
    "adBasics": {
      "product": "Smart Watch",
      "targetAudience": "Tech enthusiasts",
      "keyMessage": "Stay connected",
      "callToAction": "Buy Now"
    },
    "creative": {
      "direction": {
        "style": "Modern",
        "tone": "Energetic",
        "visualElements": ["Product shots", "Lifestyle"]
      }
    },
    "scenes": [  // NEW: Include scenes in job status
      {
        "id": "scene-1-uuid",
        "sceneNumber": 1,
        "duration": 6.0,
        "description": "...",
        "script": "...",
        "assets": ["asset-uuid-1"]
      }
    ],
    "cost": {
      "estimated": 3.015,
      "actual": null,
      "currency": "USD"
    },
    "createdAt": "2025-11-19T20:00:00Z",
    "updatedAt": "2025-11-19T20:05:00Z"
  }
}
```

### 3.3 Scene Management Endpoints

#### List Job Scenes
**Endpoint:** `GET /api/v3/jobs/{job_id}/scenes`

**Response:**
```json
{
  "data": [
    {
      "id": "scene-1-uuid",
      "sceneNumber": 1,
      "duration": 6.0,
      "description": "...",
      "script": "...",
      "shotType": "wide",
      "transition": "fade",
      "assets": ["asset-uuid-1"],
      "metadata": {}
    }
  ]
}
```

#### Get Specific Scene
**Endpoint:** `GET /api/v3/jobs/{job_id}/scenes/{scene_number}`

#### Update Scene
**Endpoint:** `PUT /api/v3/jobs/{job_id}/scenes/{scene_number}`

**Request Body:**
```json
{
  "description": "Updated scene description",
  "script": "Updated script",
  "duration": 7.5,
  "assets": ["asset-uuid-1", "asset-uuid-2"]
}
```

---

## 4. Implementation Priority

### Phase 1: Asset Handling (HIGH PRIORITY)
1. Add `url` field to asset upload endpoint
2. Implement download and blob storage
3. Create asset blob serving endpoint
4. Update asset retrieval to return V3 URLs
5. Support asset URLs in job creation

**Estimated Effort:** 3-5 days
**Dependencies:** Database schema changes

### Phase 2: Scene Generation (HIGH PRIORITY)
1. Implement AI/LLM integration for scene generation
2. Create scene database schema
3. Generate scenes on job creation
4. Implement scene regeneration action
5. Add scenes to job status endpoint

**Estimated Effort:** 5-7 days
**Dependencies:** AI/LLM service integration

### Phase 3: Complete Workflow (MEDIUM PRIORITY)
1. Implement storyboard approval workflow
2. Add scene management endpoints
3. Implement bulk regeneration
4. Add progress tracking
5. Implement video rendering trigger

**Estimated Effort:** 3-4 days
**Dependencies:** Phase 1 & 2 complete

---

## 5. Testing Requirements

### 5.1 Asset URL Tests
- [ ] Upload asset via URL (image)
- [ ] Upload asset via URL (video)
- [ ] Upload asset via URL (audio)
- [ ] Handle invalid URLs
- [ ] Handle unsupported formats
- [ ] Handle large files
- [ ] Retrieve asset blob via V3 endpoint
- [ ] Stream video asset with range requests

### 5.2 Scene Generation Tests
- [ ] Generate scenes on job creation
- [ ] Regenerate single scene
- [ ] Regenerate all scenes
- [ ] Apply user feedback
- [ ] Maintain scene continuity
- [ ] Assign assets to scenes

### 5.3 Workflow Tests
- [ ] Job creation with asset URLs
- [ ] Storyboard review state
- [ ] Scene approval
- [ ] Scene rejection
- [ ] Progress tracking
- [ ] End-to-end job completion

---

## 6. API Contract Changes

### New Pydantic Models Required

```python
# Asset URL upload
class UploadAssetFromUrl(BaseModel):
    name: str
    type: AssetType
    url: HttpUrl  # NEW
    clientId: Optional[str] = None
    campaignId: Optional[str] = None
    tags: Optional[list[str]] = None

# Scene model
class Scene(BaseModel):
    id: str
    sceneNumber: int
    duration: float
    description: str
    script: Optional[str] = None
    shotType: Optional[str] = None
    transition: Optional[str] = None
    assets: list[str]  # Asset IDs
    metadata: Optional[dict] = None

# Job with scenes
class JobWithScenes(Job):
    scenes: list[Scene]

# Asset in creative direction
class CreativeAsset(BaseModel):
    url: Optional[HttpUrl] = None
    assetId: Optional[str] = None  # Either URL or existing asset ID
    type: AssetType
    name: str
    role: Optional[str] = None  # Hint for scene placement

# Enhanced creative object
class JobCreative(BaseModel):
    direction: JobCreativeDirection
    assets: Optional[list[CreativeAsset]] = None  # NEW

# Scene regeneration request
class RegenerateSceneRequest(BaseModel):
    action: Literal["regenerate_scene"]
    sceneNumber: int
    feedback: Optional[str] = None
    constraints: Optional[dict] = None

# Storyboard approval
class StoryboardApprovalRequest(BaseModel):
    action: Literal["approve_storyboard", "reject_storyboard"]
    feedback: Optional[str] = None
```

---

## 7. External Dependencies

### Required Services

1. **AI/LLM Service** (for scene generation)
   - OpenAI GPT-4 or similar
   - Claude API
   - Or custom trained model

2. **File Download Library**
   - `httpx` or `aiohttp` for async downloads
   - Proper timeout and retry logic
   - Validation and sanitization

3. **Media Processing** (optional but recommended)
   - `Pillow` for image validation
   - `ffmpeg` for video metadata extraction
   - Audio file validation

4. **Blob Storage** (if not using Postgres)
   - S3-compatible storage (AWS S3, MinIO, etc.)
   - Or Postgres BYTEA (for simpler setup)

---

## 8. Configuration Requirements

### Environment Variables

```bash
# Asset Download
MAX_ASSET_DOWNLOAD_SIZE_MB=100
ASSET_DOWNLOAD_TIMEOUT_SECONDS=60
ALLOWED_ASSET_DOMAINS=*  # Or comma-separated list

# Scene Generation
AI_PROVIDER=openai  # or anthropic, custom
AI_API_KEY=sk-...
AI_MODEL=gpt-4
SCENES_PER_VIDEO_MIN=3
SCENES_PER_VIDEO_MAX=7

# Blob Storage
BLOB_STORAGE_TYPE=postgres  # or s3
S3_BUCKET_NAME=...  # If using S3
S3_REGION=...
```

---

## 9. Migration Path

### For Existing Assets

```sql
-- Migrate existing V2 assets to V3 blob storage
-- Run this as a background job

INSERT INTO asset_blobs (id, data, content_type, size_bytes)
SELECT
    gen_random_uuid(),
    pg_read_binary_file('/path/to/v2/assets/' || old_asset_id),
    mime_type,
    octet_length(data)
FROM v2_assets;

UPDATE assets
SET blob_id = asset_blobs.id
FROM asset_blobs
WHERE assets.v2_reference = asset_blobs.v2_id;
```

---

## 10. Success Criteria

### Must Have (Phase 1 & 2)
- [ ] Asset URLs can be provided in job creation
- [ ] Assets are automatically downloaded and stored as blobs
- [ ] Assets are served via `/api/v3/assets/{id}/data`
- [ ] Scenes are generated on job creation
- [ ] Job status includes generated scenes
- [ ] Individual scenes can be regenerated

### Should Have (Phase 3)
- [ ] Storyboard approval workflow functional
- [ ] Scene management endpoints working
- [ ] Progress tracking implemented
- [ ] All endpoints using V3 URLs

### Nice to Have
- [ ] Video streaming with range requests
- [ ] Asset CDN integration
- [ ] Scene generation customization options
- [ ] Template-based scene generation

---

## 11. Documentation Updates Required

- [ ] Update OpenAPI/Swagger spec
- [ ] Add scene generation examples
- [ ] Document asset URL format requirements
- [ ] Add workflow diagrams
- [ ] Create scene regeneration cookbook

---

## Questions for Backend Team

1. **AI Service:** Which AI/LLM provider do you prefer for scene generation?
2. **Blob Storage:** Prefer Postgres BYTEA or external S3-compatible storage?
3. **Scene Generation:** Do you have existing video generation pipeline to integrate with?
4. **Timeline:** What's realistic timeline for Phase 1 vs Phase 2?
5. **Resources:** Any specific constraints or preferences?

---

## Contact & Coordination

**Frontend Lead:** [Your Name]
**Backend Lead:** [Backend Team Lead]
**Timeline Target:** Phase 1 (2 weeks), Phase 2 (3 weeks)

---

**Status:** Awaiting Backend Team Review
**Next Steps:** Backend team to review and provide implementation plan
