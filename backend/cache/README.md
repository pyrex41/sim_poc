# Redis Caching Layer

## Overview

This module implements Redis-based caching for video generation job progress tracking. It significantly reduces database load from frequent job status polling by caching job responses in Redis with a 30-second TTL.

## Features

- **Transparent Caching**: Drop-in replacement for direct database queries
- **Graceful Degradation**: Automatically falls back to database if Redis is unavailable
- **Cache Invalidation**: Automatic cache invalidation on job updates
- **Cache Pre-warming**: Optionally pre-warms cache after updates for immediate consistency
- **Connection Pooling**: Efficient Redis connection management
- **Statistics Tracking**: Built-in cache performance metrics
- **Optional Dependency**: System works perfectly without Redis installed

## Architecture

```
┌─────────────────┐
│  API Endpoint   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ get_job_with_cache()    │
└────────┬────────────────┘
         │
    ┌────▼─────┐
    │ Redis?   │
    └──┬───┬───┘
       │   │
    Yes│   │No
       │   │
    ┌──▼───▼────┐
    │ get_job() │  ◄── Database
    └───────────┘
```

## Usage

### Basic Usage

```python
from backend.cache import get_job_with_cache, update_job_progress_with_cache

# Get job (checks cache first, falls back to DB)
job = get_job_with_cache(job_id=123)

# Update job progress (updates DB and invalidates cache)
success = update_job_progress_with_cache(
    job_id=123,
    progress={
        "current_stage": "rendering",
        "scenes_completed": 3,
        "scenes_total": 5
    }
)
```

### Cache Invalidation

```python
from backend.cache import invalidate_job_cache, invalidate_user_jobs_cache

# Invalidate specific job cache
invalidate_job_cache(job_id=123)

# Invalidate all jobs for a user
invalidate_user_jobs_cache(client_id="user@example.com")
```

### Cache Statistics

```python
from backend.cache import get_cache_stats, redis_available

# Check if Redis is available
if redis_available():
    print("Redis caching enabled")

# Get cache performance metrics
stats = get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']}%")
print(f"Total requests: {stats['total_requests']}")
```

## Configuration

### Environment Variables

Set Redis connection URL in `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
```

For production with authentication:

```bash
REDIS_URL=redis://:password@redis.example.com:6379/0
```

For Redis Cluster or Sentinel, use appropriate URL format.

### Cache Configuration

Configuration constants in `redis_cache.py`:

```python
CACHE_TTL_SECONDS = 30  # Cache TTL in seconds
JOB_CACHE_KEY_PREFIX = "job"  # Key prefix for job cache
```

## API Endpoints

### GET /api/v2/cache/stats

Get cache performance statistics.

**Response:**
```json
{
  "cache_enabled": true,
  "statistics": {
    "hits": 1250,
    "misses": 150,
    "errors": 2,
    "invalidations": 45,
    "hit_rate": 89.29,
    "total_requests": 1400,
    "redis_enabled": true,
    "redis_available": true,
    "ttl_seconds": 30
  },
  "message": "Cache is working normally"
}
```

### Job Status Endpoint (with caching)

The job status endpoint automatically uses caching:

```bash
GET /api/v2/jobs/{job_id}
```

Subsequent requests within 30 seconds are served from cache, reducing database load.

## Installation

### Install Redis Dependency

```bash
pip install redis>=5.0.0
```

Or use the requirements file:

```bash
pip install -r backend/requirements.txt
```

### Start Redis Server

**Using Docker:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Using Homebrew (macOS):**
```bash
brew install redis
brew services start redis
```

**Using apt (Ubuntu/Debian):**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest backend/cache/test_redis_cache.py -v

# Run specific test class
pytest backend/cache/test_redis_cache.py::TestCacheHitMiss -v

# Run with coverage
pytest backend/cache/test_redis_cache.py --cov=backend.cache --cov-report=html
```

### Integration Tests

Integration tests require a running Redis instance:

```bash
# Run integration tests
pytest backend/cache/test_redis_cache.py -v -m integration
```

### Manual Testing

Test cache behavior manually:

```bash
# Start the API server
cd backend
python -m uvicorn main:app --reload

# In another terminal, poll job status rapidly
for i in {1..10}; do
  curl http://localhost:8000/api/v2/jobs/1
  sleep 1
done

# Check cache statistics
curl http://localhost:8000/api/v2/cache/stats
```

## Performance Impact

### Without Caching

- Every job status request hits the database
- High database load with frequent polling (every 2-5 seconds)
- Database connection pool exhaustion under load
- Slow response times under concurrent load

### With Caching

- 90%+ cache hit rate for typical polling patterns
- 10-50x reduction in database queries
- Sub-millisecond response times for cache hits
- Predictable performance under concurrent load

### Example Metrics

For a video taking 2 minutes to render with client polling every 3 seconds:

| Metric | Without Cache | With Cache |
|--------|--------------|------------|
| Total requests | 40 | 40 |
| Database queries | 40 | 4-6 |
| Cache hits | 0 | 34-36 |
| Avg response time | 15-25ms | 1-3ms |
| Database load | 100% | 10-15% |

## Cache Key Patterns

- **Job cache**: `job:{job_id}:progress`
- **User jobs list**: `jobs:{client_id}` (future enhancement)
- **Storyboard cache**: `storyboard:{job_id}` (future enhancement)

## Monitoring

### Health Checks

```python
from backend.cache import redis_available

# In health check endpoint
if not redis_available():
    logger.warning("Redis cache unavailable, using database fallback")
```

### Logging

Cache operations are logged at DEBUG level:

```python
import logging
logging.getLogger('backend.cache.redis_cache').setLevel(logging.DEBUG)
```

Log messages include:
- Cache hits/misses
- Cache invalidations
- Redis errors (warnings)
- Cache pre-warming

### Metrics

Monitor these cache statistics:

- **Hit Rate**: Should be >80% for typical polling
- **Error Count**: Should be 0 in normal operation
- **Invalidations**: Should match update frequency
- **Total Requests**: Tracks usage volume

## Troubleshooting

### Redis Connection Failed

**Symptom:** Logs show "Redis initialization failed"

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_URL in environment
3. Check network connectivity
4. Verify Redis authentication if required

**Graceful Degradation:** System continues working with direct database queries.

### High Cache Miss Rate

**Symptom:** Hit rate < 50%

**Possible Causes:**
1. TTL too short (increase CACHE_TTL_SECONDS)
2. High job update frequency
3. Cache invalidation too aggressive
4. Redis memory eviction

**Solutions:**
- Increase TTL if acceptable
- Monitor Redis memory usage
- Check invalidation logic

### Memory Issues

**Symptom:** Redis memory usage high

**Solutions:**
1. Set Redis maxmemory policy: `maxmemory-policy allkeys-lru`
2. Monitor cache key count
3. Reduce TTL if needed
4. Implement cache size limits

## Future Enhancements

Potential improvements (marked as OPTIONAL in task):

1. **User Job List Caching**: Cache entire job lists per user
2. **Storyboard Caching**: Cache storyboard data separately
3. **Cache Warming**: Pre-warm cache on job creation
4. **Advanced Metrics**: Hit rate by endpoint, latency percentiles
5. **Cache Compression**: Compress large job responses
6. **Smart TTL**: Adjust TTL based on job status
7. **Background Refresh**: Refresh cache before expiry

## Security Considerations

1. **No Sensitive Data**: Job IDs are sequential integers (not UUIDs)
2. **Access Control**: Cache doesn't replace authorization checks
3. **Redis Auth**: Use Redis password in production
4. **Network Security**: Use Redis over private network/VPN
5. **Data Privacy**: Cache automatically expires after 30s

## Deployment

### Development

```bash
# Use local Redis
REDIS_URL=redis://localhost:6379/0
```

### Production

```bash
# Use managed Redis (e.g., AWS ElastiCache, Redis Cloud)
REDIS_URL=redis://:password@production-redis.example.com:6379/0

# Or disable caching if Redis unavailable
# (system works fine without it)
```

### Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  api:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis-data:
```

## License

Same as parent project.
