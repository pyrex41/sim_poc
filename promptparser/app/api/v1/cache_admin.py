"""Cache admin endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.services.cache import CacheManager
from app.core.dependencies import get_cache_manager

router = APIRouter()


@router.post("/cache/clear")
async def clear_cache(cache: CacheManager = Depends(get_cache_manager)):
    cleared = await cache.clear_all()
    return {"status": "success", "cleared": cleared}

