# Blob Storage Implementation for Assets

## Critical Fix: Database-Only Storage (No Filesystem)

**Problem**: The upload endpoint was incorrectly writing files to the filesystem instead of storing them entirely in the database as BLOBs.

**Solution**: Complete rewrite of asset upload and serving to use database blob storage exclusively.

---

## Changes Made

### 1. Upload Endpoint: `/api/v2/upload-asset` (POST)

**Before**: ❌ Wrote files to `backend/DATA/assets/` directory
**After**: ✅ Stores all binary data in `assets.blob_data` column

#### Key Changes:

- **Removed all filesystem writes** - No more `Path`, `mkdir`, or `open(file_path, "wb")`
- **Metadata extraction from bytes** for images using `PIL.Image.open(BytesIO(contents))`
- **Temp files only for ffprobe** - Videos/audio need ffprobe, so we:
  - Create temp file with `tempfile.NamedTemporaryFile`
  - Extract metadata
  - **Immediately delete temp file**
- **Pass `blob_data=contents`** to `create_asset()` function
- **Updated asset URL** to point to `/api/v2/assets/{asset_id}/data` (blob endpoint)

#### Code Flow:

```python
# 1. Read file contents into memory
contents = await file.read()

# 2. Extract metadata (no filesystem for images)
if asset_type == 'image':
    img = Image.open(BytesIO(contents))  # From bytes!
    width, height = img.size

elif asset_type in ['video', 'audio']:
    # Only videos/audio need temp files for ffprobe
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
        temp.write(contents)
        temp_path = temp.name

    # Extract metadata
    metadata = extract_video_metadata(temp_path)

    # DELETE temp file immediately
    Path(temp_path).unlink()

# 3. Store in database BLOB
create_asset(
    ...,
    blob_data=contents  # ← CRITICAL!
)
```

### 2. Serving Endpoint: `/api/v2/assets/{asset_id}/data` (GET)

**Before**: ❌ Used `FileResponse` to serve from filesystem
**After**: ✅ Queries `blob_data` from database and returns binary

#### Key Changes:

- **New endpoint path**: `/api/v2/assets/{asset_id}/data` (was `/api/v2/assets/{asset_id}`)
- **Queries blob_data** directly from database
- **Returns `Response`** with binary content (not `FileResponse`)
- **Proper media types** for all formats (image/jpeg, video/mp4, audio/mpeg, etc.)
- **Cache headers** for performance (`Cache-Control: public, max-age=31536000`)

#### Code:

```python
@app.get("/api/v2/assets/{asset_id}/data")
async def get_asset_data_v2(asset_id: str, current_user: Dict):
    # Get from database
    with get_db() as conn:
        row = conn.execute(
            "SELECT blob_data FROM assets WHERE id = ?",
            (asset_id,)
        ).fetchone()

        blob_data = row["blob_data"]

    # Return binary
    return Response(
        content=blob_data,
        media_type="image/jpeg",  # or video/mp4, etc.
        headers={
            "Content-Disposition": f'inline; filename="{asset.name}"',
            "Cache-Control": "public, max-age=31536000"
        }
    )
```

---

## Database Schema

### Required Column: `blob_data`

```sql
ALTER TABLE assets ADD COLUMN blob_data BLOB;
```

**Status**:
- ✅ Column exists in production schema
- ⚠️  May need to run migration if not yet applied

See migration files:
- `backend/migrations/add_blob_data_column.sql`
- `backend/migrations/run_add_blob_data.py`
- `backend/migrations/RUN_PRODUCTION_MIGRATION.md`

---

## Impact on Deployment (Fly.io)

### Why This Matters for Fly.io

Fly.io **ephemeral filesystem** means:
- ❌ Files written to disk are **lost on restart**
- ❌ Each machine has **separate filesystem** (no shared storage)
- ✅ Database persists across restarts (volume-backed)

**Before this fix**: Assets uploaded to one machine would disappear or be inaccessible from other machines.

**After this fix**: All assets stored in persistent SQLite database on mounted volume.

### Deployment Notes

1. **Volume**: `/data/scenes.db` (10GB Fly.io volume)
2. **No DATA directory needed**: Removed dependency on `backend/DATA/assets/`
3. **Stateless machines**: Any machine can serve any asset (all from DB)
4. **Scalable**: Can add more machines without shared filesystem concerns

---

## What's Removed

### Completely Eliminated:

- ✅ **No `uploads_base` directory creation**
- ✅ **No `file_path` construction**
- ✅ **No `open(file, "wb")`** writes
- ✅ **No file cleanup on errors** (no files to clean up!)
- ✅ **No `FileResponse`** for serving
- ✅ **No persistent temp files** (only transient ones for ffprobe, immediately deleted)

### Still Used (Temporarily):

- ⚠️  **Temp files for video/audio metadata** - ffprobe requires file path
  - Created with `tempfile.NamedTemporaryFile`
  - Deleted immediately after metadata extraction
  - Never persisted to `DATA/` directory

---

## API Usage

### Upload with Tags and Type

```bash
curl -X POST https://gauntlet-video-server.fly.dev/api/v2/upload-asset \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@video.mp4" \
  -F "clientId=client-123" \
  -F "type=video" \
  -F 'tags=["product", "demo"]'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://gauntlet-video-server.fly.dev/api/v2/assets/550e8400-e29b-41d4-a716-446655440000/data",
  "type": "video",
  "tags": ["product", "demo"],
  ...
}
```

### Retrieve Asset Binary

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://gauntlet-video-server.fly.dev/api/v2/assets/550e8400.../data \
  > downloaded_video.mp4
```

---

## Migration Path

### For Existing Assets (if any on filesystem)

If there are existing assets in `backend/DATA/assets/`, they won't be accessible through the new endpoint. Options:

1. **Ignore them** - Only new uploads use blob storage
2. **Migrate them** - Write script to read files and update `blob_data` column
3. **Re-upload** - Have users re-upload important assets

### Migration Script (if needed):

```python
# backend/migrations/migrate_filesystem_to_blob.py
import sqlite3
from pathlib import Path

def migrate_assets():
    conn = sqlite3.connect('/data/scenes.db')
    cursor = conn.cursor()

    # Find assets without blob_data
    rows = cursor.execute("""
        SELECT id, format FROM assets
        WHERE blob_data IS NULL
    """).fetchall()

    uploads_dir = Path('/app/backend/DATA/assets')

    for asset_id, format in rows:
        file_path = uploads_dir / f"{asset_id}.{format}"

        if file_path.exists():
            # Read file and update blob_data
            with open(file_path, 'rb') as f:
                blob_data = f.read()

            cursor.execute("""
                UPDATE assets
                SET blob_data = ?
                WHERE id = ?
            """, (blob_data, asset_id))

            print(f"Migrated {asset_id}")

    conn.commit()
    conn.close()
```

---

## Performance Considerations

### Pros:
- ✅ **Single source of truth** - Database only
- ✅ **Atomic operations** - Upload/delete is transactional
- ✅ **No orphaned files** - Can't have file without DB entry or vice versa
- ✅ **Simpler deployment** - No volume for uploads needed

### Cons:
- ⚠️  **Database size** - BLOBs can make DB large (mitigated by 10GB volume)
- ⚠️  **Memory usage** - Large files loaded into memory for serving
- ⚠️  **No CDN** - Can't easily offload to CDN without export

### Optimizations:

1. **Streaming responses** - Could implement chunked reads for large files
2. **Blob limits** - Enforce 50MB max (already done)
3. **Compression** - Could compress blobs (future enhancement)
4. **Caching** - Added `Cache-Control` headers for browser caching

---

## Testing Checklist

- [ ] Upload image and verify blob_data is populated
- [ ] Upload video and verify metadata extraction works
- [ ] Upload audio and verify temp file cleanup
- [ ] Retrieve asset via `/data` endpoint
- [ ] Verify ownership check prevents unauthorized access
- [ ] Test with 50MB file (max size)
- [ ] Verify no files created in `backend/DATA/assets/`
- [ ] Test on Fly.io deployment (ephemeral filesystem)
- [ ] Verify assets survive app restart

---

## Breaking Changes

### URL Format Changed

**Old**: `{base_url}/api/v2/assets/{asset_id}`
**New**: `{base_url}/api/v2/assets/{asset_id}/data`

Frontend must update asset URLs to use `/data` suffix.

### Assets Table Required Column

`blob_data BLOB` column must exist. Run migration before deployment.

---

## Summary

**What we fixed**:
- ❌ No more filesystem storage
- ✅ All assets in database BLOBs
- ✅ Works on ephemeral filesystems (Fly.io)
- ✅ Stateless, scalable architecture

**Files modified**:
- `backend/main.py` - Upload and serving endpoints completely rewritten

**Files created**:
- `backend/migrations/add_blob_data_column.sql`
- `backend/migrations/run_add_blob_data.py`
- `backend/migrations/RUN_PRODUCTION_MIGRATION.md`

**Next steps**:
1. Run blob_data migration on production
2. Deploy updated code
3. Test asset upload and retrieval
4. Update frontend to use `/data` endpoint
