"""Prompt Parser API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from .core.config import Settings, get_settings
from .core.logging import configure_logging
from .core.limiter import limiter
from api.v1 import parse as parse_api
from api.v1 import health as health_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize global services."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Prompt Parser API",
        version="0.1.0",
        description="Transforms prompts into structured creative direction",
        lifespan=lifespan,
    )

    from api.v1 import batch as batch_api
    from api.v1 import metrics as metrics_api
    from api.v1 import providers as providers_api
    from api.v1 import cache_admin as cache_admin_api

    from fastapi.responses import JSONResponse

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        return JSONResponse({"detail": "Too many requests"}, status_code=429)

    app.state.limiter = limiter

    app.include_router(parse_api.router, prefix="/v1", tags=["parse"])
    app.include_router(batch_api.router, prefix="/v1", tags=["batch"])
    app.include_router(metrics_api.router, tags=["metrics"])
    app.include_router(providers_api.router, prefix="/v1", tags=["providers"])
    app.include_router(cache_admin_api.router, prefix="/v1", tags=["cache"])
    app.include_router(health_api.router, prefix="/v1", tags=["health"])

    return app


app = create_app()
