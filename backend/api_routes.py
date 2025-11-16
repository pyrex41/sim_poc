"""API routes for Clients and Campaigns management.

This module provides RESTful API endpoints for the ad-video-gen frontend:
- /api/clients - Client CRUD operations
- /api/clients/:id/stats - Client statistics
- /api/clients/:id/assets - Client asset management
- /api/campaigns - Campaign CRUD operations
- /api/campaigns/:id/stats - Campaign statistics
- /api/campaigns/:id/assets - Campaign asset management
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime
import os
import uuid

from .auth import verify_auth
from .database_helpers import (
    # Client operations
    create_client,
    get_client_by_id,
    list_clients,
    update_client,
    delete_client,
    get_client_stats,
    create_client_asset,
    list_client_assets,
    delete_client_asset,
    # Campaign operations
    create_campaign,
    get_campaign_by_id,
    list_campaigns,
    update_campaign,
    delete_campaign,
    get_campaign_stats,
    create_campaign_asset,
    list_campaign_assets,
    delete_campaign_asset,
    # Video operations
    list_videos_by_campaign,
    update_video_metrics
)

# Create router
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class BrandGuidelines(BaseModel):
    """Client brand guidelines structure."""
    colors: List[str] = Field(default_factory=list, description="Array of hex colors")
    fonts: List[str] = Field(default_factory=list, description="Array of font names")
    styleKeywords: List[str] = Field(default_factory=list, description="Style descriptors")
    documentUrls: Optional[List[str]] = Field(default=None, description="Brand guideline document URLs")


class CreateClientRequest(BaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=1, max_length=100, description="Client name")
    description: str = Field(default="", max_length=500, description="Client description")
    brandGuidelines: Optional[BrandGuidelines] = Field(default=None, description="Brand guidelines")


class UpdateClientRequest(BaseModel):
    """Request model for updating a client (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    brandGuidelines: Optional[BrandGuidelines] = None


class CampaignBrief(BaseModel):
    """Campaign creative brief structure."""
    objective: str = Field(..., description="Campaign objective")
    targetAudience: str = Field(..., description="Target audience description")
    keyMessages: List[str] = Field(..., description="Key messages array")


class CreateCampaignRequest(BaseModel):
    """Request model for creating a campaign."""
    clientId: str = Field(..., description="Client UUID")
    name: str = Field(..., min_length=1, max_length=100, description="Campaign name")
    goal: str = Field(..., min_length=1, max_length=500, description="Campaign goal")
    status: str = Field(default="draft", pattern="^(active|archived|draft)$", description="Campaign status")
    brief: Optional[CampaignBrief] = Field(default=None, description="Creative brief")


class UpdateCampaignRequest(BaseModel):
    """Request model for updating a campaign (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    goal: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = Field(None, pattern="^(active|archived|draft)$")
    brief: Optional[CampaignBrief] = None


class UpdateVideoMetricsRequest(BaseModel):
    """Request model for updating video performance metrics."""
    views: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    ctr: Optional[float] = Field(None, ge=0.0, le=1.0)
    conversions: Optional[int] = Field(None, ge=0)


class ApiResponse(BaseModel):
    """Generic API response wrapper."""
    data: Any
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ============================================================================
# CLIENT ENDPOINTS
# ============================================================================

@router.get("/clients")
async def get_clients(
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get all clients for the authenticated user.

    Returns:
        ApiResponse with array of Client objects
    """
    try:
        clients = list_clients(current_user["id"])
        return ApiResponse(data=clients)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve clients: {str(e)}")


@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get a single client by ID.

    Args:
        client_id: Client UUID

    Returns:
        ApiResponse with Client object

    Raises:
        404: Client not found
    """
    client = get_client_by_id(client_id, current_user["id"])
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return ApiResponse(data=client)


@router.post("/clients", status_code=201)
async def create_new_client(
    request: CreateClientRequest,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Create a new client.

    Args:
        request: CreateClientRequest with client data

    Returns:
        ApiResponse with created Client object (includes id, createdAt, updatedAt)
    """
    try:
        # Convert Pydantic model to dict
        brand_guidelines = request.brandGuidelines.dict() if request.brandGuidelines else None

        # Create client
        client_id = create_client(
            user_id=current_user["id"],
            name=request.name,
            description=request.description,
            brand_guidelines=brand_guidelines
        )

        # Retrieve and return the created client
        client = get_client_by_id(client_id, current_user["id"])
        return ApiResponse(data=client, message="Client created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create client: {str(e)}")


@router.patch("/clients/{client_id}")
async def update_existing_client(
    client_id: str,
    request: UpdateClientRequest,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Update an existing client (partial update).

    Args:
        client_id: Client UUID
        request: UpdateClientRequest with fields to update

    Returns:
        ApiResponse with updated Client object

    Raises:
        404: Client not found
    """
    # Convert Pydantic model to dict (only provided fields)
    brand_guidelines = request.brandGuidelines.dict() if request.brandGuidelines else None

    success = update_client(
        client_id=client_id,
        user_id=current_user["id"],
        name=request.name,
        description=request.description,
        brand_guidelines=brand_guidelines
    )

    if not success:
        raise HTTPException(status_code=404, detail="Client not found")

    # Retrieve and return the updated client
    client = get_client_by_id(client_id, current_user["id"])
    return ApiResponse(data=client, message="Client updated successfully")


@router.delete("/clients/{client_id}")
async def delete_existing_client(
    client_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Delete a client (cascades to campaigns and videos).

    Args:
        client_id: Client UUID

    Returns:
        ApiResponse with success message

    Raises:
        404: Client not found
    """
    success = delete_client(client_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")

    return ApiResponse(data=None, message="Client deleted successfully")


@router.get("/clients/{client_id}/stats")
async def get_client_statistics(
    client_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get statistics for a client.

    Args:
        client_id: Client UUID

    Returns:
        ApiResponse with ClientStats object

    Raises:
        404: Client not found
    """
    stats = get_client_stats(client_id, current_user["id"])
    if stats is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return ApiResponse(data=stats)


@router.post("/clients/{client_id}/assets", status_code=201)
async def upload_client_asset(
    client_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Upload a client asset (logo, brand document, etc.).

    Args:
        client_id: Client UUID
        file: File to upload

    Returns:
        ApiResponse with ClientAsset object

    Raises:
        404: Client not found
        400: Invalid file type
    """
    # Verify client exists and user owns it
    client = get_client_by_id(client_id, current_user["id"])
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Determine asset type from MIME type
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        asset_type = "logo" if "logo" in file.filename.lower() else "image"
    elif content_type == "application/pdf" or file.filename.endswith(".pdf"):
        asset_type = "document"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: images, PDF documents")

    # Save file to storage (using DATA directory)
    from pathlib import Path
    data_dir = Path(os.getenv("DATA", "./DATA"))
    client_assets_dir = data_dir / "client_assets" / client_id
    client_assets_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = client_assets_dir / unique_filename

    # Write file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create asset URL (relative path)
    asset_url = f"/api/client-assets/{client_id}/{unique_filename}"

    # Save to database
    asset_id = create_client_asset(
        client_id=client_id,
        asset_type=asset_type,
        url=asset_url,
        name=file.filename
    )

    # Return asset data
    asset_data = {
        "id": asset_id,
        "type": asset_type,
        "url": asset_url,
        "name": file.filename,
        "uploadedAt": datetime.utcnow().isoformat() + "Z"
    }

    return ApiResponse(data=asset_data, message="Asset uploaded successfully")


# ============================================================================
# CAMPAIGN ENDPOINTS
# ============================================================================

@router.get("/campaigns")
async def get_campaigns(
    clientId: Optional[str] = Query(None, description="Filter by client ID"),
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get all campaigns for the authenticated user, optionally filtered by client.

    Args:
        clientId: Optional client UUID to filter campaigns

    Returns:
        ApiResponse with array of Campaign objects
    """
    try:
        campaigns = list_campaigns(current_user["id"], client_id=clientId)
        return ApiResponse(data=campaigns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaigns: {str(e)}")


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get a single campaign by ID.

    Args:
        campaign_id: Campaign UUID

    Returns:
        ApiResponse with Campaign object

    Raises:
        404: Campaign not found
    """
    campaign = get_campaign_by_id(campaign_id, current_user["id"])
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return ApiResponse(data=campaign)


@router.post("/campaigns", status_code=201)
async def create_new_campaign(
    request: CreateCampaignRequest,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Create a new campaign.

    Args:
        request: CreateCampaignRequest with campaign data

    Returns:
        ApiResponse with created Campaign object (includes id, createdAt, updatedAt)
    """
    try:
        # Verify client exists
        client = get_client_by_id(request.clientId, current_user["id"])
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Convert brief to dict
        brief = request.brief.dict() if request.brief else None

        # Create campaign
        campaign_id = create_campaign(
            user_id=current_user["id"],
            client_id=request.clientId,
            name=request.name,
            goal=request.goal,
            status=request.status,
            brief=brief
        )

        # Retrieve and return the created campaign
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        return ApiResponse(data=campaign, message="Campaign created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")


@router.patch("/campaigns/{campaign_id}")
async def update_existing_campaign(
    campaign_id: str,
    request: UpdateCampaignRequest,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Update an existing campaign (partial update).

    Args:
        campaign_id: Campaign UUID
        request: UpdateCampaignRequest with fields to update

    Returns:
        ApiResponse with updated Campaign object

    Raises:
        404: Campaign not found
    """
    # Convert brief to dict
    brief = request.brief.dict() if request.brief else None

    success = update_campaign(
        campaign_id=campaign_id,
        user_id=current_user["id"],
        name=request.name,
        goal=request.goal,
        status=request.status,
        brief=brief
    )

    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Retrieve and return the updated campaign
    campaign = get_campaign_by_id(campaign_id, current_user["id"])
    return ApiResponse(data=campaign, message="Campaign updated successfully")


@router.delete("/campaigns/{campaign_id}")
async def delete_existing_campaign(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Delete a campaign (cascades to campaign assets).

    Args:
        campaign_id: Campaign UUID

    Returns:
        ApiResponse with success message

    Raises:
        404: Campaign not found
        409: Campaign has associated videos (cannot delete)
    """
    # Check if campaign has videos
    videos = list_videos_by_campaign(campaign_id, limit=1)
    if videos:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete campaign with associated videos. Please delete videos first."
        )

    success = delete_campaign(campaign_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return ApiResponse(data=None, message="Campaign deleted successfully")


@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_statistics(
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Get statistics for a campaign.

    Args:
        campaign_id: Campaign UUID

    Returns:
        ApiResponse with CampaignStats object

    Raises:
        404: Campaign not found
    """
    stats = get_campaign_stats(campaign_id, current_user["id"])
    if stats is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return ApiResponse(data=stats)


@router.post("/campaigns/{campaign_id}/assets", status_code=201)
async def upload_campaign_asset(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Upload a campaign asset (image, video, document).

    Args:
        campaign_id: Campaign UUID
        file: File to upload

    Returns:
        ApiResponse with CampaignAsset object

    Raises:
        404: Campaign not found
        400: Invalid file type
    """
    # Verify campaign exists and user owns it
    campaign = get_campaign_by_id(campaign_id, current_user["id"])
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Determine asset type from MIME type
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        asset_type = "image"
    elif content_type.startswith("video/"):
        asset_type = "video"
    elif content_type == "application/pdf" or file.filename.endswith(".pdf"):
        asset_type = "document"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: images, videos, PDF documents")

    # Save file to storage
    from pathlib import Path
    data_dir = Path(os.getenv("DATA", "./DATA"))
    campaign_assets_dir = data_dir / "campaign_assets" / campaign_id
    campaign_assets_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = campaign_assets_dir / unique_filename

    # Write file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create asset URL
    asset_url = f"/api/campaign-assets/{campaign_id}/{unique_filename}"

    # Save to database
    asset_id = create_campaign_asset(
        campaign_id=campaign_id,
        asset_type=asset_type,
        url=asset_url,
        name=file.filename
    )

    # Return asset data
    asset_data = {
        "id": asset_id,
        "type": asset_type,
        "url": asset_url,
        "name": file.filename,
        "uploadedAt": datetime.utcnow().isoformat() + "Z"
    }

    return ApiResponse(data=asset_data, message="Asset uploaded successfully")


# ============================================================================
# VIDEO METRICS ENDPOINT (Enhancement)
# ============================================================================

@router.patch("/videos/{video_id}/metrics")
async def update_video_performance_metrics(
    video_id: int,
    request: UpdateVideoMetricsRequest,
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> ApiResponse:
    """
    Update video performance metrics (views, clicks, CTR, conversions).

    Args:
        video_id: Video ID
        request: UpdateVideoMetricsRequest with metrics to update

    Returns:
        ApiResponse with success message

    Raises:
        404: Video not found
    """
    success = update_video_metrics(
        video_id=video_id,
        views=request.views,
        clicks=request.clicks,
        ctr=request.ctr,
        conversions=request.conversions
    )

    if not success:
        raise HTTPException(status_code=404, detail="Video not found")

    return ApiResponse(data=None, message="Video metrics updated successfully")
