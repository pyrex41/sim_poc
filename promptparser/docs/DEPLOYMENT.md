## Prompt Parser Deployment Guide

### 1. Prerequisites
- Fly CLI installed and logged in (`fly auth login`).
- Docker installed (Fly builds via Dockerfile).
- Required secrets: `OPENAI_API_KEY`, `REDIS_URL` (or use Fly Redis add-on).

### 2. Build & Test Locally
```bash
cd promptparser
py -3.11 -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
docker build -t prompt-parser-api .
```

### 3. Fly.io Configuration
- `fly.toml` already references the Dockerfile and exposes port 8080.
- Health checks hit `/v1/health`, so make sure Redis + OpenAI credentials are valid before deploy.

### 4. Launch & Deploy
```bash
fly launch --name prompt-parser-api --copy-config --no-deploy
fly secrets set OPENAI_API_KEY=sk-... REDIS_URL=redis://...
fly deploy
```

### 5. Monitoring
- `fly status` for machine health.
- `/v1/health` endpoint reflects Redis + LLM availability.
- Logs: `fly logs`

### 6. Rollbacks
```bash
fly releases list
fly deploy --image <previous-image>
```

### 7. Future Hooks
- Once Replicate cost data is available, ensure upstream service pushes it via `cost_estimate` in the parse request.
- For multi-region scaling, adjust `primary_region` and add `[http_service]` machines as needed.

