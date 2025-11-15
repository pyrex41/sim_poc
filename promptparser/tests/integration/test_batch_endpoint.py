import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_cache_manager, get_llm_provider_registry
from app.main import app
from tests.test_parse_endpoint import FakeCache, FakeLLM

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
async def test_batch_endpoint_processes_multiple_requests():
    fake_cache = FakeCache()
    fake_llm = FakeLLM()
    app.dependency_overrides[get_cache_manager] = lambda: fake_cache
    app.dependency_overrides[get_llm_provider_registry] = lambda: {"openai": fake_llm}

    payload = [
        {"prompt": {"text": "Ad for batch 1"}},
        {"prompt": {"text": "Ad for batch 2"}},
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/parse/batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["results"]) == 2

