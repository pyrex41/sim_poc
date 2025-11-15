# Load Testing (Task 2.5.2)

Use [k6](https://k6.io) to stress `/v1/parse` and verify:

- 10 concurrent users for ~5 minutes
- p95 latency < 8 seconds
- Error rate < 2%
- Cache hit ratio > 30% (reported via Prometheus metrics and k6 custom counters)

## Prerequisites

- API running locally (`uvicorn app.main:app --port 8080`) or deployed base URL.
- Cache backend reachable. For quick tests you can set `REDIS_URL=memory://` to enable the built-in in-memory cache (expires entries after the same TTL). For production runs, point to an actual Redis instance.
- Rate limiter adjusted for load testing (e.g., `RATE_LIMIT_PER_MINUTE=600`).
- `OPENAI_API_KEY` exported in the shell running the API (not needed when `USE_MOCK_LLM=1`).
- Optional: `USE_MOCK_LLM=1` to enable the deterministic mock provider (avoids external OpenAI/Claude calls during load).
- k6 installed locally or run via Docker:

```powershell
docker run -i grafana/k6 run - < promptparser/tests/load/load_test.js
```

## Running the Test

```powershell
set BASE_URL=http://127.0.0.1:8080
set REDIS_URL=memory://
set RATE_LIMIT_PER_MINUTE=600
set USE_MOCK_LLM=1
k6 run tests/load/load_test.js
```

## What to Capture

1. k6 summary (p95 latency, error rate).  
2. Cache metrics snapshot (Prometheus `/metrics` → `prompt_parser_cache_hits_total` / `prompt_parser_cache_misses_total`).  
3. Cache hit ratio reported at the bottom of the k6 summary (custom counter).  
4. Notes on warnings/failures and any tuning performed.

Document the results in the project README or a release note for Phase 2 sign-off.

## Latest Run (Nov 15, 2025)

Command:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_load_test.ps1 -BaseUrl http://127.0.0.1:18080
```

Results (mock LLM + memory cache fallback):
- Duration: 5 minutes with 10 virtual users
- p95 latency: **5.26 ms**
- Error rate: **0%** (after dynamic rate-limit + connection-close fix)
- Cache hit ratio: **99.82%**
- Requests processed: 547

Artifacts:
- Full k6 summary printed to the console and linked in `README.md`
- Port cleanup handled automatically by `scripts/kill_port_occupant.ps1` (invoked before/after the run)

Re-run the test whenever major backend changes land and update this section with the new date/metrics.

