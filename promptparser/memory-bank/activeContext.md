# Active Context

## Current Focus (Nov 15, 2025)
- Phase 2 completion: multi-modal processing, Claude fallback, batch endpoint, cost fallback, rate limiting/content safety, admin + metrics endpoints.
- Keep all enhancements scoped to `promptparser/` to avoid impacting other teams.
- Maintain comprehensive test coverage (unit + integration) as we add Phase 2/3 features.

## Recent Decisions
- All work—including docs, code, and memory—must stay confined to `promptparser/` to avoid impacting other teams.
- Memory Bank lives at `promptparser/memory-bank/` with required core files for session-to-session continuity.
- Claude Sonnet acts as fallback provider only; OpenAI remains default.
- Cost estimates may be supplied by upstream Replicate data or auto-generated via fallback logic.
- SlowAPI limiter + OpenAI moderation guard `/v1/parse`; document rate limits for future users.

## Next Up
1. Finish remaining Phase 2 polish (structured logging metrics instrumentation, documentation refinements).
2. Transition to Phase 3 (demo prep, sample outputs, deep dive docs) once core endpoints stabilized.
3. Continue updating README/API/docs + memory-bank after each major milestone.

