"""Redis cache manager for prompt parser."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from copy import deepcopy
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.core.metrics import CACHE_HITS, CACHE_MISSES


logger = structlog.get_logger(__name__)


class CacheManager:
    """Thin async cache wrapper with Redis or in-memory fallback."""

    def __init__(self, redis_url: str, default_ttl: int = 1800) -> None:
        self.default_ttl = default_ttl
        self._use_memory = redis_url.startswith("memory://")
        if self._use_memory:
            self.redis = None
            self._memory_cache: dict[str, tuple[float, dict[str, Any]]] = {}
            self._memory_lock = asyncio.Lock()
        else:
            self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def _memory_get(self, key: str) -> Optional[dict[str, Any]]:
        async with self._memory_lock:
            entry = self._memory_cache.get(key)
            if not entry:
                return None
            expires_at, payload = entry
            if expires_at < time.time():
                self._memory_cache.pop(key, None)
                return None
            return deepcopy(payload)

    async def _memory_set(self, key: str, value: dict[str, Any], ttl: int) -> bool:
        async with self._memory_lock:
            self._memory_cache[key] = (time.time() + ttl, deepcopy(value))
        return True

    async def _memory_delete(self, key: str) -> bool:
        async with self._memory_lock:
            return self._memory_cache.pop(key, None) is not None

    async def _memory_clear_all(self, pattern: str) -> int:
        cleared = 0
        async with self._memory_lock:
            for key in list(self._memory_cache.keys()):
                if key.startswith(pattern.rstrip("*")):
                    self._memory_cache.pop(key, None)
                    cleared += 1
        return cleared

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        """Return cached value if present."""
        try:
            if self._use_memory:
                cached = await self._memory_get(key)
            else:
                cached_str = await self.redis.get(key)
                cached = json.loads(cached_str) if cached_str is not None else None
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_get", key=key, error=str(exc))
            return None

        if cached is None:
            CACHE_MISSES.inc()
            logger.info("cache.miss", key=key)
            return None

        CACHE_HITS.inc()
        logger.info("cache.hit", key=key)
        return cached

    async def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> bool:
        """Store value with TTL."""
        ttl = ttl or self.default_ttl
        try:
            if self._use_memory:
                await self._memory_set(key, value, ttl)
            else:
                payload = json.dumps(value)
                await self.redis.setex(key, ttl, payload)
            logger.info("cache.set", key=key, ttl=ttl)
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_set", key=key, error=str(exc))
            return False

    async def delete(self, key: str) -> bool:
        """Delete specific cache entry."""
        try:
            if self._use_memory:
                deleted = await self._memory_delete(key)
            else:
                deleted = await self.redis.delete(key)
            logger.info("cache.delete", key=key, deleted=deleted)
            return bool(deleted)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_delete", key=key, error=str(exc))
            return False

    async def clear_all(self, pattern: str = "prompt_parse:*") -> int:
        """Clear keys matching pattern."""
        try:
            if self._use_memory:
                cleared = await self._memory_clear_all(pattern)
            else:
                cleared = 0
                async for key in self.redis.scan_iter(match=pattern):
                    await self.redis.delete(key)
                    cleared += 1
            logger.info("cache.clear_all", pattern=pattern, cleared=cleared)
            return cleared
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_clear_all", pattern=pattern, error=str(exc))
            return 0


def generate_cache_key(request_payload: dict[str, Any]) -> str:
    """Create deterministic cache key from request."""
    prompt = request_payload.get("prompt", {})
    options = request_payload.get("options", {})
    cacheable = {
        "text": prompt.get("text"),
        "image_url": prompt.get("image_url"),
        "video_url": prompt.get("video_url"),
        "target_category": options.get("target_category"),
        "llm_provider": options.get("llm_provider", "openai"),
    }
    cacheable = {k: v for k, v in cacheable.items() if v is not None}
    normalized = json.dumps(cacheable, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"prompt_parse:v1:{digest}"
