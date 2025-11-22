"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = Field(8080, ge=1, le=65535)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE: int = Field(60, ge=1)
    USE_MOCK_LLM: bool = False

    # LangSmith observability settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "video-sim-poc"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("RATE_LIMIT_PER_MINUTE", mode="before")
    @classmethod
    def _clean_rate_limit(cls, value: int | str | None) -> int | None:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return int(value) if value is not None else None

    @field_validator("USE_MOCK_LLM", mode="before")
    @classmethod
    def _clean_use_mock(cls, value: bool | str | None) -> bool | None:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
