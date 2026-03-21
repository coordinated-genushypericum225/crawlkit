-- CrawlKit Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS ck_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    password_hash TEXT,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- API Keys table
CREATE TABLE IF NOT EXISTS ck_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ck_users(id) ON DELETE CASCADE,
    key TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT 'Default',
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_hour INT DEFAULT 20,
    max_batch_size INT DEFAULT 5,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS ck_usage (
    id BIGSERIAL PRIMARY KEY,
    api_key_id UUID REFERENCES ck_api_keys(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    url TEXT,
    parser_used TEXT,
    content_type TEXT,
    content_length INT DEFAULT 0,
    chunks_count INT DEFAULT 0,
    crawl_time_ms INT DEFAULT 0,
    success BOOLEAN DEFAULT true,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Monthly usage summary (for billing)
CREATE TABLE IF NOT EXISTS ck_usage_monthly (
    id BIGSERIAL PRIMARY KEY,
    api_key_id UUID REFERENCES ck_api_keys(id) ON DELETE CASCADE,
    month DATE NOT NULL,
    total_requests INT DEFAULT 0,
    total_chars BIGINT DEFAULT 0,
    total_chunks INT DEFAULT 0,
    successful_requests INT DEFAULT 0,
    failed_requests INT DEFAULT 0,
    UNIQUE(api_key_id, month)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ck_api_keys_key ON ck_api_keys(key);
CREATE INDEX IF NOT EXISTS idx_ck_api_keys_user ON ck_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_ck_usage_api_key ON ck_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_ck_usage_created ON ck_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_ck_usage_monthly_key ON ck_usage_monthly(api_key_id);

-- Payment requests table
CREATE TABLE IF NOT EXISTS ck_payment_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ck_users(id) ON DELETE CASCADE,
    plan_requested TEXT NOT NULL,
    amount_vnd BIGINT NOT NULL,
    memo TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT now(),
    confirmed_at TIMESTAMPTZ,
    confirmed_by TEXT
);

-- Settings table
CREATE TABLE IF NOT EXISTS ck_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_ck_payment_requests_user ON ck_payment_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_ck_payment_requests_status ON ck_payment_requests(status);

-- URL watches table
CREATE TABLE IF NOT EXISTS ck_watches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES ck_api_keys(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    webhook_url TEXT,
    selector TEXT,
    check_interval_minutes INT DEFAULT 60,
    content_hash TEXT,
    last_checked_at TIMESTAMPTZ,
    last_changed_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for watches
CREATE INDEX IF NOT EXISTS idx_ck_watches_api_key ON ck_watches(api_key_id);
CREATE INDEX IF NOT EXISTS idx_ck_watches_active ON ck_watches(is_active);
CREATE INDEX IF NOT EXISTS idx_ck_watches_last_checked ON ck_watches(last_checked_at);

-- Insert default settings
INSERT INTO ck_settings (key, value) VALUES 
    ('bank_id', ''),
    ('bank_account', ''),
    ('bank_holder', ''),
    ('price_starter_vnd', '475000'),
    ('price_pro_vnd', '1975000')
ON CONFLICT (key) DO NOTHING;

-- RLS policies
ALTER TABLE ck_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_usage_monthly ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_payment_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ck_watches ENABLE ROW LEVEL SECURITY;
