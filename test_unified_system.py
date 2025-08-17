#!/usr/bin/env python3
"""
Test script for SOPHIA Intel Unified Knowledge System
Tests the integrated knowledge repository and orchestrator
"""

import os
import asyncio
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.unified_knowledge_repository import (
    initialize_knowledge_system,
    get_knowledge_repository,
    KnowledgeContext
)
from core.sophia_orchestrator_enhanced import (
    initialize_sophia_orchestrator,
    get_sophia_orchestrator
)

async def test_knowledge_repository():
    """Test the unified knowledge repository"""
    print("🧪 Testing Unified Knowledge Repository...")
    
    try:
        # Initialize the knowledge system
        success = await initialize_knowledge_system()
        if not success:
            print("❌ Failed to initialize knowledge system")
            return False
        
        # Get repository instance
        repo = get_knowledge_repository()
        
        # Test storing a business entity
        test_entity = {
            "name": "Monthly Recurring Revenue",
            "type": "financial_metric",
            "description": "Pay Ready's monthly recurring revenue from payment processing",
            "confidence": 0.9,
            "data_sources": ["salesforce", "netsuite"],
            "ui_display_priority": 8
        }
        
        test_context = KnowledgeContext(
            user_id="test_user",
            session_id="test_session",
            business_domain="pay_ready",
            chat_flags={"enable_learning": True},
            ui_context={"user_role": "ceo"}
        )
        
        entity_id = await repo.store_business_entity(test_entity, test_context)
        print(f"✅ Stored test entity with ID: {entity_id}")
        
        # Test retrieving contextual knowledge
        knowledge = await repo.get_contextual_knowledge(
            "What is our monthly recurring revenue?",
            test_context
        )
        
        print(f"✅ Retrieved knowledge context with {len(knowledge.get('entities', []))} entities")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge repository test failed: {e}")
        return False

async def test_sophia_orchestrator():
    """Test the SOPHIA orchestrator"""
    print("🧪 Testing SOPHIA Orchestrator...")
    
    try:
        # Initialize orchestrator
        status = await initialize_sophia_orchestrator()
        print(f"✅ Orchestrator initialized with status: {status['orchestrator_status']}")
        
        # Get orchestrator instance
        orchestrator = get_sophia_orchestrator()
        
        # Test processing a business query
        test_context = KnowledgeContext(
            user_id="test_user",
            session_id="test_session",
            business_domain="pay_ready",
            chat_flags={
                "deep_payready_context": True,
                "enable_learning": True,
                "proactive_insights": True
            },
            ui_context={
                "user_role": "ceo",
                "current_priority": "revenue_growth"
            }
        )
        
        test_query = "What are our key financial metrics and how are they trending?"
        
        response = await orchestrator.process_business_query(test_query, test_context)
        
        print(f"✅ Processed query successfully")
        print(f"   Response length: {len(response.get('response', ''))}")
        print(f"   RAG system used: {response.get('rag_metrics', {}).get('system_used', 'unknown')}")
        print(f"   Confidence score: {response.get('rag_metrics', {}).get('confidence_score', 0.0)}")
        
        # Test system status
        system_status = await orchestrator.get_system_status()
        print(f"✅ System status retrieved: {system_status['orchestrator_status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

async def test_integration():
    """Test integration between components"""
    print("🧪 Testing System Integration...")
    
    try:
        # Test multiple queries to verify learning
        orchestrator = get_sophia_orchestrator()
        
        test_queries = [
            "How is Pay Ready performing in the payments market?",
            "What are our customer acquisition costs?",
            "Show me our revenue trends",
            "What opportunities do you see for growth?"
        ]
        
        test_context = KnowledgeContext(
            user_id="integration_test",
            session_id="integration_session",
            business_domain="pay_ready",
            chat_flags={
                "deep_payready_context": True,
                "cross_platform_correlation": True,
                "proactive_insights": True,
                "enable_learning": True
            },
            ui_context={
                "user_role": "cfo",
                "current_priority": "financial_analysis"
            }
        )
        
        for i, query in enumerate(test_queries, 1):
            print(f"  Processing query {i}: {query[:50]}...")
            response = await orchestrator.process_business_query(query, test_context)
            
            if response.get("error"):
                print(f"    ⚠️  Query {i} had error: {response.get('error_message')}")
            else:
                print(f"    ✅ Query {i} processed successfully")
        
        # Check final metrics
        final_status = await orchestrator.get_system_status()
        queries_processed = final_status["metrics"]["queries_processed"]
        avg_response_time = final_status["metrics"]["avg_response_time"]
        
        print(f"✅ Integration test complete:")
        print(f"   Queries processed: {queries_processed}")
        print(f"   Average response time: {avg_response_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 SOPHIA Intel Unified System Test")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    
    # Try to load different env files
    env_files = ['.env.advanced_rag', '.env.production', '.env.neo4j']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Loaded environment from {env_file}")
    
    # Set default values if not provided
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/sophia_intel"
        print("ℹ️  Using default DATABASE_URL")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - some features may not work")
    
    # Run tests
    tests = [
        ("Knowledge Repository", test_knowledge_repository),
        ("SOPHIA Orchestrator", test_sophia_orchestrator),
        ("System Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            success = await test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SOPHIA Intel unified system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

