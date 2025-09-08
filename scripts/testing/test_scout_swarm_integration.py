#!/usr/bin/env python3
"""
Test Script for Ultimate Scout Swarm and Factory Integration
Tests MCP connectivity, scout swarm execution, and base factory functionality
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scout swarm
from app.artemis.scout_swarm.ultimate_scout_swarm import (
    ArtemisScoutSwarmIntegration,
    UltimateScoutSwarm,
)

# Import base factory
from app.core.base_factory import create_base_factory

# Test MCP connectivity
try:
    from app.tools.basic_tools import list_directory, read_file, search_code

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  MCP tools not available - will test with limited functionality")

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================================================================
# TEST CONFIGURATION
# ==============================================================================

TEST_REPO = "/Users/lynnmusil/sophia-intel-ai"
TEST_TARGETS = [
    "app/artemis/scout_swarm/ultimate_scout_swarm.py",
    "app/core/base_factory.py",
    "app/sophia/agent_factory.py",
    "app/artemis/agent_factory.py",
]

# ==============================================================================
# MCP CONNECTION TESTS
# ==============================================================================


async def test_mcp_connectivity():
    """
    Test MCP server connectivity
    """
    print("\n" + "=" * 70)
    print("🔌 TESTING MCP SERVER CONNECTIVITY")
    print("=" * 70)

    results = {}

    # Test simple server health
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                health_data = response.json()
                results["simple_server"] = {"status": "connected", "health": health_data}
                print("✅ Simple Test Server: CONNECTED")
                print(f"   Health: {json.dumps(health_data, indent=2)}")
            else:
                results["simple_server"] = {"status": "error", "code": response.status_code}
                print("❌ Simple Test Server: ERROR")
    except Exception as e:
        results["simple_server"] = {"status": "failed", "error": str(e)}
        print(f"❌ Simple Test Server: {e}")

    # Test Redis connectivity
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        results["redis"] = {"status": "connected"}
        print("✅ Redis: CONNECTED")
    except Exception as e:
        results["redis"] = {"status": "failed", "error": str(e)}
        print(f"❌ Redis: {e}")

    # Test MCP tools if available
    if MCP_AVAILABLE:
        try:
            # Test file reading
            test_file = os.path.join(TEST_REPO, "README.md")
            if os.path.exists(test_file):
                content = read_file(test_file)
                results["mcp_tools"] = {"status": "functional", "test_read": "success"}
                print("✅ MCP Tools: FUNCTIONAL")
            else:
                results["mcp_tools"] = {"status": "partial"}
                print("⚠️  MCP Tools: PARTIAL")
        except Exception as e:
            results["mcp_tools"] = {"status": "error", "error": str(e)}
            print(f"❌ MCP Tools: {e}")
    else:
        results["mcp_tools"] = {"status": "not_available"}
        print("⚠️  MCP Tools: NOT AVAILABLE")

    return results


# ==============================================================================
# SCOUT SWARM TESTS
# ==============================================================================


async def test_scout_swarm_creation():
    """
    Test scout swarm initialization
    """
    print("\n" + "=" * 70)
    print("🤖 TESTING SCOUT SWARM CREATION")
    print("=" * 70)

    try:
        # Create swarm
        swarm = UltimateScoutSwarm(use_mcp=MCP_AVAILABLE)

        # Check scouts
        scout_count = sum(len(scouts) for scouts in swarm.scouts.values())
        print(f"✅ Scout Swarm Created: {scout_count} scouts")

        # Display scout configuration
        for tier, scouts in swarm.scouts.items():
            print(f"\n  {tier.value.upper()} Tier:")
            for scout in scouts:
                print(f"    • {scout.config.name}")
                print(f"      Model: {scout.config.model}")
                print(f"      Provider: {scout.config.provider}")
                print(
                    f"      Expected Time: {scout.config.performance_metrics.get('expected_time', 'N/A')}s"
                )
                print(
                    f"      Quality Score: {scout.config.performance_metrics.get('quality_score', 'N/A')}%"
                )

        return {"success": True, "scout_count": scout_count, "swarm": swarm}

    except Exception as e:
        print(f"❌ Scout Swarm Creation Failed: {e}")
        return {"success": False, "error": str(e)}


async def test_rapid_scan(swarm: UltimateScoutSwarm):
    """
    Test Tier 1 rapid scanning
    """
    print("\n" + "=" * 70)
    print("🏃 TESTING TIER 1: RAPID SCAN")
    print("=" * 70)

    try:
        start_time = time.time()

        # Execute rapid scan only
        report = await swarm.execute_tiered_scan(TEST_REPO, scan_depth="rapid", include_audit=False)

        execution_time = time.time() - start_time

        print(f"✅ Rapid Scan Completed in {execution_time:.2f}s")
        print(f"  Scan ID: {report.scan_id}")
        print(f"  Total Findings: {report.statistics['total_findings']}")
        print(f"  Critical Issues: {report.statistics['critical_issues']}")
        print(f"  Scouts Used: {report.statistics['total_scouts_used']}")
        print(f"  Total Tokens: {report.statistics['total_tokens']}")

        # Display top findings
        if report.critical_findings:
            print("\n  Top Critical Findings:")
            for i, finding in enumerate(report.critical_findings[:3], 1):
                print(f"    {i}. {finding.get('finding', {}).get('issue', 'Unknown')}")
                print(f"       Scout: {finding.get('scout', 'Unknown')}")

        return {"success": True, "report": report, "execution_time": execution_time}

    except Exception as e:
        print(f"❌ Rapid Scan Failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_custom_scan(swarm: UltimateScoutSwarm):
    """
    Test custom scan with specific scouts
    """
    print("\n" + "=" * 70)
    print("🎯 TESTING CUSTOM SCAN")
    print("=" * 70)

    try:
        # Use only fast scouts
        scouts_to_use = ["Llama-4-Scout", "GPT-4o-mini"]

        print(f"  Using scouts: {', '.join(scouts_to_use)}")

        report = await swarm.execute_custom_scan(
            TEST_REPO,
            scouts_to_use,
            custom_prompt="Focus on finding exposed API keys and security vulnerabilities",
        )

        print("✅ Custom Scan Completed")
        print(f"  Scan ID: {report.scan_id}")
        print(f"  Execution Time: {report.total_execution_time:.2f}s")
        print(f"  Findings: {report.statistics['total_findings']}")

        return {"success": True, "report": report}

    except Exception as e:
        print(f"❌ Custom Scan Failed: {e}")
        return {"success": False, "error": str(e)}


# ==============================================================================
# BASE FACTORY TESTS
# ==============================================================================


async def test_base_factory():
    """
    Test base factory creation and initialization
    """
    print("\n" + "=" * 70)
    print("🏭 TESTING BASE FACTORY")
    print("=" * 70)

    try:
        # Create Artemis factory
        artemis_factory = create_base_factory("artemis")
        print(f"✅ Artemis Factory Created: {artemis_factory.factory_id}")

        # Initialize factory
        init_results = await artemis_factory.initialize()
        print("✅ Factory Initialized")
        print(
            f"  MCP Connections: {sum(1 for v in init_results['mcp_connections'].values() if v)} / {len(init_results['mcp_connections'])}"
        )
        print(f"  Models Available: {init_results['models_available']}")

        # Create a test agent
        agent_id = await artemis_factory.create_agent(
            name="Scout Alpha",
            role="repository_scanner",
            model="llama-4-scout",
            capabilities=["code_analysis", "security_scanning"],
            tools=["read_file", "search_code"],
            personality={"tactical": True, "precision": "high"},
        )
        print(f"✅ Test Agent Created: {agent_id}")

        # Get factory status
        status = artemis_factory.get_factory_status()
        print("\n  Factory Status:")
        print(f"    Agents: {status['agents']['total']}")
        print(f"    Swarms: {status['swarms']['total']}")
        print(f"    Tasks Executed: {status['performance']['tasks_executed']}")
        print(f"    Model Usage Cost: ${status['model_usage']['total_cost']:.4f}")

        # Cleanup
        await artemis_factory.shutdown()

        return {"success": True, "factory": artemis_factory, "status": status}

    except Exception as e:
        print(f"❌ Base Factory Test Failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ==============================================================================
# ARTEMIS INTEGRATION TEST
# ==============================================================================


async def test_artemis_integration():
    """
    Test Artemis factory integration with scout swarm
    """
    print("\n" + "=" * 70)
    print("⚔️  TESTING ARTEMIS FACTORY INTEGRATION")
    print("=" * 70)

    try:
        # Create scout agent through Artemis integration
        agent_id = await ArtemisScoutSwarmIntegration.create_scout_agent("rapid")
        print(f"✅ Scout Agent Created: {agent_id}")

        # Execute tactical scan
        print("\n  Executing Tactical Scan...")
        tactical_report = await ArtemisScoutSwarmIntegration.execute_tactical_scan(
            TEST_REPO, threat_level="standard"
        )

        print("✅ Tactical Scan Completed")
        print(f"  Operation ID: {tactical_report['operation_id']}")
        print(f"  Threat Level: {tactical_report['threat_assessment']['level']}")
        print(
            f"  Critical Vulnerabilities: {tactical_report['threat_assessment']['critical_vulnerabilities']}"
        )
        print(f"  Total Issues: {tactical_report['threat_assessment']['total_issues']}")
        print(f"  Scouts Deployed: {tactical_report['execution_metrics']['scouts_deployed']}")
        print(f"  Execution Time: {tactical_report['execution_metrics']['time']:.2f}s")

        # Display tactical recommendations
        if tactical_report["tactical_recommendations"]:
            print("\n  Tactical Recommendations:")
            for i, rec in enumerate(tactical_report["tactical_recommendations"][:3], 1):
                print(f"    {i}. {rec.get('recommendation', 'Unknown')}")
                print(f"       Priority: {rec.get('priority', 'Unknown')}")
                print(f"       Count: {rec.get('count', 0)} instances")

        return {"success": True, "report": tactical_report}

    except Exception as e:
        print(f"❌ Artemis Integration Failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ==============================================================================
# MAIN TEST ORCHESTRATOR
# ==============================================================================


async def run_all_tests():
    """
    Run all integration tests
    """
    print("\n" + "#" * 70)
    print("#" + " " * 20 + "ULTIMATE SCOUT SWARM TEST SUITE" + " " * 18 + "#")
    print("#" * 70)
    print(f"\nRepository: {TEST_REPO}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"MCP Available: {MCP_AVAILABLE}")

    test_results = {}

    # 1. Test MCP Connectivity
    mcp_results = await test_mcp_connectivity()
    test_results["mcp_connectivity"] = mcp_results

    # 2. Test Scout Swarm Creation
    swarm_result = await test_scout_swarm_creation()
    test_results["swarm_creation"] = swarm_result

    if swarm_result["success"]:
        swarm = swarm_result["swarm"]

        # 3. Test Rapid Scan
        rapid_result = await test_rapid_scan(swarm)
        test_results["rapid_scan"] = rapid_result

        # 4. Test Custom Scan
        custom_result = await test_custom_scan(swarm)
        test_results["custom_scan"] = custom_result

        # Get swarm status
        swarm_status = swarm.get_swarm_status()
        test_results["swarm_status"] = swarm_status

    # 5. Test Base Factory
    factory_result = await test_base_factory()
    test_results["base_factory"] = factory_result

    # 6. Test Artemis Integration
    artemis_result = await test_artemis_integration()
    test_results["artemis_integration"] = artemis_result

    # Generate summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    success_count = 0
    failure_count = 0

    for test_name, result in test_results.items():
        if isinstance(result, dict) and "success" in result:
            if result["success"]:
                print(f"✅ {test_name}: PASSED")
                success_count += 1
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                failure_count += 1
        else:
            print(f"⚠️  {test_name}: PARTIAL")

    print(f"\nTotal: {success_count} passed, {failure_count} failed")

    # Save test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"scout_swarm_test_results_{timestamp}.json"

    # Prepare serializable results
    serializable_results = {}
    for key, value in test_results.items():
        if isinstance(value, dict):
            # Remove non-serializable objects
            clean_value = {
                k: v for k, v in value.items() if k not in ["swarm", "factory", "report"]
            }
            serializable_results[key] = clean_value
        else:
            serializable_results[key] = value

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "repository": TEST_REPO,
                "mcp_available": MCP_AVAILABLE,
                "test_results": serializable_results,
                "summary": {"passed": success_count, "failed": failure_count},
            },
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: {results_file}")

    return test_results


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Run all tests
    results = asyncio.run(run_all_tests())

    # Exit with appropriate code
    if all(
        r.get("success", False) for r in results.values() if isinstance(r, dict) and "success" in r
    ):
        print("\n🎆 ALL TESTS PASSED! Scout Swarm is operational!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the results.")
        sys.exit(1)
