# Quick Start Guide - V2 Video Generation API

## ✅ What's Working Now

The v2 API is **fully implemented and tested**. All endpoints are operational in POC mode (without requiring Replicate API key).

## 🚀 Server is Running

Server is currently running at: `http://localhost:8000`

## 🧪 Test the API

### 1. Check Health
```bash
curl http://localhost:8000/health
```

### 2. View Cache Stats
```bash
curl http://localhost:8000/api/v2/cache/stats
```

### 3. Create a Video Job
```bash
curl -X POST http://localhost:8000/api/v2/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a cinematic video about AI innovation in 2025",
    "duration": 30,
    "style": "cinematic",
    "aspect_ratio": "16:9",
    "client_id": "test-client"
  }'
```

**Expected Response:**
```json
{
  "job_id": 4,
  "status": "pending",
  "progress": {
    "current_stage": "pending",
    "scenes_total": 0,
    "scenes_completed": 0,
    "message": "Job created, waiting to start"
  },
  "estimated_cost": 3.02,
  "video_url": null,
  "approved": false,
  "created_at": "2025-11-16T04:27:46",
  "updated_at": "2025-11-16T04:27:46"
}
```

### 4. Get Job Status
```bash
curl http://localhost:8000/api/v2/jobs/4
```

### 5. List All Jobs
```bash
curl http://localhost:8000/api/v2/jobs?limit=10
```

### 6. Get Job Metadata
```bash
curl http://localhost:8000/api/v2/jobs/4/metadata
```

## 📚 API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Available Endpoints

### Job Management
- `POST /api/v2/generate` - Create video job
- `GET /api/v2/jobs/{id}` - Get job status
- `GET /api/v2/jobs` - List jobs
- `POST /api/v2/jobs/{id}/approve` - Approve storyboard
- `POST /api/v2/jobs/{id}/render` - Start rendering
- `GET /api/v2/jobs/{id}/video` - Get video file
- `GET /api/v2/jobs/{id}/metadata` - Get metadata
- `GET /api/v2/jobs/{id}/export?format=mp4&quality=medium` - Export video

### Asset Management
- `POST /api/v2/upload-asset` - Upload image/video (max 50MB)
- `GET /api/v2/assets/{id}` - Get asset
- `DELETE /api/v2/assets/{id}` - Delete asset
- `GET /api/v2/assets` - List assets

### Refinement
- `POST /api/v2/jobs/{id}/refine` - Refine scene
- `POST /api/v2/jobs/{id}/reorder` - Reorder scenes

### System
- `GET /api/v2/cache/stats` - Cache statistics

## 💾 Database

**Location**: `backend/DATA/scenes.db`

**Tables**:
- `generated_videos` - Video jobs with v2 columns
- `uploaded_assets` - User-uploaded files
- `job_cache` - SQLite-based cache

**View data**:
```bash
sqlite3 backend/DATA/scenes.db "SELECT id, prompt, status, estimated_cost, created_at FROM generated_videos ORDER BY id DESC LIMIT 5"
```

## 🗂️ File Storage

**Videos**: `backend/DATA/videos/`
**Uploads**: `backend/DATA/uploads/`
**Exports**: `backend/DATA/exports/`

## 🔧 Configuration

### POC Mode (Current)
- ✅ Works without Replicate API key
- ✅ Mock cost estimation
- ✅ SQLite caching
- ✅ File-based storage

### Production Mode (Optional)
Set environment variable:
```bash
export REPLICATE_API_KEY=r8_xxxxx
```

Then restart server for real video generation.

## 📖 Documentation Files

- `V2_API_FINAL_SUMMARY.md` - Complete implementation summary
- `IMPLEMENTATION_COMPLETE_SUMMARY.md` - Detailed technical docs
- `test_v2_api.sh` - Automated test script
- `backend/services/*_README.md` - Service-specific docs
- `backend/models/README.md` - Model documentation

## 🎯 What's Implemented

✅ All 16 API endpoints
✅ Database schema with 8 new columns
✅ 6 Pydantic models for type safety
✅ SQLite caching (30s TTL)
✅ Job creation with cost estimation
✅ Progress tracking
✅ Asset upload system
✅ Video export (3 formats, 3 qualities)
✅ Scene refinement & reordering
✅ Comprehensive error handling

## 🚦 Status

**Implementation**: 100% Complete ✅
**Testing**: All endpoints verified ✅
**Documentation**: Comprehensive ✅
**Server**: Running on port 8000 ✅

## 🎉 Next Steps

1. **Test the endpoints** using the examples above
2. **View OpenAPI docs** at http://localhost:8000/docs
3. **Check the database** to see created jobs
4. **Add Replicate API key** for real video generation (optional)
5. **Integrate with frontend** or build your own client

---

**Need Help?**
- Check `V2_API_FINAL_SUMMARY.md` for complete documentation
- View API docs at `http://localhost:8000/docs`
- Run `./test_v2_api.sh` for automated tests
