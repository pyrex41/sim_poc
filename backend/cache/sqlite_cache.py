"""
SQLite-based cache for job progress tracking
Simple POC implementation - no external dependencies needed
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL = 30  # seconds
DB_PATH = Path(__file__).parent.parent / "DATA" / "cache.db"

def _get_connection():
    """Get SQLite connection for cache database"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init_cache_table():
    """Initialize cache table if it doesn't exist"""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON job_cache(expires_at)")
        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing cache table: {e}")
    finally:
        conn.close()

# Initialize on module load
_init_cache_table()

def get_cached_job(job_id: int) -> Optional[Dict[str, Any]]:
    """
    Get cached job data if available and not expired

    Args:
        job_id: Job ID to retrieve

    Returns:
        Dict with job data if cache hit, None if miss or expired
    """
    cache_key = f"job:{job_id}"
    conn = _get_connection()

    try:
        cursor = conn.execute(
            "SELECT data FROM job_cache WHERE cache_key = ? AND expires_at > ?",
            (cache_key, time.time())
        )
        row = cursor.fetchone()

        if row:
            logger.debug(f"Cache HIT for job {job_id}")
            return json.loads(row["data"])
        else:
            logger.debug(f"Cache MISS for job {job_id}")
            return None
    except Exception as e:
        logger.error(f"Error reading from cache: {e}")
        return None
    finally:
        conn.close()

def set_cached_job(job_id: int, data: Dict[str, Any], ttl: int = CACHE_TTL):
    """
    Store job data in cache with TTL

    Args:
        job_id: Job ID
        data: Job data dictionary to cache
        ttl: Time to live in seconds (default 30)
    """
    cache_key = f"job:{job_id}"
    expires_at = time.time() + ttl

    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO job_cache (cache_key, data, expires_at) VALUES (?, ?, ?)",
            (cache_key, json.dumps(data), expires_at)
        )
        conn.commit()
        logger.debug(f"Cached job {job_id} with TTL {ttl}s")
    except Exception as e:
        logger.error(f"Error writing to cache: {e}")
    finally:
        conn.close()

def invalidate_job_cache(job_id: int):
    """
    Invalidate cache for specific job

    Args:
        job_id: Job ID to invalidate
    """
    cache_key = f"job:{job_id}"
    conn = _get_connection()

    try:
        conn.execute("DELETE FROM job_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
        logger.debug(f"Invalidated cache for job {job_id}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
    finally:
        conn.close()

def invalidate_user_jobs_cache(client_id: str):
    """
    Invalidate all cached jobs for a user

    Args:
        client_id: Client/user ID
    """
    # For simplicity, just clear all job caches
    # In production, you'd track job->user mapping
    conn = _get_connection()

    try:
        conn.execute("DELETE FROM job_cache WHERE cache_key LIKE 'job:%'")
        conn.commit()
        logger.debug(f"Invalidated all job caches for user {client_id}")
    except Exception as e:
        logger.error(f"Error invalidating user caches: {e}")
    finally:
        conn.close()

def cleanup_expired():
    """Remove expired cache entries"""
    conn = _get_connection()

    try:
        cursor = conn.execute("DELETE FROM job_cache WHERE expires_at <= ?", (time.time(),))
        deleted = cursor.rowcount
        conn.commit()
        if deleted > 0:
            logger.debug(f"Cleaned up {deleted} expired cache entries")
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
    finally:
        conn.close()

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics

    Returns:
        Dict with cache stats (total entries, expired, active)
    """
    conn = _get_connection()

    try:
        cursor = conn.execute("SELECT COUNT(*) as total FROM job_cache")
        total = cursor.fetchone()["total"]

        cursor = conn.execute(
            "SELECT COUNT(*) as active FROM job_cache WHERE expires_at > ?",
            (time.time(),)
        )
        active = cursor.fetchone()["active"]

        expired = total - active

        return {
            "total_entries": total,
            "active_entries": active,
            "expired_entries": expired,
            "cache_type": "sqlite",
            "ttl_seconds": CACHE_TTL
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}
    finally:
        conn.close()

# Wrapper functions for compatibility with main.py

def get_job_with_cache(job_id: int):
    """
    Get job with cache - compatible with main.py
    Returns cached data or fetches from DB if cache miss
    """
    # Try cache first
    cached = get_cached_job(job_id)
    if cached:
        return cached

    # Cache miss - fetch from database
    try:
        from backend.database import get_job as db_get_job
        job = db_get_job(job_id)

        if job:
            # Store in cache for next time
            set_cached_job(job_id, job)

        return job
    except Exception as e:
        logger.error(f"Error fetching job from database: {e}")
        return None

def update_job_progress_with_cache(job_id: int, progress: dict):
    """
    Update job progress and invalidate cache
    Caller should update database first, then call this
    """
    invalidate_job_cache(job_id)
