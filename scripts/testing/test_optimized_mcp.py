#!/usr/bin/env python3
"""
MCP Architecture Validation Test
===============================

Comprehensive test script to validate the optimized MCP architecture.
Tests all components, endpoints, and capabilities to ensure proper functionality.

Usage:
    python scripts/test_optimized_mcp.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MCPArchitectureValidator:
    """Validates the optimized MCP architecture"""

    def __init__(self):
        import os
        self.base_url = f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}"
        self.test_results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0,
            },
        }

    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        self.log("🚀 Starting MCP Architecture Validation")
        self.log("=" * 60)

        # Test categories
        test_categories = [
            ("Basic Health Checks", self.test_basic_health),
            ("MCP Capabilities", self.test_mcp_capabilities),
            ("Filesystem Operations", self.test_filesystem_operations),
            ("Git Operations", self.test_git_operations),
            ("Memory Operations", self.test_memory_operations),
            ("Embeddings Operations", self.test_embeddings_operations),
            ("Server Management", self.test_server_management),
            ("Connection Management", self.test_connection_management),
            ("Performance & Metrics", self.test_performance_metrics),
        ]

        for category_name, test_function in test_categories:
            self.log(f"\n📋 Testing {category_name}...")
            try:
                await test_function()
            except Exception as e:
                self.log(f"❌ Category {category_name} failed: {e}", "ERROR")
                self.test_results["tests"][category_name] = {
                    "status": "failed",
                    "error": str(e),
                }
                self.test_results["summary"]["failed"] += 1

            self.test_results["summary"]["total"] += 1

        # Generate final report
        await self.generate_test_report()

    async def test_basic_health(self):
        """Test basic health endpoints"""
        tests = [
            ("Unified Server Health", f"{self.base_url}/healthz"),
            ("MCP Health", f"{self.base_url}/api/mcp/health"),
            ("Hub Status", f"{self.base_url}/hub"),
        ]

        results = {}
        for test_name, url in tests:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url)

                    if response.status_code == 200:
                        self.log(f"✅ {test_name}: OK")
                        results[test_name] = {
                            "status": "passed",
                            "status_code": response.status_code,
                            "response_size": len(response.content),
                        }
                        self.test_results["summary"]["passed"] += 1
                    else:
                        self.log(f"❌ {test_name}: HTTP {response.status_code}")
                        results[test_name] = {
                            "status": "failed",
                            "status_code": response.status_code,
                        }
                        self.test_results["summary"]["failed"] += 1
            except Exception as e:
                self.log(f"❌ {test_name}: {str(e)}")
                results[test_name] = {
                    "status": "failed",
                    "error": str(e),
                }
                self.test_results["summary"]["failed"] += 1

        self.test_results["tests"]["Basic Health Checks"] = results

    async def test_mcp_capabilities(self):
        """Test MCP capabilities endpoint"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/mcp/capabilities")

                if response.status_code == 200:
                    data = response.json()
                    capabilities = data.get("capabilities", {})

                    self.log(f"✅ Found {len(capabilities)} capabilities")

                    # Check for expected capabilities
                    expected_capabilities = [
                        "filesystem",
                        "git",
                        "memory",
                        "embeddings",
                        "code_analysis",
                        "business_analytics",
                        "web_search",
                        "database",
                    ]

                    available = 0
                    for cap in expected_capabilities:
                        if cap in capabilities and capabilities[cap].get("available"):
                            available += 1
                            self.log(f"  ✅ {cap}: Available")
                        else:
                            self.log(f"  ⚠️ {cap}: Not available")

                    self.test_results["tests"]["MCP Capabilities"] = {
                        "status": "passed",
                        "total_capabilities": len(capabilities),
                        "available_capabilities": available,
                        "expected_capabilities": len(expected_capabilities),
                        "details": capabilities,
                    }
                    self.test_results["summary"]["passed"] += 1
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ MCP capabilities test failed: {e}")
            self.test_results["tests"]["MCP Capabilities"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_filesystem_operations(self):
        """Test filesystem MCP operations"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Test list directory
                list_response = await client.post(
                    f"{self.base_url}/api/mcp/filesystem",
                    json={
                        "method": "list_directory",
                        "params": {"path": "."},
                        "client_id": "test_client",
                    },
                )

                if list_response.status_code == 200:
                    list_data = list_response.json()
                    if list_data.get("success"):
                        items_count = len(list_data.get("items", []))
                        self.log(f"✅ Filesystem list_directory: {items_count} items")

                        # Test read file (try to read this script)
                        test_file = str(Path(__file__).name)
                        read_response = await client.post(
                            f"{self.base_url}/api/mcp/filesystem",
                            json={
                                "method": "read_file",
                                "params": {"path": f"scripts/{test_file}"},
                                "client_id": "test_client",
                            },
                        )

                        if read_response.status_code == 200:
                            read_data = read_response.json()
                            if read_data.get("success"):
                                content_size = read_data.get("size", 0)
                                self.log(
                                    f"✅ Filesystem read_file: {content_size} bytes"
                                )

                                self.test_results["tests"]["Filesystem Operations"] = {
                                    "status": "passed",
                                    "list_directory_items": items_count,
                                    "read_file_size": content_size,
                                }
                                self.test_results["summary"]["passed"] += 1
                                return

                        raise Exception("Read file operation failed")
                    else:
                        raise Exception(
                            f"List directory failed: {list_data.get('error')}"
                        )
                else:
                    raise Exception(f"HTTP {list_response.status_code}")

        except Exception as e:
            self.log(f"❌ Filesystem operations test failed: {e}")
            self.test_results["tests"]["Filesystem Operations"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_git_operations(self):
        """Test git MCP operations"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Test git status
                response = await client.post(
                    f"{self.base_url}/api/mcp/git",
                    json={
                        "method": "git_status",
                        "params": {"repository": "."},
                        "client_id": "test_client",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        files = data.get("files", [])
                        is_clean = data.get("clean", False)
                        self.log(
                            f"✅ Git status: {len(files)} changed files, clean={is_clean}"
                        )

                        self.test_results["tests"]["Git Operations"] = {
                            "status": "passed",
                            "changed_files": len(files),
                            "repository_clean": is_clean,
                        }
                        self.test_results["summary"]["passed"] += 1
                    else:
                        raise Exception(f"Git status failed: {data.get('error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ Git operations test failed: {e}")
            self.test_results["tests"]["Git Operations"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_memory_operations(self):
        """Test memory MCP operations"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Test store memory
                store_response = await client.post(
                    f"{self.base_url}/api/mcp/memory",
                    json={
                        "method": "store_memory",
                        "params": {
                            "key": "test_memory_key",
                            "content": "Test memory content for MCP validation",
                        },
                        "client_id": "test_client",
                    },
                )

                if store_response.status_code == 200:
                    store_data = store_response.json()
                    if store_data.get("success"):
                        self.log("✅ Memory store operation successful")

                        # Test retrieve memory
                        retrieve_response = await client.post(
                            f"{self.base_url}/api/mcp/memory",
                            json={
                                "method": "retrieve_memory",
                                "params": {"key": "test_memory_key"},
                                "client_id": "test_client",
                            },
                        )

                        if retrieve_response.status_code == 200:
                            retrieve_data = retrieve_response.json()
                            if retrieve_data.get("success"):
                                self.log("✅ Memory retrieve operation successful")

                                self.test_results["tests"]["Memory Operations"] = {
                                    "status": "passed",
                                    "store_successful": True,
                                    "retrieve_successful": True,
                                }
                                self.test_results["summary"]["passed"] += 1
                                return

                        raise Exception("Memory retrieve failed")
                    else:
                        raise Exception(
                            f"Memory store failed: {store_data.get('error')}"
                        )
                else:
                    raise Exception(f"HTTP {store_response.status_code}")

        except Exception as e:
            self.log(f"❌ Memory operations test failed: {e}")
            self.test_results["tests"]["Memory Operations"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_embeddings_operations(self):
        """Test embeddings MCP operations"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/api/mcp/embeddings",
                    json={
                        "method": "generate_embeddings",
                        "params": {"text": "Test text for embeddings generation"},
                        "client_id": "test_client",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        embeddings = data.get("embeddings", [])
                        dimensions = data.get("dimensions", 0)
                        model = data.get("model", "unknown")

                        self.log(
                            f"✅ Embeddings generated: {dimensions}D vector, model={model}"
                        )

                        self.test_results["tests"]["Embeddings Operations"] = {
                            "status": "passed",
                            "dimensions": dimensions,
                            "model": model,
                            "embedding_length": len(embeddings),
                        }
                        self.test_results["summary"]["passed"] += 1
                    else:
                        raise Exception(
                            f"Embeddings generation failed: {data.get('error')}"
                        )
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ Embeddings operations test failed: {e}")
            self.test_results["tests"]["Embeddings Operations"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_server_management(self):
        """Test server management endpoints"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/mcp/servers")

                if response.status_code == 200:
                    data = response.json()
                    servers = data.get("servers", {})

                    healthy_servers = 0
                    total_servers = len(servers)

                    for server_name, server_info in servers.items():
                        status = server_info.get("status", "unknown")
                        domain = server_info.get("domain", "unknown")
                        capability = server_info.get("capability", "unknown")

                        if status == "healthy":
                            healthy_servers += 1
                            self.log(
                                f"  ✅ {server_name} ({domain}/{capability}): {status}"
                            )
                        else:
                            self.log(
                                f"  ⚠️ {server_name} ({domain}/{capability}): {status}"
                            )

                    self.log(
                        f"✅ Server management: {healthy_servers}/{total_servers} healthy"
                    )

                    self.test_results["tests"]["Server Management"] = {
                        "status": "passed",
                        "total_servers": total_servers,
                        "healthy_servers": healthy_servers,
                        "server_details": servers,
                    }
                    self.test_results["summary"]["passed"] += 1
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ Server management test failed: {e}")
            self.test_results["tests"]["Server Management"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_connection_management(self):
        """Test connection management endpoints"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/mcp/connections")

                if response.status_code == 200:
                    data = response.json()
                    total_connections = data.get("total_connections", 0)
                    active_connections = data.get("active_connections", 0)
                    servers = data.get("servers", {})

                    self.log(
                        f"✅ Connections: {active_connections}/{total_connections} active"
                    )

                    # Log server utilization
                    for server_name, server_stats in servers.items():
                        utilization = server_stats.get("utilization", 0)
                        active = server_stats.get("active_connections", 0)
                        max_conn = server_stats.get("max_connections", 0)
                        self.log(
                            f"  Server {server_name}: {active}/{max_conn} ({utilization:.1f}%)"
                        )

                    self.test_results["tests"]["Connection Management"] = {
                        "status": "passed",
                        "total_connections": total_connections,
                        "active_connections": active_connections,
                        "server_stats": servers,
                    }
                    self.test_results["summary"]["passed"] += 1
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ Connection management test failed: {e}")
            self.test_results["tests"]["Connection Management"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def test_performance_metrics(self):
        """Test performance metrics endpoints"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/mcp/metrics")

                if response.status_code == 200:
                    data = response.json()
                    uptime = data.get("uptime_seconds", 0)
                    total_requests = data.get("total_requests", 0)
                    rps = data.get("requests_per_second", 0)
                    active_connections = data.get("active_connections", 0)

                    self.log("✅ Performance metrics:")
                    self.log(f"  Uptime: {uptime:.1f}s")
                    self.log(f"  Total requests: {total_requests}")
                    self.log(f"  Requests/second: {rps:.2f}")
                    self.log(f"  Active connections: {active_connections}")

                    self.test_results["tests"]["Performance & Metrics"] = {
                        "status": "passed",
                        "uptime_seconds": uptime,
                        "total_requests": total_requests,
                        "requests_per_second": rps,
                        "active_connections": active_connections,
                    }
                    self.test_results["summary"]["passed"] += 1
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.log(f"❌ Performance metrics test failed: {e}")
            self.test_results["tests"]["Performance & Metrics"] = {
                "status": "failed",
                "error": str(e),
            }
            self.test_results["summary"]["failed"] += 1

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        self.log("\n" + "=" * 60)
        self.log("📊 MCP ARCHITECTURE VALIDATION REPORT")
        self.log("=" * 60)

        summary = self.test_results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]

        if total > 0:
            pass_rate = (passed / total) * 100
            self.log(
                f"Overall Test Results: {passed}/{total} passed ({pass_rate:.1f}%)"
            )

            if pass_rate >= 80:
                self.log("🎉 MCP Architecture: HEALTHY", "SUCCESS")
            elif pass_rate >= 60:
                self.log("⚠️ MCP Architecture: DEGRADED", "WARNING")
            else:
                self.log("❌ MCP Architecture: UNHEALTHY", "ERROR")
        else:
            self.log("❌ No tests completed", "ERROR")

        # Detailed results
        self.log("\nDetailed Test Results:")
        for test_name, result in self.test_results["tests"].items():
            status = result.get("status", "unknown")
            if status == "passed":
                self.log(f"  ✅ {test_name}")
            elif status == "failed":
                error = result.get("error", "Unknown error")
                self.log(f"  ❌ {test_name}: {error}")
            else:
                self.log(f"  ⚠️ {test_name}: {status}")

        # Save detailed report
        report_path = project_root / "mcp_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        self.log(f"\n📄 Detailed report saved to: {report_path}")

        # Generate recommendations
        self.generate_recommendations()

        return pass_rate if total > 0 else 0

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        self.log("\n🔍 RECOMMENDATIONS:")

        failed_tests = [
            name
            for name, result in self.test_results["tests"].items()
            if result.get("status") == "failed"
        ]

        if not failed_tests:
            self.log("✅ All systems operational - no immediate action required")
            self.log("📈 Consider monitoring performance metrics for trends")
            return

        self.log("🚨 Issues detected - recommended actions:")

        for test_name in failed_tests:
            if "Health" in test_name:
                self.log("  • Check if unified server is running on port 8000")
                self.log("  • Verify Redis connectivity")
            elif "Filesystem" in test_name:
                self.log("  • Check filesystem permissions")
                self.log("  • Verify working directory access")
            elif "Git" in test_name:
                self.log("  • Ensure git is installed and accessible")
                self.log("  • Check if current directory is a git repository")
            elif "Memory" in test_name:
                self.log("  • Verify Redis connection for memory operations")
                self.log("  • Check memory service configuration")
            elif "Server" in test_name:
                self.log("  • Review server registry configuration")
                self.log("  • Check MCP orchestrator health")

        self.log("\n💡 General troubleshooting:")
        self.log("  1. Restart the unified server: python app/api/unified_server.py")
        self.log("  2. Check Redis status: redis-cli ping")
        self.log("  3. Review logs in the logs/ directory")
        self.log("  4. Run MCP startup script: python scripts/optimized_mcp_startup.py")


async def main():
    """Main test execution"""
    validator = MCPArchitectureValidator()

    try:
        pass_rate = await validator.run_all_tests()

        if pass_rate >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

    except KeyboardInterrupt:
        validator.log("🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        validator.log(f"💥 Test execution failed: {e}", "FATAL")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
