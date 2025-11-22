# Database Migrations

## Overview

This directory contains database migration scripts for the Physics Simulator application. Migrations are **disabled by default** in production deployments to prevent unintended database changes.

## How Migrations Work

- **Default behavior**: Migrations are **skipped** on deployment
- **Auto-discovery**: All `.py` files in this directory are automatically detected
- **Execution order**: Migrations run in alphabetical order by filename
- **Idempotency**: Migration scripts should be idempotent (safe to run multiple times)

## Running Migrations on Fly.io

### One-time migration (recommended)

When you need to run a new migration:

```bash
# 1. Enable migrations for next deployment
fly secrets set RUN_MIGRATIONS=true

# 2. Deploy (migrations will run)
fly deploy

# 3. Disable migrations again (prevents re-running on future deploys)
fly secrets unset RUN_MIGRATIONS
```

### Keep migrations always enabled (not recommended)

```bash
fly secrets set RUN_MIGRATIONS=true
```

This will run migrations on every deployment. Only use this if you want migrations to check on every deploy.

## Running Migrations Locally

```bash
# Run a specific migration
python backend/migrations/your_migration.py

# Or use the migration runner script
python run_migration.py
```

## Creating New Migrations

1. **Naming convention**: Use descriptive names with timestamp/order prefix
   - Example: `001_add_user_fields.py`, `002_create_analytics_table.py`
   - Or: `20251116_add_upscaler_settings.py`

2. **Template**:

```python
#!/usr/bin/env python3
"""
Migration: [Brief description]
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def run_migration():
    """Run the migration."""
    db_path = Path(__file__).parent.parent / "sim_poc.db"

    # Check for production environment
    if not db_path.exists():
        db_path = Path("/data/sim_poc.db")

    if not db_path.exists():
        print(f"Database not found at {db_path}, skipping migration")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Your migration SQL here
        # Use IF NOT EXISTS to make idempotent
        cursor.execute("""
            ALTER TABLE your_table ADD COLUMN new_column TEXT;
        """)

        conn.commit()
        print("✓ Migration completed successfully")

    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("✓ Migration already applied, skipping")
        else:
            print(f"✗ Migration failed: {e}")
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
```

3. **Best practices**:
   - Always handle "column already exists" errors gracefully
   - Use `IF NOT EXISTS` where possible
   - Test locally before deploying
   - Add rollback instructions in comments if needed
   - Document what the migration does in the docstring

## Migration History

| File | Description | Date Applied |
|------|-------------|--------------|
| `add_video_job_fields.py` | Added workflow tracking fields to videos table | 2024-11-16 |
| `add_clients_campaigns.py` | Created clients and campaigns tables | 2024-11-16 |
| `consolidate_assets_table.py` | Consolidated asset tables into single schema with client_id NOT NULL | 2024-11-16 |
| ~~`enforce_client_id_required.py`~~ | (Removed - made obsolete by consolidate_assets_table.py) | N/A |

## Troubleshooting

**Migrations not running?**
- Check that `RUN_MIGRATIONS=true` is set: `fly secrets list`
- Check deployment logs: `fly logs`

**Migration failed?**
- Most failures are due to duplicate columns (already applied)
- Check the error message in logs
- SSH into the instance to inspect: `fly ssh console`
- Manually check database: `sqlite3 /data/sim_poc.db`

**Need to rollback?**
- There's no automatic rollback
- Create a new migration that reverses the changes
- Or manually fix via SSH + sqlite3
