"""
Database migration: Consolidate all asset tables into single 'assets' table

This migration:
1. Drops old tables: uploaded_assets, client_assets, campaign_assets
2. Creates new consolidated 'assets' table with discriminated union support
3. Adds indexes for efficient querying

Run this migration to implement the new asset model.
"""

import sqlite3
from pathlib import Path

def run_migration(db_path: str = None):
    """Execute the asset consolidation migration"""
    if db_path is None:
        # Use the same database path as database_helpers.py
        from pathlib import Path
        import os
        DATA_DIR = Path(os.getenv("DATA", "./DATA"))
        db_path = str(DATA_DIR / "scenes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting asset consolidation migration...")

        # Step 1: Drop old asset tables
        print("Dropping old asset tables...")
        cursor.execute("DROP TABLE IF EXISTS uploaded_assets")
        cursor.execute("DROP TABLE IF EXISTS client_assets")
        cursor.execute("DROP TABLE IF EXISTS campaign_assets")

        # Step 2: Create new consolidated assets table
        print("Creating new consolidated assets table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                client_id TEXT NOT NULL,
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
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)

        # Step 3: Create indexes for efficient querying
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_client_id ON assets(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_campaign_id ON assets(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_uploaded_at ON assets(uploaded_at)")

        # Commit changes
        conn.commit()
        print("✅ Asset consolidation migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Run migration
    run_migration()
