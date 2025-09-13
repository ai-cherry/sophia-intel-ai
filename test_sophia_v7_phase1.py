#!/usr/bin/env python3
"""
Sophia AI V7 Phase 1 Comprehensive Test Suite
Tests Agno integration, unified memory, MCP framework, and contextual RBAC
"""
import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict
from core.memory.unified_memory import UnifiedMemoryManager
from core.shared_services.auth.contextual_rbac import ContextualRBACEngine
from core.shared_services.mcp_framework.agno_mcp_coordinator import MCPFramework
from core.sophia.orchestration.sophia_brain import SophiaBrain
from core.sophia.routing.claude_mal_router import ClaudeMALRouter
class SophiaV7TestSuite:
    """Comprehensive test suite for Sophia V7 Phase 1"""
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 1 tests"""
        print("🚀 Starting Sophia AI V7 Phase 1 Test Suite")
        print("=" * 60)
        tests = [
            ("Claude MAL Router", self.test_claude_mal_router),
            ("Unified Memory System", self.test_unified_memory),
            ("MCP Framework", self.test_mcp_framework),
            ("Contextual RBAC", self.test_contextual_rbac),
            ("Sophia Brain Integration", self.test_sophia_brain),
        ]
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 40)
            try:
                result = await test_func()
                self.test_results[test_name] = {"status": "PASSED", "result": result}
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                error_details = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat(),
                }
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": error_details,
                }
                print(f"❌ {test_name}: FAILED - {str(e)}")
        # Generate final report
        return self.generate_test_report()
    async def test_claude_mal_router(self) -> Dict[str, Any]:
        """Test Claude MAL router functionality"""
        config = {
            "portkey_api_key": "test-key",
            "portkey_base_url": "https://api.portkey.ai/v1",
        }
        router = ClaudeMALRouter(config)
        # Test model selection
        decision = await router.select_model_with_mal(
            query="Analyze sales performance data",
            domain="gong",
            context={"urgency": "high"},
        )
        assert decision.selected_model is not None
        assert decision.confidence_score > 0
        assert len(decision.fallback_models) > 0
        # Test analytics
        analytics = await router.get_routing_analytics()
        return {
            "selected_model": decision.selected_model,
            "confidence": decision.confidence_score,
            "reasoning": decision.reasoning,
            "analytics": analytics,
        }
    async def test_unified_memory(self) -> Dict[str, Any]:
        """Test unified memory system"""
        config = {
            "qdrant": {"host": "localhost", "port": 6333},
            "postgres": {"host": "localhost", "database": "sophia_test"},
            "redis": {"host": "localhost", "port": 6379},
            "neo4j": {"url": "bolt://localhost:7687"},
            "zep": {"api_url": "http://localhost:8000"},
            "mem0": {"api_key": "test-key"},
        }
        memory_manager = UnifiedMemoryManager(config)
        # Test storage
        success = await memory_manager.store_interaction(
            query="Test query for memory system",
            response="Test response from memory system",
            domain="test",
            user_id="test_user",
            metadata={"test": True},
        )
        assert success, "Memory storage failed"
        # Test hybrid query
        results = await memory_manager.hybrid_query(
            query="test query", domain="test", user_id="test_user", multimodal=False
        )
        # Test memory stats
        stats = await memory_manager.get_memory_stats()
        return {
            "storage_success": success,
            "query_results_count": len(results),
            "memory_stats": stats,
            "drivers_initialized": len(memory_manager.drivers),
        }
    async def test_mcp_framework(self) -> Dict[str, Any]:
        """Test MCP framework with Agno coordination"""
        config = {
            "security": {"jwt_secret": "test-secret"},
            "agno": {"model_config": {"default_model": "claude-3-5-sonnet"}},
        }
        framework = MCPFramework(config)
        # Test workflow status
        status = await framework.get_workflow_status("test_workflow")
        # Test ETL trigger creation
        trigger_id = await framework.create_estuary_trigger(
            {"source": "test", "destination": "test"}
        )
        return {
            "framework_initialized": True,
            "workflow_status": status,
            "etl_trigger_id": trigger_id,
            "security_manager": framework.security_manager is not None,
            "workflow_coordinator": framework.workflow_coordinator is not None,
        }
    async def test_contextual_rbac(self) -> Dict[str, Any]:
        """Test contextual RBAC engine"""
        config = {}
        rbac_engine = ContextualRBACEngine(config)
        # Test permission check
        context = {
            "ip_address": "192.168.1.100",
            "device_id": "test_device",
            "location": {"country": "US"},
            "risk_score": 0.2,
            "business_context": {"is_business_hours": True, "department": "sales"},
            "additional_attributes": {"device_trust_level": 0.8, "mfa_verified": True},
        }
        result = await rbac_engine.check_contextual_permission(
            user_id="test_user",
            resource="sophia:test:resource",
            action="read",
            context=context,
        )
        # Test audit log
        audit_log = await rbac_engine.get_audit_log(limit=10)
        return {
            "permission_decision": result.decision.value,
            "confidence_score": result.confidence_score,
            "explanation": result.explanation,
            "matched_rules_count": len(result.matched_rules),
            "audit_log_entries": len(audit_log),
            "policies_loaded": len(rbac_engine.policies),
        }
    async def test_sophia_brain(self) -> Dict[str, Any]:
        """Test Sophia Brain integration"""
        config = {
            "memory": {
                "qdrant": {"host": "localhost", "port": 6333},
                "postgres": {"host": "localhost", "database": "sophia_test"},
                "redis": {"host": "localhost", "port": 6379},
                "neo4j": {"url": "bolt://localhost:7687"},
                "zep": {"api_url": "http://localhost:8000"},
            },
            "routing": {
                "default_model": "claude-3-5-sonnet",
                "fallback_model": "gpt-4o-mini",
            },
            "auth": {"cerbos_endpoint": "http://localhost:3593"},
            "portkey": {"api_key": "test-key", "base_url": "https://api.portkey.ai/v1"},
        }
        brain = SophiaBrain(config)
        # Test domain configuration
        assert len(brain.domains) > 0
        assert "gong" in brain.domains
        assert "" in brain.domains
        # Test agent initialization
        assert len(brain.agents) > 0
        assert "sales_analyst" in brain.agents
        assert "dev_specialist" in brain.agents
        # Test team initialization
        assert len(brain.teams) > 0
        assert "sales_intelligence_team" in brain.teams
        assert "development_swarm" in brain.teams
        return {
            "brain_initialized": True,
            "domains_count": len(brain.domains),
            "agents_count": len(brain.agents),
            "teams_count": len(brain.teams),
            "memory_manager": brain.memory_manager is not None,
            "model_router": brain.model_router is not None,
            "rbac_engine": brain.rbac_engine is not None,
        }
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        passed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "PASSED"
        )
        total_tests = len(self.test_results)
        report = {
            "sophia_v7_phase1_test_report": {
                "timestamp": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (
                    (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                ),
                "test_results": self.test_results,
            }
        }
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 SOPHIA V7 PHASE 1 TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(
            f"📊 Tests: {passed_tests}/{total_tests} passed ({(passed_tests/total_tests)*100:.1f}%)"
        )
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Phase 1 implementation successful!")
        else:
            print("⚠️  Some tests failed. Check individual test results.")
        print("\n📋 Individual Test Results:")
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status_emoji} {test_name}: {result['status']}")
        return report
async def main():
    """Main test execution"""
    print("🧠 Sophia AI V7 Phase 1 - Agno Integration Test Suite")
    print(f"🕐 Started at: {datetime.now().isoformat()}")
    test_suite = SophiaV7TestSuite()
    try:
        report = await test_suite.run_all_tests()
        # Save test report
        with open("sophia_v7_phase1_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print("\n📄 Test report saved to: sophia_v7_phase1_test_report.json")
        # Return appropriate exit code
        success_rate = report["sophia_v7_phase1_test_report"]["success_rate"]
        if success_rate == 100:
            print("\n🚀 Phase 1 implementation COMPLETE and VERIFIED!")
            return 0
        else:
            print(
                f"\n⚠️  Phase 1 implementation has issues (success rate: {success_rate:.1f}%)"
            )
            return 1
    except Exception as e:
        print(f"\n💥 Test suite execution failed: {str(e)}")
        traceback.print_exc()
        return 1
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
