"""Cache layer for job progress tracking - SQLite-based POC implementation."""

from .sqlite_cache import (
    get_job_with_cache,
    update_job_progress_with_cache,
    invalidate_job_cache,
    invalidate_user_jobs_cache,
    get_cache_stats,
    cleanup_expired,
)

# For compatibility with existing code that checks redis_available
redis_available = False  # We're using SQLite, not Redis

__all__ = [
    "get_job_with_cache",
    "update_job_progress_with_cache",
    "invalidate_job_cache",
    "invalidate_user_jobs_cache",
    "get_cache_stats",
    "cleanup_expired",
    "redis_available",
]
