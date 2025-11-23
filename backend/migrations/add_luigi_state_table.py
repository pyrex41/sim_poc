"""
Migration: Add Luigi task state tracking table.

This migration creates the necessary table for tracking Luigi task states
in the existing database.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate():
    """Create the luigi_task_state table."""
    from ..database import get_db

    logger.info("Running migration: add_luigi_state_table")

    with get_db() as conn:
        # Check if table already exists
        cursor = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='luigi_task_state'
            """
        )

        if cursor.fetchone():
            logger.info("Table luigi_task_state already exists, skipping")
            return

        # Create the table
        conn.execute(
            """
            CREATE TABLE luigi_task_state (
                task_id VARCHAR(255) PRIMARY KEY,
                job_id INTEGER NOT NULL,
                task_name VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL,
                output_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES generated_videos(id)
            )
            """
        )

        # Create indexes for faster queries
        conn.execute(
            """
            CREATE INDEX idx_luigi_task_job_id
            ON luigi_task_state(job_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX idx_luigi_task_status
            ON luigi_task_state(status)
            """
        )

        conn.execute(
            """
            CREATE INDEX idx_luigi_task_created
            ON luigi_task_state(created_at)
            """
        )

        conn.commit()

        logger.info("Created luigi_task_state table with indexes")


if __name__ == "__main__":
    # Run migration directly
    logging.basicConfig(level=logging.INFO)
    migrate()
    print("Migration completed successfully!")
