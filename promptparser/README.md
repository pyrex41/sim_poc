## Prompt Parser API

MVP FastAPI service that transforms unstructured prompts (text/image/video) into structured creative direction JSON for downstream AI video generation.

### Structure
- `app/` – FastAPI source
  - `main.py` – application entrypoint
  - `core/config.py` – settings via `python-dotenv`/environment
  - `core/logging.py` – logging bootstrap
- `prompt-parser-prd.md` – product requirements
- `prompt-parser-tasks.md` – backlog/tasks
- `memory-bank/` – persistent context summaries

### Getting Started
Requires Python 3.11 (install via `winget install Python.Python.3.11` on Windows).

```bash
cd promptparser
py -3.11 -m venv .venv
. .venv/Scripts/activate        # or .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # fill in values
uvicorn app.main:app --reload --port 8080
```

### Environment Variables (`.env`)
```
APP_ENV=development
LOG_LEVEL=INFO
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_PER_MINUTE=60
USE_MOCK_LLM=false
```

`OPENAI_API_KEY` must be set before starting the API so the default OpenAI GPT-4o provider can initialize successfully.
`ANTHROPIC_API_KEY` enables Claude fallback; without it the service continues using OpenAI only.
Set `REDIS_URL=memory://` to use the in-memory cache fallback during local development/testing (handy if you don’t have Redis running). Use `USE_MOCK_LLM=true` to bypass external LLM calls and rely on the built-in deterministic mock provider (ideal for tests, CI, and load generation).

### Cost Estimate Passthrough
- Clients can provide a `cost_estimate` object in the parse request body (populated from Replicate or any downstream service).
- The API simply echoes that payload back in the response under `cost_estimate` so users can see pricing details without the parser computing them.

### Multi-Modal Inputs
- `prompt` accepts `text`, `image_url`/`image_base64`, and `video_url`/`video_base64`.
- Input orchestrator prioritizes **video > image > text** to set `visual_direction.style_source` and returns `extracted_references` with stub analyses for downstream consumers.
- Text context still feeds default extraction even when visual references are primary.

### Batch Parsing
- POST `/v1/parse/batch` accepts up to 10 prompts. Each response entry mirrors the single-parse schema with per-item status.
- All batch items reuse caching/LLM fallback logic.

### Cost Fallback
- Set `options.include_cost_estimate: true` when calling `/v1/parse`.
- If a `cost_estimate` payload isn’t supplied, the API computes a conservative fallback estimate (see `options.cost_fallback_enabled` to disable).

### Rate Limiting & Safety
- `/v1/parse` is rate limited to ~60 requests/minute per IP via SlowAPI.
- Prompt text runs through OpenAI’s moderation endpoint when an API key is configured; flagged prompts return `400`.

### Admin & Metrics
- GET `/v1/providers` lists configured LLM providers (OpenAI default, optional Claude fallback) with latency hints.
- POST `/v1/cache/clear` dumps cached prompts (admin/debug purposes).
- GET `/metrics` exposes Prometheus-formatted counters/histograms for Fly or any scraper.

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest -v
```

### Load Testing (Task 2.5.2)
```bash
set BASE_URL=http://127.0.0.1:8080
set REDIS_URL=memory://
set RATE_LIMIT_PER_MINUTE=600
set USE_MOCK_LLM=1
k6 run tests/load/load_test.js
```

See `tests/load/README.md` for required environment variables (including the `OPENAI_API_KEY`), cache hit metrics, and Docker-based commands if you prefer containers.

Or run the bundled automation (PowerShell defaults to the in-memory cache backend, higher rate limit, and automatic port cleanup):

```powershell
cd promptparser
powershell -ExecutionPolicy Bypass -File scripts/run_load_test.ps1 -BaseUrl http://127.0.0.1:8080
```

By default the script enables the mock LLM (`USE_MOCK_LLM=1`), so no external API calls or keys are required; pass `-UseMockLLM:$false -OpenAIKey '<key>'` if you need to exercise real providers. The automation bootstraps the virtualenv, installs deps, launches uvicorn (memory cache + higher rate limit), executes the 10-user/5-minute k6 scenario, prints the summary (including cache hit ratio), and gracefully shuts everything down.

**Latest run (Nov 15, 2025 – BaseUrl `http://127.0.0.1:18080`, mock LLM + memory cache):**
- p95 latency **5.26 ms**
- Error rate **0%**
- Cache hit ratio **99.82%**
- Requests processed: 547 in 5 minutes (10 VUs)

Use `scripts/kill_port_occupant.ps1 -Port <port> -Kill` before/after experiments if a stray watchdog holds onto the previous uvicorn port.

### Documentation Map

- `docs/API.md` – endpoint reference + example requests
- `docs/DEPLOYMENT.md` – Fly.io + Docker deployment steps
- `docs/ARCHITECTURE.md` – component diagram and request lifecycle
- `docs/TROUBLESHOOTING.md` – common local/dev issues and resolutions
- `docs/SAMPLE_OUTPUTS.md` – curated creative direction samples
- `docs/TECHNICAL_DEEP_DIVE.md` – judge-ready Q&A
- `docs/DEMO_PLAN.md` – outline for Phase 3 video/demo

### Docker Build
```bash
docker build -t prompt-parser-api .
docker run -p 8080:8080 --env-file .env prompt-parser-api
```

### Quick CLI Smoke Test

Use the bundled script to send a text prompt and print the `creative_direction` block:

```bash
cd promptparser
python scripts/prompt_cli.py "30 second Instagram ad for luxury watches"
# or read from stdin:
python scripts/prompt_cli.py <<'TXT'
Create a 20 second TikTok ad for a new sparkling water flavor.
TXT
```

Flags:
- `--base-url` (defaults to `http://127.0.0.1:8080` or `PROMPT_PARSER_BASE_URL`)
- `--include-cost` to request fallback cost estimates

The script exits non-zero on HTTP errors and prints the full response when `creative_direction` is missing.

### One-Command Local Prompt Run

Need to spin up the API, hit it once, and tear it down automatically? Use the PowerShell helper (requires your `OPENAI_API_KEY` either via `-OpenAIKey` or environment variable):

```powershell
cd promptparser
pwsh scripts/run_prompt_local.ps1 `
  -Prompt "30 second Instagram ad for luxury watches" `
  -OpenAIKey "sk-..." `
  -BaseUrl http://127.0.0.1:8080
```

What it does:
- Ensures `.venv` + requirements are installed.
- Starts uvicorn with `REDIS_URL=memory://`, `RATE_LIMIT_PER_MINUTE=600`.
- Calls `scripts/prompt_cli.py` to print the `creative_direction` (add `-IncludeCost` to request fallback estimates).
- Shuts down uvicorn before exiting.

Run without `-Prompt` to be prompted interactively; omit `-OpenAIKey` if you already exported `OPENAI_API_KEY` in the shell.
Optional flags:
- `-IncludeCost` – request fallback cost estimate.
- `-UseMockLLM` – skip real OpenAI/Claude calls (handy when offline or rate-limited).

If the CLI request fails, the script now prints the tail of `uvicorn_prompt.log` so you can see the server traceback immediately.

### Response Reliability

- The API validates every scene coming back from the LLM. If the payload is missing required fields (e.g., `duration`, `visual`) the service logs the issue, regenerates scenes locally, and still returns a structured payload with a warning in `metadata`.
- Deterministic fallback scenes ensure the frontend always has a `creative_direction` + `scenes` block even when the upstream provider misbehaves.

### Fly.io Deploy
```bash
fly launch --name prompt-parser-api --copy-config --no-deploy
fly deploy
```

### References
- See `prompt-parser-prd.md` for full specification.
- Implementation tasks tracked in `prompt-parser-tasks.md`.
- Deployment steps in `docs/DEPLOYMENT.md`.
- API reference in `docs/API.md`.
