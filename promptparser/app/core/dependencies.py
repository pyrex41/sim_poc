"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.cache import CacheManager
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.claude_provider import ClaudeProvider


@lru_cache
def _cache_manager() -> CacheManager:
    settings = get_settings()
    return CacheManager(settings.REDIS_URL)


@lru_cache
def _llm_providers() -> dict[str, LLMProvider]:
    providers: dict[str, LLMProvider] = {"openai": OpenAIProvider()}
    try:
        providers["claude"] = ClaudeProvider()
    except RuntimeError:
        providers["claude"] = providers["openai"]
    return providers


def get_cache_manager() -> CacheManager:
    return _cache_manager()


def get_llm_provider_registry() -> dict[str, LLMProvider]:
    return _llm_providers()
