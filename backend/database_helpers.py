"""Database helper functions for Clients and Campaigns management.

This module provides CRUD operations for:
- Clients (brand/client management with brand guidelines)
- Client Assets (logos, brand documents)
- Campaigns (marketing campaigns linked to clients)
- Campaign Assets (campaign-specific media)
"""

import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import os

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
    brand_guidelines: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new client."""
    client_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO clients (id, user_id, name, description, brand_guidelines)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                client_id,
                user_id,
                name,
                description,
                json.dumps(brand_guidelines) if brand_guidelines else None
            )
        )
        conn.commit()
        return client_id


def get_client_by_id(client_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a client by ID (user must own the client)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "brandGuidelines": json.loads(row["brand_guidelines"]) if row["brand_guidelines"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
    return None


def list_clients(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all clients for a user."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM clients
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "brandGuidelines": json.loads(row["brand_guidelines"]) if row["brand_guidelines"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
            for row in rows
        ]


def update_client(
    client_id: str,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    brand_guidelines: Optional[Dict[str, Any]] = None
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

        if brand_guidelines is not None:
            update_fields.append("brand_guidelines = ?")
            values.append(json.dumps(brand_guidelines))

        if not update_fields:
            return False  # Nothing to update

        # Add WHERE clause values
        values.extend([client_id, user_id])

        query = f"""
            UPDATE clients
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_client(client_id: str, user_id: int) -> bool:
    """Delete a client (cascades to campaigns and assets)."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM clients WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_client_stats(client_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get statistics for a client."""
    with get_db() as conn:
        # Verify ownership
        client = conn.execute(
            "SELECT id FROM clients WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        ).fetchone()

        if not client:
            return None

        # Get campaign count
        campaign_count_row = conn.execute(
            "SELECT COUNT(*) as count FROM campaigns WHERE client_id = ?",
            (client_id,)
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
            (client_id,)
        ).fetchone()

        video_count = video_stats_row["video_count"] if video_stats_row else 0
        total_spend = video_stats_row["total_spend"] if video_stats_row else 0.0

        return {
            "campaignCount": campaign_count,
            "videoCount": video_count,
            "totalSpend": float(total_spend)
        }


# ============================================================================
# CLIENT ASSETS CRUD OPERATIONS
# ============================================================================

def create_client_asset(
    client_id: str,
    asset_type: str,
    url: str,
    name: str
) -> str:
    """Create a client asset (logo, image, document)."""
    asset_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO client_assets (id, client_id, type, url, name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset_id, client_id, asset_type, url, name)
        )
        conn.commit()
        return asset_id


def list_client_assets(client_id: str) -> List[Dict[str, Any]]:
    """List all assets for a client."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM client_assets
            WHERE client_id = ?
            ORDER BY uploaded_at DESC
            """,
            (client_id,)
        ).fetchall()

        return [
            {
                "id": row["id"],
                "type": row["type"],
                "url": row["url"],
                "name": row["name"],
                "uploadedAt": row["uploaded_at"]
            }
            for row in rows
        ]


def delete_client_asset(asset_id: str, client_id: str) -> bool:
    """Delete a client asset."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM client_assets WHERE id = ? AND client_id = ?",
            (asset_id, client_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# CAMPAIGN CRUD OPERATIONS
# ============================================================================

def create_campaign(
    user_id: int,
    client_id: str,
    name: str,
    goal: str,
    status: str = "draft",
    brief: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new campaign."""
    campaign_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO campaigns (id, client_id, user_id, name, goal, status, brief)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                client_id,
                user_id,
                name,
                goal,
                status,
                json.dumps(brief) if brief else None
            )
        )
        conn.commit()
        return campaign_id


def get_campaign_by_id(campaign_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a campaign by ID (user must own the campaign)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ? AND user_id = ?",
            (campaign_id, user_id)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "clientId": row["client_id"],
                "name": row["name"],
                "goal": row["goal"],
                "status": row["status"],
                "brief": json.loads(row["brief"]) if row["brief"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
    return None


def list_campaigns(
    user_id: int,
    client_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
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
                (user_id, client_id, limit, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM campaigns
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            ).fetchall()

        return [
            {
                "id": row["id"],
                "clientId": row["client_id"],
                "name": row["name"],
                "goal": row["goal"],
                "status": row["status"],
                "brief": json.loads(row["brief"]) if row["brief"] else None,
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
            for row in rows
        ]


def update_campaign(
    campaign_id: str,
    user_id: int,
    name: Optional[str] = None,
    goal: Optional[str] = None,
    status: Optional[str] = None,
    brief: Optional[Dict[str, Any]] = None
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

        if brief is not None:
            update_fields.append("brief = ?")
            values.append(json.dumps(brief))

        if not update_fields:
            return False  # Nothing to update

        # Add WHERE clause values
        values.extend([campaign_id, user_id])

        query = f"""
            UPDATE campaigns
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_campaign(campaign_id: str, user_id: int) -> bool:
    """Delete a campaign (cascades to campaign assets)."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM campaigns WHERE id = ? AND user_id = ?",
            (campaign_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_campaign_stats(campaign_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get statistics for a campaign."""
    with get_db() as conn:
        # Verify ownership
        campaign = conn.execute(
            "SELECT id FROM campaigns WHERE id = ? AND user_id = ?",
            (campaign_id, user_id)
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
            (campaign_id,)
        ).fetchone()

        video_count = stats_row["video_count"] if stats_row else 0
        total_spend = stats_row["total_spend"] if stats_row else 0.0
        avg_cost = stats_row["avg_cost"] if stats_row else 0.0

        return {
            "videoCount": video_count,
            "totalSpend": float(total_spend),
            "avgCost": float(avg_cost)
        }


# ============================================================================
# CAMPAIGN ASSETS CRUD OPERATIONS
# ============================================================================

def create_campaign_asset(
    campaign_id: str,
    asset_type: str,
    url: str,
    name: str
) -> str:
    """Create a campaign asset (image, video, document)."""
    asset_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO campaign_assets (id, campaign_id, type, url, name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset_id, campaign_id, asset_type, url, name)
        )
        conn.commit()
        return asset_id


def list_campaign_assets(campaign_id: str) -> List[Dict[str, Any]]:
    """List all assets for a campaign."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM campaign_assets
            WHERE campaign_id = ?
            ORDER BY uploaded_at DESC
            """,
            (campaign_id,)
        ).fetchall()

        return [
            {
                "id": row["id"],
                "type": row["type"],
                "url": row["url"],
                "name": row["name"],
                "uploadedAt": row["uploaded_at"]
            }
            for row in rows
        ]


def delete_campaign_asset(asset_id: str, campaign_id: str) -> bool:
    """Delete a campaign asset."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM campaign_assets WHERE id = ? AND campaign_id = ?",
            (asset_id, campaign_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# VIDEO OPERATIONS (Enhanced for frontend integration)
# ============================================================================

def update_video_metrics(
    video_id: int,
    views: Optional[int] = None,
    clicks: Optional[int] = None,
    ctr: Optional[float] = None,
    conversions: Optional[int] = None
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
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def list_videos_by_campaign(
    campaign_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List all videos for a campaign."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM generated_videos
            WHERE campaign_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (campaign_id, limit, offset)
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
                "name": row["prompt"][:50] if row["prompt"] else "Untitled",  # Use prompt as name
                "status": row["status"],
                "format": safe_get(row, "format", "16:9"),
                "duration": safe_get(row, "duration", 30),
                "prompt": row["prompt"],
                "videoUrl": row["video_url"],
                "storyboard": json.loads(safe_get(row, "storyboard_data")) if safe_get(row, "storyboard_data") else None,
                "generationProgress": json.loads(safe_get(row, "progress")) if safe_get(row, "progress") else None,
                "metrics": {
                    "views": safe_get(row, "views", 0),
                    "clicks": safe_get(row, "clicks", 0),
                    "ctr": safe_get(row, "ctr", 0.0),
                    "conversions": safe_get(row, "conversions", 0)
                },
                "cost": safe_get(row, "actual_cost", 0.0),
                "createdAt": row["created_at"],
                "updatedAt": safe_get(row, "updated_at", row["created_at"])
            }
            for row in rows
        ]
