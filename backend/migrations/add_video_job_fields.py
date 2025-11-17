"""
Database migration to add video generation v2 workflow fields.

This migration adds columns needed for the video generation workflow:
- progress: JSON field for tracking progress
- storyboard_data: JSON field for storing storyboard entries
- approved: Boolean flag for storyboard approval
- approved_at: Timestamp of approval
- estimated_cost: Float for cost estimation
- actual_cost: Float for actual cost
- error_message: Text field for error messages
- updated_at: Timestamp for last update
"""

import sqlite3
from pathlib import Path
import os

# Get database path from environment
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DB_PATH = DATA_DIR / "scenes.db"


def migrate():
    """Run the migration to add video job workflow fields."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Add progress field (JSON)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN progress TEXT")
            print("✓ Added 'progress' column")
        except sqlite3.OperationalError:
            print("- 'progress' column already exists")

        # Add storyboard_data field (JSON)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN storyboard_data TEXT")
            print("✓ Added 'storyboard_data' column")
        except sqlite3.OperationalError:
            print("- 'storyboard_data' column already exists")

        # Add approved field (Boolean, default False)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN approved BOOLEAN DEFAULT 0")
            print("✓ Added 'approved' column")
        except sqlite3.OperationalError:
            print("- 'approved' column already exists")

        # Add approved_at field (Timestamp)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN approved_at TIMESTAMP")
            print("✓ Added 'approved_at' column")
        except sqlite3.OperationalError:
            print("- 'approved_at' column already exists")

        # Add estimated_cost field (Float, default 0.0)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN estimated_cost REAL DEFAULT 0.0")
            print("✓ Added 'estimated_cost' column")
        except sqlite3.OperationalError:
            print("- 'estimated_cost' column already exists")

        # Add actual_cost field (Float)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN actual_cost REAL")
            print("✓ Added 'actual_cost' column")
        except sqlite3.OperationalError:
            print("- 'actual_cost' column already exists")

        # Add error_message field (Text)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN error_message TEXT")
            print("✓ Added 'error_message' column")
        except sqlite3.OperationalError:
            print("- 'error_message' column already exists")

        # Add updated_at field (Timestamp, default CURRENT_TIMESTAMP)
        try:
            cursor.execute("ALTER TABLE generated_videos ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✓ Added 'updated_at' column")
        except sqlite3.OperationalError:
            print("- 'updated_at' column already exists")

        # Create trigger to auto-update updated_at timestamp
        try:
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_generated_videos_timestamp
                AFTER UPDATE ON generated_videos
                FOR EACH ROW
                BEGIN
                    UPDATE generated_videos
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END;
            """)
            print("✓ Created auto-update trigger for 'updated_at'")
        except sqlite3.OperationalError as e:
            print(f"- Trigger creation skipped: {e}")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
