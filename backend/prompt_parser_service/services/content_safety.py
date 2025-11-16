"""Prompt content safety checks."""

from __future__ import annotations

import structlog
from openai import AsyncOpenAI

from backend.prompt_parser_service.core.config import get_settings

logger = structlog.get_logger(__name__)


class ContentSafetyError(Exception):
    """Raised when prompt violates content policy."""


async def ensure_prompt_safe(prompt_text: str) -> None:
    settings = get_settings()
    if not settings.OPENAI_API_KEY or not prompt_text:
        return

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = await client.moderations.create(
            model="omni-moderation-latest",
            input=prompt_text,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("content_safety.moderation_failed", error=str(exc))
        return

    result = response.results[0]
    if result.flagged:
        raise ContentSafetyError("Prompt violates content policy.")

