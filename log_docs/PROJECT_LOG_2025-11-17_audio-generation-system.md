# Project Log - Audio Generation System Implementation
**Date:** 2025-11-17
**Session:** Audio/Music Generation Feature Addition

## Summary
Implemented comprehensive audio/music generation system mirroring the existing image/video infrastructure. Added support for meta/musicgen and riffusion/riffusion models with full backend API, database schema, and campaign tracking integration.

## Changes Made

### 1. Database Schema (backend/schema.sql:223-250)
- Created `generated_audio` table with complete structure:
  - Core fields: id, prompt, audio_url, model_id, parameters, status
  - Tracking: created_at, collection, metadata
  - Download management: download_attempted, download_retries, download_error, audio_data (BLOB)
  - Campaign integration: brief_id, client_id, campaign_id
  - Audio-specific: duration (REAL)
- Added indexes for performance: created_at, model_id, brief_id, client_id, campaign_id

### 2. Database Helper Functions (backend/database.py:667-832)
- `save_generated_audio()` - Create audio records with campaign tracking
- `update_audio_status()` - Update generation status and URLs
- `get_audio_by_id()` - Retrieve single audio with full URL conversion
- `list_audio()` - Query with filters (client, campaign, status, collection)
- `delete_audio()` - Remove audio records
- Fixed import error handling for migrate module

### 3. API Models & Enums (backend/main.py:929-963)
**Video Model Enum:**
```python
class VideoModel(str, Enum):
    SEEDANCE = "bytedance/seedance-1-lite"  # Default
    KLING = "kwaivgi/kling-v2.1"
```

**Audio Model Enum:**
```python
class AudioModel(str, Enum):
    MUSICGEN = "meta/musicgen"  # Default, 3.1M runs
    RIFFUSION = "riffusion/riffusion"
```

**Request Models:**
- Updated `VideoGenerationRequest` with model selection parameter
- Added `AudioGenerationRequest` with prompt, model, duration, campaign tracking

### 4. Video Generation Enhancement (backend/main.py:4820-4908)
- Added model parameter support to `/api/v2/generate/video`
- Implemented model-specific input parameter building:
  - **Seedance**: image, duration, resolution, aspect_ratio, fps, camera_fixed
  - **Kling**: start_image, mode, duration, negative_prompt
- Dynamic Replicate API URL construction based on selected model
- Maintained backward compatibility with default model

### 5. Audio Generation Endpoint (backend/main.py:4925-5018)
**POST `/api/v2/generate/audio`**
- Rate limit: 10 requests/minute
- Model selection: MusicGen (default) | Riffusion
- Model-specific parameters:
  - **MusicGen**: stereo-melody-large, duration (8s default), temperature, top_k, top_p, classifier_free_guidance, output_format (mp3)
  - **Riffusion**: prompt_a, denoising (0.75), num_inference_steps (50), seed_image_id (vibes)
- Webhook support for async processing
- Campaign and client tracking integration
- Returns: `{audio_id, status, model}`

### 6. Audio Gallery Endpoints (backend/main.py:2879-2937)
**GET `/api/audio`**
- Query parameters: limit, offset, model_id, collection, client_id, campaign_id, status
- Returns paginated audio list with full metadata

**GET `/api/audio/{audio_id}`**
- Retrieve specific audio by ID
- Full metadata including generation parameters

**DELETE `/api/audio/{audio_id}`**
- Remove audio from database
- Requires authentication

### 7. Database Imports (backend/main.py:49-53)
Added audio functions to imports:
- save_generated_audio
- update_audio_status
- get_audio_by_id
- list_audio
- delete_audio

## Model Research & Selection

### Selected Models
1. **meta/musicgen** (Primary, 3.1M runs)
   - Stereo-melody-large model version
   - 8-second default duration (2-12s range)
   - Temperature, top_k, top_p controls
   - MP3 output format

2. **riffusion/riffusion** (Alternative)
   - Spectrogram-based generation
   - Prompt interpolation support
   - Seed image variations

### Replicate API Integration
- Full parameter schemas fetched from Replicate docs
- Sensible defaults configured for rapid development
- Easy model swapping via enum pattern

## Task-Master Status
**Active Tasks:** None currently in progress
**Note:** Audio generation system implemented outside existing task structure as enhancement to v2 API endpoints

**Relevant Tasks for Future Work:**
- Task #1: Database schema extension (audio table added as part of this work)
- Task #3: Core API endpoints (audio endpoints added to v2 API)

## Current Todo List Status
✅ Completed:
- Explore current image/video structure
- Find and select Replicate audio models
- Add audio database schema and tables
- Add audio database helper functions
- Add audio generation endpoints
- Add audio gallery endpoints

⏸️ Deferred (Frontend - Elm UI):
- Create Audio.elm generation page
- Create AudioGallery.elm gallery page
- Create AudioDetail.elm detail page
- Update Route.elm for audio routes
- Update Main.elm to handle audio

**Decision:** Backend infrastructure complete. Frontend Elm implementation deferred for later iteration.

## API Usage Examples

### Generate Music (MusicGen - Default)
```bash
curl -X POST http://localhost:8000/api/v2/generate/audio \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "upbeat electronic dance music with heavy bass",
    "campaign_id": "campaign_123",
    "duration": 10
  }'
```

### Generate with Riffusion
```bash
curl -X POST http://localhost:8000/api/v2/generate/audio \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "ambient lo-fi hip hop beats",
    "campaign_id": "campaign_123",
    "model": "riffusion/riffusion"
  }'
```

### List Generated Audio
```bash
curl http://localhost:8000/api/audio \
  -H "X-API-Key: YOUR_KEY"
```

### Filter by Campaign
```bash
curl "http://localhost:8000/api/audio?campaign_id=campaign_123&status=completed" \
  -H "X-API-Key: YOUR_KEY"
```

## Code References
- Audio schema: backend/schema.sql:223-250
- Audio DB functions: backend/database.py:667-832
- Audio generation endpoint: backend/main.py:4925-5018
- Audio gallery endpoints: backend/main.py:2879-2937
- Video model selection: backend/main.py:4820-4908
- Model enums: backend/main.py:929-935

## Next Steps

### Immediate (Backend)
1. Add background task for audio download/processing (similar to video/image)
2. Implement webhook handler updates for audio completion
3. Add audio data blob storage endpoint (GET `/api/audio/{audio_id}/data`)
4. Add polling mechanism for audio status updates

### Frontend (Elm UI)
1. Create Audio.elm page with Replicate model browser
2. Add AudioGallery.elm with audio player controls
3. Implement audio playback in detail views
4. Add audio tab to main navigation

### Enhancement
1. Add more audio models (stable-audio, musicgen variants)
2. Implement audio-to-audio transformations
3. Add audio visualization/waveform generation
4. Integrate audio with video generation workflow

## Testing Recommendations
1. Test audio generation with both models
2. Verify campaign tracking and client association
3. Test gallery filtering and pagination
4. Validate audio status polling
5. Test authentication on all audio endpoints

## Notes
- Backend audio system fully mirrors image/video infrastructure
- Easy to extend with additional audio models
- Campaign tracking integrated from day one
- Ready for frontend implementation when needed
- Database migrations applied automatically on server startup
