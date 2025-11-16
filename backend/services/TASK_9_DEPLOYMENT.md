# Task 9 Deployment Guide

## Prerequisites

### 1. System Requirements
- **ffmpeg** installed and available in system PATH
- Python 3.8+
- SQLite 3.8+

### 2. Check ffmpeg Installation
```bash
ffmpeg -version
```

If not installed:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Docker (in Dockerfile):**
```dockerfile
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ... rest of Dockerfile
```

---

## Environment Variables

Add to your `.env` file:

```bash
# Video storage path (for exports)
VIDEO_STORAGE_PATH=/data/videos
```

**Default:** `./DATA/videos` if not set

---

## Database Migration

The new columns are automatically created when the application starts. No manual migration needed.

**To verify:**
```bash
sqlite3 DATA/scenes.db "PRAGMA table_info(generated_videos);" | grep -E "(download_count|refinement_count)"
```

**Expected output:**
```
19|download_count|INTEGER|0|0|0
20|refinement_count|INTEGER|0|0|0
```

---

## Directory Structure

Ensure these directories exist and are writable:

```bash
mkdir -p DATA/videos/exports
chmod -R 755 DATA/videos
```

**Expected structure:**
```
DATA/
└── videos/
    ├── exports/
    │   ├── 1/          # Job ID 1 exports
    │   │   ├── mp4_high.mp4
    │   │   ├── webm_low.webm
    │   │   └── mov_medium.mov
    │   ├── 2/          # Job ID 2 exports
    │   └── ...
    └── [original videos]
```

---

## Docker Deployment

### 1. Update Dockerfile

**Add ffmpeg installation:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create data directories
RUN mkdir -p /data/videos/exports && \
    chmod -R 755 /data

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Update docker-compose.yml

**Add volume for persistent exports:**
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - VIDEO_STORAGE_PATH=/data/videos
      - REPLICATE_API_KEY=${REPLICATE_API_KEY}
    volumes:
      - video_data:/data/videos
      - db_data:/app/DATA
    restart: unless-stopped

volumes:
  video_data:
    driver: local
  db_data:
    driver: local
```

### 3. Build and Run

```bash
docker-compose up -d --build
```

### 4. Verify ffmpeg Inside Container

```bash
docker-compose exec backend ffmpeg -version
```

---

## Fly.io Deployment

### 1. Update fly.toml

**Add persistent volume for exports:**
```toml
app = "your-app-name"

[build]
  dockerfile = "Dockerfile"

[env]
  VIDEO_STORAGE_PATH = "/data/videos"

[mounts]
  source = "video_storage"
  destination = "/data/videos"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### 2. Create Volume

```bash
fly volumes create video_storage --size 10 --region ord
```

### 3. Set Secrets

```bash
fly secrets set VIDEO_STORAGE_PATH=/data/videos
fly secrets set REPLICATE_API_KEY=your_key_here
```

### 4. Deploy

```bash
fly deploy
```

### 5. Verify Deployment

```bash
# Check ffmpeg
fly ssh console -C "ffmpeg -version"

# Check volume
fly ssh console -C "ls -la /data/videos"

# Test export endpoint
curl -X GET "https://your-app.fly.dev/api/v2/jobs/1/export?format=mp4&quality=medium" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o test.mp4
```

---

## Health Checks

### 1. ffmpeg Availability

**Endpoint:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Add health check to main.py** (if not exists):
```python
@app.get("/health")
async def health_check():
    from .services.video_exporter import check_ffmpeg_available

    ffmpeg_ok = check_ffmpeg_available()

    return {
        "status": "healthy" if ffmpeg_ok else "degraded",
        "ffmpeg": "available" if ffmpeg_ok else "unavailable",
        "database": "ok",  # Could add DB check
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. Export Storage Health

**Check disk space:**
```bash
df -h /data/videos/exports
```

**Monitor export directory size:**
```bash
du -sh /data/videos/exports
```

---

## Monitoring and Logging

### 1. Track Export Usage

**Query database:**
```sql
-- Total downloads across all jobs
SELECT SUM(download_count) as total_downloads FROM generated_videos;

-- Most downloaded videos
SELECT id, prompt, download_count, created_at
FROM generated_videos
ORDER BY download_count DESC
LIMIT 10;

-- Refinement statistics
SELECT
  COUNT(*) as total_jobs,
  SUM(refinement_count) as total_refinements,
  AVG(refinement_count) as avg_refinements
FROM generated_videos;
```

### 2. Application Logs

**Export operations:**
```bash
# Docker
docker-compose logs -f backend | grep -i export

# Fly.io
fly logs | grep -i export
```

**Example log entries:**
```
INFO: Exporting job 123 to mp4/high
INFO: Video exported successfully: /data/videos/exports/123/mp4_high.mp4
INFO: Regenerating image for job 123, scene 2
INFO: Generated new image: https://replicate.delivery/...
```

### 3. Error Monitoring

**Common errors to watch for:**
```bash
# ffmpeg errors
grep "ffmpeg error" logs/app.log

# Export failures
grep "Export failed" logs/app.log

# Refinement limit exceeded
grep "Maximum refinement limit" logs/app.log

# Disk space issues
grep "OSError" logs/app.log
```

---

## Performance Optimization

### 1. Export Caching

Exports are automatically cached. Clear old exports periodically:

```bash
# Delete exports older than 7 days
find /data/videos/exports -type f -mtime +7 -delete

# Or keep only 3 most recent exports per job
for job_dir in /data/videos/exports/*/; do
  ls -t "$job_dir" | tail -n +4 | xargs -I {} rm "$job_dir{}"
done
```

**Automated cleanup (cron):**
```bash
# Add to crontab
0 2 * * * find /data/videos/exports -type f -mtime +7 -delete
```

### 2. Storage Limits

**Set maximum export directory size:**

Add to systemd service or supervisor config:
```bash
# Alert if exports exceed 10GB
if [ $(du -s /data/videos/exports | awk '{print $1}') -gt 10485760 ]; then
  echo "WARNING: Export storage exceeds 10GB"
fi
```

### 3. Rate Limiting

**Add rate limiting to export endpoint** (optional):

```python
from .prompt_parser_service.core.limiter import limiter

@app.get("/api/v2/jobs/{job_id}/export")
@limiter.limit("10/minute")  # 10 exports per minute per user
async def export_job_video(...):
    ...
```

---

## Backup and Recovery

### 1. Backup Exports

**Regular backups:**
```bash
# Backup to S3
aws s3 sync /data/videos/exports s3://your-bucket/exports/$(date +%Y%m%d)/

# Or tar backup
tar -czf exports_backup_$(date +%Y%m%d).tar.gz /data/videos/exports
```

### 2. Database Backup

**Backup with download counts:**
```bash
sqlite3 DATA/scenes.db ".backup DATA/scenes_backup_$(date +%Y%m%d).db"
```

### 3. Recovery

**Restore exports:**
```bash
# From S3
aws s3 sync s3://your-bucket/exports/20251115/ /data/videos/exports/

# From tar
tar -xzf exports_backup_20251115.tar.gz -C /
```

---

## Testing Checklist

### Pre-Deployment Tests

1. **ffmpeg Installation**
   ```bash
   ffmpeg -version
   ```

2. **Export Functionality**
   ```bash
   # Test all formats
   curl -X GET "http://localhost:8000/api/v2/jobs/1/export?format=mp4&quality=high" -H "Auth: ..." -o test.mp4
   curl -X GET "http://localhost:8000/api/v2/jobs/1/export?format=mov&quality=medium" -H "Auth: ..." -o test.mov
   curl -X GET "http://localhost:8000/api/v2/jobs/1/export?format=webm&quality=low" -H "Auth: ..." -o test.webm

   # Verify files
   file test.mp4 test.mov test.webm
   ```

3. **Refinement Functionality**
   ```bash
   # Test image regeneration
   curl -X POST "http://localhost:8000/api/v2/jobs/1/refine?scene_number=1&new_image_prompt=test" -H "Auth: ..."

   # Test refinement limit (try 6 times)
   for i in {1..6}; do
     curl -X POST "http://localhost:8000/api/v2/jobs/1/refine?scene_number=1&new_description=Test$i" -H "Auth: ..."
   done
   ```

4. **Reordering Functionality**
   ```bash
   curl -X POST "http://localhost:8000/api/v2/jobs/1/reorder?scene_order=1&scene_order=3&scene_order=2" -H "Auth: ..."
   ```

5. **Metadata Endpoint**
   ```bash
   curl -X GET "http://localhost:8000/api/v2/jobs/1/metadata"
   ```

6. **Download Tracking**
   ```bash
   # Download video twice
   curl -X GET "http://localhost:8000/api/v2/jobs/1/video" -o v1.mp4
   curl -X GET "http://localhost:8000/api/v2/jobs/1/video" -o v2.mp4

   # Check download count
   curl -X GET "http://localhost:8000/api/v2/jobs/1/metadata" | jq '.metrics.download_count'
   # Should be 2 or more
   ```

### Post-Deployment Verification

1. **Health Check**
   ```bash
   curl https://your-app.fly.dev/health
   ```

2. **Storage Verification**
   ```bash
   # SSH into container
   fly ssh console

   # Check directories
   ls -la /data/videos/exports
   ```

3. **Export Test**
   ```bash
   curl -X GET "https://your-app.fly.dev/api/v2/jobs/1/export?format=mp4&quality=medium" \
     -H "Authorization: Bearer TOKEN" \
     -o production_test.mp4

   # Verify file
   file production_test.mp4
   ffprobe production_test.mp4
   ```

---

## Troubleshooting

### Problem: ffmpeg not found

**Symptoms:**
```json
{
  "detail": "Video export service unavailable (ffmpeg not installed)"
}
```

**Solutions:**
```bash
# Check if installed
which ffmpeg

# Install if missing (Ubuntu/Debian)
sudo apt-get install -y ffmpeg

# In Docker, rebuild image
docker-compose build --no-cache
```

---

### Problem: Export fails with timeout

**Symptoms:**
```json
{
  "detail": "Export failed: Video export timed out (exceeded 5 minutes)"
}
```

**Solutions:**
1. Increase timeout in `video_exporter.py`:
   ```python
   timeout=600  # Increase from 300 to 600 seconds
   ```

2. Use lower quality preset
3. Check server CPU resources

---

### Problem: Refinement limit reached unexpectedly

**Symptoms:**
```json
{
  "detail": "Maximum refinement limit (5) reached for this job"
}
```

**Solutions:**
1. Check current count:
   ```sql
   SELECT id, refinement_count FROM generated_videos WHERE id = 123;
   ```

2. Reset if needed (CAREFUL!):
   ```sql
   UPDATE generated_videos SET refinement_count = 0 WHERE id = 123;
   ```

---

### Problem: Exports directory growing too large

**Symptoms:**
- Disk space warnings
- Slow export creation

**Solutions:**
1. Clean old exports:
   ```bash
   find /data/videos/exports -type f -mtime +7 -delete
   ```

2. Implement automatic cleanup:
   ```python
   from .services.video_exporter import cleanup_old_exports
   cleanup_old_exports(settings.VIDEO_STORAGE_PATH, job_id)
   ```

---

## Security Checklist

- [ ] ffmpeg version is up to date
- [ ] Export directory has correct permissions (755)
- [ ] Authentication required for all write operations
- [ ] Rate limiting enabled on export endpoint
- [ ] Input validation on all parameters
- [ ] File path traversal prevention in place
- [ ] Disk space monitoring configured
- [ ] Logs don't expose sensitive information

---

## Rollback Plan

If deployment fails:

1. **Revert Code**
   ```bash
   git revert HEAD
   fly deploy
   ```

2. **Check Database**
   ```bash
   # New columns won't break existing code
   # But verify with:
   sqlite3 DATA/scenes.db "SELECT * FROM generated_videos LIMIT 1;"
   ```

3. **Restore Backups**
   ```bash
   cp DATA/scenes_backup.db DATA/scenes.db
   ```

---

## Production Checklist

- [ ] ffmpeg installed and verified
- [ ] VIDEO_STORAGE_PATH environment variable set
- [ ] Persistent volume configured for exports
- [ ] Database columns created (download_count, refinement_count)
- [ ] Health check endpoint working
- [ ] Export endpoints returning correct formats
- [ ] Refinement limit enforced (5 max)
- [ ] Download tracking functional
- [ ] Logs configured and monitored
- [ ] Backup strategy implemented
- [ ] Disk space monitoring configured
- [ ] Error alerting set up

---

## Support and Maintenance

### Weekly Tasks
- Check disk usage of exports directory
- Review error logs for export failures
- Monitor refinement usage patterns

### Monthly Tasks
- Clean old exports (>30 days)
- Review download statistics
- Update ffmpeg if security patches available

### Quarterly Tasks
- Analyze storage costs
- Review and optimize export quality presets
- Audit refinement limits effectiveness
