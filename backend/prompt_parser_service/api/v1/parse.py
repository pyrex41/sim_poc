"""Parse endpoint."""

import json
from typing import Any, Tuple, List, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import ValidationError

# Import auth from main backend
from ....auth import verify_auth

from ....config import get_settings
from ...core.dependencies import get_cache_manager, get_llm_provider_registry
from ...models.request import ParseRequest, PromptInput
from ...models.response import ParseResponse, Scene
from ...prompts.creative_direction import (
    CREATIVE_DIRECTION_SYSTEM_PROMPT,
    build_creative_direction_prompt,
)
from ...services.cache import CacheManager, generate_cache_key
from ...core.limiter import limiter
from ...services.defaults import apply_smart_defaults
from ...services.llm.base import LLMProvider
from ...services.input_orchestrator import analyze_inputs
from ...services.parsers.text_parser import parse_text_prompt
from ...services.scene_generator import generate_scenes
from ...services.validator import calculate_confidence, validate_scenes
from ...services.edit_handler import merge_iterative_edit
from ...services.cost_estimator import estimate_cost
from ...services.content_safety import ensure_prompt_safe, ContentSafetyError

# Import database functions
from ....database import save_creative_brief
import uuid

logger = structlog.get_logger(__name__)

router = APIRouter()


async def process_parse_request(
    parse_request: ParseRequest,
    cache: CacheManager,
    llm_providers: dict[str, LLMProvider],
    bypass_cache: bool = False,
    model_name: str = None,
) -> ParseResponse:
    payload = parse_request.model_dump()
    if model_name:
        payload['model'] = model_name  # Include model in key for bypass
    cache_key = generate_cache_key(payload)
    if not bypass_cache:
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
    default_provider = "mock" if settings.USE_MOCK_LLM else settings.DEFAULT_LLM_PROVIDER
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
    bypass_cache: bool = False,
    current_user: Dict[str, Any] = Depends(verify_auth),  # Add authentication
    cache: CacheManager = Depends(get_cache_manager),
    llm_providers: dict[str, LLMProvider] = Depends(get_llm_provider_registry),
) -> ParseResponse:
    # Content safety check
    try:
        await ensure_prompt_safe(parse_request.prompt.text or "")
    except ContentSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Determine primary LLM provider
    settings = get_settings()
    default_provider = "mock" if settings.USE_MOCK_LLM else settings.DEFAULT_LLM_PROVIDER
    primary_name = parse_request.options.llm_provider or default_provider

    # Attempt full processing first
    try:
        response = await process_parse_request(parse_request, cache, llm_providers, bypass_cache=bypass_cache, model_name=primary_name)

        # Save brief to database
        brief_id = None
        try:
            brief_id = str(uuid.uuid4())
            save_creative_brief(
                brief_id=brief_id,
                user_id=current_user["id"],
                prompt_text=parse_request.prompt.text,
                image_url=parse_request.prompt.image_url,
                video_url=parse_request.prompt.video_url,
                image_data=None,  # From upload endpoint
                video_data=None,
                creative_direction=response.creative_direction,
                scenes=[scene.model_dump() for scene in response.scenes] if response.scenes else None,
                confidence_score=response.metadata.confidence_score if response.metadata else None
            )
            logger.info(f"Saved creative brief {brief_id} for user {current_user['id']}")
        except Exception as db_error:
            logger.error(f"Failed to save brief to database: {db_error}")
            # Don't fail the request if DB save fails, just log it

        # NOTE: Physics scene auto-generation is disabled here
        # Physics scenes should be generated separately via the /api/physics/generate endpoint
        # This keeps the creative brief generation focused on prompt parsing and brief creation
        # The generation_prompt in scenes can be used later for physics simulation generation

        # Add brief_id to response
        response.briefId = brief_id
        return response

    except Exception as e:
        logger.warning(f"Full processing failed: {e}, attempting fallback to text-only")

        # Fallback: Create text-only request if media processing failed
        if parse_request.prompt.image_url or parse_request.prompt.video_url or parse_request.prompt.image_base64 or parse_request.prompt.video_base64:
            text_only_request = ParseRequest(
                prompt=PromptInput(
                    text=parse_request.prompt.text,
                    # Exclude media fields for fallback
                ),
                options=parse_request.options,
                context=parse_request.context
            )

            try:
                logger.info("Attempting text-only processing as fallback")
                response = await process_parse_request(text_only_request, cache, llm_providers, bypass_cache, primary_name)

                # Save fallback brief to database
                brief_id = None
                try:
                    brief_id = str(uuid.uuid4())
                    save_creative_brief(
                        brief_id=brief_id,
                        user_id=current_user["id"],
                        prompt_text=parse_request.prompt.text,
                        # No media URLs for fallback
                        creative_direction=response.creative_direction,
                        scenes=[scene.model_dump() for scene in response.scenes] if response.scenes else None,
                        confidence_score=response.metadata.confidence_score if response.metadata else None
                    )
                    logger.info(f"Saved fallback creative brief {brief_id} for user {current_user['id']}")
                except Exception as db_error:
                    logger.error(f"Failed to save fallback brief to database: {db_error}")

                # Add brief_id to response
                response.briefId = brief_id
                return response

            except Exception as fallback_error:
                logger.error(f"Text-only fallback also failed: {fallback_error}")
                raise HTTPException(
                    status_code=500,
                    detail="Processing failed for both full and text-only modes. Please check your input and try again."
                ) from fallback_error
        else:
            # No media to fall back from, re-raise original error
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") from e


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
