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
