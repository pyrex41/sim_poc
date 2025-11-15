# System Patterns

## Architecture
- FastAPI app with modules: input processors (text/image/video), LLM orchestrator, cache manager, scene generator, validator, cost estimator, content safety, admin endpoints.
- Redis (async) caches parse results with deterministic keys to limit LLM spend.
- LLM provider abstraction supports OpenAI (default) and Claude fallback with retry/backoff.
- SlowAPI enforces per-IP rate limiting; OpenAI moderation guards prompt safety.
- Prometheus `/metrics` endpoint with shared counters/histograms for Fly scraping.
- Fly.io deployment (Dockerized) with health checks, autoscaling, and Redis sidecar.

## Design Principles
- Stateless API: every request carries complete context.
- Multi-modal priority: video → image → text; text augments visuals.
- Fail-fast & transparent errors with actionable codes; warnings in metadata for nonfatal issues.
- Idempotent outputs via caching + versioned keys.
- Confidence scoring combines product understanding, style clarity, and technical feasibility.

## Key Workflows
1. **Parse Request**: validate input → check cache → orchestrate inputs → generate creative_direction + scenes → validate + score → cache result → respond.
2. **Image Pipeline**: download/validate → resize/convert → CLIP + GPT-4V analysis → merge with text context.
3. **Video Pipeline**: download/validate → OpenCV extract first/last frames → analyze each frame → treat as primary visual reference.
- **Fallback Logic**: attempt preferred provider; on rate-limit/timeout, fall back; surface provider info via `/v1/providers`.
- **Batch Pipeline**: `/v1/parse/batch` reuses the same request processing helper concurrently (<=10 prompts).
- **Admin Tools**: `/v1/cache/clear` flushes Redis; `/metrics` exposes Prometheus metrics for monitoring.

