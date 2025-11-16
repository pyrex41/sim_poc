"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.prompt_parser_service.core.dependencies import get_cache_manager, get_llm_provider_registry
from backend.prompt_parser_service.services.cache import CacheManager
from backend.prompt_parser_service.services.llm.base import LLMProvider

router = APIRouter()


@router.get("/health")
async def health(
    cache: CacheManager = Depends(get_cache_manager),
    llm_providers: dict[str, LLMProvider] = Depends(get_llm_provider_registry),
) -> dict[str, str | bool]:
    redis_ok = True
    try:
        await cache.redis.ping()
    except Exception:  # pragma: no cover
        redis_ok = False

    provider_ok = any([await provider.is_available() for provider in llm_providers.values()])
    status = "healthy" if redis_ok and provider_ok else "degraded"

    return {
        "status": status,
        "redis": redis_ok,
        "llm_available": provider_ok,
    }
