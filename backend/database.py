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
                metadata TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON generated_scenes(created_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_model
            ON generated_scenes(model)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_created_at
            ON generated_videos(created_at DESC)
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
    metadata: Optional[dict] = None
) -> int:
    """Save a generated scene to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_scenes (prompt, scene_data, model, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (
                prompt,
                json.dumps(scene_data),
                model,
                json.dumps(metadata) if metadata else None
            )
        )
        conn.commit()
        return cursor.lastrowid

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
    status: str = "completed"
) -> int:
    """Save a generated video to the database."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_videos (prompt, video_url, model_id, parameters, collection, metadata, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                video_url,
                model_id,
                json.dumps(parameters),
                collection,
                json.dumps(metadata) if metadata else None,
                status
            )
        )
        conn.commit()
        return cursor.lastrowid

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
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
    return None

def list_videos(
    limit: int = 50,
    offset: int = 0,
    model_id: Optional[str] = None,
    collection: Optional[str] = None
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

# Initialize database on import
init_db()
