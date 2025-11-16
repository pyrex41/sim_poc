"""Claude provider implementation."""

from __future__ import annotations

import json
from typing import Any, Optional

from anthropic import AsyncAnthropic
import structlog

from ...core.config import get_settings
from .base import LLMProvider

logger = structlog.get_logger(__name__)


class ClaudeProvider(LLMProvider):
    """Wrapper around Claude Sonnet."""

    def __init__(self, model: str = "claude-3-sonnet-20240229", *, client: AsyncAnthropic | None = None) -> None:
        settings = get_settings()
        api_key = settings.ANTHROPIC_API_KEY
        if client is None and not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for ClaudeProvider")

        self.client = client or AsyncAnthropic(api_key=api_key)
        self.model = model
        self._available = True
        self._latency_ms = 4000

    async def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                system=system_prompt or "You are an expert creative director.",
                max_tokens=4000,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            self._available = True
            content = response.content[0].text if response.content else ""
            return content
        except Exception as exc:  # pragma: no cover
            self._available = False
            logger.warning("claude.complete_failed", error=str(exc))
            raise

    async def analyze_image(self, image_b64: str, question: str) -> dict[str, Any]:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                            {"type": "text", "text": question},
                        ],
                    }
                ],
            )
            self._available = True
            raw = response.content[0].text if response.content else "{}"
            return json.loads(raw)
        except Exception as exc:  # pragma: no cover
            self._available = False
            logger.warning("claude.analyze_image_failed", error=str(exc))
            raise

    async def is_available(self) -> bool:
        return self._available

    def get_estimated_latency(self) -> int:
        return self._latency_ms

