import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from tests.test_parse_endpoint import FakeCache, FakeLLM

transport = ASGITransport(app=app)


@pytest.fixture(autouse=True)
def clear_overrides(monkeypatch):
    app.dependency_overrides = {}
    limiter = app.state.limiter
    limiter.enabled = False

    yield
    limiter.enabled = True


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_providers_endpoint_lists_providers():
    fake_llm = FakeLLM()
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/providers")

    assert resp.status_code == 200
    assert resp.json()["providers"][0]["id"] == "openai"


@pytest.mark.anyio
async def test_cache_clear_endpoint():
    fake_cache = FakeCache()
    fake_cache.store["key"] = "{}"
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/cache/clear")

    assert resp.status_code == 200
    assert resp.json()["cleared"] >= 0


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_data():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert "python_gc_objects_collected_total" in resp.text

