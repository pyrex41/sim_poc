# Product Requirements Document: Prompt Parser Integration

**Version:** 1.0  
**Last Updated:** November 15, 2025  
**Status:** Draft

---

## 1. Core Concept

The Prompt Parser Integration merges the advanced multi-modal prompt processing capabilities from the standalone `promptparser` service into the main backend API. This creates a unified, stateful application that combines creative brief generation with physics simulation, video rendering, and media storage.

**Primary Purpose:** Transform vague user inputs (text, images, videos) into structured creative briefs for video generation, leveraging the main backend's authentication, database, and rendering pipelines.

**Key Benefits:**
- Centralized API: Single endpoint for all AI-driven features (scene generation, creative planning, video rendering).
- Enhanced User Experience: Authenticated users can save, retrieve, and iterate on creative briefs alongside physics scenes and videos.
- Cost Efficiency: Shared caching (Redis) and LLM providers reduce redundant API calls.
- Scalability: Integrates with existing database for persistence, enabling features like brief history and collaboration.

**Goal:** Enable end-to-end video production workflow: User prompt → Creative brief → Physics scene → Rendered video, all within one authenticated session.

---

## 2. User Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  PROMPT PARSER INTEGRATION                   │
└─────────────────────────────────────────────────────────────┘

1. USER INPUT (Multi-Modal)
   - Text: "Create a luxury watch ad with dramatic fall"
   - Image/Video: Upload reference (e.g., brand style image)
   - Platform: TikTok/Instagram (influences defaults)
   ↓

2. AUTHENTICATION CHECK
   - Verify JWT/API key
   - Load user preferences (e.g., default platform)
   ↓

3. CREATIVE BRIEF GENERATION (5-15s)
   - LLM (GPT-4o/Claude) analyzes input
   - Applies smart defaults (duration, style, scenes)
   - Generates JSON: creative_direction + scene_sequence
   - Validates feasibility (total duration, scene count)
   ↓

4. PERSISTENCE
   - Save brief to database (creative_briefs table)
   - Cache LLM response (Redis)
   ↓

5. OUTPUT & INTEGRATION
   - Return structured brief to frontend
   - Optional: Auto-generate physics scene from first scene prompt
   - User iterates: Refine brief → Re-generate
   ↓

6. DOWNSTREAM WORKFLOW
   - Brief → Physics scene generation (/api/generate)
   - Scene → Video rendering (/api/genesis/render)
   - Store final video in user media library
```

**Error Handling:** If LLM fails, fallback to simple text-to-scene; notify user of low confidence.

---

## 3. Technical Architecture

### 3.1 System Diagram

```
┌───────────────────── BROWSER ─────────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────┐            │
│  │         Elm Frontend                 │            │
│  │  - Multi-modal input form            │            │
│  │  - Brief display & editor            │            │
│  └────┬─────────────────────────────┬───┘            │
│       │ Ports                       │ HTTP           │
│       ▼                             ▼                │
│  ┌─────────────┐         ┌──────────────────┐       │
│  │ File Upload │◀───────▶│ FastAPI Backend   │       │
│  │ (Media)     │         │                   │       │
│  └─────────────┘         │ - /api/creative/  │       │
│                          │   parse           │       │
│                          │ - Auth & DB       │       │
│                          └────┬─────────────┘       │
│                               │                      │
│                               ▼                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │ Redis    │    │ LLM      │    │ SQLite   │        │
│  │ Cache    │    │ (GPT-4o/ │    │ (Briefs, │        │
│  └──────────┘    │ Claude)  │    │ Scenes)  │        │
│                  └──────────┘    └──────────┘        │
│                                                        │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Backend Structure (Post-Integration)

```
backend/
├── __init__.py
├── main.py                          # Unified FastAPI app
├── database.py                      # Extended with creative_briefs table
├── auth.py                          # Existing auth middleware
├── config.py                        # Centralized Pydantic settings (from promptparser)
├── dependencies.py                  # DI for cache, LLM providers
├── prompt_parser_service/           # Namespaced from promptparser/app/
│   ├── api/v1/parse.py              # Core parsing logic
│   ├── core/                        # Config, logging, metrics
│   ├── models/                      # Request/Response Pydantic models
│   ├── services/                    # LLM, cache, validators
│   └── ...
├── integrations/                    # Existing (Replicate, Genesis)
└── utils/                           # Shared helpers
```

**Key Changes:**
- **Dependencies:** Merge `requirements.txt`; add Redis, Anthropic, OpenCV, SlowAPI, Prometheus.
- **Configuration:** Adopt Pydantic Settings for all env vars (e.g., `OPENAI_API_KEY`, `REDIS_URL`, `REPLICATE_API_KEY`).
- **Services:** Shared LLM registry (supports multiple providers); unified caching.
- **Database:** Add `creative_briefs` table; link to users and scenes.

### 3.3 API Endpoints

- **POST /api/creative/parse** (New)
  - Input: `ParseRequest` (text, image_url, video_url, platform, category)
  - Output: `ParseResponse` (creative_direction JSON, confidence_score, scenes list)
  - Auth: Required (JWT/API key)
  - Rate Limit: 10/min per user (SlowAPI)

- **GET /api/creative/briefs** (New)
  - Output: List of user's saved briefs (paginated)
  - Auth: Required

- **POST /api/creative/briefs/{id}/refine** (New)
  - Input: Refinement text
  - Output: Updated brief
  - Auth: Required

- Existing: `/api/generate`, `/api/genesis/render` (enhanced to accept brief-derived prompts)

### 3.4 Frontend Integration (Elm)

- **New Components:**
  - `CreativeBriefEditor.elm`: Form for multi-modal input; displays JSON tree.
  - `BriefGallery.elm`: List user's saved briefs; preview scenes.
- **Ports:** Add media upload (images/videos) to backend.
- **Workflow:** After parsing, auto-populate physics scene input; button to "Generate Video from Brief".

---

## 4. Data Models

### 4.1 Pydantic Models (from promptparser + Extensions)

```python
# backend/prompt_parser_service/models/request.py
class ParseRequest(BaseModel):
    text: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    platform: Optional[str] = "tiktok"  # Influences defaults
    category: Optional[str] = "luxury"  # e.g., tech, fashion
    user_id: str  # From auth

# backend/prompt_parser_service/models/response.py
class CreativeDirection(BaseModel):
    style: str
    tone: str
    duration: int
    pacing: str
    color_palette: List[str]
    music_suggestion: str

class Scene(BaseModel):
    id: str
    purpose: str
    duration: float
    prompt: str  # For downstream renderer
    transition: str

class ParseResponse(BaseModel):
    creative_direction: CreativeDirection
    scenes: List[Scene]
    confidence_score: float  # 0-1
    validation_errors: List[str]
```

### 4.2 Database Schema (SQLite Extension)

```sql
-- Add to backend/database.py
CREATE TABLE IF NOT EXISTS creative_briefs (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    prompt_text TEXT,
    image_url TEXT,
    video_url TEXT,
    creative_direction JSON NOT NULL,
    scenes JSON NOT NULL,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_briefs_user ON creative_briefs(user_id);
CREATE INDEX idx_briefs_created ON creative_briefs(created_at);
```

**Functions:** `save_creative_brief()`, `get_user_briefs()`, `update_brief()`.

---

## 5. Key Features & User Stories

### 5.1 Core Features

**Must Have (MVP):**
1. Multi-modal parsing endpoint with auth.
2. Creative brief generation using shared LLM/cache.
3. Database persistence for briefs.
4. Basic frontend integration (input form, brief display).

**Should Have (v1.0):**
5. Brief refinement endpoint.
6. Auto-generate physics scene from brief's first scene.
7. Brief gallery with search/filter.
8. Metrics/observability (Prometheus integration).

**Nice to Have (v1.1+):**
9. Collaborative briefs (share via link).
10. Brief-to-video pipeline (one-click render).
11. Advanced validation (e.g., total duration checks).

### 5.2 User Stories

```
As an authenticated user, I want to:

1. Submit a multi-modal prompt via /api/creative/parse
   - So I get a structured brief in <15s
   - Acceptance: Returns valid JSON; cached if identical.

2. View and edit saved briefs in the gallery
   - So I can iterate on ideas
   - Acceptance: Paginated list; edit saves to DB.

3. Refine a brief with additional text
   - So I can adjust without starting over
   - Acceptance: Updates DB; re-uses cache where possible.

4. Generate a physics scene from a brief
   - So I can prototype video ideas
   - Acceptance: Extracts first scene prompt; calls /api/generate.

5. Monitor generation costs/metrics
   - So I can optimize usage
   - Acceptance: Expose Prometheus endpoints.
```

---

## 6. Non-Functional Requirements

### Performance Targets

| Metric              | Target          |
|---------------------|-----------------|
| Brief generation    | <15s (p95)     |
| Cache hit rate      | >70%           |
| DB query latency    | <50ms          |
| Rate limit          | 10/min/user    |
| Concurrent requests | 50 (horizontal scale via Fly.io) |

### Security & Reliability
- **Auth:** All endpoints require JWT/API key.
- **Input Validation:** Sanitize URLs; scan images/videos for malware (via services).
- **Error Handling:** Graceful fallbacks (e.g., text-only if media fails).
- **Data Privacy:** Briefs stored per-user; no PII in LLM prompts.
- **Monitoring:** Structured logging (Structlog); Prometheus metrics.

### Compatibility
- Python 3.11+; FastAPI 0.109+.
- Integrates with existing frontend (Elm) and backend services.

---

## 7. Development Phases

### Phase 1: Setup & Core Integration (1-2 days)
- [ ] Copy promptparser/app to backend/prompt_parser_service.
- [ ] Merge requirements.txt; pip install.
- [ ] Centralize config.py; update env vars.
- [ ] Add dependencies.py for DI.
- **Deliverable:** Standalone /api/creative/parse works (no DB).

### Phase 2: Database & Auth (1 day)
- [ ] Extend database.py with creative_briefs table.
- [ ] Add save/load functions.
- [ ] Secure endpoint with verify_auth.
- [ ] Integrate caching/LLM DI.
- **Deliverable:** Briefs persist; auth required.

### Phase 3: Refinement & Frontend (2 days)
- [ ] Add /api/creative/briefs and refine endpoint.
- [ ] Update Elm: New components for input/gallery.
- [ ] Auto-generate scenes from briefs.
- **Deliverable:** End-to-end flow: Parse → Save → Refine → Scene gen.

### Phase 4: Polish & Testing (1 day)
- [ ] Add metrics/logging.
- [ ] Unit/integration tests (e.g., test_parse_endpoint.py).
- [ ] Cleanup: Remove old promptparser files.
- **Deliverable:** Deployable integration; docs updated.

---

## 8. Open Questions

1. **LLM Provider Priority:** Default to GPT-4o; fallback to Claude? Configurable per-user?
2. **Media Storage:** Store uploaded images/videos in DB or filesystem? Integrate with existing media tables?
3. **Brief-Scene Linking:** Auto-link briefs to generated scenes/videos in DB?
4. **Caching Strategy:** Invalidate cache on refinement? TTL for briefs?
5. **Frontend Uploads:** Handle large videos client-side (chunked) or server-side?

---

## 9. Success Metrics

**Integration Success:**
- 100% test coverage for new endpoints.
- <5s average generation with cache hits.
- No auth bypasses; all briefs saved to DB.

**User Adoption:**
- 80% of video generations use integrated parser.
- Average 2 refinements per brief.
- Reduced support tickets for "vague prompts".

---

## 10. What We're NOT Building (v1.0)

- Real-time collaboration on briefs.
- Advanced media analysis (e.g., video frame extraction).
- Export briefs to external tools (e.g., Adobe After Effects).
- Custom LLM fine-tuning for domain-specific prompts.
- Offline parsing (requires LLM access).

These can be added post-MVP based on usage.

---

**Next Step:** Implement Phase 1; test standalone endpoint locally.