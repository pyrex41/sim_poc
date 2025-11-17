"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache

from ...config import get_settings
from ..services.cache import CacheManager
from ..services.llm.base import LLMProvider
from ..services.llm.openai_provider import OpenAIProvider
from ..services.llm.claude_provider import ClaudeProvider
from ..services.llm.openrouter_provider import OpenRouterProvider
from ..services.llm.mock_provider import MockProvider


@lru_cache
def _cache_manager() -> CacheManager:
    # Use SQLite-based cache instead of Redis
    return CacheManager("./cache.db")


@lru_cache
def _llm_providers() -> dict[str, LLMProvider]:
    settings = get_settings()
    providers: dict[str, LLMProvider] = {}
    if settings.USE_MOCK_LLM:
        providers["mock"] = MockProvider()
        return providers

    # Register OpenRouter with GPT-5-nano as the primary provider
    if settings.OPENROUTER_API_KEY:
        providers["openrouter"] = OpenRouterProvider(model="openai/gpt-5-nano-2025-08-07")

    # Fallback providers
    if settings.OPENAI_API_KEY:
        providers["openai"] = OpenAIProvider()
    if settings.ANTHROPIC_API_KEY:
        providers["claude"] = ClaudeProvider()
    return providers


def get_cache_manager() -> CacheManager:
    return _cache_manager()


def get_llm_provider_registry() -> dict[str, LLMProvider]:
    return _llm_providers()
