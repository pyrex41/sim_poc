# Product Requirements Document: Integrated Video Generation API

**Version:** 2.1
**Last Updated:** November 15, 2025
**Status:** Approved for Development
**Authors:** Grok (xAI) – Synthesis of Hybrid API Design, Claude (Anthropic) – Technical Review & Enhancement
**Stakeholders:** Product Team, Engineering, Design  

---

## 1. Core Concept

The Integrated Video Generation API unifies the Next.js frontend's multi-card workflow with a robust, stepwise backend process for AI-driven video ad creation. It transforms user inputs (text prompts, assets, brand guidelines) into polished video ads via Replicate's text-to-image and image-to-video models, with human-in-the-loop approval for storyboards. This hybrid design combines incremental endpoints for user control (start → poll → approve/render) with efficient background processing for AI tasks (prompt parsing → image generation → video rendering).

**Primary Purpose:** Enable authenticated users to generate, review, and refine short-form video ads (15-60s) for platforms like TikTok/Meta, integrating with existing campaign/client management. Focus on cost-efficiency, fault tolerance, and seamless frontend polling.

**Key Benefits:**
- **User-Centric Workflow:** Stepwise generation prevents over-generation; users approve storyboards before expensive video renders.
- **Replicate-Only Simplicity:** Leverages stable, managed AI (no custom renderers like Genesis); easy scaling via API keys.
- **Persistence & Observability:** All jobs stored in DB; real-time progress via polling, with caching for retries.
- **Cost Optimization:** Upfront estimates; variations queued in parallel only post-approval.
- **Extensibility:** JSON fields for flexible outputs (e.g., multiple formats); hooks for future audio overlays or exports.

**Goal:** Achieve end-to-end generation in <10min (p95), with 80% user approval rate on storyboards, reducing support for "bad outputs."

**Out of Scope (v2.0):** Real-time collaboration, advanced audio synthesis (e.g., voiceover gen), bulk campaign automation, non-Replicate models (e.g., RunwayML).

---

## 2. User Flow

```
┌─────────────────────────────────────────────────────────────┐
│             INTEGRATED VIDEO GENERATION FLOW                │
└─────────────────────────────────────────────────────────────┘

1. FRONTEND SETUP (Cards 1-3)
   - User fills: Ad Basics (name, duration, platform), Creative Direction (prompt, assets), Advanced Options (audio, exports).
   - Auto-include: Campaign brief, client brand guidelines.
   ↓ [Generate Storyboard Button]

2. API CALL: POST /api/v2/generate
   - Backend: Save job to DB; queue background parse → image gen.
   - Return: job_id for polling.
   ↓

3. POLLING: GET /api/v2/jobs/{job_id} (adaptive interval)
   - Initial: 2s for fast feedback (parsing stage)
   - Storyboard gen: 5s (active image generation)
   - Video render: 10s (long-running operation)
   - Progress: "parsing_brief" → "generating_scene_3" → "storyboard_complete".
   - On complete: Display storyboard grid (images + descriptions) in Review Card.
   ↓ [User Reviews/Refines → Approve Button]

4. API CALL: POST /api/v2/jobs/{job_id}/render
   - Backend: Validate approval; queue background video render (images → video via Replicate).
   - Return: Updated status; estimated cost.
   ↓

5. POLLING: Continued via /jobs/{id}
   - Progress: "rendering_video" → "exporting_formats" → "completed".
   - On success: Display video player, metrics (cost, duration); download links for formats.
   ↓

6. POST-GENERATION
   - Save to campaign videos library; optional: Regenerate scene or full video.
   - Error: Rollback to "failed" with details; user retries via refine endpoint.
```

**Error Handling:** Timeouts → "failed" status with retry button; low-confidence parses → prompt user for clarification. All steps authenticated; unauth → redirect to login. See Section 3.4 for detailed error recovery strategies.

---

## 3. Technical Architecture

### 3.1 System Diagram

```
┌───────────────────── NEXT.JS FRONTEND ─────────────────────┐
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Cards: Basics | Direction | Options | Storyboard     │   │
│  │ Review | Progress | Actions                         │   │
│  └─────────────┬───────────────────────────────────────┘   │
│                │ HTTP (Polling)                           │
│                ▼                                          │
│  ┌─────────────┐                                          │
│  │ File Upload │ (Assets: /api/upload-image)             │
│  └─────────────┘                                          │
└────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────── FASTAPI BACKEND ──────────────────────┐
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ /v2/generate│  │ /jobs/{id}  │  │ /render     │        │
│  │ (Job Start) │  │ (Poll)      │  │ (Video Gen) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                 │                 │                       │
│                 ▼                 ▼                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Prompt      │  │ Replicate   │  │ SQLite DB   │        │
│  │ Parser      │◀─▶│ (Images/   │  │ (Jobs,      │        │
│  │ (Scenes)    │  │  Videos)    │  │  Videos)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                 │                 │                       │
│                 ▼                 ▼                       │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │ Redis Cache │  │ FFmpeg      │                        │
│  │ (Prompts/   │  │ (Exports)   │                        │
│  └─────────────┘  └─────────────┘                        │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Backend Structure

```
backend/
├── main.py                          # Core app; include v2 router
├── api/
│   └── v2/
│       ├── videos.py                # New: /generate, /jobs/{id}, /render
│       └── __init__.py
├── models/
│   └── video.py                     # GenerationRequest, VideoProgress
├── database.py                      # Extend generated_videos table
├── services/
│   ├── replicate_client.py          # Helpers: _generate_image, _generate_video
│   ├── background_tasks.py          # generate_storyboard_ai, generate_video_ai
│   └── exporters.py                 # FFmpeg for formats
├── prompt_parser_service/           # Existing: For scene parsing
└── utils/                           # Cost estimator, progress utils
```

**Key Changes:**
- **Dependencies:** Add `requests`, `subprocess` (FFmpeg), `alembic` (migrations); reuse Replicate auth.
- **Configuration:** Env vars: `REPLICATE_API_KEY`, `REPLICATE_STORYBOARD_MODEL=flux-schnell`, `REPLICATE_VIDEO_MODEL=skyreels-2`, `VIDEO_STORAGE_PATH=/data/videos`.
- **Async:** BackgroundTasks for MVP; migrate to Celery for prod.
- **DB:** Extend `generated_videos` with `progress JSON`, `video_url TEXT`, `storyboard_data JSON`, `approved BOOLEAN`; add indexes on `status`, `campaign_id`.
- **Storage:** Videos stored as files in `VIDEO_STORAGE_PATH`; URLs stored in DB (not BLOBs for performance).

### 3.3 API Endpoints (v2 Prefix for Backward Compat)

| Method | Endpoint                  | Description | Auth | Rate Limit |
|--------|---------------------------|-------------|------|------------|
| POST   | /api/v2/upload-asset     | Upload image/video assets for job | Req  | 10/min/user |
| POST   | /api/v2/generate         | Start job: Parse → Storyboard images | Req  | 5/min/user |
| GET    | /api/v2/jobs/{job_id}    | Poll status/progress/storyboard/video | Req  | 30/min/user |
| POST   | /api/v2/jobs/{job_id}/approve | Mark storyboard as approved | Req  | 5/min/user |
| POST   | /api/v2/jobs/{job_id}/render | Approve → Video render + exports | Req  | 2/min/user |
| GET    | /api/v2/jobs/{job_id}/data | Binary video download | Req  | - |
| GET    | /api/v2/jobs/{job_id}/thumbnail | JPEG thumbnail | Req  | - |
| POST   | /api/v2/jobs/{job_id}/refine | Update prompt/assets; re-gen storyboard | Req  | 3/min/user |
| DELETE | /api/v2/jobs/{job_id}    | Cancel job (rollback) | Req  | - |

**Request/Response Examples:**
- **POST /generate**: Body: `{creativePrompt: "...", duration: 30, ...}` → `{job_id: 123, estimatedCost: 3.50}`
- **GET /jobs/123**: → `{status: "storyboard_complete", progress: {stage: "ready", percentage: 50}, storyboard: [{sceneNumber:1, imageUrl: "...", ...}]}`

### 3.4 Error Handling & Recovery Strategies

**Timeout Thresholds:**
| Stage | Timeout | Action |
|-------|---------|--------|
| Prompt Parsing | 30s | Mark failed; return parse error |
| Scene Image Generation | 120s/image | Retry 3x with exponential backoff (5s, 15s, 45s) |
| Video Rendering | 600s | Retry 2x; alert if failure persists |
| FFmpeg Export | 60s | Retry 1x; skip format if failed |

**Retry Policies:**
- **Replicate API Failures:** Exponential backoff: 5s → 15s → 45s, then mark failed
- **Network Errors:** Retry immediately 1x, then exponential backoff
- **Rate Limiting (429):** Wait based on `Retry-After` header, max 2 retries
- **Server Errors (5xx):** Exponential backoff 3x, then fail

**Partial Failure Handling:**
- **Storyboard (3/5 scenes generated):** Store partial results; user can refine/retry failed scenes
- **Variations (1/3 videos failed):** Return successful videos; mark job as "partially_completed"
- **Exports (MP4 success, GIF failed):** Serve MP4; log export failure; retry export in background

**Job Stuck Detection:**
- Monitor jobs with `updated_at` timestamp
- If `status = "generating_*"` and `updated_at > 15min ago`, mark as "stalled"
- Background cleanup task runs hourly to mark stalled jobs as "failed"
- User can retry stalled jobs via `/refine` endpoint

**Replicate API Downtime:**
- If 3+ consecutive failures across different jobs: trigger circuit breaker
- Return 503 Service Unavailable with `Retry-After: 300` header
- Queue jobs for retry when service recovers
- Send alert to ops team

**Database Errors:**
- All DB writes wrapped in transactions with rollback on failure
- Failed writes log to error queue; retry async
- Critical path (job creation) fails fast; return 500 to user

**Asset Upload Errors:**
- Validate file type/size before upload (max 50MB, types: jpg, png, mp4, mov)
- Scan for malware using ClamAV (optional, prod-only)
- Return 400 for invalid uploads with clear error message

**Cost Estimation Errors:**
- If Replicate pricing API unavailable, use cached rates (updated daily)
- Return estimate with disclaimer: "Estimate based on recent rates"
- Track actual costs post-generation; alert if >20% deviation

---

## 4. Data Models

### 4.1 Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from enum import Enum
import json

class VideoStatus(str, Enum):
    generating_storyboard = "generating_storyboard"
    storyboard_complete = "storyboard_complete"
    generating_video = "generating_video"
    completed = "completed"
    failed = "failed"

class Scene(BaseModel):  # From prompt parser
    prompt: str
    duration: float
    description: str

class StoryboardEntry(BaseModel):
    sceneNumber: int
    imageUrl: str
    description: str
    timestamp: float

class GenerationRequest(BaseModel):  # Frontend interface
    campaignId: str
    clientId: str
    videoName: str
    creativePrompt: str
    duration: Literal[15, 30, 60]
    platform: Literal['tiktok', 'meta', 'youtube', 'custom']
    aspectRatio: str  # "9:16"
    numberOfVariations: Literal[1, 2, 3]
    keywords: List[str]
    stylePresets: List[str]
    assets: List[Dict[str, Any]]  # {id, url, type, ...}
    audioControls: Dict[str, Any]  # {musicStyle, ...}
    exportFormats: List[str]  # ['mp4', 'gif']
    # Auto-filled: brandGuidelines, campaignBrief

class VideoProgress(BaseModel):
    stage: str  # "parsing_brief", "generating_scene_X", "rendering_video"
    percentage: int  # 0-100
    currentScene: Optional[str]
    estimatedTimeRemaining: Optional[int]  # Seconds
    cost: float  # Running total

class JobResponse(BaseModel):
    job_id: int
    status: VideoStatus
    progress: VideoProgress
    storyboard: Optional[List[StoryboardEntry]]
    results: Optional[Dict[str, Any]]  # {videoUrl: "...", variations: [...], exports: {...}}
    error: Optional[str]
```

### 4.2 Database Schema & Migration Strategy

**New Columns for `generated_videos` Table:**

```sql
-- Migration: v2_video_generation.sql
-- Version: 001
-- Date: 2025-11-15

-- Add new columns (check if exists to be idempotent)
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS progress TEXT DEFAULT '{}';
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS video_url TEXT;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS storyboard_data TEXT;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS estimated_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS actual_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_status ON generated_videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_campaign ON generated_videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_client ON generated_videos(client_id);
CREATE INDEX IF NOT EXISTS idx_videos_updated ON generated_videos(updated_at);

-- Trigger to auto-update updated_at
CREATE TRIGGER IF NOT EXISTS update_videos_timestamp
AFTER UPDATE ON generated_videos
FOR EACH ROW
BEGIN
    UPDATE generated_videos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

**Migration Strategy:**
1. Use Alembic for version-controlled migrations
2. Migrations stored in `backend/alembic/versions/`
3. Auto-generate migration skeletons: `alembic revision --autogenerate -m "description"`
4. Apply migrations: `alembic upgrade head`
5. Rollback: `alembic downgrade -1`

**Rollback Script:**
```sql
-- Rollback migration (if needed)
DROP TRIGGER IF EXISTS update_videos_timestamp;
DROP INDEX IF EXISTS idx_videos_updated;
DROP INDEX IF EXISTS idx_videos_client;
DROP INDEX IF EXISTS idx_videos_campaign;
DROP INDEX IF EXISTS idx_videos_status;

-- Note: SQLite doesn't support DROP COLUMN, so rollback requires recreating table
-- For production, test migrations on staging first
```

**Helper Functions:**

```python
import json
from typing import Dict, Optional
from datetime import datetime

def update_job_progress(job_id: int, progress: VideoProgress):
    """Update job progress with auto-timestamp"""
    with get_db() as conn:
        conn.execute(
            """UPDATE generated_videos
               SET progress = ?, status = ?, updated_at = ?
               WHERE id = ?""",
            (json.dumps(progress.model_dump()), progress.stage, datetime.utcnow(), job_id)
        )
        conn.commit()

def get_job(job_id: int) -> Optional[Dict]:
    """Fetch job with parsed JSON fields"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM generated_videos WHERE id = ?", (job_id,)
        ).fetchone()
        if not row:
            return None

        job = dict(row)
        # Parse JSON fields
        job['progress'] = json.loads(job.get('progress', '{}'))
        job['storyboard_data'] = json.loads(job.get('storyboard_data', '[]'))
        return job

def increment_retry_count(job_id: int):
    """Track retry attempts"""
    with get_db() as conn:
        conn.execute(
            "UPDATE generated_videos SET retry_count = retry_count + 1 WHERE id = ?",
            (job_id,)
        )
        conn.commit()
```

**Asset Storage Structure:**
```
VIDEO_STORAGE_PATH/
├── videos/
│   ├── {job_id}/
│   │   ├── final.mp4
│   │   ├── final.gif
│   │   ├── final.webm
│   │   └── thumbnail.jpg
├── storyboards/
│   └── {job_id}/
│       ├── scene_1.jpg
│       ├── scene_2.jpg
│       └── ...
└── uploads/
    └── {client_id}/
        └── {asset_id}.{ext}
```

---

## 5. Key Features & User Stories

### 5.1 Core Features

**Must Have (MVP v2.0):**
1. Stepwise API: Generate storyboard, poll/review, approve/render.
2. Replicate Integration: Text-to-image (Flux) for scenes; image-to-video (SkyReels) for finals.
3. Progress Tracking: Granular stages with % and costs.
4. File Storage/Serving: Videos stored as files; URLs in DB; thumbnail gen via FFmpeg.
5. Variations: Parallel renders post-approval.
6. Asset Upload: Endpoint for user-uploaded images/videos.

**Should Have (v2.1):**
6. Refinement: Update job prompt/assets → re-gen storyboard.
7. Exports: Auto-generate GIF/WebM from MP4.
8. Caching: Redis for repeated prompts/scenes.

**Nice to Have (v3.0):**
9. Webhooks: Push updates to frontend (e.g., via Server-Sent Events).
10. Audio Overlay: Integrate Replicate TTS for voiceover.
11. Analytics: Track approval rates, avg costs per campaign.

### 5.2 User Stories

```
As an authenticated marketer, I want to:

1. Submit a full form (Cards 1-3) via /v2/generate
   - So I get a job_id and initial progress in <5s
   - Acceptance: DB insert; background task queued; est. cost returned.

2. Poll /v2/jobs/{id} during storyboard gen
   - So I see real-time images/descriptions in the Review Card
   - Acceptance: Returns 5-8 scenes; handles polling load.

3. Approve storyboard and trigger /v2/render
   - So video gen starts only after my OK
   - Acceptance: Validates status; queues render; returns cost breakdown.

4. Poll for video completion and download
   - So I can play/preview and export formats
   - Acceptance: Binary serves at /data; thumbnails load fast.

5. Cancel or refine a job mid-flow
   - So I can iterate without starting over
   - Acceptance: DELETE sets status='cancelled'; refine re-parses.
```

### 5.3 Cost Model & Estimation

**Replicate API Pricing (as of Nov 2025):**

| Operation | Model | Unit Cost | Avg Duration | Notes |
|-----------|-------|-----------|--------------|-------|
| Scene Image | flux-schnell | $0.003/image | 8s | 1024x1024 resolution |
| Scene Image (HD) | flux-pro | $0.055/image | 15s | 2048x2048 for hero scenes |
| Video Generation | skyreels-2 | $0.10/sec | 45s | Input: 1-8 images, max 60s output |
| Video Upscale | stable-video | $0.25/video | 90s | Optional quality boost |

**Cost Calculation Examples:**

**Example 1: Simple 30s TikTok Video (1 variation)**
```
- Prompt Parsing: $0 (local)
- Storyboard (5 scenes): 5 × $0.003 = $0.015
- Video Render (30s): $0.10 × 30 = $3.00
- Exports (GIF, WebM): $0 (FFmpeg local)
- Total: $3.015 (~$3.00)
```

**Example 2: HD Instagram Reel (3 variations)**
```
- Storyboard (8 scenes, HD): 8 × $0.055 = $0.44
- Video Render (30s × 3): 3 × ($0.10 × 30) = $9.00
- Exports (3 sets): $0
- Total: $9.44 (~$9.50)
```

**Example 3: 60s YouTube Short (1 variation, upscaled)**
```
- Storyboard (10 scenes): 10 × $0.003 = $0.03
- Video Render (60s): $0.10 × 60 = $6.00
- Upscale: $0.25
- Total: $6.28 (~$6.30)
```

**Cost Estimation Logic:**

```python
def estimate_cost(request: GenerationRequest) -> float:
    """Calculate upfront cost estimate"""
    # Scene count heuristic: 1 scene per 5-8 seconds
    scene_count = max(3, request.duration // 6)

    # Image cost (flux-schnell by default)
    image_cost_per_scene = 0.003
    if 'hd' in request.stylePresets:
        image_cost_per_scene = 0.055

    storyboard_cost = scene_count * image_cost_per_scene

    # Video cost ($0.10/sec × duration × variations)
    video_cost = 0.10 * request.duration * request.numberOfVariations

    # Optional upscaling
    upscale_cost = 0.25 if 'upscale' in request.stylePresets else 0

    total = storyboard_cost + video_cost + upscale_cost
    return round(total, 2)

def track_actual_cost(job_id: int, operation: str, cost: float):
    """Track real costs from Replicate API responses"""
    with get_db() as conn:
        current = conn.execute(
            "SELECT actual_cost FROM generated_videos WHERE id = ?", (job_id,)
        ).fetchone()[0] or 0.0
        conn.execute(
            "UPDATE generated_videos SET actual_cost = ? WHERE id = ?",
            (current + cost, job_id)
        )
```

**Cost Monitoring:**
- Log estimate vs actual cost per job
- Alert if actual > estimate × 1.2 (20% overage)
- Daily report: total spend, avg cost/video, cost by campaign
- Budget limits: Soft limit at $100/day (alert), hard limit at $150/day (pause new jobs)

**Cost Optimization Strategies:**
- Use `flux-schnell` by default; `flux-pro` only for stylePresets='hd'
- Cache generated scene images for 24hrs; reuse for similar prompts
- Batch variations in single API call if Replicate supports (investigate)
- Compress exports aggressively (target 5MB for 30s video)

---

## 6. Non-Functional Requirements

### Performance Targets

| Metric                  | Target          |
|-------------------------|-----------------|
| Storyboard Gen (5 scenes) | <2min (p95)    |
| Video Render (30s)      | <5min (p95)    |
| Poll Latency            | <200ms         |
| Concurrent Jobs         | 20/user (scale via Celery) |
| Cost per Video          | <$5 (Replicate est.) |

### Security & Reliability
- **Auth:** JWT via `verify_auth`; ownership checks on job_id/campaign_id.
- **Validation:** Pydantic for inputs; scan assets for malware (ClamAV optional).
- **Errors:** Graceful fallbacks (e.g., text-only if image fails); retry polls 3x.
- **Privacy:** No PII in prompts; jobs per-user via client_id.
- **Monitoring:** Structlog for tasks; Prometheus for endpoints (see Observability below).

### Observability & Metrics

**Structured Logging (Structlog):**
```python
# Log format: JSON with context
{
  "timestamp": "2025-11-15T10:30:45Z",
  "level": "INFO",
  "job_id": 123,
  "campaign_id": "abc",
  "event": "storyboard_generation_started",
  "scene_count": 5,
  "duration_ms": 1250
}
```

**Key Metrics (Prometheus):**

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|-----------------|
| `video_gen_requests_total` | Counter | Total /generate calls | - |
| `video_gen_duration_seconds` | Histogram | End-to-end gen time | p95 > 600s |
| `storyboard_gen_duration_seconds` | Histogram | Storyboard gen time | p95 > 180s |
| `video_render_duration_seconds` | Histogram | Video render time | p95 > 360s |
| `replicate_api_errors_total` | Counter | Replicate failures | rate > 5% |
| `replicate_api_latency_seconds` | Histogram | Replicate response time | p95 > 120s |
| `job_status_gauge` | Gauge | Jobs by status | queued > 20 |
| `job_failures_total` | Counter | Failed jobs by reason | rate > 3% |
| `cost_actual_dollars` | Counter | Cumulative spend | daily > $100 |
| `cost_variance_ratio` | Gauge | actual/estimate | > 1.2 |
| `poll_requests_total` | Counter | /jobs/{id} calls | rate > 1000/min |
| `cache_hit_rate` | Gauge | Redis cache hits | < 0.8 |

**Logging Levels:**
- **DEBUG:** Scene prompts, API payloads, cache lookups
- **INFO:** Job lifecycle (created, approved, completed), progress updates
- **WARNING:** Retries, partial failures, cost overages
- **ERROR:** API failures, DB errors, stuck jobs
- **CRITICAL:** Circuit breaker triggered, storage full, auth bypass attempts

**Dashboards (Grafana):**
1. **Operations Dashboard:**
   - Active jobs by status (pie chart)
   - Gen duration trends (time series)
   - Error rate (time series)
   - Cost tracking (gauge + time series)

2. **Performance Dashboard:**
   - Replicate API latency (heatmap)
   - Poll request rate (time series)
   - Cache hit rate (gauge)
   - Queue depth (time series)

3. **Business Dashboard:**
   - Videos generated per day
   - Approval rate (storyboards)
   - Avg refinements per job
   - Cost per video trend

**Alerts (PagerDuty/Slack):**
- **P0 (Critical):** API down >5min, DB corruption, auth bypass
- **P1 (High):** Failure rate >5%, cost spike (>$50/hr), stuck jobs >10
- **P2 (Medium):** p95 latency degradation, cache failures
- **P3 (Low):** Cost variance, retry spikes

**Tracing (OpenTelemetry - Future):**
- Trace full request path: API → Parser → Replicate → DB
- Visualize bottlenecks in storyboard/video gen
- Track async task spans for background jobs

### Compatibility
- Python 3.11+; FastAPI 0.109+; Next.js 15+.
- Replicate Models: Flux-Schnell (images), SkyReels-2 (videos)—configurable.
- SQLite 3.35+ (for JSON functions); upgrade to PostgreSQL for scale.

---

## 6.5 Brand Guidelines & Campaign Brief Integration

**Purpose:** Auto-inject client brand voice, visual style, and campaign context into prompts without manual user input.

**Data Sources:**
1. **Client Brand Guidelines (stored in DB per client_id):**
   ```json
   {
     "brand_voice": "playful, energetic, Gen-Z friendly",
     "visual_style": "bright colors, high contrast, minimal text",
     "forbidden_elements": ["competitor logos", "stock photography"],
     "logo_url": "/assets/clients/abc/logo.png",
     "color_palette": ["#FF6B6B", "#4ECDC4", "#FFE66D"]
   }
   ```

2. **Campaign Brief (per campaign_id):**
   ```json
   {
     "objective": "Launch new sneaker line targeting 18-25 urban athletes",
     "key_messages": ["sustainability", "performance", "street style"],
     "cta": "Shop now at example.com/sneakers",
     "do_not_mention": ["previous product lines"]
   }
   ```

**Integration Flow:**
```
User Prompt: "Show a runner in the city"
     ↓
Fetch brand guidelines + campaign brief
     ↓
Augmented Prompt: "Show a runner in the city, bright neon colors (#FF6B6B palette),
                   energetic Gen-Z vibe, focus on sustainability message,
                   avoid stock photography, include [logo]"
     ↓
Send to Prompt Parser
```

**Implementation (Phase 1 MVP):**
- Simple string concatenation in `generate_storyboard_ai`
- Fetch from existing `clients` and `campaigns` tables
- No AI prompt engineering (v2.1 feature: use LLM to merge context)

**Example Code:**
```python
def augment_prompt_with_context(
    user_prompt: str,
    client_id: str,
    campaign_id: str
) -> str:
    """Inject brand guidelines into user prompt"""
    brand = get_brand_guidelines(client_id)
    campaign = get_campaign_brief(campaign_id)

    context = f"""
    Style: {brand['visual_style']}
    Brand voice: {brand['brand_voice']}
    Key messages: {', '.join(campaign['key_messages'])}
    Avoid: {', '.join(brand['forbidden_elements'])}
    """

    return f"{user_prompt}\n\nContext: {context}"
```

**Future Enhancements (v2.1+):**
- LLM-based prompt merging for natural integration
- Visual style transfer from brand asset examples
- Auto-detect brand guideline violations in generated scenes
- A/B test prompt strategies per client

---

## 7. Development Phases

### Phase 1: API Scaffolding & DB (1 day)
- [ ] Extend DB: Add progress/video_data columns; update functions.
- [ ] Implement v2 endpoints: /generate, /jobs/{id}, /render (stubs).
- [ ] Add Pydantic models; integrate auth/rate limits.
- **Deliverable:** Manual job creation/polling works; no background.

### Phase 2: Background Tasks & Replicate (2 days)
- [ ] Impl `generate_storyboard_ai`: Parse → images; update progress/storyboard.
- [ ] Impl `generate_video_ai`: Chain images → video; handle variations/exports.
- [ ] Helpers: Replicate clients, FFmpeg exports, cost estimator.
- **Deliverable:** End-to-end gen via manual task trigger; binaries serve.

### Phase 3: Integration & Polish (1 day)
- [ ] Frontend hooks: Update `useVideoGeneration.ts` for v2 calls/polling.
- [ ] Add refine/cancel; caching; error simulations.
- [ ] Tests: Unit (helpers), integration (full flow), load (10 concurrent).
- **Deliverable:** Deployable to Fly.io; e2e demo video.

### Phase 4: Monitoring & Launch (1 day)
- [ ] Metrics/logging; webhook stubs.
- [ ] Docs: API spec (OpenAPI); migration SQL.
- **Deliverable:** Prod release; monitor first 10 jobs.

---

## 8. Open Questions

1. **Variations Handling:** Store as separate jobs or array in results? (Array for simplicity.)
2. **Audio Integration:** Embed music/voiceover prompts in video gen, or post-process? (Post for v2.1.)
3. **Large Assets:** Chunk uploads >10MB? (Yes, via frontend Dropzone.)
4. **Fallback Models:** If SkyReels down, switch to Stable Video? (Configurable env.)
5. **Costs:** Integrate Stripe for billing? (Phase out-of-scope; track only.)

---

## 9. Success Metrics

**Technical:**
- 95% job completion rate; <3% Replicate failures.
- Avg gen time: <4min; poll hit rate >95%.
- Test coverage: 85% (tasks/endpoints).

**User/Business:**
- 70% storyboard approval rate.
- Avg 1.5 refinements/job.
- 50 videos generated in first month; <$2 avg cost.
- NPS >7 from beta users (via post-gen survey).

---

## 10. What We're NOT Building (v2.0)

- Custom physics sim (Genesis)—Replicate only.
- Real-time updates (SSE/WebSockets)—polling suffices.
- Advanced analytics (e.g., A/B testing videos).
- Mobile-specific optimizations (e.g., low-bandwidth thumbnails).
- Internationalization (prompts in EN only).

These align with Phase 4+ based on metrics.

---

**Next Step:** Kick off Phase 1; schedule sprint review Nov 18, 2025. Questions? Let's iterate!
