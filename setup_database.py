#!/usr/bin/env python3
"""
Database Setup Script for SOPHIA Intel
Configures Neon PostgreSQL database and initializes schema
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from multiple sources"""
    env_files = ['.env.neon', '.env.advanced_rag', '.env.production']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
    
    # Check required variables
    required_vars = ['NEON_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    return True

def setup_neon_database():
    """Setup Neon database using API"""
    print("🔧 Setting up Neon PostgreSQL database...")
    
    api_token = os.getenv('NEON_API_TOKEN')
    if not api_token:
        print("❌ NEON_API_TOKEN not found")
        return None
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get projects
        response = requests.get('https://console.neon.tech/api/v2/projects', headers=headers)
        
        if response.status_code == 200:
            projects = response.json()['projects']
            print(f"✅ Found {len(projects)} Neon projects")
            
            # Use first project or create new one
            if projects:
                project = projects[0]
                project_id = project['id']
                print(f"✅ Using existing project: {project['name']} ({project_id})")
            else:
                # Create new project
                project_data = {
                    'project': {
                        'name': 'sophia-intel',
                        'region_id': 'aws-us-east-1'
                    }
                }
                
                response = requests.post(
                    'https://console.neon.tech/api/v2/projects',
                    headers=headers,
                    json=project_data
                )
                
                if response.status_code == 201:
                    project = response.json()['project']
                    project_id = project['id']
                    print(f"✅ Created new project: {project['name']} ({project_id})")
                else:
                    print(f"❌ Failed to create project: {response.text}")
                    return None
            
            # Get database connection string
            db_response = requests.get(
                f'https://console.neon.tech/api/v2/projects/{project_id}/connection_uri',
                headers=headers
            )
            
            if db_response.status_code == 200:
                connection_uri = db_response.json()['uri']
                print("✅ Retrieved database connection URI")
                
                # Update environment with database URL
                os.environ['DATABASE_URL'] = connection_uri
                os.environ['NEON_PROJECT_ID'] = project_id
                
                # Write to .env.neon file
                with open('.env.neon', 'a') as f:
                    f.write(f"\n# Auto-generated database connection\n")
                    f.write(f"NEON_PROJECT_ID={project_id}\n")
                    f.write(f"DATABASE_URL={connection_uri}\n")
                
                return connection_uri
            else:
                print(f"❌ Failed to get connection URI: {db_response.text}")
                return None
        
        else:
            print(f"❌ Failed to get projects: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Neon API error: {e}")
        return None

async def initialize_database_schema():
    """Initialize database schema"""
    print("🔧 Initializing database schema...")
    
    try:
        # Add backend to path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from database.unified_knowledge_repository import initialize_knowledge_system
        
        success = await initialize_knowledge_system()
        
        if success:
            print("✅ Database schema initialized successfully")
            return True
        else:
            print("❌ Failed to initialize database schema")
            return False
    
    except Exception as e:
        print(f"❌ Schema initialization error: {e}")
        return False

async def test_database_connection():
    """Test database connection"""
    print("🧪 Testing database connection...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from database.unified_knowledge_repository import get_knowledge_repository, KnowledgeContext
        
        repo = get_knowledge_repository()
        
        # Test storing and retrieving data
        test_entity = {
            "name": "Database Test Entity",
            "type": "test",
            "description": "Test entity for database connection verification",
            "confidence": 1.0,
            "data_sources": ["test"]
        }
        
        test_context = KnowledgeContext(
            user_id="setup_test",
            session_id="setup_session",
            business_domain="test"
        )
        
        entity_id = await repo.store_business_entity(test_entity, test_context)
        print(f"✅ Successfully stored test entity: {entity_id}")
        
        # Test retrieval
        knowledge = await repo.get_contextual_knowledge("test", test_context)
        print(f"✅ Successfully retrieved knowledge context")
        
        return True
    
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def create_database_migration():
    """Create database migration script"""
    print("📝 Creating database migration script...")
    
    migration_sql = """
-- SOPHIA Intel Database Schema Migration
-- Generated: {}

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business entities table
CREATE TABLE IF NOT EXISTS business_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 0.7,
    data_sources TEXT[],
    embedding_id VARCHAR(255),
    llama_context TEXT,
    haystack_doc_id VARCHAR(255),
    graph_node_id VARCHAR(255),
    ui_display_priority INTEGER DEFAULT 5,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    domain VARCHAR(100) DEFAULT 'pay_ready'
);

-- Knowledge interactions table
CREATE TABLE IF NOT EXISTS knowledge_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    interaction_text TEXT NOT NULL,
    extracted_entities JSONB,
    rag_sources JSONB,
    chat_flags JSONB,
    ui_context JSONB,
    response_quality_score DECIMAL(3,2),
    user_feedback_score INTEGER,
    llama_model_used VARCHAR(100),
    haystack_pipeline_used VARCHAR(100),
    orchestrator_decisions JSONB,
    micro_agent_contributions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Context cache table
CREATE TABLE IF NOT EXISTS context_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    context_data JSONB NOT NULL,
    entity_ids UUID[],
    ttl_expires_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Background agent tasks table
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    task_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cross-platform correlations table
CREATE TABLE IF NOT EXISTS cross_platform_correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id UUID,
    target_entity_id UUID,
    correlation_type VARCHAR(100),
    correlation_strength DECIMAL(3,2),
    evidence_sources TEXT[],
    rag_evidence_docs JSONB,
    llama_analysis TEXT,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_business_entities_name ON business_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_business_entities_type ON business_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_business_entities_domain ON business_entities(domain);
CREATE INDEX IF NOT EXISTS idx_knowledge_interactions_session ON knowledge_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_interactions_user ON knowledge_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_key ON context_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_type ON agent_tasks(agent_type);

-- Insert initial Pay Ready business entities
INSERT INTO business_entities (entity_name, entity_type, description, confidence_score, data_sources, ui_display_priority, domain) VALUES
('Monthly Recurring Revenue', 'financial_metric', 'Pay Ready monthly recurring revenue from payment processing', 0.95, ARRAY['salesforce', 'netsuite'], 10, 'pay_ready'),
('Customer Acquisition Cost', 'financial_metric', 'Cost to acquire new customers for Pay Ready', 0.90, ARRAY['hubspot', 'salesforce'], 9, 'pay_ready'),
('Churn Rate', 'financial_metric', 'Monthly customer churn rate', 0.90, ARRAY['salesforce', 'intercom'], 9, 'pay_ready'),
('Payment Processing Volume', 'business_metric', 'Total volume of payments processed', 0.95, ARRAY['netsuite', 'internal_systems'], 10, 'pay_ready'),
('Merchant Onboarding', 'business_process', 'Process for onboarding new merchants', 0.85, ARRAY['salesforce', 'asana'], 7, 'pay_ready'),
('KYC Compliance', 'business_process', 'Know Your Customer compliance process', 0.90, ARRAY['compliance_system', 'salesforce'], 8, 'pay_ready'),
('API Integration', 'product_feature', 'Pay Ready payment API for merchants', 0.95, ARRAY['github', 'linear'], 8, 'pay_ready'),
('Dashboard Analytics', 'product_feature', 'Merchant dashboard for payment analytics', 0.85, ARRAY['looker', 'internal_systems'], 7, 'pay_ready')
ON CONFLICT (id) DO NOTHING;

COMMIT;
""".format(datetime.utcnow().isoformat())
    
    with open('database_migration.sql', 'w') as f:
        f.write(migration_sql)
    
    print("✅ Database migration script created: database_migration.sql")

async def main():
    """Main setup function"""
    print("🚀 SOPHIA Intel Database Setup")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        return 1
    
    # Setup Neon database
    connection_uri = setup_neon_database()
    if not connection_uri:
        print("❌ Failed to setup Neon database")
        return 1
    
    # Create migration script
    create_database_migration()
    
    # Initialize schema
    schema_success = await initialize_database_schema()
    if not schema_success:
        print("❌ Failed to initialize schema")
        return 1
    
    # Test connection
    test_success = await test_database_connection()
    if not test_success:
        print("❌ Database connection test failed")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ SOPHIA Intel Database Setup Complete!")
    print("=" * 50)
    print(f"Database URL: {connection_uri[:50]}...")
    print("Schema: Initialized with Pay Ready business entities")
    print("Status: Ready for SOPHIA orchestrator integration")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

