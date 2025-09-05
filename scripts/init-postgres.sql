-- ==============================================
-- SOPHIA INTEL AI - PostgreSQL Initialization
-- Creates database schema and tables for local development
-- ==============================================

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==============================================
-- MEMORY & KNOWLEDGE STORAGE
-- ==============================================

-- Memory entries table
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    embedding VECTOR(1536), -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(100),
    session_id VARCHAR(100)
);

-- Full text search index
CREATE INDEX IF NOT EXISTS memory_entries_fts_idx ON memory_entries USING GIN(to_tsvector('english', content));

-- Vector similarity index
CREATE INDEX IF NOT EXISTS memory_entries_embedding_idx ON memory_entries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Metadata index
CREATE INDEX IF NOT EXISTS memory_entries_metadata_idx ON memory_entries USING GIN(metadata);

-- Time-based indexes
CREATE INDEX IF NOT EXISTS memory_entries_created_at_idx ON memory_entries(created_at);
CREATE INDEX IF NOT EXISTS memory_entries_user_session_idx ON memory_entries(user_id, session_id);

-- ==============================================
-- CONVERSATION & SESSION TRACKING
-- ==============================================

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    title VARCHAR(200),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Session index
CREATE INDEX IF NOT EXISTS sessions_session_id_idx ON sessions(session_id);
CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_last_activity_idx ON sessions(last_activity);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) REFERENCES sessions(session_id),
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Message indexes
CREATE INDEX IF NOT EXISTS messages_session_id_idx ON messages(session_id);
CREATE INDEX IF NOT EXISTS messages_created_at_idx ON messages(created_at);
CREATE INDEX IF NOT EXISTS messages_role_idx ON messages(role);

-- ==============================================
-- AGENT & SWARM ORCHESTRATION
-- ==============================================

-- Agent definitions
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',
    model_config JSONB DEFAULT '{}',
    tools JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Agent index
CREATE INDEX IF NOT EXISTS agents_agent_id_idx ON agents(agent_id);
CREATE INDEX IF NOT EXISTS agents_is_active_idx ON agents(is_active);

-- Team definitions
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    members JSONB DEFAULT '[]', -- Array of agent_ids
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Team index
CREATE INDEX IF NOT EXISTS teams_team_id_idx ON teams(team_id);
CREATE INDEX IF NOT EXISTS teams_is_active_idx ON teams(is_active);

-- Execution history
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    session_id VARCHAR(100),
    agent_id VARCHAR(100),
    team_id VARCHAR(100),
    input TEXT,
    output TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Execution indexes
CREATE INDEX IF NOT EXISTS executions_execution_id_idx ON executions(execution_id);
CREATE INDEX IF NOT EXISTS executions_session_id_idx ON executions(session_id);
CREATE INDEX IF NOT EXISTS executions_status_idx ON executions(status);
CREATE INDEX IF NOT EXISTS executions_started_at_idx ON executions(started_at);

-- ==============================================
-- API USAGE & MONITORING
-- ==============================================

-- API calls tracking
CREATE TABLE IF NOT EXISTS api_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL, -- 'openai', 'anthropic', 'openrouter', etc.
    model VARCHAR(100),
    endpoint VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    cost_estimate DECIMAL(10,6) DEFAULT 0.0,
    response_time_ms INTEGER,
    status VARCHAR(20), -- 'success', 'error', 'timeout'
    error_message TEXT,
    session_id VARCHAR(100),
    user_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API calls indexes
CREATE INDEX IF NOT EXISTS api_calls_provider_idx ON api_calls(provider);
CREATE INDEX IF NOT EXISTS api_calls_created_at_idx ON api_calls(created_at);
CREATE INDEX IF NOT EXISTS api_calls_status_idx ON api_calls(status);
CREATE INDEX IF NOT EXISTS api_calls_user_id_idx ON api_calls(user_id);

-- ==============================================
-- VECTOR STORE SYNCHRONIZATION
-- ==============================================

-- Track vector store synchronization
CREATE TABLE IF NOT EXISTS vector_sync (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID REFERENCES memory_entries(id),
    vector_store_id VARCHAR(200), -- Weaviate object ID
    vector_store_type VARCHAR(50) DEFAULT 'weaviate', -- 'weaviate' only (qdrant removed)
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'synced', 'failed'
    last_synced TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Vector sync indexes
CREATE INDEX IF NOT EXISTS vector_sync_memory_id_idx ON vector_sync(memory_id);
CREATE INDEX IF NOT EXISTS vector_sync_status_idx ON vector_sync(sync_status);
CREATE INDEX IF NOT EXISTS vector_sync_store_type_idx ON vector_sync(vector_store_type);

-- ==============================================
-- FUNCTIONS & TRIGGERS
-- ==============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_memory_entries_updated_at BEFORE UPDATE ON memory_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update session last_activity
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions SET last_activity = NOW() WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update session activity on new messages
CREATE TRIGGER update_session_last_activity AFTER INSERT ON messages FOR EACH ROW EXECUTE FUNCTION update_session_activity();

-- ==============================================
-- INITIAL DATA
-- ==============================================

-- Insert default agents
INSERT INTO agents (agent_id, name, description, config, model_config, tools) VALUES
('strategic-planner', 'Strategic Planner', 'High-level strategy and architecture planning',
 '{"role": "planner", "priority": 10}',
 '{"provider": "openai", "model": "gpt-4", "temperature": 0.3, "max_tokens": 2000}',
 '["analysis", "planning", "documentation"]'),
('code-developer', 'Code Developer', 'Core development and implementation',
 '{"role": "developer", "priority": 8}',
 '{"provider": "openai", "model": "gpt-4", "temperature": 0.2, "max_tokens": 4000}',
 '["coding", "testing", "debugging", "file_operations"]'),
('quality-critic', 'Quality Critic', 'Code review and quality assurance',
 '{"role": "critic", "priority": 9}',
 '{"provider": "anthropic", "model": "claude-3-sonnet", "temperature": 0.1, "max_tokens": 3000}',
 '["review", "testing", "analysis"]')
ON CONFLICT (agent_id) DO NOTHING;

-- Insert default teams
INSERT INTO teams (team_id, name, description, members, config) VALUES
('development-swarm', 'Development Swarm', 'Full-stack development team',
 '["strategic-planner", "code-developer", "quality-critic"]',
 '{"model_pool": "balanced", "max_iterations": 5}'),
('strategic-swarm', 'Strategic Swarm', 'High-level planning and architecture',
 '["strategic-planner", "quality-critic"]',
 '{"model_pool": "heavy", "max_iterations": 3}')
ON CONFLICT (team_id) DO NOTHING;

-- ==============================================
-- PERMISSIONS & SECURITY
-- ==============================================

-- Grant permissions to sophia user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sophia;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sophia;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sophia;

-- Create read-only user for monitoring
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sophia_readonly') THEN
        CREATE USER sophia_readonly WITH PASSWORD 'sophia_readonly_2024';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE sophia TO sophia_readonly;
GRANT USAGE ON SCHEMA public TO sophia_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sophia_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sophia_readonly;

-- Final setup
ANALYZE;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✅ Sophia Intel AI PostgreSQL schema initialized successfully';
    RAISE NOTICE '📊 Tables created: %, %, %, %, %, %, %, %',
        'memory_entries', 'sessions', 'messages', 'agents', 'teams', 'executions', 'api_calls', 'vector_sync';
    RAISE NOTICE '🔧 Extensions enabled: uuid-ossp, vector, pg_trgm';
    RAISE NOTICE '👥 Users: sophia (admin), sophia_readonly (monitoring)';
END $$;
