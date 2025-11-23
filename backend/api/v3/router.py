"""
FastAPI router for v3 API endpoints.

This router provides a simplified, frontend-aligned API that matches
the data requirements of the Next.js frontend with proper Pydantic models.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
    BackgroundTasks,
    Request,
)
from typing import List, Optional, Dict, Any, cast
from datetime import datetime
import logging
import json
import uuid
import mimetypes
import asyncio
from asyncio import Semaphore

# Configure logging
logger = logging.getLogger(__name__)

from .models import (
    APIResponse,
    Client,
    ClientCreateRequest,
    ClientUpdateRequest,
    Campaign,
    CampaignCreateRequest,
    CampaignUpdateRequest,
    Job,
    JobCreateRequest,
    JobActionRequest,
    JobStatus,
    JobAction,
    CostEstimate,
    DryRunRequest,
    Asset,
    UploadAssetInput,
    UnifiedAssetUploadInput,
    SceneAudioRequest,
    ScenePrompt,
    PropertyVideoRequest,
)
from ...schemas.assets import UploadAssetFromUrlInput, BulkAssetFromUrlInput

from ...services.scene_audio_generator import generate_scene_audio_track
from ...database_helpers import (
    create_client,
    get_client_by_id,
    list_clients,
    update_client,
    delete_client,
    get_client_stats,
    create_campaign,
    get_campaign_by_id,
    list_campaigns,
    update_campaign,
    delete_campaign,
    get_campaign_stats,
    create_asset,
    get_asset_by_id,
    list_assets,
    update_asset,
    delete_asset,
    create_job_scene,
    get_scenes_by_job,
    get_scene_by_id,
    update_job_scene,
    delete_job_scene,
)
from ...database import update_job_parameters
from ...auth import verify_auth
from ...services.storyboard_generator import generate_storyboard_task
from ...services.video_renderer import render_video_task
from ...services.replicate_client import ReplicateClient
from ...services.asset_downloader import (
    download_asset_from_url,
    store_blob,
    AssetDownloadError,
)
from ...services.scene_generator import (
    generate_scenes,
    regenerate_scene,
    SceneGenerationError,
)
from ...database import (
    get_job,
    update_job_progress,
    approve_storyboard,
    create_video_job,
    update_video_status,
    get_audio_by_id,
)
from ...config import get_settings

# Initialize router (tags are set per endpoint for better organization)
router = APIRouter(prefix="/api/v3")
settings = get_settings()


# ============================================================================
# Helper Functions
# ============================================================================


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"


def create_api_meta(
    page: Optional[int] = None, total: Optional[int] = None
) -> Dict[str, Any]:
    """Create standard API meta object"""
    meta: Dict[str, Any] = {"timestamp": get_current_timestamp()}
    if page is not None:
        meta["page"] = page
    if total is not None:
        meta["total"] = total
    return meta


# ============================================================================
# Client Endpoints
# ============================================================================


@router.get("/clients", response_model=APIResponse, tags=["v3-clients"])
async def get_clients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Get all clients for the authenticated user"""
    logger.info(
        f"V3 clients endpoint called by user {current_user.get('id')} with limit={limit}, offset={offset}"
    )

    try:
        logger.info(f"Calling list_clients for user {current_user['id']}")
        clients = list_clients(current_user["id"], limit=limit, offset=offset)

        logger.info(f"Retrieved {len(clients)} clients from database")
        if clients:
            logger.info(f"First client sample: {clients[0]}")
            logger.info(
                f"Client keys: {list(clients[0].keys()) if clients[0] else 'No clients'}"
            )

        meta = create_api_meta(page=(offset // limit) + 1, total=len(clients))
        logger.info(f"Response meta: {meta}")

        # Try to validate the response against the Client model
        try:
            from .models import Client

            if clients:
                # Try to validate the first client
                test_client = Client(**clients[0])
                logger.info(
                    f"Client model validation successful for client {clients[0]['id']}"
                )
        except Exception as validation_error:
            logger.error(f"Client model validation failed: {validation_error}")
            logger.error(f"Client data: {clients[0] if clients else 'No clients'}")

        response = APIResponse.success(data=clients, meta=meta)
        logger.info(f"Returning successful response with {len(clients)} clients")

        return response
    except Exception as e:
        logger.error(f"Error in get_clients: {str(e)}", exc_info=True)
        return APIResponse.create_error(f"Failed to fetch clients: {str(e)}")


@router.get("/clients/{client_id}", response_model=APIResponse, tags=["v3-clients"])
async def get_client(
    client_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get a specific client by ID"""
    logger.info(
        f"V3 get_client endpoint called for client_id={client_id} by user {current_user.get('id')}"
    )

    try:
        logger.info(f"Calling get_client_by_id for client {client_id}")
        client = get_client_by_id(client_id, current_user["id"])

        if not client:
            logger.warning(
                f"Client {client_id} not found for user {current_user['id']}"
            )
            return APIResponse.create_error("Client not found")

        logger.info(f"Retrieved client: {client}")
        logger.info(f"Client keys: {list(client.keys())}")

        # Try to validate the response against the Client model
        try:
            from .models import Client

            test_client = Client(**client)
            logger.info(f"Client model validation successful for client {client_id}")
        except Exception as validation_error:
            logger.error(
                f"Client model validation failed for client {client_id}: {validation_error}"
            )
            logger.error(f"Client data: {client}")

        response = APIResponse.success(data=client, meta=create_api_meta())
        logger.info(f"Returning successful response for client {client_id}")

        return response
    except Exception as e:
        logger.error(
            f"Error in get_client for client {client_id}: {str(e)}", exc_info=True
        )
        return APIResponse.create_error(f"Failed to fetch client: {str(e)}")


@router.post("/clients", response_model=APIResponse, tags=["v3-clients"])
async def create_new_client(
    request: ClientCreateRequest, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Create a new client"""
    try:
        client_id = create_client(
            user_id=current_user["id"],
            name=request.name,
            description=request.description or "",
            homepage=request.homepage,
            brand_guidelines=request.brandGuidelines.dict()
            if request.brandGuidelines
            else None,
            metadata=request.metadata,
        )

        # Fetch the created client
        client = get_client_by_id(client_id, current_user["id"])
        return APIResponse.success(data=client, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to create client: {str(e)}")


@router.put("/clients/{client_id}", response_model=APIResponse, tags=["v3-clients"])
async def update_existing_client(
    client_id: str,
    request: ClientUpdateRequest,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Update an existing client"""
    try:
        success = update_client(
            client_id=client_id,
            user_id=current_user["id"],
            name=request.name,
            description=request.description,
            homepage=request.homepage,
            brand_guidelines=request.brandGuidelines.dict()
            if request.brandGuidelines
            else None,
            metadata=request.metadata,
        )

        if not success:
            return APIResponse.create_error("Client not found or update failed")

        # Fetch the updated client
        client = get_client_by_id(client_id, current_user["id"])
        return APIResponse.success(data=client, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to update client: {str(e)}")


@router.delete("/clients/{client_id}", response_model=APIResponse, tags=["v3-clients"])
async def delete_existing_client(
    client_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete a client"""
    try:
        success = delete_client(client_id, current_user["id"])
        if not success:
            return APIResponse.create_error("Client not found")

        return APIResponse.success(
            data={"message": "Client deleted successfully"}, meta=create_api_meta()
        )
    except Exception as e:
        return APIResponse.create_error(f"Failed to delete client: {str(e)}")


@router.get(
    "/clients/{client_id}/stats", response_model=APIResponse, tags=["v3-clients"]
)
async def get_client_statistics(
    client_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get statistics for a client"""
    try:
        stats = get_client_stats(client_id, current_user["id"])
        if stats is None:
            return APIResponse.create_error("Client not found")

        return APIResponse.success(data=stats, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch client stats: {str(e)}")


# ============================================================================
# Campaign Endpoints
# ============================================================================


@router.get("/campaigns", response_model=APIResponse, tags=["v3-campaigns"])
async def get_campaigns(
    client_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Get campaigns, optionally filtered by client"""
    try:
        # Strip whitespace from client_id if provided
        clean_client_id = client_id.strip() if client_id else None

        campaigns = list_campaigns(
            user_id=None,  # Allow access to all campaigns
            client_id=clean_client_id, limit=limit, offset=offset
        )
        meta = create_api_meta(page=(offset // limit) + 1, total=len(campaigns))
        return APIResponse.success(data=campaigns, meta=meta)
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch campaigns: {str(e)}")


@router.get(
    "/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"]
)
async def get_campaign(
    campaign_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get a specific campaign by ID"""
    try:
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        if not campaign:
            return APIResponse.create_error("Campaign not found")

        return APIResponse.success(data=campaign, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch campaign: {str(e)}")


@router.post("/campaigns", response_model=APIResponse, tags=["v3-campaigns"])
async def create_new_campaign(
    request: CampaignCreateRequest, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Create a new campaign"""
    try:
        campaign_id = create_campaign(
            user_id=current_user["id"],
            client_id=request.clientId,
            name=request.name,
            goal=request.goal,
            status=request.status,
            product_url=request.productUrl,
            brief=request.brief,
            metadata=request.metadata,
        )

        # Fetch the created campaign
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        return APIResponse.success(data=campaign, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to create campaign: {str(e)}")


@router.put(
    "/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"]
)
async def update_existing_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Update an existing campaign"""
    try:
        success = update_campaign(
            campaign_id=campaign_id,
            user_id=current_user["id"],
            name=request.name,
            goal=request.goal,
            status=request.status,
            product_url=request.productUrl,
            brief=request.brief,
            metadata=request.metadata,
        )

        if not success:
            return APIResponse.create_error("Campaign not found or update failed")

        # Fetch the updated campaign
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        return APIResponse.success(data=campaign, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to update campaign: {str(e)}")


@router.delete(
    "/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"]
)
async def delete_existing_campaign(
    campaign_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete a campaign"""
    try:
        success = delete_campaign(campaign_id, current_user["id"])
        if not success:
            return APIResponse.create_error("Campaign not found")

        return APIResponse.success(
            data={"message": "Campaign deleted successfully"}, meta=create_api_meta()
        )
    except Exception as e:
        return APIResponse.create_error(f"Failed to delete campaign: {str(e)}")


@router.get(
    "/campaigns/{campaign_id}/stats", response_model=APIResponse, tags=["v3-campaigns"]
)
async def get_campaign_statistics(
    campaign_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get statistics for a campaign"""
    try:
        stats = get_campaign_stats(campaign_id, current_user["id"])
        if stats is None:
            return APIResponse.create_error("Campaign not found")

        return APIResponse.success(data=stats, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch campaign stats: {str(e)}")


# ============================================================================
# Asset Endpoints
# ============================================================================


@router.get("/assets", response_model=APIResponse, tags=["v3-assets"])
async def get_assets(
    client_id: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Get assets with optional filtering"""
    try:
        assets = list_assets(
            user_id=None,  # Allow access to all campaigns
            client_id=client_id,
            campaign_id=campaign_id,
            asset_type=asset_type,
            limit=limit,
            offset=offset,
        )
        meta = create_api_meta(page=(offset // limit) + 1, total=len(assets))
        return APIResponse.success(data=assets, meta=meta)
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=APIResponse, tags=["v3-assets"])
async def get_asset(
    asset_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get a specific asset by ID"""
    try:
        asset = get_asset_by_id(asset_id)
        if not asset:
            return APIResponse.create_error("Asset not found")

        return APIResponse.success(data=asset, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch asset: {str(e)}")


@router.get("/assets/{asset_id}/data", tags=["v3-assets"])
async def get_asset_data(
    asset_id: str,
    request: Request,
    token: Optional[str] = Query(
        None, description="Temporary access token for public access"
    ),
):
    """
    Serve the binary asset data.

    Supports two authentication methods:
    1. Standard user authentication (Bearer token, API key, or cookie)
    2. Temporary asset access token (query parameter ?token=...)

    The temporary token allows external services (like Replicate) to access
    assets without user credentials.
    """
    from fastapi.responses import Response
    from ...database_helpers import get_db
    from ...auth import (
        verify_asset_access_token,
        _verify_api_key_and_get_user,
        decode_access_token,
        get_user_by_username,
        COOKIE_NAME,
    )
    import os

    # Verify authentication: either temporary token OR standard auth required
    authenticated = False

    # Try token-based access first
    if token:
        verified_asset_id = verify_asset_access_token(token)
        if verified_asset_id and verified_asset_id == asset_id:
            # Token is valid and matches the requested asset
            authenticated = True
        else:
            raise HTTPException(
                status_code=401, detail="Invalid or expired access token"
            )
    else:
        # No token provided - try standard authentication (API key, cookie, or Bearer token)
        # Check for local development bypass
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        if base_url.startswith("http://localhost") or base_url.startswith(
            "http://127.0.0.1"
        ):
            authenticated = True
        else:
            # Try API key from X-API-Key header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                user = _verify_api_key_and_get_user(api_key)
                if user:
                    authenticated = True

            # Try cookie authentication
            if not authenticated:
                cookie_token = request.cookies.get(COOKIE_NAME)
                if cookie_token:
                    payload = decode_access_token(cookie_token)
                    if payload:
                        username = payload.get("sub")
                        if username:
                            user = get_user_by_username(username)
                            if user and user.get("is_active"):
                                authenticated = True

            # Try Bearer token from Authorization header
            if not authenticated:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    bearer_token = auth_header[7:]  # Remove "Bearer " prefix
                    payload = decode_access_token(bearer_token)
                    if payload:
                        username = payload.get("sub")
                        if username:
                            user = get_user_by_username(username)
                            if user and user.get("is_active"):
                                authenticated = True

    if not authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Query asset directly from database to get blob_id and blob_data
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT blob_id, blob_data, format, name
                FROM assets
                WHERE id = ?
                """,
                (asset_id,),
            ).fetchone()

            if not row:
                return APIResponse.create_error("Asset not found")

            blob_id = row["blob_id"]
            blob_data = row["blob_data"]
            asset_format = row["format"]
            asset_name = row["name"]

        # Check if asset has blob_id (V3 blob storage)
        if blob_id:
            from ...services.asset_downloader import get_blob_by_id

            blob_result = get_blob_by_id(blob_id)

            if blob_result:
                data, content_type = blob_result
                return Response(
                    content=data,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f'inline; filename="{asset_name}"',
                        "Cache-Control": "public, max-age=31536000",
                    },
                )

        # Fallback to blob_data column (legacy storage)
        if blob_data:
            # Determine content type from format
            format_to_mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
                "gif": "image/gif",
                "mp4": "video/mp4",
                "webm": "video/webm",
                "mov": "video/quicktime",
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "ogg": "audio/ogg",
                "pdf": "application/pdf",
            }

            content_type = format_to_mime.get(
                asset_format.lower(), "application/octet-stream"
            )

            return Response(
                content=bytes(blob_data),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{asset_name}"',
                    "Cache-Control": "public, max-age=31536000",
                },
            )

        # No binary data available
        return APIResponse.create_error("Asset data not available")

    except Exception as e:
        return APIResponse.create_error(f"Failed to serve asset data: {str(e)}")


@router.get("/assets/{asset_id}/thumbnail", tags=["v3-assets"])
async def get_asset_thumbnail(asset_id: str, current_user: Dict = Depends(verify_auth)):
    """Serve the asset thumbnail"""
    from fastapi.responses import Response
    from ...database_helpers import get_db

    try:
        # Query asset to get thumbnail_blob_id
        with get_db() as conn:
            row = conn.execute(
                "SELECT thumbnail_blob_id, name FROM assets WHERE id = ?", (asset_id,)
            ).fetchone()

            if not row or not row["thumbnail_blob_id"]:
                return APIResponse.create_error("Thumbnail not available")

            thumbnail_blob_id = row["thumbnail_blob_id"]
            asset_name = row["name"]

        # Get thumbnail data from blob storage
        from ...services.asset_downloader import get_blob_by_id

        blob_result = get_blob_by_id(thumbnail_blob_id)

        if blob_result:
            data, content_type = blob_result
            return Response(
                content=data,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{asset_name}_thumbnail.jpg"',
                    "Cache-Control": "public, max-age=31536000",
                },
            )

        return APIResponse.create_error("Thumbnail data not available")

    except Exception as e:
        return APIResponse.create_error(f"Failed to serve thumbnail: {str(e)}")


@router.post("/assets", response_model=APIResponse, tags=["v3-assets"])
async def upload_asset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    type: Optional[str] = None,
    clientId: Optional[str] = None,
    campaignId: Optional[str] = None,
    tags: Optional[str] = None,  # JSON string
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Upload a new asset"""
    try:
        # Parse tags if provided
        tags_list = None
        if tags:
            try:
                tags_list = json.loads(tags)
            except:
                tags_list = [tags]  # Single tag as string

        # Read file content
        file_content = await file.read()

        # Determine format
        filename = file.filename or "unknown"
        format_ext = filename.split(".")[-1] if "." in filename else "bin"

        # Generate ID first
        asset_id = str(uuid.uuid4())

        # Construct the serving URL (pointing to the existing v2 data endpoint)
        asset_url = f"/api/v2/assets/{asset_id}/data"

        # Create asset with specific ID and valid URL
        create_asset(
            asset_id=asset_id,
            name=name or filename,
            asset_type=type or "document",
            url=asset_url,
            format=format_ext,
            size=len(file_content),
            user_id=current_user["id"],
            client_id=clientId,
            campaign_id=campaignId,
            tags=tags_list,
            blob_data=file_content,
        )

        # Fetch the created asset
        asset = get_asset_by_id(asset_id)
        return APIResponse.success(data=asset, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to upload asset: {str(e)}")


@router.post("/assets/from-url", response_model=APIResponse, tags=["v3-assets"])
async def upload_asset_from_url(
    request: UploadAssetFromUrlInput, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Upload an asset by downloading it from a URL"""
    try:
        # Download asset from URL
        asset_data, content_type, metadata = download_asset_from_url(
            url=request.url, asset_type=request.type
        )

        # Store as blob in database
        blob_id = store_blob(asset_data, content_type)

        # Generate asset ID
        asset_id = str(uuid.uuid4())

        # Construct V3 serving URL
        asset_url = f"/api/v3/assets/{asset_id}/data"

        # Create asset record with blob reference
        create_asset(
            asset_id=asset_id,
            name=request.name,
            asset_type=request.type,
            url=asset_url,
            format=metadata.get("format", "unknown"),
            size=metadata.get("size", len(asset_data)),
            user_id=current_user["id"],
            client_id=request.clientId,
            campaign_id=request.campaignId,
            tags=request.tags,
            blob_id=blob_id,
            source_url=request.url,
            width=metadata.get("width"),
            height=metadata.get("height"),
            duration=metadata.get("duration"),
        )

        # Fetch the created asset
        asset = get_asset_by_id(asset_id)
        return APIResponse.success(data=asset, meta=create_api_meta())
    except AssetDownloadError as e:
        return APIResponse.create_error(f"Failed to download asset: {str(e)}")
    except Exception as e:
        return APIResponse.create_error(f"Failed to upload asset from URL: {str(e)}")


@router.post("/assets/from-urls", response_model=APIResponse, tags=["v3-assets"])
async def upload_assets_from_urls(
    request: BulkAssetFromUrlInput, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Upload multiple assets by downloading them from URLs"""

    async def process_single_asset(asset_item, semaphore):
        """Process a single asset upload"""
        async with semaphore:
            try:
                # Download asset from URL
                asset_data, content_type, metadata = download_asset_from_url(
                    url=asset_item.url, asset_type=asset_item.type
                )

                # Store as blob in database
                blob_id = store_blob(asset_data, content_type)

                # Generate thumbnail if applicable
                thumbnail_blob_id = None
                if asset_item.type in ["image", "video"]:
                    from ...services.asset_downloader import (
                        generate_and_store_thumbnail,
                    )

                    thumbnail_blob_id = generate_and_store_thumbnail(
                        asset_data, content_type, asset_item.type
                    )

                # Generate asset ID
                asset_id = str(uuid.uuid4())

                # Construct V3 serving URL
                asset_url = f"/api/v3/assets/{asset_id}/data"

                # Create asset record with blob reference
                create_asset(
                    asset_id=asset_id,
                    name=asset_item.name,
                    asset_type=asset_item.type,
                    url=asset_url,
                    format=metadata.get("format", "unknown"),
                    size=metadata.get("size", len(asset_data)),
                    user_id=current_user["id"],
                    client_id=request.clientId,
                    campaign_id=request.campaignId,
                    tags=asset_item.tags,
                    blob_id=blob_id,
                    source_url=asset_item.url,
                    thumbnail_blob_id=thumbnail_blob_id,
                    width=metadata.get("width"),
                    height=metadata.get("height"),
                    duration=metadata.get("duration"),
                )

                # Fetch the created asset
                asset = get_asset_by_id(asset_id)
                return {"asset": asset, "success": True, "error": None}

            except AssetDownloadError as e:
                logger.warning(
                    f"Failed to download asset from {asset_item.url}: {str(e)}"
                )
                return {
                    "asset": None,
                    "success": False,
                    "error": f"Failed to download: {str(e)}",
                }
            except Exception as e:
                logger.error(f"Failed to process asset {asset_item.name}: {str(e)}")
                return {
                    "asset": None,
                    "success": False,
                    "error": f"Processing failed: {str(e)}",
                }

    try:
        if not request.assets:
            return APIResponse.create_error("No assets provided")

        if len(request.assets) > 100:  # Limit bulk uploads to prevent abuse
            return APIResponse.create_error(
                "Maximum 100 assets allowed per bulk upload"
            )

        logger.info(
            f"Bulk uploading {len(request.assets)} assets for user {current_user['id']}"
        )

        # Create semaphore to limit concurrent downloads (max 2 simultaneous for production)
        # Lower limit prevents overwhelming the server during bulk uploads
        semaphore = Semaphore(2)

        # Process all assets concurrently
        tasks = [
            process_single_asset(asset_item, semaphore) for asset_item in request.assets
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception in asset {i}: {str(result)}")
                processed_results.append(
                    {
                        "asset": None,
                        "success": False,
                        "error": f"Unexpected error: {str(result)}",
                    }
                )
            else:
                processed_results.append(result)

        # Calculate summary
        successful = sum(1 for r in processed_results if r["success"])
        failed = len(processed_results) - successful

        logger.info(f"Bulk upload completed: {successful} successful, {failed} failed")

        response_data = {
            "results": processed_results,
            "summary": {
                "total": len(processed_results),
                "successful": successful,
                "failed": failed,
            },
        }

        return APIResponse.success(data=response_data, meta=create_api_meta())

    except Exception as e:
        logger.error(f"Bulk asset upload failed: {str(e)}", exc_info=True)
        return APIResponse.create_error(f"Failed to upload assets: {str(e)}")


@router.post("/audio/generate-scenes", response_model=APIResponse, tags=["v3-audio"])
async def generate_scene_audio(
    request: SceneAudioRequest, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Generate continuous audio track from scene prompts using MusicGen continuation"""
    try:
        logger.info(
            f"Generating scene audio for user {current_user['id']}: {len(request.scenes)} scenes"
        )

        # Generate the audio track
        result = await generate_scene_audio_track(
            scenes=[scene.dict() for scene in request.scenes],
            default_duration=request.default_duration,
            model_id=request.model_id,
        )

        logger.info(f"Scene audio generation completed: {result}")

        return APIResponse.success(data=result, meta=create_api_meta())

    except Exception as e:
        logger.error(f"Scene audio generation failed: {str(e)}", exc_info=True)
        return APIResponse.create_error(f"Failed to generate scene audio: {str(e)}")


@router.post("/assets/unified", response_model=APIResponse, tags=["v3-assets"])
async def upload_asset_unified(
    request: UnifiedAssetUploadInput,
    file: Optional[UploadFile] = File(None),
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Unified asset upload endpoint supporting both file uploads and URL downloads"""
    try:
        asset_data = None
        content_type = None
        metadata = {}
        source_url = None

        if request.uploadType == "file":
            # Handle direct file upload
            if not file:
                return APIResponse.create_error("File is required for file upload type")

            # Read file content
            asset_data = await file.read()

            # Determine content type and metadata
            filename = file.filename or "unknown"
            content_type = (
                file.content_type
                or mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            # Basic metadata extraction
            metadata = {
                "size": len(asset_data),
                "format": filename.split(".")[-1] if "." in filename else "bin",
            }

            # Try to extract additional metadata for images
            if request.type == "image" and content_type.startswith("image/"):
                try:
                    from PIL import Image
                    import io

                    image = Image.open(io.BytesIO(asset_data))
                    metadata["width"] = image.width
                    metadata["height"] = image.height
                except:
                    pass

        elif request.uploadType == "url":
            # Handle URL download
            if not request.sourceUrl:
                return APIResponse.create_error(
                    "sourceUrl is required for URL upload type"
                )

            # Download asset from URL
            asset_data, content_type, metadata = download_asset_from_url(
                url=request.sourceUrl, asset_type=request.type
            )
            source_url = request.sourceUrl

        else:
            return APIResponse.create_error(f"Invalid uploadType: {request.uploadType}")

        # Store asset data as blob
        blob_id = store_blob(asset_data, content_type)

        # Generate asset ID
        asset_id = str(uuid.uuid4())

        # Construct V3 serving URL
        asset_url = f"/api/v3/assets/{asset_id}/data"

        # Generate thumbnail if requested and applicable
        thumbnail_blob_id = None
        if request.generateThumbnail and request.type in ["image", "video"]:
            from ...services.asset_downloader import generate_and_store_thumbnail

            thumbnail_blob_id = generate_and_store_thumbnail(
                asset_data, content_type, request.type
            )

        # Create asset record
        create_asset(
            asset_id=asset_id,
            name=request.name,
            asset_type=request.type,
            url=asset_url,
            format=metadata.get("format", "unknown"),
            size=metadata.get("size", len(asset_data)),
            user_id=current_user["id"],
            client_id=request.clientId,
            campaign_id=request.campaignId,
            tags=request.tags,
            blob_id=blob_id,
            source_url=source_url,
            thumbnail_blob_id=thumbnail_blob_id,
            width=metadata.get("width"),
            height=metadata.get("height"),
            duration=metadata.get("duration"),
        )

        # Fetch the created asset
        asset = get_asset_by_id(asset_id)
        return APIResponse.success(data=asset, meta=create_api_meta())

    except AssetDownloadError as e:
        return APIResponse.create_error(f"Failed to download asset: {str(e)}")
    except Exception as e:
        logger.error(f"Unified asset upload failed: {e}", exc_info=True)
        return APIResponse.create_error(f"Failed to upload asset: {str(e)}")


@router.delete("/assets/{asset_id}", response_model=APIResponse, tags=["v3-assets"])
async def delete_asset_v3(
    asset_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete an asset"""
    try:
        # Check if asset exists and belongs to user
        asset = get_asset_by_id(asset_id)
        if not asset:
            return APIResponse.create_error("Asset not found")

        # Delete the asset
        success = delete_asset(asset_id, current_user["id"])
        if not success:
            return APIResponse.create_error("Failed to delete asset or asset not found")

        return APIResponse.success(
            data={"message": "Asset deleted successfully"}, meta=create_api_meta()
        )
    except Exception as e:
        return APIResponse.create_error(f"Failed to delete asset: {str(e)}")


# ============================================================================
# Job Endpoints (Generation Workflow)
# ============================================================================


@router.post("/jobs", response_model=APIResponse, tags=["v3-jobs"])
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Create a new generation job"""
    try:
        # Process assets if provided
        processed_asset_ids = []
        if request.creative.assets:
            logger.info(
                f"Processing {len(request.creative.assets)} assets for job creation"
            )

            for asset_input in request.creative.assets:
                # If asset has a URL, download and store it
                if asset_input.url:
                    logger.info(
                        f"Downloading asset from URL: {asset_input.url[:50]}..."
                    )

                    # Determine asset type
                    asset_type = asset_input.type or "image"  # Default to image

                    # Download asset from URL
                    asset_data, content_type, metadata = download_asset_from_url(
                        url=asset_input.url, asset_type=asset_type
                    )

                    # Store as blob
                    blob_id = store_blob(asset_data, content_type)

                    # Generate asset ID
                    asset_id = str(uuid.uuid4())
                    asset_url = f"/api/v3/assets/{asset_id}/data"

                    # Generate thumbnail if applicable
                    thumbnail_blob_id = None
                    if asset_type in ["image", "video"]:
                        from ...services.asset_downloader import (
                            generate_and_store_thumbnail,
                        )

                        thumbnail_blob_id = generate_and_store_thumbnail(
                            asset_data, content_type, asset_type
                        )

                    # Create asset record
                    create_asset(
                        asset_id=asset_id,
                        name=asset_input.name or f"{asset_type}-{asset_id[:8]}",
                        asset_type=asset_type,
                        url=asset_url,
                        format=metadata.get("format", "unknown"),
                        size=metadata.get("size", len(asset_data)),
                        user_id=current_user["id"],
                        client_id=request.context.clientId,
                        campaign_id=request.context.campaignId,
                        blob_id=blob_id,
                        source_url=asset_input.url,
                        thumbnail_blob_id=thumbnail_blob_id,
                        width=metadata.get("width"),
                        height=metadata.get("height"),
                        duration=metadata.get("duration"),
                    )

                    processed_asset_ids.append(asset_id)
                    logger.info(f"Created asset {asset_id} from URL")

                # If asset has an ID, just use the existing asset
                elif asset_input.assetId:
                    # Verify asset exists
                    existing_asset = get_asset_by_id(asset_input.assetId)
                    if not existing_asset:
                        return APIResponse.create_error(
                            f"Asset not found: {asset_input.assetId}"
                        )
                    processed_asset_ids.append(asset_input.assetId)
                    logger.info(f"Using existing asset {asset_input.assetId}")

        # Build prompt from request data
        prompt = f"""
        Product: {request.adBasics.product}
        Target Audience: {request.adBasics.targetAudience}
        Key Message: {request.adBasics.keyMessage}
        Call to Action: {request.adBasics.callToAction}
        Style: {request.creative.direction.style}
        """

        # Create job using existing video job function
        audio_cost = 2.0 if request.generateAudio else 0.0
        job_id = create_video_job(
            prompt=prompt,
            model_id="v3-job",  # Placeholder model
            parameters={
                "context": request.context.dict(),
                "ad_basics": request.adBasics.dict(),
                "creative": request.creative.dict(),
                "advanced": request.advanced.dict() if request.advanced else None,
                "processed_asset_ids": processed_asset_ids,
                "generate_audio": request.generateAudio,
                "audio_cost": audio_cost,
            },
            estimated_cost=5.0 + audio_cost,
            client_id=request.context.clientId,
            status="scene_generation",
        )

        logger.info(
            f"Created job {job_id} (audio: {request.generateAudio}, cost: ${5.0 + audio_cost})"
        )

        logger.info(f"Created job {job_id} with audio enabled: {request.generateAudio}")

        # Generate scenes using AI
        logger.info(f"Generating scenes for job {job_id}")
        try:
            scenes = generate_scenes(
                ad_basics=request.adBasics.dict(),
                creative_direction=request.creative.direction.dict(),
                assets=processed_asset_ids,
                duration=request.creative.videoSpecs.duration,
                num_scenes=None,  # Auto-determine based on duration
            )

            # Store generated scenes in database
            for scene in scenes:
                create_job_scene(
                    job_id=job_id,
                    scene_number=scene["sceneNumber"],
                    duration=scene["duration"],
                    description=scene["description"],
                    script=scene.get("script"),
                    shot_type=scene.get("shotType"),
                    transition=scene.get("transition"),
                    assets=scene.get("assets", []),
                    metadata=scene.get("metadata", {}),
                )

            logger.info(f"Generated and stored {len(scenes)} scenes for job {job_id}")

            # Generate audio track if requested
            audio_info = None
            actual_cost = 5.0
            if request.generateAudio:
                try:
                    # Prepare scene prompts for audio generation
                    scene_prompts = []
                    for scene in scenes:
                        combined_prompt = f"{scene['description']}"
                        if scene.get("script"):
                            combined_prompt += f". Voiceover: {scene['script']}"

                        scene_prompts.append(
                            {
                                "scene_number": scene["sceneNumber"],
                                "prompt": combined_prompt,
                                "duration": scene["duration"],
                            }
                        )

                    logger.info(
                        f"🎵 Generating audio track for {len(scene_prompts)} scenes (job {job_id})"
                    )

                    # Generate the audio track
                    audio_result = await generate_scene_audio_track(
                        scenes=scene_prompts,
                        default_duration=4.0,
                        model_id="meta/musicgen",
                        user_id=current_user["id"],
                    )

                    audio_info = {
                        "status": "completed",
                        "audio_id": audio_result["audio_id"],
                        "audio_url": audio_result["audio_url"],
                        "total_duration": audio_result["total_duration"],
                        "scenes_processed": audio_result["scenes_processed"],
                        "model_used": audio_result["model_used"],
                    }

                    actual_cost += 2.0  # Audio cost
                    logger.info(
                        f"✓ Audio track generated successfully for job {job_id}: {audio_info['audio_id']}"
                    )

                    # Store audio info in job parameters for rendering
                    current_params = {
                        "context": request.context.dict(),
                        "ad_basics": request.adBasics.dict(),
                        "creative": request.creative.dict(),
                        "advanced": request.advanced.dict()
                        if request.advanced
                        else None,
                        "processed_asset_ids": processed_asset_ids,
                        "scenes": [
                            {k: v for k, v in s.items() if k != "metadata"}
                            for s in scenes
                        ],  # Store scenes without large metadata
                        "audio_info": audio_info,
                    }
                    update_job_parameters(job_id, current_params)

                except Exception as audio_error:
                    logger.error(
                        f"⚠️ Audio generation failed for job {job_id}: {audio_error}"
                    )
                    audio_info = {
                        "status": "failed",
                        "error": str(audio_error),
                        "requested": True,
                        "fallback_available": False,
                    }
                    # No additional cost for failed audio
            else:
                audio_info = {"status": "not_requested"}

            auto_approve = request.advanced.autoApprove if request.advanced else False

            if auto_approve:
                approve_storyboard(job_id)
                background_tasks.add_task(render_video_task, job_id)
                update_video_status(job_id, "video_processing")
                response_status = JobStatus.VIDEO_PROCESSING
            else:
                update_video_status(job_id, "storyboard_ready")
                response_status = JobStatus.STORYBOARD_READY

            # Prepare response with audio info and actual cost
            job_response = {
                "id": str(job_id),
                "status": response_status,
                "assetIds": processed_asset_ids,
                "scenes": scenes,
                "audio": audio_info,
                "estimatedCost": actual_cost,
                "createdAt": get_current_timestamp(),
                "updatedAt": get_current_timestamp(),
            }

            logger.info(
                f"Job {job_id} ready: {len(scenes)} scenes, audio: {audio_info.get('status', 'none')}, cost: ${actual_cost}"
            )
            return APIResponse.success(data=job_response, meta=create_api_meta())

        except SceneGenerationError as e:
            logger.error(f"Scene generation failed for job {job_id}: {e}")
            update_video_status(job_id, "failed")
            return APIResponse.create_error(f"Failed to generate scenes: {str(e)}")
    except AssetDownloadError as e:
        logger.error(f"Asset download error: {e}", exc_info=True)
        return APIResponse.create_error(f"Failed to download asset: {str(e)}")
    except Exception as e:
        logger.error(f"Job creation failed: {e}", exc_info=True)
        return APIResponse.create_error(f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=APIResponse, tags=["v3-jobs"])
async def get_job_status(
    job_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get job status and progress"""
    try:
        job_raw = get_job(int(job_id))
        if job_raw is None:
            return APIResponse.create_error("Job not found")
        job_dict = cast(Dict[str, Any], job_raw)

        # Map database status (v2 style) to frontend enum (v3 style)
        status_mapping = {
            "pending": JobStatus.PENDING,
            "parsing": JobStatus.STORYBOARD_PROCESSING,
            "generating_storyboard": JobStatus.STORYBOARD_PROCESSING,
            "storyboard_ready": JobStatus.STORYBOARD_READY,
            "rendering": JobStatus.VIDEO_PROCESSING,
            "processing": JobStatus.VIDEO_PROCESSING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "canceled": JobStatus.CANCELLED,
            "cancelled": JobStatus.CANCELLED,
        }

        # Default to FAILED if unknown status
        v3_status = status_mapping.get(
            job_dict["status"] if "status" in job_dict else "failed", JobStatus.FAILED
        )

        # Get scenes from job_scenes table
        scenes = get_scenes_by_job(int(job_id))

        # Extract audio info from job parameters
        audio_info = {"status": "not_requested"}
        if "parameters" in job_dict:
            try:
                params = (
                    json.loads(job_dict["parameters"])
                    if isinstance(job_dict["parameters"], str)
                    else job_dict["parameters"]
                )

                if "audio_info" in params:
                    audio_info = params["audio_info"]
                elif "audio" in params:
                    audio_info = params["audio"]
                elif "generate_audio" in params and params["generate_audio"]:
                    audio_info = {"status": "processing", "requested": True}

            except (json.JSONDecodeError, KeyError) as param_error:
                logger.debug(
                    f"Could not parse audio info from job params: {param_error}"
                )

        job_data = {
            "id": str(job_dict["id"]),
            "status": v3_status,
            "progress": job_dict.get("progress"),
            "storyboard": job_dict.get("storyboard_data"),
            "scenes": scenes,
            "audio": audio_info,
            "videoUrl": job_dict.get("video_url"),
            "error": job_dict.get("error_message"),
            "estimatedCost": job_dict.get("estimated_cost"),
            "actualCost": job_dict.get("actual_cost"),
            "createdAt": job_dict.get("created_at", ""),
            "updatedAt": job_dict.get("updated_at", ""),
        }

        # Extract comprehensive audio information from job parameters and database
        audio_info = {"status": "not_requested"}

        if "parameters" in job_dict:
            try:
                params = (
                    json.loads(job_dict["parameters"])
                    if isinstance(job_dict["parameters"], str)
                    else job_dict["parameters"]
                )

                # Check for audio info in parameters
                if "audio_info" in params:
                    audio_info = params["audio_info"].copy()
                    audio_info["source"] = "job_parameters"
                elif "audio" in params:
                    audio_info = params["audio"].copy()
                    audio_info["source"] = "legacy_parameters"
                elif params.get("generate_audio", False):
                    # Audio was requested but may not be complete yet
                    audio_info = {
                        "status": "processing"
                        if v3_status in ["scene_generation", "storyboard_processing"]
                        else "requested",
                        "requested": True,
                        "source": "job_parameters",
                    }

                # Enhance with current status info
                if audio_info.get("status") == "completed" and "audio_id" in audio_info:
                    # Verify audio still exists in database
                    audio_record = get_audio_by_id(audio_info["audio_id"])
                    if audio_record:
                        audio_info["verified"] = True
                        audio_info["current_status"] = audio_record.get(
                            "status", "unknown"
                        )
                    else:
                        audio_info["status"] = "missing"
                        audio_info["verified"] = False

            except (json.JSONDecodeError, KeyError, AttributeError) as param_error:
                logger.debug(
                    f"Could not parse audio info from job {job_id} params: {param_error}"
                )
                audio_info["parse_error"] = str(param_error)

        # If audio was requested but no info found, check job metadata
        if (
            audio_info.get("requested", False)
            and audio_info.get("status") == "processing"
        ):
            # Check if audio generation is still in progress
            job_status = job_dict.get("status", "")
            if job_status in ["storyboard_ready", "video_processing", "completed"]:
                audio_info["status"] = "available_but_not_found"
                audio_info["recommendation"] = (
                    "Check job parameters or regenerate audio"
                )

        job_data = {
            "id": str(job_dict["id"]),
            "status": v3_status,
            "progress": job_dict.get("progress", 0.0),
            "storyboard": job_dict.get("storyboard_data"),
            "scenes": scenes or [],  # Ensure scenes is always a list
            "audio": audio_info,  # Comprehensive audio information
            "videoUrl": job_dict.get("video_url"),
            "error": job_dict.get("error_message"),
            "estimatedCost": job_dict.get("estimated_cost", 0.0),
            "actualCost": job_dict.get("actual_cost", None),
            "createdAt": job_dict.get("created_at", ""),
            "updatedAt": job_dict.get("updated_at", job_dict.get("created_at", "")),
        }

        # Handle storyboard data formatting with better error handling
        if job_data["storyboard"]:
            sb_data = job_data["storyboard"]
            if isinstance(sb_data, str):
                try:
                    parsed = json.loads(sb_data)
                    job_data["storyboard"] = (
                        parsed if isinstance(parsed, dict) else {"scenes": parsed}
                    )
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to parse storyboard JSON for job {job_id}: {e}"
                    )
                    job_data["storyboard"] = {"error": "Invalid JSON format"}
            elif isinstance(sb_data, list):
                job_data["storyboard"] = {"scenes": sb_data}
            # If it's already a dict, leave it as-is

        # Add debugging info in development
        if get_settings().ENVIRONMENT == "development":
            job_data["_debug"] = {
                "raw_parameters": str(job_dict.get("parameters", ""))[:200] + "..."
                if len(str(job_dict.get("parameters", ""))) > 200
                else str(job_dict.get("parameters", "")),
                "parameter_parse_success": "parameters" in job_dict,
                "audio_debug": audio_info,
            }

        logger.debug(
            f"Job {job_id} status response prepared: audio status={audio_info.get('status', 'unknown')}"
        )
        return APIResponse.success(data=job_data, meta=create_api_meta())
    except Exception as e:
        import traceback

        traceback.print_exc()
        return APIResponse.create_error(f"Failed to get job status: {str(e)}")


@router.post("/jobs/{job_id}/actions", response_model=APIResponse, tags=["v3-jobs"])
async def perform_job_action(
    job_id: str,
    request: JobActionRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Perform an action on a job (approve, cancel, regenerate)"""
    try:
        job_id_int = int(job_id)

        if request.action == JobAction.APPROVE:
            # Approve storyboard and start video rendering
            success = approve_storyboard(job_id_int)
            if success:
                background_tasks.add_task(render_video_task, job_id_int)
                return APIResponse.success(
                    data={"message": "Storyboard approved, video rendering started"},
                    meta=create_api_meta(),
                )
            else:
                return APIResponse.create_error("Failed to approve storyboard")

        elif request.action == JobAction.CANCEL:
            # Cancel the job by updating status
            update_video_status(job_id_int, "cancelled")
            return APIResponse.success(
                data={"message": "Job cancelled successfully"}, meta=create_api_meta()
            )

        elif request.action == JobAction.REGENERATE_SCENE:
            # Regenerate a specific scene using payload
            payload = request.payload or {}
            scene_id = payload.get("sceneId")

            if not scene_id:
                return APIResponse.create_error(
                    "sceneId is required in payload for REGENERATE_SCENE action"
                )

            scene = get_scene_by_id(scene_id)
            if not scene:
                return APIResponse.create_error(f"Scene not found: {scene_id}")
            if str(scene["jobId"]) != job_id:
                return APIResponse.create_error("Scene does not belong to this job")

            # Get all scenes and job details for regeneration
            all_scenes = get_scenes_by_job(job_id_int)
            job = get_job(job_id_int)
            if not job:
                return APIResponse.create_error("Job not found")

            job_params = (
                json.loads(job["parameters"])
                if isinstance(job["parameters"], str)
                else job["parameters"]
            )
            ad_basics = job_params.get("ad_basics", {})
            creative_direction = job_params.get("creative", {}).get("direction", {})

            # Regenerate scene with optional feedback from payload
            feedback = payload.get("feedback", "")
            constraints = payload.get("constraints", {})

            new_scene = regenerate_scene(
                scene_number=scene["sceneNumber"],
                original_scene=scene,
                all_scenes=all_scenes,
                ad_basics=ad_basics,
                creative_direction=creative_direction,
                feedback=feedback,
                constraints=constraints,
            )

            # Update scene in database
            update_job_scene(
                scene_id=scene_id,
                description=new_scene["description"],
                script=new_scene.get("script"),
                shot_type=new_scene.get("shotType"),
                transition=new_scene.get("transition"),
                duration=new_scene.get("duration"),
                assets=new_scene.get("assets"),
                metadata=new_scene.get("metadata", {}),
            )

            updated_scene = get_scene_by_id(scene_id)
            return APIResponse.success(
                data={
                    "message": "Scene regenerated successfully",
                    "scene": updated_scene,
                },
                meta=create_api_meta(),
            )

        else:
            return APIResponse.create_error(f"Unknown action: {request.action}")

    except Exception as e:
        return APIResponse.create_error(f"Failed to perform job action: {str(e)}")


# ============================================================================
# Cost Estimation Endpoints
# ============================================================================


@router.post("/jobs/dry-run", response_model=APIResponse, tags=["v3-cost"])
async def estimate_job_cost(
    request: DryRunRequest, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Estimate cost for a job without creating it"""
    try:
        # Use ReplicateClient to estimate cost
        replicate_client = ReplicateClient()

        # Estimate cost (simplified: assume 5 images, 30 second video)
        estimated_cost = replicate_client.estimate_cost(num_images=5, video_duration=30)

        estimate = CostEstimate(
            estimatedCost=estimated_cost,
            currency="USD",
            breakdown={
                "storyboard_generation": estimated_cost * 0.3,
                "image_generation": estimated_cost * 0.5,
                "video_rendering": estimated_cost * 0.2,
            },
            validUntil=(
                datetime.utcnow().replace(hour=23, minute=59, second=59)
            ).isoformat()
            + "Z",
        )

        return APIResponse.success(data=estimate.dict(), meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to estimate cost: {str(e)}")


# ============================================================================
# SCENE MANAGEMENT ENDPOINTS (Phase 2.5)
# ============================================================================


@router.get("/jobs/{job_id}/scenes", response_model=APIResponse, tags=["v3-scenes"])
async def list_job_scenes(
    job_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get all scenes for a job"""
    try:
        scenes = get_scenes_by_job(int(job_id))
        return APIResponse.success(data={"scenes": scenes}, meta=create_api_meta())
    except Exception as e:
        logger.error(f"Failed to list scenes: {e}")
        return APIResponse.create_error(f"Failed to list scenes: {str(e)}")


@router.get(
    "/jobs/{job_id}/scenes/{scene_id}", response_model=APIResponse, tags=["v3-scenes"]
)
async def get_scene(
    job_id: str, scene_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get a specific scene by ID"""
    try:
        scene = get_scene_by_id(scene_id)
        if not scene:
            return APIResponse.create_error("Scene not found")

        # Verify scene belongs to the job
        if str(scene["jobId"]) != job_id:
            return APIResponse.create_error("Scene does not belong to this job")

        return APIResponse.success(data=scene, meta=create_api_meta())
    except Exception as e:
        logger.error(f"Failed to get scene: {e}")
        return APIResponse.create_error(f"Failed to get scene: {str(e)}")


@router.put(
    "/jobs/{job_id}/scenes/{scene_id}", response_model=APIResponse, tags=["v3-scenes"]
)
async def update_scene(
    job_id: str,
    scene_id: str,
    request: Dict[str, Any],
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Update a scene's details"""
    try:
        # Verify scene exists and belongs to job
        scene = get_scene_by_id(scene_id)
        if not scene:
            return APIResponse.create_error("Scene not found")
        if str(scene["jobId"]) != job_id:
            return APIResponse.create_error("Scene does not belong to this job")

        # Update scene with provided fields
        success = update_job_scene(
            scene_id=scene_id,
            description=request.get("description"),
            script=request.get("script"),
            shot_type=request.get("shotType"),
            transition=request.get("transition"),
            duration=request.get("duration"),
            assets=request.get("assets"),
            metadata=request.get("metadata"),
        )

        if not success:
            return APIResponse.create_error("Failed to update scene")

        # Get updated scene
        updated_scene = get_scene_by_id(scene_id)
        return APIResponse.success(data=updated_scene, meta=create_api_meta())
    except Exception as e:
        logger.error(f"Failed to update scene: {e}")
        return APIResponse.create_error(f"Failed to update scene: {str(e)}")


@router.post(
    "/jobs/{job_id}/scenes/{scene_id}/regenerate",
    response_model=APIResponse,
    tags=["v3-scenes"],
)
async def regenerate_scene_endpoint(
    job_id: str,
    scene_id: str,
    request: Dict[str, Any],
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """Regenerate a specific scene with optional feedback"""
    try:
        # Get current scene
        scene = get_scene_by_id(scene_id)
        if not scene:
            return APIResponse.create_error("Scene not found")
        if str(scene["jobId"]) != job_id:
            return APIResponse.create_error("Scene does not belong to this job")

        # Get all scenes for context
        all_scenes = get_scenes_by_job(int(job_id))

        # Get job details for ad basics and creative direction
        job = get_job(int(job_id))
        if not job:
            return APIResponse.create_error("Job not found")

        job_params = (
            json.loads(job["parameters"])
            if isinstance(job["parameters"], str)
            else job["parameters"]
        )
        ad_basics = job_params.get("ad_basics", {})
        creative_direction = job_params.get("creative", {}).get("direction", {})

        # Regenerate scene with AI
        feedback = request.get("feedback", "")
        constraints = request.get("constraints", {})

        new_scene = regenerate_scene(
            scene_number=scene["sceneNumber"],
            original_scene=scene,
            all_scenes=all_scenes,
            ad_basics=ad_basics,
            creative_direction=creative_direction,
            feedback=feedback,
            constraints=constraints,
        )

        # Update scene in database
        update_job_scene(
            scene_id=scene_id,
            description=new_scene["description"],
            script=new_scene.get("script"),
            shot_type=new_scene.get("shotType"),
            transition=new_scene.get("transition"),
            duration=new_scene.get("duration"),
            assets=new_scene.get("assets"),
            metadata=new_scene.get("metadata", {}),
        )

        # Get updated scene
        updated_scene = get_scene_by_id(scene_id)
        return APIResponse.success(data=updated_scene, meta=create_api_meta())
    except SceneGenerationError as e:
        logger.error(f"Failed to regenerate scene: {e}")
        return APIResponse.create_error(f"Failed to regenerate scene: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to regenerate scene: {e}")
        return APIResponse.create_error(f"Failed to regenerate scene: {str(e)}")


@router.delete(
    "/jobs/{job_id}/scenes/{scene_id}", response_model=APIResponse, tags=["v3-scenes"]
)
async def delete_scene(
    job_id: str, scene_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete a scene"""
    try:
        # Verify scene exists and belongs to job
        scene = get_scene_by_id(scene_id)
        if not scene:
            return APIResponse.create_error("Scene not found")
        if str(scene["jobId"]) != job_id:
            return APIResponse.create_error("Scene does not belong to this job")

        # Delete scene
        success = delete_job_scene(scene_id)
        if not success:
            return APIResponse.create_error("Failed to delete scene")

        return APIResponse.success(
            data={"message": "Scene deleted successfully"}, meta=create_api_meta()
        )
    except Exception as e:
        logger.error(f"Failed to delete scene: {e}")
        return APIResponse.create_error(f"Failed to delete scene: {str(e)}")


# ============================================================================
# IMAGE PAIR SELECTION & VIDEO GENERATION ENDPOINTS (New Feature)
# ============================================================================


@router.post("/jobs/from-image-pairs", response_model=APIResponse, tags=["v3-jobs"])
async def create_job_from_image_pairs(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """
    Create a new job that selects image pairs from campaign assets and generates videos.

    Workflow:
    1. Fetch campaign assets (images only)
    2. Use xAI Grok to select optimal image pairs
    3. Create main job with status "image_pair_selection"
    4. Store selected pairs in job parameters
    5. Trigger parallel video generation for all pairs
    6. Return job ID for polling

    Request body:
    {
        "campaignId": "campaign-uuid",
        "clientId": "client-uuid" (optional),
        "clipDuration": 5.0 (optional, seconds per clip),
        "numPairs": 10 (optional, target number of pairs)
    }
    """
    from ...services.xai_client import XAIClient
    from ...services.sub_job_orchestrator import process_image_pairs_to_videos
    from ...database_helpers import list_assets, get_campaign_by_id, get_client_by_id

    try:
        campaign_id = request.get("campaignId")
        client_id = request.get("clientId")
        clip_duration = request.get("clipDuration")
        num_pairs = request.get("numPairs")

        if not campaign_id:
            return APIResponse.create_error("campaignId is required")

        # Fetch campaign assets (images only)
        assets = list_assets(
            user_id=None,  # Allow access to all campaigns
            campaign_id=campaign_id,
            asset_type="image",
            limit=1000,
            offset=0,
        )

        if len(assets) < 2:
            return APIResponse.create_error(
                f"Need at least 2 image assets, but campaign has {len(assets)}"
            )

        logger.info(f"Found {len(assets)} image assets for campaign {campaign_id}")

        # Get campaign context for AI selection
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        campaign_context = None
        if campaign:
            campaign_context = {
                "goal": campaign.get("goal"),
                "name": campaign.get("name"),
            }

        # Get client brand guidelines if available
        brand_guidelines = None
        if client_id:
            client = get_client_by_id(client_id, current_user["id"])
            if client and client.get("brandGuidelines"):
                brand_guidelines = client["brandGuidelines"]

        # Update job status
        job_id = create_video_job(
            prompt=f"Image pair selection and video generation for campaign {campaign_id}",
            model_id="image-pair-workflow",
            parameters={
                "campaign_id": campaign_id,
                "client_id": client_id,
                "clip_duration": clip_duration,
                "num_pairs": num_pairs,
            },
            estimated_cost=0.0,  # Will be calculated during generation
            client_id=client_id,
            status="image_pair_selection",
        )

        logger.info(f"Created job {job_id} for image pair workflow")

        # Use xAI Grok to select image pairs
        xai_client = XAIClient()

        # Prepare asset data for Grok
        logger.info(f"[IMAGE PAIRING] Preparing asset data for {len(assets)} images")

        # Also write to persistent file for debugging
        debug_log_path = "/tmp/image_pairing_debug.log"
        with open(debug_log_path, "a") as debug_file:
            debug_file.write(f"\n{'='*80}\n")
            debug_file.write(f"NEW JOB - Campaign: {campaign_id}\n")
            debug_file.write(f"Timestamp: {__import__('datetime').datetime.now().isoformat()}\n")
            debug_file.write(f"Total assets: {len(assets)}\n")
            debug_file.write(f"{'='*80}\n\n")

        asset_data = []
        for i, asset in enumerate(assets):
            # Parse tags if they're stored as JSON string
            tags = getattr(asset, "tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            elif tags is None:
                tags = []

            # Create meaningful description from available metadata
            name = getattr(asset, "name", "")
            description_parts = [name]
            if tags:
                description_parts.append(f"Tags: {', '.join(tags)}")
            description = " | ".join(description_parts) if description_parts else "No description"

            asset_dict = {
                "id": asset.id,
                "name": name,
                "description": description,
                "tags": tags,
                "type": "image",
                "url": getattr(asset, "url", ""),
            }
            asset_data.append(asset_dict)

            # Log each asset being sent to Grok
            logger.info(
                f"[IMAGE PAIRING] Asset {i+1}/{len(assets)}: "
                f"id={asset.id[:12]}... name='{name}' tags={tags}"
            )

            # Write to debug file
            with open(debug_log_path, "a") as debug_file:
                debug_file.write(f"Asset {i+1}/{len(assets)}:\n")
                debug_file.write(f"  ID: {asset.id}\n")
                debug_file.write(f"  Name: {name}\n")
                debug_file.write(f"  Tags: {tags}\n")
                debug_file.write(f"  Description: {description}\n\n")

        # Log summary of asset data
        logger.info(
            f"[IMAGE PAIRING] Asset data summary: "
            f"{len(asset_data)} assets with tags={sum(1 for a in asset_data if a['tags'])}"
        )

        try:
            image_pairs = xai_client.select_image_pairs(
                assets=asset_data,
                campaign_context=campaign_context,
                client_brand_guidelines=brand_guidelines,
                num_pairs=num_pairs,
            )
        except Exception as e:
            logger.error(f"Image pair selection failed: {e}")
            update_video_status(job_id, "failed", metadata={"error": str(e)})
            return APIResponse.create_error(f"Image pair selection failed: {str(e)}")

        # Store selected pairs in job parameters
        from ...database import get_job, update_job_progress

        job = get_job(job_id)
        if job:
            params = (
                json.loads(job["parameters"])
                if isinstance(job["parameters"], str)
                else job["parameters"]
            )
            params["selected_pairs"] = [
                {
                    "image1_id": pair[0],
                    "image2_id": pair[1],
                    "score": pair[2],
                    "reasoning": pair[3],
                }
                for pair in image_pairs
            ]
            update_job_progress(job_id, {"selected_pairs": len(image_pairs)})

        logger.info(f"Selected {len(image_pairs)} image pairs for job {job_id}")

        # Launch parallel video generation in background
        async def run_orchestration():
            try:
                await process_image_pairs_to_videos(job_id, image_pairs, clip_duration)
            except Exception as e:
                logger.error(f"Orchestration failed for job {job_id}: {e}")
                update_video_status(job_id, "failed", metadata={"error": str(e)})

        # Schedule orchestration in background
        import asyncio

        asyncio.create_task(run_orchestration())

        # Return job ID immediately for polling
        return APIResponse.success(
            data={
                "jobId": str(job_id),
                "status": "image_pair_selection",
                "totalPairs": len(image_pairs),
                "message": f"Job created with {len(image_pairs)} image pairs. Video generation started.",
            },
            meta=create_api_meta(),
        )

    except Exception as e:
        logger.error(f"Failed to create job from image pairs: {e}", exc_info=True)
        return APIResponse.create_error(f"Failed to create job: {str(e)}")


@router.post("/jobs/from-property-photos", response_model=APIResponse, tags=["v3-jobs"])
async def create_job_from_property_photos(
    request: PropertyVideoRequest,
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """
    Create video generation job from luxury lodging property photos.

    This endpoint uses AI (Grok) to intelligently select 7 image pairs
    from crawled property photos based on predefined scene types for
    luxury hospitality marketing videos (35 seconds total, 5s per scene).

    Workflow:
    1. Call Grok to analyze all photos and select optimal pairs per scene type
    2. Store photos as assets in the campaign
    3. Create video job with 7 sub-jobs (one per scene)
    4. Launch parallel video generation
    5. Return job ID for progress tracking

    Args:
        request: PropertyVideoRequest with property info and photos
        current_user: Authenticated user from API key

    Returns:
        APIResponse with job details and Grok's selection metadata
    """
    from ...services.property_photo_selector import PropertyPhotoSelector
    from ...services.sub_job_orchestrator import process_image_pairs_to_videos
    from ...database_helpers import create_asset, get_campaign_by_id, get_client_by_id

    try:
        logger.info(
            f"Creating property video job for '{request.propertyInfo.name}' "
            f"with {len(request.photos)} photos"
        )

        # Validate campaign exists
        campaign = get_campaign_by_id(request.campaignId, current_user["id"])
        if not campaign:
            return APIResponse.create_error(f"Campaign not found: {request.campaignId}")

        # Initialize property photo selector
        selector = PropertyPhotoSelector()

        # Convert Pydantic models to dicts for selector
        property_info_dict = request.propertyInfo.model_dump()
        photos_dict = [photo.model_dump() for photo in request.photos]

        # Call Grok to select scene-based image pairs
        logger.info(f"Calling Grok to select scene pairs...")
        selection_result = selector.select_scene_image_pairs(
            property_info=property_info_dict, photos=photos_dict
        )

        logger.info(
            f"Grok selected {len(selection_result['scene_pairs'])} scene pairs "
            f"with confidence {selection_result.get('selection_metadata', {}).get('selection_confidence', 'unknown')}"
        )

        # Store photos as assets in the database
        logger.info(f"Storing {len(request.photos)} photos as assets...")
        photo_id_to_asset_id = {}

        for photo in request.photos:
            # Create asset record (photo URL will be used for video generation)
            asset_id = create_asset(
                user_id=current_user["id"],
                name=photo.filename or f"{request.propertyInfo.name}_{photo.id}",
                asset_type="image",
                url=photo.url,
                format="jpg",  # Default, can be enhanced
                client_id=campaign.get("clientId"),
                campaign_id=request.campaignId,
                tags=photo.tags or [],
                metadata={
                    "dominant_colors": photo.dominantColors or [],
                    "detected_objects": photo.detectedObjects or [],
                    "composition": photo.composition,
                    "lighting": photo.lighting,
                    "property_name": request.propertyInfo.name,
                    "property_type": request.propertyInfo.propertyType,
                },
            )
            photo_id_to_asset_id[photo.id] = asset_id

        logger.info(f"Created {len(photo_id_to_asset_id)} asset records")

        # Convert selection result to video generation format
        # Map photo IDs to asset IDs
        image_pairs = []
        for scene_pair in selection_result["scene_pairs"]:
            first_photo_id = scene_pair["first_image"]["id"]
            last_photo_id = scene_pair["last_image"]["id"]

            first_asset_id = photo_id_to_asset_id.get(first_photo_id)
            last_asset_id = photo_id_to_asset_id.get(last_photo_id)

            if not first_asset_id or not last_asset_id:
                logger.warning(
                    f"Scene {scene_pair['scene_number']}: Could not map photo IDs to assets, skipping"
                )
                continue

            score = (
                scene_pair.get("transition_analysis", {}).get(
                    "interpolation_confidence", 8.0
                )
                / 10.0
            )

            reasoning = (
                f"Scene {scene_pair['scene_number']}: {scene_pair['scene_type']}. "
                f"{scene_pair['first_image'].get('reasoning', '')} → "
                f"{scene_pair['last_image'].get('reasoning', '')}"
            )

            image_pairs.append((first_asset_id, last_asset_id, score, reasoning))

        if len(image_pairs) != 7:
            logger.warning(
                f"Expected 7 image pairs, got {len(image_pairs)}. "
                "Video may be shorter than expected."
            )

        # Create video job
        from ...database import create_video_job, update_video_status

        job_id = create_video_job(
            user_id=current_user["id"],
            prompt=f"Luxury lodging video for {request.propertyInfo.name}",
            duration=35.0,  # 7 scenes * 5 seconds
            parameters={
                "property_info": property_info_dict,
                "campaign_id": request.campaignId,
                "video_model": request.videoModel,
                "clip_duration": request.clipDuration,
                "selection_metadata": selection_result.get("selection_metadata", {}),
                "scene_pairs": selection_result["scene_pairs"],
            },
        )

        logger.info(f"Created job {job_id} for property '{request.propertyInfo.name}'")

        # Update status to indicate AI selection complete
        update_video_status(job_id, "image_pair_selection")

        # Launch parallel video generation in background
        async def run_orchestration():
            try:
                await process_image_pairs_to_videos(
                    job_id, image_pairs, request.clipDuration
                )
            except Exception as e:
                logger.error(f"Orchestration failed for job {job_id}: {e}")
                update_video_status(job_id, "failed", metadata={"error": str(e)})

        # Schedule orchestration in background
        import asyncio

        asyncio.create_task(run_orchestration())

        # Return job details with Grok's selection metadata
        return APIResponse.success(
            data={
                "jobId": job_id,
                "status": "image_pair_selection",
                "propertyName": request.propertyInfo.name,
                "totalScenes": len(image_pairs),
                "selectionMetadata": selection_result.get("selection_metadata", {}),
                "scenePairs": selection_result["scene_pairs"],
                "message": f"Job created with {len(image_pairs)} scene pairs. Video generation started.",
            },
            meta=create_api_meta(),
        )

    except Exception as e:
        logger.error(f"Failed to create property video job: {e}", exc_info=True)
        return APIResponse.create_error(
            f"Failed to create property video job: {str(e)}"
        )


@router.get("/jobs/{job_id}/sub-jobs", response_model=APIResponse, tags=["v3-jobs"])
async def get_job_sub_jobs(
    job_id: str, current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """
    Get all sub-jobs for a job with their individual status.

    This endpoint provides detailed progress tracking for parallel video generation.

    Returns:
    {
        "data": {
            "subJobs": [...],  // Array of SubJob objects
            "summary": {
                "total": 10,
                "pending": 2,
                "processing": 3,
                "completed": 4,
                "failed": 1
            }
        }
    }
    """
    from ...database import get_sub_jobs_by_job, get_sub_job_progress_summary

    try:
        job_id_int = int(job_id)

        # Get all sub-jobs
        sub_jobs = get_sub_jobs_by_job(job_id_int)

        # Get summary
        summary = get_sub_job_progress_summary(job_id_int)

        return APIResponse.success(
            data={"subJobs": sub_jobs, "summary": summary}, meta=create_api_meta()
        )

    except ValueError:
        return APIResponse.create_error("Invalid job ID format")
    except Exception as e:
        logger.error(f"Failed to get sub-jobs for job {job_id}: {e}")
        return APIResponse.create_error(f"Failed to get sub-jobs: {str(e)}")


# ============================================================================
# VIDEO SERVING ENDPOINTS
# ============================================================================


@router.get("/videos/{job_id}/clips/{clip_filename}", tags=["v3-videos"])
async def get_video_clip(job_id: str, clip_filename: str):
    """Serve individual video clips from storage"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    try:
        video_path = Path(settings.VIDEO_STORAGE_PATH) / job_id / "clips" / clip_filename

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video clip not found")

        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=31536000",
            },
        )
    except Exception as e:
        logger.error(f"Failed to serve video clip {clip_filename} for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve video: {str(e)}")


@router.get("/videos/{job_id}/combined", tags=["v3-videos"])
async def get_combined_video(job_id: str):
    """Serve combined video from database blob storage"""
    from fastapi.responses import Response
    from ...database import get_db

    try:
        # Get video blob from database
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT video_data
                FROM generated_videos
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()

            if not row or not row["video_data"]:
                raise HTTPException(status_code=404, detail="Combined video not found")

            video_data = row["video_data"]

        return Response(
            content=video_data,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=31536000",
                "Content-Length": str(len(video_data)),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve combined video for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve video: {str(e)}")


@router.get("/ai-videos", response_model=APIResponse, tags=["v3-jobs"])
async def list_ai_generated_videos(
    limit: int = 20,
    offset: int = 0,
    status: str = "completed",
    current_user: Dict = Depends(verify_auth),
) -> APIResponse:
    """
    List AI-generated videos from the image pair selection pipeline.

    Query parameters:
    - limit: Number of videos to return (default: 20, max: 100)
    - offset: Pagination offset (default: 0)
    - status: Filter by status (default: "completed", options: "all", "completed", "processing", "failed")

    Returns:
    {
        "data": {
            "videos": [...],  // Array of video records
            "total": 42       // Total count matching filter
        }
    }
    """
    from ...database import get_db

    try:
        # Validate and limit pagination
        limit = min(limit, 100)
        offset = max(offset, 0)

        with get_db() as conn:
            # Build query based on status filter
            where_clause = "WHERE status = ?" if status != "all" else ""
            params = [status] if status != "all" else []

            # Get total count
            count_query = f"""
                SELECT COUNT(*) FROM video_sub_jobs {where_clause}
            """
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Get videos with pagination
            query = f"""
                SELECT
                    id,
                    job_id,
                    sub_job_number,
                    model_id,
                    video_url,
                    status,
                    duration_seconds,
                    progress,
                    error_message,
                    created_at,
                    completed_at,
                    input_parameters
                FROM video_sub_jobs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor = conn.execute(query, params)

            videos = []
            for row in cursor.fetchall():
                try:
                    input_params = json.loads(row[11]) if row[11] else {}
                except json.JSONDecodeError:
                    logger.warning(
                        f"Invalid JSON in input_parameters for sub-job {row[0]}"
                    )
                    input_params = {}

                # Handle potential None values
                safe_row = [r if r is not None else "" for r in row]

                video_record = {
                    "id": str(safe_row[0]),
                    "jobId": safe_row[1],
                    "subJobNumber": safe_row[2],
                    "modelId": safe_row[3] or "unknown",
                    "videoUrl": safe_row[4] or "",
                    "status": safe_row[5] or "unknown",
                    "durationSeconds": safe_row[6] or 0.0,
                    "progress": safe_row[7] or 0.0,
                    "errorMessage": safe_row[8],
                    "createdAt": safe_row[9] or "",
                    "completedAt": safe_row[10] or "",
                    "prompt": input_params.get(
                        "prompt", f"Job {safe_row[1]} - Clip {safe_row[2]}"
                    ),
                    "thumbnailUrl": safe_row[4]
                    or "",  # Use video URL as thumbnail for now
                    "assetIds": input_params.get(
                        "asset_ids", []
                    ),  # Include source assets
                }

                # Add audio info if available in parameters
                if "audio_info" in input_params:
                    video_record["audioInfo"] = input_params["audio_info"]

                videos.append(video_record)

            logger.info(
                f"Retrieved {len(videos)} AI videos for offset {offset}, limit {limit}"
            )

            return APIResponse.success(
                data={"videos": videos, "total": total}, meta=create_api_meta()
            )

    except Exception as e:
        logger.error(f"Failed to list AI-generated videos: {e}", exc_info=True)
        return APIResponse.create_error(f"Failed to list AI-generated videos: {str(e)}")
