import json
import base64
import io
from typing import Any

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from app.services.input_orchestrator import InputAnalysis
from app.main import app


class FakeCache:
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

    async def clear_all(self):
        cleared = len(self.store)
        self.store.clear()
        return cleared


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, *args, **kwargs):
        self.calls += 1
        return json.dumps(
            {
                "product": {"name": "Sneakers"},
                "technical_specs": {"duration": 30},
            }
        )

    async def is_available(self) -> bool:
        return True

    def get_estimated_latency(self) -> int:
        return 1000


class FailLLM(FakeLLM):
    async def complete(self, *args, **kwargs):
        raise RuntimeError("LLM failure")


def _small_png_base64(color) -> str:
    image = Image.new("RGB", (2, 2), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


SAMPLE_IMAGE_B64 = _small_png_base64((0, 255, 0))


transport = ASGITransport(app=app)


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides = {}
    limiter = app.state.limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def patch_content_safety(monkeypatch):
    from app.api.v1 import parse as parse_module

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(parse_module, "ensure_prompt_safe", noop)


@pytest.mark.anyio
async def test_parse_endpoint_returns_structured_response():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={"prompt": {"text": "30 second instagram ad for sneakers"}},
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["creative_direction"]["technical_specs"]["duration"] == 30
    assert len(data["scenes"]) >= 3
    assert data["metadata"]["cache_hit"] is False
    assert fake_llm.calls == 1


@pytest.mark.anyio
async def test_parse_endpoint_uses_cache():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/v1/parse", json={"prompt": {"text": "ad for coffee"}})
        second = await client.post("/v1/parse", json={"prompt": {"text": "ad for coffee"}})

    assert fake_llm.calls == 1
    assert second.json()["metadata"]["cache_hit"] is True


@pytest.mark.anyio
async def test_parse_endpoint_passes_through_cost_estimate():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    cost_payload = {"total_usd": 1.5, "breakdown": {"video": 1.2}}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {"text": "Ad for coffee"},
                "cost_estimate": cost_payload,
            },
        )

    assert response.json()["cost_estimate"] == cost_payload


@pytest.mark.anyio
async def test_parse_endpoint_fallback_cost_estimate():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {"text": "estimate cost"},
                "options": {"include_cost_estimate": True},
            },
        )

    data = response.json()
    assert data["cost_estimate"]["total_usd"] > 0


@pytest.mark.anyio
async def test_parse_endpoint_sets_style_source_from_image():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/parse",
                json={
                    "prompt": {
                        "text": "ad for shoes",
                        "image_base64": SAMPLE_IMAGE_B64,
                    }
                },
            )

    data = response.json()
    assert data["creative_direction"]["visual_direction"]["style_source"] == "image"
    assert data["extracted_references"]["images"][0]["reference"] == "inline_base64_image"


@pytest.mark.anyio
async def test_parse_endpoint_prioritizes_video_over_image(monkeypatch):
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async def fake_analyze(prompt):
        return InputAnalysis(
            style_source="video",
            reference_summary={"primary_reference": "video_ref"},
            extracted_references={"videos": [{"reference": "video_ref"}]},
        )

    import app.api.v1.parse as parse_module

    monkeypatch.setattr(parse_module, "analyze_inputs", fake_analyze)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {
                    "video_url": "https://example.com/video.mp4",
                    "image_base64": SAMPLE_IMAGE_B64,
                    "text": "video ref",
                }
            },
        )

    data = response.json()
    assert data["creative_direction"]["visual_direction"]["style_source"] == "video"
    assert "videos" in data["extracted_references"]


@pytest.mark.anyio
async def test_parse_endpoint_falls_back_to_claude_on_failure():
    fake_cache = FakeCache()
    failing = FailLLM()
    fallback = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {
        "openai": failing,
        "claude": fallback,
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/parse", json={"prompt": {"text": "ad for fallback"}})

    data = response.json()
    assert data["metadata"]["llm_provider_used"] == "claude"


@pytest.mark.anyio
async def test_health_endpoint():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
