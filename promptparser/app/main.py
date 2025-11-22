"""Prompt Parser API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from langsmith import traceable

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.limiter import limiter
from app.api.v1 import parse as parse_api
from app.api.v1 import health as health_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize global services."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    yield


class LangSmithMiddleware(BaseHTTPMiddleware):
    """Middleware to trace HTTP requests with LangSmith"""

    async def dispatch(self, request: Request, call_next):
        # Get settings to check if tracing is enabled
        settings = get_settings()

        # Skip tracing if disabled or for health checks/docs
        if not settings.LANGCHAIN_TRACING_V2 or request.url.path in ["/v1/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Create traced function for the request
        @traceable(
            name=f"{request.method} {request.url.path}",
            tags=["http_request", "prompt_parser", request.method.lower()],
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
            }
        )
        async def process_request():
            response = await call_next(request)
            return response

        return await process_request()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Prompt Parser API",
        version="0.1.0",
        description="Transforms prompts into structured creative direction",
        lifespan=lifespan,
    )

    from app.api.v1 import batch as batch_api
    from app.api.v1 import metrics as metrics_api
    from app.api.v1 import providers as providers_api
    from app.api.v1 import cache_admin as cache_admin_api

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

    # Add LangSmith tracing middleware
    app.add_middleware(LangSmithMiddleware)

    return app


app = create_app()
