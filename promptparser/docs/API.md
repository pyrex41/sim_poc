## Prompt Parser API Reference

### Base URL
```
https://prompt-parser-api.fly.dev
```

### Authentication
- None for MVP (trusts upstream caller). Add auth headers before production hardening.

---

## POST `/v1/parse`
Transforms user prompts into creative direction JSON.

### Request Body
```json
{
  "prompt": {
    "text": "30 second Instagram ad for luxury watches",
    "image_url": "https://example.com/ref.jpg",
    "video_url": "https://example.com/ref.mp4"
  },
  "options": {
    "llm_provider": "openai",
    "include_cost_estimate": false,
    "cost_fallback_enabled": true
  },
  "cost_estimate": {
    "total_usd": 1.45,
    "breakdown": {
      "video_generation": 1.20,
      "audio_generation": 0.25
    }
  }
}
```
- At least one of `text`, `image_*`, or `video_*` must be provided.
- When both video and image exist, video becomes the primary style source.
- `cost_estimate` is optional passthrough data from Replicate or other downstream services.
- `options.llm_provider` can be `openai` or `claude`. If the selected provider fails, the API automatically falls back to any remaining configured providers.
- If `options.include_cost_estimate` is true and `cost_estimate` is omitted, the parser computes a low-confidence fallback (disable with `cost_fallback_enabled: false`).

### Success Response (200)
```json
{
  "status": "success",
  "creative_direction": {
    "product": {...},
    "technical_specs": {...},
    "visual_direction": {"style_source": "video", ...},
    "...": "..."
  },
  "scenes": [
    {"id": "scene_1", "purpose": "hook", "duration": 4.0, "...": "..."}
  ],
  "metadata": {
    "cache_hit": false,
    "defaults_used": ["technical_specs.aspect_ratio"],
    "warnings": [],
    "confidence_score": 0.82,
    "confidence_breakdown": {
      "product_understanding": 0.74,
      "style_clarity": 0.9,
      "technical_feasibility": 0.83
    }
  },
  "cost_estimate": {
    "total_usd": 1.45,
    "breakdown": {...}
  },
  "extracted_references": {
    "videos": [
      {
        "reference": "https://example.com/ref.mp4",
        "frames": [
          {"frame_type": "first", "analysis": {"lighting": "dynamic"}}
        ]
      }
    ]
  }
}
```

### Error Responses
- `400`: validation error (missing inputs, text too long, etc.).
- `502`: LLM provider failure (rate limit, timeout).
- `504`: future use when orchestrating long-running requests.

---

## POST `/v1/parse/batch`
Processes up to 10 prompts in one call. Body is an array of objects shaped like the single parse request. Response:
```json
{
  "status": "success",
  "results": [
    {"status": "success", "response": { /* /v1/parse payload */ }},
    {"status": "error", "error": "message"}
  ]
}
```

---

## GET `/v1/health`
Returns service health for Fly/monitoring.

### Sample Response
```json
{
  "status": "healthy",
  "redis": true,
  "llm_available": true
}
```

---

## GET `/v1/providers`
Lists configured LLM providers and their estimated latency. Useful for dashboards or diagnosing availability.

---

## POST `/v1/cache/clear`
Clears cached parse results (debug/admin use). Returns count of removed keys.

---

## GET `/metrics`
Prometheus-formatted metrics endpoint. Scrape via Fly or Prometheus to collect runtime stats (includes default Python metrics plus custom histograms/counters as they are added).

---

## Notes
- Cache TTL defaults to 30 minutes; repeated prompts may return instantly with `metadata.cache_hit: true`.
- Multi-modal analysis currently uses lightweight stubs; swap in real image/video analyzers without changing the API.
- `/v1/parse/batch` mirrors the single parse behavior for multiple prompts.
- `/v1/parse` enforces ~60 requests per minute per IP (SlowAPI). Prompt text is moderated via OpenAI when an API key is configured; flagged prompts return HTTP 400.
- Admin/ops: `/v1/providers`, `/v1/cache/clear`, and `/metrics` support observability and cache management.

