"""Redis cache manager for prompt parser."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import redis.asyncio as redis
import structlog


logger = structlog.get_logger(__name__)


class CacheManager:
    """Thin async Redis wrapper."""

    def __init__(self, redis_url: str, default_ttl: int = 1800) -> None:
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        """Return cached value if present."""
        try:
            cached = await self.redis.get(key)
            if cached is None:
                logger.info("cache.miss", key=key)
                return None
            logger.info("cache.hit", key=key)
            return json.loads(cached)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_get", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> bool:
        """Store value with TTL."""
        payload = json.dumps(value)
        ttl = ttl or self.default_ttl
        try:
            await self.redis.setex(key, ttl, payload)
            logger.info("cache.set", key=key, ttl=ttl)
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_set", key=key, error=str(exc))
            return False

    async def delete(self, key: str) -> bool:
        """Delete specific cache entry."""
        try:
            deleted = await self.redis.delete(key)
            logger.info("cache.delete", key=key, deleted=deleted)
            return bool(deleted)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_delete", key=key, error=str(exc))
            return False

    async def clear_all(self, pattern: str = "prompt_parse:*") -> int:
        """Clear keys matching pattern."""
        cleared = 0
        try:
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                cleared += 1
            logger.info("cache.clear_all", pattern=pattern, cleared=cleared)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache.error_clear_all", pattern=pattern, error=str(exc))
        return cleared


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
