-- ============================================================================
-- Ad Video Generation Platform - Complete Database Schema
-- ============================================================================
-- This schema represents the complete, authoritative database structure.
-- Run migrations on server init to ensure all tables and columns exist.
-- ============================================================================

-- ============================================================================
-- AUTHENTICATION & USER MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- ============================================================================
-- CLIENT & CAMPAIGN MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    homepage TEXT,
    brand_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'archived', 'draft')) DEFAULT 'draft',
    product_url TEXT,
    brief TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaigns_client_id ON campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

-- ============================================================================
-- ASSET MANAGEMENT (Consolidated)
-- ============================================================================

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
    blob_data BLOB,
    blob_id TEXT,
    source_url TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_client_id ON assets(client_id);
CREATE INDEX IF NOT EXISTS idx_assets_campaign_id ON assets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_uploaded_at ON assets(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_assets_blob_id ON assets(blob_id);

-- ============================================================================
-- BLOB STORAGE (for V3 asset handling)
-- ============================================================================

CREATE TABLE IF NOT EXISTS asset_blobs (
    id TEXT PRIMARY KEY,
    data BLOB NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_asset_blobs_created_at ON asset_blobs(created_at);

-- ============================================================================
-- CREATIVE BRIEFS
-- ============================================================================

CREATE TABLE IF NOT EXISTS creative_briefs (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    prompt_text TEXT,
    image_url TEXT,
    video_url TEXT,
    image_data BLOB,
    video_data BLOB,
    creative_direction TEXT NOT NULL,
    scenes TEXT NOT NULL,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_briefs_user ON creative_briefs(user_id);
CREATE INDEX IF NOT EXISTS idx_briefs_created ON creative_briefs(created_at DESC);

-- ============================================================================
-- GENERATED CONTENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    scene_data TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    brief_id TEXT,
    FOREIGN KEY (brief_id) REFERENCES creative_briefs(id)
);

CREATE INDEX IF NOT EXISTS idx_created_at ON generated_scenes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model ON generated_scenes(model);
CREATE INDEX IF NOT EXISTS idx_scenes_brief ON generated_scenes(brief_id);

CREATE TABLE IF NOT EXISTS generated_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    image_url TEXT NOT NULL,
    model_id TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collection TEXT,
    metadata TEXT,
    download_attempted BOOLEAN DEFAULT 0,
    download_retries INTEGER DEFAULT 0,
    download_error TEXT,
    image_data BLOB,
    brief_id TEXT,
    client_id TEXT,
    campaign_id TEXT,
    FOREIGN KEY (brief_id) REFERENCES creative_briefs(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX IF NOT EXISTS idx_images_created_at ON generated_images(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_model ON generated_images(model_id);
CREATE INDEX IF NOT EXISTS idx_images_brief ON generated_images(brief_id);
CREATE INDEX IF NOT EXISTS idx_images_client ON generated_images(client_id);
CREATE INDEX IF NOT EXISTS idx_images_campaign ON generated_images(campaign_id);

CREATE TABLE IF NOT EXISTS generated_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    video_url TEXT NOT NULL,
    model_id TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collection TEXT,
    metadata TEXT,
    download_attempted BOOLEAN DEFAULT 0,
    download_retries INTEGER DEFAULT 0,
    download_error TEXT,
    video_data BLOB,
    thumbnail_data BLOB,
    progress TEXT,
    storyboard_data TEXT,
    approved BOOLEAN DEFAULT 0,
    approved_at TIMESTAMP,
    estimated_cost REAL DEFAULT 0.0,
    actual_cost REAL DEFAULT 0.0,
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    refinement_count INTEGER DEFAULT 0,
    brief_id TEXT,
    client_id TEXT,
    campaign_id TEXT,
    format TEXT CHECK (format IN ('9:16', '1:1', '16:9')) DEFAULT '16:9',
    duration INTEGER CHECK (duration IN (15, 30, 60)) DEFAULT 30,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0.0,
    conversions INTEGER DEFAULT 0,
    FOREIGN KEY (brief_id) REFERENCES creative_briefs(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX IF NOT EXISTS idx_videos_created_at ON generated_videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_brief ON generated_videos(brief_id);
CREATE INDEX IF NOT EXISTS idx_videos_model ON generated_videos(model_id);
CREATE INDEX IF NOT EXISTS idx_videos_client ON generated_videos(client_id);
CREATE INDEX IF NOT EXISTS idx_videos_campaign ON generated_videos(campaign_id);

-- ============================================================================
-- JOB SCENES (for V3 scene generation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_scenes (
    id TEXT PRIMARY KEY,
    job_id INTEGER NOT NULL,
    scene_number INTEGER NOT NULL,
    duration_seconds REAL NOT NULL,
    description TEXT NOT NULL,
    script TEXT,
    shot_type TEXT,
    transition TEXT,
    assets TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES generated_videos(id) ON DELETE CASCADE,
    UNIQUE(job_id, scene_number)
);

CREATE INDEX IF NOT EXISTS idx_job_scenes_job_id ON job_scenes(job_id);
CREATE INDEX IF NOT EXISTS idx_job_scenes_scene_number ON job_scenes(scene_number);

CREATE TABLE IF NOT EXISTS generated_audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    audio_url TEXT NOT NULL,
    model_id TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collection TEXT,
    metadata TEXT,
    download_attempted BOOLEAN DEFAULT 0,
    download_retries INTEGER DEFAULT 0,
    download_error TEXT,
    audio_data BLOB,
    duration REAL,
    brief_id TEXT,
    client_id TEXT,
    campaign_id TEXT,
    FOREIGN KEY (brief_id) REFERENCES creative_briefs(id),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX IF NOT EXISTS idx_audio_created_at ON generated_audio(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audio_model ON generated_audio(model_id);
CREATE INDEX IF NOT EXISTS idx_audio_brief ON generated_audio(brief_id);
CREATE INDEX IF NOT EXISTS idx_audio_client ON generated_audio(client_id);
CREATE INDEX IF NOT EXISTS idx_audio_campaign ON generated_audio(campaign_id);

CREATE TABLE IF NOT EXISTS genesis_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_data TEXT NOT NULL,
    video_path TEXT NOT NULL,
    quality TEXT NOT NULL,
    duration REAL NOT NULL,
    fps INTEGER NOT NULL,
    resolution TEXT,
    scene_context TEXT,
    object_descriptions TEXT,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_genesis_videos_created_at ON genesis_videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_genesis_videos_quality ON genesis_videos(quality);

-- ============================================================================
-- LEGACY TABLES (for backwards compatibility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS uploaded_assets (
    asset_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assets_user ON uploaded_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_uploaded ON uploaded_assets(uploaded_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_clients_timestamp
AFTER UPDATE ON clients
FOR EACH ROW
BEGIN
    UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_campaigns_timestamp
AFTER UPDATE ON campaigns
FOR EACH ROW
BEGIN
    UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
