#!/usr/bin/env python3
"""
Load testing for Sophia Intel AI with optimizations
Tests connection pooling, circuit breakers, and performance improvements
"""

import asyncio
import aiohttp
import time
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
import statistics

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make a single request and measure performance"""
        start_time = time.time()
        try:
            async with session.request(method, f"{self.base_url}{endpoint}", json=data) as response:
                status = response.status
                body = await response.text()
                success = status < 400
        except Exception as e:
            status = 0
            body = str(e)
            success = False
        
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "endpoint": endpoint,
            "status": status,
            "success": success,
            "response_time_ms": elapsed,
            "timestamp": time.time()
        }
    
    async def run_concurrent_requests(self, endpoint: str, count: int = 100, concurrency: int = 10) -> List[Dict]:
        """Run multiple concurrent requests"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(count):
                task = self.make_request(session, endpoint)
                tasks.append(task)
                
                # Control concurrency
                if len(tasks) >= concurrency:
                    batch_results = await asyncio.gather(*tasks)
                    results.extend(batch_results)
                    tasks = []
            
            # Process remaining tasks
            if tasks:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
        
        return results
    
    def analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze test results and calculate metrics"""
        if not results:
            return {"error": "No results to analyze"}
        
        response_times = [r["response_time_ms"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])
        
        if not response_times:
            return {
                "total_requests": len(results),
                "success_rate": 0,
                "error": "All requests failed"
            }
        
        return {
            "total_requests": len(results),
            "successful_requests": success_count,
            "failed_requests": len(results) - success_count,
            "success_rate": (success_count / len(results)) * 100,
            "response_times": {
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "p95_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                "p99_ms": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)
            },
            "throughput_rps": len(results) / ((max(r["timestamp"] for r in results) - min(r["timestamp"] for r in results)) or 1)
        }
    
    async def test_connection_pooling(self):
        """Test connection pooling effectiveness"""
        print("\n🔄 Testing Connection Pooling...")
        
        # Baseline: Sequential requests
        start = time.time()
        sequential_results = []
        async with aiohttp.ClientSession() as session:
            for _ in range(20):
                result = await self.make_request(session, "/healthz")
                sequential_results.append(result)
        sequential_time = time.time() - start
        
        # With pooling: Concurrent requests
        start = time.time()
        concurrent_results = await self.run_concurrent_requests("/healthz", count=20, concurrency=10)
        concurrent_time = time.time() - start
        
        improvement = ((sequential_time - concurrent_time) / sequential_time) * 100
        
        print(f"  Sequential time: {sequential_time:.2f}s")
        print(f"  Concurrent time: {concurrent_time:.2f}s")
        print(f"  Improvement: {improvement:.1f}%")
        
        return improvement > 30  # Expect at least 30% improvement
    
    async def test_circuit_breakers(self):
        """Test circuit breaker functionality"""
        print("\n🛡️ Testing Circuit Breakers...")
        
        # Simulate failures to trigger circuit breaker
        results = []
        
        # Make requests to a failing endpoint
        for i in range(15):
            result = await self.run_concurrent_requests("/test/fail", count=1, concurrency=1)
            results.extend(result)
            
            # Check if circuit opened (fast failures)
            if i > 10 and result[0]["response_time_ms"] < 100:
                print(f"  ✅ Circuit breaker opened after {i} failures")
                return True
        
        print("  ⚠️ Circuit breaker did not open as expected")
        return False
    
    async def run_comprehensive_load_test(self):
        """Run comprehensive load test suite"""
        print("=" * 60)
        print("🚀 SOPHIA INTEL AI - LOAD TEST SUITE")
        print("=" * 60)
        
        test_results = {
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Test 1: Health endpoint baseline
        print("\n1️⃣ Health Endpoint Baseline (100 requests)")
        health_results = await self.run_concurrent_requests("/healthz", count=100, concurrency=20)
        test_results["tests"]["health"] = self.analyze_results(health_results)
        
        # Test 2: API endpoints under load
        print("\n2️⃣ API Endpoints Under Load (50 requests each)")
        endpoints = ["/api/metrics", "/agents", "/workflows"]
        for endpoint in endpoints:
            results = await self.run_concurrent_requests(endpoint, count=50, concurrency=10)
            test_results["tests"][endpoint] = self.analyze_results(results)
        
        # Test 3: Connection pooling
        connection_pool_pass = await self.test_connection_pooling()
        test_results["tests"]["connection_pooling"] = {"passed": connection_pool_pass}
        
        # Test 4: Circuit breakers (if test endpoint exists)
        # circuit_breaker_pass = await self.test_circuit_breakers()
        # test_results["tests"]["circuit_breakers"] = {"passed": circuit_breaker_pass}
        
        # Calculate overall performance score
        self._calculate_score(test_results)
        
        return test_results
    
    def _calculate_score(self, results: Dict) -> None:
        """Calculate architecture health score based on test results"""
        score = 0
        max_score = 100
        
        # Response time scoring (30 points)
        if "health" in results["tests"]:
            health_metrics = results["tests"]["health"]
            if health_metrics.get("response_times"):
                mean_time = health_metrics["response_times"]["mean_ms"]
                if mean_time < 50:
                    score += 30
                elif mean_time < 100:
                    score += 20
                elif mean_time < 200:
                    score += 10
        
        # Success rate scoring (30 points)
        total_success_rate = []
        for test_name, test_data in results["tests"].items():
            if isinstance(test_data, dict) and "success_rate" in test_data:
                total_success_rate.append(test_data["success_rate"])
        
        if total_success_rate:
            avg_success = statistics.mean(total_success_rate)
            if avg_success >= 99:
                score += 30
            elif avg_success >= 95:
                score += 20
            elif avg_success >= 90:
                score += 10
        
        # Connection pooling (20 points)
        if results["tests"].get("connection_pooling", {}).get("passed"):
            score += 20
        
        # Circuit breakers (20 points)
        if results["tests"].get("circuit_breakers", {}).get("passed"):
            score += 20
        
        results["architecture_score"] = score
        results["max_score"] = max_score
        
        print("\n" + "=" * 60)
        print(f"📊 ARCHITECTURE HEALTH SCORE: {score}/{max_score}")
        
        if score >= 85:
            print("✅ Excellent - System is highly optimized")
        elif score >= 70:
            print("🟡 Good - Some optimizations could be improved")
        else:
            print("🔴 Needs Improvement - Critical optimizations required")
        
        print("=" * 60)


async def main():
    """Run the load test"""
    tester = LoadTester()
    results = await tester.run_comprehensive_load_test()
    
    # Save results
    with open("load_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to load_test_results.json")
    
    # Print summary
    print("\n📈 SUMMARY:")
    for test_name, test_data in results["tests"].items():
        if isinstance(test_data, dict):
            if "success_rate" in test_data:
                print(f"  {test_name}: {test_data['success_rate']:.1f}% success rate")
            elif "passed" in test_data:
                status = "✅ Passed" if test_data["passed"] else "❌ Failed"
                print(f"  {test_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())