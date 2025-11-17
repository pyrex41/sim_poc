"""
Migration: Enforce client_id as required (NOT NULL) in assets table
Every asset must be associated with a client
"""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Make client_id required in assets table"""
    cursor = conn.cursor()

    try:
        # SQLite doesn't support ALTER COLUMN to add NOT NULL directly
        # We need to recreate the table with the new constraint

        # Step 1: Create new table with client_id NOT NULL
        cursor.execute("""
            CREATE TABLE assets_new (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                client_id TEXT NOT NULL,  -- NOW REQUIRED
                campaign_id TEXT,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                url TEXT NOT NULL,
                size INTEGER,
                uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                format TEXT NOT NULL,
                tags TEXT,
                width INTEGER,
                height INTEGER,
                duration INTEGER,
                thumbnail_url TEXT,
                waveform_url TEXT,
                page_count INTEGER,
                blob_data BLOB,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (client_id) REFERENCES clients(id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)

        # Step 2: Copy data from old table to new table
        # Only copy rows that already have a client_id
        cursor.execute("""
            INSERT INTO assets_new
            SELECT * FROM assets
            WHERE client_id IS NOT NULL
        """)

        # Step 3: Drop old table
        cursor.execute("DROP TABLE assets")

        # Step 4: Rename new table to original name
        cursor.execute("ALTER TABLE assets_new RENAME TO assets")

        # Step 5: Recreate indexes
        cursor.execute("CREATE INDEX idx_assets_user_id ON assets(user_id)")
        cursor.execute("CREATE INDEX idx_assets_client_id ON assets(client_id)")
        cursor.execute("CREATE INDEX idx_assets_campaign_id ON assets(campaign_id)")
        cursor.execute("CREATE INDEX idx_assets_type ON assets(asset_type)")
        cursor.execute("CREATE INDEX idx_assets_uploaded_at ON assets(uploaded_at)")

        conn.commit()

        # Count how many rows were copied
        cursor.execute("SELECT COUNT(*) FROM assets")
        count = cursor.fetchone()[0]

        print(f"✓ Enforced client_id as required in assets table")
        print(f"✓ Migrated {count} assets with valid client_id")
        print(f"⚠ Assets without client_id were excluded (if any)")

    except sqlite3.OperationalError as e:
        print(f"✗ Migration failed: {e}")
        raise

    cursor.close()


def down(conn: sqlite3.Connection):
    """
    Revert client_id to optional
    """
    cursor = conn.cursor()

    try:
        # Create table with client_id as optional again
        cursor.execute("""
            CREATE TABLE assets_new (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                client_id TEXT,  -- OPTIONAL AGAIN
                campaign_id TEXT,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                url TEXT NOT NULL,
                size INTEGER,
                uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                format TEXT NOT NULL,
                tags TEXT,
                width INTEGER,
                height INTEGER,
                duration INTEGER,
                thumbnail_url TEXT,
                waveform_url TEXT,
                page_count INTEGER,
                blob_data BLOB,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (client_id) REFERENCES clients(id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)

        cursor.execute("INSERT INTO assets_new SELECT * FROM assets")
        cursor.execute("DROP TABLE assets")
        cursor.execute("ALTER TABLE assets_new RENAME TO assets")

        # Recreate indexes
        cursor.execute("CREATE INDEX idx_assets_user_id ON assets(user_id)")
        cursor.execute("CREATE INDEX idx_assets_client_id ON assets(client_id)")
        cursor.execute("CREATE INDEX idx_assets_campaign_id ON assets(campaign_id)")
        cursor.execute("CREATE INDEX idx_assets_type ON assets(asset_type)")
        cursor.execute("CREATE INDEX idx_assets_uploaded_at ON assets(uploaded_at)")

        conn.commit()
        print("✓ Reverted client_id to optional in assets table")

    except sqlite3.OperationalError as e:
        print(f"✗ Downgrade failed: {e}")
        raise

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
