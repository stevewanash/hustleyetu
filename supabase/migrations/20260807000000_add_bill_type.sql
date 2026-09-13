-- Migration: Add bill_type column to bills table
-- Purpose: Support classification of bills as financial, regulatory, or hybrid
-- to route to the appropriate analysis agents (Financial Impact vs. Compliance Advisor)

ALTER TABLE bills ADD COLUMN IF NOT EXISTS bill_type VARCHAR(20) NOT NULL DEFAULT 'financial';

-- Add check constraint for valid bill types
ALTER TABLE bills ADD CONSTRAINT chk_bill_type
    CHECK (bill_type IN ('financial', 'regulatory', 'hybrid'));
