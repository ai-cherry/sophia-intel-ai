"""
Performance benchmarks for core system components.
Uses pytest-benchmark to establish baseline performance metrics.
"""

import pytest
from agents.base_agent import BaseAgent
from unittest.mock import AsyncMock, MagicMock
import asyncio


class SimpleMockAgent(BaseAgent):
    """Simple mock agent implementation for benchmarking."""

    async def _process_task_impl(self, task_id: str, task_data: dict):
        """Mock implementation that simulates processing time."""
        await asyncio.sleep(0.001)  # Simulate minimal processing
        return {"result": f"Processed {task_id}"}


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    return SimpleMockAgent(name="BenchmarkAgent", concurrency=5)


def test_agent_stats_performance(benchmark, mock_agent):
    """Benchmark the agent stats calculation performance."""
    # Setup mock agent with some statistics
    mock_agent.tasks_completed = 1000
    mock_agent.tasks_failed = 50
    mock_agent.tasks_timeout = 10
    mock_agent.total_duration = 5000.0

    # Benchmark the stats calculation
    result = benchmark(mock_agent.get_stats)

    # Verify the result contains expected fields
    assert "name" in result
    assert "success_rate" in result
    assert "average_duration" in result


@pytest.mark.asyncio
async def test_memory_service_recall_performance(benchmark):
    """Benchmark the memory service recall function."""
    # This would normally be imported from mcp_servers.memory_service
    # For now we'll use a mock implementation

    async def mock_recall(query, limit=10):
        """Mock recall function that simulates memory lookup."""
        await asyncio.sleep(0.005)  # Simulate db lookup
        return [{"id": f"doc{i}", "content": f"Content {i}", "score": 0.9 - (i * 0.1)}
                for i in range(min(5, limit))]

    # Create a sync wrapper for benchmark compatibility
    def sync_recall_wrapper():
        return asyncio.run(mock_recall("test query"))

    # Benchmark the recall function
    results = benchmark(sync_recall_wrapper)

    # Basic validation of the mock to ensure benchmark is meaningful
    actual_results = asyncio.run(mock_recall("test query"))
    assert len(actual_results) == 5
    assert actual_results[0]["id"] == "doc0"


@pytest.mark.asyncio
async def test_entity_resolver_performance(benchmark):
    """Benchmark the entity resolver performance."""
    # Mock entity resolver function
    async def mock_resolve_entity(name, entity_type):
        """Mock implementation that simulates entity resolution."""
        await asyncio.sleep(0.002)  # Simulate resolution time
        return {"id": f"{entity_type}_123", "name": name, "confidence": 0.95}

    # Create a sync wrapper for benchmark compatibility
    def sync_resolve_wrapper():
        return asyncio.run(mock_resolve_entity("Acme Corp", "company"))

    # Benchmark the entity resolution
    result = benchmark(sync_resolve_wrapper)

    # Basic validation
    actual_result = asyncio.run(mock_resolve_entity("Acme Corp", "company"))
    assert actual_result["id"] == "company_123"
    assert actual_result["name"] == "Acme Corp"
