"""Parse endpoint."""

import json
from typing import Any, Tuple, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from app.models.request import ParseRequest
from app.models.response import ParseResponse, Scene
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

logger = structlog.get_logger(__name__)

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

    settings = get_settings()
    default_provider = "mock" if settings.USE_MOCK_LLM else "openai"
    primary_name = parse_request.options.llm_provider or default_provider
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

    scenes, scene_warnings = _prepare_scenes(creative_direction)
    warnings = scene_warnings + validate_scenes(creative_direction, scenes)
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


# derive rate limit from settings so tests can override RATE_LIMIT_PER_MINUTE
_parse_rate_limit = f"{get_settings().RATE_LIMIT_PER_MINUTE}/minute"


@router.post("/parse", response_model=ParseResponse)
@limiter.limit(_parse_rate_limit)
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


def _prepare_scenes(creative_direction: dict[str, Any]) -> Tuple[List[dict[str, Any]], List[str]]:
    """Normalize LLM scenes or regenerate defaults if invalid."""
    raw_scenes = creative_direction.get("scenes")
    if not raw_scenes:
        generated = generate_scenes(creative_direction)
        creative_direction["scenes"] = generated
        return generated, [
            "Scenes auto-generated because LLM response omitted required fields."
        ]

    normalized: List[dict[str, Any]] = []
    for idx, raw in enumerate(raw_scenes):
        try:
            scene = Scene.model_validate(raw)
        except ValidationError as exc:
            logger.warning(
                "scene_validation_failed",
                scene_index=idx,
                errors=exc.errors(),
            )
            generated = generate_scenes(creative_direction)
            creative_direction["scenes"] = generated
            return generated, [
                "Scenes regenerated because LLM output did not match the schema."
            ]
        normalized.append(scene.model_dump())

    creative_direction["scenes"] = normalized
    return normalized, []
