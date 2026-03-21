-- CrawlKit UI Database Migrations
-- Run this in Supabase SQL Editor

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

-- Settings table (key-value store)
CREATE TABLE IF NOT EXISTS ck_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Default settings
INSERT INTO ck_settings (key, value) VALUES 
    ('bank_id', 'MB') ON CONFLICT (key) DO NOTHING;
INSERT INTO ck_settings (key, value) VALUES 
    ('bank_account', '') ON CONFLICT (key) DO NOTHING;
INSERT INTO ck_settings (key, value) VALUES 
    ('bank_holder', '') ON CONFLICT (key) DO NOTHING;
INSERT INTO ck_settings (key, value) VALUES 
    ('price_starter_vnd', '475000') ON CONFLICT (key) DO NOTHING;
INSERT INTO ck_settings (key, value) VALUES 
    ('price_pro_vnd', '1975000') ON CONFLICT (key) DO NOTHING;

-- Index for faster payment request lookups
CREATE INDEX IF NOT EXISTS idx_payment_requests_user_id ON ck_payment_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_requests_status ON ck_payment_requests(status);
