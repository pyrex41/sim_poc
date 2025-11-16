#!/usr/bin/env python3
"""
Idempotent database migration script for v2 Video Generation API
Safely adds columns only if they don't exist
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "backend" / "DATA" / "scenes.db"

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def run_migration():
    """Run migration with idempotent column additions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Starting migration...")

    # Define columns to add
    # Note: updated_at can't have CURRENT_TIMESTAMP default in ALTER TABLE
    # We'll add it as NULL and the trigger will populate it
    columns = [
        ("progress", "TEXT DEFAULT '{}'"),
        ("storyboard_data", "TEXT"),
        ("approved", "BOOLEAN DEFAULT 0"),
        ("approved_at", "TIMESTAMP"),
        ("estimated_cost", "REAL DEFAULT 0.0"),
        ("actual_cost", "REAL DEFAULT 0.0"),
        ("error_message", "TEXT"),
        ("updated_at", "TIMESTAMP"),
    ]

    # Add columns if they don't exist
    for col_name, col_def in columns:
        if not column_exists(cursor, "generated_videos", col_name):
            try:
                cursor.execute(f"ALTER TABLE generated_videos ADD COLUMN {col_name} {col_def}")
                print(f"✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Column {col_name} might already exist: {e}")
        else:
            print(f"⏭️  Column already exists: {col_name}")

    # Commit column additions before creating indexes
    conn.commit()

    # Create indexes (IF NOT EXISTS supported)
    indexes = [
        ("idx_videos_status", "status"),
        ("idx_videos_updated", "updated_at"),
        ("idx_videos_approved", "approved"),
    ]

    for idx_name, col_name in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON generated_videos({col_name})")
            print(f"✅ Created/verified index: {idx_name}")
        except sqlite3.OperationalError as e:
            print(f"⚠️  Could not create index {idx_name}: {e}")

    # Initialize updated_at for existing records
    if column_exists(cursor, "generated_videos", "updated_at"):
        cursor.execute("UPDATE generated_videos SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        print("✅ Initialized updated_at for existing records")

    # Create trigger
    cursor.execute("DROP TRIGGER IF EXISTS update_videos_timestamp")
    cursor.execute("""
        CREATE TRIGGER update_videos_timestamp
        AFTER UPDATE ON generated_videos
        FOR EACH ROW
        WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
        BEGIN
            UPDATE generated_videos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    """)
    print("✅ Created trigger: update_videos_timestamp")

    # Commit changes
    conn.commit()

    # Verify schema
    print("\n📋 Final schema for generated_videos:")
    cursor.execute("PRAGMA table_info(generated_videos)")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {row[2]}")

    print("\n📋 Indexes:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='generated_videos'")
    for row in cursor.fetchall():
        print(f"  {row[0]}")

    print("\n📋 Triggers:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='generated_videos'")
    for row in cursor.fetchall():
        print(f"  {row[0]}")

    conn.close()
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
