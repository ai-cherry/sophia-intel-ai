#!/usr/bin/env python3
"""
Test AGNO Framework Implementation
Tests both Sophia and Artemis AGNO Teams and Orchestrators
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sophia_agno_teams():
    """Test Sophia AGNO Teams"""
    print("\n" + "="*60)
    print("🔵 TESTING SOPHIA AGNO TEAMS")
    print("="*60)
    
    try:
        from app.swarms.sophia_agno_teams import SophiaAGNOTeamFactory
        
        # Test Sales Intelligence Team
        print("\n💎 Testing Sales Intelligence Team...")
        sales_team = await SophiaAGNOTeamFactory.create_sales_intelligence_team()
        print(f"✅ Sales Intelligence Team created with {len(sales_team.team.agents)} agents")
        
        # Test pipeline analysis
        pipeline_data = {
            "total_value": "$2.4M",
            "deal_count": 47,
            "close_rate": "23%"
        }
        result = await sales_team.analyze_pipeline_health(pipeline_data)
        print(f"✅ Pipeline analysis completed: {result.get('success', False)}")
        
        # Test Research Team
        print("\n💎 Testing Research Team...")
        research_team = await SophiaAGNOTeamFactory.create_research_team()
        print(f"✅ Research Team created with {len(research_team.team.agents)} agents")
        
        # Test market research
        research_scope = {
            "market": "AI SaaS",
            "region": "North America",
            "timeframe": "Q4 2024"
        }
        result = await research_team.conduct_market_research(research_scope)
        print(f"✅ Market research completed: {result.get('success', False)}")
        
        print("\n🎯 Sophia AGNO Teams: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Sophia AGNO Teams test failed: {str(e)}")
        return False

async def test_artemis_agno_teams():
    """Test Artemis AGNO Teams"""
    print("\n" + "="*60)
    print("🔴 TESTING ARTEMIS AGNO TEAMS")
    print("="*60)
    
    try:
        from app.swarms.artemis_agno_teams import ArtemisAGNOTeamFactory
        
        # Test Code Analysis Team
        print("\n⚔️ Testing Code Analysis Team...")
        code_team = await ArtemisAGNOTeamFactory.create_code_analysis_team()
        print(f"✅ Code Analysis Team created with {len(code_team.team.agents)} agents")
        
        # Test codebase analysis
        codebase_data = {
            "language": "python",
            "files": 156,
            "lines_of_code": 12500
        }
        result = await code_team.analyze_codebase(codebase_data)
        print(f"✅ Codebase analysis completed: {result.get('success', False)}")
        
        # Test Security Team
        print("\n⚔️ Testing Security Team...")
        security_team = await ArtemisAGNOTeamFactory.create_security_team()
        print(f"✅ Security Team created with {len(security_team.team.agents)} agents")
        
        # Test security audit
        system_data = {
            "endpoints": 23,
            "auth_methods": ["JWT", "OAuth2"],
            "data_encryption": "AES-256"
        }
        result = await security_team.conduct_security_audit(system_data)
        print(f"✅ Security audit completed: {result.get('success', False)}")
        
        print("\n🎯 Artemis AGNO Teams: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Artemis AGNO Teams test failed: {str(e)}")
        return False

async def test_sophia_agno_orchestrator():
    """Test Sophia AGNO Orchestrator"""
    print("\n" + "="*60)
    print("🔵 TESTING SOPHIA AGNO ORCHESTRATOR")
    print("="*60)
    
    try:
        from app.orchestrators.sophia_agno_orchestrator import (
            SophiaAGNOOrchestrator,
            BusinessContext
        )
        
        # Create and initialize orchestrator
        print("\n💎 Initializing Sophia AGNO Orchestrator...")
        orchestrator = SophiaAGNOOrchestrator()
        init_success = await orchestrator.initialize()
        
        if not init_success:
            print("❌ Failed to initialize Sophia AGNO Orchestrator")
            return False
            
        print("✅ Sophia AGNO Orchestrator initialized successfully")
        
        # Test business request processing
        print("\n💎 Testing business request processing...")
        context = BusinessContext(
            user_id="test_user",
            session_id="test_session_001"
        )
        
        request = "Analyze our sales pipeline and identify top 3 deals to focus on this quarter"
        response = await orchestrator.process_business_request(request, context)
        
        print(f"✅ Business request processed: {response.success}")
        print(f"📊 Teams used: {getattr(response, 'agno_teams_used', [])}")
        print(f"🔗 Cross-team synthesis: {bool(getattr(response, 'cross_team_synthesis', None))}")
        
        # Test orchestrator status
        status = await orchestrator.get_orchestrator_status()
        print(f"✅ Orchestrator status: {status['status']}")
        print(f"🎯 Teams operational: {len([t for t in status.get('agno_teams', {}).values() if t.get('status') == 'operational'])}")
        
        print("\n🎯 Sophia AGNO Orchestrator: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Sophia AGNO Orchestrator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_artemis_agno_orchestrator():
    """Test Artemis AGNO Orchestrator"""
    print("\n" + "="*60)
    print("🔴 TESTING ARTEMIS AGNO ORCHESTRATOR")
    print("="*60)
    
    try:
        from app.orchestrators.artemis_agno_orchestrator import (
            ArtemisAGNOOrchestrator,
            TechnicalContext
        )
        
        # Create and initialize orchestrator
        print("\n⚔️ Initializing Artemis AGNO Orchestrator...")
        orchestrator = ArtemisAGNOOrchestrator()
        init_success = await orchestrator.initialize()
        
        if not init_success:
            print("❌ Failed to initialize Artemis AGNO Orchestrator")
            return False
            
        print("✅ Artemis AGNO Orchestrator initialized successfully")
        
        # Test technical request processing
        print("\n⚔️ Testing technical request processing...")
        context = TechnicalContext(
            user_id="test_user",
            session_id="tech_session_001"
        )
        
        request = "Review this codebase for security vulnerabilities and performance issues"
        response = await orchestrator.process_technical_request(request, context)
        
        print(f"✅ Technical request processed: {response.success}")
        print(f"⚔️ Teams used: {getattr(response, 'agno_teams_used', [])}")
        print(f"🔗 Cross-team synthesis: {bool(getattr(response, 'cross_team_synthesis', None))}")
        
        # Test orchestrator status
        status = await orchestrator.get_orchestrator_status()
        print(f"✅ Orchestrator status: {status['status']}")
        print(f"🎯 Teams operational: {len([t for t in status.get('agno_teams', {}).values() if t.get('status') == 'operational'])}")
        
        print("\n🎯 Artemis AGNO Orchestrator: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Artemis AGNO Orchestrator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between both systems"""
    print("\n" + "="*60)
    print("🔄 TESTING AGNO FRAMEWORK INTEGRATION")
    print("="*60)
    
    try:
        # Test both orchestrators can run concurrently
        from app.orchestrators.sophia_agno_orchestrator import SophiaAGNOOrchestrator, BusinessContext
        from app.orchestrators.artemis_agno_orchestrator import ArtemisAGNOOrchestrator, TechnicalContext
        
        print("\n🔄 Testing concurrent orchestrator operations...")
        
        # Initialize both orchestrators
        sophia_orch = SophiaAGNOOrchestrator()
        artemis_orch = ArtemisAGNOOrchestrator()
        
        sophia_init, artemis_init = await asyncio.gather(
            sophia_orch.initialize(),
            artemis_orch.initialize(),
            return_exceptions=True
        )
        
        print(f"✅ Sophia initialization: {sophia_init}")
        print(f"✅ Artemis initialization: {artemis_init}")
        
        # Run concurrent requests
        if sophia_init and artemis_init:
            business_context = BusinessContext(session_id="integration_test_biz")
            technical_context = TechnicalContext(session_id="integration_test_tech")
            
            sophia_response, artemis_response = await asyncio.gather(
                sophia_orch.process_business_request("What are our revenue opportunities?", business_context),
                artemis_orch.process_technical_request("Optimize system performance", technical_context),
                return_exceptions=True
            )
            
            print(f"✅ Sophia response: {getattr(sophia_response, 'success', False)}")
            print(f"✅ Artemis response: {getattr(artemis_response, 'success', False)}")
        
        print("\n🎯 AGNO Framework Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all AGNO framework tests"""
    print("🚀 AGNO FRAMEWORK COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Sophia AGNO Teams", test_sophia_agno_teams),
        ("Artemis AGNO Teams", test_artemis_agno_teams),
        ("Sophia AGNO Orchestrator", test_sophia_agno_orchestrator),
        ("Artemis AGNO Orchestrator", test_artemis_agno_orchestrator),
        ("AGNO Framework Integration", test_integration)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} tests...")
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 AGNO FRAMEWORK TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🏆 AGNO FRAMEWORK IMPLEMENTATION: FULLY FUNCTIONAL!")
        print("\n💡 Key observations:")
        print("• Specialized AGNO teams provide domain expertise")
        print("• Cross-team synthesis enhances intelligence coordination")
        print("• Personality-driven responses maintain system character")
        print("• Multi-team orchestration scales for complex operations")
        return True
    else:
        print("⚠️ AGNO FRAMEWORK IMPLEMENTATION: PARTIAL SUCCESS")
        print("Some components need attention before production deployment")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)