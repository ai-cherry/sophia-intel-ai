#!/usr/bin/env python3
"""Test script for Sophia-Intel-AI components"""
import asyncio
import sys

sys.path.insert(0, ".")


async def test_monitoring_agents():
    """Test monitoring agents"""
    print("\n=== Testing Monitoring Agents ===")
    try:
        from app.agents.background.monitoring_agents import (
            CostTrackerAgent,
            MemoryGuardAgent,
            PerformanceAgent,
        )

        # Test MemoryGuardAgent
        memory_agent = MemoryGuardAgent()
        metrics = await memory_agent.collect_metrics()
        print(f"✓ MemoryGuardAgent: Collected {len(metrics)} metrics")

        # Test CostTrackerAgent
        cost_agent = CostTrackerAgent()
        cost_agent.track_request("openai", 0.05)
        cost_agent.track_request("anthropic", 0.03)
        metrics = await cost_agent.collect_metrics()
        print(
            f"✓ CostTrackerAgent: Tracked ${sum(m.value for m in metrics):.2f} in costs"
        )

        # Test PerformanceAgent
        perf_agent = PerformanceAgent()
        perf_agent.track_response(120.5, True)
        perf_agent.track_response(85.3, True)
        perf_agent.track_response(150.0, False)
        metrics = await perf_agent.collect_metrics()
        print(f"✓ PerformanceAgent: Collected {len(metrics)} performance metrics")

        return True
    except Exception as e:
        print(f"✗ Monitoring agents test failed: {e}")
        return False


async def test_bridge():
    """Deprecated Artemis bridge test (removed)."""
    print("\n=== Skipping deprecated Artemis bridge test ===")
    return True


async def test_chains():
    """Test composable agent chains"""
    print("\n=== Testing Composable Agent Chains ===")
    try:
        from app.chains.composable_agent_chains import (
            AgentStatus,
            ChainBuilder,
            ChainOrchestrator,
        )

        # Test sequential chain
        chain = ChainBuilder.analyze_and_optimize()
        context = await chain.execute("Test data")
        success_count = sum(
            1 for r in context.results if r.status == AgentStatus.SUCCESS
        )
        print(
            f"✓ Sequential Chain: {success_count}/{len(context.results)} agents succeeded"
        )

        # Test parallel chain
        parallel_chain = ChainBuilder.parallel_analysis()
        context = await parallel_chain.execute("Parallel test")
        print(f"✓ Parallel Chain: Executed {len(context.results)} agents")

        # Test orchestrator
        orchestrator = ChainOrchestrator()
        orchestrator.register_chain("test", ChainBuilder.full_pipeline())
        context = await orchestrator.execute_chain("test", "Orchestrator test")
        metrics = orchestrator.get_performance_metrics()
        print(f"✓ Chain Orchestrator: {metrics['success_rate']:.1f}% success rate")

        return True
    except Exception as e:
        print(f"✗ Chains test failed: {e}")
        return False


async def test_integration():
    """Integration test without Artemis bridge (skipped)."""
    print("\n=== Skipping integration test that depended on Artemis bridge ===")
    return True


async def run_all_tests():
    """Run all component tests"""
    print("=" * 60)
    print("SOPHIA-INTEL-AI COMPONENT QUALITY TESTING")
    print("=" * 60)

    results = []

    # Run individual component tests
    results.append(await test_monitoring_agents())
    results.append(await test_bridge())
    results.append(await test_chains())
    results.append(await test_integration())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    return all(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
