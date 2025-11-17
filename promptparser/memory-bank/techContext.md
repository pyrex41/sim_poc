# Tech Context

## Stack
- **Backend**: FastAPI (Python 3.11+), Uvicorn, Pydantic v2.
- **LLM Providers**: OpenAI GPT-4o (vision) primary, Claude Sonnet 4 fallback via Anthropic SDK.
- **Processing**: Pillow for image handling, OpenCV for video frame extraction, CLIP embeddings, optional lodash-style utilities via Python equivalents.
- **Caching**: Redis (asyncio) with 30-minute default TTL; cache key derived from prompt payload + provider selection.
- **Deployment**: Docker container on Fly.io (multi-region), health checks hitting `/v1/health`, Prometheus `/metrics` endpoint for Fly scraping.
- **Tooling**: Tenacity for retries, SlowAPI for rate limiting, structlog for JSON logs, prometheus-client for metrics, pytest for tests, k6 for load.

## Constraints
- Windows-first dev machines; after build, app must run without extra internet access besides LLM endpoints.
- 30+ FPS preview expectation influences scene pacing defaults; ensure outputs remain achievable by downstream renderer.
- Emphasis on stability: guard against crashes, memory leaks, long-running video/image processing.

## Integrations
- Downstream `gauntlet-video-server.fly.dev` expects consistent scene prompts, timing, and audio directives.
- FFmpeg sidecar (via Tauri in broader project) handles thumbnails/exports; ensure parser metadata supports those workflows (e.g., CTA timing, overlays).

