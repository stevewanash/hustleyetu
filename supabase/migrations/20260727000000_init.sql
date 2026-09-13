-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Create helper function for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 1. BILLS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_hash VARCHAR(16) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    pdf_storage_path TEXT,
    extracted_text TEXT,
    ai_summary_en TEXT,
    ai_summary_sw TEXT,
    ai_status VARCHAR(20) NOT NULL DEFAULT 'ingested',
    ai_error TEXT,
    verification_score DECIMAL(3,2),
    regex_extractions JSONB,
    source_api VARCHAR(20) NOT NULL DEFAULT 'scraper',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for bills
CREATE INDEX IF NOT EXISTS idx_bills_ai_status ON bills (ai_status);
CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills (created_at DESC);

-- Trigger for bills
CREATE TRIGGER update_bills_updated_at
BEFORE UPDATE ON bills
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ==========================================
-- 2. BILL TAGS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS bill_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    industry_tag VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    CONSTRAINT unique_bill_tag UNIQUE(bill_id, industry_tag)
);

-- Indexes for bill_tags
CREATE INDEX IF NOT EXISTS idx_bill_tags_industry ON bill_tags (industry_tag);


-- ==========================================
-- 3. SUBSCRIBERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash VARCHAR(64) UNIQUE NOT NULL,
    phone_encrypted TEXT NOT NULL,
    industry_tags TEXT[] NOT NULL,
    preferred_tier VARCHAR(100),
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    channels TEXT[] NOT NULL DEFAULT '{sms}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    consent_given_at TIMESTAMPTZ NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL, -- FK to Supabase Auth
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for subscribers
CREATE INDEX IF NOT EXISTS idx_subscribers_industry ON subscribers USING GIN (industry_tags);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers (is_active) WHERE is_active = TRUE;

-- Trigger for subscribers
CREATE TRIGGER update_subscribers_updated_at
BEFORE UPDATE ON subscribers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ==========================================
-- 4. FEEDBACK TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, -- FK to Supabase Auth
    support VARCHAR(10) NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    concerns TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_bill_user_feedback UNIQUE(bill_id, user_id)
);

-- Indexes for feedback
CREATE INDEX IF NOT EXISTS idx_feedback_bill_id ON feedback (bill_id);


-- ==========================================
-- 5. USER PROFILES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, -- FK to Supabase Auth
    industry VARCHAR(100) NOT NULL,
    tier_label VARCHAR(100),
    custom_metrics JSONB NOT NULL,
    consent_given_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ==========================================
-- 6. NOTIFICATIONS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    subscriber_id UUID NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
    channel VARCHAR(10) NOT NULL,
    message_body TEXT NOT NULL,
    at_message_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    failure_reason TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_bill_subscriber_channel UNIQUE(bill_id, subscriber_id, channel)
);

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications (status);
CREATE INDEX IF NOT EXISTS idx_notifications_subscriber ON notifications (subscriber_id);


-- ==========================================
-- 7. TIER IMPACT CACHE TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS tier_impact_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    industry VARCHAR(100) NOT NULL,
    tier_label VARCHAR(100) NOT NULL,
    impact_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_bill_industry_tier_impact UNIQUE(bill_id, industry, tier_label)
);

-- Index for tier_impact_cache lookup
CREATE INDEX IF NOT EXISTS idx_tier_impact_lookup ON tier_impact_cache (bill_id, industry, tier_label);