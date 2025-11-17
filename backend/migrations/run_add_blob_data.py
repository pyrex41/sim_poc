#!/usr/bin/env python3
"""
Safe migration to add blob_data column to assets table
Checks if column exists before attempting to add it
"""

import sqlite3
import sys
from pathlib import Path


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_blob_data_column(db_path: str):
    """Add blob_data column to assets table if it doesn't exist"""

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        if column_exists(cursor, 'assets', 'blob_data'):
            print("✓ blob_data column already exists in assets table")
            print("  No migration needed")
            return True

        # Add the column
        print("Adding blob_data column to assets table...")
        cursor.execute("ALTER TABLE assets ADD COLUMN blob_data BLOB")
        conn.commit()

        # Verify it was added
        if column_exists(cursor, 'assets', 'blob_data'):
            print("✓ Successfully added blob_data column to assets table")
            return True
        else:
            print("✗ Failed to add blob_data column")
            return False

    except sqlite3.OperationalError as e:
        print(f"✗ Migration failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def main():
    # Determine database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default paths to check
        possible_paths = [
            "/data/scenes.db",  # Production path on Fly.io
            "backend/sim_poc.db",  # Local dev path
            "sim_poc.db",  # Alternative local path
        ]

        db_path = None
        for path in possible_paths:
            if Path(path).exists():
                db_path = path
                break

        if not db_path:
            print("Error: Could not find database file")
            print("Usage: python run_add_blob_data.py [path/to/database.db]")
            print("\nSearched paths:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)

    print(f"Database path: {db_path}\n")

    # Run migration
    success = add_blob_data_column(db_path)

    if success:
        print("\n✓ Migration completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
