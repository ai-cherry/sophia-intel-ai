#!/usr/bin/env python3
"""
Comprehensive test suite for Sophia AI platform
Tests all services, APIs, and integration points
"""

import asyncio
import json
import time
from typing import Any, Dict, List

import httpx


class ComprehensiveTestSuite:
    def __init__(self):
        self.results = {
            "unit_tests": [],
            "integration_tests": [],
            "api_tests": [],
            "performance_tests": [],
            "chaos_tests": [],
        }
        self.services = {
            "orchestrator": "http://localhost:8002",
            "neural-engine": "http://localhost:8001",
            "enhanced-search": "http://localhost:8004",
            "chat-service": "http://localhost:8003",
        }

    async def test_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Test individual service health"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                end_time = time.time()

                return {
                    "service": service_name,
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "response_time_ms": round((end_time - start_time) * 1000, 2),
                    "status_code": response.status_code,
                    "response": (
                        response.json() if response.status_code == 200 else None
                    ),
                }
        except Exception as e:
            return {
                "service": service_name,
                "status": "FAIL",
                "error": str(e),
                "response_time_ms": None,
            }

    async def test_api_endpoints(self) -> List[Dict[str, Any]]:
        """Test all API endpoints"""
        tests = []

        # Test neural inference
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.services['neural-engine']}/api/v1/inference",
                    json={"prompt": "Test inference", "max_tokens": 10},
                )
                tests.append(
                    {
                        "endpoint": "neural_inference",
                        "status": "PASS" if response.status_code == 200 else "FAIL",
                        "response_code": response.status_code,
                    }
                )
        except Exception as e:
            tests.append(
                {"endpoint": "neural_inference", "status": "FAIL", "error": str(e)}
            )

        # Test enhanced search
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.services['enhanced-search']}/search",
                    json={"query": "test search", "max_results": 5},
                )
                tests.append(
                    {
                        "endpoint": "enhanced_search",
                        "status": "PASS" if response.status_code == 200 else "FAIL",
                        "response_code": response.status_code,
                    }
                )
        except Exception as e:
            tests.append(
                {"endpoint": "enhanced_search", "status": "FAIL", "error": str(e)}
            )

        return tests

    async def performance_test(
        self, service_name: str, url: str, requests: int = 10
    ) -> Dict[str, Any]:
        """Performance test for service"""
        response_times = []
        errors = 0

        async with httpx.AsyncClient(timeout=5.0) as client:
            for _ in range(requests):
                start_time = time.time()
                try:
                    response = await client.get(f"{url}/health")
                    end_time = time.time()
                    if response.status_code == 200:
                        response_times.append((end_time - start_time) * 1000)
                    else:
                        errors += 1
                except Exception:errors += 1

        if response_times:
            return {
                "service": service_name,
                "requests": requests,
                "errors": errors,
                "avg_response_time_ms": round(
                    sum(response_times) / len(response_times), 2
                ),
                "min_response_time_ms": round(min(response_times), 2),
                "max_response_time_ms": round(max(response_times), 2),
                "p95_response_time_ms": round(
                    sorted(response_times)[int(len(response_times) * 0.95)], 2
                ),
            }
        else:
            return {
                "service": service_name,
                "requests": requests,
                "errors": errors,
                "status": "ALL_FAILED",
            }

    async def run_all_tests(self):
        """Execute comprehensive test suite"""
        print("🧪 Running comprehensive test suite...")

        # Health tests
        print("📊 Testing service health...")
        health_results = []
        for service_name, url in self.services.items():
            result = await self.test_service_health(service_name, url)
            health_results.append(result)
            print(
                f"  {service_name}: {result['status']} ({result.get('response_time_ms', 'N/A')}ms)"
            )

        self.results["integration_tests"] = health_results

        # API tests
        print("🔌 Testing API endpoints...")
        api_results = await self.test_api_endpoints()
        self.results["api_tests"] = api_results
        for result in api_results:
            print(f"  {result['endpoint']}: {result['status']}")

        # Performance tests
        print("⚡ Running performance tests...")
        perf_results = []
        for service_name, url in self.services.items():
            result = await self.performance_test(service_name, url, 10)
            perf_results.append(result)
            if "avg_response_time_ms" in result:
                print(
                    f"  {service_name}: {result['avg_response_time_ms']}ms avg, {result['p95_response_time_ms']}ms p95"
                )
            else:
                print(f"  {service_name}: {result.get('status', 'FAILED')}")

        self.results["performance_tests"] = perf_results

        # Summary
        total_tests = len(health_results) + len(api_results) + len(perf_results)
        passed_tests = (
            sum(1 for r in health_results if r["status"] == "PASS")
            + sum(1 for r in api_results if r["status"] == "PASS")
            + sum(1 for r in perf_results if "avg_response_time_ms" in r)
        )

        print(
            f"\n🎯 TEST SUMMARY: {passed_tests}/{total_tests} tests passed ({round(passed_tests/total_tests*100, 1)}%)"
        )

        return self.results


async def main():
    suite = ComprehensiveTestSuite()
    results = await suite.run_all_tests()

    # Save results
    with open("comprehensive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Test results saved to comprehensive_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
