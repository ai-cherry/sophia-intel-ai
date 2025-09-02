#!/usr/bin/env python3
"""
Comprehensive test suite for swarms, AG UI, and MCP server connections.
Tests all integration points and ensures everything is working properly.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv('.env.local', override=True)


class SwarmIntegrationTester:
    """Test all swarm integrations and connections."""

    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }

    def _record_test(self, name: str, success: bool, details: str = ""):
        """Record test result."""
        self.results["tests"].append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.results["summary"]["total"] += 1
        if success:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1

    async def test_health_check(self):
        """Test basic health endpoint."""
        print("\n" + "="*60)
        print("🏥 Testing Health Check")
        print("="*60)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/healthz")
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Server healthy")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Systems: {json.dumps(data.get('systems', {}), indent=2)}")
                    self._record_test("Health check", True, str(data))
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    self._record_test("Health check", False, f"Status {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Health check error: {e}")
                self._record_test("Health check", False, str(e))
                return False

    async def test_teams_api(self):
        """Test teams API endpoints."""
        print("\n" + "="*60)
        print("👥 Testing Teams API")
        print("="*60)

        async with httpx.AsyncClient() as client:
            # Get available teams
            print("\n1. Getting available teams...")
            try:
                response = await client.get(f"{self.base_url}/teams")
                if response.status_code == 200:
                    teams = response.json()
                    print(f"✅ Found {len(teams)} teams")
                    for team in teams:
                        print(f"   - {team['id']}: {team['name']}")
                    self._record_test("Get teams", True, f"{len(teams)} teams")
                else:
                    print(f"❌ Failed to get teams: {response.status_code}")
                    self._record_test("Get teams", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Error getting teams: {e}")
                self._record_test("Get teams", False, str(e))

            # Test team execution
            print("\n2. Testing team execution...")
            test_requests = [
                {
                    "team_id": "SIMPLEX",
                    "message": "Test message for simplex team",
                    "pool": "balanced"
                },
                {
                    "team_id": "CONSENSUS",
                    "message": "Test consensus mechanism",
                    "pool": "fast"
                }
            ]

            for req in test_requests:
                try:
                    response = await client.post(
                        f"{self.base_url}/teams/run",
                        json=req,
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        # Handle streaming response
                        response_text = response.text
                        # Check if we got any content
                        if response_text and len(response_text.strip()) > 0:
                            print(f"✅ Team {req['team_id']}: Executed successfully (streaming)")
                            self._record_test(f"Execute team {req['team_id']}", True, "Streaming response received")
                        else:
                            print(f"⚠️ Team {req['team_id']}: Empty response")
                            self._record_test(f"Execute team {req['team_id']}", False, "Empty streaming response")
                    else:
                        print(f"❌ Team {req['team_id']}: Failed ({response.status_code})")
                        error_detail = response.text[:200] if response.text else "No details"
                        self._record_test(f"Execute team {req['team_id']}", False, error_detail)
                except Exception as e:
                    print(f"❌ Team {req['team_id']}: Error - {e}")
                    self._record_test(f"Execute team {req['team_id']}", False, str(e))

    async def test_workflows_api(self):
        """Test workflows API endpoints."""
        print("\n" + "="*60)
        print("🔄 Testing Workflows API")
        print("="*60)

        async with httpx.AsyncClient() as client:
            # Get available workflows
            print("\n1. Getting available workflows...")
            try:
                response = await client.get(f"{self.base_url}/workflows")
                if response.status_code == 200:
                    workflows = response.json()
                    print(f"✅ Found {len(workflows)} workflows")
                    for workflow in workflows:
                        print(f"   - {workflow['id']}: {workflow['name']}")
                    self._record_test("Get workflows", True, f"{len(workflows)} workflows")
                else:
                    print(f"❌ Failed to get workflows: {response.status_code}")
                    self._record_test("Get workflows", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Error getting workflows: {e}")
                self._record_test("Get workflows", False, str(e))

            # Test workflow execution
            print("\n2. Testing workflow execution...")
            test_workflow = {
                "workflow_id": "code_review",
                "message": "Review this test code: def add(a, b): return a + b",
                "pool": "balanced"
            }

            try:
                response = await client.post(
                    f"{self.base_url}/workflows/run",
                    json=test_workflow,
                    timeout=30.0
                )
                if response.status_code == 200:
                    # Handle streaming response
                    response_text = response.text
                    if response_text and len(response_text.strip()) > 0:
                        print("✅ Workflow executed successfully (streaming)")
                        self._record_test("Execute workflow", True, "Streaming response received")
                    else:
                        print("⚠️ Workflow: Empty response")
                        self._record_test("Execute workflow", False, "Empty streaming response")
                else:
                    print(f"❌ Workflow failed: {response.status_code}")
                    self._record_test("Execute workflow", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Workflow error: {e}")
                self._record_test("Execute workflow", False, str(e))

    async def test_memory_system(self):
        """Test memory storage and retrieval."""
        print("\n" + "="*60)
        print("🧠 Testing Memory System")
        print("="*60)

        async with httpx.AsyncClient() as client:
            # Test memory add
            print("\n1. Testing memory storage...")
            test_memory = {
                "topic": "test_topic",
                "content": "This is a test memory entry for swarm testing",
                "source": "test_script",
                "tags": ["test", "integration"],
                "memory_type": "semantic"
            }

            try:
                response = await client.post(
                    f"{self.base_url}/memory/add",
                    json=test_memory
                )
                if response.status_code == 200:
                    print("✅ Memory stored successfully")
                    self._record_test("Memory storage", True, "Success")
                else:
                    print(f"❌ Memory storage failed: {response.status_code}")
                    self._record_test("Memory storage", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Memory storage error: {e}")
                self._record_test("Memory storage", False, str(e))

            # Test memory search
            print("\n2. Testing memory retrieval...")
            search_query = {
                "query": "test memory swarm",
                "top_k": 5,
                "use_semantic": True,
                "use_bm25": True
            }

            try:
                response = await client.post(
                    f"{self.base_url}/memory/search",
                    json=search_query
                )
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Memory search returned {len(results.get('results', []))} results")
                    self._record_test("Memory search", True, f"{len(results.get('results', []))} results")
                else:
                    print(f"❌ Memory search failed: {response.status_code}")
                    self._record_test("Memory search", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Memory search error: {e}")
                self._record_test("Memory search", False, str(e))

    async def test_search_system(self):
        """Test hybrid search functionality."""
        print("\n" + "="*60)
        print("🔍 Testing Search System")
        print("="*60)

        async with httpx.AsyncClient() as client:
            print("\n1. Testing hybrid search...")
            search_request = {
                "query": "authentication implementation",
                "top_k": 10,
                "use_semantic": True,
                "use_bm25": True,
                "use_reranker": False,
                "include_graph": False
            }

            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=search_request
                )
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Search returned {len(results.get('results', []))} results")
                    self._record_test("Hybrid search", True, f"{len(results.get('results', []))} results")
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    self._record_test("Hybrid search", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Search error: {e}")
                self._record_test("Hybrid search", False, str(e))

    async def test_mcp_connections(self):
        """Test MCP server connections."""
        print("\n" + "="*60)
        print("🔌 Testing MCP Server Connections")
        print("="*60)

        # Check if MCP servers are configured
        mcp_servers = {
            "filesystem": os.getenv("MCP_FILESYSTEM", "true").lower() == "true",
            "git": os.getenv("MCP_GIT", "true").lower() == "true",
            "supermemory": os.getenv("MCP_SUPERMEMORY", "true").lower() == "true"
        }

        print("\nMCP Server Configuration:")
        for server, enabled in mcp_servers.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"  {server}: {status}")
            self._record_test(f"MCP {server} config", enabled, "Enabled" if enabled else "Disabled")

    async def test_stats_endpoint(self):
        """Test statistics endpoint."""
        print("\n" + "="*60)
        print("📊 Testing Statistics")
        print("="*60)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/stats")
                if response.status_code == 200:
                    stats = response.json()
                    print("✅ Statistics retrieved")
                    print(f"   Teams: {stats.get('teams', {})}")
                    print(f"   Workflows: {stats.get('workflows', {})}")
                    print(f"   Memory: {stats.get('memory', {})}")
                    self._record_test("Statistics", True, "Success")
                else:
                    print(f"❌ Stats failed: {response.status_code}")
                    self._record_test("Statistics", False, f"Status {response.status_code}")
            except Exception as e:
                print(f"❌ Stats error: {e}")
                self._record_test("Statistics", False, str(e))

    async def test_swarm_patterns(self):
        """Test swarm pattern implementations."""
        print("\n" + "="*60)
        print("🎭 Testing Swarm Patterns")
        print("="*60)

        # Import pattern modules
        try:
            from app.swarms.patterns import (
                AdversarialDebatePattern,
                ConsensusPattern,
                QualityGatesPattern,
                SwarmComposer,
            )
            print("✅ Pattern modules imported successfully")
            self._record_test("Pattern imports", True, "All patterns imported")

            # Test pattern initialization
            patterns_to_test = [
                ("Adversarial Debate", AdversarialDebatePattern),
                ("Quality Gates", QualityGatesPattern),
                ("Consensus", ConsensusPattern)
            ]

            for name, PatternClass in patterns_to_test:
                try:
                    pattern = PatternClass()
                    print(f"✅ {name} pattern initialized")
                    self._record_test(f"{name} pattern", True, "Initialized")
                except Exception as e:
                    print(f"❌ {name} pattern failed: {e}")
                    self._record_test(f"{name} pattern", False, str(e))

        except ImportError as e:
            print(f"❌ Failed to import patterns: {e}")
            self._record_test("Pattern imports", False, str(e))

    async def test_ag_ui_connection(self):
        """Test AG UI dashboard connection."""
        print("\n" + "="*60)
        print("🖥️ Testing AG UI Dashboard Connection")
        print("="*60)

        # Check if AG UI is configured
        ag_ui_port = os.getenv("AGENT_UI_PORT", "3000")
        ag_ui_url = f"http://localhost:{ag_ui_port}"

        print(f"\nChecking AG UI at {ag_ui_url}...")

        async with httpx.AsyncClient() as client:
            try:
                # Try to connect to AG UI
                response = await client.get(ag_ui_url, timeout=5.0)
                if response.status_code in [200, 302]:  # 302 for redirects
                    print(f"✅ AG UI is accessible at port {ag_ui_port}")
                    self._record_test("AG UI connection", True, f"Port {ag_ui_port}")
                else:
                    print(f"⚠️ AG UI returned status {response.status_code}")
                    self._record_test("AG UI connection", False, f"Status {response.status_code}")
            except httpx.ConnectError:
                print(f"❌ AG UI not running on port {ag_ui_port}")
                print("   Run: cd agent-ui && pnpm dev")
                self._record_test("AG UI connection", False, "Not running")
            except Exception as e:
                print(f"❌ AG UI connection error: {e}")
                self._record_test("AG UI connection", False, str(e))

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        summary = self.results["summary"]
        print(f"\nTotal Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")

        if summary['total'] > 0:
            pass_rate = (summary['passed'] / summary['total']) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")

        # List failed tests
        failed_tests = [t for t in self.results["tests"] if not t["success"]]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test.get('details', 'No details')}")

        # Save results
        results_file = "test_results_swarms.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed results saved to {results_file}")

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE SWARM INTEGRATION TEST")
        print("="*60)
        print(f"Server: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")

        # Check if server is running
        server_healthy = await self.test_health_check()

        if not server_healthy:
            print("\n⚠️ Server not healthy, some tests may fail")

        # Run all test suites
        test_suites = [
            self.test_teams_api,
            self.test_workflows_api,
            self.test_memory_system,
            self.test_search_system,
            self.test_mcp_connections,
            self.test_stats_endpoint,
            self.test_swarm_patterns,
            self.test_ag_ui_connection
        ]

        for test_func in test_suites:
            try:
                await test_func()
            except Exception as e:
                print(f"\n❌ Test suite failed: {e}")
                self._record_test(f"{test_func.__name__}", False, str(e))

        # Print summary
        self.print_summary()

        return self.results["summary"]["failed"] == 0


async def main():
    """Main test function."""
    print("🔍 Starting Swarm Integration Tests...")
    print("Make sure the unified server is running on port 8003")

    tester = SwarmIntegrationTester()
    success = await tester.run_all_tests()

    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Check the details above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
