#!/usr/bin/env python3
"""
Memory System Performance Test
Tests the performance of the new Mem0 + LangChain hybrid memory system
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/memory_benchmark.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("memory_benchmark")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from memory.mem0_bridge import Mem0Bridge
except ImportError:
    logger.error(
        "Error: Could not import Mem0Bridge. Make sure memory/mem0_bridge.py exists."
    )
    sys.exit(1)


class MemoryBenchmark:
    """Benchmark the memory system performance"""

    def __init__(self, num_memories: int = 100, agent_id: str = "benchmark"):
        """Initialize the benchmark"""
        self.num_memories = num_memories
        self.agent_id = agent_id
        self.bridge = Mem0Bridge()
        self.memories = []
        self.results = {"add_time": 0, "retrieve_time": 0, "precision": 0, "recall": 0}
        logger.info(f"Initialized benchmark with {num_memories} memories")

    def generate_test_memories(self):
        """Generate test memories with varying content and relevance"""
        logger.info("Generating test memories...")

        # Categories of content
        categories = [
            "bug",
            "feature",
            "documentation",
            "refactor",
            "test",
            "performance",
            "security",
            "database",
            "ui",
            "api",
        ]

        # Generate memories with different relevance scores
        for i in range(self.num_memories):
            category = random.choice(categories)
            relevance = random.uniform(0.5, 1.0)

            # More specific content based on category
            if category == "bug":
                content = f"Found a bug in the {random.choice(['authentication', 'authorization', 'validation', 'input handling', 'error handling'])} system related to {random.choice(['null values', 'edge cases', 'race conditions', 'memory leaks', 'exception handling'])}."
            elif category == "feature":
                content = f"Implemented a new {random.choice(['search', 'filter', 'sort', 'export', 'import'])} feature for the {random.choice(['user', 'admin', 'reporting', 'dashboard', 'settings'])} module."
            elif category == "documentation":
                content = f"Updated {random.choice(['API', 'user', 'developer', 'deployment', 'configuration'])} documentation with {random.choice(['examples', 'diagrams', 'troubleshooting steps', 'best practices', 'migration guide'])}."
            elif category == "refactor":
                content = f"Refactored the {random.choice(['authentication', 'data access', 'cache', 'logging', 'validation'])} code to improve {random.choice(['readability', 'performance', 'modularity', 'testability', 'maintainability'])}."
            else:
                content = f"Working on {category} task related to {random.choice(['users', 'accounts', 'reports', 'settings', 'notifications'])}."

            # Add metadata
            metadata = {
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "priority": random.choice(["high", "medium", "low"]),
                "tags": random.sample(
                    [
                        "python",
                        "javascript",
                        "database",
                        "api",
                        "ui",
                        "test",
                        "security",
                    ],
                    k=2,
                ),
            }

            self.memories.append(
                {"content": content, "relevance": relevance, "metadata": metadata}
            )

        logger.info(f"Generated {len(self.memories)} test memories")
        return self.memories

    async def add_memories(self):
        """Add generated memories to the memory system"""
        logger.info("Adding memories to the system...")

        start_time = time.time()
        for memory in self.memories:
            await self.bridge.add(
                agent_id=self.agent_id,
                content=memory["content"],
                relevance=memory["relevance"],
                metadata=memory["metadata"],
            )

        total_time = time.time() - start_time
        avg_time = total_time / len(self.memories)

        self.results["add_time"] = avg_time
        logger.info(
            f"Added {len(self.memories)} memories in {total_time:.2f}s (avg: {avg_time:.4f}s per memory)"
        )
        return avg_time

    async def benchmark_retrieval(self, num_queries: int = 20):
        """Benchmark memory retrieval with random queries"""
        logger.info(f"Benchmarking retrieval with {num_queries} queries...")

        # Generate test queries
        queries = [
            "authentication bug",
            "performance optimization",
            "documentation update",
            "feature implementation",
            "security vulnerability",
            "database issue",
            "user interface",
            "api endpoint",
            "test coverage",
            "refactoring code",
        ]

        # Add more random queries if needed
        while len(queries) < num_queries:
            category = random.choice(
                ["bug", "feature", "documentation", "refactor", "test"]
            )
            element = random.choice(
                ["authentication", "database", "api", "ui", "settings"]
            )
            queries.append(f"{category} {element}")

        # Use only the number of queries requested
        queries = queries[:num_queries]

        # Run benchmark
        total_time = 0
        relevant_results = 0
        total_expected = 0

        for query in queries:
            logger.info(f"Running query: {query}")

            # Count expected results (how many memories should match this query)
            expected = sum(
                1
                for memory in self.memories
                if any(
                    term in memory["content"].lower() for term in query.lower().split()
                )
            )
            total_expected += expected

            # Run query and measure time
            start_time = time.time()
            results = await self.bridge.retrieve(
                agent_id=self.agent_id, query=query, limit=10, include_entities=True
            )
            query_time = time.time() - start_time
            total_time += query_time

            # Count relevant results (how many returned results actually contain query terms)
            query_relevant = sum(
                1
                for r in results["merged_results"]
                if any(term in r["content"].lower() for term in query.lower().split())
            )
            relevant_results += query_relevant

            logger.info(
                f"Query '{query}' returned {len(results['merged_results'])} results ({query_relevant} relevant) in {query_time:.4f}s"
            )

        # Calculate metrics
        avg_time = total_time / len(queries)
        precision = (
            relevant_results / (len(queries) * 10) if queries else 0
        )  # 10 is the limit per query
        recall = relevant_results / total_expected if total_expected > 0 else 0

        self.results["retrieve_time"] = avg_time
        self.results["precision"] = precision
        self.results["recall"] = recall

        logger.info("Retrieval benchmark completed:")
        logger.info(f"  Average retrieval time: {avg_time:.4f}s")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")

        return self.results

    async def cleanup(self):
        """Clean up the test memories"""
        logger.info("Cleaning up test memories...")
        await self.bridge.clear(self.agent_id)
        logger.info("Cleanup complete")


async def main():
    """Run the benchmark"""
    parser = argparse.ArgumentParser(description="Memory System Benchmark")
    parser.add_argument(
        "--memories", type=int, default=100, help="Number of test memories to generate"
    )
    parser.add_argument(
        "--queries", type=int, default=20, help="Number of test queries to run"
    )
    parser.add_argument(
        "--agent", type=str, default="benchmark", help="Agent ID for the benchmark"
    )
    parser.add_argument(
        "--skip-cleanup", action="store_true", help="Skip cleaning up test memories"
    )
    args = parser.parse_args()

    logger.info("Starting memory system benchmark...")

    # Create required directories
    os.makedirs("logs", exist_ok=True)

    # Create and run benchmark
    benchmark = MemoryBenchmark(num_memories=args.memories, agent_id=args.agent)
    benchmark.generate_test_memories()

    try:
        await benchmark.add_memories()
        results = await benchmark.benchmark_retrieval(num_queries=args.queries)

        # Save results
        with open("logs/memory_benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Benchmark results saved to logs/memory_benchmark_results.json")

        # Clean up if not skipped
        if not args.skip_cleanup:
            await benchmark.cleanup()
        else:
            logger.info("Skipping cleanup as requested")

        logger.info("Benchmark completed successfully")
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        # Try to clean up anyway
        if not args.skip_cleanup:
            await benchmark.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
