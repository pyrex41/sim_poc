"""Rate limiter instance."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.prompt_parser_service.core.config import get_settings

settings = get_settings()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)

