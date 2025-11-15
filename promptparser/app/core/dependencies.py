"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.cache import CacheManager
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.mock_provider import MockProvider


@lru_cache
def _cache_manager() -> CacheManager:
    settings = get_settings()
    return CacheManager(settings.REDIS_URL)


@lru_cache
def _llm_providers() -> dict[str, LLMProvider]:
    settings = get_settings()
    providers: dict[str, LLMProvider] = {}
    if settings.USE_MOCK_LLM:
        providers["mock"] = MockProvider()
        return providers

    providers["openai"] = OpenAIProvider()
    if settings.ANTHROPIC_API_KEY:
        providers["claude"] = ClaudeProvider()
    return providers


def get_cache_manager() -> CacheManager:
    return _cache_manager()


def get_llm_provider_registry() -> dict[str, LLMProvider]:
    return _llm_providers()
