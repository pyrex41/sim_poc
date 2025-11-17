"""Cache admin endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ...services.cache import CacheManager
from ...core.dependencies import get_cache_manager

router = APIRouter()


@router.post("/cache/clear")
async def clear_cache(cache: CacheManager = Depends(get_cache_manager)):
    cleared = await cache.clear_all()
    return {"status": "success", "cleared": cleared}

