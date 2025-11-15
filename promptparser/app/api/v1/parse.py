"""Parse endpoint."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from app.models.request import ParseRequest
from app.models.response import ParseResponse
from app.prompts.creative_direction import (
    CREATIVE_DIRECTION_SYSTEM_PROMPT,
    build_creative_direction_prompt,
)
from app.services.cache import CacheManager, generate_cache_key
from app.core.limiter import limiter
from app.services.defaults import apply_smart_defaults
from app.services.llm.base import LLMProvider
from app.services.input_orchestrator import analyze_inputs
from app.services.parsers.text_parser import parse_text_prompt
from app.services.scene_generator import generate_scenes
from app.services.validator import calculate_confidence, validate_scenes
from app.services.edit_handler import merge_iterative_edit
from app.services.cost_estimator import estimate_cost
from app.services.content_safety import ensure_prompt_safe, ContentSafetyError

router = APIRouter()


async def process_parse_request(
    parse_request: ParseRequest,
    cache: CacheManager,
    llm_providers: dict[str, LLMProvider],
) -> ParseResponse:
    payload = parse_request.model_dump()
    cache_key = generate_cache_key(payload)
    cached = await cache.get(cache_key)
    if cached:
        cached["metadata"]["cache_hit"] = True
        return ParseResponse(**cached)

    parsed_prompt = parse_text_prompt(parse_request.prompt.text or "")
    defaults = apply_smart_defaults(parsed_prompt.to_dict())
    input_analysis = await analyze_inputs(parse_request.prompt)
    merged_context = None
    if parse_request.context and parse_request.context.previous_config:
        merged_context = merge_iterative_edit(parse_request.context.previous_config, parse_request.prompt.text or "")

    user_prompt = build_creative_direction_prompt(
        parse_request.prompt.text or "",
        extracted_parameters=parsed_prompt.to_dict(),
        applied_defaults=defaults,
        visual_context=input_analysis.reference_summary if input_analysis else None,
        previous_config=merged_context,
    )

    primary_name = parse_request.options.llm_provider or "openai"
    provider_order: list[tuple[str, LLMProvider]] = []
    if provider := llm_providers.get(primary_name):
        provider_order.append((primary_name, provider))
    # add fallback providers if not already queued
    for name, provider in llm_providers.items():
        if all(provider is existing for _, existing in provider_order):
            continue
        provider_order.append((name, provider))

    creative_direction = None
    provider_used_name: str | None = None
    last_error: Exception | None = None
    tried = []
    for provider_name, provider in provider_order:
        tried.append(provider_name)
        try:
            completion = await provider.complete(
                user_prompt,
                system_prompt=CREATIVE_DIRECTION_SYSTEM_PROMPT,
                response_format={"type": "json_object"},
            )
            creative_direction = json.loads(completion or "{}")
            provider_used_name = provider_name
            break
        except Exception as exc:  # pragma: no cover
            last_error = exc
            continue

    if creative_direction is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM providers failed: {last_error}",
        ) from last_error

    visual_direction = creative_direction.setdefault("visual_direction", {})
    if input_analysis:
        visual_direction = creative_direction.setdefault("visual_direction", {})
        visual_direction["style_source"] = input_analysis.style_source

    scenes = creative_direction.get("scenes") or generate_scenes(creative_direction)
    warnings = validate_scenes(creative_direction, scenes)
    confidence = calculate_confidence(parsed_prompt.to_dict(), scenes, warnings)
    metadata = {
        "cache_hit": False,
        "defaults_used": defaults.get("metadata", {}).get("defaults_used", []),
        "warnings": warnings,
        **confidence,
    }
    if provider_used_name:
        metadata["llm_provider_used"] = provider_used_name

    response_dict: dict[str, Any] = {
        "status": "success",
        "creative_direction": creative_direction,
        "scenes": scenes,
        "metadata": metadata,
    }
    if parse_request.cost_estimate is not None:
        response_dict["cost_estimate"] = parse_request.cost_estimate
    elif parse_request.options.include_cost_estimate and parse_request.options.cost_fallback_enabled:
        response_dict["cost_estimate"] = estimate_cost(scenes)
    if input_analysis:
        response_dict["extracted_references"] = input_analysis.extracted_references

    await cache.set(cache_key, response_dict)
    return ParseResponse(**response_dict)


@router.post("/parse", response_model=ParseResponse)
@limiter.limit("60/minute")
async def parse_prompt(
    request: Request,
    parse_request: ParseRequest,
    cache: CacheManager = Depends(get_cache_manager),
    llm_providers: dict[str, LLMProvider] = Depends(get_llm_provider_registry),
) -> ParseResponse:
    try:
        await ensure_prompt_safe(parse_request.prompt.text or "")
    except ContentSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return await process_parse_request(parse_request, cache, llm_providers)
