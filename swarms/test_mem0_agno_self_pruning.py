#!/usr/bin/env python3
"""
Unit tests for Mem0-Agno Self-Pruning Redis Optimization System
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis

# Import the system under test
from mem0_agno_self_pruning import MemoryOptimizationSwarm, RedisPruningAgent


class TestRedisPruningAgent:
    """Unit tests for RedisPruningAgent"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_client = Mock(spec=redis.Redis)
        mock_client.info.return_value = {
            "used_memory": 1024 * 1024 * 100,  # 100MB
            "used_memory_human": "100M",
            "used_memory_peak": 1024 * 1024 * 150,  # 150MB
            "mem_fragmentation_ratio": 1.2,
        }
        mock_client.keys.return_value = [b"test_key_1", b"test_key_2", b"test_key_3"]
        mock_client.ttl.return_value = -1  # No expiration
        mock_client.memory_usage.return_value = 1024 * 1024 * 10  # 10MB
        mock_client.object.return_value = 7200  # 2 hours idle
        mock_client.delete.return_value = 1
        return mock_client

    @pytest.fixture
    def mock_mem0_client(self):
        """Mock Mem0 client for testing"""
        mock_client = Mock()
        mock_client.add = Mock()
        return mock_client

    @pytest.fixture
    def pruning_agent(self, mock_redis_client, mock_mem0_client):
        """Create RedisPruningAgent instance for testing"""
        return RedisPruningAgent(mock_redis_client, mock_mem0_client)

    @pytest.mark.asyncio
    async def test_analyze_redis_usage(self, pruning_agent, mock_redis_client):
        """Test Redis usage analysis"""
        # Setup mock responses
        mock_redis_client.info.side_effect = [
            {
                "used_memory": 1024 * 1024 * 100,
                "used_memory_human": "100M",
                "used_memory_peak": 1024 * 1024 * 150,
                "mem_fragmentation_ratio": 1.2,
            },
            {"db0": {"keys": 1000, "expires": 100}},
        ]

        # Test usage analysis
        usage_data = await pruning_agent.analyze_redis_usage()

        # Verify results
        assert usage_data["used_memory"] == 1024 * 1024 * 100
        assert usage_data["used_memory_human"] == "100M"
        assert usage_data["total_keys"] == 1000
        assert "timestamp" in usage_data

        # Verify Redis calls
        assert mock_redis_client.info.call_count == 2

    @pytest.mark.asyncio
    async def test_identify_pruning_candidates(self, pruning_agent, mock_redis_client):
        """Test identification of pruning candidates"""
        # Setup mock responses
        mock_redis_client.keys.return_value = [b"large_key_1", b"large_key_2", b"small_key"]

        def mock_memory_usage(key):
            if b"large" in key:
                return 1024 * 1024 * 200  # 200MB
            return 1024 * 100  # 100KB

        def mock_object_idletime(key):
            if b"large" in key:
                return 7200  # 2 hours idle
            return 300  # 5 minutes idle

        mock_redis_client.memory_usage.side_effect = mock_memory_usage
        mock_redis_client.object.side_effect = mock_object_idletime
        mock_redis_client.ttl.return_value = -1

        # Test candidate identification
        candidates = await pruning_agent.identify_pruning_candidates(threshold_mb=100)

        # Verify results
        assert len(candidates) == 2  # Only large keys should be candidates
        assert all("large" in candidate["key"] for candidate in candidates)
        assert all(candidate["memory_usage"] > 100 * 1024 * 1024 for candidate in candidates)
        assert all(candidate["last_access"] > 3600 for candidate in candidates)

    @pytest.mark.asyncio
    async def test_execute_pruning(self, pruning_agent, mock_redis_client, mock_mem0_client):
        """Test pruning execution"""
        # Setup test candidates
        candidates = [
            {
                "key": "test_key_1",
                "memory_usage": 1024 * 1024 * 100,  # 100MB
                "last_access": 7200,
                "ttl": -1,
            },
            {
                "key": "test_key_2",
                "memory_usage": 1024 * 1024 * 50,  # 50MB
                "last_access": 3600,
                "ttl": -1,
            },
        ]

        # Mock successful deletion
        mock_redis_client.delete.return_value = 1

        # Test pruning execution
        result = await pruning_agent.execute_pruning(candidates, max_prune=2)

        # Verify results
        assert len(result["pruned_keys"]) == 2
        assert result["memory_saved"] == 1024 * 1024 * 150  # 150MB total
        assert result["cost_savings"] > 0
        assert "timestamp" in result

        # Verify Redis and Mem0 calls
        assert mock_redis_client.delete.call_count == 2
        assert mock_mem0_client.add.call_count == 2

    @pytest.mark.asyncio
    async def test_store_pruning_metadata(self, pruning_agent, mock_mem0_client):
        """Test storing pruning metadata"""
        # Test data
        key = "test_key"
        metadata = {"memory_usage": 1024 * 1024 * 100, "last_access": 7200, "ttl": -1}

        # Test metadata storage
        await pruning_agent.store_pruning_metadata(key, metadata)

        # Verify Mem0 call
        mock_mem0_client.add.assert_called_once()
        call_args = mock_mem0_client.add.call_args
        assert "messages" in call_args.kwargs
        assert "metadata" in call_args.kwargs


class TestMemoryOptimizationSwarm:
    """Unit tests for MemoryOptimizationSwarm"""

    @pytest.fixture
    def mock_redis_url(self):
        """Mock Redis URL for testing"""
        return "${REDIS_URL}"

    @pytest.fixture
    def mock_mem0_api_key(self):
        """Mock Mem0 API key for testing"""
        return "test_mem0_api_key"

    @pytest.mark.asyncio
    async def test_swarm_initialization(self):
        """Test swarm initialization"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url") as mock_redis:
                with patch("mem0_agno_self_pruning.MemoryClient") as mock_mem0:
                    # Setup mocks
                    mock_redis_client = Mock()
                    mock_redis.return_value = mock_redis_client
                    mock_mem0_client = Mock()
                    mock_mem0.return_value = mock_mem0_client

                    # Test initialization
                    swarm = MemoryOptimizationSwarm()

                    # Verify initialization
                    assert swarm.redis_client == mock_redis_client
                    assert swarm.mem0_client == mock_mem0_client
                    assert not swarm.running

    @pytest.mark.asyncio
    async def test_create_swarm(self):
        """Test swarm creation"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url"):
                with patch("mem0_agno_self_pruning.MemoryClient"):
                    swarm = MemoryOptimizationSwarm()

                    # Test swarm creation
                    created_swarm = await swarm.create_swarm()

                    # Verify swarm properties
                    assert created_swarm.name == "redis_optimization_swarm"
                    assert len(created_swarm.agents) == 1
                    assert created_swarm.max_iterations == 15

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_skip_low_usage(self):
        """Test optimization cycle skipping when usage is low"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url"):
                with patch("mem0_agno_self_pruning.MemoryClient"):
                    swarm = MemoryOptimizationSwarm()

                    # Mock low memory usage
                    mock_agent = Mock()
                    mock_agent.analyze_redis_usage = AsyncMock(
                        return_value={
                            "used_memory": 1024 * 1024 * 50,  # 50MB
                            "used_memory_peak": 1024 * 1024 * 200,  # 200MB
                            "total_keys": 1000,
                        }
                    )

                    swarm.swarm = Mock()
                    swarm.swarm.agents = [mock_agent]

                    # Test optimization cycle
                    result = await swarm.run_optimization_cycle()

                    # Verify skipped due to low usage
                    assert result["status"] == "skipped"
                    assert "usage_ratio" in result
                    assert result["usage_ratio"] < 0.8

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_no_candidates(self):
        """Test optimization cycle with no pruning candidates"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url"):
                with patch("mem0_agno_self_pruning.MemoryClient"):
                    swarm = MemoryOptimizationSwarm()

                    # Mock high memory usage but no candidates
                    mock_agent = Mock()
                    mock_agent.analyze_redis_usage = AsyncMock(
                        return_value={
                            "used_memory": 1024 * 1024 * 180,  # 180MB
                            "used_memory_peak": 1024 * 1024 * 200,  # 200MB
                            "total_keys": 1000,
                        }
                    )
                    mock_agent.identify_pruning_candidates = AsyncMock(return_value=[])

                    swarm.swarm = Mock()
                    swarm.swarm.agents = [mock_agent]

                    # Test optimization cycle
                    result = await swarm.run_optimization_cycle()

                    # Verify no candidates found
                    assert result["status"] == "no_candidates"
                    assert "usage_data" in result

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_success(self):
        """Test successful optimization cycle"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url"):
                with patch("mem0_agno_self_pruning.MemoryClient"):
                    swarm = MemoryOptimizationSwarm()

                    # Mock successful optimization
                    mock_agent = Mock()
                    mock_agent.analyze_redis_usage = AsyncMock(
                        return_value={
                            "used_memory": 1024 * 1024 * 180,  # 180MB
                            "used_memory_peak": 1024 * 1024 * 200,  # 200MB
                            "total_keys": 1000,
                        }
                    )
                    mock_agent.identify_pruning_candidates = AsyncMock(
                        return_value=[{"key": "test_key", "memory_usage": 1024 * 1024 * 50}]
                    )
                    mock_agent.execute_pruning = AsyncMock(
                        return_value={
                            "pruned_keys": ["test_key"],
                            "memory_saved": 1024 * 1024 * 50,
                            "cost_savings": 5.0,
                        }
                    )
                    mock_agent.pruning_stats = {
                        "keys_pruned": 1,
                        "memory_saved": 1024 * 1024 * 50,
                        "cost_savings": 5.0,
                    }

                    swarm.swarm = Mock()
                    swarm.swarm.agents = [mock_agent]

                    # Test optimization cycle
                    result = await swarm.run_optimization_cycle()

                    # Verify successful optimization
                    assert result["status"] == "completed"
                    assert "usage_data" in result
                    assert "pruning_result" in result
                    assert "stats" in result

    def test_stop_optimization(self):
        """Test stopping optimization"""
        with patch.dict(os.environ, {"REDIS_URL": "${REDIS_URL}"}):
            with patch("redis.from_url"):
                with patch("mem0_agno_self_pruning.MemoryClient"):
                    swarm = MemoryOptimizationSwarm()
                    swarm.running = True

                    # Test stopping
                    swarm.stop_optimization()

                    # Verify stopped
                    assert not swarm.running


class TestErrorHandling:
    """Test error handling in the Redis optimization system"""

    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Test handling Redis connection errors"""
        with patch("redis.from_url") as mock_redis:
            # Mock Redis connection error
            mock_redis.side_effect = redis.ConnectionError("Connection failed")

            with patch("mem0_agno_self_pruning.MemoryClient"):
                swarm = MemoryOptimizationSwarm()

                # The swarm should handle the error gracefully
                assert swarm.redis_client is not None  # Should still create client

    @pytest.mark.asyncio
    async def test_mem0_initialization_error(self):
        """Test handling Mem0 initialization errors"""
        with patch.dict(os.environ, {}, clear=True):  # Clear MEM0_API_KEY
            with patch("redis.from_url"):
                swarm = MemoryOptimizationSwarm()

                # Should handle missing API key gracefully
                assert swarm.mem0_client is None

    @pytest.mark.asyncio
    async def test_pruning_agent_error_handling(self):
        """Test error handling in pruning agent"""
        mock_redis_client = Mock(spec=redis.Redis)
        mock_redis_client.info.side_effect = redis.RedisError("Redis error")

        mock_mem0_client = Mock()

        agent = RedisPruningAgent(mock_redis_client, mock_mem0_client)

        # Test that errors are handled gracefully
        usage_data = await agent.analyze_redis_usage()
        assert usage_data == {}  # Should return empty dict on error


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
