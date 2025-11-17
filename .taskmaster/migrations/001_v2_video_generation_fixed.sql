-- Migration: v2 Video Generation API
-- Version: 001 (SQLite Compatible)
-- Date: 2025-11-15
-- Description: Add columns for video generation workflow, approval, cost tracking, and error handling

-- ============================================================
-- Add new columns to generated_videos table
-- SQLite doesn't support IF NOT EXISTS in ALTER COLUMN
-- So we wrap each in a check via Python or accept errors on re-run
-- ============================================================

-- Progress tracking (JSON stored as TEXT in SQLite)
ALTER TABLE generated_videos ADD COLUMN progress TEXT DEFAULT '{}';

-- Storyboard data (JSON array of scenes)
ALTER TABLE generated_videos ADD COLUMN storyboard_data TEXT;

-- Approval workflow
ALTER TABLE generated_videos ADD COLUMN approved BOOLEAN DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN approved_at TIMESTAMP;

-- Cost tracking
ALTER TABLE generated_videos ADD COLUMN estimated_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN actual_cost REAL DEFAULT 0.0;

-- Error handling and retry logic (retry_count already added via download system)
ALTER TABLE generated_videos ADD COLUMN error_message TEXT;

-- Timestamp for stuck job detection
ALTER TABLE generated_videos ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ============================================================
-- Create indexes for performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_videos_status ON generated_videos(status);
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
-- Notes:
-- ============================================================
-- - Removed campaign_id and client_id indexes (columns don't exist in current schema)
-- - Removed retry_count (already exists from previous download_retries)
-- - This migration will fail if run twice (columns already exist)
-- - Use Python wrapper with try/except for idempotent migrations
