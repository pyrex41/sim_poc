"""Request models."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class PromptInput(BaseModel):
    text: str | None = Field(None, max_length=5000)
    image_url: str | None = None
    image_base64: str | None = None
    video_url: str | None = None
    video_base64: str | None = None

    @model_validator(mode="after")
    def validate_input(cls, values):
        if not any(
            [
                values.text,
                values.image_url,
                values.image_base64,
                values.video_url,
                values.video_base64,
            ]
        ):
            raise ValueError("At least one of text, image, or video input must be provided.")
        return values


class ParseOptions(BaseModel):
    llm_provider: str | None = None
    include_cost_estimate: bool = False
    cost_fallback_enabled: bool = True


class ParseContext(BaseModel):
    previous_config: Optional[dict[str, Any]] = None


class ParseRequest(BaseModel):
    prompt: PromptInput
    options: ParseOptions = ParseOptions()
    cost_estimate: Optional[dict[str, Any]] = None
    context: Optional[ParseContext] = None
