-- Phase 7: RAG & Verification Enhancement Schema
-- 1. Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- 2. Create bill_chunks table for structural vector storage
CREATE TABLE IF NOT EXISTS public.bill_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES public.bills(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    section_ref VARCHAR(150),
    token_count INTEGER DEFAULT 0,
    embedding extensions.vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_bill_chunks_bill_chunk UNIQUE (bill_id, chunk_index)
);

-- Indexes on bill_chunks
CREATE INDEX IF NOT EXISTS idx_bill_chunks_bill_id_index ON public.bill_chunks (bill_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_bill_chunks_embedding ON public.bill_chunks USING hnsw (embedding extensions.vector_cosine_ops);

-- 3. Create match_bill_chunks vector search RPC function
CREATE OR REPLACE FUNCTION public.match_bill_chunks(
    query_embedding extensions.vector(768),
    match_threshold float DEFAULT 0.0,
    match_count int DEFAULT 5,
    filter_bill_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    bill_id uuid,
    chunk_index int,
    chunk_text text,
    section_ref varchar(150),
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        bc.id,
        bc.bill_id,
        bc.chunk_index,
        bc.chunk_text,
        bc.section_ref,
        (1 - (bc.embedding <=> query_embedding))::float AS similarity
    FROM public.bill_chunks bc
    WHERE (filter_bill_id IS NULL OR bc.bill_id = filter_bill_id)
      AND (1 - (bc.embedding <=> query_embedding)) > match_threshold
    ORDER BY bc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 4. Create llm_usage_log table for token usage and cost monitoring
CREATE TABLE IF NOT EXISTS public.llm_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID REFERENCES public.bills(id) ON DELETE SET NULL,
    agent_name VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms FLOAT NOT NULL DEFAULT 0.0,
    estimated_cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indexes on llm_usage_log
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_bill_id ON public.llm_usage_log(bill_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_agent_name ON public.llm_usage_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_created_at ON public.llm_usage_log(created_at DESC);

-- Grants
GRANT ALL PRIVILEGES ON TABLE public.bill_chunks TO anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON TABLE public.llm_usage_log TO anon, authenticated, service_role;
