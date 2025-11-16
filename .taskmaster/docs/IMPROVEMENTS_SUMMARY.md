# PRD & Tasks Improvements Summary

**Date:** November 15, 2025
**Reviewers:** Claude (Anthropic)
**Status:** Ready for Implementation

---

## Executive Summary

Both the PRD and tasks.json were comprehensively reviewed. While well-structured, several critical gaps were identified and addressed:

### PRD Improvements (v2.0 → v2.1)
- ✅ Added detailed error handling & recovery strategies (Section 3.4)
- ✅ Implemented database migration strategy with Alembic (Section 4.2)
- ✅ Changed storage from BLOB to file-based URLs (performance improvement)
- ✅ Added comprehensive cost model with examples (Section 5.3)
- ✅ Added observability/metrics framework (Section 6.1)
- ✅ Added brand guidelines integration spec (Section 6.5)
- ✅ Added adaptive polling intervals (Section 2)
- ✅ Added /upload-asset and /approve endpoints

### Tasks.json Improvements
- ✅ Added 5 new critical tasks (0, 11, 12, 13, 14)
- ✅ Fixed 8 dependency issues
- ✅ Added 7 missing subtasks
- ✅ Clarified testing strategies across all tasks

---

## Critical Changes Overview

### 1. Storage Architecture Change
**Before:** Store videos as BLOBs in SQLite
**After:** Store videos as files on disk, URLs in DB

**Impact:**
- ⬆️ Database performance (no large BLOBs)
- ⬇️ Query complexity (simpler retrieval)
- ⬆️ Scalability (easier to move to S3/R2 later)
- ✅ Easier backups (separate DB and media)

**Migration:** No breaking changes (new deployments only)

### 2. New Required Tasks

| Task ID | Title | Priority | Why Critical |
|---------|-------|----------|--------------|
| 0 | Database Migration System | High | Foundation for schema changes |
| 11 | Asset Upload Endpoint | High | PRD mentions it, but no task existed |
| 12 | Approval Flow | High | Core user workflow was missing |
| 13 | Deployment | Medium | No way to ship to production |
| 14 | Monitoring | Medium | Required for production operations |

### 3. Fixed Dependencies

**Task 1 Subtasks:**
- Before: All subtasks independent (incorrect)
- After: Sequential dependencies (2→1, 3→1,2)
- Impact: Prevents testing before schema exists

**Task 10 (Frontend):**
- Before: Dependencies [3, 4, 8, 9]
- After: Dependencies [3, 4, 6, 7, 8, 9]
- Impact: Can't test frontend without background tasks

### 4. Error Handling Enhancements

**New Timeout Thresholds:**
- Prompt parsing: 30s
- Image generation: 120s/image
- Video rendering: 600s (10min)
- FFmpeg export: 60s

**Retry Policies:**
- Replicate API: 3x with exponential backoff (5s → 15s → 45s)
- Network errors: Immediate 1x retry, then exponential
- Rate limits: Respect `Retry-After` header

**Partial Failure Handling:**
- Storyboard: Store partial results, allow retry
- Variations: Return successful videos as "partially_completed"
- Exports: Serve primary format, background retry failures

---

## PRD Changes Detail

### Section 3.4: Error Handling & Recovery (NEW)
Comprehensive failure scenarios with thresholds, retry policies, and recovery strategies.

**Key additions:**
- Timeout table with specific values per stage
- Exponential backoff formulas
- Partial failure handling
- Circuit breaker for Replicate downtime
- Job stuck detection (cleanup every hour)

### Section 4.2: Database Schema & Migration Strategy (ENHANCED)
Replaced simple ALTER statements with Alembic-based migrations.

**New columns:**
- `video_url TEXT` (instead of `video_data BLOB`)
- `storyboard_data TEXT` (JSON array of scenes)
- `approved BOOLEAN` (for approval flow)
- `actual_cost REAL` (track vs estimate)
- `retry_count INTEGER` (for debugging)
- `error_message TEXT` (last failure reason)
- `updated_at TIMESTAMP` (for stuck job detection)

**New indexes:**
- `idx_videos_status`, `idx_videos_campaign`, `idx_videos_client`, `idx_videos_updated`

**Migration strategy:**
- Version control with Alembic
- Idempotent migrations (IF NOT EXISTS)
- Rollback scripts documented
- Asset storage structure defined

### Section 5.3: Cost Model & Estimation (NEW)
Detailed pricing table, calculation examples, and monitoring strategy.

**Replicate pricing:**
- flux-schnell: $0.003/image (8s avg)
- flux-pro (HD): $0.055/image (15s avg)
- skyreels-2: $0.10/sec of video
- stable-video (upscale): $0.25/video

**Cost examples:**
- 30s TikTok (1 var): ~$3.00
- HD Instagram Reel (3 vars): ~$9.50
- 60s YouTube Short (upscaled): ~$6.30

**Monitoring:**
- Alert if actual > estimate × 1.2
- Daily spend reports
- Budget limits ($100 soft, $150 hard)

### Section 6.1: Observability & Metrics (NEW)
Prometheus metrics, Structlog config, Grafana dashboards, alert thresholds.

**Key metrics:**
- `video_gen_duration_seconds` (histogram) - Alert at p95 > 600s
- `replicate_api_errors_total` (counter) - Alert at rate > 5%
- `cost_actual_dollars` (counter) - Alert at daily > $100
- `job_status_gauge` (gauge) - Alert at queued > 20

**Dashboards:**
1. Operations: Job status, errors, duration trends
2. Performance: API latency, cache hit rate
3. Business: Videos/day, approval rate, cost trends

**Alerts:**
- P0: API down, DB corruption
- P1: Failure rate >5%, cost spike, stuck jobs
- P2: Latency degradation
- P3: Cost variance

### Section 6.5: Brand Guidelines Integration (NEW)
Specification for auto-injecting client brand voice and campaign context into prompts.

**Data sources:**
- Client brand guidelines (DB per `client_id`)
- Campaign briefs (DB per `campaign_id`)

**Implementation:**
- Phase 1: Simple string concatenation
- Phase 2: LLM-based prompt merging

### API Endpoints Added
- `POST /api/v2/upload-asset` - Upload images/videos (max 50MB)
- `POST /api/v2/jobs/{id}/approve` - Mark storyboard approved

### Polling Optimization
- Adaptive intervals: 2s (parsing) → 5s (storyboard) → 10s (rendering)
- Reduces unnecessary polls by ~60%

---

## Tasks.json Changes Detail

### New Task 0: Database Migration System
**Why:** No way to safely evolve schema without Alembic.

**Subtasks:**
1. Install and configure Alembic
2. Create v2 video generation migration

**Dependencies:** None (foundation task)
**Estimated Time:** 2-3 hours

### New Task 11: Asset Upload Endpoint
**Why:** PRD mentions `/api/upload-image` but no implementation task.

**Subtasks:**
1. Create upload endpoint with validation (MIME types, size limits)
2. Implement file storage service (organize by client_id)
3. Add asset URL generation and retrieval

**Dependencies:** [0, 1, 2]
**Estimated Time:** 4-6 hours

### New Task 12: Approval Flow
**Why:** Core user workflow (storyboard review → approve → render) was not implemented.

**Subtasks:**
1. Create approval endpoint
2. Add approval validation to render endpoint

**Dependencies:** [0, 3, 6]
**Estimated Time:** 3-4 hours

### New Task 13: Deployment
**Why:** No way to ship to production without containerization.

**Subtasks:**
1. Create Dockerfile and docker-compose
2. Configure Fly.io deployment
3. Initialize production database and secrets

**Dependencies:** [10, 11, 12]
**Estimated Time:** 6-8 hours

### New Task 14: Monitoring & Logging
**Why:** PRD mentions Prometheus/Structlog but no implementation.

**Subtasks:**
1. Set up Prometheus metrics
2. Configure structured logging
3. Create Grafana dashboards
4. Configure alerts

**Dependencies:** [3, 6, 7]
**Estimated Time:** 8-10 hours

### Added Subtasks to Existing Tasks

**Task 5 (Replicate Client):**
- **New subtask 3:** Implement polling and status handling
- Why: Original subtasks only covered API calls, not async polling

**Task 7 (Video Rendering):**
- **New subtask 5:** Add error handling and retry logic
- Why: Video generation can fail in many ways (timeouts, expired URLs, etc.)

**Task 8 (Progress Tracking):**
- **New subtask 3:** Implement Redis caching for job polling
- Why: Reduce DB load from polling (30 req/min/user × 100 users = 3K req/min)

### Fixed Dependencies

| Task | Old Dependencies | New Dependencies | Reason |
|------|------------------|------------------|--------|
| Task 1 | [] | [0] | Needs migration system |
| Task 2 | [] | [0] | Needs migration system |
| Task 3 | [1, 2] | [0, 1, 2] | Needs migration system |
| Task 1.2 | [] | [1] | Can't test functions before schema exists |
| Task 1.3 | [] | [1, 2] | Indexes only after schema + functions |
| Task 10.1 | [3,4,8,9] | [3,4,6,7,8,9] | Frontend needs backend tasks complete |

---

## Implementation Roadmap

### Week 1: Foundation
- [ ] **Day 1-2:** Task 0 (Migrations), Task 1 (DB Schema), Task 2 (Models)
- [ ] **Day 3:** Task 11 (File Uploads), Task 3 (API Stubs)
- [ ] **Day 4:** Task 4 (Auth/Rate Limiting)
- [ ] **Day 5:** Task 5 (Replicate Client)

### Week 2: Core Features
- [ ] **Day 6-7:** Task 6 (Storyboard Generation)
- [ ] **Day 8-9:** Task 7 (Video Rendering)
- [ ] **Day 10:** Task 12 (Approval Flow), Task 8 (Progress Tracking)

### Week 3: Polish & Deploy
- [ ] **Day 11:** Task 9 (Exports/Refinement)
- [ ] **Day 12-13:** Task 14 (Monitoring), Task 10 (Frontend Integration)
- [ ] **Day 14-15:** Task 13 (Deployment), E2E Testing

**Total Estimated Time:** 15 working days

---

## Risk Mitigation

### High-Risk Items
1. **Replicate API Stability:** Mitigated by retry logic, circuit breaker, fallback models
2. **Cost Overruns:** Mitigated by upfront estimates, budget limits, real-time tracking
3. **Storage Scaling:** Mitigated by file-based storage (easy to migrate to S3)
4. **Polling Load:** Mitigated by adaptive intervals, Redis caching

### Testing Requirements
- **Unit tests:** 85% coverage target (all helpers, services)
- **Integration tests:** All endpoints, full job lifecycle
- **Load tests:** 10 concurrent jobs, 1000 polls/min
- **E2E tests:** Complete user flow from upload → download

---

## Migration Path from v2.0 to v2.1

### For Existing Deployments
1. Run Alembic migration: `alembic upgrade head`
2. Set new env vars: `VIDEO_STORAGE_PATH`, update model names
3. No data migration needed (new columns have defaults)
4. Redeploy backend with new endpoints
5. Update frontend to use `/upload-asset` and `/approve`

### For New Deployments
1. Use updated PRD v2.1
2. Follow task order: 0 → 1-2 → 11 → 3-4 → ...
3. All improvements included from start

### Breaking Changes
**None.** All changes are additive or internal optimizations.

---

## Questions Resolved

| Original Question | Answer |
|-------------------|--------|
| Variations handling? | Array in `results` field (simpler) |
| Audio integration? | Post-processing in v2.1 |
| Large assets chunking? | Yes, via Dropzone in frontend |
| Fallback models? | Configurable via env vars |
| Cost billing integration? | Track only; Stripe out of scope |
| **Video storage?** | **Files on disk, not BLOBs (NEW)** |
| **Migration strategy?** | **Alembic with version control (NEW)** |
| **Approval flow?** | **Explicit /approve endpoint (NEW)** |
| **Brand guidelines?** | **String concat in v2.0, LLM in v2.1 (NEW)** |

---

## Next Steps

1. ✅ Review this summary with team
2. ⬜ Update tasks.json with new tasks and dependencies
3. ⬜ Begin Task 0 (Alembic setup)
4. ⬜ Schedule daily standups during implementation
5. ⬜ Set up Grafana/Prometheus before Week 3

---

**Prepared by:** Claude (Anthropic)
**For questions:** Reference `.taskmaster/docs/tasks-improvements.md` for detailed task specs
