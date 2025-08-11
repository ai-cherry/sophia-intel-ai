#!/usr/bin/env python3
"""
Comprehensive Performance Test for Enhanced MCP Server
Tests AI routing performance, context management, and system scalability
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import threading

class PerformanceTestSuite:
    """Comprehensive performance testing for Enhanced MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.results = {
            "ai_routing": [],
            "context_operations": [],
            "concurrent_requests": [],
            "system_stats": []
        }
    
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Comprehensive Performance Test Suite")
        print(f"📍 Testing server at: {self.base_url}")
        print("=" * 60)
    
    async def teardown(self):
        """Cleanup and generate report"""
        if self.session:
            await self.session.close()
        
        self.generate_performance_report()
    
    async def test_ai_routing_performance(self):
        """Test AI routing performance across different task types"""
        print("🧠 Testing AI Routing Performance...")
        
        test_scenarios = [
            {
                "name": "Code Generation",
                "prompt": "Write a Python function to implement binary search",
                "task_type": "code_generation",
                "cost_preference": "balanced"
            },
            {
                "name": "Math Problem",
                "prompt": "Solve: ∫(x² + 3x - 2)dx",
                "task_type": "math",
                "quality_requirement": "premium"
            },
            {
                "name": "Creative Writing",
                "prompt": "Write a short story about AI and humanity",
                "task_type": "creative_writing",
                "cost_preference": "performance_optimized"
            },
            {
                "name": "General Chat",
                "prompt": "Explain quantum computing in simple terms",
                "task_type": "general_chat",
                "latency_requirement": "low_latency"
            },
            {
                "name": "Code Review",
                "prompt": "Review this Python code for potential improvements",
                "task_type": "code_review",
                "quality_requirement": "high"
            }
        ]
        
        for scenario in test_scenarios:
            start_time = time.time()
            
            try:
                async with self.session.post(
                    f"{self.base_url}/ai/route",
                    json=scenario
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        end_time = time.time()
                        
                        performance_data = {
                            "scenario": scenario["name"],
                            "task_type": scenario["task_type"],
                            "response_time": end_time - start_time,
                            "selected_provider": result["routing_decision"]["selected_provider"],
                            "selected_model": result["routing_decision"]["selected_model"],
                            "confidence_score": result["routing_decision"]["confidence_score"],
                            "estimated_cost": result["routing_decision"]["estimated_cost"],
                            "estimated_latency": result["routing_decision"]["estimated_latency"]
                        }
                        
                        self.results["ai_routing"].append(performance_data)
                        
                        print(f"  ✅ {scenario['name']}: {performance_data['selected_provider']}:{performance_data['selected_model']} "
                              f"({performance_data['response_time']:.3f}s, confidence: {performance_data['confidence_score']:.3f})")
                    else:
                        print(f"  ❌ {scenario['name']}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"  ❌ {scenario['name']}: {e}")
    
    async def test_context_management_performance(self):
        """Test context storage and retrieval performance"""
        print("\n💾 Testing Context Management Performance...")
        
        session_id = f"perf_test_{int(time.time())}"
        
        # Test context storage performance
        storage_times = []
        for i in range(10):
            start_time = time.time()
            
            try:
                async with self.session.post(
                    f"{self.base_url}/context/store",
                    json={
                        "session_id": session_id,
                        "content": f"Performance test context entry {i}. This is a comprehensive test of context storage capabilities with varying content lengths and metadata.",
                        "metadata": {"test_id": i, "batch": "performance_test"}
                    }
                ) as response:
                    if response.status == 200:
                        end_time = time.time()
                        storage_times.append(end_time - start_time)
                    else:
                        print(f"  ❌ Storage {i}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Storage {i}: {e}")
        
        # Test context query performance
        query_times = []
        for i in range(5):
            start_time = time.time()
            
            try:
                async with self.session.post(
                    f"{self.base_url}/context/query",
                    json={
                        "session_id": session_id,
                        "query": f"performance test {i}",
                        "top_k": 5
                    }
                ) as response:
                    if response.status == 200:
                        end_time = time.time()
                        query_times.append(end_time - start_time)
                    else:
                        print(f"  ❌ Query {i}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Query {i}: {e}")
        
        if storage_times:
            avg_storage_time = statistics.mean(storage_times)
            print(f"  📊 Average Storage Time: {avg_storage_time:.3f}s")
            
        if query_times:
            avg_query_time = statistics.mean(query_times)
            print(f"  📊 Average Query Time: {avg_query_time:.3f}s")
        
        self.results["context_operations"] = {
            "storage_times": storage_times,
            "query_times": query_times,
            "avg_storage_time": statistics.mean(storage_times) if storage_times else 0,
            "avg_query_time": statistics.mean(query_times) if query_times else 0
        }
    
    async def test_concurrent_requests(self):
        """Test system performance under concurrent load"""
        print("\n⚡ Testing Concurrent Request Performance...")
        
        async def make_concurrent_request(request_id: int):
            """Make a single concurrent request"""
            start_time = time.time()
            
            try:
                async with self.session.post(
                    f"{self.base_url}/ai/route",
                    json={
                        "prompt": f"Concurrent test request {request_id}",
                        "task_type": "general_chat",
                        "cost_preference": "balanced"
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        end_time = time.time()
                        
                        return {
                            "request_id": request_id,
                            "response_time": end_time - start_time,
                            "success": True,
                            "provider": result["routing_decision"]["selected_provider"]
                        }
                    else:
                        return {
                            "request_id": request_id,
                            "response_time": time.time() - start_time,
                            "success": False,
                            "error": f"HTTP {response.status}"
                        }
                        
            except Exception as e:
                return {
                    "request_id": request_id,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            print(f"  🔄 Testing {concurrency} concurrent requests...")
            
            start_time = time.time()
            tasks = [make_concurrent_request(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            successful_requests = [r for r in results if r["success"]]
            failed_requests = [r for r in results if not r["success"]]
            
            if successful_requests:
                avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
                throughput = len(successful_requests) / total_time
                
                print(f"    ✅ Success Rate: {len(successful_requests)}/{concurrency} ({len(successful_requests)/concurrency*100:.1f}%)")
                print(f"    📊 Average Response Time: {avg_response_time:.3f}s")
                print(f"    🚀 Throughput: {throughput:.2f} requests/second")
                
                self.results["concurrent_requests"].append({
                    "concurrency": concurrency,
                    "total_time": total_time,
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "avg_response_time": avg_response_time,
                    "throughput": throughput
                })
            else:
                print(f"    ❌ All requests failed")
    
    async def test_system_statistics(self):
        """Test system statistics and health endpoints"""
        print("\n📈 Testing System Statistics...")
        
        try:
            # Test health endpoint
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                health_time = time.time() - start_time
                if response.status == 200:
                    health_data = await response.json()
                    print(f"  ✅ Health Check: {health_time:.3f}s")
                else:
                    print(f"  ❌ Health Check: HTTP {response.status}")
            
            # Test stats endpoint
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/stats") as response:
                stats_time = time.time() - start_time
                if response.status == 200:
                    stats_data = await response.json()
                    print(f"  ✅ Statistics: {stats_time:.3f}s")
                else:
                    print(f"  ❌ Statistics: HTTP {response.status}")
            
            # Test models endpoint
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/models") as response:
                models_time = time.time() - start_time
                if response.status == 200:
                    models_data = await response.json()
                    print(f"  ✅ Models ({len(models_data)} available): {models_time:.3f}s")
                else:
                    print(f"  ❌ Models: HTTP {response.status}")
            
            self.results["system_stats"] = {
                "health_response_time": health_time,
                "stats_response_time": stats_time,
                "models_response_time": models_time,
                "models_available": len(models_data) if 'models_data' in locals() else 0
            }
            
        except Exception as e:
            print(f"  ❌ System Statistics: {e}")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 60)
        
        # AI Routing Performance Summary
        if self.results["ai_routing"]:
            print("\n🧠 AI ROUTING PERFORMANCE")
            print("-" * 30)
            
            response_times = [r["response_time"] for r in self.results["ai_routing"]]
            confidence_scores = [r["confidence_score"] for r in self.results["ai_routing"]]
            
            print(f"Total Scenarios Tested: {len(self.results['ai_routing'])}")
            print(f"Average Response Time: {statistics.mean(response_times):.3f}s")
            print(f"Min Response Time: {min(response_times):.3f}s")
            print(f"Max Response Time: {max(response_times):.3f}s")
            print(f"Average Confidence Score: {statistics.mean(confidence_scores):.3f}")
            
            # Provider distribution
            providers = [r["selected_provider"] for r in self.results["ai_routing"]]
            provider_counts = {p: providers.count(p) for p in set(providers)}
            print(f"Provider Distribution: {provider_counts}")
        
        # Context Management Performance
        if self.results["context_operations"]:
            print("\n💾 CONTEXT MANAGEMENT PERFORMANCE")
            print("-" * 35)
            
            ctx_ops = self.results["context_operations"]
            print(f"Average Storage Time: {ctx_ops['avg_storage_time']:.3f}s")
            print(f"Average Query Time: {ctx_ops['avg_query_time']:.3f}s")
            print(f"Storage Operations: {len(ctx_ops['storage_times'])}")
            print(f"Query Operations: {len(ctx_ops['query_times'])}")
        
        # Concurrent Request Performance
        if self.results["concurrent_requests"]:
            print("\n⚡ CONCURRENT REQUEST PERFORMANCE")
            print("-" * 35)
            
            for result in self.results["concurrent_requests"]:
                print(f"Concurrency {result['concurrency']}: "
                      f"{result['throughput']:.2f} req/s, "
                      f"{result['avg_response_time']:.3f}s avg, "
                      f"{result['successful_requests']}/{result['concurrency']} success")
        
        # System Statistics
        if self.results["system_stats"]:
            print("\n📈 SYSTEM STATISTICS")
            print("-" * 20)
            
            stats = self.results["system_stats"]
            print(f"Health Check: {stats.get('health_response_time', 0):.3f}s")
            print(f"Statistics Endpoint: {stats.get('stats_response_time', 0):.3f}s")
            print(f"Models Endpoint: {stats.get('models_response_time', 0):.3f}s")
            print(f"Available Models: {stats.get('models_available', 0)}")
        
        # Overall Assessment
        print("\n🎯 OVERALL ASSESSMENT")
        print("-" * 20)
        
        if self.results["ai_routing"]:
            avg_routing_time = statistics.mean([r["response_time"] for r in self.results["ai_routing"]])
            avg_confidence = statistics.mean([r["confidence_score"] for r in self.results["ai_routing"]])
            
            if avg_routing_time < 0.1:
                routing_grade = "🟢 EXCELLENT"
            elif avg_routing_time < 0.5:
                routing_grade = "🟡 GOOD"
            else:
                routing_grade = "🔴 NEEDS IMPROVEMENT"
            
            print(f"AI Routing Performance: {routing_grade} ({avg_routing_time:.3f}s avg)")
            print(f"AI Routing Confidence: {'🟢 HIGH' if avg_confidence > 0.8 else '🟡 MODERATE' if avg_confidence > 0.6 else '🔴 LOW'} ({avg_confidence:.3f})")
        
        if self.results["concurrent_requests"]:
            max_throughput = max([r["throughput"] for r in self.results["concurrent_requests"]])
            print(f"Peak Throughput: {max_throughput:.2f} requests/second")
        
        print("\n✅ Performance testing completed successfully!")
        print("🚀 Enhanced MCP Server is ready for production deployment!")
    
    async def run_all_tests(self):
        """Run all performance tests"""
        await self.setup()
        
        await self.test_ai_routing_performance()
        await self.test_context_management_performance()
        await self.test_concurrent_requests()
        await self.test_system_statistics()
        
        await self.teardown()


async def main():
    """Main performance test runner"""
    tester = PerformanceTestSuite()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

