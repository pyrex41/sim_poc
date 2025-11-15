# System Architecture

```
┌────────────────────────────────────────────────────────────┐
│          Client / Creative Tools (REST callers)            │
└───────────────┬────────────────────────────────────────────┘
                │  JSON request (text/image/video, options)
        ┌───────▼────────────────────────────────────────────┐
        │                 FastAPI Application                │
        │  (app.main:app with dependency-injected services)  │
        └───────┬──────────────────────────────┬─────────────┘
                │                              │
   ┌────────────▼────────────┐      ┌───────────▼───────────┐
   │      Request Layer      │      │  Observability Layer  │
   │ `/v1/parse`, `/batch`,  │      │  structlog + metrics  │
   │ `/health`, `/admin`     │      │  + SlowAPI limiter    │
   └────────────┬────────────┘      └───────────┬───────────┘
                │                               │
      ┌─────────▼───────────┐       ┌───────────▼──────────┐
      │   Core Services     │       │   Cache / Storage    │
      │ (input orchestration│       │ Redis (async)        │
      │ scene generator,    │<──────│ or memory fallback   │
      │ validator, cost est)│       └───────────┬──────────┘
      └─────────┬───────────┘                   │
                │                               │
      ┌─────────▼────────────┐         ┌────────▼─────────┐
      │ LLM Provider Registry│         │ Media Processors │
      │ (OpenAI + Claude +   │         │ (Pillow/OpenCV)  │
      │ mock for tests)      │         │ video > image >  │
      └─────────┬────────────┘         │ text prioritizer │
                │                      └──────────────────┘
                │
        ┌───────▼────────────┐
        │ Downstream Outputs │
        │ creative_direction │
        │ scenes + metadata  │
        └─────────┬──────────┘
                  │
  ┌───────────────▼─────────────────┐
  │ gauntlet-video-server (Fly.io)  │
  │ renders actual video assets     │
  └─────────────────────────────────┘
```

## Key Components

- **API Layer** – FastAPI routers implement `/v1/parse`, `/v1/parse/batch`, `/v1/health`, `/v1/providers`, `/v1/cache/clear`, `/metrics`.
- **Core Services** – Input orchestrator prioritises video > image > text; `scene_generator`, `validator`, `cost_estimator`, `edit_handler`, and `content_safety` compose the final payload.
- **LLM Providers** – Abstract base class with OpenAI GPT-4o default, Claude Sonnet fallback, and a deterministic mock provider for tests/load runs.
- **Caching** – Redis preferred; `memory://` toggles in-process cache for local testing. Deterministic keys ensure idempotent responses and protect LLM quotas.
- **Observability** – `structlog` for JSON logs, Prometheus metrics via `app/core/metrics.py`, and SlowAPI rate limiting (configurable via `RATE_LIMIT_PER_MINUTE`).
- **Automation** – `scripts/run_load_test.ps1` spins up uvicorn, runs k6, and tears down; `scripts/kill_port_occupant.ps1` kills stray processes holding the target port.

## Deployment Topology

- **Runtime**: Dockerized FastAPI app deployed on Fly.io.
- **Scale**: Stateless web instances; Redis may run as Fly.io addon or remote service.
- **Health & Metrics**: Fly hits `/v1/health`; Prometheus (or Fly’s agent) scrapes `/metrics`.
- **Secrets**: Managed via Fly secrets (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`, etc.).

## Request Lifecycle

1. Client sends prompt payload to `/v1/parse`.
2. SlowAPI enforces per-IP throttling; OpenAI moderation (if configured) validates text safety.
3. Deterministic cache key checked in Redis/memory.
4. Input orchestrator loads video/image references, extracts basic features, and merges with text defaults.
5. Prompt builder composes system/user prompts and calls the LLM provider registry (primary + fallback order).
6. Scene generator fills any missing scenes; validator issues warnings/confidence breakdown; cost estimator provides fallback pricing if requested.
7. Response cached and returned with metadata (warnings, provider used, cache hit flag, etc.).
8. Logs + metrics record latency, cache hit/miss, and provider stats for observability.

Use this document alongside `docs/DEPLOYMENT.md` and `docs/TROUBLESHOOTING.md` when extending or operating the service.

