"""
End-to-End tests for Concurrent Operations
Tests 8 concurrent task execution, resource contention handling,
and load balancing between orchestrators
"""

import asyncio
import random
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.artemis.unified_factory import ArtemisUnifiedFactory
from app.mcp.connection_manager import ConnectionState, MCPConnectionManager
from app.sophia.unified_factory import SophiaUnifiedFactory


class TestConcurrentOperations:
    """Test suite for concurrent operations across the consolidated system"""

    @pytest.fixture
    def artemis_factory(self):
        """Create Artemis factory"""
        with patch("app.artemis.unified_factory.store_memory"):
            return ArtemisUnifiedFactory()

    @pytest.fixture
    def sophia_factory(self):
        """Create Sophia factory"""
        with patch("app.sophia.unified_factory.store_memory"):
            return SophiaUnifiedFactory()

    @pytest.fixture
    def connection_manager(self):
        """Create connection manager"""
        with patch("asyncio.create_task"):
            return MCPConnectionManager()

    # ==============================================================================
    # 8 CONCURRENT TASK EXECUTION TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_eight_concurrent_task_limit_enforcement(
        self, artemis_factory, sophia_factory
    ):
        """Test that both factories enforce the 8 concurrent task limit"""
        # Fill Artemis factory to capacity
        artemis_tasks = []
        for i in range(8):
            acquired = await artemis_factory._acquire_task_slot()
            assert acquired is True
            artemis_tasks.append(i)

        assert artemis_factory._concurrent_tasks == 8

        # 9th task should fail
        acquired = await artemis_factory._acquire_task_slot()
        assert acquired is False

        # Similarly for Sophia
        sophia_tasks = []
        for i in range(8):
            acquired = await sophia_factory._acquire_task_slot()
            assert acquired is True
            sophia_tasks.append(i)

        assert sophia_factory._concurrent_tasks == 8

        # 9th task should fail
        acquired = await sophia_factory._acquire_task_slot()
        assert acquired is False

        # Clean up
        for _ in range(8):
            await artemis_factory._release_task_slot()
            await sophia_factory._release_task_slot()

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation_across_domains(
        self, artemis_factory, sophia_factory
    ):
        """Test concurrent agent creation in both domains"""

        async def create_artemis_agents():
            agents = []
            for template in [
                "code_reviewer",
                "security_auditor",
                "performance_optimizer",
            ]:
                agent_id = await artemis_factory.create_technical_agent(template)
                agents.append(agent_id)
            return agents

        async def create_sophia_agents():
            agents = []
            for template in [
                "sales_pipeline_analyst",
                "revenue_forecaster",
                "client_success_manager",
            ]:
                agent_id = await sophia_factory.create_business_agent(template)
                agents.append(agent_id)
            return agents

        # Create agents concurrently
        artemis_task = asyncio.create_task(create_artemis_agents())
        sophia_task = asyncio.create_task(create_sophia_agents())

        artemis_agents, sophia_agents = await asyncio.gather(artemis_task, sophia_task)

        # Verify all agents created
        assert len(artemis_agents) == 3
        assert len(sophia_agents) == 3

        # Verify no ID collisions
        all_ids = artemis_agents + sophia_agents
        assert len(set(all_ids)) == 6

    @pytest.mark.asyncio
    async def test_concurrent_mission_execution(self, artemis_factory):
        """Test concurrent mission execution with task limit"""
        missions = []

        with patch.object(
            artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
        ) as mock_phase:
            mock_phase.return_value = {"success": True}

            # Create multiple missions concurrently
            async def execute_mission(mission_type, target):
                result = await artemis_factory.execute_mission(
                    mission_type, target=target
                )
                return result

            # Execute missions up to limit
            tasks = []
            for i in range(8):
                task = asyncio.create_task(
                    execute_mission("rapid_response", f"/target_{i}")
                )
                tasks.append(task)

            # All should succeed
            results = await asyncio.gather(*tasks)
            assert all(r["success"] for r in results)

            # 9th mission should be queued
            ninth_result = await artemis_factory.execute_mission(
                "rapid_response", "/target_9"
            )

            # Should be queued
            if isinstance(ninth_result, str):
                assert ninth_result.startswith("queued_")
            else:
                assert ninth_result.get("queued") is True

    @pytest.mark.asyncio
    async def test_concurrent_business_task_execution(self, sophia_factory):
        """Test concurrent business task execution"""
        # Create multiple agents
        agent_ids = []
        for _ in range(3):
            agent_id = await sophia_factory.create_business_agent(
                "sales_pipeline_analyst"
            )
            agent_ids.append(agent_id)

        # Execute tasks concurrently
        async def execute_task(agent_id, task_name):
            result = await sophia_factory.execute_business_task(agent_id, task_name)
            return result

        tasks = []
        for i, agent_id in enumerate(agent_ids):
            task = asyncio.create_task(
                execute_task(agent_id, f"Analyze pipeline segment {i}")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r["success"] for r in results)
        assert sophia_factory.business_metrics["analyses_completed"] == 3

    # ==============================================================================
    # RESOURCE CONTENTION HANDLING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_connection_pool_contention(self, connection_manager):
        """Test handling of connection pool contention"""
        # Configure limited pool
        pool = connection_manager.pools["shared_database"]
        pool.config.max_size = 3  # Limit pool size

        # Mock connection acquisition
        connections = []
        for i in range(3):
            conn = MagicMock()
            conn.server_name = "shared_database"
            conn.id = f"conn_{i}"
            connections.append(conn)

        # Create contention by requesting more connections than available
        async def request_connection(delay):
            await asyncio.sleep(delay)
            try:
                conn = await connection_manager.get_connection("shared_database")
                await asyncio.sleep(0.1)  # Hold connection briefly
                await connection_manager.release_connection(conn)
                return True
            except Exception:return False

        # Mock the pool's acquire method to simulate contention
        call_count = 0

        async def mock_acquire():
            nonlocal call_count
            if call_count < 3:
                call_count += 1
                conn = connections[call_count - 1]
                return conn
            else:
                raise asyncio.TimeoutError("Pool exhausted")

        pool.acquire = mock_acquire

        # Request connections concurrently
        tasks = []
        for i in range(5):  # More than pool size
            task = asyncio.create_task(request_connection(i * 0.01))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should succeed, some may timeout
        successes = sum(1 for r in results if r is True)
        assert successes <= 3  # No more than pool size

    @pytest.mark.asyncio
    async def test_task_queue_under_load(self, artemis_factory):
        """Test task queueing behavior under load"""
        # Fill all task slots
        for _ in range(8):
            await artemis_factory._acquire_task_slot()

        # Queue multiple tasks
        queued_ids = []
        for i in range(5):
            task = {
                "type": "test_task",
                "priority": random.choice(["low", "medium", "high"]),
                "data": f"task_{i}",
            }
            queue_id = await artemis_factory.queue_task(task)
            queued_ids.append(queue_id)

        assert len(artemis_factory._task_queue) == 5
        assert all(id.startswith("queued_") for id in queued_ids)

        # Release a slot and verify queue processing
        await artemis_factory._release_task_slot()
        assert artemis_factory._concurrent_tasks == 7

        # In real implementation, queued task would be processed
        # For test, verify queue state
        assert len(artemis_factory._task_queue) == 5  # Still queued

    @pytest.mark.asyncio
    async def test_circuit_breaker_under_concurrent_load(self, connection_manager):
        """Test circuit breaker behavior under concurrent load"""
        breaker = connection_manager.circuit_breakers["artemis_filesystem"]

        # Simulate concurrent failures
        async def failing_operation():
            raise Exception("Service unavailable")

        # Execute concurrent failing operations
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(
                breaker.async_call(failing_operation),
            )
            tasks.append(task)

        # Gather results (all should fail)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should be exceptions
        assert all(isinstance(r, Exception) for r in results)

        # Circuit should be open after threshold
        assert breaker.state == ConnectionState.OPEN
        assert breaker.failure_count >= breaker.config.failure_threshold

    @pytest.mark.asyncio
    async def test_resource_isolation_between_domains(
        self, artemis_factory, sophia_factory
    ):
        """Test that resource exhaustion in one domain doesn't affect the other"""
        # Exhaust Artemis resources
        for _ in range(8):
            await artemis_factory._acquire_task_slot()

        assert artemis_factory._concurrent_tasks == 8

        # Sophia should still be able to operate
        sophia_agent = await sophia_factory.create_business_agent(
            "sales_pipeline_analyst"
        )
        assert sophia_agent is not None

        # Sophia can execute tasks
        result = await sophia_factory.execute_business_task(
            sophia_agent, "Independent analysis"
        )
        assert result["success"] is True

        # Verify isolation
        assert artemis_factory._concurrent_tasks == 8  # Still full
        assert sophia_factory._concurrent_tasks < 8  # Has capacity

    # ==============================================================================
    # LOAD BALANCING TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_load_balancing_between_factories(
        self, artemis_factory, sophia_factory
    ):
        """Test load distribution between Artemis and Sophia factories"""
        load_metrics = {
            "artemis_tasks": 0,
            "sophia_tasks": 0,
            "artemis_time": 0,
            "sophia_time": 0,
        }

        async def artemis_work():
            start = time.time()
            agent = await artemis_factory.create_technical_agent("code_reviewer")
            load_metrics["artemis_tasks"] += 1
            load_metrics["artemis_time"] += time.time() - start
            return agent

        async def sophia_work():
            start = time.time()
            agent = await sophia_factory.create_business_agent("sales_pipeline_analyst")
            load_metrics["sophia_tasks"] += 1
            load_metrics["sophia_time"] += time.time() - start
            return agent

        # Create mixed workload
        tasks = []
        for i in range(10):
            if i % 2 == 0:
                task = asyncio.create_task(artemis_work())
            else:
                task = asyncio.create_task(sophia_work())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify balanced distribution
        assert load_metrics["artemis_tasks"] == 5
        assert load_metrics["sophia_tasks"] == 5
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_dynamic_load_rebalancing(self, connection_manager):
        """Test dynamic load rebalancing in connection pools"""
        # Track connection distribution
        connection_counts = {
            "artemis_filesystem": 0,
            "artemis_code_analysis": 0,
            "sophia_web_search": 0,
            "sophia_analytics": 0,
        }

        async def get_and_release_connection(server_name):
            try:
                # Mock successful acquisition
                mock_conn = MagicMock()
                mock_conn.server_name = server_name
                connection_manager.pools[server_name].acquire = AsyncMock(
                    return_value=mock_conn
                )

                conn = await connection_manager.get_connection(server_name)
                connection_counts[server_name] += 1
                await connection_manager.release_connection(conn)
                return True
            except Exception:return False

        # Create varied load pattern
        tasks = []
        servers = list(connection_counts.keys())
        weights = [0.4, 0.2, 0.3, 0.1]  # Different load weights

        for _ in range(20):
            server = random.choices(servers, weights=weights)[0]
            task = asyncio.create_task(get_and_release_connection(server))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify load distribution roughly matches weights
        total = sum(connection_counts.values())
        assert total > 0

        # Check distribution (with tolerance for randomness)
        assert connection_counts["artemis_filesystem"] >= 4  # ~40%
        assert connection_counts["sophia_web_search"] >= 2  # ~30%

    @pytest.mark.asyncio
    async def test_orchestrator_coordination_under_load(
        self, artemis_factory, sophia_factory
    ):
        """Test orchestrator coordination when both are under load"""
        coordination_events = []

        async def artemis_orchestrated_task():
            with patch.object(
                artemis_factory, "_execute_mission_phase", new_callable=AsyncMock
            ) as mock:
                mock.return_value = {"success": True}
                result = await artemis_factory.execute_mission(
                    "rapid_response", target="/orchestrated/artemis"
                )
                coordination_events.append(("artemis", datetime.now(timezone.utc)))
                return result

        async def sophia_orchestrated_task():
            team_id = await sophia_factory.create_business_team("sales_intelligence")
            result = await sophia_factory.execute_business_task(
                team_id, "Orchestrated business analysis"
            )
            coordination_events.append(("sophia", datetime.now(timezone.utc)))
            return result

        # Execute orchestrated tasks concurrently
        tasks = []
        for i in range(6):
            if i % 2 == 0:
                task = asyncio.create_task(artemis_orchestrated_task())
            else:
                task = asyncio.create_task(sophia_orchestrated_task())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify both orchestrators handled tasks
        artemis_events = [e for e in coordination_events if e[0] == "artemis"]
        sophia_events = [e for e in coordination_events if e[0] == "sophia"]

        assert len(artemis_events) == 3
        assert len(sophia_events) == 3
        assert all(r["success"] for r in results)

    # ==============================================================================
    # STRESS AND PERFORMANCE TESTS
    # ==============================================================================

    @pytest.mark.asyncio
    async def test_sustained_concurrent_operations(
        self, artemis_factory, sophia_factory
    ):
        """Test system behavior under sustained concurrent load"""
        duration_seconds = 2
        operations_count = {"artemis": 0, "sophia": 0}
        errors_count = {"artemis": 0, "sophia": 0}

        async def continuous_artemis_operations():
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    agent = await artemis_factory.create_technical_agent(
                        "code_reviewer"
                    )
                    operations_count["artemis"] += 1
                    await asyncio.sleep(0.1)  # Small delay between operations
                except Exception:
                    errors_count["artemis"] += 1

        async def continuous_sophia_operations():
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    agent = await sophia_factory.create_business_agent(
                        "sales_pipeline_analyst"
                    )
                    operations_count["sophia"] += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    errors_count["sophia"] += 1

        # Run sustained operations
        tasks = [
            asyncio.create_task(continuous_artemis_operations()),
            asyncio.create_task(continuous_sophia_operations()),
        ]

        await asyncio.gather(*tasks)

        # Verify sustained operation
        assert operations_count["artemis"] > 10
        assert operations_count["sophia"] > 10
        assert errors_count["artemis"] == 0
        assert errors_count["sophia"] == 0

    @pytest.mark.asyncio
    async def test_burst_load_handling(self, artemis_factory):
        """Test handling of burst load scenarios"""
        burst_size = 20
        burst_results = []

        async def burst_operation(index):
            try:
                # Try to acquire slot
                if await artemis_factory._acquire_task_slot():
                    await asyncio.sleep(0.05)  # Simulate work
                    await artemis_factory._release_task_slot()
                    return ("success", index)
                else:
                    # Queue the task
                    task_id = await artemis_factory.queue_task(
                        {"type": "burst", "index": index}
                    )
                    return ("queued", task_id)
            except Exception as e:
                return ("error", str(e))

        # Create burst of operations
        tasks = []
        for i in range(burst_size):
            task = asyncio.create_task(burst_operation(i))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Analyze results
        successes = [r for r in results if r[0] == "success"]
        queued = [r for r in results if r[0] == "queued"]
        errors = [r for r in results if r[0] == "error"]

        # Should handle burst gracefully
        assert len(successes) <= 8  # Max concurrent
        assert len(queued) >= burst_size - 8  # Rest queued
        assert len(errors) == 0  # No errors

    @pytest.mark.asyncio
    async def test_graceful_degradation_under_overload(self, connection_manager):
        """Test graceful degradation when system is overloaded"""
        # Simulate overload by making services unhealthy
        connection_manager.health_status["artemis_filesystem"] = False
        connection_manager.health_status["artemis_code_analysis"] = False

        # System should still function with remaining services
        connection_manager.health_status["shared_database"] = True

        # Mock successful connection for healthy service
        mock_conn = MagicMock()
        mock_conn.server_name = "shared_database"
        connection_manager.pools["shared_database"].acquire = AsyncMock(
            return_value=mock_conn
        )

        # Should still get connection to healthy service
        conn = await connection_manager.get_connection("shared_database")
        assert conn is not None

        # Unhealthy services should be rejected gracefully
        with pytest.raises(Exception) as exc_info:
            await connection_manager.get_connection("artemis_filesystem")
        assert "unhealthy" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_recovery_from_concurrent_failures(self, connection_manager):
        """Test system recovery from multiple concurrent failures"""
        # Simulate multiple circuit breakers opening
        breakers_to_test = [
            "artemis_filesystem",
            "sophia_web_search",
            "shared_database",
        ]

        # Force all circuits open
        for name in breakers_to_test:
            breaker = connection_manager.circuit_breakers[name]
            breaker.state = ConnectionState.OPEN
            breaker.failure_count = breaker.config.failure_threshold

        # All should be open
        for name in breakers_to_test:
            assert (
                connection_manager.circuit_breakers[name].state == ConnectionState.OPEN
            )

        # Simulate recovery timeout
        for name in breakers_to_test:
            breaker = connection_manager.circuit_breakers[name]
            breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=70)

        # Mock successful operations for recovery
        async def success_operation():
            return "success"

        # Attempt operations to trigger recovery
        for name in breakers_to_test:
            breaker = connection_manager.circuit_breakers[name]
            # Should transition to HALF_OPEN
            result = await breaker.async_call(success_operation)
            assert result == "success"
            assert breaker.state == ConnectionState.HALF_OPEN

        # Complete recovery with more successes
        for name in breakers_to_test:
            breaker = connection_manager.circuit_breakers[name]
            for _ in range(breaker.config.success_threshold):
                await breaker.async_call(success_operation)

            # Should be fully recovered
            assert breaker.state == ConnectionState.CLOSED
