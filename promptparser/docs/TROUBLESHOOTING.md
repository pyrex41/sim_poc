# Troubleshooting Guide

| Issue | Symptoms | Fix |
|-------|----------|-----|
| **Port 8080 still busy / PID keeps changing** | `uvicorn` fails to bind (`error while attempting to bind on address ... 8080`) or `Get-NetTCPConnection` shows shifting PIDs. | Run `pwsh scripts/kill_port_occupant.ps1 -Port 8080 -Kill` (or `-Port 18080` if you used the alternate port). The script walks the parent process tree and terminates the reloader/root, preventing new children from respawning. |
| **Load-test script fails: `k6` not found** | `scripts/run_load_test.ps1` exits with “The term 'k6' is not recognized”. | Install k6 (`choco install k6` or download from k6.io) **or** rely on the built-in Docker fallback by installing Docker Desktop. |
| **Load-test script fails: Docker not running** | Error mentions `dockerDesktopLinuxEngine` or inability to connect to Docker socket. | Start Docker Desktop (or disable Docker fallback by installing the native k6 CLI). |
| **`OPENAI_API_KEY` looks empty inside script** | Script aborts with “environment variable is required” even though `.env` contains the key. | Either export the key in the same PowerShell session (`$env:OPENAI_API_KEY='sk-...'`) or pass it explicitly: `pwsh scripts/run_load_test.ps1 -OpenAIKey 'sk-...'`. Cursor masks secrets when reading `.env`, so the script cannot see them without one of these methods. |
| **Redis unreachable / connection refused** | `/v1/health` shows `redis: false` or parse requests log cache errors. | For local work, set `REDIS_URL=memory://` (already the default in `.env.example`) to enable the in-memory cache fallback. In production, verify the Fly secrets and ensure the Redis service/security group allows connections. |
| **k6 run hits 429 errors mid-test** | Summary shows many `Too Many Requests`. | Raise the limiter via `RATE_LIMIT_PER_MINUTE` (the load-test script already sets 600). Ensure you’re targeting a dedicated load-test base URL so normal traffic doesn’t trip the limiter. |
| **EOF / connection reset during k6 run** | k6 stack trace: `the body is null ... EOF` or `wsarecv: An existing connection was forcibly closed...`. | Use the current `tests/load/load_test.js` (includes `Connection: close`) and ensure `scripts/run_load_test.ps1` is binding to a dedicated port (e.g., `-BaseUrl http://127.0.0.1:18080`). |

## Quick Commands

```powershell
# Kill anything on port 8080 (or 18080)
pwsh scripts/kill_port_occupant.ps1 -Port 8080 -Kill

# Start load test on alternate port with mock LLM + memory cache
pwsh scripts/run_load_test.ps1 -BaseUrl http://127.0.0.1:18080

# Run load test with real providers (requires keys & Redis)
pwsh scripts/run_load_test.ps1 `
  -BaseUrl http://127.0.0.1:8080 `
  -UseMockLLM:$false `
  -OpenAIKey (Get-Secret OPENAI_API_KEY)
```

Keep this file updated whenever a new failure mode or mitigation is discovered.

