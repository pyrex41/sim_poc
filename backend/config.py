"""Centralized configuration management for the entire backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Main backend settings
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    HOST: str = "0.0.0.0"
    PORT: int = Field(8000, ge=1, le=65535)
    BASE_URL: str = "http://localhost:8000"  # Set to ngrok URL for local dev, or deployed URL for production

    # AI/ML settings
    REPLICATE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # Storage settings
    VIDEO_STORAGE_PATH: str = "./DATA/videos"

    # Prompt parser settings (from prompt_parser_service)
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    REDIS_URL: str = "redis://localhost:6379/0"  # Will use SQLite instead
    RATE_LIMIT_PER_MINUTE: int = Field(10, ge=1)  # Aligned to PRD
    USE_MOCK_LLM: bool = False
    DEFAULT_LLM_PROVIDER: str = Field("openai", description="Default LLM provider (e.g., openai for GPT-4o, claude)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow extra env vars
    )

    @field_validator("RATE_LIMIT_PER_MINUTE", mode="before")
    @classmethod
    def _clean_rate_limit(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return int(value) if value is not None else None

    @field_validator("USE_MOCK_LLM", mode="before")
    @classmethod
    def _clean_use_mock(cls, value):
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