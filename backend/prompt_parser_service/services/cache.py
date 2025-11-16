"""Redis cache manager for prompt parser."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from copy import deepcopy
from typing import Any, Optional

import sqlite3
import structlog

from backend.prompt_parser_service.core.metrics import CACHE_HITS, CACHE_MISSES


logger = structlog.get_logger(__name__)


class CacheManager:
    """SQLite-based cache manager."""

    def __init__(self, db_path: str = "./cache.db", default_ttl: int = 1800) -> None:
        self.default_ttl = default_ttl
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database and create cache table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)")
            conn.commit()

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get value from cache."""
        CACHE_MISSES.inc()  # Will be corrected if hit

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                if row:
                    value_str, expires_at = row
                    if expires_at > time.time():
                        CACHE_HITS.inc()
                        CACHE_MISSES.dec()
                        return json.loads(value_str)
                    else:
                        # Expired, clean up
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                        conn.commit()
                return None

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def set(self, key: str, value: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        serialized = json.dumps(value)

        def _set():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, serialized, expires_at)
                )
                conn.commit()
                return True

        return await asyncio.get_event_loop().run_in_executor(None, _set)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""

        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def clear_expired(self) -> int:
        """Clear expired entries."""

        def _clear():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
                conn.commit()
                return cursor.rowcount

        return await asyncio.get_event_loop().run_in_executor(None, _clear)


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
