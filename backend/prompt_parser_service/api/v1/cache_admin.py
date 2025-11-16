"""Cache admin endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.prompt_parser_service.services.cache import CacheManager
from backend.prompt_parser_service.core.dependencies import get_cache_manager

router = APIRouter()


@router.post("/cache/clear")
async def clear_cache(cache: CacheManager = Depends(get_cache_manager)):
    cleared = await cache.clear_all()
    return {"status": "success", "cleared": cleared}

