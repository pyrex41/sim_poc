# Prompt Parser API – Project Brief

## Overview
- Build the Prompt Parser REST API that turns messy user prompts (text, image, video) into structured creative direction JSON for AI video generation.
- Operate strictly inside `promptparser/`; other teams handle the rest of `sim_poc`.
- MVP due **Nov 16, 2025 @ 10:59 PM CT**; full release by **Nov 22, 2025 @ 10:59 PM CT**.

## Objectives
1. Parse prompts into detailed `creative_direction`, scene breakdowns, and metadata.
2. Support multi-modal inputs (text, image, video) with priority Video > Image > Text.
3. Provide validation, confidence scoring, caching, cost estimation, and provider fallback.
4. Deliver clear API contracts + docs so downstream video generator can consume outputs.

## Constraints
- Stack: FastAPI (Py 3.11), Redis cache, OpenAI GPT-4o primary, Claude Sonnet fallback, Fly.io deployment.
- Windows-focused dev env; no touching project roots outside `promptparser/`.
- Emphasis on stability (fail-fast, graceful degradation, caching).

## Key Deliverables
- FastAPI service with `/v1/parse`, `/v1/health`, later `/v1/parse/batch`, `/v1/providers`, `/v1/cache/clear`.
- Image/video processing pipelines, smart defaults, scene generator, validation/confidence scoring, cost estimator.
- Redis-backed cache, structured logging, metrics, content safety, rate limiting.
- Deployment assets (Dockerfile, fly.toml) and docs (README, API refs, technical deep dive, demo prep).

