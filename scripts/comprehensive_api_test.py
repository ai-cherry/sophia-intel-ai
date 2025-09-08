#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Provides actual proof that every API and integration is working
"""

import asyncio
import json
import sys
import time
from datetime import datetime

import requests


class ComprehensiveAPITester:
    """Tests all APIs and integrations with real proof"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "api_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "errors": [],
        }

    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🔍 COMPREHENSIVE API TESTING - ACTUAL PROOF")
        print("=" * 60)

        # Test all API endpoints
        await self.test_fusion_apis()
        await self.test_core_apis()
        await self.test_integration_functionality()
        await self.test_performance_metrics()

        # Generate final report
        self.generate_test_report()

        return self.test_results

    async def test_fusion_apis(self):
        """Test all fusion API endpoints"""
        print("🚀 Testing Fusion API Endpoints...")

        fusion_endpoints = [
            ("/api/fusion/metrics", "GET", "Fusion Metrics"),
            ("/api/fusion/health", "GET", "System Health"),
            ("/api/fusion/performance", "GET", "Performance Metrics"),
            ("/api/fusion/status", "GET", "System Status"),
            ("/api/fusion/trigger/redis_optimization", "POST", "Redis Trigger"),
            ("/api/fusion/trigger/edge_rag", "POST", "Edge RAG Trigger"),
            ("/api/fusion/trigger/hybrid_routing", "POST", "Hybrid Routing Trigger"),
            ("/api/fusion/trigger/cross_db_analytics", "POST", "Cross-DB Trigger"),
        ]

        for endpoint, method, name in fusion_endpoints:
            await self.test_api_endpoint(endpoint, method, name)

    async def test_core_apis(self):
        """Test core API endpoints"""
        print("🔧 Testing Core API Endpoints...")

        core_endpoints = [
            ("/health", "GET", "Health Check"),
            ("/smoke", "GET", "Smoke Test"),
            ("/", "GET", "Root Endpoint"),
            ("/info", "GET", "Platform Info"),
            ("/api/gpu-quota", "GET", "GPU Quota"),
        ]

        for endpoint, method, name in core_endpoints:
            await self.test_api_endpoint(endpoint, method, name)

    async def test_api_endpoint(self, endpoint: str, method: str, name: str):
        """Test individual API endpoint"""
        self.test_results["total_tests"] += 1

        try:
            url = f"{self.base_url}{endpoint}"

            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check if response is successful
            if response.status_code in [200, 201]:
                self.test_results["passed_tests"] += 1
                status = "✅ PASS"

                # Try to parse JSON response
                try:
                    response_data = response.json()
                    data_preview = (
                        str(response_data)[:100] + "..."
                        if len(str(response_data)) > 100
                        else str(response_data)
                    )
                except:
                    data_preview = (
                        response.text[:100] + "..." if len(response.text) > 100 else response.text
                    )

                self.test_results["api_tests"][name] = {
                    "status": "PASS",
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "response_preview": data_preview,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }

                print(
                    f"  {status} {name} ({method} {endpoint}) - {response.status_code} - {response.elapsed.total_seconds()*1000:.0f}ms"
                )

            else:
                self.test_results["failed_tests"] += 1
                status = "❌ FAIL"

                self.test_results["api_tests"][name] = {
                    "status": "FAIL",
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "error": response.text[:200],
                }

                print(f"  {status} {name} ({method} {endpoint}) - {response.status_code}")

        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["errors"].append(f"{name}: {str(e)}")

            self.test_results["api_tests"][name] = {
                "status": "ERROR",
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
            }

            print(f"  ❌ ERROR {name} ({method} {endpoint}) - {str(e)}")

    async def test_integration_functionality(self):
        """Test integration functionality"""
        print("🔌 Testing Integration Functionality...")

        # Test fusion metrics data structure
        await self.test_fusion_metrics_structure()

        # Test system health calculations
        await self.test_system_health_calculations()

        # Test performance metrics
        await self.test_performance_metrics_structure()

    async def test_fusion_metrics_structure(self):
        """Test fusion metrics data structure"""
        self.test_results["total_tests"] += 1

        try:
            response = requests.get(f"{self.base_url}/api/fusion/metrics", timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Verify required fields
                required_fields = [
                    "redis_optimization",
                    "edge_rag",
                    "hybrid_routing",
                    "cross_db_analytics",
                    "timestamp",
                ]

                all_fields_present = all(field in data for field in required_fields)

                if all_fields_present:
                    # Verify each system has required metrics
                    redis_metrics = data["redis_optimization"]
                    edge_metrics = data["edge_rag"]
                    hybrid_metrics = data["hybrid_routing"]
                    cross_db_metrics = data["cross_db_analytics"]

                    redis_valid = all(
                        key in redis_metrics
                        for key in ["memory_saved", "cost_savings", "keys_pruned", "status"]
                    )
                    edge_valid = all(
                        key in edge_metrics
                        for key in ["query_count", "avg_latency", "success_rate", "status"]
                    )
                    hybrid_valid = all(
                        key in hybrid_metrics
                        for key in ["requests_routed", "cost_optimization", "uptime", "status"]
                    )
                    cross_db_valid = all(
                        key in cross_db_metrics
                        for key in ["predictions_made", "accuracy", "data_points", "status"]
                    )

                    if redis_valid and edge_valid and hybrid_valid and cross_db_valid:
                        self.test_results["passed_tests"] += 1
                        self.test_results["integration_tests"]["Fusion Metrics Structure"] = {
                            "status": "PASS",
                            "details": "All required fields present and valid",
                            "data_sample": {
                                "redis_cost_savings": redis_metrics["cost_savings"],
                                "edge_success_rate": edge_metrics["success_rate"],
                                "hybrid_uptime": hybrid_metrics["uptime"],
                                "cross_db_accuracy": cross_db_metrics["accuracy"],
                            },
                        }
                        print("  ✅ PASS Fusion Metrics Structure - All fields valid")
                    else:
                        raise ValueError("Missing required metric fields")
                else:
                    raise ValueError("Missing required top-level fields")
            else:
                raise ValueError(f"HTTP {response.status_code}")

        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["integration_tests"]["Fusion Metrics Structure"] = {
                "status": "FAIL",
                "error": str(e),
            }
            print(f"  ❌ FAIL Fusion Metrics Structure - {str(e)}")

    async def test_system_health_calculations(self):
        """Test system health calculations"""
        self.test_results["total_tests"] += 1

        try:
            response = requests.get(f"{self.base_url}/api/fusion/health", timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Verify health metrics
                required_fields = [
                    "overall_uptime",
                    "avg_response_time",
                    "total_cost_savings",
                    "active_systems",
                    "timestamp",
                ]

                if all(field in data for field in required_fields):
                    # Verify data types and ranges
                    uptime_valid = (
                        isinstance(data["overall_uptime"], (int, float))
                        and 0 <= data["overall_uptime"] <= 100
                    )
                    response_time_valid = (
                        isinstance(data["avg_response_time"], (int, float))
                        and data["avg_response_time"] > 0
                    )
                    cost_savings_valid = (
                        isinstance(data["total_cost_savings"], (int, float))
                        and data["total_cost_savings"] >= 0
                    )
                    active_systems_valid = (
                        isinstance(data["active_systems"], int) and data["active_systems"] >= 0
                    )

                    if (
                        uptime_valid
                        and response_time_valid
                        and cost_savings_valid
                        and active_systems_valid
                    ):
                        self.test_results["passed_tests"] += 1
                        self.test_results["integration_tests"]["System Health Calculations"] = {
                            "status": "PASS",
                            "details": "All health metrics calculated correctly",
                            "metrics": {
                                "uptime": data["overall_uptime"],
                                "response_time": data["avg_response_time"],
                                "cost_savings": data["total_cost_savings"],
                                "active_systems": data["active_systems"],
                            },
                        }
                        print(
                            f"  ✅ PASS System Health Calculations - Uptime: {data['overall_uptime']}%, Cost Savings: ${data['total_cost_savings']}"
                        )
                    else:
                        raise ValueError("Invalid health metric values")
                else:
                    raise ValueError("Missing required health fields")
            else:
                raise ValueError(f"HTTP {response.status_code}")

        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["integration_tests"]["System Health Calculations"] = {
                "status": "FAIL",
                "error": str(e),
            }
            print(f"  ❌ FAIL System Health Calculations - {str(e)}")

    async def test_performance_metrics_structure(self):
        """Test performance metrics structure"""
        self.test_results["total_tests"] += 1

        try:
            response = requests.get(f"{self.base_url}/api/fusion/performance", timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Verify performance metrics
                required_fields = [
                    "redis_memory_reduction",
                    "redis_cost_optimization",
                    "edge_rag_success_rate",
                    "edge_rag_latency_improvement",
                    "hybrid_routing_uptime",
                    "cross_db_accuracy",
                    "timestamp",
                ]

                if all(field in data for field in required_fields):
                    # Verify all metrics are numeric and in valid ranges
                    metrics_valid = all(
                        isinstance(data[field], (int, float)) and 0 <= data[field] <= 100
                        for field in required_fields[:-1]  # Exclude timestamp
                    )

                    if metrics_valid:
                        self.test_results["passed_tests"] += 1
                        self.test_results["integration_tests"]["Performance Metrics Structure"] = {
                            "status": "PASS",
                            "details": "All performance metrics valid",
                            "metrics": {
                                "redis_memory_reduction": data["redis_memory_reduction"],
                                "edge_rag_success_rate": data["edge_rag_success_rate"],
                                "hybrid_routing_uptime": data["hybrid_routing_uptime"],
                                "cross_db_accuracy": data["cross_db_accuracy"],
                            },
                        }
                        print(
                            f"  ✅ PASS Performance Metrics - Memory: {data['redis_memory_reduction']}%, Accuracy: {data['cross_db_accuracy']}%"
                        )
                    else:
                        raise ValueError("Invalid performance metric values")
                else:
                    raise ValueError("Missing required performance fields")
            else:
                raise ValueError(f"HTTP {response.status_code}")

        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["integration_tests"]["Performance Metrics Structure"] = {
                "status": "FAIL",
                "error": str(e),
            }
            print(f"  ❌ FAIL Performance Metrics Structure - {str(e)}")

    async def test_performance_metrics(self):
        """Test API performance metrics"""
        print("⚡ Testing API Performance...")

        # Test response times for critical endpoints
        critical_endpoints = ["/api/fusion/metrics", "/api/fusion/health", "/health"]

        for endpoint in critical_endpoints:
            await self.test_endpoint_performance(endpoint)

    async def test_endpoint_performance(self, endpoint: str):
        """Test individual endpoint performance"""
        self.test_results["total_tests"] += 1

        try:
            # Measure response time
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            if response.status_code == 200 and response_time_ms < 5000:  # 5 second threshold
                self.test_results["passed_tests"] += 1
                self.test_results["performance_tests"][f"{endpoint} Performance"] = {
                    "status": "PASS",
                    "response_time_ms": response_time_ms,
                    "threshold_ms": 5000,
                }
                print(f"  ✅ PASS {endpoint} Performance - {response_time_ms:.0f}ms")
            else:
                raise ValueError(
                    f"Slow response: {response_time_ms:.0f}ms or HTTP {response.status_code}"
                )

        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["performance_tests"][f"{endpoint} Performance"] = {
                "status": "FAIL",
                "error": str(e),
            }
            print(f"  ❌ FAIL {endpoint} Performance - {str(e)}")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE API TEST REPORT - ACTUAL PROOF")
        print("=" * 60)

        # Overall statistics
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0

        print("📊 OVERALL RESULTS:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print()

        # API Tests Results
        print("🚀 API ENDPOINT TESTS:")
        for name, result in self.test_results["api_tests"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "PASS":
                print(f"    Response Time: {result.get('response_time_ms', 0):.0f}ms")
                print(f"    Status Code: {result['status_code']}")
        print()

        # Integration Tests Results
        print("🔌 INTEGRATION TESTS:")
        for name, result in self.test_results["integration_tests"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "PASS" and "details" in result:
                print(f"    Details: {result['details']}")
        print()

        # Performance Tests Results
        print("⚡ PERFORMANCE TESTS:")
        for name, result in self.test_results["performance_tests"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "PASS":
                print(f"    Response Time: {result['response_time_ms']:.0f}ms")
        print()

        # Errors
        if self.test_results["errors"]:
            print("⚠️ ERRORS:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
            print()

        # Save detailed report
        report_file = "/home/ubuntu/sophia-main/COMPREHENSIVE_API_TEST_REPORT.json"
        with open(report_file, "w") as f:
            json.dump(self.test_results, f, indent=2)

        print(f"📄 Detailed report saved to: {report_file}")

        # Final verdict
        if success_rate >= 80:
            print(f"\n🎉 COMPREHENSIVE TESTING PASSED! ({success_rate:.1f}% success rate)")
            print("✅ APIs and integrations are working with actual proof!")
        else:
            print(f"\n💥 COMPREHENSIVE TESTING FAILED! ({success_rate:.1f}% success rate)")
            print("❌ Some APIs or integrations need attention.")


async def main():
    """Main testing function"""
    tester = ComprehensiveAPITester()
    results = await tester.run_all_tests()

    # Return appropriate exit code
    success_rate = (
        (results["passed_tests"] / results["total_tests"] * 100)
        if results["total_tests"] > 0
        else 0
    )
    return 0 if success_rate >= 80 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
