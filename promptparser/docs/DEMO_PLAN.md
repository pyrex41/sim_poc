# Demo Video Plan (5–7 Minutes)

_Purpose: cover prompt-to-output flow, architecture walkthrough, style comparisons, and key innovations._

## 1. Audience & Setup
- **Audience:** AI Video Pipeline judges + partner engineers.
- **Environment:** Local FastAPI instance (`uvicorn app.main:app`), Redis running, HTTP client (Bruno or curl), browser tabs for docs.
- **Artifacts:** `docs/SAMPLE_OUTPUTS.md`, Prometheus dashboard screenshot, Fly deployment page.

## 2. Agenda & Timing
| Segment | Duration | Content |
| --- | --- | --- |
| Intro & Problem Framing | 0:00 – 0:45 | Why prompt parsing matters, recap competition goals. |
| Live Text Prompt Parse | 0:45 – 2:15 | Send curl request, show JSON response, highlight creative_direction + scenes. |
| Multi-modal Showcase | 2:15 – 3:45 | Run image-primary and video-primary requests, compare metadata (style_source, confidence). |
| Architecture Walkthrough | 3:45 – 5:00 | Slide/diagram covering FastAPI modules, Redis cache, LLM fallback, SlowAPI, Prometheus. |
| Trade-offs & Innovations | 5:00 – 6:00 | Discuss caching strategy, fallback resilience, validation warnings, cost transparency. |
| Closing & Next Steps | 6:00 – 6:45 | Mention Phase 3 docs, invite Q&A. Buffer for overruns. |

## 3. Live Demo Script
1. **Kickoff:** 1-slide summary referencing PRD progress (Phase 3 polish underway).
2. **Text Prompt Run:** Use a luxury watch curl example; copy excerpt from `docs/SAMPLE_OUTPUTS.md` to explain sections.
3. **Image Prompt Run:** Upload sneaker photo via URL, highlight extracted palette + `style_source: image`.
4. **Video Prompt Run:** Reference hosted clip, show extracted first/last frames and warnings.
5. **Highlight Metadata:** Point out confidence breakdown, cache hits, and provider tracking.
6. **Observability:** Tail structured logs (`structlog`) + show `/metrics` endpoint for Prometheus scraping.
7. **Fallback Story:** Simulate OpenAI failure via env flag (mock) and show Claude takeover in metadata.

## 4. Supporting Materials
- **Slides:** 3 slides (Problem, Architecture, Differentiators) – reuse diagram from PRD section 3.
- **Docs:** Link to `docs/TECHNICAL_DEEP_DIVE.md` for judges wanting deeper answers.
- **Sample Outputs:** Provide JSON snippets via `docs/SAMPLE_OUTPUTS.md`.

## 5. Risks & Mitigations
- **LLM latency:** Prewarm cache with sample prompts; mention timestamp showing cache hits.
- **Network hiccups:** Keep offline copies of responses for backup (JSON files in `/docs/examples/` if time permits).
- **Time overrun:** Agenda includes 45s buffer; rehearsals target 6 minutes.

