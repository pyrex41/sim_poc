#!/usr/bin/env python3
"""
Migration script from old schema to v3.

This script:
1. Backs up the existing database
2. Creates a new database with v3 schema
3. Optionally migrates critical data (users, clients, campaigns)
"""
import sqlite3
import shutil
import os
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles migration from old schema to v3."""

    def __init__(
        self,
        old_db_path: str = "backend/simulator.db",
        new_db_path: str = "backend/simulator_v3.db",
        schema_path: str = "backend/schema_v3.sql"
    ):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.schema_path = schema_path
        self.backup_path = None

    def run(self, migrate_data: bool = True, skip_backup: bool = False):
        """
        Run the full migration.

        Args:
            migrate_data: Whether to migrate existing data
            skip_backup: Skip backup step (use with caution)
        """
        logger.info("=" * 60)
        logger.info("Starting migration to v3 schema")
        logger.info("=" * 60)

        # Step 1: Backup
        if not skip_backup and os.path.exists(self.old_db_path):
            self.backup_old_database()
        else:
            logger.info("Skipping backup (old database doesn't exist or backup skipped)")

        # Step 2: Create new database
        self.create_new_database()

        # Step 3: Migrate data
        if migrate_data and os.path.exists(self.old_db_path):
            self.migrate_data()
        else:
            logger.info("Skipping data migration")

        logger.info("=" * 60)
        logger.info("Migration complete!")
        logger.info(f"New database: {self.new_db_path}")
        if self.backup_path:
            logger.info(f"Backup saved: {self.backup_path}")
        logger.info("=" * 60)

    def backup_old_database(self):
        """Create backup of old database."""
        if not os.path.exists(self.old_db_path):
            logger.warning(f"Old database not found: {self.old_db_path}")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = f"{self.old_db_path}.backup_{timestamp}"

        logger.info(f"Backing up old database to: {self.backup_path}")
        shutil.copy2(self.old_db_path, self.backup_path)
        logger.info("✓ Backup complete")

    def create_new_database(self):
        """Create new database with v3 schema."""
        logger.info(f"Creating new database: {self.new_db_path}")

        # Remove existing v3 db if it exists
        if os.path.exists(self.new_db_path):
            logger.warning(f"Removing existing v3 database: {self.new_db_path}")
            os.remove(self.new_db_path)

        # Read schema
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, 'r') as f:
            schema_sql = f.read()

        # Create database and apply schema
        conn = sqlite3.connect(self.new_db_path)
        try:
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("✓ New database created with v3 schema")
        finally:
            conn.close()

    def migrate_data(self):
        """Migrate data from old database to new."""
        logger.info("Migrating data from old database...")

        old_conn = sqlite3.connect(self.old_db_path)
        new_conn = sqlite3.connect(self.new_db_path)

        old_conn.row_factory = sqlite3.Row
        new_conn.row_factory = sqlite3.Row

        try:
            # Migrate users
            self._migrate_users(old_conn, new_conn)

            # Migrate clients
            self._migrate_clients(old_conn, new_conn)

            # Migrate campaigns
            self._migrate_campaigns(old_conn, new_conn)

            # Migrate API keys
            self._migrate_api_keys(old_conn, new_conn)

            new_conn.commit()
            logger.info("✓ Data migration complete")

        except Exception as e:
            logger.error(f"Error during data migration: {e}", exc_info=True)
            new_conn.rollback()
            raise

        finally:
            old_conn.close()
            new_conn.close()

    def _migrate_users(self, old_conn, new_conn):
        """Migrate users table."""
        try:
            old_cursor = old_conn.cursor()
            old_cursor.execute("SELECT * FROM users")
            users = old_cursor.fetchall()

            if not users:
                logger.info("  No users to migrate")
                return

            new_cursor = new_conn.cursor()
            for user in users:
                new_cursor.execute("""
                    INSERT INTO users (
                        id, username, email, hashed_password,
                        is_active, is_admin, created_at, last_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['id'],
                    user['username'],
                    user['email'],
                    user['hashed_password'],
                    user['is_active'],
                    user.get('is_admin', 0),
                    user['created_at'],
                    user.get('last_login')
                ))

            logger.info(f"  ✓ Migrated {len(users)} users")

        except sqlite3.Error as e:
            logger.warning(f"  Could not migrate users: {e}")

    def _migrate_clients(self, old_conn, new_conn):
        """Migrate clients table."""
        try:
            old_cursor = old_conn.cursor()
            old_cursor.execute("SELECT * FROM clients")
            clients = old_cursor.fetchall()

            if not clients:
                logger.info("  No clients to migrate")
                return

            new_cursor = new_conn.cursor()
            for client in clients:
                new_cursor.execute("""
                    INSERT INTO clients (
                        id, user_id, name, description,
                        brand_guidelines, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    client['id'],
                    client['user_id'],
                    client['name'],
                    client.get('description'),
                    client.get('brand_guidelines'),
                    client['created_at'],
                    client.get('updated_at', client['created_at'])
                ))

            logger.info(f"  ✓ Migrated {len(clients)} clients")

        except sqlite3.Error as e:
            logger.warning(f"  Could not migrate clients: {e}")

    def _migrate_campaigns(self, old_conn, new_conn):
        """Migrate campaigns table."""
        try:
            old_cursor = old_conn.cursor()
            old_cursor.execute("SELECT * FROM campaigns")
            campaigns = old_cursor.fetchall()

            if not campaigns:
                logger.info("  No campaigns to migrate")
                return

            new_cursor = new_conn.cursor()
            for campaign in campaigns:
                new_cursor.execute("""
                    INSERT INTO campaigns (
                        id, client_id, user_id, name, goal,
                        status, brief, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign['id'],
                    campaign['client_id'],
                    campaign['user_id'],
                    campaign['name'],
                    campaign['goal'],
                    campaign.get('status', 'draft'),
                    campaign.get('brief'),
                    campaign['created_at'],
                    campaign.get('updated_at', campaign['created_at'])
                ))

            logger.info(f"  ✓ Migrated {len(campaigns)} campaigns")

        except sqlite3.Error as e:
            logger.warning(f"  Could not migrate campaigns: {e}")

    def _migrate_api_keys(self, old_conn, new_conn):
        """Migrate API keys table."""
        try:
            old_cursor = old_conn.cursor()
            old_cursor.execute("SELECT * FROM api_keys")
            api_keys = old_cursor.fetchall()

            if not api_keys:
                logger.info("  No API keys to migrate")
                return

            new_cursor = new_conn.cursor()
            for key in api_keys:
                new_cursor.execute("""
                    INSERT INTO api_keys (
                        id, key_hash, name, user_id, is_active,
                        created_at, last_used, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key['id'],
                    key['key_hash'],
                    key['name'],
                    key['user_id'],
                    key['is_active'],
                    key['created_at'],
                    key.get('last_used'),
                    key.get('expires_at')
                ))

            logger.info(f"  ✓ Migrated {len(api_keys)} API keys")

        except sqlite3.Error as e:
            logger.warning(f"  Could not migrate API keys: {e}")


def main():
    """Run migration."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate to v3 schema')
    parser.add_argument(
        '--no-data',
        action='store_true',
        help='Skip data migration (fresh database)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup (use with caution)'
    )
    parser.add_argument(
        '--old-db',
        default='backend/simulator.db',
        help='Path to old database'
    )
    parser.add_argument(
        '--new-db',
        default='backend/simulator_v3.db',
        help='Path to new database'
    )

    args = parser.parse_args()

    migrator = DatabaseMigrator(
        old_db_path=args.old_db,
        new_db_path=args.new_db
    )

    migrator.run(
        migrate_data=not args.no_data,
        skip_backup=args.no_backup
    )


if __name__ == '__main__':
    main()
