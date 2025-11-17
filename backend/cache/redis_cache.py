"""
Redis caching layer for job progress tracking.

This module provides Redis-based caching to reduce database load from frequent
job status polling. Implements graceful fallback to direct database queries if
Redis is unavailable.

Features:
- Job response caching with 30-second TTL
- Cache invalidation on job updates
- Connection pooling with automatic retry
- Graceful degradation when Redis is unavailable
- Cache statistics tracking
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import redis
    from redis import ConnectionPool, Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None
    Redis = None

from ..config import get_settings
from ..database import get_job, update_job_progress

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL_SECONDS = 30
JOB_CACHE_KEY_PREFIX = "job"
USER_JOBS_KEY_PREFIX = "jobs"
STATS_KEY = "cache:stats"

# Global connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None
_redis_enabled = False

# Cache statistics
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "errors": 0,
    "invalidations": 0
}


def _initialize_redis() -> bool:
    """
    Initialize Redis connection pool.

    Returns:
        True if Redis is available and initialized, False otherwise
    """
    global _redis_pool, _redis_client, _redis_enabled

    if not REDIS_AVAILABLE:
        logger.warning("redis-py library not installed, caching disabled")
        return False

    if _redis_client is not None:
        return _redis_enabled

    try:
        settings = get_settings()
        redis_url = settings.REDIS_URL

        # Create connection pool
        _redis_pool = ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )

        # Create Redis client
        _redis_client = Redis(connection_pool=_redis_pool)

        # Test connection
        _redis_client.ping()

        _redis_enabled = True
        logger.info(f"Redis cache initialized successfully: {redis_url}")
        return True

    except Exception as e:
        logger.warning(f"Redis initialization failed, caching disabled: {e}")
        _redis_enabled = False
        _redis_client = None
        _redis_pool = None
        return False


def redis_available() -> bool:
    """
    Check if Redis is available and operational.

    Returns:
        True if Redis is available, False otherwise
    """
    if not _redis_enabled:
        _initialize_redis()

    return _redis_enabled


def _get_redis_client() -> Optional[Redis]:
    """
    Get Redis client instance, initializing if necessary.

    Returns:
        Redis client instance or None if unavailable
    """
    global _redis_client

    if _redis_client is None:
        _initialize_redis()

    return _redis_client if _redis_enabled else None


def _serialize_job_response(job: Dict[str, Any]) -> str:
    """
    Serialize job response to JSON string for caching.

    Args:
        job: Job dictionary from database

    Returns:
        JSON string representation
    """
    # Create a copy to avoid modifying original
    job_copy = job.copy()

    # Convert datetime objects to ISO format strings
    for key in ["created_at", "updated_at", "approved_at"]:
        if key in job_copy and job_copy[key]:
            if isinstance(job_copy[key], datetime):
                job_copy[key] = job_copy[key].isoformat()

    return json.dumps(job_copy)


def _deserialize_job_response(json_str: str) -> Dict[str, Any]:
    """
    Deserialize job response from JSON string.

    Args:
        json_str: JSON string from cache

    Returns:
        Job dictionary
    """
    job = json.loads(json_str)

    # Convert ISO format strings back to strings (database layer expects strings)
    # The conversion to datetime objects is handled by the API response models

    return job


def get_job_with_cache(job_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve job from cache or database.

    This function first checks Redis cache. On cache miss, it fetches from
    the database and stores in cache for future requests.

    Args:
        job_id: The video job ID

    Returns:
        Job dictionary or None if not found
    """
    cache_key = f"{JOB_CACHE_KEY_PREFIX}:{job_id}:progress"
    client = _get_redis_client()

    # Try cache first
    if client:
        try:
            cached_data = client.get(cache_key)
            if cached_data:
                _cache_stats["hits"] += 1
                logger.debug(f"Cache HIT for job {job_id}")
                return _deserialize_job_response(cached_data)
            else:
                _cache_stats["misses"] += 1
                logger.debug(f"Cache MISS for job {job_id}")
        except Exception as e:
            _cache_stats["errors"] += 1
            logger.warning(f"Redis GET error for job {job_id}: {e}")
            # Continue to database fallback

    # Cache miss or Redis unavailable - fetch from database
    job = get_job(job_id)

    if job and client:
        # Store in cache for future requests
        try:
            serialized = _serialize_job_response(job)
            client.setex(cache_key, CACHE_TTL_SECONDS, serialized)
            logger.debug(f"Cached job {job_id} with TTL={CACHE_TTL_SECONDS}s")
        except Exception as e:
            _cache_stats["errors"] += 1
            logger.warning(f"Redis SETEX error for job {job_id}: {e}")

    return job


def update_job_progress_with_cache(job_id: int, progress: dict) -> bool:
    """
    Update job progress in database and invalidate cache.

    This function updates the database using the existing update_job_progress()
    function, then invalidates the Redis cache to ensure fresh data on next read.
    Optionally pre-warms the cache with updated data.

    Args:
        job_id: The video job ID
        progress: Dictionary containing progress information

    Returns:
        True on success, False on failure
    """
    # Update database first
    success = update_job_progress(job_id, progress)

    if not success:
        return False

    # Invalidate cache
    invalidate_job_cache(job_id)

    # Optional: Pre-warm cache with updated data
    client = _get_redis_client()
    if client:
        try:
            # Fetch fresh data from database
            job = get_job(job_id)
            if job:
                cache_key = f"{JOB_CACHE_KEY_PREFIX}:{job_id}:progress"
                serialized = _serialize_job_response(job)
                client.setex(cache_key, CACHE_TTL_SECONDS, serialized)
                logger.debug(f"Pre-warmed cache for job {job_id} after update")
        except Exception as e:
            _cache_stats["errors"] += 1
            logger.warning(f"Cache pre-warm error for job {job_id}: {e}")

    return True


def invalidate_job_cache(job_id: int) -> None:
    """
    Invalidate Redis cache for a specific job.

    This should be called whenever job data is updated to ensure
    clients receive fresh data.

    Args:
        job_id: The video job ID
    """
    client = _get_redis_client()
    if not client:
        return

    try:
        cache_key = f"{JOB_CACHE_KEY_PREFIX}:{job_id}:progress"
        deleted = client.delete(cache_key)
        _cache_stats["invalidations"] += 1

        if deleted:
            logger.debug(f"Invalidated cache for job {job_id}")
        else:
            logger.debug(f"No cache entry to invalidate for job {job_id}")
    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"Cache invalidation error for job {job_id}: {e}")


def invalidate_user_jobs_cache(client_id: str) -> None:
    """
    Invalidate Redis cache for all jobs belonging to a user/client.

    This is useful when user-level job lists need to be refreshed.
    Currently implemented as a pattern-based delete.

    Args:
        client_id: The client identifier
    """
    client = _get_redis_client()
    if not client:
        return

    try:
        # Delete user's job list cache
        user_cache_key = f"{USER_JOBS_KEY_PREFIX}:{client_id}"
        deleted = client.delete(user_cache_key)
        _cache_stats["invalidations"] += 1

        if deleted:
            logger.debug(f"Invalidated jobs cache for client {client_id}")
        else:
            logger.debug(f"No jobs cache entry for client {client_id}")

        # Note: We don't invalidate individual job caches here as they may be
        # shared across users (jobs are accessed by ID, not client_id)

    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"User jobs cache invalidation error for client {client_id}: {e}")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics.

    Returns:
        Dictionary containing cache metrics:
        - hits: Number of cache hits
        - misses: Number of cache misses
        - errors: Number of Redis errors
        - invalidations: Number of cache invalidations
        - hit_rate: Cache hit rate percentage
        - redis_enabled: Whether Redis is currently enabled
        - redis_available: Whether Redis library is installed
    """
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0

    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "errors": _cache_stats["errors"],
        "invalidations": _cache_stats["invalidations"],
        "hit_rate": round(hit_rate, 2),
        "total_requests": total_requests,
        "redis_enabled": _redis_enabled,
        "redis_available": REDIS_AVAILABLE,
        "ttl_seconds": CACHE_TTL_SECONDS
    }


def reset_cache_stats() -> None:
    """
    Reset cache statistics counters.

    This is useful for testing or periodic statistics reporting.
    """
    global _cache_stats
    _cache_stats = {
        "hits": 0,
        "misses": 0,
        "errors": 0,
        "invalidations": 0
    }
    logger.info("Cache statistics reset")


def close_redis_connection() -> None:
    """
    Close Redis connection pool.

    This should be called when shutting down the application.
    """
    global _redis_pool, _redis_client, _redis_enabled

    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")

    if _redis_pool:
        try:
            _redis_pool.disconnect()
            logger.info("Redis connection pool disconnected")
        except Exception as e:
            logger.warning(f"Error disconnecting Redis pool: {e}")

    _redis_client = None
    _redis_pool = None
    _redis_enabled = False
