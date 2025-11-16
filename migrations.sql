-- Complete database migration for deployment
-- SQLite compatible - will show errors for columns that already exist, that's OK

-- ============================================
-- Migration 1: Add video job workflow fields
-- ============================================

-- Add progress tracking
ALTER TABLE generated_videos ADD COLUMN progress TEXT;

-- Add storyboard data
ALTER TABLE generated_videos ADD COLUMN storyboard_data TEXT;

-- Add approval fields
ALTER TABLE generated_videos ADD COLUMN approved BOOLEAN DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN approved_at TIMESTAMP;

-- Add cost tracking
ALTER TABLE generated_videos ADD COLUMN estimated_cost REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN actual_cost REAL DEFAULT 0.0;

-- Add error tracking
ALTER TABLE generated_videos ADD COLUMN error_message TEXT;

-- Add updated timestamp (can't use CURRENT_TIMESTAMP as default in ALTER TABLE)
ALTER TABLE generated_videos ADD COLUMN updated_at TIMESTAMP;

-- Add download and refinement tracking
ALTER TABLE generated_videos ADD COLUMN download_count INTEGER DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN refinement_count INTEGER DEFAULT 0;

-- Initialize updated_at for existing records
UPDATE generated_videos SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Create trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_generated_videos_timestamp;
CREATE TRIGGER update_generated_videos_timestamp
AFTER UPDATE ON generated_videos
FOR EACH ROW
BEGIN
    UPDATE generated_videos
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================
-- Migration 2: Add Clients and Campaigns
-- ============================================

-- Create clients table
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    brand_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create campaigns table
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
);

-- Add campaign_id to generated_videos
ALTER TABLE generated_videos ADD COLUMN campaign_id TEXT REFERENCES campaigns(id);

-- Add format and duration to generated_videos
ALTER TABLE generated_videos ADD COLUMN format TEXT CHECK (format IN ('9:16', '1:1', '16:9')) DEFAULT '16:9';
ALTER TABLE generated_videos ADD COLUMN duration INTEGER CHECK (duration IN (15, 30, 60)) DEFAULT 30;

-- Add video metrics columns
ALTER TABLE generated_videos ADD COLUMN views INTEGER DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN clicks INTEGER DEFAULT 0;
ALTER TABLE generated_videos ADD COLUMN ctr REAL DEFAULT 0.0;
ALTER TABLE generated_videos ADD COLUMN conversions INTEGER DEFAULT 0;

-- Create indexes for clients and campaigns
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);
CREATE INDEX IF NOT EXISTS idx_campaigns_client_id ON campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_videos_campaign_id ON generated_videos(campaign_id);

-- Create triggers for updated_at timestamps
DROP TRIGGER IF EXISTS update_clients_timestamp;
CREATE TRIGGER update_clients_timestamp
AFTER UPDATE ON clients
FOR EACH ROW
BEGIN
    UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS update_campaigns_timestamp;
CREATE TRIGGER update_campaigns_timestamp
AFTER UPDATE ON campaigns
FOR EACH ROW
BEGIN
    UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- Migration 3: Consolidate Assets Table
-- ============================================

-- Drop old asset tables if they exist
DROP TABLE IF EXISTS uploaded_assets;
DROP TABLE IF EXISTS client_assets;
DROP TABLE IF EXISTS campaign_assets;

-- Create new consolidated assets table
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    client_id TEXT,
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
);

-- Create indexes for assets table
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_client_id ON assets(client_id);
CREATE INDEX IF NOT EXISTS idx_assets_campaign_id ON assets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_uploaded_at ON assets(uploaded_at);
