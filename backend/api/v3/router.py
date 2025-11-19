"""
FastAPI router for v3 API endpoints.

This router provides a simplified, frontend-aligned API that matches
the data requirements of the Next.js frontend with proper Pydantic models.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, cast
from datetime import datetime
import json
import uuid

from .models import (
    APIResponse, Client, ClientCreateRequest, ClientUpdateRequest,
    Campaign, CampaignCreateRequest, CampaignUpdateRequest,
    Job, JobCreateRequest, JobActionRequest, JobStatus, JobAction,
    CostEstimate, DryRunRequest, Asset, UploadAssetInput
)
from ...schemas.assets import UploadAssetFromUrlInput
from ...database_helpers import (
    create_client, get_client_by_id, list_clients, update_client, delete_client, get_client_stats,
    create_campaign, get_campaign_by_id, list_campaigns, update_campaign, delete_campaign, get_campaign_stats,
    create_asset, get_asset_by_id, list_assets, update_asset, delete_asset
)
from ...auth import verify_auth
from ...services.storyboard_generator import generate_storyboard_task
from ...services.video_renderer import render_video_task
from ...services.replicate_client import ReplicateClient
from ...services.asset_downloader import (
    download_asset_from_url, store_blob, AssetDownloadError
)
from ...database import (
    get_job, update_job_progress, approve_storyboard,
    create_video_job, update_video_status
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


def create_api_meta(page: Optional[int] = None, total: Optional[int] = None) -> Dict[str, Any]:
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
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get all clients for the authenticated user"""
    try:
        clients = list_clients(current_user["id"], limit=limit, offset=offset)
        meta = create_api_meta(page=(offset // limit) + 1, total=len(clients))
        return APIResponse.success(data=clients, meta=meta)
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch clients: {str(e)}")


@router.get("/clients/{client_id}", response_model=APIResponse, tags=["v3-clients"])
async def get_client(
    client_id: str,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get a specific client by ID"""
    try:
        client = get_client_by_id(client_id, current_user["id"])
        if not client:
            return APIResponse.create_error("Client not found")

        return APIResponse.success(data=client, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch client: {str(e)}")


@router.post("/clients", response_model=APIResponse, tags=["v3-clients"])
async def create_new_client(
    request: ClientCreateRequest,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Create a new client"""
    try:
        client_id = create_client(
            user_id=current_user["id"],
            name=request.name,
            description=request.description or "",
            brand_guidelines=request.brandGuidelines.dict() if request.brandGuidelines else None
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
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Update an existing client"""
    try:
        success = update_client(
            client_id=client_id,
            user_id=current_user["id"],
            name=request.name,
            description=request.description,
            brand_guidelines=request.brandGuidelines.dict() if request.brandGuidelines else None
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
    client_id: str,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete a client"""
    try:
        success = delete_client(client_id, current_user["id"])
        if not success:
            return APIResponse.create_error("Client not found")

        return APIResponse.success(data={"message": "Client deleted successfully"}, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to delete client: {str(e)}")


@router.get("/clients/{client_id}/stats", response_model=APIResponse, tags=["v3-clients"])
async def get_client_statistics(
    client_id: str,
    current_user: Dict = Depends(verify_auth)
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
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get campaigns, optionally filtered by client"""
    try:
        campaigns = list_campaigns(
            user_id=current_user["id"],
            client_id=client_id,
            limit=limit,
            offset=offset
        )
        meta = create_api_meta(page=(offset // limit) + 1, total=len(campaigns))
        return APIResponse.success(data=campaigns, meta=meta)
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch campaigns: {str(e)}")


@router.get("/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"])
async def get_campaign(
    campaign_id: str,
    current_user: Dict = Depends(verify_auth)
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
    request: CampaignCreateRequest,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Create a new campaign"""
    try:
        campaign_id = create_campaign(
            user_id=current_user["id"],
            client_id=request.clientId,
            name=request.name,
            goal=request.goal,
            status=request.status,
            brief=request.brief
        )

        # Fetch the created campaign
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        return APIResponse.success(data=campaign, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to create campaign: {str(e)}")


@router.put("/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"])
async def update_existing_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Update an existing campaign"""
    try:
        success = update_campaign(
            campaign_id=campaign_id,
            user_id=current_user["id"],
            name=request.name,
            goal=request.goal,
            status=request.status,
            brief=request.brief
        )

        if not success:
            return APIResponse.create_error("Campaign not found or update failed")

        # Fetch the updated campaign
        campaign = get_campaign_by_id(campaign_id, current_user["id"])
        return APIResponse.success(data=campaign, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to update campaign: {str(e)}")


@router.delete("/campaigns/{campaign_id}", response_model=APIResponse, tags=["v3-campaigns"])
async def delete_existing_campaign(
    campaign_id: str,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Delete a campaign"""
    try:
        success = delete_campaign(campaign_id, current_user["id"])
        if not success:
            return APIResponse.create_error("Campaign not found")

        return APIResponse.success(data={"message": "Campaign deleted successfully"}, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to delete campaign: {str(e)}")


@router.get("/campaigns/{campaign_id}/stats", response_model=APIResponse, tags=["v3-campaigns"])
async def get_campaign_statistics(
    campaign_id: str,
    current_user: Dict = Depends(verify_auth)
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
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Get assets with optional filtering"""
    try:
        assets = list_assets(
            user_id=current_user["id"],
            client_id=client_id,
            campaign_id=campaign_id,
            asset_type=asset_type,
            limit=limit,
            offset=offset
        )
        meta = create_api_meta(page=(offset // limit) + 1, total=len(assets))
        return APIResponse.success(data=assets, meta=meta)
    except Exception as e:
        return APIResponse.create_error(f"Failed to fetch assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=APIResponse, tags=["v3-assets"])
async def get_asset(
    asset_id: str,
    current_user: Dict = Depends(verify_auth)
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
    current_user: Dict = Depends(verify_auth)
):
    """Serve the binary asset data"""
    from fastapi.responses import Response
    from ...database_helpers import get_db

    try:
        # Query asset directly from database to get blob_id and blob_data
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT blob_id, blob_data, format, name
                FROM assets
                WHERE id = ?
                """,
                (asset_id,)
            ).fetchone()

            if not row:
                return APIResponse.create_error("Asset not found", status_code=404)

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
                        "Cache-Control": "public, max-age=31536000"
                    }
                )

        # Fallback to blob_data column (legacy storage)
        if blob_data:
            # Determine content type from format
            format_to_mime = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp", "gif": "image/gif",
                "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
                "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
                "pdf": "application/pdf"
            }

            content_type = format_to_mime.get(asset_format.lower(), "application/octet-stream")

            return Response(
                content=bytes(blob_data),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{asset_name}"',
                    "Cache-Control": "public, max-age=31536000"
                }
            )

        # No binary data available
        return APIResponse.create_error("Asset data not available", status_code=404)

    except Exception as e:
        return APIResponse.create_error(f"Failed to serve asset data: {str(e)}")


@router.post("/assets", response_model=APIResponse, tags=["v3-assets"])
async def upload_asset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    type: Optional[str] = None,
    clientId: Optional[str] = None,
    campaignId: Optional[str] = None,
    tags: Optional[str] = None,  # JSON string
    current_user: Dict = Depends(verify_auth)
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
        format_ext = filename.split('.')[-1] if '.' in filename else 'bin'

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
            blob_data=file_content
        )

        # Fetch the created asset
        asset = get_asset_by_id(asset_id)
        return APIResponse.success(data=asset, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to upload asset: {str(e)}")


@router.post("/assets/from-url", response_model=APIResponse, tags=["v3-assets"])
async def upload_asset_from_url(
    request: UploadAssetFromUrlInput,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Upload an asset by downloading it from a URL"""
    try:
        # Download asset from URL
        asset_data, content_type, metadata = download_asset_from_url(
            url=request.url,
            asset_type=request.type
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
            duration=metadata.get("duration")
        )

        # Fetch the created asset
        asset = get_asset_by_id(asset_id)
        return APIResponse.success(data=asset, meta=create_api_meta())
    except AssetDownloadError as e:
        return APIResponse.create_error(f"Failed to download asset: {str(e)}", status_code=400)
    except Exception as e:
        return APIResponse.create_error(f"Failed to upload asset from URL: {str(e)}")


@router.delete("/assets/{asset_id}", response_model=APIResponse, tags=["v3-assets"])
async def delete_asset_v3(
    asset_id: str,
    current_user: Dict = Depends(verify_auth)
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
            data={"message": "Asset deleted successfully"},
            meta=create_api_meta()
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
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Create a new generation job"""
    try:
        # Build prompt from request data
        prompt = f"""
        Product: {request.adBasics.product}
        Target Audience: {request.adBasics.targetAudience}
        Key Message: {request.adBasics.keyMessage}
        Call to Action: {request.adBasics.callToAction}
        Style: {request.creative.direction.style}
        """

        # Create job using existing video job function
        job_id = create_video_job(
            prompt=prompt,
            model_id="v3-job",  # Placeholder model
            parameters={
                "context": request.context.dict(),
                "ad_basics": request.adBasics.dict(),
                "creative": request.creative.dict(),
                "advanced": request.advanced.dict() if request.advanced else None
            },
            estimated_cost=5.0,  # Placeholder cost
            client_id=request.context.clientId,
            status="pending"
        )

        # Start background storyboard generation
        background_tasks.add_task(generate_storyboard_task, job_id)

        # Return job info
        job = {
            "id": str(job_id),
            "status": JobStatus.PENDING,
            "createdAt": get_current_timestamp(),
            "updatedAt": get_current_timestamp()
        }

        return APIResponse.success(data=job, meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=APIResponse, tags=["v3-jobs"])
async def get_job_status(
    job_id: str,
    current_user: Dict = Depends(verify_auth)
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
            "cancelled": JobStatus.CANCELLED
        }

        # Default to FAILED if unknown status
        v3_status = status_mapping.get(job_dict["status"] if "status" in job_dict else "failed", JobStatus.FAILED)

        job_data = {
            "id": str(job_dict["id"]),
            "status": v3_status,
            "progress": job_dict["progress"] if "progress" in job_dict else None,
            "storyboard": job_dict["storyboard_data"] if "storyboard_data" in job_dict and isinstance(job_dict["storyboard_data"], dict) else None,
            "videoUrl": job_dict["video_url"] if "video_url" in job_dict else None,
            "error": job_dict["error_message"] if "error_message" in job_dict else None,
            "estimatedCost": job_dict["estimated_cost"] if "estimated_cost" in job_dict else None,
            "actualCost": job_dict["actual_cost"] if "actual_cost" in job_dict else None,
            "createdAt": job_dict["created_at"],
            "updatedAt": job_dict["updated_at"]
        }
        
        # Handle storyboard data loading if it's a string/list from DB
        if "storyboard_data" in job_dict and job_dict["storyboard_data"]:
             sb_data = job_dict["storyboard_data"]
             if isinstance(sb_data, str):
                 try:
                     job_data["storyboard"] = json.loads(sb_data)
                 except:
                     job_data["storyboard"] = None
             elif isinstance(sb_data, list):
                 # Wrap list in dict if frontend expects dict, or just pass list
                 # Based on models.py Job model, storyboard is Optional[Dict[str, Any]]
                 # But v2 storyboard is a List. Let's wrap it to be safe or check frontend expectations.
                 # Looking at prompt, frontend expects: storyboard: [{ image_url, description, scene_idx }]
                 # But model says Dict. Let's assume we pass it as a dict wrapper key
                 job_data["storyboard"] = {"scenes": sb_data}

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
    current_user: Dict = Depends(verify_auth)
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
                    meta=create_api_meta()
                )
            else:
                return APIResponse.create_error("Failed to approve storyboard")

        elif request.action == JobAction.CANCEL:
            # Cancel the job by updating status
            update_video_status(job_id_int, "cancelled")
            return APIResponse.success(
                data={"message": "Job cancelled successfully"},
                meta=create_api_meta()
            )

        elif request.action == JobAction.REGENERATE_SCENE:
            # Regenerate a specific scene (not implemented in v1, placeholder)
            return APIResponse.create_error("Scene regeneration not yet implemented")

        else:
            return APIResponse.create_error(f"Unknown action: {request.action}")

    except Exception as e:
        return APIResponse.create_error(f"Failed to perform job action: {str(e)}")


# ============================================================================
# Cost Estimation Endpoints
# ============================================================================

@router.post("/jobs/dry-run", response_model=APIResponse, tags=["v3-cost"])
async def estimate_job_cost(
    request: DryRunRequest,
    current_user: Dict = Depends(verify_auth)
) -> APIResponse:
    """Estimate cost for a job without creating it"""
    try:
        # Use ReplicateClient to estimate cost
        replicate_client = ReplicateClient()

        # Estimate cost (simplified: assume 5 images, 30 second video)
        estimated_cost = replicate_client.estimate_cost(
            num_images=5,
            video_duration=30
        )

        estimate = CostEstimate(
            estimatedCost=estimated_cost,
            currency="USD",
            breakdown={
                "storyboard_generation": estimated_cost * 0.3,
                "image_generation": estimated_cost * 0.5,
                "video_rendering": estimated_cost * 0.2
            },
            validUntil=(datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + "Z"
        )

        return APIResponse.success(data=estimate.dict(), meta=create_api_meta())
    except Exception as e:
        return APIResponse.create_error(f"Failed to estimate cost: {str(e)}")