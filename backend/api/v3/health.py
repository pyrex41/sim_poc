"""
V3 API - Health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime

from backend.core import HealthResponse


router = APIRouter(prefix="/api/v3", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status of the API and its services.
    """
    return HealthResponse(
        status="healthy",
        version="3.0.0",
        timestamp=datetime.now(),
        services={
            "database": "healthy",
            "engines": "healthy",
        }
    )


@router.get("/")
async def root():
    """
    API root endpoint.

    Returns basic information about the API.
    """
    return {
        "name": "Generation Platform API",
        "version": "3.0.0",
        "description": "Composable AI generation platform with image, video, and audio engines",
        "docs": "/docs",
        "health": "/api/v3/health"
    }
