#!/usr/bin/env python3
"""Security and Performance Testing for Sophia-Intel-AI Components"""
import asyncio
import sys
import time
import tracemalloc

import psutil

sys.path.insert(0, ".")


async def test_memory_leaks():
    """Test for memory leaks in monitoring agents"""
    print("\n=== Memory Leak Testing ===")
    from app.agents.background.monitoring_agents import MemoryGuardAgent

    tracemalloc.start()
    agent = MemoryGuardAgent()

    # Initial snapshot
    snapshot1 = tracemalloc.take_snapshot()

    # Run multiple iterations
    for i in range(100):
        await agent.collect_metrics()

    # Second snapshot
    snapshot2 = tracemalloc.take_snapshot()

    # Check for memory growth
    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    total_growth = sum(stat.size_diff for stat in top_stats[:10])

    print(f"Memory growth after 100 iterations: {total_growth / 1024:.2f} KB")

    # Check if growth is reasonable (less than 1MB)
    if total_growth < 1024 * 1024:
        print("✓ No significant memory leaks detected")
        return True
    else:
        print(f"✗ Potential memory leak: {total_growth / 1024 / 1024:.2f} MB growth")
        return False


async def test_performance_under_load():
    """Test performance under load"""
    print("\n=== Performance Under Load Testing ===")
    from app.chains.composable_agent_chains import ChainBuilder

    chain = ChainBuilder.analyze_and_optimize()

    # Measure execution time under load
    times = []
    for i in range(10):
        start = time.time()
        await chain.execute(f"Load test {i}")
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)
    max_time = max(times)

    print(f"Average execution time: {avg_time:.3f}s")
    print(f"Max execution time: {max_time:.3f}s")

    # Check if performance is acceptable (avg < 3s, max < 5s)
    if avg_time < 3 and max_time < 5:
        print("✓ Performance is acceptable under load")
        return True
    else:
        print("✗ Performance degradation detected")
        return False


async def test_concurrent_execution():
    """Test concurrent execution safety"""
    print("\n=== Concurrent Execution Testing ===")
    from app.chains.composable_agent_chains import ChainBuilder

    chain = ChainBuilder.analyze_and_optimize()

    # Run multiple chains concurrently
    tasks = [chain.execute(f"Concurrent test {i}") for i in range(5)]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]

        if not exceptions:
            print(f"✓ Successfully executed {len(results)} concurrent chains")
            return True
        else:
            print(f"✗ {len(exceptions)} exceptions during concurrent execution")
            for e in exceptions:
                print(f"  - {e}")
            return False
    except Exception as e:
        print(f"✗ Concurrent execution failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and recovery"""
    print("\n=== Error Handling Testing ===")
    from app.chains.composable_agent_chains import AgentStatus, BaseAgent, ChainContext

    class FailingAgent(BaseAgent):
        def __init__(self):
            super().__init__("FailingAgent")
            self.retry_count = 2  # Reduce retries for testing

        async def process(self, input_data, context):
            raise ValueError("Intentional failure")

    # Test with failing agent
    failing_agent = FailingAgent()
    context = ChainContext(initial_input="test")

    result = await failing_agent.execute(context)

    if result.status == AgentStatus.FAILED and result.error:
        print("✓ Errors properly caught and reported")
        return True
    else:
        print("✗ Error handling not working correctly")
        return False


async def test_input_validation():
    """Test input validation and sanitization"""
    print("\n=== Input Validation Testing ===")
    # Artemis bridge removed

    bridge = SophiaArtemisBridge()

    # Test with various potentially problematic inputs
    test_inputs = [
        "",  # Empty string
        "a" * 10000,  # Very long string
        "<script>alert('xss')</script>",  # XSS attempt
        "'; DROP TABLE users; --",  # SQL injection attempt
        {"nested": {"very": {"deep": {"structure": "test"}}}},  # Deep nesting
    ]

    errors = []
    for test_input in test_inputs:
        try:
            if isinstance(test_input, str):
                insight = bridge.translate_to_technical(test_input)
            else:
                insight = bridge.translate_to_business(test_input)
        except Exception as e:
            errors.append(
                (
                    (
                        test_input[:50]
                        if isinstance(test_input, str)
                        else str(test_input)[:50]
                    ),
                    e,
                )
            )

    if not errors:
        print("✓ All inputs handled safely")
        return True
    else:
        print(f"✗ {len(errors)} input validation issues found")
        for inp, err in errors:
            print(f"  - Input '{inp}': {err}")
        return False


async def test_resource_cleanup():
    """Test proper resource cleanup"""
    print("\n=== Resource Cleanup Testing ===")
    from app.agents.background.monitoring_agents import BackgroundAgentManager

    manager = BackgroundAgentManager()

    # Start agents
    await manager.start_all()

    # Wait briefly
    await asyncio.sleep(2)

    # Stop all agents
    await manager.stop_all()

    # Check that all agents are stopped
    all_stopped = all(not agent.running for agent in manager.agents.values())

    if all_stopped:
        print("✓ All resources properly cleaned up")
        return True
    else:
        print("✗ Some agents still running after cleanup")
        return False


async def test_rate_limiting():
    """Test rate limiting and throttling"""
    print("\n=== Rate Limiting Testing ===")
    # Artemis bridge removed

    bridge = SophiaArtemisBridge()

    # Simulate rapid requests
    start = time.time()
    for i in range(50):
        bridge.translate_to_technical(f"Request {i}")

    elapsed = time.time() - start

    # Check cache is being used (should be very fast)
    if elapsed < 1:
        print(f"✓ Cache working effectively ({elapsed:.3f}s for 50 requests)")
        return True
    else:
        print(f"✗ Performance issue: {elapsed:.3f}s for 50 requests")
        return False


async def run_security_performance_tests():
    """Run all security and performance tests"""
    print("=" * 60)
    print("SECURITY AND PERFORMANCE TESTING")
    print("=" * 60)

    results = []

    results.append(await test_memory_leaks())
    results.append(await test_performance_under_load())
    results.append(await test_concurrent_execution())
    results.append(await test_error_handling())
    results.append(await test_input_validation())
    results.append(await test_resource_cleanup())
    results.append(await test_rate_limiting())

    # Summary
    print("\n" + "=" * 60)
    print("SECURITY & PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    # Resource usage summary
    process = psutil.Process()
    print("\nFinal Resource Usage:")
    print(f"  CPU: {process.cpu_percent()}%")
    print(f"  Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    return all(results)


if __name__ == "__main__":
    success = asyncio.run(run_security_performance_tests())
    sys.exit(0 if success else 1)
