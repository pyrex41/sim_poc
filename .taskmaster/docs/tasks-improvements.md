# Tasks.json Improvements

## Summary of Changes

### New Tasks to Add

#### Task 0: Database Migration System (NEW - insert before Task 1)
```json
{
  "id": 0,
  "title": "Set Up Database Migration System with Alembic",
  "description": "Initialize Alembic for version-controlled database migrations to safely manage schema changes",
  "details": "Install Alembic, configure for SQLite, create initial migration for existing schema, and set up migration workflow. Create v2_video_generation migration with new columns.",
  "testStrategy": "Test migrations on clean DB, test rollback, verify idempotency by running migrations twice",
  "priority": "high",
  "dependencies": [],
  "status": "pending",
  "subtasks": [
    {
      "id": 1,
      "title": "Install and Configure Alembic",
      "description": "Set up Alembic with SQLite configuration",
      "dependencies": [],
      "details": "Run 'alembic init alembic', configure alembic.ini for SQLite, set up env.py with app models",
      "status": "pending",
      "testStrategy": "Verify alembic commands work: alembic current, alembic history"
    },
    {
      "id": 2,
      "title": "Create v2 Video Generation Migration",
      "description": "Generate migration for new video generation columns",
      "dependencies": [1],
      "details": "Create migration adding: progress, video_url, storyboard_data, approved, estimated_cost, actual_cost, retry_count, error_message, updated_at columns plus indexes and triggers",
      "status": "pending",
      "testStrategy": "Apply migration to test DB, verify all columns exist, test rollback"
    }
  ]
}
```

#### Task 11: File Upload Implementation (insert after Task 10)
```json
{
  "id": 11,
  "title": "Implement Asset Upload Endpoint",
  "description": "Create /api/v2/upload-asset endpoint for user-uploaded images and videos",
  "details": "Accept multipart/form-data uploads, validate file types (jpg, png, mp4, mov) and sizes (max 50MB), store in VIDEO_STORAGE_PATH/uploads/{client_id}/, return asset URL. Optional: ClamAV malware scanning for production.",
  "testStrategy": "Upload valid files, verify storage and URL. Test invalid types/sizes return 400. Test concurrent uploads.",
  "priority": "high",
  "dependencies": [0, 1, 2],
  "status": "pending",
  "subtasks": [
    {
      "id": 1,
      "title": "Create Upload Endpoint with Validation",
      "description": "Implement POST /api/v2/upload-asset with file validation",
      "dependencies": [],
      "details": "Use FastAPI UploadFile, validate MIME types and file size, generate unique asset IDs, implement rate limiting (10/min/user)",
      "status": "pending",
      "testStrategy": "Integration tests: upload valid files, test size limits, test invalid MIME types"
    },
    {
      "id": 2,
      "title": "Implement File Storage Service",
      "description": "Create service to save uploaded files to disk with proper organization",
      "dependencies": [1],
      "details": "Create directory structure: /uploads/{client_id}/{asset_id}.{ext}, ensure directory permissions, handle disk full errors",
      "status": "pending",
      "testStrategy": "Unit tests: verify file paths, test permissions, simulate disk full scenario"
    },
    {
      "id": 3,
      "title": "Add Asset URL Generation and Retrieval",
      "dependencies": [2],
      "description": "Generate URLs for uploaded assets and implement retrieval endpoint",
      "details": "Return signed URLs or paths after upload, implement GET /api/v2/assets/{asset_id} for serving files with proper Content-Type headers",
      "status": "pending",
      "testStrategy": "Upload file, verify URL works, test asset retrieval with authentication"
    }
  ]
}
```

#### Task 12: Approval Flow Implementation (insert after Task 11)
```json
{
  "id": 12,
  "title": "Implement Storyboard Approval Workflow",
  "description": "Add approval state management and validation before video rendering",
  "details": "Create POST /api/v2/jobs/{id}/approve endpoint, add 'approved' column to DB (already in migration), validate approval status before allowing render, track approval timestamp",
  "testStrategy": "Test approval flow: generate storyboard → approve → render. Test render without approval returns 403.",
  "priority": "high",
  "dependencies": [0, 3, 6],
  "status": "pending",
  "subtasks": [
    {
      "id": 1,
      "title": "Create Approval Endpoint",
      "description": "Implement POST /api/v2/jobs/{id}/approve",
      "dependencies": [],
      "details": "Validate job status is 'storyboard_complete', set approved=true, log approval event, return updated job state",
      "status": "pending",
      "testStrategy": "Integration test: approve job after storyboard, verify DB update, test approving already-approved job"
    },
    {
      "id": 2,
      "title": "Add Approval Validation to Render Endpoint",
      "description": "Modify /render endpoint to check approval status",
      "dependencies": [1],
      "details": "In POST /jobs/{id}/render, verify approved=true before queuing video render, return 403 with message if not approved",
      "status": "pending",
      "testStrategy": "Test render without approval fails, test render after approval succeeds"
    }
  ]
}
```

#### Task 13: Deployment and Infrastructure (insert after Task 12)
```json
{
  "id": 13,
  "title": "Deployment and Infrastructure Setup",
  "description": "Containerize application and deploy to Fly.io with proper configuration",
  "details": "Create Dockerfile, docker-compose.yml, Fly.io configuration (fly.toml), set up environment variables, initialize production database, configure volume mounts for VIDEO_STORAGE_PATH",
  "testStrategy": "Deploy to staging, test full E2E flow, verify environment variables, test volume persistence",
  "priority": "medium",
  "dependencies": [10, 11, 12],
  "status": "pending",
  "subtasks": [
    {
      "id": 1,
      "title": "Create Dockerfile and Docker Compose",
      "description": "Build containerized application with all dependencies",
      "dependencies": [],
      "details": "Multi-stage Dockerfile for Python backend and Next.js frontend, include FFmpeg, set up volume mounts, optimize layer caching",
      "status": "pending",
      "testStrategy": "Build image locally, run with docker-compose, test all endpoints work"
    },
    {
      "id": 2,
      "title": "Configure Fly.io Deployment",
      "description": "Set up Fly.io app with proper resource allocation",
      "dependencies": [1],
      "details": "Create fly.toml, configure volumes for storage, set memory/CPU limits, configure health checks, set up secrets",
      "status": "pending",
      "testStrategy": "Deploy to Fly.io staging, verify app starts, test health check endpoint"
    },
    {
      "id": 3,
      "title": "Initialize Production Database and Secrets",
      "description": "Run migrations and configure environment for production",
      "dependencies": [2],
      "details": "Run Alembic migrations on prod DB, configure secrets (REPLICATE_API_KEY, JWT_SECRET), set up backup strategy",
      "status": "pending",
      "testStrategy": "Verify migrations applied, test API calls work, verify secrets not exposed in logs"
    }
  ]
}
```

#### Task 14: Monitoring and Logging Infrastructure (insert after Task 13)
```json
{
  "id": 14,
  "title": "Implement Monitoring and Logging Infrastructure",
  "description": "Set up Prometheus metrics, Structlog logging, and Grafana dashboards",
  "details": "Integrate prometheus_client library, configure Structlog with JSON output, create key metrics (duration, errors, costs), set up Grafana dashboards and alerts",
  "testStrategy": "Generate jobs, verify metrics exported, check logs format, test alert thresholds",
  "priority": "medium",
  "dependencies": [3, 6, 7],
  "status": "pending",
  "subtasks": [
    {
      "id": 1,
      "title": "Set Up Prometheus Metrics",
      "description": "Integrate prometheus_client and define key metrics",
      "dependencies": [],
      "details": "Install prometheus_client, create metrics: video_gen_duration_seconds, job_failures_total, cost_actual_dollars, replicate_api_errors_total, expose /metrics endpoint",
      "status": "pending",
      "testStrategy": "Hit endpoints, scrape /metrics, verify metric values increment"
    },
    {
      "id": 2,
      "title": "Configure Structured Logging with Structlog",
      "description": "Replace print statements with structured JSON logging",
      "dependencies": [],
      "details": "Install structlog, configure JSON renderer, add context processors (job_id, campaign_id, timestamp), set log levels per environment",
      "status": "pending",
      "testStrategy": "Generate job, verify logs are valid JSON with expected fields, test log levels"
    },
    {
      "id": 3,
      "title": "Create Grafana Dashboards",
      "description": "Build Operations, Performance, and Business dashboards",
      "dependencies": [1, 2],
      "details": "Create 3 dashboards: Ops (job status, errors, duration), Performance (API latency, cache hits), Business (videos/day, approval rate, costs)",
      "status": "pending",
      "testStrategy": "Generate test data, verify dashboards populate, test time ranges work"
    },
    {
      "id": 4,
      "title": "Configure Alerts",
      "description": "Set up Prometheus alerts for critical issues",
      "dependencies": [1],
      "details": "Configure alerts: failure rate >5%, p95 latency >600s, cost >$100/day, stuck jobs >10. Integrate with Slack/PagerDuty",
      "status": "pending",
      "testStrategy": "Trigger alert conditions, verify notifications sent, test alert silencing"
    }
  ]
}
```

### Dependency Fixes for Existing Tasks

#### Task 1: Fix Subtask Dependencies
```json
{
  "id": 2,
  "title": "Implement Helper Functions for Job Management",
  "dependencies": [1]  // CHANGE: Now depends on subtask 1
},
{
  "id": 3,
  "title": "Add Indexes and Conduct Testing",
  "dependencies": [1, 2]  // CHANGE: Now depends on subtasks 1 and 2
}
```

#### Task 5: Add Polling Subtask
Add new subtask 3:
```json
{
  "id": 3,
  "title": "Implement Replicate Polling and Status Handling",
  "description": "Add async polling logic to wait for Replicate prediction completion",
  "dependencies": [1, 2],
  "details": "Poll Replicate /predictions/{id} endpoint every 2s, handle status: starting/processing/succeeded/failed, implement timeout handling (120s for images, 600s for videos), exponential backoff on errors",
  "status": "pending",
  "testStrategy": "Unit tests with mocked Replicate responses for each status, test timeout handling, verify retry logic"
}
```

#### Task 7: Add Error Handling Subtask
Add new subtask 5:
```json
{
  "id": 5,
  "title": "Add Error Handling and Retry Logic for Video Rendering",
  "description": "Implement retry with exponential backoff for failed renders",
  "dependencies": [1, 2, 3, 4],
  "details": "Wrap video generation in try/catch, implement retry logic (2x with backoff), handle expired image URLs, track retry count in DB, log failures with context",
  "status": "pending",
  "testStrategy": "Unit tests: simulate API failures, verify retries, test max retry limit. Integration: test partial failure scenarios"
}
```

#### Task 8: Add Caching Subtask
Add new subtask 3:
```json
{
  "id": 3,
  "title": "Implement Redis Caching for Job Polling",
  "description": "Cache job responses to reduce DB load during frequent polling",
  "dependencies": [1, 2],
  "details": "Install redis-py, cache JobResponse in Redis with TTL=30s, invalidate cache on job updates, implement cache miss fallback to DB",
  "status": "pending",
  "testStrategy": "Integration tests: poll job, verify cache hit on subsequent polls, verify cache invalidation on updates"
}
```

#### Task 10: Fix Dependencies
Update Task 10 subtask 1:
```json
{
  "id": 1,
  "title": "Update useVideoGeneration.ts Hook for v2 API Calls",
  "dependencies": [3, 4, 6, 7, 8, 9],  // CHANGE: Added dependencies 6 and 7
  ...
}
```

### New Dependencies to Add

Task 0: No dependencies
Task 1: dependencies: [0] // CHANGE: Now depends on Task 0 (migration system)
Task 2: dependencies: [0] // CHANGE: Now depends on Task 0
Task 3: dependencies: [0, 1, 2] // CHANGE: Added Task 0 dependency
Task 11: dependencies: [0, 1, 2]
Task 12: dependencies: [0, 3, 6]
Task 13: dependencies: [10, 11, 12]
Task 14: dependencies: [3, 6, 7]

## Implementation Priority Order

1. **Task 0** - Migration system (foundation)
2. **Tasks 1-2** - Data models and DB schema (depends on 0)
3. **Task 11** - File uploads (parallel with 1-2)
4. **Task 3** - API endpoints (depends on 1, 2, 11)
5. **Task 4** - Auth/rate limiting (depends on 3)
6. **Task 5** - Replicate client (parallel with 4)
7. **Task 6** - Storyboard generation (depends on 1, 2, 5)
8. **Task 7** - Video rendering (depends on 1, 2, 5, 6)
9. **Task 12** - Approval flow (depends on 3, 6)
10. **Task 8** - Progress tracking (depends on 3, 6, 7)
11. **Task 9** - Exports/refinement (depends on 3, 7)
12. **Task 14** - Monitoring (parallel with 8-9)
13. **Task 10** - Frontend integration (depends on all backend)
14. **Task 13** - Deployment (depends on 10, 11, 12)

## Testing Strategy Updates

Add to each task's testStrategy:
- **Integration tests** must include error scenarios (network failures, invalid inputs)
- **Load tests** for endpoints must verify rate limiting works
- **E2E tests** must clean up test data (jobs, uploaded files)
- **All tests** must mock Replicate API to avoid costs
