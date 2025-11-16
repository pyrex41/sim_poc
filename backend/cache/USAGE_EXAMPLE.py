"""
Usage examples for Redis caching layer.

This file demonstrates how to use the caching system in different scenarios.
"""

from backend.cache import (
    get_job_with_cache,
    update_job_progress_with_cache,
    invalidate_job_cache,
    invalidate_user_jobs_cache,
    get_cache_stats,
    redis_available
)


def example_1_basic_usage():
    """Example 1: Basic job retrieval with caching."""
    print("Example 1: Basic Job Retrieval")
    print("-" * 50)

    job_id = 123

    # First request - cache miss, fetches from DB
    print(f"Fetching job {job_id}...")
    job = get_job_with_cache(job_id)

    if job:
        print(f"  Job ID: {job['id']}")
        print(f"  Status: {job['status']}")
        print(f"  Progress: {job.get('progress', {})}")
    else:
        print(f"  Job {job_id} not found")

    # Second request within 30s - cache hit
    print(f"\nFetching job {job_id} again (should be cached)...")
    job = get_job_with_cache(job_id)
    print(f"  Retrieved from cache")

    # Check stats
    stats = get_cache_stats()
    print(f"\nCache Stats:")
    print(f"  Hit rate: {stats['hit_rate']}%")
    print(f"  Hits: {stats['hits']}, Misses: {stats['misses']}")


def example_2_progress_updates():
    """Example 2: Updating job progress with cache invalidation."""
    print("\nExample 2: Progress Updates")
    print("-" * 50)

    job_id = 123

    # Update progress
    progress_data = {
        "current_stage": "rendering",
        "scenes_total": 5,
        "scenes_completed": 3,
        "current_scene": 4,
        "estimated_completion_seconds": 45,
        "message": "Rendering scene 4 of 5..."
    }

    print(f"Updating progress for job {job_id}...")
    success = update_job_progress_with_cache(job_id, progress_data)

    if success:
        print(f"  ✓ Progress updated successfully")
        print(f"  ✓ Cache invalidated")
        print(f"  ✓ Cache pre-warmed with new data")

        # Fetch updated job (will use pre-warmed cache)
        job = get_job_with_cache(job_id)
        print(f"\nUpdated job status:")
        print(f"  Current stage: {job['progress']['current_stage']}")
        print(f"  Scenes completed: {job['progress']['scenes_completed']}/{job['progress']['scenes_total']}")
    else:
        print(f"  ✗ Failed to update progress")


def example_3_cache_invalidation():
    """Example 3: Manual cache invalidation."""
    print("\nExample 3: Cache Invalidation")
    print("-" * 50)

    job_id = 123
    client_id = "user@example.com"

    # Invalidate specific job
    print(f"Invalidating cache for job {job_id}...")
    invalidate_job_cache(job_id)
    print(f"  ✓ Job cache invalidated")

    # Invalidate user's job list (future enhancement)
    print(f"\nInvalidating all jobs for client {client_id}...")
    invalidate_user_jobs_cache(client_id)
    print(f"  ✓ User jobs cache invalidated")


def example_4_monitoring():
    """Example 4: Monitoring cache performance."""
    print("\nExample 4: Cache Monitoring")
    print("-" * 50)

    # Check if Redis is available
    if redis_available():
        print("✓ Redis is available and operational")
    else:
        print("✗ Redis is unavailable (using database fallback)")

    # Get detailed statistics
    stats = get_cache_stats()

    print(f"\nCache Statistics:")
    print(f"  Enabled: {stats['redis_enabled']}")
    print(f"  Available: {stats['redis_available']}")
    print(f"  TTL: {stats['ttl_seconds']} seconds")
    print(f"\nPerformance:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']}%")
    print(f"  Errors: {stats['errors']}")
    print(f"  Invalidations: {stats['invalidations']}")


def example_5_error_handling():
    """Example 5: Graceful error handling."""
    print("\nExample 5: Error Handling")
    print("-" * 50)

    # Even if Redis is down, the system continues working
    job_id = 123

    try:
        print(f"Fetching job {job_id}...")
        job = get_job_with_cache(job_id)

        if job:
            print(f"  ✓ Job retrieved successfully")
            print(f"  Status: {job['status']}")

            # If Redis is down, this will log a warning but still work
            if redis_available():
                print(f"  Source: Redis cache")
            else:
                print(f"  Source: Database (Redis unavailable)")
        else:
            print(f"  Job not found")

    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_6_typical_workflow():
    """Example 6: Typical video generation workflow with caching."""
    print("\nExample 6: Typical Workflow")
    print("-" * 50)

    job_id = 456

    # Step 1: Job created (not cached yet)
    print("Step 1: Job created")
    print(f"  Job ID: {job_id}")

    # Step 2: Client starts polling
    print("\nStep 2: Client polling (every 3 seconds)")

    for poll_count in range(1, 6):
        print(f"\n  Poll #{poll_count}")
        job = get_job_with_cache(job_id)

        if job:
            stats = get_cache_stats()
            source = "cache" if stats['hits'] > 0 else "database"
            print(f"    Status: {job['status']}")
            print(f"    Source: {source}")
            print(f"    Hit rate: {stats['hit_rate']}%")

        # Simulate progress update after 2nd poll
        if poll_count == 2:
            print(f"\n  → Progress update triggered")
            update_job_progress_with_cache(job_id, {
                "current_stage": "generating_storyboard",
                "scenes_completed": 2,
                "scenes_total": 5
            })
            print(f"    Cache invalidated and pre-warmed")

    # Step 3: Final statistics
    print("\nStep 3: Final Statistics")
    stats = get_cache_stats()
    print(f"  Total polls: 5")
    print(f"  Database queries: {stats['misses']} (cache misses) + 1 (update)")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Database load reduction: {(stats['hits'] / stats['total_requests'] * 100):.0f}%")


def example_7_concurrent_users():
    """Example 7: Multiple users polling the same job."""
    print("\nExample 7: Concurrent Users")
    print("-" * 50)

    job_id = 789

    print("Simulating 10 concurrent users polling the same job...")
    print("(All users get cached data after first request)\n")

    for user in range(1, 11):
        job = get_job_with_cache(job_id)
        stats = get_cache_stats()

        source = "database" if user == 1 else "cache"
        print(f"  User {user:2d}: Retrieved job {job_id} from {source}")

    stats = get_cache_stats()
    print(f"\nResult:")
    print(f"  Database queries: 1 (first user)")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Database load: {(1 / stats['total_requests'] * 100):.0f}% of what it would be without cache")


# Example usage
if __name__ == "__main__":
    print("=" * 50)
    print("Redis Caching Layer - Usage Examples")
    print("=" * 50)

    # Run examples
    example_1_basic_usage()
    example_2_progress_updates()
    example_3_cache_invalidation()
    example_4_monitoring()
    example_5_error_handling()
    example_6_typical_workflow()
    example_7_concurrent_users()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("=" * 50)


# Integration with FastAPI endpoints
def fastapi_endpoint_examples():
    """
    Examples of how the caching is used in FastAPI endpoints.
    """

    # Example 1: Job status endpoint
    from fastapi import HTTPException

    async def get_job_status(job_id: int):
        """Get job status with caching."""
        # Use cache-aware function
        job = get_job_with_cache(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "job_id": job["id"],
            "status": job["status"],
            "progress": job["progress"]
        }

    # Example 2: Approve storyboard endpoint
    async def approve_storyboard(job_id: int):
        """Approve storyboard and invalidate cache."""
        # Get job from cache
        job = get_job_with_cache(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Perform approval (database operation)
        from backend.database import approve_storyboard as db_approve
        success = db_approve(job_id)

        if success:
            # Invalidate cache so next request gets fresh data
            invalidate_job_cache(job_id)

        return {"success": success}

    # Example 3: Update progress endpoint
    async def update_progress(job_id: int, progress: dict):
        """Update progress with automatic cache management."""
        # Uses cache-aware function that handles invalidation
        success = update_job_progress_with_cache(job_id, progress)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update progress")

        return {"success": True}

    # Example 4: Cache stats monitoring endpoint
    async def cache_statistics():
        """Get cache performance metrics."""
        stats = get_cache_stats()

        return {
            "cache_enabled": redis_available(),
            "statistics": stats,
            "message": "Cache is working normally" if stats["redis_enabled"]
                      else "Cache is disabled or unavailable"
        }
