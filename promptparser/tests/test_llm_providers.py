from types import SimpleNamespace

import pytest

from app.prompts.creative_direction import (
    CREATIVE_DIRECTION_SYSTEM_PROMPT,
    build_creative_direction_prompt,
)
from app.services.llm.openai_provider import OpenAIProvider


class DummyChatCompletions:
    def __init__(self) -> None:
        self.kwargs = None
        self.response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}", parsed=None))]
        )

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


class DummyAsyncOpenAI:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=DummyChatCompletions())


@pytest.mark.asyncio
async def test_openai_provider_complete(monkeypatch):
    provider = OpenAIProvider(client=DummyAsyncOpenAI())
    result = await provider.complete("hello world", system_prompt="system")
    assert result == "{}"

    kwargs = provider.client.chat.completions.kwargs  # type: ignore[attr-defined]
    assert kwargs["model"] == provider.model
    assert kwargs["messages"][0]["content"] == "system"


@pytest.mark.asyncio
async def test_openai_provider_analyze_image_returns_json():
    dummy_client = DummyAsyncOpenAI()
    dummy_client.chat.completions.response.choices[0].message.content = '{"lighting":"soft"}'
    provider = OpenAIProvider(client=dummy_client)

    result = await provider.analyze_image("abc123", "describe")
    assert result == {"lighting": "soft"}


def test_build_creative_direction_prompt_contains_context():
    prompt = build_creative_direction_prompt(
        "make an ad",
        extracted_parameters={"duration": 30},
        applied_defaults={"platform": "instagram"},
    )
    assert "make an ad" in prompt
    assert "duration" in prompt
    assert "instagram" in prompt
    assert CREATIVE_DIRECTION_SYSTEM_PROMPT.startswith("You are an award-winning")
