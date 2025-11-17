# Production Migration: Add blob_data Column

## Problem
The `blob_data` column is missing from the `assets` table in production, causing errors when uploading assets.

## Solution
Run the migration to add the `blob_data BLOB` column to the assets table.

---

## Option 1: Python Script (Recommended - Safest)

The Python script checks if the column exists before attempting to add it.

### On Fly.io Production

```bash
# SSH into the production machine
fly ssh console -a gauntlet-video-server

# Navigate to the app directory
cd /app

# Run the migration script
python3 backend/migrations/run_add_blob_data.py /data/scenes.db

# Expected output:
# Database path: /data/scenes.db
#
# Adding blob_data column to assets table...
# ✓ Successfully added blob_data column to assets table
#
# ✓ Migration completed successfully

# Exit the SSH session
exit
```

### Locally (for testing)

```bash
cd /Users/reuben/gauntlet/video/sim_poc

# Run the migration
python3 backend/migrations/run_add_blob_data.py backend/sim_poc.db
```

---

## Option 2: Direct SQL (Faster but less safe)

⚠️ **Warning**: This will error if the column already exists (which is safe but not graceful)

### On Fly.io Production

```bash
# SSH into production
fly ssh console -a gauntlet-video-server

# Run SQLite with the production database
sqlite3 /data/scenes.db

# Add the column
ALTER TABLE assets ADD COLUMN blob_data BLOB;

# Verify it was added (optional)
PRAGMA table_info(assets);
-- Look for: blob_data | BLOB | 0 | NULL | 0

# Exit SQLite
.quit

# Exit SSH
exit
```

### Using SQL File

```bash
# SSH into production
fly ssh console -a gauntlet-video-server

# Run the SQL file
sqlite3 /data/scenes.db < backend/migrations/add_blob_data_column.sql

# Exit
exit
```

---

## Option 3: Using Existing Migration Script

The original migration script from the previous session:

```bash
# SSH into production
fly ssh console -a gauntlet-video-server

# Navigate to app directory
cd /app

# Run the existing migration
python3 backend/migrations/add_asset_blob_storage.py

# Exit
exit
```

---

## Verification

After running the migration, verify the column exists:

```bash
# SSH into production
fly ssh console -a gauntlet-video-server

# Check the schema
sqlite3 /data/scenes.db "PRAGMA table_info(assets);" | grep blob_data

# Expected output:
# 17|blob_data|BLOB|0||0

# Exit
exit
```

---

## Restart Application

After running the migration, restart the app to ensure clean state:

```bash
fly apps restart gauntlet-video-server
```

---

## Rollback (if needed)

If something goes wrong, you can remove the column:

⚠️ **Warning**: This will drop the column and any data in it

```bash
# SQLite doesn't support DROP COLUMN directly before version 3.35.0
# You would need to recreate the table without the column

# Backup first!
fly ssh console -a gauntlet-video-server
cp /data/scenes.db /data/scenes.db.backup

# Then use the migration down() function or manually recreate table
```

---

## Expected Schema After Migration

The `assets` table should have these columns:

```
id              TEXT PRIMARY KEY
user_id         INTEGER
client_id       TEXT NOT NULL
campaign_id     TEXT
name            TEXT NOT NULL
asset_type      TEXT NOT NULL
url             TEXT NOT NULL
size            INTEGER
uploaded_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
format          TEXT NOT NULL
tags            TEXT
width           INTEGER
height          INTEGER
duration        INTEGER
thumbnail_url   TEXT
waveform_url    TEXT
page_count      INTEGER
blob_data       BLOB          <- NEW COLUMN
```

---

## Troubleshooting

### Error: "duplicate column name: blob_data"
**Cause**: Column already exists
**Solution**: No action needed, migration already ran

### Error: "no such table: assets"
**Cause**: Wrong database path or database not initialized
**Solution**: Verify database path with `ls -la /data/`

### Error: "database is locked"
**Cause**: Application is writing to database
**Solution**: Stop app temporarily: `fly apps restart gauntlet-video-server`

### Permission denied
**Cause**: SSH user doesn't have write access
**Solution**: Run migration as root or check file permissions

---

## Post-Migration Testing

Test the asset upload endpoint after migration:

```bash
curl -X POST https://gauntlet-video-server.fly.dev/api/v2/upload-asset \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.jpg" \
  -F "clientId=test-client-123" \
  -F "name=Test Upload" \
  -F 'tags=["test"]'
```

Should return 200 with asset object (no blob_data errors).

---

## Notes

- The `blob_data` column is optional - it stores binary asset data in the database
- Existing assets will have `NULL` in this column (files are stored on filesystem)
- New uploads can use blob storage if the upload endpoint is updated to include it
- Column is nullable, so no data migration needed for existing rows
