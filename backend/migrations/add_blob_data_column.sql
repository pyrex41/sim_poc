-- Migration: Add blob_data column to assets table
-- This column stores binary asset data directly in the database
-- Run this on production database before deploying new code

-- Add blob_data column if it doesn't exist
-- Note: SQLite doesn't have IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- If column already exists, this will error (which is safe - just means it's already added)

ALTER TABLE assets ADD COLUMN blob_data BLOB;

-- Verify the column was added
-- Run this separately to check:
-- PRAGMA table_info(assets);

-- Expected output should include:
-- ... | blob_data | BLOB | 0 | NULL | 0
