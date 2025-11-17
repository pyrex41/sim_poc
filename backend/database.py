"""Database models and operations for storing generated scenes."""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

# Get data directory from environment variable, default to ./DATA
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "scenes.db"

def init_db():
    """Initialize the database with required tables.

    Uses the migration system to apply schema from schema.sql.
    All migrations are idempotent - safe to run on every server startup.
    """
    try:
        from .migrate import run_migrations
    except ImportError:
        from migrate import run_migrations
    run_migrations()

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def save_generated_scene(
    prompt: str,
    scene_data: dict,
    model: str,
    metadata: Optional[dict] = None,
    brief_id: Optional[str] = None
) -> int:
    """Save a generated scene to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_scenes (prompt, scene_data, model, metadata, brief_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                prompt,
                json.dumps(scene_data),
                model,
                json.dumps(metadata) if metadata else None,
                brief_id
            )
        )
        conn.commit()
        return cursor.lastrowid or 0

def get_scene_by_id(scene_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific scene by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM generated_scenes WHERE id = ?",
            (scene_id,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "prompt": row["prompt"],
                "scene_data": json.loads(row["scene_data"]),
                "model": row["model"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    return None

def list_scenes(
    limit: int = 50,
    offset: int = 0,
    model: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List generated scenes with pagination and optional model filter."""
    query = "SELECT * FROM generated_scenes"
    params = []

    if model:
        query += " WHERE model = ?"
        params.append(model)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "scene_data": json.loads(row["scene_data"]),
                "model": row["model"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
            for row in rows
        ]

def get_scene_count(model: Optional[str] = None) -> int:
    """Get total count of scenes, optionally filtered by model."""
    query = "SELECT COUNT(*) as count FROM generated_scenes"
    params = []

    if model:
        query += " WHERE model = ?"
        params.append(model)

    with get_db() as conn:
        row = conn.execute(query, params).fetchone()
        return row["count"]

def get_models_list() -> List[str]:
    """Get list of unique models that have generated scenes."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT model FROM generated_scenes ORDER BY model"
        ).fetchall()
        return [row["model"] for row in rows]

def delete_scene(scene_id: int) -> bool:
    """Delete a scene by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM generated_scenes WHERE id = ?",
            (scene_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def save_generated_video(
    prompt: str,
    video_url: str,
    model_id: str,
    parameters: dict,
    collection: Optional[str] = None,
    metadata: Optional[dict] = None,
    status: str = "completed",
    brief_id: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None
) -> int:
    """Save a generated video to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_videos (prompt, video_url, model_id, parameters, collection, metadata, status, brief_id, client_id, campaign_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                video_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status,
                brief_id,
                client_id,
                campaign_id
            )
        )
        conn.commit()
        return cursor.lastrowid or 0

def update_video_status(
    video_id: int,
    status: str,
    video_url: Optional[str] = None,
    metadata: Optional[dict] = None
) -> None:
    """Update the status and optionally the video_url and metadata of a video."""
    with get_db() as conn:
        if video_url is not None:
            conn.execute(
                """
                UPDATE generated_videos
                SET status = ?, video_url = ?, metadata = ?
                WHERE id = ?
                """,
                (status, video_url, json.dumps(metadata) if metadata else None, video_id)
            )
        else:
            conn.execute(
                """
                UPDATE generated_videos
                SET status = ?
                WHERE id = ?
                """,
                (status, video_id)
            )
        conn.commit()

def mark_download_attempted(video_id: int) -> bool:
    """Mark that a download has been attempted for a video. Returns False if already attempted."""
    with get_db() as conn:
        # Check if already attempted
        row = conn.execute(
            "SELECT download_attempted FROM generated_videos WHERE id = ?",
            (video_id,)
        ).fetchone()

        if row and row["download_attempted"]:
            return False  # Already attempted

        # Mark as attempted
        conn.execute(
            "UPDATE generated_videos SET download_attempted = 1 WHERE id = ?",
            (video_id,)
        )
        conn.commit()
        return True

def increment_download_retries(video_id: int) -> int:
    """Increment the download retry counter and return the new count."""
    with get_db() as conn:
        conn.execute(
            "UPDATE generated_videos SET download_retries = download_retries + 1 WHERE id = ?",
            (video_id,)
        )
        conn.commit()

        row = conn.execute(
            "SELECT download_retries FROM generated_videos WHERE id = ?",
            (video_id,)
        ).fetchone()

        return row["download_retries"] if row else 0

def mark_download_failed(video_id: int, error: str) -> None:
    """Mark a video download as permanently failed."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE generated_videos
            SET status = 'failed', download_error = ?
            WHERE id = ?
            """,
            (error, video_id)
        )
        conn.commit()

def get_video_by_id(video_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific video by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM generated_videos WHERE id = ?",
            (video_id,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "prompt": row["prompt"],
                "video_url": row["video_url"],
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "collection": row["collection"],
                "brief_id": row["brief_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    return None

def list_videos(
    limit: int = 50,
    offset: int = 0,
    model_id: Optional[str] = None,
    collection: Optional[str] = None,
    brief_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List generated videos with pagination and optional filters."""
    query = "SELECT * FROM generated_videos WHERE 1=1"
    params = []

    if model_id:
        query += " AND model_id = ?"
        params.append(model_id)

    if collection:
        query += " AND collection = ?"
        params.append(collection)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "video_url": row["video_url"],
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "collection": row["collection"],
                "brief_id": row["brief_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
            for row in rows
        ]

def delete_video(video_id: int) -> bool:
    """Delete a video by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM generated_videos WHERE id = ?",
            (video_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def save_genesis_video(
    scene_data: dict,
    video_path: str,
    quality: str,
    duration: float,
    fps: int,
    resolution: tuple = (1920, 1080),
    scene_context: Optional[str] = None,
    object_descriptions: Optional[dict] = None,
    metadata: Optional[dict] = None
) -> int:
    """Save a Genesis-rendered video to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO genesis_videos
            (scene_data, video_path, quality, duration, fps, resolution, scene_context, object_descriptions, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(scene_data),
                video_path,
                quality,
                duration,
                fps,
                f"{resolution[0]}x{resolution[1]}",
                scene_context,
                json.dumps(object_descriptions) if object_descriptions else None,
                json.dumps(metadata) if metadata else None
            )
        )
        conn.commit()
        return cursor.lastrowid

def get_genesis_video_by_id(video_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific Genesis video by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM genesis_videos WHERE id = ?",
            (video_id,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "scene_data": json.loads(row["scene_data"]),
                "video_path": row["video_path"],
                "quality": row["quality"],
                "duration": row["duration"],
                "fps": row["fps"],
                "resolution": row["resolution"],
                "scene_context": row["scene_context"],
                "object_descriptions": json.loads(row["object_descriptions"]) if row["object_descriptions"] else None,
                "status": row["status"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    return None

def list_genesis_videos(
    limit: int = 50,
    offset: int = 0,
    quality: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List Genesis videos with pagination and optional quality filter."""
    query = "SELECT * FROM genesis_videos WHERE 1=1"
    params = []

    if quality:
        query += " AND quality = ?"
        params.append(quality)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "scene_data": json.loads(row["scene_data"]),
                "video_path": row["video_path"],
                "quality": row["quality"],
                "duration": row["duration"],
                "fps": row["fps"],
                "resolution": row["resolution"],
                "scene_context": row["scene_context"],
                "object_descriptions": json.loads(row["object_descriptions"]) if row["object_descriptions"] else None,
                "status": row["status"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
            for row in rows
        ]

def delete_genesis_video(video_id: int) -> bool:
    """Delete a Genesis video by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM genesis_videos WHERE id = ?",
            (video_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_genesis_video_count(quality: Optional[str] = None) -> int:
    """Get total count of Genesis videos, optionally filtered by quality."""
    query = "SELECT COUNT(*) as count FROM genesis_videos"
    params = []

    if quality:
        query += " WHERE quality = ?"
        params.append(quality)

    with get_db() as conn:
        row = conn.execute(query, params).fetchone()
        return row["count"]

# Image generation functions
def save_generated_image(
    prompt: str,
    image_url: str,
    model_id: str,
    parameters: dict,
    collection: Optional[str] = None,
    metadata: Optional[dict] = None,
    status: str = "completed",
    brief_id: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None
) -> int:
    """Save a generated image to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_images (prompt, image_url, model_id, parameters, collection, metadata, status, brief_id, client_id, campaign_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                image_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status,
                brief_id,
                client_id,
                campaign_id
            )
        )
        conn.commit()
        return cursor.lastrowid or 0

def update_image_status(
    image_id: int,
    status: str,
    image_url: Optional[str] = None,
    metadata: Optional[dict] = None
) -> None:
    """Update the status and optionally the image_url and metadata of an image."""
    with get_db() as conn:
        if image_url is not None:
            conn.execute(
                """
                UPDATE generated_images
                SET status = ?, image_url = ?, metadata = ?
                WHERE id = ?
                """,
                (status, image_url, json.dumps(metadata) if metadata else None, image_id)
            )
        else:
            if metadata is not None:
                conn.execute(
                    """
                    UPDATE generated_images
                    SET status = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (status, json.dumps(metadata), image_id)
                )
            else:
                conn.execute(
                    """
                    UPDATE generated_images
                    SET status = ?
                    WHERE id = ?
                    """,
                    (status, image_id)
                )
        conn.commit()

def mark_image_download_attempted(image_id: int) -> bool:
    """Mark that a download has been attempted for an image. Returns False if already attempted."""
    with get_db() as conn:
        # Check if already attempted
        row = conn.execute(
            "SELECT download_attempted FROM generated_images WHERE id = ?",
            (image_id,)
        ).fetchone()

        if row and row["download_attempted"]:
            return False  # Already attempted

        # Mark as attempted
        conn.execute(
            "UPDATE generated_images SET download_attempted = 1 WHERE id = ?",
            (image_id,)
        )
        conn.commit()
        return True

def increment_image_download_retries(image_id: int) -> int:
    """Increment the download retry counter for an image and return the new count."""
    with get_db() as conn:
        conn.execute(
            "UPDATE generated_images SET download_retries = download_retries + 1 WHERE id = ?",
            (image_id,)
        )
        conn.commit()

        row = conn.execute(
            "SELECT download_retries FROM generated_images WHERE id = ?",
            (image_id,)
        ).fetchone()

        return row["download_retries"] if row else 0

def mark_image_download_failed(image_id: int, error: str) -> None:
    """Mark an image download as permanently failed."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE generated_images
            SET status = 'failed', download_error = ?
            WHERE id = ?
            """,
            (error, image_id)
        )
        conn.commit()

def get_image_by_id(image_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific image by ID."""
    import os
    # Get base URL for full URLs
    base_url = os.getenv("BASE_URL", "").strip()

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM generated_images WHERE id = ?",
            (image_id,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "prompt": row["prompt"],
                "image_url": _convert_to_full_url(row["image_url"], base_url),
                "thumbnail_url": _convert_to_full_url(f"/api/images/{row['id']}/thumbnail", base_url),
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "collection": row["collection"],
                "brief_id": row["brief_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    return None

def list_images(
    limit: int = 50,
    offset: int = 0,
    model_id: Optional[str] = None,
    collection: Optional[str] = None,
    brief_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List generated images with pagination and optional filters."""
    import os
    query = "SELECT * FROM generated_images WHERE 1=1"
    params = []

    if model_id:
        query += " AND model_id = ?"
        params.append(model_id)

    if collection:
        query += " AND collection = ?"
        params.append(collection)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    # Get base URL for full URLs
    base_url = os.getenv("BASE_URL", "").strip()

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "image_url": _convert_to_full_url(row["image_url"], base_url),
                "thumbnail_url": _convert_to_full_url(f"/api/images/{row['id']}/thumbnail", base_url),
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "collection": row["collection"],
                "brief_id": row["brief_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
            for row in rows
        ]

def _convert_to_full_url(url: str, base_url: str) -> str:
    """Convert relative URL to full URL using BASE_URL if available."""
    if not url:
        return url
    if url.startswith("http"):
        return url  # Already a full URL
    if base_url:
        return f"{base_url}{url}"
    return url  # Return relative URL

def delete_image(image_id: int) -> bool:
    """Delete an image by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM generated_images WHERE id = ?",
            (image_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

# Audio generation helper functions
def save_generated_audio(
    prompt: str,
    audio_url: str,
    model_id: str,
    parameters: dict,
    collection: Optional[str] = None,
    metadata: Optional[dict] = None,
    status: str = "completed",
    brief_id: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    duration: Optional[float] = None
) -> int:
    """Save a generated audio to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_audio (prompt, audio_url, model_id, parameters, collection, metadata, status, brief_id, client_id, campaign_id, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                audio_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status,
                brief_id,
                client_id,
                campaign_id,
                duration
            )
        )
        conn.commit()
        return cursor.lastrowid or 0

def update_audio_status(
    audio_id: int,
    status: str,
    audio_url: Optional[str] = None,
    metadata: Optional[dict] = None
) -> None:
    """Update the status and optionally the audio_url and metadata of an audio."""
    with get_db() as conn:
        if audio_url is not None:
            conn.execute(
                """
                UPDATE generated_audio
                SET status = ?, audio_url = ?, metadata = ?
                WHERE id = ?
                """,
                (status, audio_url, json.dumps(metadata) if metadata else None, audio_id)
            )
        else:
            if metadata is not None:
                conn.execute(
                    """
                    UPDATE generated_audio
                    SET status = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (status, json.dumps(metadata), audio_id)
                )
            else:
                conn.execute(
                    """
                    UPDATE generated_audio
                    SET status = ?
                    WHERE id = ?
                    """,
                    (status, audio_id)
                )
        conn.commit()

def get_audio_by_id(audio_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific audio by ID."""
    import os
    base_url = os.getenv("BASE_URL", "").strip()

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM generated_audio WHERE id = ?",
            (audio_id,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "prompt": row["prompt"],
                "audio_url": _convert_to_full_url(row["audio_url"], base_url),
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]) if row["parameters"] else {},
                "collection": row["collection"],
                "status": row["status"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "duration": row["duration"],
                "brief_id": row["brief_id"],
                "client_id": row["client_id"],
                "campaign_id": row["campaign_id"]
            }
    return None

def list_audio(
    limit: int = 50,
    offset: int = 0,
    collection: Optional[str] = None,
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List generated audio with optional filters."""
    import os
    base_url = os.getenv("BASE_URL", "").strip()

    with get_db() as conn:
        query = "SELECT * FROM generated_audio WHERE 1=1"
        params: List[Any] = []

        if collection:
            query += " AND collection = ?"
            params.append(collection)
        if status:
            query += " AND status = ?"
            params.append(status)
        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        if campaign_id:
            query += " AND campaign_id = ?"
            params.append(campaign_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "audio_url": _convert_to_full_url(row["audio_url"], base_url),
                "model_id": row["model_id"],
                "parameters": json.loads(row["parameters"]) if row["parameters"] else {},
                "collection": row["collection"],
                "status": row["status"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "duration": row["duration"],
                "brief_id": row["brief_id"],
                "client_id": row["client_id"],
                "campaign_id": row["campaign_id"]
            }
            for row in rows
        ]

def delete_audio(audio_id: int) -> bool:
    """Delete an audio by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM generated_audio WHERE id = ?",
            (audio_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

def mark_audio_download_attempted(audio_id: int) -> bool:
    """Mark that a download has been attempted for an audio. Returns False if already attempted."""
    with get_db() as conn:
        # Check if already attempted
        row = conn.execute(
            "SELECT download_attempted FROM generated_audio WHERE id = ?",
            (audio_id,)
        ).fetchone()

        if row and row["download_attempted"]:
            return False  # Already attempted

        # Mark as attempted
        conn.execute(
            "UPDATE generated_audio SET download_attempted = 1 WHERE id = ?",
            (audio_id,)
        )
        conn.commit()
        return True

def increment_audio_download_retries(audio_id: int) -> int:
    """Increment the download retry counter for an audio and return the new count."""
    with get_db() as conn:
        conn.execute(
            "UPDATE generated_audio SET download_retries = download_retries + 1 WHERE id = ?",
            (audio_id,)
        )
        conn.commit()

        row = conn.execute(
            "SELECT download_retries FROM generated_audio WHERE id = ?",
            (audio_id,)
        ).fetchone()

        return row["download_retries"] if row else 0

def mark_audio_download_failed(audio_id: int, error: str) -> None:
    """Mark an audio download as permanently failed."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE generated_audio
            SET status = 'failed', download_error = ?
            WHERE id = ?
            """,
            (error, audio_id)
        )
        conn.commit()

# Authentication helper functions
def create_user(username: str, email: str, hashed_password: str, is_admin: bool = False) -> int:
    """Create a new user."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, hashed_password, is_admin)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, hashed_password, is_admin)
        )
        conn.commit()
        return cursor.lastrowid

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "is_active": bool(row["is_active"]),
                "is_admin": bool(row["is_admin"]),
                "created_at": row["created_at"],
                "last_login": row["last_login"]
            }
    return None

def update_user_last_login(user_id: int) -> None:
    """Update user's last login timestamp."""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()

def create_api_key(key_hash: str, name: str, user_id: int, expires_at: Optional[str] = None) -> int:
    """Create a new API key."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO api_keys (key_hash, name, user_id, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (key_hash, name, user_id, expires_at)
        )
        conn.commit()
        return cursor.lastrowid

def get_api_key_by_hash(key_hash: str) -> Optional[Dict[str, Any]]:
    """Get API key by hash."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT ak.*, u.username, u.is_active as user_is_active
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = ?
            """,
            (key_hash,)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "key_hash": row["key_hash"],
                "name": row["name"],
                "user_id": row["user_id"],
                "username": row["username"],
                "is_active": bool(row["is_active"]),
                "user_is_active": bool(row["user_is_active"]),
                "created_at": row["created_at"],
                "last_used": row["last_used"],
                "expires_at": row["expires_at"]
            }
    return None

def update_api_key_last_used(key_hash: str) -> None:
    """Update API key's last used timestamp."""
    with get_db() as conn:
        conn.execute(
            "UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE key_hash = ?",
            (key_hash,)
        )
        conn.commit()

def list_api_keys(user_id: int) -> List[Dict[str, Any]]:
    """List all API keys for a user."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, is_active, created_at, last_used, expires_at
            FROM api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
                "last_used": row["last_used"],
                "expires_at": row["expires_at"]
            }
            for row in rows
        ]

def revoke_api_key(key_id: int, user_id: int) -> bool:
    """Revoke an API key."""
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?",
            (key_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

# Creative Briefs CRUD functions
def save_creative_brief(
    brief_id: str,
    user_id: int,
    prompt_text: Optional[str] = None,
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
    image_data: Optional[bytes] = None,
    video_data: Optional[bytes] = None,
    creative_direction: Optional[Dict[str, Any]] = None,
    scenes: Optional[List[Dict[str, Any]]] = None,
    confidence_score: Optional[float] = None
) -> str:
    """Save a creative brief to the database."""
    # Serialize dict/list data to JSON strings
    cd_json = json.dumps(creative_direction) if creative_direction else None
    scenes_json = json.dumps(scenes) if scenes else None

    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO creative_briefs
            (id, user_id, prompt_text, image_url, video_url, image_data, video_data, creative_direction, scenes, confidence_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (brief_id, user_id, prompt_text, image_url, video_url, image_data, video_data, cd_json, scenes_json, confidence_score)
        )
        conn.commit()
        return brief_id

def get_creative_brief(brief_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific creative brief by ID for a user."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, prompt_text, image_url, video_url, image_data, video_data,
                   creative_direction, scenes, confidence_score,
                   created_at, updated_at
            FROM creative_briefs
            WHERE id = ? AND user_id = ?
            """,
            (brief_id, user_id)
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "prompt_text": row["prompt_text"],
                "image_url": row["image_url"],
                "video_url": row["video_url"],
                "image_data": row["image_data"],
                "video_data": row["video_data"],
                "creative_direction": json.loads(row["creative_direction"]) if row["creative_direction"] else None,
                "scenes": json.loads(row["scenes"]) if row["scenes"] else None,
                "confidence_score": row["confidence_score"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    return None

def get_user_briefs(
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all creative briefs for a user with pagination."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, prompt_text, image_url, video_url, image_data, video_data,
                   creative_direction, scenes, confidence_score,
                   created_at, updated_at
            FROM creative_briefs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        ).fetchall()

        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "prompt_text": row["prompt_text"],
                "image_url": row["image_url"],
                "video_url": row["video_url"],
                "image_data": row["image_data"],
                "video_data": row["video_data"],
                "creative_direction": json.loads(row["creative_direction"]) if row["creative_direction"] else None,
                "scenes": json.loads(row["scenes"]) if row["scenes"] else None,
                "confidence_score": row["confidence_score"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

def update_brief(
    brief_id: str,
    user_id: int,
    prompt_text: Optional[str] = None,
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
    image_data: Optional[bytes] = None,
    video_data: Optional[bytes] = None,
    creative_direction: Optional[Dict[str, Any]] = None,
    scenes: Optional[List[Dict[str, Any]]] = None,
    confidence_score: Optional[float] = None
) -> bool:
    """Update a creative brief."""
    with get_db() as conn:
        # Build dynamic update query
        update_fields = []
        values = []

        if prompt_text is not None:
            update_fields.append("prompt_text = ?")
            values.append(prompt_text)
        if image_url is not None:
            update_fields.append("image_url = ?")
            values.append(image_url)
        if video_url is not None:
            update_fields.append("video_url = ?")
            values.append(video_url)
        if image_data is not None:
            update_fields.append("image_data = ?")
            values.append(image_data)
        if video_data is not None:
            update_fields.append("video_data = ?")
            values.append(video_data)
        if creative_direction is not None:
            update_fields.append("creative_direction = ?")
            values.append(json.dumps(creative_direction))
        if scenes is not None:
            update_fields.append("scenes = ?")
            values.append(json.dumps(scenes))
        if confidence_score is not None:
            update_fields.append("confidence_score = ?")
            values.append(confidence_score)

        if not update_fields:
            return False  # Nothing to update

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([brief_id, user_id])

        query = f"""
            UPDATE creative_briefs
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
        """

        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

def delete_brief(brief_id: str, user_id: int) -> bool:
    """Delete a creative brief."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM creative_briefs WHERE id = ? AND user_id = ?",
            (brief_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_brief_count(user_id: int) -> int:
    """Get the total count of briefs for a user."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as count FROM creative_briefs WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row["count"] if row else 0

# Video generation job helper functions (for v2 API)
def update_job_progress(job_id: int, progress: dict) -> bool:
    """
    Update the progress JSON field for a job.
    The updated_at timestamp is automatically updated by the trigger.

    Args:
        job_id: The video job ID
        progress: Dictionary containing progress information

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE generated_videos SET progress = ? WHERE id = ?",
                (json.dumps(progress), job_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating job progress for job {job_id}: {e}")
        return False

def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete job record by ID.

    Args:
        job_id: The video job ID

    Returns:
        Dictionary with all job fields, or None if not found
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM generated_videos WHERE id = ?",
                (job_id,)
            ).fetchone()

            if row:
                # Helper function to safely get column value
                def safe_get(key, default=None):
                    try:
                        return row[key]
                    except (KeyError, IndexError):
                        return default

                return {
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "video_url": row["video_url"],
                    "model_id": row["model_id"],
                    "parameters": json.loads(row["parameters"]) if row["parameters"] else {},
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "collection": row["collection"],
                    "brief_id": safe_get("brief_id"),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "download_attempted": bool(safe_get("download_attempted", 0)),
                    "download_retries": safe_get("download_retries", 0),
                    "download_error": safe_get("download_error"),
                    "progress": json.loads(safe_get("progress")) if safe_get("progress") else {},
                    "storyboard_data": json.loads(safe_get("storyboard_data")) if safe_get("storyboard_data") else None,
                    "approved": bool(safe_get("approved", 0)),
                    "approved_at": safe_get("approved_at"),
                    "estimated_cost": safe_get("estimated_cost", 0.0),
                    "actual_cost": safe_get("actual_cost", 0.0),
                    "error_message": safe_get("error_message"),
                    "updated_at": safe_get("updated_at")
                }
    except Exception as e:
        print(f"Error retrieving job {job_id}: {e}")
        import traceback
        traceback.print_exc()
    return None

def increment_retry_count(job_id: int) -> int:
    """
    Increment the retry_count (download_retries) for a failed job.

    Args:
        job_id: The video job ID

    Returns:
        The new retry count value
    """
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE generated_videos SET download_retries = download_retries + 1 WHERE id = ?",
                (job_id,)
            )
            conn.commit()

            row = conn.execute(
                "SELECT download_retries FROM generated_videos WHERE id = ?",
                (job_id,)
            ).fetchone()

            return row["download_retries"] if row else 0
    except Exception as e:
        print(f"Error incrementing retry count for job {job_id}: {e}")
        return 0

def mark_job_failed(job_id: int, error_message: str) -> bool:
    """
    Mark a job as failed with an error message.
    The updated_at timestamp is automatically updated by the trigger.

    Args:
        job_id: The video job ID
        error_message: Description of the error

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE generated_videos
                SET status = 'failed', error_message = ?
                WHERE id = ?
                """,
                (error_message, job_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error marking job {job_id} as failed: {e}")
        return False

def get_jobs_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get jobs with a specific status, ordered by most recently updated.

    Args:
        status: The status to filter by ('pending', 'processing', 'completed', 'failed', etc.)
        limit: Maximum number of records to return (default 50)

    Returns:
        List of job dictionaries
    """
    try:
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM generated_videos
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (status, limit)
            ).fetchall()

            result = []
            for row in rows:
                # Helper function to safely get column value
                def safe_get(key, default=None):
                    try:
                        return row[key]
                    except (KeyError, IndexError):
                        return default

                result.append({
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "video_url": row["video_url"],
                    "model_id": row["model_id"],
                    "parameters": json.loads(row["parameters"]) if row["parameters"] else {},
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "collection": row["collection"],
                    "brief_id": safe_get("brief_id"),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "download_attempted": bool(safe_get("download_attempted", 0)),
                    "download_retries": safe_get("download_retries", 0),
                    "download_error": safe_get("download_error"),
                    "progress": json.loads(safe_get("progress")) if safe_get("progress") else {},
                    "storyboard_data": json.loads(safe_get("storyboard_data")) if safe_get("storyboard_data") else None,
                    "approved": bool(safe_get("approved", 0)),
                    "approved_at": safe_get("approved_at"),
                    "estimated_cost": safe_get("estimated_cost", 0.0),
                    "actual_cost": safe_get("actual_cost", 0.0),
                    "error_message": safe_get("error_message"),
                    "updated_at": safe_get("updated_at")
                })
            return result
    except Exception as e:
        print(f"Error retrieving jobs by status '{status}': {e}")
        import traceback
        traceback.print_exc()
        return []

def approve_storyboard(job_id: int) -> bool:
    """
    Mark a job's storyboard as approved.
    Sets approved=True and approved_at=CURRENT_TIMESTAMP.

    Args:
        job_id: The video job ID

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE generated_videos
                SET approved = 1, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (job_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error approving storyboard for job {job_id}: {e}")
        return False

def create_video_job(
    prompt: str,
    model_id: str,
    parameters: dict,
    estimated_cost: float,
    client_id: Optional[str] = None,
    status: str = "pending"
) -> int:
    """
    Create a new video generation job for the v2 workflow.

    Args:
        prompt: User's video concept prompt
        model_id: Model identifier being used
        parameters: Generation parameters
        estimated_cost: Estimated cost in USD
        client_id: Optional client identifier
        status: Initial status (default: 'pending')

    Returns:
        The newly created job ID
    """
    try:
        with get_db() as conn:
            # Initialize progress as empty dict
            progress = json.dumps({
                "current_stage": status,
                "scenes_total": 0,
                "scenes_completed": 0,
                "current_scene": None,
                "estimated_completion_seconds": None,
                "message": "Job created, waiting to start"
            })

            cursor = conn.execute(
                """
                INSERT INTO generated_videos
                (prompt, video_url, model_id, parameters, status, estimated_cost, progress, client_id)
                VALUES (?, '', ?, ?, ?, ?, ?, ?)
                """,
                (
                    prompt,
                    model_id,
                    json.dumps(parameters),
                    status,
                    estimated_cost,
                    progress,
                    client_id
                )
            )
            conn.commit()
            return cursor.lastrowid or 0
    except Exception as e:
        print(f"Error creating video job: {e}")
        import traceback
        traceback.print_exc()
        return 0

def update_storyboard_data(job_id: int, storyboard_data: List[Dict[str, Any]]) -> bool:
    """
    Update the storyboard_data field for a job.

    Args:
        job_id: The video job ID
        storyboard_data: List of storyboard entries

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE generated_videos SET storyboard_data = ?, status = 'storyboard_ready' WHERE id = ?",
                (json.dumps(storyboard_data), job_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating storyboard data for job {job_id}: {e}")
        return False

def get_jobs_by_client(client_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get jobs for a specific client, optionally filtered by status.

    Args:
        client_id: The client identifier
        status: Optional status filter
        limit: Maximum number of records to return

    Returns:
        List of job dictionaries
    """
    try:
        with get_db() as conn:
            if status:
                query = """
                    SELECT * FROM generated_videos
                    WHERE client_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, status, limit)
            else:
                query = """
                    SELECT * FROM generated_videos
                    WHERE client_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                def safe_get(key, default=None):
                    try:
                        return row[key]
                    except (KeyError, IndexError):
                        return default

                result.append({
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "video_url": row["video_url"],
                    "model_id": row["model_id"],
                    "parameters": json.loads(row["parameters"]) if row["parameters"] else {},
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "client_id": safe_get("client_id"),
                    "progress": json.loads(safe_get("progress")) if safe_get("progress") else {},
                    "storyboard_data": json.loads(safe_get("storyboard_data")) if safe_get("storyboard_data") else None,
                    "approved": bool(safe_get("approved", 0)),
                    "approved_at": safe_get("approved_at"),
                    "estimated_cost": safe_get("estimated_cost", 0.0),
                    "actual_cost": safe_get("actual_cost", 0.0),
                    "error_message": safe_get("error_message"),
                    "updated_at": safe_get("updated_at")
                })
            return result
    except Exception as e:
        print(f"Error retrieving jobs for client {client_id}: {e}")
        import traceback
        traceback.print_exc()
        return []

# Asset management functions
def save_uploaded_asset(
    asset_id: str,
    user_id: int,
    filename: str,
    file_path: str,
    file_type: str,
    size_bytes: int
) -> str:
    """Save an uploaded asset to the database."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_assets (asset_id, user_id, filename, file_path, file_type, size_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asset_id, user_id, filename, file_path, file_type, size_bytes)
        )
        conn.commit()
        return asset_id

def get_asset_by_id(asset_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific asset by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM uploaded_assets WHERE asset_id = ?",
            (asset_id,)
        ).fetchone()

        if row:
            return {
                "asset_id": row["asset_id"],
                "user_id": row["user_id"],
                "filename": row["filename"],
                "file_path": row["file_path"],
                "file_type": row["file_type"],
                "size_bytes": row["size_bytes"],
                "uploaded_at": row["uploaded_at"]
            }
    return None

def list_user_assets(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """List all assets for a user with pagination."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM uploaded_assets
            WHERE user_id = ?
            ORDER BY uploaded_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        ).fetchall()

        return [
            {
                "asset_id": row["asset_id"],
                "filename": row["filename"],
                "file_type": row["file_type"],
                "size_bytes": row["size_bytes"],
                "uploaded_at": row["uploaded_at"]
            }
            for row in rows
        ]

def delete_asset(asset_id: str, user_id: int) -> bool:
    """Delete an asset by ID (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM uploaded_assets WHERE asset_id = ? AND user_id = ?",
            (asset_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

# Video Export and Refinement functions
def increment_download_count(job_id: int) -> bool:
    """
    Increment the download count for a video job.

    Args:
        job_id: The video job ID

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE generated_videos SET download_count = COALESCE(download_count, 0) + 1 WHERE id = ?",
                (job_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error incrementing download count for job {job_id}: {e}")
        return False

def get_download_count(job_id: int) -> int:
    """
    Get the download count for a video job.

    Args:
        job_id: The video job ID

    Returns:
        Download count (0 if not found or error)
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT COALESCE(download_count, 0) as count FROM generated_videos WHERE id = ?",
                (job_id,)
            ).fetchone()
            return row["count"] if row else 0
    except Exception as e:
        print(f"Error getting download count for job {job_id}: {e}")
        return 0

def refine_scene_in_storyboard(
    job_id: int,
    scene_number: int,
    new_image_url: Optional[str] = None,
    new_description: Optional[str] = None,
    new_image_prompt: Optional[str] = None
) -> bool:
    """
    Refine a specific scene in the storyboard by updating its data.

    Args:
        job_id: The video job ID
        scene_number: Scene number to refine (1-indexed)
        new_image_url: New image URL (if regenerated)
        new_description: New scene description
        new_image_prompt: New image generation prompt

    Returns:
        True on success, False on failure
    """
    try:
        job = get_job(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return False

        storyboard_data = job.get("storyboard_data")
        if not storyboard_data:
            print(f"No storyboard data for job {job_id}")
            return False

        # Find the scene to update
        scene_found = False
        for entry in storyboard_data:
            scene = entry.get("scene", {})
            if scene.get("scene_number") == scene_number:
                scene_found = True

                # Update scene data
                if new_image_url:
                    entry["image_url"] = new_image_url
                    entry["generation_status"] = "completed"

                if new_description:
                    scene["description"] = new_description

                if new_image_prompt:
                    scene["image_prompt"] = new_image_prompt

                break

        if not scene_found:
            print(f"Scene {scene_number} not found in job {job_id}")
            return False

        # Update database with modified storyboard and reset approval
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE generated_videos
                SET storyboard_data = ?,
                    approved = 0,
                    approved_at = NULL,
                    refinement_count = COALESCE(refinement_count, 0) + 1
                WHERE id = ?
                """,
                (json.dumps(storyboard_data), job_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    except Exception as e:
        print(f"Error refining scene {scene_number} in job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def reorder_storyboard_scenes(job_id: int, scene_order: List[int]) -> bool:
    """
    Reorder scenes in the storyboard.

    Args:
        job_id: The video job ID
        scene_order: New order of scene numbers (e.g., [1, 3, 2, 4])

    Returns:
        True on success, False on failure
    """
    try:
        job = get_job(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return False

        storyboard_data = job.get("storyboard_data")
        if not storyboard_data:
            print(f"No storyboard data for job {job_id}")
            return False

        # Validate scene_order
        current_scene_numbers = [entry.get("scene", {}).get("scene_number") for entry in storyboard_data]
        if sorted(scene_order) != sorted(current_scene_numbers):
            print(f"Invalid scene order: {scene_order} vs {current_scene_numbers}")
            return False

        # Create a mapping of old scene numbers to entries
        scene_map = {
            entry.get("scene", {}).get("scene_number"): entry
            for entry in storyboard_data
        }

        # Reorder based on new order
        reordered_storyboard = []
        for new_position, old_scene_number in enumerate(scene_order, start=1):
            entry = scene_map[old_scene_number]
            # Update scene number to match new position
            entry["scene"]["scene_number"] = new_position
            reordered_storyboard.append(entry)

        # Update database with reordered storyboard and reset approval
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE generated_videos
                SET storyboard_data = ?,
                    approved = 0,
                    approved_at = NULL
                WHERE id = ?
                """,
                (json.dumps(reordered_storyboard), job_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    except Exception as e:
        print(f"Error reordering scenes in job {job_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_refinement_count(job_id: int) -> int:
    """
    Get the refinement count for a job.

    Args:
        job_id: The video job ID

    Returns:
        Refinement count (0 if not found or error)
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT COALESCE(refinement_count, 0) as count FROM generated_videos WHERE id = ?",
                (job_id,)
            ).fetchone()
            return row["count"] if row else 0
    except Exception as e:
        print(f"Error getting refinement count for job {job_id}: {e}")
        return 0

def increment_estimated_cost(job_id: int, additional_cost: float) -> bool:
    """
    Increment the estimated cost for a job (used when refining scenes).

    Args:
        job_id: The video job ID
        additional_cost: Additional cost to add

    Returns:
        True on success, False on failure
    """
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE generated_videos
                SET estimated_cost = COALESCE(estimated_cost, 0.0) + ?
                WHERE id = ?
                """,
                (additional_cost, job_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error incrementing estimated cost for job {job_id}: {e}")
        return False

def get_generated_images_by_client(client_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get generated images for a specific client, optionally filtered by status.

    Args:
        client_id: The client identifier
        status: Optional status filter
        limit: Maximum number of records to return

    Returns:
        List of image dictionaries
    """
    try:
        with get_db() as conn:
            if status:
                query = """
                    SELECT * FROM generated_images
                    WHERE client_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, status, limit)
            else:
                query = """
                    SELECT * FROM generated_images
                    WHERE client_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                result.append(dict(row))

            return result
    except Exception as e:
        print(f"Error getting images for client {client_id}: {e}")
        return []

def get_generated_videos_by_client(client_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get generated videos for a specific client, optionally filtered by status.

    Args:
        client_id: The client identifier
        status: Optional status filter
        limit: Maximum number of records to return

    Returns:
        List of video dictionaries
    """
    try:
        with get_db() as conn:
            if status:
                query = """
                    SELECT * FROM generated_videos
                    WHERE client_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, status, limit)
            else:
                query = """
                    SELECT * FROM generated_videos
                    WHERE client_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (client_id, limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                result.append(dict(row))

            return result
    except Exception as e:
        print(f"Error getting videos for client {client_id}: {e}")
        return []

def get_generated_images_by_campaign(campaign_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get generated images for a specific campaign, optionally filtered by status.

    Args:
        campaign_id: The campaign identifier
        status: Optional status filter
        limit: Maximum number of records to return

    Returns:
        List of image dictionaries
    """
    try:
        with get_db() as conn:
            if status:
                query = """
                    SELECT * FROM generated_images
                    WHERE campaign_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (campaign_id, status, limit)
            else:
                query = """
                    SELECT * FROM generated_images
                    WHERE campaign_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (campaign_id, limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                result.append(dict(row))

            return result
    except Exception as e:
        print(f"Error getting images for campaign {campaign_id}: {e}")
        return []

def get_generated_videos_by_campaign(campaign_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get generated videos for a specific campaign, optionally filtered by status.

    Args:
        campaign_id: The campaign identifier
        status: Optional status filter
        limit: Maximum number of records to return

    Returns:
        List of video dictionaries
    """
    try:
        with get_db() as conn:
            if status:
                query = """
                    SELECT * FROM generated_videos
                    WHERE campaign_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (campaign_id, status, limit)
            else:
                query = """
                    SELECT * FROM generated_videos
                    WHERE campaign_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (campaign_id, limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                result.append(dict(row))

            return result
    except Exception as e:
        print(f"Error getting videos for campaign {campaign_id}: {e}")
        return []

# Initialize database on import
init_db()
