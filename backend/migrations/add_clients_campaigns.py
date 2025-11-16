"""Migration: Add Clients and Campaigns tables for ad-video-gen frontend integration.

This migration adds:
1. clients table - Brand/client management with brand guidelines
2. client_assets table - Client-specific assets (logos, brand docs)
3. campaigns table - Marketing campaigns linked to clients
4. campaign_assets table - Campaign-specific assets
5. Foreign key constraints linking campaigns to clients and videos to campaigns
"""

import sqlite3
import json
from pathlib import Path
import os
from datetime import datetime

# Get data directory from environment variable, default to ./DATA
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "scenes.db"


def run_migration():
    """Run the migration to add clients and campaigns tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        print("Starting migration: add_clients_campaigns")

        # 1. Create clients table
        print("Creating clients table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                brand_guidelines TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 2. Create client_assets table
        print("Creating client_assets table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS client_assets (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('logo', 'image', 'document')),
                url TEXT NOT NULL,
                name TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        # 3. Create campaigns table
        print("Creating campaigns table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                goal TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('active', 'archived', 'draft')) DEFAULT 'draft',
                brief TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 4. Create campaign_assets table
        print("Creating campaign_assets table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaign_assets (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('image', 'video', 'document')),
                url TEXT NOT NULL,
                name TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)

        # 5. Add campaign_id column to generated_videos if it doesn't exist
        print("Adding campaign_id to generated_videos table...")
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN campaign_id TEXT REFERENCES campaigns(id)")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - campaign_id column already exists, skipping...")
            else:
                raise

        # 6. Add format and duration columns to generated_videos if they don't exist
        print("Adding format column to generated_videos table...")
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN format TEXT CHECK (format IN ('9:16', '1:1', '16:9')) DEFAULT '16:9'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - format column already exists, skipping...")
            else:
                raise

        print("Adding duration column to generated_videos table...")
        try:
            conn.execute("ALTER TABLE generated_videos ADD COLUMN duration INTEGER CHECK (duration IN (15, 30, 60)) DEFAULT 30")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - duration column already exists, skipping...")
            else:
                raise

        # 7. Add video metrics columns
        print("Adding metrics columns to generated_videos table...")
        metrics_columns = [
            ("views", "INTEGER DEFAULT 0"),
            ("clicks", "INTEGER DEFAULT 0"),
            ("ctr", "REAL DEFAULT 0.0"),
            ("conversions", "INTEGER DEFAULT 0")
        ]

        for col_name, col_def in metrics_columns:
            try:
                conn.execute(f"ALTER TABLE generated_videos ADD COLUMN {col_name} {col_def}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  - {col_name} column already exists, skipping...")
                else:
                    raise

        # 8. Create indexes for performance
        print("Creating indexes...")
        indexes = [
            ("idx_clients_user_id", "clients", "user_id"),
            ("idx_clients_name", "clients", "name"),
            ("idx_client_assets_client_id", "client_assets", "client_id"),
            ("idx_campaigns_client_id", "campaigns", "client_id"),
            ("idx_campaigns_user_id", "campaigns", "user_id"),
            ("idx_campaigns_status", "campaigns", "status"),
            ("idx_campaign_assets_campaign_id", "campaign_assets", "campaign_id"),
            ("idx_videos_campaign_id", "generated_videos", "campaign_id"),
        ]

        for idx_name, table_name, column_name in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})")
            except Exception as e:
                print(f"  - Warning: Could not create index {idx_name}: {e}")

        # 9. Create triggers for updated_at timestamps
        print("Creating update triggers...")

        # Clients update trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_clients_timestamp
            AFTER UPDATE ON clients
            FOR EACH ROW
            BEGIN
                UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

        # Campaigns update trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_campaigns_timestamp
            AFTER UPDATE ON campaigns
            FOR EACH ROW
            BEGIN
                UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

        conn.commit()
        print("Migration completed successfully!")

        # Verify tables were created
        print("\nVerifying tables...")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Total tables: {len(tables)}")

        required_tables = ['clients', 'client_assets', 'campaigns', 'campaign_assets']
        for table in required_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} - MISSING!")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
