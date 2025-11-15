# Technical Deep Dive

_Updated: Nov 15, 2025_

## 1. Ensuring Visual Coherence
- **Multi-modal priority** (video → image → text) keeps the strongest visual signal as the canonical “style source.” Extracted palettes, lighting, composition, and mood are propagated to every scene template.
- **Smart defaults** keep platform and category conventions (aspect ratio, pacing, overlays) consistent when prompts are sparse.
- **LLM prompt scaffolding** injects extracted parameters, defaults, and previous iterations into a tightly constrained system prompt so that the JSON structure and stylistic anchors stay aligned.
- **Validator checks** flag mismatches (e.g., 9:16 output containing “wide landscape” cues or palettes exceeding 6 colors) and surface warnings to the caller.

## 2. Audio–Visual Synchronization
- Each scene carries `audio.music_intensity`, `sound_effects`, and optional `voiceover_text`; pacing metadata (cuts per minute, energy curve) is derived directly from the requested duration and category defaults.
- The parser outputs transition metadata (`transition_to_next`) and overlay timing so the downstream compositor knows when cuts occur and how text aligns with beats.
- Confidence scoring includes a `technical_feasibility` component that penalizes overly dense text overlays or sub-2s scenes, prompting the user to adjust before rendering.

## 3. Cost Optimization Strategy
- **Deterministic caching** (SHA-256 of normalized request payload + provider) prevents duplicate LLM spends for identical briefs.
- **Provider telemetry** tracks latency/rate limiting so we only escalate to Claude when OpenAI is actually degraded, minimizing more expensive inference calls.
- **Cost passthrough vs. fallback**: if upstream Replicate pricing is provided we honor it; otherwise the fallback estimator uses scene count + modality mix to give conservative expectations.
- Rate limiting (60/min per IP) protects the system from abusive spikes that could trigger costly LLM bursts.

## 4. Generation Failure Handling
- Input guardrails validate size/duration, run OpenAI moderation, and short-circuit before any LLM call.
- LLM requests are wrapped with structured retries (tenacity-ready), and every provider call is traced so the fallback chain can pivot automatically.
- Cache, Redis, or download failures degrade gracefully (warnings in metadata, HTTP 502/504 with actionable error codes when necessary).
- Validation warnings + confidence breakdown give downstream operators enough signal to reject or re-run before triggering expensive generation.

## 5. Pipeline Differentiators
- **Multimodal-first orchestration**: video/image analysis, CLIP-style embeddings, and text parsing feed a single creative direction template instead of disjoint heuristics.
- **Structured observability**: SlowAPI, structlog, and Prometheus metrics expose rate limits, provider latency, and cache stats for Fly dashboards.
- **Iteration-aware context**: `context.previous_config` and merge helpers support edit workflows without re-authoring the entire brief.
- **Battle-tested test suite**: 30+ unit/integration tests simulate cache hits, fallback logic, content safety, and multimodal prioritization, giving judges reproducible evidence.

