"""Database migration runner.

This module applies the complete schema from schema.sql on server init.
All migrations are idempotent - safe to run multiple times.
"""

import sqlite3
from pathlib import Path
import os

# Get data directory from environment variable, default to ./DATA
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "scenes.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def run_migrations():
    """
    Apply all database migrations from schema.sql.

    This function is idempotent - safe to run on every server startup.
    Uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    # Read schema file
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        # STEP 1: Add missing columns to existing tables
        # These ALTER TABLE statements are idempotent - they'll fail silently if column exists
        print("Running pre-migration column additions...")

        # Add client_id and campaign_id to generated_images if missing
        try:
            conn.execute("ALTER TABLE generated_images ADD COLUMN client_id TEXT")
            print("  ✓ Added client_id to generated_images")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE generated_images ADD COLUMN campaign_id TEXT")
            print("  ✓ Added campaign_id to generated_images")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add client_id and campaign_id to generated_videos if missing
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN client_id TEXT")
            print("  ✓ Added client_id to generated_videos")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN campaign_id TEXT")
            print("  ✓ Added campaign_id to generated_videos")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add blob_data to assets if missing
        try:
            conn.execute("ALTER TABLE assets ADD COLUMN blob_data BLOB")
            print("  ✓ Added blob_data to assets")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add thumbnail_data to generated_videos if missing
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN thumbnail_data BLOB")
            print("  ✓ Added thumbnail_data to generated_videos")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add blob_id to assets if missing (for V3 blob storage)
        try:
            conn.execute("ALTER TABLE assets ADD COLUMN blob_id TEXT")
            print("  ✓ Added blob_id to assets")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add source_url to assets if missing (for V3 asset tracking)
        try:
            conn.execute("ALTER TABLE assets ADD COLUMN source_url TEXT")
            print("  ✓ Added source_url to assets")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add thumbnail_blob_id to assets if missing (for V3 thumbnail storage)
        try:
            conn.execute("ALTER TABLE assets ADD COLUMN thumbnail_blob_id TEXT")
            print("  ✓ Added thumbnail_blob_id to assets")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add homepage to clients if missing (for V3 client management)
        try:
            conn.execute("ALTER TABLE clients ADD COLUMN homepage TEXT")
            print("  ✓ Added homepage to clients")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add metadata to clients if missing (for V3 client management)
        try:
            conn.execute("ALTER TABLE clients ADD COLUMN metadata TEXT")
            print("  ✓ Added metadata to clients")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add product_url to campaigns if missing (for V3 campaign management)
        try:
            conn.execute("ALTER TABLE campaigns ADD COLUMN product_url TEXT")
            print("  ✓ Added product_url to campaigns")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add metadata to campaigns if missing (for V3 campaign management)
        try:
            conn.execute("ALTER TABLE campaigns ADD COLUMN metadata TEXT")
            print("  ✓ Added metadata to campaigns")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        print("✓ Pre-migration column additions complete")

        # STEP 2: Execute main schema
        # Execute schema using executescript for proper multi-statement handling
        # executescript handles triggers, transactions, etc. properly
        conn.executescript(schema_sql)
        print("✓ Database migrations applied successfully")

        # Verify critical tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        critical_tables = [
            'users', 'api_keys', 'clients', 'campaigns', 'assets',
            'creative_briefs', 'generated_scenes', 'generated_images',
            'generated_videos', 'genesis_videos'
        ]

        missing_tables = [t for t in critical_tables if t not in tables]
        if missing_tables:
            print(f"⚠ Warning: Missing tables: {', '.join(missing_tables)}")
        else:
            print(f"✓ All {len(critical_tables)} critical tables verified")

        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Run migrations when executed directly
    run_migrations()
