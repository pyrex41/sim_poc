import json
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from app.main import app


class StubCache:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.redis = self

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: dict, ttl: int | None = None):
        self.store[key] = value
        return True

    async def ping(self):
        return True


class StubLLM:
    def __init__(self) -> None:
        self.calls = []

    async def complete(self, prompt: str, **kwargs):
        self.calls.append(prompt)
        return json.dumps(
            {
                "product": {"name": "Integration Product"},
                "technical_specs": {"duration": 24},
            }
        )

    async def is_available(self) -> bool:
        return True


transport = ASGITransport(app=app)


@pytest.fixture(autouse=True)
def clear_overrides(monkeypatch):
    app.dependency_overrides = {}
    limiter = app.state.limiter
    limiter.enabled = False

    from app.api.v1 import parse as parse_module

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(parse_module, "ensure_prompt_safe", noop)
    yield
    limiter.enabled = True


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_full_flow_handles_multiple_prompts():
    cache = StubCache()
    llm = StubLLM()
    app.dependency_overrides[get_cache_manager] = lambda: cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": llm}

    prompts = [
        {"prompt": {"text": "15 second TikTok ad for coffee"}},
        {"prompt": {"image_url": "https://example.com/img.jpg", "text": "match this style"}},
        {"prompt": {"video_url": "https://example.com/vid.mp4"}},
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = []
        for payload in prompts:
            resp = await client.post("/v1/parse", json=payload)
            responses.append(resp)

    assert all(resp.status_code == 200 for resp in responses)
    assert len(llm.calls) == 3

    first = responses[0].json()
    assert first["creative_direction"]["technical_specs"]["duration"] == 24
    assert first["metadata"]["cache_hit"] is False

    # Ensure cache reused on repeated prompt
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cached = await client.post("/v1/parse", json=prompts[0])
    assert cached.json()["metadata"]["cache_hit"] is True

