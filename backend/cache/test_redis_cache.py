"""
Unit tests for Redis caching layer.

Run with: pytest backend/cache/test_redis_cache.py -v
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from .redis_cache import (
    get_job_with_cache,
    update_job_progress_with_cache,
    invalidate_job_cache,
    invalidate_user_jobs_cache,
    get_cache_stats,
    reset_cache_stats,
    redis_available,
    _serialize_job_response,
    _deserialize_job_response
)


@pytest.fixture
def sample_job():
    """Sample job data for testing."""
    return {
        "id": 123,
        "prompt": "Test video",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "progress": {
            "current_stage": "pending",
            "scenes_total": 5,
            "scenes_completed": 0
        },
        "estimated_cost": 1.50,
        "video_url": None
    }


@pytest.fixture
def sample_job_with_datetime():
    """Sample job with datetime objects."""
    return {
        "id": 456,
        "prompt": "Test video 2",
        "status": "completed",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 13, 0, 0),
        "approved_at": datetime(2024, 1, 1, 12, 30, 0),
        "progress": {},
        "estimated_cost": 2.00,
        "actual_cost": 1.95
    }


class TestSerialization:
    """Test JSON serialization/deserialization."""

    def test_serialize_job_basic(self, sample_job):
        """Test serialization of basic job data."""
        result = _serialize_job_response(sample_job)
        assert isinstance(result, str)

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed["id"] == 123
        assert parsed["prompt"] == "Test video"

    def test_serialize_datetime_objects(self, sample_job_with_datetime):
        """Test serialization converts datetime to ISO format."""
        result = _serialize_job_response(sample_job_with_datetime)
        parsed = json.loads(result)

        # Check datetime conversion
        assert parsed["created_at"] == "2024-01-01T12:00:00"
        assert parsed["updated_at"] == "2024-01-01T13:00:00"
        assert parsed["approved_at"] == "2024-01-01T12:30:00"

    def test_deserialize_job(self, sample_job):
        """Test deserialization of job data."""
        serialized = _serialize_job_response(sample_job)
        result = _deserialize_job_response(serialized)

        assert result["id"] == sample_job["id"]
        assert result["prompt"] == sample_job["prompt"]
        assert result["progress"] == sample_job["progress"]

    def test_roundtrip_serialization(self, sample_job):
        """Test serialize -> deserialize roundtrip."""
        serialized = _serialize_job_response(sample_job)
        deserialized = _deserialize_job_response(serialized)

        # Most fields should match (datetime strings may differ)
        assert deserialized["id"] == sample_job["id"]
        assert deserialized["status"] == sample_job["status"]
        assert deserialized["progress"] == sample_job["progress"]


class TestCacheFallback:
    """Test graceful fallback when Redis is unavailable."""

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.get_job')
    def test_get_job_redis_unavailable(self, mock_get_job, mock_redis_client, sample_job):
        """Test fallback to database when Redis is unavailable."""
        # Redis returns None (unavailable)
        mock_redis_client.return_value = None
        mock_get_job.return_value = sample_job

        result = get_job_with_cache(123)

        assert result == sample_job
        mock_get_job.assert_called_once_with(123)

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.update_job_progress')
    def test_update_job_redis_unavailable(self, mock_update, mock_redis_client):
        """Test update works when Redis is unavailable."""
        mock_redis_client.return_value = None
        mock_update.return_value = True

        progress = {"current_stage": "rendering"}
        result = update_job_progress_with_cache(123, progress)

        assert result is True
        mock_update.assert_called_once_with(123, progress)


class TestCacheHitMiss:
    """Test cache hit and miss scenarios."""

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.get_job')
    def test_cache_hit(self, mock_get_job, mock_redis_client, sample_job):
        """Test successful cache hit."""
        # Setup mock Redis
        mock_client = MagicMock()
        cached_data = _serialize_job_response(sample_job)
        mock_client.get.return_value = cached_data
        mock_redis_client.return_value = mock_client

        reset_cache_stats()
        result = get_job_with_cache(123)

        # Should return cached data without calling database
        assert result["id"] == sample_job["id"]
        mock_client.get.assert_called_once()
        mock_get_job.assert_not_called()

        # Verify stats
        stats = get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.get_job')
    def test_cache_miss(self, mock_get_job, mock_redis_client, sample_job):
        """Test cache miss and database fallback."""
        # Setup mock Redis with cache miss
        mock_client = MagicMock()
        mock_client.get.return_value = None  # Cache miss
        mock_redis_client.return_value = mock_client
        mock_get_job.return_value = sample_job

        reset_cache_stats()
        result = get_job_with_cache(123)

        # Should fetch from database and cache it
        assert result["id"] == sample_job["id"]
        mock_client.get.assert_called_once()
        mock_get_job.assert_called_once_with(123)
        mock_client.setex.assert_called_once()  # Should cache the result

        # Verify stats
        stats = get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1


class TestCacheInvalidation:
    """Test cache invalidation."""

    @patch('backend.cache.redis_cache._get_redis_client')
    def test_invalidate_job_cache(self, mock_redis_client):
        """Test invalidating a specific job's cache."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_redis_client.return_value = mock_client

        reset_cache_stats()
        invalidate_job_cache(123)

        # Should delete the cache key
        mock_client.delete.assert_called_once_with("job:123:progress")

        stats = get_cache_stats()
        assert stats["invalidations"] == 1

    @patch('backend.cache.redis_cache._get_redis_client')
    def test_invalidate_user_jobs_cache(self, mock_redis_client):
        """Test invalidating user's job list cache."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_redis_client.return_value = mock_client

        invalidate_user_jobs_cache("test_user")

        # Should delete user's jobs cache
        mock_client.delete.assert_called_once_with("jobs:test_user")

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.update_job_progress')
    @patch('backend.cache.redis_cache.get_job')
    def test_update_invalidates_cache(self, mock_get_job, mock_update, mock_redis_client, sample_job):
        """Test that update invalidates and pre-warms cache."""
        mock_client = MagicMock()
        mock_redis_client.return_value = mock_client
        mock_update.return_value = True
        mock_get_job.return_value = sample_job

        progress = {"current_stage": "rendering"}
        result = update_job_progress_with_cache(123, progress)

        assert result is True
        # Should update database
        mock_update.assert_called_once_with(123, progress)
        # Should delete old cache
        mock_client.delete.assert_called()
        # Should pre-warm with new data
        mock_client.setex.assert_called()


class TestCacheStats:
    """Test cache statistics."""

    def test_initial_stats(self):
        """Test initial cache statistics."""
        reset_cache_stats()
        stats = get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0
        assert stats["invalidations"] == 0
        assert stats["hit_rate"] == 0.0
        assert "redis_enabled" in stats
        assert "redis_available" in stats

    def test_hit_rate_calculation(self):
        """Test hit rate percentage calculation."""
        reset_cache_stats()

        # Simulate some cache activity
        with patch('backend.cache.redis_cache._cache_stats', {"hits": 7, "misses": 3, "errors": 0, "invalidations": 0}):
            stats = get_cache_stats()
            assert stats["hit_rate"] == 70.0  # 7/10 = 70%

    def test_reset_stats(self):
        """Test resetting cache statistics."""
        # Modify stats
        with patch('backend.cache.redis_cache._cache_stats', {"hits": 10, "misses": 5, "errors": 1, "invalidations": 2}):
            stats = get_cache_stats()
            assert stats["hits"] == 10

        # Reset
        reset_cache_stats()
        stats = get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestErrorHandling:
    """Test error handling and resilience."""

    @patch('backend.cache.redis_cache._get_redis_client')
    @patch('backend.cache.redis_cache.get_job')
    def test_redis_error_fallback(self, mock_get_job, mock_redis_client, sample_job):
        """Test fallback to database on Redis error."""
        # Setup Redis to raise exception
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_redis_client.return_value = mock_client
        mock_get_job.return_value = sample_job

        reset_cache_stats()
        result = get_job_with_cache(123)

        # Should still return data from database
        assert result == sample_job
        mock_get_job.assert_called_once_with(123)

        # Should track error
        stats = get_cache_stats()
        assert stats["errors"] >= 1

    @patch('backend.cache.redis_cache._get_redis_client')
    def test_invalidate_nonexistent_key(self, mock_redis_client):
        """Test invalidating a non-existent cache key."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0  # Key didn't exist
        mock_redis_client.return_value = mock_client

        # Should not raise exception
        invalidate_job_cache(999)
        mock_client.delete.assert_called_once()


# Integration test (requires actual Redis)
@pytest.mark.integration
@pytest.mark.skipif(not redis_available(), reason="Redis not available")
class TestRealRedis:
    """Integration tests with real Redis (optional)."""

    def test_real_redis_connection(self):
        """Test actual Redis connection."""
        assert redis_available() is True

    def test_real_cache_operations(self, sample_job):
        """Test real cache set/get operations."""
        # This test requires actual Redis running
        # Reset stats
        reset_cache_stats()

        # First call should be a miss
        with patch('backend.cache.redis_cache.get_job', return_value=sample_job):
            result1 = get_job_with_cache(999)
            assert result1["id"] == sample_job["id"]

        stats = get_cache_stats()
        assert stats["misses"] == 1

        # Second call should be a hit (if Redis is working)
        result2 = get_job_with_cache(999)
        if stats["redis_enabled"]:
            stats = get_cache_stats()
            assert stats["hits"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
