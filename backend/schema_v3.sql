-- ============================================================================
-- Generation Platform v3 - Clean Database Schema
-- ============================================================================
-- Designed for composable, modular generation engines
-- Breaking change: New architecture, fresh start
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

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
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- ============================================================================
-- CLIENT & CAMPAIGN MANAGEMENT
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);

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

CREATE INDEX IF NOT EXISTS idx_campaigns_client_id ON campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

-- ============================================================================
-- GENERATION ENGINE SYSTEM
-- ============================================================================

-- Central table for all async generation tasks
CREATE TABLE IF NOT EXISTS generation_tasks (
    id TEXT PRIMARY KEY,
    engine TEXT NOT NULL CHECK (engine IN ('image', 'video', 'audio', 'prompt')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'canceled')) DEFAULT 'pending',

    -- Provider info
    provider TEXT NOT NULL,
    provider_task_id TEXT,

    -- User context
    user_id INTEGER NOT NULL,
    client_id TEXT,
    campaign_id TEXT,

    -- Task data (JSON)
    params TEXT NOT NULL,  -- JSON: generation parameters
    result TEXT,           -- JSON: generation result
    error TEXT,            -- Error message if failed
    metadata TEXT,         -- JSON: custom metadata

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_engine ON generation_tasks(engine);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON generation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON generation_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_client ON generation_tasks(client_id);
CREATE INDEX IF NOT EXISTS idx_tasks_campaign ON generation_tasks(campaign_id);
CREATE INDEX IF NOT EXISTS idx_tasks_provider_id ON generation_tasks(provider_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON generation_tasks(created_at DESC);

-- Generated content (images, videos, audio)
-- This table stores the final results with full metadata
CREATE TABLE IF NOT EXISTS generated_content (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('image', 'video', 'audio')),

    -- URLs and storage
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    local_path TEXT,

    -- File info
    format TEXT NOT NULL,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    duration INTEGER,  -- For video/audio (seconds)

    -- Generation details (JSON)
    generation_params TEXT NOT NULL,  -- JSON: full parameters used

    -- Context
    user_id INTEGER NOT NULL,
    client_id TEXT,
    campaign_id TEXT,

    -- Metadata
    tags TEXT,  -- JSON: array of tags
    metadata TEXT,  -- JSON: custom metadata

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES generation_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_content_task ON generated_content(task_id);
CREATE INDEX IF NOT EXISTS idx_content_type ON generated_content(content_type);
CREATE INDEX IF NOT EXISTS idx_content_user ON generated_content(user_id);
CREATE INDEX IF NOT EXISTS idx_content_client ON generated_content(client_id);
CREATE INDEX IF NOT EXISTS idx_content_campaign ON generated_content(campaign_id);
CREATE INDEX IF NOT EXISTS idx_content_created ON generated_content(created_at DESC);

-- ============================================================================
-- PIPELINE ORCHESTRATION
-- ============================================================================

-- Pipeline execution tracking
CREATE TABLE IF NOT EXISTS pipeline_executions (
    id TEXT PRIMARY KEY,
    name TEXT,
    execution_mode TEXT NOT NULL CHECK (execution_mode IN ('sequential', 'parallel', 'dag')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'canceled')) DEFAULT 'pending',

    -- User context
    user_id INTEGER NOT NULL,
    client_id TEXT,
    campaign_id TEXT,

    -- Pipeline definition (JSON)
    pipeline_config TEXT NOT NULL,  -- JSON: full pipeline configuration

    -- Results
    output TEXT,  -- JSON: final pipeline output
    error TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_exec_user ON pipeline_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_exec_status ON pipeline_executions(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_exec_created ON pipeline_executions(created_at DESC);

-- Individual pipeline steps
CREATE TABLE IF NOT EXISTS pipeline_steps (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    engine TEXT NOT NULL,
    task_id TEXT,  -- Reference to generation_task
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'skipped')) DEFAULT 'pending',

    -- Step data
    input_params TEXT NOT NULL,  -- JSON: step input
    output TEXT,  -- JSON: step output
    error TEXT,

    -- Dependencies
    depends_on TEXT,  -- JSON: array of step indices this depends on

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    FOREIGN KEY (execution_id) REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES generation_tasks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_steps_execution ON pipeline_steps(execution_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_task ON pipeline_steps(task_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_steps_status ON pipeline_steps(status);

-- ============================================================================
-- ASSET MANAGEMENT (Uploaded files)
-- ============================================================================

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    client_id TEXT,
    campaign_id TEXT,

    name TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('image', 'video', 'audio', 'document', 'other')),

    -- Storage
    url TEXT NOT NULL,
    local_path TEXT,
    thumbnail_url TEXT,

    -- File info
    format TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,

    -- Media dimensions
    width INTEGER,
    height INTEGER,
    duration INTEGER,

    -- Metadata
    tags TEXT,  -- JSON: array of tags
    metadata TEXT,  -- JSON: custom metadata

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_assets_user ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_client ON assets(client_id);
CREATE INDEX IF NOT EXISTS idx_assets_campaign ON assets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_uploaded ON assets(uploaded_at DESC);

-- ============================================================================
-- WEBHOOK TRACKING (for provider callbacks)
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    provider_task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,  -- JSON: full webhook payload
    processed BOOLEAN DEFAULT 0,
    processed_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhooks_provider_id ON webhook_events(provider_task_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_processed ON webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_webhooks_created ON webhook_events(created_at DESC);

-- ============================================================================
-- SYSTEM METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (3, 'Generation Platform v3 - Modular architecture with composable engines');
