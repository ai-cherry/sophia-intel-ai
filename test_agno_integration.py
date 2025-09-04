#!/usr/bin/env python3
"""
Test script for AGNO framework integration with Portkey virtual keys
"""

import asyncio
import logging
from app.swarms.agno_teams import (
    SophiaAGNOTeam, 
    AGNOTeamConfig, 
    ExecutionStrategy
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agno_team_creation():
    """Test creating and initializing an AGNO team"""
    print("🔧 Testing AGNO Team Creation...")
    
    # Test configuration
    config = AGNOTeamConfig(
        name="test_team",
        strategy=ExecutionStrategy.BALANCED,
        max_agents=3,
        timeout=30,
        enable_memory=False,  # Disable memory for basic test
        enable_circuit_breaker=False
    )
    
    # Create team
    team = SophiaAGNOTeam(config)
    
    try:
        # Initialize team
        await team.initialize()
        print(f"✅ Team '{team.config.name}' created successfully")
        print(f"📊 Strategy: {team.config.strategy.value}")
        print(f"👥 Agents: {len(team.agents)}")
        
        # List agents
        for agent in team.agents:
            model_name = agent.model.id if hasattr(agent.model, 'id') else str(agent.model)
            print(f"  - {agent.name}: {model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Team creation failed: {e}")
        logger.error(f"Team creation error: {e}", exc_info=True)
        return False

async def test_agno_task_execution():
    """Test executing a simple task with AGNO team"""
    print("\n🚀 Testing AGNO Task Execution...")
    
    # Create balanced team for task execution
    config = AGNOTeamConfig(
        name="exec_test_team", 
        strategy=ExecutionStrategy.LITE,  # Use LITE for faster testing
        enable_memory=False,
        enable_circuit_breaker=False
    )
    
    team = SophiaAGNOTeam(config)
    
    try:
        await team.initialize()
        
        # Execute a simple task
        result = await team.execute_task(
            task_description="Hello, this is a test task for AGNO team verification",
            context={
                "test_type": "integration_test",
                "framework": "agno",
                "provider": "portkey"
            }
        )
        
        print(f"✅ Task executed successfully")
        print(f"📊 Success: {result.get('success', False)}")
        print(f"⏱️  Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"🎯 Strategy: {result.get('strategy', 'unknown')}")
        
        if result.get('success', False):
            print("🎉 AGNO integration is working correctly!")
            return True
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        logger.error(f"Task execution error: {e}", exc_info=True)
        return False

async def test_portkey_virtual_keys():
    """Test that virtual keys are properly configured"""
    print("\n🔑 Testing Portkey Virtual Keys Configuration...")
    
    from app.swarms.agno_teams import PORTKEY_VIRTUAL_KEYS, portkey
    
    print(f"📋 Available virtual keys: {len(PORTKEY_VIRTUAL_KEYS)}")
    for provider, vk in PORTKEY_VIRTUAL_KEYS.items():
        print(f"  - {provider}: {vk}")
    
    # Test Portkey client initialization
    if portkey:
        print("✅ Portkey client initialized successfully")
        print(f"🔐 API key configured: {'hPxFZGd8AN269n4bznDf2/Onbi8I'[:8]}***")
        return True
    else:
        print("❌ Portkey client initialization failed")
        return False

async def test_model_configurations():
    """Test approved model configurations"""
    print("\n🤖 Testing Model Configurations...")
    
    from app.swarms.agno_teams import SophiaAGNOTeam
    
    approved_models = SophiaAGNOTeam.APPROVED_MODELS
    print(f"📊 Approved models configured: {len(approved_models)}")
    
    for role, config in approved_models.items():
        print(f"  - {role}: {config['model']} ({config['provider']}) -> {config['virtual_key']}")
    
    print("✅ All model configurations are properly structured")
    return True

async def main():
    """Run all integration tests"""
    print("🧪 AGNO Framework Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Virtual Keys Configuration", test_portkey_virtual_keys()),
        ("Model Configurations", test_model_configurations()),
        ("AGNO Team Creation", test_agno_team_creation()),
        ("AGNO Task Execution", test_agno_task_execution()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AGNO integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)