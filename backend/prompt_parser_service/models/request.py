"""Request models."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator, field_validator
import re
import base64
from urllib.parse import urlparse


class PromptInput(BaseModel):
    text: str | None = Field(None, max_length=5000)
    image_url: str | None = None
    image_base64: str | None = None
    video_url: str | None = None
    video_base64: str | None = None

    @field_validator('image_url', 'video_url', mode='before')
    @classmethod
    def validate_and_sanitize_url(cls, v):
        if v is None:
            return v

        # Convert to string and strip whitespace
        v = str(v).strip()

        if not v:
            return None

        # Basic URL validation
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")

        # Only allow http and https
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("Only HTTP and HTTPS URLs are allowed")

        # Basic security checks - block localhost/private IPs
        hostname = parsed.hostname
        if hostname and isinstance(hostname, str):
            hostname = hostname.lower()
            if hostname in ['localhost', '127.0.0.1', '::1'] or hostname.startswith('192.168.') or hostname.startswith('10.') or hostname.startswith('172.'):
                raise ValueError("Local/private network URLs are not allowed")

        # Check for potentially malicious patterns
        suspicious_patterns = [
            r'<script', r'javascript:', r'data:', r'vbscript:',
            r'on\w+\s*=', r'&#', r'%3C', r'%3E'
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potentially malicious URL detected")

        return v

    @field_validator('image_base64', 'video_base64', mode='before')
    @classmethod
    def validate_base64_data(cls, v):
        if v is None:
            return v

        # Convert to string and strip whitespace
        v = str(v).strip()

        if not v:
            return None

        # Basic base64 validation
        try:
            # Remove data URL prefix if present
            if v.startswith('data:'):
                v = v.split(',', 1)[1] if ',' in v else v

            # Validate base64 format
            base64.b64decode(v, validate=True)

            # Basic security check - reject if too large (prevent DoS)
            if len(v) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("Base64 data too large")

        except Exception:
            raise ValueError("Invalid base64 data")

        return v

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
