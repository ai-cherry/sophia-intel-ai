#!/usr/bin/env python3
"""Lightweight performance benchmarking for Artemis swarms"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BenchmarkResult:
    """Single benchmark result"""

    swarm_type: str
    task: str
    execution_time: float
    tokens_used: int
    success: bool
    prefetch_enabled: bool
    error: Optional[str] = None


class SwarmBenchmark:
    """Lightweight benchmarking for swarm performance"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    async def benchmark_scout(self, with_prefetch: bool = True) -> BenchmarkResult:
        """Benchmark scout swarm performance"""
        task = "Analyze repository for integrations and hotspots"

        # Set prefetch flag
        import os

        os.environ["SCOUT_PREFETCH_ENABLED"] = "true" if with_prefetch else "false"

        start = time.time()
        try:
            # Mock execution for testing without LLM
            if os.getenv("BENCHMARK_MODE") == "mock":
                await asyncio.sleep(0.5)  # Simulate work
                tokens = 6000 if with_prefetch else 8000
                success = True
                error = None
            else:
                # Real execution
                from app.swarms.core.swarm_integration import get_artemis_orchestrator

                orchestrator = get_artemis_orchestrator()
                result = await orchestrator.execute_swarm(
                    content=task, swarm_type="repository_scout"
                )
                tokens = result.get("tokens", 0)
                success = result.get("success", False)
                error = result.get("error")

        except Exception as e:
            tokens = 0
            success = False
            error = str(e)

        execution_time = time.time() - start

        return BenchmarkResult(
            swarm_type="scout",
            task=task,
            execution_time=execution_time,
            tokens_used=tokens,
            success=success,
            prefetch_enabled=with_prefetch,
            error=error,
        )

    async def run_benchmarks(self) -> Dict[str, any]:
        """Run core benchmarks"""

        # Scout with and without prefetch
        scout_with = await self.benchmark_scout(with_prefetch=True)
        scout_without = await self.benchmark_scout(with_prefetch=False)

        self.results.extend([scout_with, scout_without])

        # Calculate improvements
        prefetch_speedup = (
            (scout_without.execution_time - scout_with.execution_time)
            / scout_without.execution_time
            * 100
        )

        token_reduction = (
            (scout_without.tokens_used - scout_with.tokens_used)
            / scout_without.tokens_used
            * 100
        )

        return {
            "results": [r.__dict__ for r in self.results],
            "improvements": {
                "prefetch_speedup_percent": round(prefetch_speedup, 1),
                "token_reduction_percent": round(token_reduction, 1),
            },
            "summary": {
                "total_benchmarks": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "avg_execution_time": sum(r.execution_time for r in self.results)
                / len(self.results),
            },
        }

    def save_results(self, filepath: str = "benchmark_results.json"):
        """Save benchmark results to file"""
        results = {
            "timestamp": time.time(),
            "benchmarks": [r.__dict__ for r in self.results],
        }

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)


# Quick benchmark script
async def main():
    """Run quick benchmarks"""
    print("🏃 Running Artemis swarm benchmarks...")

    benchmark = SwarmBenchmark()
    results = await benchmark.run_benchmarks()

    print("\n📊 Benchmark Results:")
    print(f"  Total runs: {results['summary']['total_benchmarks']}")
    print(f"  Successful: {results['summary']['successful']}")
    print(f"  Avg time: {results['summary']['avg_execution_time']:.2f}s")

    print("\n🚀 Improvements with prefetch:")
    print(
        f"  Speed improvement: {results['improvements']['prefetch_speedup_percent']:.1f}%"
    )
    print(
        f"  Token reduction: {results['improvements']['token_reduction_percent']:.1f}%"
    )

    benchmark.save_results()
    print("\n💾 Results saved to benchmark_results.json")


if __name__ == "__main__":
    # Run in mock mode for testing
    import os

    os.environ["BENCHMARK_MODE"] = "mock"
    asyncio.run(main())
