-- CrawlKit Learning Engine Schema
-- Self-improving extraction patterns learned from successful crawls
-- Run this manually in Supabase SQL Editor

-- Site patterns learned from crawling
CREATE TABLE IF NOT EXISTS ck_site_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    domain TEXT NOT NULL,
    url_pattern TEXT NOT NULL,
    content_selectors JSONB DEFAULT '[]',
    title_selector TEXT,
    author_selector TEXT,
    date_selector TEXT,
    noise_selectors JSONB DEFAULT '[]',
    content_type TEXT DEFAULT 'generic',
    quality_score FLOAT DEFAULT 0.5,
    fingerprint TEXT,
    sample_count INT DEFAULT 1,
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(domain, url_pattern)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_patterns_domain ON ck_site_patterns(domain);
CREATE INDEX IF NOT EXISTS idx_patterns_fingerprint ON ck_site_patterns(fingerprint);
CREATE INDEX IF NOT EXISTS idx_patterns_quality ON ck_site_patterns(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_last_seen ON ck_site_patterns(last_seen DESC);

-- Extraction feedback from users (for improving quality)
CREATE TABLE IF NOT EXISTS ck_extraction_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    api_key_id UUID,
    feedback_type TEXT NOT NULL, -- 'good', 'bad', 'missing_content', 'wrong_type'
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_domain ON ck_extraction_feedback(domain);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON ck_extraction_feedback(created_at DESC);

-- Domain statistics (aggregated stats per domain)
CREATE TABLE IF NOT EXISTS ck_domain_stats (
    domain TEXT PRIMARY KEY,
    total_crawls INT DEFAULT 0,
    successful_crawls INT DEFAULT 0,
    avg_quality_score FLOAT DEFAULT 0,
    avg_content_length INT DEFAULT 0,
    content_types JSONB DEFAULT '{}',  -- {"article": 45, "listing": 12}
    last_crawled TIMESTAMPTZ DEFAULT NOW(),
    first_crawled TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_stats_crawls ON ck_domain_stats(total_crawls DESC);
CREATE INDEX IF NOT EXISTS idx_domain_stats_quality ON ck_domain_stats(avg_quality_score DESC);

-- Comments for documentation
COMMENT ON TABLE ck_site_patterns IS 'Learned extraction patterns from successful crawls';
COMMENT ON TABLE ck_extraction_feedback IS 'User feedback on extraction quality';
COMMENT ON TABLE ck_domain_stats IS 'Aggregated statistics per domain';

COMMENT ON COLUMN ck_site_patterns.fingerprint IS 'MD5 hash of DOM structure (tag hierarchy)';
COMMENT ON COLUMN ck_site_patterns.quality_score IS 'Extraction quality 0.0-1.0';
COMMENT ON COLUMN ck_site_patterns.sample_count IS 'Number of times this pattern was successfully used';
COMMENT ON COLUMN ck_site_patterns.content_selectors IS 'CSS selectors for main content (ordered by priority)';
COMMENT ON COLUMN ck_site_patterns.noise_selectors IS 'CSS selectors to remove (ads, nav, etc.)';

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_ck_site_patterns_updated_at
    BEFORE UPDATE ON ck_site_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ck_domain_stats_updated_at
    BEFORE UPDATE ON ck_domain_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for easy querying

-- Top learned domains
CREATE OR REPLACE VIEW ck_top_learned_domains AS
SELECT 
    domain,
    COUNT(*) as pattern_count,
    AVG(quality_score) as avg_quality,
    SUM(sample_count) as total_uses,
    MAX(last_seen) as last_seen
FROM ck_site_patterns
GROUP BY domain
ORDER BY total_uses DESC, avg_quality DESC;

-- Recent learning activity
CREATE OR REPLACE VIEW ck_recent_learnings AS
SELECT 
    domain,
    url_pattern,
    content_type,
    quality_score,
    sample_count,
    last_seen
FROM ck_site_patterns
ORDER BY last_seen DESC
LIMIT 100;

-- Learning stats summary
CREATE OR REPLACE VIEW ck_learning_stats AS
SELECT 
    COUNT(DISTINCT domain) as domains_learned,
    COUNT(*) as total_patterns,
    AVG(quality_score) as avg_quality,
    SUM(sample_count) as total_pattern_uses,
    MAX(last_seen) as last_activity
FROM ck_site_patterns;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ CrawlKit Learning Engine schema created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - ck_site_patterns (learned extraction patterns)';
    RAISE NOTICE '  - ck_extraction_feedback (user feedback)';
    RAISE NOTICE '  - ck_domain_stats (domain statistics)';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - ck_top_learned_domains';
    RAISE NOTICE '  - ck_recent_learnings';
    RAISE NOTICE '  - ck_learning_stats';
END $$;
