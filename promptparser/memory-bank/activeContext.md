# Active Context

## Current Focus (Nov 15, 2025)
- Phase 2 (incl. load-testing harness + results + documentation bundle) is signed off; shift fully to Phase 3 polish/deliverables.
- Keep all enhancements scoped to `promptparser/` to avoid impacting other teams.
- Maintain comprehensive test coverage (unit + integration + load) as final docs/demo assets are produced.

## Recent Decisions
- All work—including docs, code, and memory—must stay confined to `promptparser/` to avoid impacting other teams.
- Memory Bank lives at `promptparser/memory-bank/` with required core files for session-to-session continuity.
- Claude Sonnet acts as fallback provider only; OpenAI remains default (mock provider available for tests/automation).
- Cost estimates may be supplied by upstream Replicate data or auto-generated via fallback logic.
- SlowAPI limiter + OpenAI moderation guard `/v1/parse`; document rate limits for future users.
- Scene responses are now validated server-side; malformed LLM scenes trigger deterministic regeneration + warnings instead of 500s.
- `scripts/run_prompt_local.ps1` now supports mock-mode, captures uvicorn logs, and echoes prompt/output so manual QA is simpler.

## Next Up
1. Execute remaining Phase 3 deliverables: record/demo per `docs/DEMO_PLAN.md`, gather real sample outputs/screens, and prep submission bundle.
2. Keep load-test + cleanup scripts handy so every regression test starts/ends cleanly (rerun if major backend changes land).
3. Monitor for lingering doc gaps or Phase 3 judge feedback; update Memory Bank + docs as soon as new requirements arrive.

