"""
V3 API package.
"""
from .generation import router as generation_router
from .health import router as health_router
from .clients import router as clients_router
from .campaigns import router as campaigns_router

__all__ = [
    "generation_router",
    "health_router",
    "clients_router",
    "campaigns_router",
]
