# Prompt Parser API – Product Context

## Problem & Users
- Creative teams submit vague prompts and references; downstream video generation needs precise direction.
- The parser bridges user intent to generation-ready specs, saving time and cost.

## Value Propositions
1. **Upscale prompts** into professional briefs with intelligent defaults.
2. **Extract visual style** from reference images/videos (visual input takes precedence).
3. **Fill gaps + validate feasibility** before expensive rendering.
4. **Expose costs + confidence** so users know what to expect.

## User Journey
```
User Prompt (text/image/video)
      ↓
Prompt Parser API (this project)
      ↓
Creative Direction JSON
      ↓
Partner Video Generator (gauntlet-video-server.fly.dev)
      ↓
Final Video
```

## Experience Goals
- Synchronous REST responses <10 s (p95) for MVP, <8 s full release.
- Transparent metadata: confidence breakdown, warnings, cache hits, provider used.
- Consistent JSON schema for downstream automation; idempotent via caching.

## Out of Scope
- Authentication/authorization, actual media generation, payments, long-term storage, streaming responses.

