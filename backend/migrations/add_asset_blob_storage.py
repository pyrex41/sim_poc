"""
Migration: Add blob_data column to assets table
Allows storing assets directly in the database as binary blobs
"""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Add blob_data column to assets table"""
    cursor = conn.cursor()

    try:
        # Add blob_data column for storing asset binary data
        cursor.execute("""
            ALTER TABLE assets
            ADD COLUMN blob_data BLOB
        """)

        conn.commit()
        print("✓ Added blob_data column to assets table")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠ blob_data column already exists, skipping")
        else:
            raise

    cursor.close()


def down(conn: sqlite3.Connection):
    """
    Remove blob_data column from assets table
    Note: SQLite doesn't support DROP COLUMN directly, would need table recreation
    """
    cursor = conn.cursor()

    # SQLite limitation: Can't drop columns easily
    # Would need to:
    # 1. Create new table without blob_data
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table

    print("⚠ Downgrade not implemented for SQLite (DROP COLUMN not supported)")
    print("  To remove blob_data column, manually recreate the table")

    cursor.close()


def run_migration(db_path: str = "backend/sim_poc.db"):
    """Run the migration"""
    conn = sqlite3.connect(db_path)
    try:
        up(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    # Run migration if executed directly
    run_migration()
