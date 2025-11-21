"""Database helper functions for Clients and Campaigns management.

This module provides CRUD operations for:
- Clients (brand/client management with brand guidelines)
- Client Assets (logos, brand documents)
- Campaigns (marketing campaigns linked to clients)
- Campaign Assets (campaign-specific media)
- Assets (consolidated asset management with Pydantic models)
"""

import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager
from pathlib import Path
import os
from datetime import datetime

# Import Pydantic asset models
from .schemas.assets import (
    Asset,
    AssetDB,
    ImageAsset,
    VideoAsset,
    AudioAsset,
    DocumentAsset,
)

# Get data directory from environment variable, default to ./DATA
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DB_PATH = DATA_DIR / "scenes.db"


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============================================================================
# CLIENT CRUD OPERATIONS
# ============================================================================


def create_client(
    user_id: int,
    name: str,
    description: str = "",
    homepage: Optional[str] = None,
    brand_guidelines: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new client."""
    client_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO clients (id, user_id, name, description, homepage, brand_guidelines, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                user_id,
                name,
                description,
                homepage,
                json.dumps(brand_guidelines) if brand_guidelines else None,
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        return client_id


def get_client_by_id(client_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a client by ID (user must own the client)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ? AND user_id = ?", (client_id, user_id)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "homepage": row["homepage"],
                "brandGuidelines": json.loads(row["brand_guidelines"])
                if row["brand_guidelines"]
                else None,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
    return None


def list_clients(
    user_id: int, limit: int = 100, offset: int = 0
) -> List[Dict[str, Any]]:
    """List all clients for a user."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM clients
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "homepage": row["homepage"],
                "brandGuidelines": json.loads(row["brand_guidelines"])
                if row["brand_guidelines"]
                else None,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]


def update_client(
    client_id: str,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    homepage: Optional[str] = None,
    brand_guidelines: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Update a client (partial update)."""
    with get_db() as conn:
        # Build dynamic update query
        update_fields = []
        values = []

        if name is not None:
            update_fields.append("name = ?")
            values.append(name)

        if description is not None:
            update_fields.append("description = ?")
            values.append(description)

        if homepage is not None:
            update_fields.append("homepage = ?")
            values.append(homepage)

        if brand_guidelines is not None:
            update_fields.append("brand_guidelines = ?")
            values.append(json.dumps(brand_guidelines))

        if metadata is not None:
            update_fields.append("metadata = ?")
            values.append(json.dumps(metadata))

        if not update_fields:
            return False  # Nothing to update

        # Add WHERE clause values
        values.extend([client_id, user_id])

        query = f"""
            UPDATE clients
            SET {", ".join(update_fields)}
            WHERE id = ? AND user_id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_client(client_id: str, user_id: int) -> bool:
    """Delete a client (cascades to campaigns and assets)."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM clients WHERE id = ? AND user_id = ?", (client_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_client_stats(client_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get statistics for a client."""
    with get_db() as conn:
        # Verify ownership
        client = conn.execute(
            "SELECT id FROM clients WHERE id = ? AND user_id = ?", (client_id, user_id)
        ).fetchone()

        if not client:
            return None

        # Get campaign count
        campaign_count_row = conn.execute(
            "SELECT COUNT(*) as count FROM campaigns WHERE client_id = ?", (client_id,)
        ).fetchone()
        campaign_count = campaign_count_row["count"] if campaign_count_row else 0

        # Get video count and total spend
        video_stats_row = conn.execute(
            """
            SELECT
                COUNT(v.id) as video_count,
                COALESCE(SUM(v.actual_cost), 0) as total_spend
            FROM campaigns c
            LEFT JOIN generated_videos v ON v.campaign_id = c.id
            WHERE c.client_id = ?
            """,
            (client_id,),
        ).fetchone()

        video_count = video_stats_row["video_count"] if video_stats_row else 0
        total_spend = video_stats_row["total_spend"] if video_stats_row else 0.0

        return {
            "campaignCount": campaign_count,
            "videoCount": video_count,
            "totalSpend": float(total_spend),
        }


# ============================================================================
# CONSOLIDATED ASSETS CRUD OPERATIONS
# ============================================================================


def create_asset(
    name: str,
    asset_type: str,
    url: str,
    format: str,
    size: Optional[int] = None,
    user_id: Optional[int] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    duration: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
    thumbnail_blob_id: Optional[str] = None,
    waveform_url: Optional[str] = None,
    page_count: Optional[int] = None,
    asset_id: Optional[str] = None,
    blob_data: Optional[bytes] = None,
    blob_id: Optional[str] = None,
    source_url: Optional[str] = None,
) -> str:
    """Create a new asset in the consolidated assets table.

    Args:
        name: Display name of the asset
        asset_type: Type discriminator ('image', 'video', 'audio', 'document')
        url: Full URL to the file in cloud storage
        format: Specific file format ('png', 'mp4', 'mp3', 'pdf', etc.)
        size: File size in bytes
        user_id: Owner user ID (nullable)
        client_id: Associated client ID (nullable)
        campaign_id: Associated campaign ID (nullable)
        tags: Array of text tags
        width: For images and videos
        height: For images and videos
        duration: For videos and audio (in seconds)
        thumbnail_url: For videos and documents
        waveform_url: For audio
        page_count: For documents
        asset_id: Optional pre-generated asset ID (if None, generates new UUID)
        blob_data: Optional binary blob data for storing asset in database
        blob_id: Optional reference to asset_blobs table (for V3 blob storage)
        source_url: Optional original URL where asset was downloaded from

    Returns:
        Asset ID (UUID string)
    """
    if asset_id is None:
        asset_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO assets (
                id, user_id, client_id, campaign_id, name, asset_type, url,
                size, format, tags, width, height, duration, thumbnail_url,
                thumbnail_blob_id, waveform_url, page_count, blob_data, blob_id, source_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                user_id,
                client_id,
                campaign_id,
                name,
                asset_type,
                url,
                size,
                format,
                json.dumps(tags) if tags else None,
                width,
                height,
                duration,
                thumbnail_url,
                thumbnail_blob_id,
                waveform_url,
                page_count,
                blob_data,
                blob_id,
                source_url,
            ),
        )
        conn.commit()
        return asset_id


def get_asset_by_id(asset_id: str, include_blob: bool = False) -> Optional[Asset]:
    """Get an asset by ID and return as Pydantic Asset model.

    Args:
        asset_id: Asset UUID
        include_blob: If True, includes blob_data in the response (default False)

    Returns:
        Asset (ImageAsset | VideoAsset | AudioAsset | DocumentAsset) or None
    """
    with get_db() as conn:
        # Select all columns except blob_data unless specifically requested
        if include_blob:
            query = "SELECT * FROM assets WHERE id = ?"
        else:
            query = """
                SELECT id, user_id, client_id, campaign_id, name, asset_type, url,
                       size, uploaded_at, format, tags, width, height, duration,
                       thumbnail_url, waveform_url, page_count, blob_id, source_url
                FROM assets WHERE id = ?
            """

        row = conn.execute(query, (asset_id,)).fetchone()

        if row:
            return _row_to_asset_model(row)
    return None


def list_assets(
    user_id: Optional[int] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Asset]:
    """List assets with optional filtering.

    Args:
        user_id: Filter by user
        client_id: Filter by client
        campaign_id: Filter by campaign
        asset_type: Filter by type ('image', 'video', 'audio', 'document')
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of Asset Pydantic models (ImageAsset | VideoAsset | AudioAsset | DocumentAsset)
    """
    with get_db() as conn:
        # Build dynamic query
        where_clauses = []
        values = []

        if user_id is not None:
            where_clauses.append("user_id = ?")
            values.append(user_id)

        if client_id is not None:
            where_clauses.append("client_id = ?")
            values.append(client_id)

        if campaign_id is not None:
            where_clauses.append("campaign_id = ?")
            values.append(campaign_id)

        if asset_type is not None:
            where_clauses.append("asset_type = ?")
            values.append(asset_type)

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        values.extend([limit, offset])

        # Don't include blob_data in list queries for performance
        query = f"""
            SELECT id, user_id, client_id, campaign_id, name, asset_type, url,
                   size, uploaded_at, format, tags, width, height, duration,
                   thumbnail_url, waveform_url, page_count
            FROM assets
            {where_clause}
            ORDER BY uploaded_at DESC
            LIMIT ? OFFSET ?
        """

        rows = conn.execute(query, values).fetchall()
        return [_row_to_asset_model(row) for row in rows]


def update_asset(
    asset_id: str,
    name: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Update an asset (partial update)."""
    with get_db() as conn:
        update_fields = []
        values = []

        if name is not None:
            update_fields.append("name = ?")
            values.append(name)

        if client_id is not None:
            update_fields.append("client_id = ?")
            values.append(client_id)

        if campaign_id is not None:
            update_fields.append("campaign_id = ?")
            values.append(campaign_id)

        if tags is not None:
            update_fields.append("tags = ?")
            values.append(json.dumps(tags))

        if not update_fields:
            return False

        values.append(asset_id)

        query = f"""
            UPDATE assets
            SET {", ".join(update_fields)}
            WHERE id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_asset(asset_id: str, user_id: Optional[int] = None) -> bool:
    """Delete an asset. If user_id is provided, only delete if asset belongs to user."""
    with get_db() as conn:
        if user_id is not None:
            # Check ownership first
            cursor = conn.execute(
                "SELECT id FROM assets WHERE id = ? AND user_id = ?",
                (asset_id, user_id),
            )
            if not cursor.fetchone():
                return False

        cursor = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()
        return cursor.rowcount > 0


def _row_to_asset_model(row: sqlite3.Row) -> Asset:
    """Convert a database row to an Asset Pydantic model.

    Returns the appropriate asset type (ImageAsset | VideoAsset | AudioAsset | DocumentAsset)
    based on asset_type discriminator.
    """
    # Parse tags from JSON string
    tags_list = None
    if row["tags"]:
        try:
            tags_list = json.loads(row["tags"])
        except:
            pass

    # Common fields for all asset types
    common = {
        "id": row["id"],
        "userId": str(row["user_id"]) if row["user_id"] else "",
        "clientId": row["client_id"],
        "campaignId": row["campaign_id"],
        "name": row["name"],
        "url": row["url"],
        "size": row["size"],
        "uploadedAt": row["uploaded_at"],  # Will be formatted by Pydantic if datetime
        "tags": tags_list,
        "format": row["format"],
    }

    # Create appropriate Asset type based on discriminator
    asset_type = row["asset_type"]

    if asset_type == "image":
        return ImageAsset(
            **common,
            width=row["width"] or 0,
            height=row["height"] or 0,
        )
    elif asset_type == "video":
        return VideoAsset(
            **common,
            width=row["width"] or 0,
            height=row["height"] or 0,
            duration=row["duration"] or 0,
            thumbnailUrl=row["thumbnail_url"] or "",
        )
    elif asset_type == "audio":
        return AudioAsset(
            **common,
            duration=row["duration"] or 0,
            waveformUrl=row["waveform_url"],
        )
    elif asset_type == "document":
        return DocumentAsset(
            **common,
            pageCount=row["page_count"],
            thumbnailUrl=row["thumbnail_url"],
        )
    else:
        raise ValueError(f"Unknown asset type: {asset_type}")


# ============================================================================
# CAMPAIGN CRUD OPERATIONS
# ============================================================================


def create_campaign(
    user_id: int,
    client_id: str,
    name: str,
    goal: str,
    status: str = "draft",
    product_url: Optional[str] = None,
    brief: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new campaign."""
    campaign_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO campaigns (id, client_id, user_id, name, goal, status, product_url, brief, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                client_id,
                user_id,
                name,
                goal,
                status,
                product_url,
                json.dumps(brief) if brief else None,
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        return campaign_id


def get_campaign_by_id(campaign_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a campaign by ID (user must own the campaign)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ? AND user_id = ?",
            (campaign_id, user_id),
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "clientId": row["client_id"],
                "name": row["name"],
                "goal": row["goal"],
                "status": row["status"],
                "productUrl": row["product_url"],
                "brief": json.loads(row["brief"]) if row["brief"] else None,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
    return None


def list_campaigns(
    user_id: int, client_id: Optional[str] = None, limit: int = 100, offset: int = 0
) -> List[Dict[str, Any]]:
    """List campaigns for a user, optionally filtered by client."""
    with get_db() as conn:
        if client_id:
            rows = conn.execute(
                """
                SELECT * FROM campaigns
                WHERE user_id = ? AND client_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, client_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM campaigns
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "clientId": row["client_id"],
                "name": row["name"],
                "goal": row["goal"],
                "status": row["status"],
                "productUrl": row["product_url"],
                "brief": json.loads(row["brief"]) if row["brief"] else None,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]


def update_campaign(
    campaign_id: str,
    user_id: int,
    name: Optional[str] = None,
    goal: Optional[str] = None,
    status: Optional[str] = None,
    product_url: Optional[str] = None,
    brief: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Update a campaign (partial update)."""
    with get_db() as conn:
        # Build dynamic update query
        update_fields = []
        values = []

        if name is not None:
            update_fields.append("name = ?")
            values.append(name)

        if goal is not None:
            update_fields.append("goal = ?")
            values.append(goal)

        if status is not None:
            update_fields.append("status = ?")
            values.append(status)

        if product_url is not None:
            update_fields.append("product_url = ?")
            values.append(product_url)

        if brief is not None:
            update_fields.append("brief = ?")
            values.append(json.dumps(brief))

        if metadata is not None:
            update_fields.append("metadata = ?")
            values.append(json.dumps(metadata))

        if not update_fields:
            return False  # Nothing to update

        # Add WHERE clause values
        values.extend([campaign_id, user_id])

        query = f"""
            UPDATE campaigns
            SET {", ".join(update_fields)}
            WHERE id = ? AND user_id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_campaign(campaign_id: str, user_id: int) -> bool:
    """Delete a campaign (cascades to campaign assets)."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_campaign_stats(campaign_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get statistics for a campaign."""
    with get_db() as conn:
        # Verify ownership
        campaign = conn.execute(
            "SELECT id FROM campaigns WHERE id = ? AND user_id = ?",
            (campaign_id, user_id),
        ).fetchone()

        if not campaign:
            return None

        # Get video count, total spend, and average cost
        stats_row = conn.execute(
            """
            SELECT
                COUNT(id) as video_count,
                COALESCE(SUM(actual_cost), 0) as total_spend,
                COALESCE(AVG(actual_cost), 0) as avg_cost
            FROM generated_videos
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()

        video_count = stats_row["video_count"] if stats_row else 0
        total_spend = stats_row["total_spend"] if stats_row else 0.0
        avg_cost = stats_row["avg_cost"] if stats_row else 0.0

        return {
            "videoCount": video_count,
            "totalSpend": float(total_spend),
            "avgCost": float(avg_cost),
        }


# ============================================================================
# DEPRECATED: Old campaign asset functions (use consolidated assets API)
# ============================================================================
# These functions are kept for backward compatibility but redirect to new assets table


# ============================================================================
# VIDEO OPERATIONS (Enhanced for frontend integration)
# ============================================================================


def update_video_metrics(
    video_id: int,
    views: Optional[int] = None,
    clicks: Optional[int] = None,
    ctr: Optional[float] = None,
    conversions: Optional[int] = None,
) -> bool:
    """Update video performance metrics."""
    with get_db() as conn:
        # Build dynamic update query
        update_fields = []
        values = []

        if views is not None:
            update_fields.append("views = ?")
            values.append(views)

        if clicks is not None:
            update_fields.append("clicks = ?")
            values.append(clicks)

        if ctr is not None:
            update_fields.append("ctr = ?")
            values.append(ctr)

        if conversions is not None:
            update_fields.append("conversions = ?")
            values.append(conversions)

        if not update_fields:
            return False  # Nothing to update

        # Add WHERE clause value
        values.append(video_id)

        query = f"""
            UPDATE generated_videos
            SET {", ".join(update_fields)}
            WHERE id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def list_videos_by_campaign(
    campaign_id: str, limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """List all videos for a campaign."""
    with get_db() as conn:
        # Exclude video_data BLOB to avoid loading large binary data for gallery listing
        rows = conn.execute(
            """
            SELECT id, prompt, video_url, model_id, parameters, status,
                   created_at, collection, metadata, campaign_id, format,
                   duration, views, clicks, ctr, conversions, actual_cost,
                   updated_at, storyboard_data, progress
            FROM generated_videos
            WHERE campaign_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (campaign_id, limit, offset),
        ).fetchall()

        def safe_get(row, key, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default

        return [
            {
                "id": row["id"],
                "campaignId": safe_get(row, "campaign_id"),
                "name": row["prompt"][:50]
                if row["prompt"]
                else "Untitled",  # Use prompt as name
                "status": row["status"],
                "format": safe_get(row, "format", "16:9"),
                "duration": safe_get(row, "duration", 30),
                "prompt": row["prompt"],
                "videoUrl": row["video_url"],
                "storyboard": json.loads(safe_get(row, "storyboard_data"))
                if safe_get(row, "storyboard_data")
                else None,
                "generationProgress": json.loads(safe_get(row, "progress"))
                if safe_get(row, "progress")
                else None,
                "metrics": {
                    "views": safe_get(row, "views", 0),
                    "clicks": safe_get(row, "clicks", 0),
                    "ctr": safe_get(row, "ctr", 0.0),
                    "conversions": safe_get(row, "conversions", 0),
                },
                "cost": safe_get(row, "actual_cost", 0.0),
                "createdAt": row["created_at"],
                "updatedAt": safe_get(row, "updated_at", row["created_at"]),
            }
            for row in rows
        ]


# ============================================================================
# Scene Management Functions (Phase 2)
# ============================================================================


def create_job_scene(
    job_id: int,
    scene_number: int,
    duration: float,
    description: str,
    script: Optional[str] = None,
    shot_type: Optional[str] = None,
    transition: Optional[str] = None,
    assets: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a scene record for a job.

    Args:
        job_id: The job ID this scene belongs to
        scene_number: Scene number (1-indexed)
        duration: Scene duration in seconds
        description: Scene description
        script: Optional voiceover script
        shot_type: Optional shot type (wide, close-up, etc.)
        transition: Optional transition type (cut, fade, etc.)
        assets: Optional list of asset IDs used in this scene
        metadata: Optional additional scene metadata

    Returns:
        The created scene ID
    """
    scene_id = str(uuid.uuid4())
    assets_json = json.dumps(assets) if assets else None
    metadata_json = json.dumps(metadata) if metadata else None

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO job_scenes (
                id, job_id, scene_number, duration_seconds, description,
                script, shot_type, transition, assets, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scene_id,
                job_id,
                scene_number,
                duration,
                description,
                script,
                shot_type,
                transition,
                assets_json,
                metadata_json,
            ),
        )
        conn.commit()

    return scene_id


def get_scenes_by_job(job_id: int) -> List[Dict[str, Any]]:
    """
    Get all scenes for a job, ordered by scene number.

    Args:
        job_id: The job ID

    Returns:
        List of scene dictionaries
    """
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, job_id, scene_number, duration_seconds, description,
                   script, shot_type, transition, assets, metadata,
                   created_at, updated_at
            FROM job_scenes
            WHERE job_id = ?
            ORDER BY scene_number ASC
            """,
            (job_id,),
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "jobId": row["job_id"],
                "sceneNumber": row["scene_number"],
                "duration": row["duration_seconds"],
                "description": row["description"],
                "script": row["script"],
                "shotType": row["shot_type"],
                "transition": row["transition"],
                "assets": json.loads(row["assets"]) if row["assets"] else [],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]


def get_scene_by_id(scene_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific scene by ID.

    Args:
        scene_id: The scene UUID

    Returns:
        Scene dictionary or None if not found
    """
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, job_id, scene_number, duration_seconds, description,
                   script, shot_type, transition, assets, metadata,
                   created_at, updated_at
            FROM job_scenes
            WHERE id = ?
            """,
            (scene_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "jobId": row["job_id"],
            "sceneNumber": row["scene_number"],
            "duration": row["duration_seconds"],
            "description": row["description"],
            "script": row["script"],
            "shotType": row["shot_type"],
            "transition": row["transition"],
            "assets": json.loads(row["assets"]) if row["assets"] else [],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }


def update_job_scene(
    scene_id: str,
    description: Optional[str] = None,
    script: Optional[str] = None,
    shot_type: Optional[str] = None,
    transition: Optional[str] = None,
    duration: Optional[float] = None,
    assets: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Update a scene record.

    Args:
        scene_id: The scene UUID
        description: Optional new description
        script: Optional new script
        shot_type: Optional new shot type
        transition: Optional new transition
        duration: Optional new duration
        assets: Optional new assets list
        metadata: Optional new metadata

    Returns:
        True if updated successfully
    """
    updates = []
    params = []

    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if script is not None:
        updates.append("script = ?")
        params.append(script)
    if shot_type is not None:
        updates.append("shot_type = ?")
        params.append(shot_type)
    if transition is not None:
        updates.append("transition = ?")
        params.append(transition)
    if duration is not None:
        updates.append("duration_seconds = ?")
        params.append(duration)
    if assets is not None:
        updates.append("assets = ?")
        params.append(json.dumps(assets))
    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(scene_id)

    with get_db() as conn:
        cursor = conn.execute(
            f"UPDATE job_scenes SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_job_scene(scene_id: str) -> bool:
    """
    Delete a scene record.

    Args:
        scene_id: The scene UUID

    Returns:
        True if deleted successfully
    """
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM job_scenes WHERE id = ?", (scene_id,))
        conn.commit()
        return cursor.rowcount > 0


def delete_scenes_by_job(job_id: int) -> int:
    """
    Delete all scenes for a job.

    Args:
        job_id: The job ID

    Returns:
        Number of scenes deleted
    """
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM job_scenes WHERE job_id = ?", (job_id,))
        conn.commit()
        return cursor.rowcount
