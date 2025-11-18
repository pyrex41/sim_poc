"""
V3 API - Campaign management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
import sqlite3
import logging

from backend.core.database import get_db_connection
from backend.core.client_models import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
)
from backend.core.repositories import CampaignRepository
from backend.core.models import PaginatedResponse
from backend.core.exceptions import NotFoundError, ValidationError, DatabaseError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/campaigns", tags=["campaigns"])


# ============================================================================
# DEPENDENCY: Get current user ID (placeholder for auth)
# ============================================================================

def get_current_user_id() -> int:
    """
    Get current authenticated user ID.
    TODO: Replace with actual authentication.
    """
    return 1  # Default user for now


# ============================================================================
# CAMPAIGN ENDPOINTS
# ============================================================================

@router.post("", response_model=Campaign, status_code=201)
def create_campaign(
    data: CampaignCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Create a new campaign.

    Args:
        data: Campaign creation data
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Created campaign
    """
    try:
        repo = CampaignRepository(conn)
        campaign = repo.create(user_id, data)
        logger.info(f"Created campaign {campaign.id} for user {user_id}")
        return campaign

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[Campaign])
def list_campaigns(
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    client_id: str = Query(None, description="Filter by client ID"),
    status: str = Query(None, pattern="^(active|archived|draft)$", description="Filter by status"),
    search: str = Query(None, description="Search by campaign name")
):
    """
    List campaigns for the current user.

    Args:
        user_id: Current user ID (from auth)
        conn: Database connection
        page: Page number
        page_size: Items per page
        sort_by: Field to sort by
        sort_order: Sort order
        client_id: Optional client filter
        status: Optional status filter
        search: Optional search term

    Returns:
        Paginated list of campaigns
    """
    try:
        repo = CampaignRepository(conn)
        campaigns, total = repo.list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            client_id=client_id,
            status=status,
            search=search
        )

        return PaginatedResponse.create(
            items=campaigns,
            total=total,
            page=page,
            page_size=page_size
        )

    except DatabaseError as e:
        logger.error(f"Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=Campaign)
def get_campaign(
    campaign_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Get a campaign by ID.

    Args:
        campaign_id: Campaign ID
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Campaign data
    """
    try:
        repo = CampaignRepository(conn)
        return repo.get_by_id(campaign_id, user_id)

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{campaign_id}", response_model=Campaign)
def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Update a campaign.

    Args:
        campaign_id: Campaign ID
        data: Update data
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Updated campaign
    """
    try:
        repo = CampaignRepository(conn)
        campaign = repo.update(campaign_id, user_id, data)
        logger.info(f"Updated campaign {campaign_id}")
        return campaign

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to update campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Delete a campaign.

    Args:
        campaign_id: Campaign ID
        user_id: Current user ID (from auth)
        conn: Database connection
    """
    try:
        repo = CampaignRepository(conn)
        repo.delete(campaign_id, user_id)
        logger.info(f"Deleted campaign {campaign_id}")

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to delete campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
