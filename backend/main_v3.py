"""
Generation Platform v3 - Main Application

Clean, modular FastAPI application with composable generation engines.
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core import configure_middleware
from backend.api.v3 import generation_router, health_router, clients_router, campaigns_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Create app
    app = FastAPI(
        title="Generation Platform API",
        description="Composable AI generation platform with image, video, and audio engines",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure middleware
    configure_middleware(app)

    # Register routers
    app.include_router(health_router)
    app.include_router(generation_router)
    app.include_router(clients_router)
    app.include_router(campaigns_router)

    # Mount static files
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

    logger.info("=" * 60)
    logger.info("Generation Platform v3 initialized")
    logger.info("=" * 60)
    logger.info("Available endpoints:")
    logger.info("  GET  /                        - API info")
    logger.info("  GET  /api/v3/health           - Health check")
    logger.info("  POST /api/v3/generate/image   - Generate image")
    logger.info("  GET  /api/v3/tasks/{id}       - Get task status")
    logger.info("  GET  /api/v3/tasks/{id}/result - Get task result")
    logger.info("  POST /api/v3/tasks/{id}/cancel - Cancel task")
    logger.info("")
    logger.info("Client & Campaign Management:")
    logger.info("  GET    /api/v3/clients              - List clients")
    logger.info("  POST   /api/v3/clients              - Create client")
    logger.info("  GET    /api/v3/clients/{id}         - Get client")
    logger.info("  PATCH  /api/v3/clients/{id}         - Update client")
    logger.info("  DELETE /api/v3/clients/{id}         - Delete client")
    logger.info("  GET    /api/v3/campaigns            - List campaigns")
    logger.info("  POST   /api/v3/campaigns            - Create campaign")
    logger.info("  GET    /api/v3/campaigns/{id}       - Get campaign")
    logger.info("  PATCH  /api/v3/campaigns/{id}       - Update campaign")
    logger.info("  DELETE /api/v3/campaigns/{id}       - Delete campaign")
    logger.info("")
    logger.info("Web Interface:")
    logger.info("  http://localhost:8000/app/clients-campaigns.html")
    logger.info("=" * 60)

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main_v3:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
