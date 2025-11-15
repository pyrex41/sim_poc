import asyncio
import json
from typing import Any, AsyncIterator

import pytest

from app.services.cache import CacheManager, generate_cache_key


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:  # noqa: ARG002
        self.store[key] = value

    async def delete(self, key: str) -> int:
        return int(self.store.pop(key, None) is not None)

    async def scan_iter(self, match: str = "*") -> AsyncIterator[str]:
        for key in list(self.store.keys()):
            if key.startswith(match.rstrip("*")):
                yield key


@pytest.mark.asyncio
async def test_cache_manager_get_set_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager("redis://localhost:6379/0")
    dummy = DummyRedis()
    monkeypatch.setattr(cache, "redis", dummy)

    key = "prompt_parse:v1:test"
    payload = {"status": "success"}

    assert await cache.get(key) is None

    await cache.set(key, payload, ttl=5)
    assert json.loads(dummy.store[key]) == payload

    cached = await cache.get(key)
    assert cached == payload

    assert await cache.delete(key) is True
    assert await cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_manager_clear_all(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager("redis://localhost:6379/0")
    dummy = DummyRedis()
    monkeypatch.setattr(cache, "redis", dummy)

    await cache.set("prompt_parse:v1:one", {"a": 1})
    await cache.set("prompt_parse:v1:two", {"b": 2})
    await cache.set("other:key", {"skip": True})

    cleared = await cache.clear_all()
    assert cleared == 2
    assert "other:key" in dummy.store


def test_generate_cache_key_deterministic() -> None:
    request = {
        "prompt": {"text": "luxury watch ad"},
        "options": {"llm_provider": "openai"},
    }
    key1 = generate_cache_key(request)
    key2 = generate_cache_key(request)

    assert key1 == key2
    assert key1.startswith("prompt_parse:v1:")


def test_generate_cache_key_changes_with_input() -> None:
    req_a = {"prompt": {"text": "watch ad"}}
    req_b = {"prompt": {"text": "shoe ad"}}

    assert generate_cache_key(req_a) != generate_cache_key(req_b)
