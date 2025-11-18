"""
V3 API - Client management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
import sqlite3
import logging

from backend.core.database import get_db_connection
from backend.core.client_models import (
    Client,
    ClientCreate,
    ClientUpdate,
    ClientFilter,
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignFilter,
)
from backend.core.repositories import ClientRepository, CampaignRepository
from backend.core.models import PaginatedResponse
from backend.core.exceptions import NotFoundError, ValidationError, DatabaseError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/clients", tags=["clients"])


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
# CLIENT ENDPOINTS
# ============================================================================

@router.post("", response_model=Client, status_code=201)
def create_client(
    data: ClientCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Create a new client.

    Args:
        data: Client creation data
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Created client
    """
    try:
        repo = ClientRepository(conn)
        client = repo.create(user_id, data)
        logger.info(f"Created client {client.id} for user {user_id}")
        return client

    except DatabaseError as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[Client])
def list_clients(
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    search: str = Query(None, description="Search by client name")
):
    """
    List clients for the current user.

    Args:
        user_id: Current user ID (from auth)
        conn: Database connection
        page: Page number
        page_size: Items per page
        sort_by: Field to sort by
        sort_order: Sort order
        search: Optional search term

    Returns:
        Paginated list of clients
    """
    try:
        repo = ClientRepository(conn)
        clients, total = repo.list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search
        )

        return PaginatedResponse.create(
            items=clients,
            total=total,
            page=page,
            page_size=page_size
        )

    except DatabaseError as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}", response_model=Client)
def get_client(
    client_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Get a client by ID.

    Args:
        client_id: Client ID
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Client data
    """
    try:
        repo = ClientRepository(conn)
        return repo.get_by_id(client_id, user_id)

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to get client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{client_id}", response_model=Client)
def update_client(
    client_id: str,
    data: ClientUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Update a client.

    Args:
        client_id: Client ID
        data: Update data
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Updated client
    """
    try:
        repo = ClientRepository(conn)
        client = repo.update(client_id, user_id, data)
        logger.info(f"Updated client {client_id}")
        return client

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to update client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Delete a client.

    Args:
        client_id: Client ID
        user_id: Current user ID (from auth)
        conn: Database connection
    """
    try:
        repo = ClientRepository(conn)
        repo.delete(client_id, user_id)
        logger.info(f"Deleted client {client_id}")

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to delete client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CAMPAIGN ENDPOINTS (nested under clients)
# ============================================================================

@router.post("/{client_id}/campaigns", response_model=Campaign, status_code=201)
def create_campaign(
    client_id: str,
    data: CampaignCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]
):
    """
    Create a new campaign for a client.

    Args:
        client_id: Client ID
        data: Campaign creation data
        user_id: Current user ID (from auth)
        conn: Database connection

    Returns:
        Created campaign
    """
    # Ensure client_id in path matches data
    if data.client_id != client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id in path must match client_id in request body"
        )

    try:
        repo = CampaignRepository(conn)
        campaign = repo.create(user_id, data)
        logger.info(f"Created campaign {campaign.id} for client {client_id}")
        return campaign

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}/campaigns", response_model=PaginatedResponse[Campaign])
def list_client_campaigns(
    client_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    status: str = Query(None, pattern="^(active|archived|draft)$", description="Filter by status"),
    search: str = Query(None, description="Search by campaign name")
):
    """
    List campaigns for a specific client.

    Args:
        client_id: Client ID
        user_id: Current user ID (from auth)
        conn: Database connection
        page: Page number
        page_size: Items per page
        sort_by: Field to sort by
        sort_order: Sort order
        status: Optional status filter
        search: Optional search term

    Returns:
        Paginated list of campaigns
    """
    try:
        # Verify client exists and user has access
        client_repo = ClientRepository(conn)
        client_repo.get_by_id(client_id, user_id)

        # Get campaigns
        campaign_repo = CampaignRepository(conn)
        campaigns, total = campaign_repo.list(
            user_id=user_id,
            client_id=client_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            status=status,
            search=search
        )

        return PaginatedResponse.create(
            items=campaigns,
            total=total,
            page=page,
            page_size=page_size
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Failed to list campaigns for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
