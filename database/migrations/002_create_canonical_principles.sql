-- Migration: 002_create_canonical_principles.sql
-- Description: Create canonical_principles table for Primary Mentor Initiative
-- Date: 2025-08-15

CREATE TABLE IF NOT EXISTS canonical_principles (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    principle_text TEXT NOT NULL,
    source_interaction_id VARCHAR(255),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'pending')),
    importance_score INTEGER DEFAULT 5 CHECK (importance_score >= 1 AND importance_score <= 10),
    tags TEXT[], -- Array of tags for categorization
    notion_page_id VARCHAR(255), -- Link to Notion page
    embedding_id VARCHAR(255) -- Reference to Qdrant vector ID
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_canonical_principles_entity_type ON canonical_principles(entity_type);
CREATE INDEX IF NOT EXISTS idx_canonical_principles_entity_name ON canonical_principles(entity_name);
CREATE INDEX IF NOT EXISTS idx_canonical_principles_status ON canonical_principles(status);
CREATE INDEX IF NOT EXISTS idx_canonical_principles_created_at ON canonical_principles(created_at);
CREATE INDEX IF NOT EXISTS idx_canonical_principles_importance ON canonical_principles(importance_score);
CREATE INDEX IF NOT EXISTS idx_canonical_principles_notion_id ON canonical_principles(notion_page_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_canonical_principles_updated_at 
    BEFORE UPDATE ON canonical_principles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample canonical principles for SOPHIA
INSERT INTO canonical_principles (entity_type, entity_name, principle_text, created_by, importance_score, tags) VALUES
('AI_ASSISTANT', 'SOPHIA', 'Always prioritize accuracy and truthfulness over speed of response. When uncertain, explicitly state the uncertainty rather than guessing.', 'system', 10, ARRAY['accuracy', 'truthfulness', 'core_values']),
('AI_ASSISTANT', 'SOPHIA', 'Maintain context awareness throughout conversations. Reference previous interactions and build upon established knowledge.', 'system', 9, ARRAY['context', 'memory', 'conversation']),
('AI_ASSISTANT', 'SOPHIA', 'When providing code solutions, always include error handling and consider edge cases. Explain the reasoning behind architectural decisions.', 'system', 8, ARRAY['code_quality', 'architecture', 'best_practices']),
('ORGANIZATION', 'Pay Ready', 'Security and data privacy are non-negotiable. All systems must be designed with security-first principles.', 'system', 10, ARRAY['security', 'privacy', 'compliance']),
('ORGANIZATION', 'Pay Ready', 'Prefer Infrastructure as Code (IaC) approaches for all deployments and system management.', 'system', 9, ARRAY['infrastructure', 'automation', 'deployment']);

-- Create a view for active principles
CREATE VIEW active_canonical_principles AS
SELECT * FROM canonical_principles 
WHERE status = 'active' 
ORDER BY importance_score DESC, created_at DESC;

COMMENT ON TABLE canonical_principles IS 'Stores canonical principles and truths for the Primary Mentor system';
COMMENT ON COLUMN canonical_principles.entity_type IS 'Type of entity (AI_ASSISTANT, ORGANIZATION, PROJECT, etc.)';
COMMENT ON COLUMN canonical_principles.entity_name IS 'Specific name of the entity (SOPHIA, Pay Ready, etc.)';
COMMENT ON COLUMN canonical_principles.principle_text IS 'The actual principle or truth statement';
COMMENT ON COLUMN canonical_principles.source_interaction_id IS 'ID of the interaction that generated this principle';
COMMENT ON COLUMN canonical_principles.importance_score IS 'Importance score from 1-10, with 10 being most critical';
COMMENT ON COLUMN canonical_principles.notion_page_id IS 'Reference to corresponding Notion page for governance';
COMMENT ON COLUMN canonical_principles.embedding_id IS 'Reference to vector embedding in Qdrant';

