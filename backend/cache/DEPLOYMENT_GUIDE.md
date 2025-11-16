# Redis Caching Deployment Guide

## Quick Start

### 1. Install Redis Client Library

```bash
pip install redis>=5.0.0
```

Or update from requirements:

```bash
pip install -r backend/requirements.txt
```

### 2. Start Redis Server

**Option A: Docker (Recommended for Development)**

```bash
docker run -d \
  --name redis-cache \
  -p 6379:6379 \
  redis:7-alpine
```

**Option B: Docker Compose**

Add to your `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis-data:
```

Then start:

```bash
docker-compose up -d redis
```

**Option C: Local Installation**

macOS (Homebrew):
```bash
brew install redis
brew services start redis
```

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 3. Configure Environment

Add to your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 4. Restart API Server

```bash
cd backend
python -m uvicorn main:app --reload
```

### 5. Verify Installation

```bash
# Check Redis is running
redis-cli ping
# Should output: PONG

# Check cache statistics
curl http://localhost:8000/api/v2/cache/stats

# Should see:
# {
#   "cache_enabled": true,
#   "statistics": {
#     "redis_enabled": true,
#     ...
#   }
# }
```

## Production Deployment

### AWS ElastiCache

1. **Create Redis Cluster**

```bash
# Via AWS CLI
aws elasticache create-cache-cluster \
  --cache-cluster-id video-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

2. **Get Endpoint**

```bash
aws elasticache describe-cache-clusters \
  --cache-cluster-id video-cache \
  --show-cache-node-info
```

3. **Configure Application**

```bash
REDIS_URL=redis://video-cache.abc123.use1.cache.amazonaws.com:6379/0
```

### Redis Cloud

1. **Create Database** at https://redis.com/try-free/

2. **Get Connection String**

```bash
REDIS_URL=redis://:password@redis-12345.cloud.redislabs.com:12345
```

### Google Cloud Memorystore

1. **Create Instance**

```bash
gcloud redis instances create video-cache \
  --size=1 \
  --region=us-central1 \
  --tier=basic
```

2. **Get IP Address**

```bash
gcloud redis instances describe video-cache \
  --region=us-central1 \
  --format="get(host)"
```

3. **Configure Application**

```bash
REDIS_URL=redis://10.0.0.3:6379/0
```

### Azure Cache for Redis

1. **Create Cache**

```bash
az redis create \
  --name video-cache \
  --resource-group myResourceGroup \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

2. **Get Access Keys**

```bash
az redis list-keys \
  --name video-cache \
  --resource-group myResourceGroup
```

3. **Configure Application**

```bash
REDIS_URL=redis://:primary-key@video-cache.redis.cache.windows.net:6380?ssl=true
```

## Configuration Options

### Environment Variables

```bash
# Basic configuration
REDIS_URL=redis://localhost:6379/0

# With password
REDIS_URL=redis://:password@localhost:6379/0

# SSL/TLS
REDIS_URL=redis://:password@localhost:6380?ssl=true

# Redis Sentinel
REDIS_URL=redis+sentinel://sentinel1:26379,sentinel2:26379/mymaster/0

# Redis Cluster
REDIS_URL=redis://node1:7000,node2:7000,node3:7000?cluster=true
```

### Redis Server Configuration

Recommended `redis.conf` settings for production:

```conf
# Persistence
appendonly yes
appendfsync everysec

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security
requirepass your-strong-password
bind 127.0.0.1  # Or private IP

# Performance
tcp-backlog 511
timeout 300
```

## Monitoring

### Health Checks

Add to your monitoring:

```bash
#!/bin/bash
# check-redis.sh

# Check Redis is responding
redis-cli -h localhost -p 6379 ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Redis is DOWN"
  exit 1
fi

# Check cache stats via API
curl -f http://localhost:8000/api/v2/cache/stats > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Cache stats endpoint is DOWN"
  exit 1
fi

echo "Redis is healthy"
exit 0
```

### CloudWatch Metrics (AWS)

Monitor these ElastiCache metrics:

- `EngineCPUUtilization` - Should be < 80%
- `DatabaseMemoryUsagePercentage` - Should be < 90%
- `CacheHits` and `CacheMisses` - Track hit rate
- `NetworkBytesIn/Out` - Monitor traffic
- `Evictions` - Should be low

### Prometheus Metrics

Export cache stats for Prometheus:

```python
# Add to your metrics endpoint
from prometheus_client import Gauge

cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate percentage')
cache_requests = Gauge('cache_requests_total', 'Total cache requests')

@app.get("/metrics")
def metrics():
    stats = get_cache_stats()
    cache_hit_rate.set(stats['hit_rate'])
    cache_requests.set(stats['total_requests'])
    # ... return prometheus metrics
```

## Performance Tuning

### Optimal TTL Selection

Current: 30 seconds

Adjust based on your polling frequency:

| Polling Interval | Recommended TTL | Cache Efficiency |
|-----------------|-----------------|------------------|
| 1 second | 10-15 seconds | Medium |
| 2-3 seconds | 30 seconds | High ✓ |
| 5 seconds | 30-60 seconds | Very High |
| 10+ seconds | 60+ seconds | Very High |

### Connection Pool Sizing

Current: 10 connections

Adjust based on concurrent users:

| Concurrent Users | Pool Size | Memory Impact |
|-----------------|-----------|---------------|
| 1-50 | 5-10 | Low ✓ |
| 50-200 | 10-20 | Medium |
| 200-1000 | 20-50 | High |
| 1000+ | 50-100 | Very High |

### Memory Usage

Estimate Redis memory needs:

```
Single job entry ≈ 2 KB
Cache TTL = 30 seconds
Polling rate = 3 seconds/request

Jobs in cache = Active jobs × (TTL / Polling rate)
              = Active jobs × 10

For 100 active jobs:
Memory needed ≈ 100 jobs × 10 entries × 2 KB = 2 MB

Recommended Redis memory: 5-10x estimated = 20-40 MB
```

## Security

### Network Security

1. **Private Network**
   - Deploy Redis in private subnet
   - Use VPC peering or private link
   - Never expose Redis to internet

2. **Firewall Rules**
   ```bash
   # Only allow API servers
   iptables -A INPUT -p tcp --dport 6379 -s 10.0.1.0/24 -j ACCEPT
   iptables -A INPUT -p tcp --dport 6379 -j DROP
   ```

3. **VPN/Bastion**
   - Access Redis only through VPN
   - Use bastion host for maintenance

### Authentication

1. **Require Password**
   ```conf
   # redis.conf
   requirepass your-very-strong-password-here
   ```

2. **Use Strong Passwords**
   ```bash
   # Generate strong password
   openssl rand -base64 32
   ```

3. **Rotate Credentials**
   - Rotate passwords quarterly
   - Use secrets management (AWS Secrets Manager, Vault)

### TLS/SSL

Enable encryption in transit:

```conf
# redis.conf
tls-port 6380
port 0  # Disable non-TLS
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
```

Update connection:
```bash
REDIS_URL=redis://:password@localhost:6380?ssl=true&ssl_cert_reqs=required
```

## Troubleshooting

### Issue: Cache Not Working

**Symptoms:**
- Cache stats show `redis_enabled: false`
- All requests show cache misses

**Solutions:**

1. **Check Redis is running**
   ```bash
   redis-cli ping
   # Should output: PONG
   ```

2. **Check connection**
   ```bash
   redis-cli -h localhost -p 6379
   > AUTH your-password  # if password set
   > PING
   ```

3. **Check logs**
   ```bash
   tail -f logs/app.log | grep -i redis
   # Look for connection errors
   ```

4. **Verify REDIS_URL**
   ```bash
   echo $REDIS_URL
   # Should match your Redis instance
   ```

### Issue: High Memory Usage

**Symptoms:**
- Redis memory > expected
- Evictions increasing

**Solutions:**

1. **Check key count**
   ```bash
   redis-cli DBSIZE
   ```

2. **Reduce TTL**
   ```python
   # In redis_cache.py
   CACHE_TTL_SECONDS = 15  # Reduce from 30
   ```

3. **Set memory limit**
   ```conf
   # redis.conf
   maxmemory 256mb
   maxmemory-policy allkeys-lru
   ```

### Issue: Connection Timeouts

**Symptoms:**
- Intermittent cache errors
- Timeout exceptions in logs

**Solutions:**

1. **Increase timeout**
   ```python
   # In redis_cache.py
   socket_connect_timeout=5,  # Increase from 2
   socket_timeout=5,
   ```

2. **Increase pool size**
   ```python
   max_connections=20,  # Increase from 10
   ```

3. **Check network latency**
   ```bash
   redis-cli --latency -h redis-server
   ```

## Rollback Plan

If you need to disable caching:

### Option 1: Stop Redis

```bash
# Docker
docker stop redis-cache

# System service
sudo systemctl stop redis
```

System automatically falls back to database.

### Option 2: Invalid REDIS_URL

```bash
# Set to invalid URL
export REDIS_URL=redis://invalid:9999
```

### Option 3: Remove Package

```bash
pip uninstall redis -y
```

System gracefully handles missing package.

**No code changes needed for rollback!**

## Upgrade Path

### From No Cache → Redis Cache

✅ Already implemented!

### Future: Redis → Redis Cluster

When scaling beyond single Redis:

1. Update connection URL
2. Enable cluster mode
3. No code changes needed

### Future: Add Read Replicas

1. Configure Redis replication
2. Use read replica for gets
3. Use master for writes

## Checklist

Before deploying to production:

- [ ] Redis server running and accessible
- [ ] REDIS_URL environment variable set
- [ ] Password authentication enabled
- [ ] Network security configured (firewall, VPC)
- [ ] TLS/SSL enabled for production
- [ ] Monitoring and alerts configured
- [ ] Backup strategy in place
- [ ] Rollback plan tested
- [ ] Performance baseline established
- [ ] Cache stats endpoint monitored

## Support

For issues or questions:

1. Check logs: `tail -f logs/app.log | grep cache`
2. Check cache stats: `curl http://localhost:8000/api/v2/cache/stats`
3. Test Redis: `redis-cli ping`
4. Review documentation: `backend/cache/README.md`

Remember: The system works perfectly without Redis - it's an optimization, not a requirement!
