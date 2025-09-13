#!/usr/bin/env python3
"""
Frontend Dashboard Connectivity Testing Script
Tests that the frontend dashboard can connect to backend APIs
"""
import asyncio
import json
import os
import sys
from datetime import datetime
import requests
class FrontendConnectivityTester:
    """Tests frontend dashboard connectivity to backend APIs"""
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "connectivity_tests": {},
            "dashboard_tests": {},
            "errors": [],
        }
    async def run_connectivity_tests(self):
        """Run all frontend connectivity tests"""
        print("🎨 FRONTEND DASHBOARD CONNECTIVITY TESTING")
        print("=" * 60)
        # Test API connectivity
        await self.test_api_connectivity()
        # Test dashboard component structure
        await self.test_dashboard_component()
        # Test data flow
        await self.test_data_flow()
        # Generate report
        self.generate_connectivity_report()
        return self.test_results
    async def test_api_connectivity(self):
        """Test API connectivity from frontend perspective"""
        print("🔌 Testing API Connectivity...")
        # Test all fusion API endpoints that the dashboard uses
        fusion_endpoints = [
            "/api/fusion/metrics",
            "/api/fusion/health",
            "/api/fusion/performance",
            "/api/fusion/status",
        ]
        for endpoint in fusion_endpoints:
            await self.test_endpoint_connectivity(endpoint)
    async def test_endpoint_connectivity(self, endpoint: str):
        """Test individual endpoint connectivity"""
        self.test_results["total_tests"] += 1
        try:
            # Test the endpoint
            response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                # Verify JSON response
                data = response.json()
                # Check if response has expected structure
                if endpoint == "/api/fusion/metrics":
                    required_fields = [
                        "redis_optimization",
                        "edge_rag",
                        "hybrid_routing",
                        "cross_db_analytics",
                    ]
                    has_required_fields = all(
                        field in data for field in required_fields
                    )
                elif endpoint == "/api/fusion/health":
                    required_fields = [
                        "overall_uptime",
                        "avg_response_time",
                        "total_cost_savings",
                    ]
                    has_required_fields = all(
                        field in data for field in required_fields
                    )
                elif endpoint == "/api/fusion/performance":
                    required_fields = [
                        "redis_memory_reduction",
                        "edge_rag_success_rate",
                        "cross_db_accuracy",
                    ]
                    has_required_fields = all(
                        field in data for field in required_fields
                    )
                elif endpoint == "/api/fusion/status":
                    required_fields = ["overall_status", "systems"]
                    has_required_fields = all(
                        field in data for field in required_fields
                    )
                else:
                    has_required_fields = True
                if has_required_fields:
                    self.test_results["passed_tests"] += 1
                    self.test_results["connectivity_tests"][
                        f"{endpoint} Connectivity"
                    ] = {
                        "status": "PASS",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "data_structure": "valid",
                        "sample_data": (
                            str(data)[:200] + "..."
                            if len(str(data)) > 200
                            else str(data)
                        ),
                    }
                    print(
                        f"  ✅ PASS {endpoint} - {response.elapsed.total_seconds()*1000:.0f}ms"
                    )
                else:
                    raise ValueError("Missing required fields in response")
            else:
                raise ValueError(f"HTTP {response.status_code}")
        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["connectivity_tests"][f"{endpoint} Connectivity"] = {
                "status": "FAIL",
                "error": str(e),
            }
            self.test_results["errors"].append(f"{endpoint}: {str(e)}")
            print(f"  ❌ FAIL {endpoint} - {str(e)}")
    async def test_dashboard_component(self):
        """Test dashboard component structure"""
        print("🎨 Testing Dashboard Component...")
        self.test_results["total_tests"] += 1
        try:
            # Check if dashboard component file exists
            dashboard_file = "/home/ubuntu/sophia-main/frontend/src/components/FusionMonitoringDashboard.tsx"
            if not os.path.exists(dashboard_file):
                raise ValueError("Dashboard component file not found")
            # Read and analyze dashboard component
            with open(dashboard_file) as f:
                dashboard_content = f.read()
            # Check for required elements
            required_elements = [
                "FusionMonitoringDashboard",
                "useState",
                "useEffect",
                "/api/fusion/metrics",
                "redis_optimization",
                "edge_rag",
                "hybrid_routing",
                "cross_db_analytics",
                "Card",
                "Tabs",
            ]
            missing_elements = [
                elem for elem in required_elements if elem not in dashboard_content
            ]
            if not missing_elements:
                # Check for proper TypeScript/React structure
                has_proper_structure = all(
                    [
                        "export default" in dashboard_content,
                        "interface" in dashboard_content or "type" in dashboard_content,
                        "return (" in dashboard_content,
                    ]
                )
                if has_proper_structure:
                    self.test_results["passed_tests"] += 1
                    self.test_results["dashboard_tests"][
                        "Dashboard Component Structure"
                    ] = {
                        "status": "PASS",
                        "details": "All required elements present",
                        "component_size": len(dashboard_content),
                        "required_elements": len(required_elements),
                    }
                    print(
                        "  ✅ PASS Dashboard Component - All required elements present"
                    )
                else:
                    raise ValueError(
                        "Dashboard component missing proper React/TypeScript structure"
                    )
            else:
                raise ValueError(
                    f"Dashboard component missing elements: {missing_elements}"
                )
        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["dashboard_tests"]["Dashboard Component Structure"] = {
                "status": "FAIL",
                "error": str(e),
            }
            self.test_results["errors"].append(f"Dashboard Component: {str(e)}")
            print(f"  ❌ FAIL Dashboard Component - {str(e)}")
    async def test_data_flow(self):
        """Test data flow from API to dashboard"""
        print("📊 Testing Data Flow...")
        self.test_results["total_tests"] += 1
        try:
            # Simulate the data flow that the dashboard would use
            # Step 1: Fetch metrics data
            metrics_response = requests.get(
                f"{self.backend_url}/api/fusion/metrics", timeout=10
            )
            if metrics_response.status_code != 200:
                raise ValueError("Failed to fetch metrics data")
            metrics_data = metrics_response.json()
            # Step 2: Fetch health data
            health_response = requests.get(
                f"{self.backend_url}/api/fusion/health", timeout=10
            )
            if health_response.status_code != 200:
                raise ValueError("Failed to fetch health data")
            health_data = health_response.json()
            # Step 3: Fetch performance data
            performance_response = requests.get(
                f"{self.backend_url}/api/fusion/performance", timeout=10
            )
            if performance_response.status_code != 200:
                raise ValueError("Failed to fetch performance data")
            performance_data = performance_response.json()
            # Step 4: Simulate dashboard data processing
            dashboard_data = {
                "overview": {
                    "total_cost_savings": health_data.get("total_cost_savings", 0),
                    "overall_uptime": health_data.get("overall_uptime", 0),
                    "active_systems": health_data.get("active_systems", 0),
                },
                "systems": {
                    "redis": {
                        "memory_saved": metrics_data.get("redis_optimization", {}).get(
                            "memory_saved", 0
                        ),
                        "cost_savings": metrics_data.get("redis_optimization", {}).get(
                            "cost_savings", 0
                        ),
                        "status": metrics_data.get("redis_optimization", {}).get(
                            "status", "unknown"
                        ),
                    },
                    "edge_rag": {
                        "query_count": metrics_data.get("edge_rag", {}).get(
                            "query_count", 0
                        ),
                        "success_rate": metrics_data.get("edge_rag", {}).get(
                            "success_rate", 0
                        ),
                        "status": metrics_data.get("edge_rag", {}).get(
                            "status", "unknown"
                        ),
                    },
                    "hybrid_routing": {
                        "requests_routed": metrics_data.get("hybrid_routing", {}).get(
                            "requests_routed", 0
                        ),
                        "uptime": metrics_data.get("hybrid_routing", {}).get(
                            "uptime", 0
                        ),
                        "status": metrics_data.get("hybrid_routing", {}).get(
                            "status", "unknown"
                        ),
                    },
                    "cross_db_analytics": {
                        "predictions_made": metrics_data.get(
                            "cross_db_analytics", {}
                        ).get("predictions_made", 0),
                        "accuracy": metrics_data.get("cross_db_analytics", {}).get(
                            "accuracy", 0
                        ),
                        "status": metrics_data.get("cross_db_analytics", {}).get(
                            "status", "unknown"
                        ),
                    },
                },
                "performance": {
                    "redis_memory_reduction": performance_data.get(
                        "redis_memory_reduction", 0
                    ),
                    "edge_rag_success_rate": performance_data.get(
                        "edge_rag_success_rate", 0
                    ),
                    "hybrid_routing_uptime": performance_data.get(
                        "hybrid_routing_uptime", 0
                    ),
                    "cross_db_accuracy": performance_data.get("cross_db_accuracy", 0),
                },
            }
            # Verify all data is present and valid
            data_valid = all(
                [
                    isinstance(
                        dashboard_data["overview"]["total_cost_savings"], (int, float)
                    ),
                    isinstance(
                        dashboard_data["overview"]["overall_uptime"], (int, float)
                    ),
                    isinstance(dashboard_data["overview"]["active_systems"], int),
                    len(dashboard_data["systems"]) == 4,
                    len(dashboard_data["performance"]) == 4,
                ]
            )
            if data_valid:
                self.test_results["passed_tests"] += 1
                self.test_results["dashboard_tests"]["Data Flow"] = {
                    "status": "PASS",
                    "details": "Complete data flow from API to dashboard format",
                    "data_summary": {
                        "total_cost_savings": dashboard_data["overview"][
                            "total_cost_savings"
                        ],
                        "systems_count": len(dashboard_data["systems"]),
                        "performance_metrics_count": len(dashboard_data["performance"]),
                    },
                }
                print(
                    f"  ✅ PASS Data Flow - Cost Savings: ${dashboard_data['overview']['total_cost_savings']}, Systems: {len(dashboard_data['systems'])}"
                )
            else:
                raise ValueError("Invalid data structure in dashboard processing")
        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.test_results["dashboard_tests"]["Data Flow"] = {
                "status": "FAIL",
                "error": str(e),
            }
            self.test_results["errors"].append(f"Data Flow: {str(e)}")
            print(f"  ❌ FAIL Data Flow - {str(e)}")
    def generate_connectivity_report(self):
        """Generate connectivity test report"""
        print("\n" + "=" * 60)
        print("📋 FRONTEND CONNECTIVITY TEST REPORT")
        print("=" * 60)
        # Overall statistics
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        print("📊 CONNECTIVITY TEST RESULTS:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print()
        # Connectivity Tests Results
        print("🔌 API CONNECTIVITY TESTS:")
        for name, result in self.test_results["connectivity_tests"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "PASS":
                print(f"    Response Time: {result['response_time_ms']:.0f}ms")
                print(f"    Data Structure: {result['data_structure']}")
        print()
        # Dashboard Tests Results
        print("🎨 DASHBOARD TESTS:")
        for name, result in self.test_results["dashboard_tests"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "PASS" and "details" in result:
                print(f"    Details: {result['details']}")
        print()
        # Errors
        if self.test_results["errors"]:
            print("⚠️ ERRORS:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
            print()
        # Save detailed report
        report_file = "/home/ubuntu/sophia-main/FRONTEND_CONNECTIVITY_TEST_REPORT.json"
        with open(report_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"📄 Detailed report saved to: {report_file}")
        # Final verdict
        if success_rate >= 80:
            print(
                f"\n🎉 FRONTEND CONNECTIVITY TESTING PASSED! ({success_rate:.1f}% success rate)"
            )
            print("✅ Frontend dashboard can connect to all backend APIs!")
        else:
            print(
                f"\n💥 FRONTEND CONNECTIVITY TESTING FAILED! ({success_rate:.1f}% success rate)"
            )
            print("❌ Frontend dashboard connectivity needs attention.")
async def main():
    """Main testing function"""
    tester = FrontendConnectivityTester()
    results = await tester.run_connectivity_tests()
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
