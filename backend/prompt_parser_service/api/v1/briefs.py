"""Brief management endpoints."""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.dependencies import get_cache_manager, get_llm_provider_registry
from ...services.cache import CacheManager
from ...services.llm.base import LLMProvider
from ....database import get_user_briefs, get_creative_brief, update_brief, get_brief_count, delete_brief
from ....auth import verify_auth

router = APIRouter()


class BriefRefinementRequest(BaseModel):
    """Request model for brief refinement."""
    text: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    creative_direction: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Dict[str, Any]]] = None


class BriefsResponse(BaseModel):
    """Response model for briefs list."""
    briefs: List[Dict[str, Any]]
    totalPages: int


@router.get("/briefs", response_model=BriefsResponse)
async def get_user_creative_briefs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(verify_auth),
) -> BriefsResponse:
    """
    Get paginated list of user's creative briefs.
    Requires authentication.
    """
    try:
        print(f"DEBUG: Getting briefs for user {current_user['id']}, page {page}, limit {limit}")
        offset = (page - 1) * limit
        briefs = get_user_briefs(current_user["id"], limit=limit, offset=offset)
        total_count = get_brief_count(current_user["id"])
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        print(f"DEBUG: Found {len(briefs)} briefs, total pages: {total_pages}")
        return BriefsResponse(briefs=briefs, totalPages=total_pages)
    except Exception as e:
        print(f"DEBUG: Error in get_user_creative_briefs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve briefs: {str(e)}")


@router.get("/briefs/count")
async def get_user_brief_count(
    current_user: Dict[str, Any] = Depends(verify_auth),
) -> Dict[str, int]:
    """
    Get the total count of briefs for the authenticated user.
    Requires authentication.
    """
    try:
        count = get_brief_count(current_user["id"])
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brief count: {str(e)}")


@router.get("/briefs/{brief_id}", response_model=Dict[str, Any])
async def get_creative_brief_by_id(
    brief_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get a specific creative brief by ID.
    Requires authentication and ownership.
    """
    try:
        brief = get_creative_brief(brief_id, current_user["id"])
        if not brief:
            raise HTTPException(status_code=404, detail="Brief not found")
        return brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve brief: {str(e)}")


@router.post("/briefs/{brief_id}/refine", response_model=Dict[str, Any])
async def refine_creative_brief(
    brief_id: str,
    refinement: BriefRefinementRequest,
    current_user: Dict[str, Any] = Depends(verify_auth),
    cache: CacheManager = Depends(get_cache_manager),
    llm_providers: Dict[str, LLMProvider] = Depends(get_llm_provider_registry),
) -> Dict[str, Any]:
    """
    Refine an existing creative brief with additional input.
    Requires authentication and ownership.
    """
    try:
        # First check if brief exists and belongs to user
        existing_brief = get_creative_brief(brief_id, current_user["id"])
        if not existing_brief:
            raise HTTPException(status_code=404, detail="Brief not found")

        # Prepare refinement data
        refinement_data = {}
        if refinement.text is not None:
            refinement_data["prompt_text"] = refinement.text
        if refinement.image_url is not None:
            refinement_data["image_url"] = refinement.image_url
        if refinement.video_url is not None:
            refinement_data["video_url"] = refinement.video_url
        if refinement.creative_direction is not None:
            import json
            refinement_data["creative_direction"] = json.dumps(refinement.creative_direction)
        if refinement.scenes is not None:
            import json
            refinement_data["scenes"] = json.dumps(refinement.scenes)

        if not refinement_data:
            raise HTTPException(status_code=400, detail="No refinement data provided")

        # Update the brief
        success = update_brief(brief_id, current_user["id"], **refinement_data)
        if not success:
            raise HTTPException(status_code=404, detail="Brief not found or update failed")

        # Invalidate cache for this brief
        cache_key = f"brief_{brief_id}"
        await cache.delete(cache_key)

        # Return updated brief
        updated_brief = get_creative_brief(brief_id, current_user["id"])
        if not updated_brief:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated brief")

        return updated_brief

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refine brief: {str(e)}")


@router.delete("/briefs/{brief_id}")
async def delete_creative_brief(
    brief_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth),
    cache: CacheManager = Depends(get_cache_manager),
) -> Dict[str, bool]:
    """
    Delete a creative brief.
    Requires authentication and ownership.
    """
    try:
        # Delete the brief
        success = delete_brief(brief_id, current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Brief not found or already deleted")

        # Invalidate cache for this brief
        cache_key = f"brief_{brief_id}"
        await cache.delete(cache_key)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete brief: {str(e)}")