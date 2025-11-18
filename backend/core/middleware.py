"""
Middleware for cross-cutting concerns: logging, error handling, CORS, etc.
"""
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import PlatformException
from .models import ErrorResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[ID: {request_id}]"
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[ID: {request_id}] - {str(e)}",
                exc_info=True
            )
            raise
        finally:
            # Log response
            duration = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[ID: {request_id}] - Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling platform exceptions uniformly."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except PlatformException as e:
            # Handle our custom exceptions
            request_id = getattr(request.state, "request_id", None)
            error_response = ErrorResponse(
                error=e.__class__.__name__,
                message=e.message,
                details=e.details,
                request_id=request_id
            )

            logger.warning(
                f"Platform exception: {e.__class__.__name__} - {e.message} "
                f"[Request ID: {request_id}]"
            )

            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
        except Exception as e:
            # Handle unexpected exceptions
            request_id = getattr(request.state, "request_id", None)
            error_response = ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                details={"original_error": str(e)},
                request_id=request_id
            )

            logger.error(
                f"Unexpected exception: {str(e)} [Request ID: {request_id}]",
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump()
            )


def configure_cors(app) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Deprecation-Warning"]
    )


def configure_trusted_hosts(app, allowed_hosts: list[str] = None) -> None:
    """Configure trusted host middleware."""
    if allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )


def configure_middleware(app, allowed_hosts: list[str] = None) -> None:
    """Configure all middleware for the application."""
    # Order matters: last added = first executed

    # Exception handling (should be outermost)
    app.add_middleware(ExceptionHandlerMiddleware)

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # CORS
    configure_cors(app)

    # Trusted hosts (if configured)
    if allowed_hosts:
        configure_trusted_hosts(app, allowed_hosts)

    logger.info("Middleware configured successfully")
