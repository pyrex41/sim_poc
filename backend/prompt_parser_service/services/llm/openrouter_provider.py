"""OpenRouter provider implementation."""

from __future__ import annotations

import json
from typing import Any, Optional

from openai import AsyncOpenAI
import structlog

from ...core.config import get_settings
from .base import LLMProvider

logger = structlog.get_logger(__name__)


class OpenRouterProvider(LLMProvider):
    """Wrapper around OpenRouter API endpoints."""

    def __init__(self, model: str = "openai/gpt-5-nano-2025-08-07", *, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        api_key = settings.OPENROUTER_API_KEY
        if client is None and not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for OpenRouterProvider")

        # OpenRouter uses OpenAI-compatible API
        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self._available = True
        self._latency_ms = 2000  # OpenRouter is typically fast

    async def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }
            if response_format:
                params["response_format"] = response_format

            response = await self.client.chat.completions.create(**params)
            self._available = True
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover - network errors mocked in tests
            self._available = False
            logger.warning("openrouter.complete_failed", error=str(exc), model=self.model)
            raise

    async def analyze_image(self, image_b64: str, question: str) -> dict[str, Any]:
        try:
            if not image_b64.startswith("data:"):
                image_b64 = f"data:image/jpeg;base64,{image_b64}"
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": image_b64}},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
            )
            self._available = True
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as exc:  # pragma: no cover
            self._available = False
            logger.warning("openrouter.analyze_image_failed", error=str(exc), model=self.model)
            raise

    async def is_available(self) -> bool:
        return self._available

    def get_estimated_latency(self) -> int:
        return self._latency_ms
