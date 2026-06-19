-- MemoraAI - Database Schema
CREATE EXTENSION IF NOT EXISTS "vector";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source VARCHAR(500) NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('pdf', 'url', 'text')),
    title VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    indexed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);

-- Chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(3072),
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    token_count INTEGER,
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', content)
    ) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector similarity index (disabled because pgvector indexes (ivfflat/hnsw) do not support > 2000 dimensions)
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_chunks_search ON chunks USING gin(search_vector);

-- Composite index for document lookup
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

-- Short-term memory (conversation history)
CREATE TABLE IF NOT EXISTS short_term_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stm_session_id ON short_term_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_stm_created_at ON short_term_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stm_session_time ON short_term_memory(session_id, created_at DESC);

-- Long-term memory (persistent user facts)
CREATE TABLE IF NOT EXISTS long_term_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    key VARCHAR(200) NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, key)
);

CREATE INDEX IF NOT EXISTS idx_ltm_user_id ON long_term_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_ltm_category ON long_term_memory(user_id, category);

-- Episodic memory (session summaries)
CREATE TABLE IF NOT EXISTS episodic_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    key_topics JSONB DEFAULT '[]',
    important_facts JSONB DEFAULT '[]',
    sentiment VARCHAR(50),
    duration_minutes INTEGER,
    message_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_em_user_id ON episodic_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_em_session_id ON episodic_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_em_created_at ON episodic_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_em_user_time ON episodic_memory(user_id, created_at DESC);

-- Ingestion jobs tracking
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(500) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    total_chunks INTEGER DEFAULT 0,
    chunks_processed INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ij_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ij_source ON ingestion_jobs(source);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at (drop first to allow re-running)
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ltm_updated_at ON long_term_memory;
CREATE TRIGGER update_ltm_updated_at
    BEFORE UPDATE ON long_term_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function for hybrid search scoring
CREATE OR REPLACE FUNCTION hybrid_search_score(
    vector_rank INTEGER,
    fts_rank FLOAT
)
RETURNS FLOAT AS $$
DECLARE
    rrf_score FLOAT;
BEGIN
    rrf_score := 1.0 / (60 + vector_rank) + 1.0 / (60 + fts_rank);
    RETURN rrf_score;
END;
$$ LANGUAGE plpgsql;

-- View for combined retrieval results
CREATE OR REPLACE VIEW retrieval_results AS
SELECT 
    c.id,
    c.document_id,
    c.content,
    c.metadata,
    c.chunk_index,
    d.source,
    d.title
FROM chunks c
JOIN documents d ON c.document_id = d.id;

-- Statistics and monitoring views
CREATE OR REPLACE VIEW chunk_statistics AS
SELECT 
    document_id,
    COUNT(*) as chunk_count,
    SUM(token_count) as total_tokens,
    AVG(LENGTH(content)) as avg_chunk_length,
    MIN(created_at) as first_chunk,
    MAX(created_at) as last_chunk
FROM chunks
GROUP BY document_id;

CREATE OR REPLACE VIEW memory_usage_stats AS
SELECT 
    'short_term' as memory_type,
    COUNT(*) as total_entries,
    COUNT(DISTINCT session_id) as unique_sessions
FROM short_term_memory
UNION ALL
SELECT 
    'long_term' as memory_type,
    COUNT(*) as total_entries,
    COUNT(DISTINCT user_id) as unique_users
FROM long_term_memory
UNION ALL
SELECT 
    'episodic' as memory_type,
    COUNT(*) as total_entries,
    COUNT(DISTINCT user_id) as unique_users
FROM episodic_memory;
