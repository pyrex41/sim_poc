"""LLM provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMProvider(ABC):
    """Base interface for LLM providers."""

    name: str

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Generate a completion for the given prompt."""

    @abstractmethod
    async def analyze_image(self, image_b64: str, question: str) -> dict[str, Any]:
        """Analyze an image along with textual instructions."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Return current availability."""

    @abstractmethod
    def get_estimated_latency(self) -> int:
        """Return estimated latency in milliseconds."""
