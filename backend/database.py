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
    """Initialize the database with required tables."""
    with get_db() as conn:
        # Authentication tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash
            ON api_keys(key_hash)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username
            ON users(username)
        """)

        # Existing tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                scene_data TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                video_url TEXT NOT NULL,
                model_id TEXT NOT NULL,
                parameters TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                collection TEXT,
                metadata TEXT,
                download_attempted BOOLEAN DEFAULT 0,
                download_retries INTEGER DEFAULT 0,
                download_error TEXT
            )
        """)

        # Add download tracking columns if they don't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN download_attempted BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN download_retries INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN download_error TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN video_data BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add image data column for generated_images
        try:
            conn.execute("ALTER TABLE generated_images ADD COLUMN image_data BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON generated_scenes(created_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_model
            ON generated_scenes(model)
        """)

        # Add brief_id column to generated_scenes if it doesn't exist
        try:
            conn.execute("ALTER TABLE generated_scenes ADD COLUMN brief_id TEXT REFERENCES creative_briefs(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scenes_brief
            ON generated_scenes(brief_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_created_at
            ON generated_videos(created_at DESC)
        """)

        # Add brief_id column to generated_videos if it doesn't exist
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN brief_id TEXT REFERENCES creative_briefs(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_brief
            ON generated_videos(brief_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_model
            ON generated_videos(model_id)
        """)

        # Genesis-specific videos table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS genesis_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_data TEXT NOT NULL,
                video_path TEXT NOT NULL,
                quality TEXT NOT NULL,
                duration REAL NOT NULL,
                fps INTEGER NOT NULL,
                resolution TEXT,
                scene_context TEXT,
                object_descriptions TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_genesis_videos_created_at
            ON genesis_videos(created_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_genesis_videos_quality
            ON genesis_videos(quality)
        """)

        # Generated images table (similar to generated_videos)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                image_url TEXT NOT NULL,
                model_id TEXT NOT NULL,
                parameters TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                collection TEXT,
                metadata TEXT,
                download_attempted BOOLEAN DEFAULT 0,
                download_retries INTEGER DEFAULT 0,
                download_error TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_created_at
            ON generated_images(created_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_model
            ON generated_images(model_id)
        """)

        # Add brief_id column to generated_images if it doesn't exist
        try:
            conn.execute("ALTER TABLE generated_images ADD COLUMN brief_id TEXT REFERENCES creative_briefs(id)")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_brief
            ON generated_images(brief_id)
        """)

        # Creative briefs table for prompt parser integration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS creative_briefs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                prompt_text TEXT,
                image_url TEXT,
                video_url TEXT,
                image_data BLOB,
                video_data BLOB,
                creative_direction TEXT NOT NULL,
                scenes TEXT NOT NULL,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_briefs_user
            ON creative_briefs(user_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_briefs_created
            ON creative_briefs(created_at DESC)
        """)

        # Add BLOB columns if table exists (for existing DB)
        try:
            conn.execute("ALTER TABLE creative_briefs ADD COLUMN image_data BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE creative_briefs ADD COLUMN video_data BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()

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
    brief_id: Optional[str] = None
) -> int:
    """Save a generated video to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_videos (prompt, video_url, model_id, parameters, collection, metadata, status, brief_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                video_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status,
                brief_id
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
    brief_id: Optional[str] = None
) -> int:
    """Save a generated image to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_images (prompt, image_url, model_id, parameters, collection, metadata, status, brief_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                image_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status,
                brief_id
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

# Initialize database on import
init_db()
