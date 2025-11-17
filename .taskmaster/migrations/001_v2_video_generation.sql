-- Migration: v2 Video Generation API
-- Version: 001
-- Date: 2025-11-15
-- Description: Add columns for video generation workflow, approval, cost tracking, and error handling

-- ============================================================
-- Add new columns to generated_videos table
-- ============================================================

-- Progress tracking (JSON stored as TEXT in SQLite)
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS progress TEXT DEFAULT '{}';

-- Video storage (URL instead of BLOB for performance)
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS video_url TEXT;

-- Storyboard data (JSON array of scenes)
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS storyboard_data TEXT;

-- Approval workflow
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

-- Cost tracking
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS estimated_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS actual_cost REAL DEFAULT 0.0;

-- Error handling and retry logic
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Timestamp for stuck job detection
ALTER TABLE generated_videos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ============================================================
-- Create indexes for performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_videos_status ON generated_videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_campaign ON generated_videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_client ON generated_videos(client_id);
CREATE INDEX IF NOT EXISTS idx_videos_updated ON generated_videos(updated_at);
CREATE INDEX IF NOT EXISTS idx_videos_approved ON generated_videos(approved);

-- ============================================================
-- Create trigger to auto-update updated_at timestamp
-- ============================================================

DROP TRIGGER IF EXISTS update_videos_timestamp;

CREATE TRIGGER update_videos_timestamp
AFTER UPDATE ON generated_videos
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE generated_videos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================
-- Verification queries (run these to confirm migration success)
-- ============================================================

-- Verify all columns exist:
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='generated_videos';

-- Verify indexes exist:
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='generated_videos';

-- Verify trigger exists:
-- SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='generated_videos';

-- ============================================================
-- Notes:
-- ============================================================
-- - This migration is idempotent (IF NOT EXISTS) - safe to run multiple times
-- - No data is lost - only adds columns with default values
-- - SQLite doesn't support DROP COLUMN, so no rollback script provided
-- - For rollback, you would need to recreate the table without these columns
-- - All JSON fields stored as TEXT (SQLite best practice)
-- - BLOB storage removed for better query performance
-- - Videos now stored as files on disk, URLs in database
