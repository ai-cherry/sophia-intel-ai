#!/usr/bin/env python3
"""
Local Database Setup Script for SOPHIA Intel
Sets up local PostgreSQL database for development and testing
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime
from dotenv import load_dotenv

def load_environment():
    """Load environment variables"""
    env_files = ['.env.advanced_rag', '.env.production', '.env.neon']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
    
    return True

def setup_local_postgresql():
    """Setup local PostgreSQL database"""
    print("🔧 Setting up local PostgreSQL database...")
    
    try:
        # Check if PostgreSQL is installed
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if result.returncode != 0:
            print("📦 Installing PostgreSQL...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'postgresql', 'postgresql-contrib'], check=True)
            print("✅ PostgreSQL installed")
        else:
            print("✅ PostgreSQL already installed")
        
        # Start PostgreSQL service
        subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'postgresql'], check=True)
        print("✅ PostgreSQL service started")
        
        # Create database and user
        db_name = "sophia_intel"
        db_user = "sophia_user"
        db_password = "sophia_password_2025"
        
        # Create user and database
        create_user_cmd = f"sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\""
        create_db_cmd = f"sudo -u postgres psql -c \"CREATE DATABASE {db_name} OWNER {db_user};\""
        grant_cmd = f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};\""
        
        # Execute commands (ignore errors if user/db already exists)
        subprocess.run(create_user_cmd, shell=True, capture_output=True)
        subprocess.run(create_db_cmd, shell=True, capture_output=True)
        subprocess.run(grant_cmd, shell=True, capture_output=True)
        
        # Set database URL
        database_url = f"postgresql://{db_user}:{db_password}@localhost:5432/{db_name}"
        os.environ['DATABASE_URL'] = database_url
        
        # Write to environment file
        with open('.env.local', 'w') as f:
            f.write(f"# Local Development Database Configuration\n")
            f.write(f"# Generated: {datetime.utcnow().isoformat()}\n\n")
            f.write(f"DATABASE_URL={database_url}\n")
            f.write(f"POSTGRES_HOST=localhost\n")
            f.write(f"POSTGRES_PORT=5432\n")
            f.write(f"POSTGRES_DB={db_name}\n")
            f.write(f"POSTGRES_USER={db_user}\n")
            f.write(f"POSTGRES_PASSWORD={db_password}\n")
            f.write(f"\n# Redis Configuration\n")
            f.write(f"REDIS_HOST=localhost\n")
            f.write(f"REDIS_PORT=6379\n")
            f.write(f"REDIS_DB=0\n")
        
        print(f"✅ Local database configured: {db_name}")
        print(f"✅ Database URL: {database_url}")
        
        return database_url
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup PostgreSQL: {e}")
        return None
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return None

def setup_redis():
    """Setup Redis for caching"""
    print("🔧 Setting up Redis...")
    
    try:
        # Check if Redis is installed
        result = subprocess.run(['which', 'redis-server'], capture_output=True, text=True)
        if result.returncode != 0:
            print("📦 Installing Redis...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'redis-server'], check=True)
            print("✅ Redis installed")
        else:
            print("✅ Redis already installed")
        
        # Start Redis service
        subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'redis-server'], check=True)
        print("✅ Redis service started")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Redis setup failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Redis setup error: {e}")
        return False

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
        import traceback
        traceback.print_exc()
        return False

async def test_full_system():
    """Test the full system integration"""
    print("🧪 Testing full system integration...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from database.unified_knowledge_repository import get_knowledge_repository, KnowledgeContext
        from core.sophia_orchestrator_enhanced import get_sophia_orchestrator, initialize_sophia_orchestrator
        
        # Test knowledge repository
        repo = get_knowledge_repository()
        
        test_entity = {
            "name": "Pay Ready Revenue Growth",
            "type": "business_metric",
            "description": "Monthly revenue growth rate for Pay Ready payment processing",
            "confidence": 0.95,
            "data_sources": ["salesforce", "netsuite"],
            "ui_display_priority": 10
        }
        
        test_context = KnowledgeContext(
            user_id="system_test",
            session_id="system_test_session",
            business_domain="pay_ready",
            chat_flags={
                "deep_payready_context": True,
                "enable_learning": True
            },
            ui_context={
                "user_role": "ceo",
                "current_priority": "revenue_analysis"
            }
        )
        
        entity_id = await repo.store_business_entity(test_entity, test_context)
        print(f"✅ Stored test entity: {entity_id}")
        
        # Test SOPHIA orchestrator
        await initialize_sophia_orchestrator()
        orchestrator = get_sophia_orchestrator()
        
        test_query = "What can you tell me about Pay Ready's revenue growth?"
        response = await orchestrator.process_business_query(test_query, test_context)
        
        print(f"✅ SOPHIA response generated:")
        print(f"   Length: {len(response.get('response', ''))}")
        print(f"   System: {response.get('rag_metrics', {}).get('system_used', 'unknown')}")
        print(f"   Confidence: {response.get('rag_metrics', {}).get('confidence_score', 0.0)}")
        
        return True
    
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_startup_script():
    """Create startup script for development"""
    startup_script = """#!/bin/bash
# SOPHIA Intel Development Startup Script

echo "🚀 Starting SOPHIA Intel Development Environment"

# Start PostgreSQL
sudo systemctl start postgresql
echo "✅ PostgreSQL started"

# Start Redis
sudo systemctl start redis-server
echo "✅ Redis started"

# Load environment
export $(cat .env.local | xargs)
echo "✅ Environment loaded"

echo "🎉 SOPHIA Intel development environment ready!"
echo "Database URL: $DATABASE_URL"
echo "Redis: localhost:6379"
"""
    
    with open('start_dev.sh', 'w') as f:
        f.write(startup_script)
    
    os.chmod('start_dev.sh', 0o755)
    print("✅ Created startup script: start_dev.sh")

async def main():
    """Main setup function"""
    print("🚀 SOPHIA Intel Local Database Setup")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Setup PostgreSQL
    database_url = setup_local_postgresql()
    if not database_url:
        print("❌ Failed to setup PostgreSQL")
        return 1
    
    # Setup Redis
    redis_success = setup_redis()
    if not redis_success:
        print("⚠️  Redis setup failed, caching will be disabled")
    
    # Load local environment
    load_dotenv('.env.local')
    
    # Initialize schema
    schema_success = await initialize_database_schema()
    if not schema_success:
        print("❌ Failed to initialize schema")
        return 1
    
    # Test full system
    test_success = await test_full_system()
    if not test_success:
        print("❌ System test failed")
        return 1
    
    # Create startup script
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("✅ SOPHIA Intel Local Setup Complete!")
    print("=" * 50)
    print(f"Database: {database_url}")
    print(f"Redis: localhost:6379 ({'✅ Active' if redis_success else '❌ Inactive'})")
    print("Configuration: .env.local")
    print("Startup: ./start_dev.sh")
    print("\n🎯 Ready for Phase 2: Advanced RAG Integration!")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

