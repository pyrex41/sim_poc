# V3 API - Backend Implementation Handoff

**Date:** 2025-11-19
**Status:** Ready for Backend Development
**Priority:** HIGH

---

## 🎉 Current Status

### ✅ What's Working (Verified Today)
- All V3 basic CRUD endpoints (Clients, Campaigns, Assets, Jobs)
- New stats endpoints for clients and campaigns
- Job creation and cost estimation
- Asset listing and retrieval
- Response envelope format
- Authentication and authorization
- Pagination

**Test Results:** 100% passing (all tests verified at 21:01 UTC)

### 🎯 What's Needed Next

Two major features for complete V3 integration:

1. **Asset URL Handling** (Phase 1 - 2 weeks)
2. **Scene Generation** (Phase 2 - 2 weeks)

---

## 📋 Quick Requirements

### 1. Asset URL Handling

**Goal:** Frontend passes URLs → Backend downloads and stores as blobs

**What to Build:**
- Accept `url` field in asset upload requests
- Download assets from URLs automatically
- Store as blobs in database (new `asset_blobs` table)
- Serve blobs via new endpoint: `GET /api/v3/assets/{id}/data`
- Support asset URLs in job creation

**Example:**
```json
POST /api/v3/jobs
{
  "creative": {
    "assets": [
      {"url": "https://example.com/product.jpg", "type": "image"}
    ]
  }
}
```

Backend should:
1. Download the image
2. Store as blob
3. Return asset with V3 URL
4. Use in scene generation

### 2. Scene Generation

**Goal:** Generate 3-7 video scenes automatically when job is created

**What to Build:**
- Integrate AI/LLM for scene generation (OpenAI GPT-4 or Claude)
- Create new `job_scenes` table
- Generate scenes on job creation
- Include scenes in job status response
- Support scene regeneration with feedback
- Implement storyboard approval workflow

**Example Response:**
```json
GET /api/v3/jobs/{id}
{
  "data": {
    "status": "storyboard_review",
    "scenes": [
      {
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

---

## 📚 Documentation Available

Created comprehensive documentation for backend team:

### Main Documents

1. **V3_BACKEND_REQUIREMENTS.md** (Full spec - 400+ lines)
   - Complete API specifications
   - Database schema changes
   - Pydantic models needed
   - Implementation phases
   - Testing requirements
   - Success criteria

2. **V3_BACKEND_REQUIREMENTS_SUMMARY.md** (Quick reference)
   - TL;DR version
   - Key requirements
   - Timeline estimates
   - Environment variables needed

3. **V3_WORKFLOW_DIAGRAM.md** (Visual guide)
   - Flow diagrams
   - Database relationships
   - API endpoint organization
   - Frontend UI mockups
   - Before/after comparisons

4. **V3_CRITICAL_GAPS_RESOLVED.md**
   - Documents the schema fixes you already completed
   - Shows what's working now

---

## 🗃️ Database Changes Needed

### New Tables

```sql
-- Blob storage
CREATE TABLE asset_blobs (
    id UUID PRIMARY KEY,
    data BYTEA NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scene storage
CREATE TABLE job_scenes (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    scene_number INTEGER NOT NULL,
    duration_seconds DECIMAL(5,2),
    description TEXT,
    script TEXT,
    shot_type VARCHAR(50),
    transition VARCHAR(50),
    assets JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, scene_number)
);

-- Update existing assets table
ALTER TABLE assets
    ADD COLUMN blob_id UUID REFERENCES asset_blobs(id),
    ADD COLUMN source_url TEXT;
```

---

## 🔌 New Endpoints Needed

```
Assets:
GET  /api/v3/assets/{id}/data        Serve asset blob

Scenes:
GET  /api/v3/jobs/{id}/scenes        List all scenes
GET  /api/v3/jobs/{id}/scenes/{num}  Get specific scene
PUT  /api/v3/jobs/{id}/scenes/{num}  Update scene

Job Actions (enhanced):
POST /api/v3/jobs/{id}/actions
  - action: "regenerate_scene" + sceneNumber + feedback
  - action: "regenerate_all_scenes" + feedback
  - action: "approve_storyboard"
  - action: "reject_storyboard" + feedback
```

---

## 🧪 Testing Checklist

### Phase 1 (Asset Handling)
- [ ] Download image from URL and store as blob
- [ ] Download video from URL and store as blob
- [ ] Handle invalid URLs gracefully
- [ ] Serve blob via /data endpoint
- [ ] Support asset URLs in job creation

### Phase 2 (Scene Generation)
- [ ] Generate 3-7 scenes on job creation
- [ ] Scenes include description, script, assets
- [ ] Job enters "storyboard_review" status
- [ ] Regenerate single scene works
- [ ] Regenerate all scenes works
- [ ] Apply user feedback to regeneration

---

## 🚀 Implementation Timeline

### Phase 1: Asset URL Handling (Week 1-2)
**Priority:** HIGH
**Deliverable:** Assets can be provided via URL and stored as blobs

Tasks:
1. Add asset URL download functionality
2. Implement blob storage (Postgres BYTEA recommended)
3. Create `/api/v3/assets/{id}/data` endpoint
4. Update job creation to accept asset URLs
5. Test with various file types

### Phase 2: Scene Generation (Week 3-4)
**Priority:** HIGH
**Deliverable:** Jobs automatically generate scenes

Tasks:
1. Choose and integrate AI/LLM (OpenAI or Anthropic)
2. Implement scene generation logic
3. Create scene database schema
4. Add scenes to job creation flow
5. Implement regeneration endpoints

### Phase 3: Complete Workflow (Week 5)
**Priority:** MEDIUM
**Deliverable:** Full storyboard approval workflow

Tasks:
1. Implement approval/rejection actions
2. Add scene management endpoints
3. Complete progress tracking
4. End-to-end testing

---

## ⚙️ Environment Variables

```bash
# Asset Download
MAX_ASSET_DOWNLOAD_SIZE_MB=100
ASSET_DOWNLOAD_TIMEOUT_SECONDS=60
ALLOWED_ASSET_DOMAINS=*

# Scene Generation
AI_PROVIDER=openai  # or anthropic
AI_API_KEY=sk-...
AI_MODEL=gpt-4
SCENES_PER_VIDEO_MIN=3
SCENES_PER_VIDEO_MAX=7

# Blob Storage (if using S3 instead of Postgres)
BLOB_STORAGE_TYPE=postgres  # or s3
S3_BUCKET_NAME=...
S3_REGION=...
```

---

## 🤔 Questions for Backend Team

Before starting, please confirm:

1. **AI Provider:** OpenAI GPT-4, Anthropic Claude, or custom?
2. **Blob Storage:** Postgres BYTEA or S3-compatible storage?
3. **Timeline:** Can Phase 1 start this week?
4. **Video Pipeline:** Do you have existing video rendering to integrate with?
5. **Constraints:** Any API limits, storage limits, or other constraints?

---

## 📞 Next Steps

1. **Backend Team:** Review all documentation
2. **Backend Team:** Answer questions above
3. **Backend Team:** Provide implementation timeline
4. **Kickoff Meeting:** Align on approach and timeline
5. **Phase 1 Start:** Asset URL handling development

---

## 📁 All Documentation Files

Located in project root:

- `V3_BACKEND_REQUIREMENTS.md` - Full specification
- `V3_BACKEND_REQUIREMENTS_SUMMARY.md` - Quick reference
- `V3_WORKFLOW_DIAGRAM.md` - Visual guide
- `V3_CRITICAL_GAPS_RESOLVED.md` - Recent fixes
- `BACKEND_HANDOFF.md` - This file

---

## ✅ Success Criteria

### Phase 1 Complete When:
- ✅ Can create job with asset URLs
- ✅ Assets downloaded and stored as blobs
- ✅ Assets served via V3 endpoint
- ✅ No V2 URLs in responses

### Phase 2 Complete When:
- ✅ Jobs generate scenes automatically
- ✅ Scenes have descriptions and scripts
- ✅ Can regenerate scenes
- ✅ Storyboard approval works

### Full Integration Complete When:
- ✅ Complete job workflow functional
- ✅ Scene management endpoints working
- ✅ All features using V3 exclusively
- ✅ Frontend can build complete UI

---

## 💬 Contact

**Frontend Team:** Ready for integration testing
**Current Status:** All V3 basics verified and working
**Waiting On:** Phase 1 & 2 backend implementation

---

**Status:** 🟢 Ready for Development
**Last Updated:** 2025-11-19 21:15 UTC
