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
```

`OPENAI_API_KEY` must be set before starting the API so the default OpenAI GPT-4o provider can initialize successfully.
`ANTHROPIC_API_KEY` enables Claude fallback; without it the service continues using OpenAI only.

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

### Docker Build
```bash
docker build -t prompt-parser-api .
docker run -p 8080:8080 --env-file .env prompt-parser-api
```

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
