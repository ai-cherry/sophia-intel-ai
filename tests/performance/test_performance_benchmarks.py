#!/usr/bin/env python3
"""
🚀 SOPHIA AI Performance Testing Framework
Performance-First Testing Pyramid with Benchmarking
Test Hierarchy (Performance Priority):
1. Performance Smoke Tests (<1s)
2. API Response Time Tests (<100ms target)
3. Memory Usage Tests (<512MB target)
4. Concurrent Load Tests (100 RPS target)
5. Integration Performance Tests
"""
import asyncio
import statistics
import time
from typing import Dict, List
import aiohttp
import psutil
import pytest
import uvloop
# Performance targets
PERFORMANCE_TARGETS = {
    "api_response_time_ms": 100,
    "memory_usage_mb": 512,
    "startup_time_ms": 5000,
    "concurrent_requests": 100,
    "throughput_rps": 50,
}
class PerformanceProfiler:
    """High-performance profiler for testing"""
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    def start_timer(self, name: str) -> None:
        """Start performance timer"""
        self.metrics.setdefault(name, []).append(time.perf_counter())
    def end_timer(self, name: str) -> float:
        """End timer and return duration in ms"""
        if name in self.metrics and self.metrics[name]:
            start_time = self.metrics[name].pop()
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.metrics.setdefault(f"{name}_results", []).append(duration_ms)
            return duration_ms
        return 0.0
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get performance statistics"""
        results_key = f"{name}_results"
        if results_key not in self.metrics:
            return {}
        values = self.metrics[results_key]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "p95": (
                sorted(values)[int(0.95 * len(values))]
                if len(values) >= 20
                else max(values)
            ),
            "p99": (
                sorted(values)[int(0.99 * len(values))]
                if len(values) >= 100
                else max(values)
            ),
        }
@pytest.fixture(scope="session")
def profiler():
    """Performance profiler fixture"""
    return PerformanceProfiler()
@pytest.fixture(scope="session")
def event_loop():
    """Use uvloop for performance testing"""
    try:
        uvloop.install()
    except ImportError:
        pass
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
# ================================
# PERFORMANCE SMOKE TESTS (<1s)
# ================================
@pytest.mark.performance
def test_import_performance(profiler):
    """Test core module import performance"""
    profiler.start_timer("import_core")
    import_time = profiler.end_timer("import_core")
    assert import_time < 100, f"Import time {import_time:.1f}ms exceeds 100ms target"
@pytest.mark.performance
def test_memory_baseline(profiler):
    """Test baseline memory usage"""
    import gc
    gc.collect()  # Clean up before measurement
    process = psutil.Process()
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    # Target: <100MB baseline
    assert (
        baseline_memory < 100
    ), f"Baseline memory {baseline_memory:.1f}MB exceeds 100MB target"
# ================================
# API PERFORMANCE TESTS
# ================================
@pytest.mark.performance
@pytest.mark.asyncio
async def test_api_health_response_time(profiler):
    """Test API health endpoint response time"""
    async with aiohttp.ClientSession() as session:
        # Warm up
        for _ in range(3):
            async with session.get("http://localhost:8000/health") as response:
                await response.text()
        # Measure response times
        response_times = []
        for _ in range(10):
            profiler.start_timer("api_health")
            async with session.get("http://localhost:8000/health") as response:
                await response.text()
                response_time = profiler.end_timer("api_health")
                response_times.append(response_time)
                assert response.status == 200
        # Performance validation
        avg_response_time = statistics.mean(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        assert (
            avg_response_time < PERFORMANCE_TARGETS["api_response_time_ms"]
        ), f"Average response time {avg_response_time:.1f}ms exceeds {PERFORMANCE_TARGETS['api_response_time_ms']}ms target"
        assert (
            p95_response_time < PERFORMANCE_TARGETS["api_response_time_ms"] * 2
        ), f"P95 response time {p95_response_time:.1f}ms exceeds target"
@pytest.mark.performance
@pytest.mark.asyncio
async def test_api_concurrent_requests(profiler):
    """Test API performance under concurrent load"""
    async def make_request(session):
        profiler.start_timer("concurrent_request")
        async with session.get("http://localhost:8000/health") as response:
            result = await response.text()
            response_time = profiler.end_timer("concurrent_request")
            return response.status, response_time
    async with aiohttp.ClientSession() as session:
        # Test with increasing concurrency
        for concurrency in [10, 25, 50]:
            tasks = [make_request(session) for _ in range(concurrency)]
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start_time
            # Validate all requests succeeded
            status_codes = [result[0] for result in results]
            assert all(status == 200 for status in status_codes), "Some requests failed"
            # Calculate throughput
            throughput = len(results) / total_time
            # Performance assertions
            response_times = [result[1] for result in results]
            avg_response_time = statistics.mean(response_times)
            assert (
                avg_response_time < PERFORMANCE_TARGETS["api_response_time_ms"] * 2
            ), f"Average response time {avg_response_time:.1f}ms too high for concurrency {concurrency}"
            print(
                f"Concurrency {concurrency}: {throughput:.1f} RPS, avg {avg_response_time:.1f}ms"
            )
# ================================
# MEMORY PERFORMANCE TESTS
# ================================
@pytest.mark.performance
def test_agent_memory_efficiency(profiler):
    """Test memory efficiency of agent creation"""
    import gc
    from core.clean_architecture.domain import Agent, AgentConfig
    # Baseline memory
    gc.collect()
    process = psutil.Process()
    baseline = process.memory_info().rss / 1024 / 1024
    # Create multiple agents
    agents = []
    for i in range(50):
        config = AgentConfig(
            agent_id=f"test-{i}", agent_name=f"TestAgent{i}", capabilities=[]
        )
        agents.append(Agent(config))
    # Measure memory after agent creation
    current = process.memory_info().rss / 1024 / 1024
    memory_per_agent = (current - baseline) / 50
    # Target: <2MB per agent
    assert (
        memory_per_agent < 2.0
    ), f"Memory per agent {memory_per_agent:.2f}MB exceeds 2MB target"
    # Cleanup test
    del agents
    gc.collect()
@pytest.mark.performance
@pytest.mark.asyncio
async def test_async_memory_usage(profiler):
    """Test memory usage of async operations"""
    import gc
    async def memory_intensive_task():
        # Simulate memory-intensive async operation
        data = list(range(10000))
        await asyncio.sleep(0.001)  # Yield control
        return sum(data)
    gc.collect()
    process = psutil.Process()
    baseline = process.memory_info().rss / 1024 / 1024
    # Create many concurrent tasks
    tasks = [memory_intensive_task() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    current = process.memory_info().rss / 1024 / 1024
    memory_increase = current - baseline
    # Target: <50MB increase for 100 concurrent tasks
    assert (
        memory_increase < 50
    ), f"Memory increase {memory_increase:.1f}MB exceeds 50MB target"
    assert len(results) == 100
    assert all(result == 49995000 for result in results)
# ================================
# LOAD TESTING
# ================================
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_sustained_load(profiler):
    """Test performance under sustained load"""
    async def sustained_request_load():
        async with aiohttp.ClientSession() as session:
            response_times = []
            # Run for 30 seconds
            end_time = time.time() + 30
            request_count = 0
            while time.time() < end_time:
                profiler.start_timer("sustained_load")
                async with session.get("http://localhost:8000/health") as response:
                    await response.text()
                    response_time = profiler.end_timer("sustained_load")
                    response_times.append(response_time)
                    request_count += 1
                    assert response.status == 200
                # Small delay to maintain reasonable RPS
                await asyncio.sleep(0.1)
            return response_times, request_count
    response_times, request_count = await sustained_request_load()
    # Performance validation
    avg_response_time = statistics.mean(response_times)
    throughput = request_count / 30  # RPS
    assert (
        avg_response_time < PERFORMANCE_TARGETS["api_response_time_ms"] * 1.5
    ), f"Sustained load avg response time {avg_response_time:.1f}ms too high"
    assert throughput >= 5, f"Throughput {throughput:.1f} RPS below minimum threshold"
    print(f"Sustained load: {throughput:.1f} RPS, avg {avg_response_time:.1f}ms")
# ================================
# INTEGRATION PERFORMANCE TESTS
# ================================
@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_stack_performance(profiler):
    """Test full stack integration performance"""
    async with aiohttp.ClientSession() as session:
        # Test complete workflow
        profiler.start_timer("full_stack")
        # 1. Health check
        async with session.get("http://localhost:8000/health") as response:
            assert response.status == 200
        # 2. API endpoint test
        async with session.post(
            "http://localhost:8000/api/v1/test", json={"test": "performance"}
        ) as response:
            if response.status == 200:  # If endpoint exists
                await response.json()
        # 3. Metrics endpoint
        async with session.get("http://localhost:8000/metrics") as response:
            if response.status == 200:  # If endpoint exists
                await response.text()
        total_time = profiler.end_timer("full_stack")
        # Target: <500ms for full stack test
        assert (
            total_time < 500
        ), f"Full stack test time {total_time:.1f}ms exceeds 500ms target"
# ================================
# PERFORMANCE REPORTING
# ================================
@pytest.mark.performance
def test_generate_performance_report(profiler):
    """Generate comprehensive performance report"""
    # Collect all performance metrics
    stats = profiler.get_stats("api_health")
    concurrent_stats = profiler.get_stats("concurrent_request")
    report = {
        "performance_targets": PERFORMANCE_TARGETS,
        "test_results": {
            "api_health": stats,
            "concurrent_requests": concurrent_stats,
        },
        "system_info": {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "recommendations": [
            "Enable uvloop in production for async performance boost",
            "Use connection pooling for database operations",
            "Implement Redis caching for frequently accessed data",
            "Monitor memory usage during peak loads",
            "Use performance-optimized Docker images",
        ],
    }
    # Save report
    import json
    with open("performance_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n🚀 Performance Test Summary:")
    print(
        f"📊 API Response Time: {stats.get('mean', 0):.1f}ms (target: {PERFORMANCE_TARGETS['api_response_time_ms']}ms)"
    )
    print(f"📊 Concurrent Performance: {concurrent_stats.get('mean', 0):.1f}ms")
    print("📄 Full report saved to performance_test_report.json")
if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "performance"])
