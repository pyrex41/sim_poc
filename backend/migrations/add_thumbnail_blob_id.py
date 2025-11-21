"""
Migration: Add thumbnail_blob_id column to assets table
Allows storing thumbnail references in the asset_blobs table
"""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Add thumbnail_blob_id column to assets table"""
    cursor = conn.cursor()

    try:
        # Add thumbnail_blob_id column for storing thumbnail blob references
        cursor.execute("""
            ALTER TABLE assets
            ADD COLUMN thumbnail_blob_id TEXT
        """)

        conn.commit()
        print("✓ Added thumbnail_blob_id column to assets table")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠ thumbnail_blob_id column already exists, skipping")
        else:
            raise

    cursor.close()


def down(conn: sqlite3.Connection):
    """
    Remove thumbnail_blob_id column from assets table
    Note: SQLite doesn't support DROP COLUMN directly, would need table recreation
    """
    cursor = conn.cursor()

    # SQLite limitation: Can't drop columns easily
    # Would need to:
    # 1. Create new table without thumbnail_blob_id
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table

    print("⚠ Downgrade not implemented for SQLite (DROP COLUMN not supported)")
    print("  To remove thumbnail_blob_id column, manually recreate the table")

    cursor.close()


def run_migration(db_path: str = "backend/DATA/scenes.db"):
    """Run the migration"""
    conn = sqlite3.connect(db_path)
    try:
        up(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    # Run migration if executed directly
    run_migration()
