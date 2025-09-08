"""
Load Testing for MCP Connection Pool
Tests connection pool performance and resilience under load
"""

import asyncio
import random
import time
from datetime import datetime

import pytest


@pytest.mark.load
@pytest.mark.asyncio
class TestMCPConnectionPoolLoad:
    """Load tests for MCP connection pool management"""

    async def test_connection_pool_saturation(
        self, mcp_connection_manager, artemis_mcp_servers, benchmark_timer
    ):
        """Test connection pool behavior when saturated"""
        # Arrange
        max_connections = 10
        num_requests = 100
        mcp_connection_manager.max_connections = max_connections

        active_connections = []
        rejected_requests = []
        successful_requests = []

        async def simulate_connection(request_id):
            # Try to acquire connection
            if len(active_connections) >= max_connections:
                rejected_requests.append(request_id)
                raise ConnectionError(
                    f"Connection pool exhausted for request {request_id}"
                )

            # Simulate connection use
            connection_id = f"conn-{request_id}"
            active_connections.append(connection_id)

            try:
                # Simulate work with connection
                await asyncio.sleep(random.uniform(0.01, 0.1))
                successful_requests.append(request_id)
                return {"request_id": request_id, "status": "success"}
            finally:
                # Release connection
                if connection_id in active_connections:
                    active_connections.remove(connection_id)

        mcp_connection_manager.execute.side_effect = simulate_connection

        # Act
        with benchmark_timer:
            tasks = [
                mcp_connection_manager.execute(f"request-{i}")
                for i in range(num_requests)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = [r for r in results if isinstance(r, dict)]
        failed = [r for r in results if isinstance(r, Exception)]

        # Assert
        assert len(successful) > 0
        assert len(successful) + len(failed) == num_requests

        print("\nConnection Pool Saturation Test:")
        print(f"  Max connections: {max_connections}")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {len(successful)}")
        print(f"  Rejected: {len(rejected_requests)}")
        print(f"  Duration: {benchmark_timer.elapsed:.2f}s")
        print(f"  Throughput: {len(successful)/benchmark_timer.elapsed:.2f} req/sec")

    async def test_connection_reuse_efficiency(
        self, mcp_connection_manager, shared_mcp_cluster, benchmark_timer
    ):
        """Test efficient reuse of connections in the pool"""
        # Arrange
        num_connections = 5
        num_requests = 50
        connection_usage = {}

        async def track_connection_reuse(request_id):
            # Simulate connection assignment
            connection_id = f"conn-{hash(request_id) % num_connections}"

            if connection_id not in connection_usage:
                connection_usage[connection_id] = []

            connection_usage[connection_id].append(request_id)

            # Simulate work
            await asyncio.sleep(0.02)

            return {
                "request_id": request_id,
                "connection_id": connection_id,
                "reuse_count": len(connection_usage[connection_id]),
            }

        mcp_connection_manager.execute.side_effect = track_connection_reuse

        # Act
        with benchmark_timer:
            tasks = [
                mcp_connection_manager.execute(f"reuse-{i}")
                for i in range(num_requests)
            ]
            results = await asyncio.gather(*tasks)

        # Analyze connection reuse
        avg_reuse = sum(len(uses) for uses in connection_usage.values()) / len(
            connection_usage
        )
        max_reuse = max(len(uses) for uses in connection_usage.values())
        min_reuse = min(len(uses) for uses in connection_usage.values())

        # Assert
        assert avg_reuse >= num_requests / num_connections * 0.8  # Good distribution
        assert max_reuse - min_reuse <= num_requests * 0.3  # Balanced usage

        print("\nConnection Reuse Efficiency Test:")
        print(f"  Total connections: {len(connection_usage)}")
        print(f"  Total requests: {num_requests}")
        print(f"  Average reuse: {avg_reuse:.1f}")
        print(f"  Max reuse: {max_reuse}")
        print(f"  Min reuse: {min_reuse}")
        print(f"  Duration: {benchmark_timer.elapsed:.2f}s")

    async def test_multi_server_load_distribution(
        self,
        mcp_router,
        artemis_mcp_servers,
        sophia_mcp_servers,
        shared_mcp_cluster,
        benchmark_timer,
    ):
        """Test load distribution across multiple MCP servers"""
        # Arrange
        num_requests = 200
        server_load = {
            "artemis": {"filesystem": 0, "code_analysis": 0},
            "sophia": {"web_search": 0},
            "shared": {"database": 0},
        }

        async def route_to_server(domain, operation, server_type):
            # Track server load
            if domain in server_load and server_type in server_load[domain]:
                server_load[domain][server_type] += 1

            # Simulate server processing
            if server_type == "filesystem":
                server = artemis_mcp_servers["filesystem"]
            elif server_type == "code_analysis":
                server = artemis_mcp_servers["code_analysis"]
            elif server_type == "web_search":
                server = sophia_mcp_servers["web_search"]
            else:
                # Use shared cluster for database
                return await shared_mcp_cluster.execute_with_load_balancing(
                    operation, {}, "round_robin"
                )

            return await server.execute(operation)

        mcp_router.route_request.side_effect = route_to_server

        # Act
        with benchmark_timer:
            tasks = []

            # Create mixed workload
            for i in range(num_requests):
                if i % 4 == 0:
                    # Artemis filesystem operation
                    task = mcp_router.route_request("artemis", "read", "filesystem")
                elif i % 4 == 1:
                    # Artemis code analysis operation
                    task = mcp_router.route_request(
                        "artemis", "analyze", "code_analysis"
                    )
                elif i % 4 == 2:
                    # Sophia web search operation
                    task = mcp_router.route_request("sophia", "search", "web_search")
                else:
                    # Shared database operation
                    task = mcp_router.route_request("shared", "query", "database")

                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]

        # Calculate load distribution
        total_load = sum(sum(loads.values()) for loads in server_load.values())

        # Assert
        assert len(successful) >= num_requests * 0.9  # 90% success rate
        assert total_load >= num_requests * 0.75  # Most requests were tracked

        print("\nMulti-Server Load Distribution Test:")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print("  Server load distribution:")
        for domain, servers in server_load.items():
            for server, load in servers.items():
                percentage = (load / total_load * 100) if total_load > 0 else 0
                print(f"    {domain}.{server}: {load} ({percentage:.1f}%)")
        print(f"  Duration: {benchmark_timer.elapsed:.2f}s")
        print(f"  Throughput: {len(successful)/benchmark_timer.elapsed:.2f} req/sec")

    async def test_connection_recovery_under_load(
        self, mcp_connection_manager, artemis_mcp_servers, benchmark_timer
    ):
        """Test connection recovery mechanisms under continuous load"""
        # Arrange
        num_requests = 100
        failure_injection_points = [20, 40, 60, 80]  # Inject failures at these points
        reconnect_attempts = []

        async def simulate_with_failures(request_id):
            request_num = int(request_id.split("-")[-1])

            # Inject failures at specific points
            if request_num in failure_injection_points:
                # Simulate connection failure
                reconnect_attempts.append(request_num)

                # Attempt reconnection
                success = await mcp_connection_manager.reconnect()
                if not success:
                    raise ConnectionError(
                        f"Failed to reconnect at request {request_num}"
                    )

            # Normal operation
            await asyncio.sleep(0.01)
            return {"request_id": request_id, "status": "success"}

        mcp_connection_manager.execute.side_effect = simulate_with_failures
        mcp_connection_manager.reconnect.return_value = (
            True  # Always succeed reconnection
        )

        # Act
        with benchmark_timer:
            tasks = [
                mcp_connection_manager.execute(f"recovery-{i}")
                for i in range(num_requests)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = [r for r in results if isinstance(r, dict)]
        failed = [r for r in results if isinstance(r, Exception)]

        # Assert
        assert len(successful) >= num_requests * 0.95  # High recovery rate
        assert len(reconnect_attempts) == len(failure_injection_points)

        print("\nConnection Recovery Under Load Test:")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print(f"  Failures injected: {len(failure_injection_points)}")
        print(f"  Reconnection attempts: {len(reconnect_attempts)}")
        print(f"  Recovery rate: {len(successful)/num_requests:.1%}")
        print(f"  Duration: {benchmark_timer.elapsed:.2f}s")


@pytest.mark.load
@pytest.mark.spike
@pytest.mark.asyncio
class TestMCPConnectionSpike:
    """Spike tests for sudden load increases"""

    async def test_traffic_spike_handling(
        self, mcp_connection_manager, shared_mcp_cluster, benchmark_timer
    ):
        """Test system response to sudden traffic spikes"""
        # Arrange
        baseline_load = 10  # requests per second
        spike_load = 100  # requests per second during spike
        spike_duration = 5  # seconds

        metrics = {
            "baseline": {"requests": 0, "successful": 0, "failed": 0, "latencies": []},
            "spike": {"requests": 0, "successful": 0, "failed": 0, "latencies": []},
            "recovery": {"requests": 0, "successful": 0, "failed": 0, "latencies": []},
        }

        async def execute_request(request_id, phase):
            start = time.time()
            try:
                result = await shared_mcp_cluster.execute_with_load_balancing(
                    "operation", {"id": request_id}
                )
                latency = time.time() - start

                metrics[phase]["successful"] += 1
                metrics[phase]["latencies"].append(latency)

                return result
            except Exception as e:
                metrics[phase]["failed"] += 1
                raise e
            finally:
                metrics[phase]["requests"] += 1

        # Act
        print("\nTraffic Spike Test:")
        print(f"  Baseline: {baseline_load} req/sec")
        print(f"  Spike: {spike_load} req/sec for {spike_duration}s")

        # Phase 1: Baseline load
        print("  Phase 1: Baseline load...")
        baseline_tasks = []
        for i in range(baseline_load * 5):  # 5 seconds of baseline
            task = execute_request(f"baseline-{i}", "baseline")
            baseline_tasks.append(task)
            await asyncio.sleep(1 / baseline_load)

        # Phase 2: Spike load
        print("  Phase 2: Traffic spike...")
        spike_start = time.time()
        spike_tasks = []

        with benchmark_timer:
            for i in range(spike_load * spike_duration):
                task = execute_request(f"spike-{i}", "spike")
                spike_tasks.append(task)

                # Faster submission rate for spike
                if i % spike_load == 0:
                    await asyncio.sleep(1)

        spike_duration_actual = benchmark_timer.elapsed

        # Phase 3: Recovery (back to baseline)
        print("  Phase 3: Recovery phase...")
        recovery_tasks = []
        for i in range(baseline_load * 5):  # 5 seconds of recovery
            task = execute_request(f"recovery-{i}", "recovery")
            recovery_tasks.append(task)
            await asyncio.sleep(1 / baseline_load)

        # Wait for all tasks to complete
        await asyncio.gather(
            *baseline_tasks, *spike_tasks, *recovery_tasks, return_exceptions=True
        )

        # Analyze results
        for phase, data in metrics.items():
            if data["latencies"]:
                avg_latency = sum(data["latencies"]) / len(data["latencies"])
                max_latency = max(data["latencies"])
                success_rate = data["successful"] / max(data["requests"], 1)

                print(f"\n  {phase.capitalize()} Phase:")
                print(f"    Requests: {data['requests']}")
                print(f"    Success rate: {success_rate:.1%}")
                print(f"    Avg latency: {avg_latency:.3f}s")
                print(f"    Max latency: {max_latency:.3f}s")

        # Assert
        # System should maintain reasonable success rate even during spike
        spike_success_rate = metrics["spike"]["successful"] / max(
            metrics["spike"]["requests"], 1
        )
        assert spike_success_rate >= 0.7  # At least 70% success during spike

        # Recovery should return to baseline performance
        if metrics["recovery"]["latencies"] and metrics["baseline"]["latencies"]:
            recovery_avg = sum(metrics["recovery"]["latencies"]) / len(
                metrics["recovery"]["latencies"]
            )
            baseline_avg = sum(metrics["baseline"]["latencies"]) / len(
                metrics["baseline"]["latencies"]
            )
            assert (
                recovery_avg <= baseline_avg * 1.5
            )  # Recovery latency within 150% of baseline

    async def test_connection_pool_elasticity(
        self, mcp_connection_manager, benchmark_timer
    ):
        """Test connection pool's ability to scale up and down"""
        # Arrange
        min_connections = 2
        max_connections = 20

        connection_counts = []
        timestamps = []

        async def monitor_pool_size():
            """Monitor connection pool size over time"""
            for _ in range(60):  # Monitor for 60 seconds
                current_connections = mcp_connection_manager.active_connections
                connection_counts.append(current_connections)
                timestamps.append(datetime.utcnow())
                await asyncio.sleep(1)

        async def generate_variable_load():
            """Generate variable load pattern"""
            patterns = [
                ("low", 5, 10),  # 5 requests/sec for 10 seconds
                ("high", 50, 10),  # 50 requests/sec for 10 seconds
                ("low", 5, 10),  # Back to low
                ("spike", 100, 5),  # Spike
                ("low", 5, 15),  # Extended low period
            ]

            for phase, rate, duration in patterns:
                print(f"  Load phase: {phase} ({rate} req/sec for {duration}s)")

                tasks = []
                for _ in range(rate * duration):

                    async def make_request():
                        await asyncio.sleep(random.uniform(0.01, 0.1))
                        return {"status": "success"}

                    task = make_request()
                    tasks.append(task)

                    if len(tasks) % rate == 0:
                        await asyncio.sleep(1)

                await asyncio.gather(*tasks, return_exceptions=True)

        # Mock dynamic pool sizing
        mcp_connection_manager.active_connections = min_connections

        def update_pool_size():
            # Simulate elastic scaling based on load
            current = mcp_connection_manager.active_connections
            if random.random() > 0.5:  # Simulate scaling decision
                if current < max_connections:
                    mcp_connection_manager.active_connections = min(
                        current + 2, max_connections
                    )
                elif current > min_connections:
                    mcp_connection_manager.active_connections = max(
                        current - 1, min_connections
                    )
            return mcp_connection_manager.active_connections

        mcp_connection_manager.get_connection.side_effect = lambda: update_pool_size()

        # Act
        print("\nConnection Pool Elasticity Test:")
        print(f"  Min connections: {min_connections}")
        print(f"  Max connections: {max_connections}")

        with benchmark_timer:
            monitor_task = asyncio.create_task(monitor_pool_size())
            load_task = asyncio.create_task(generate_variable_load())

            await load_task
            monitor_task.cancel()

        # Analyze elasticity
        if connection_counts:
            min_observed = min(connection_counts)
            max_observed = max(connection_counts)
            avg_connections = sum(connection_counts) / len(connection_counts)

            # Calculate scaling events
            scaling_events = 0
            for i in range(1, len(connection_counts)):
                if connection_counts[i] != connection_counts[i - 1]:
                    scaling_events += 1

            print("\nElasticity Results:")
            print(f"  Min observed: {min_observed}")
            print(f"  Max observed: {max_observed}")
            print(f"  Average: {avg_connections:.1f}")
            print(f"  Scaling events: {scaling_events}")
            print(f"  Duration: {benchmark_timer.elapsed:.2f}s")

            # Assert
            assert min_observed >= min_connections
            assert max_observed <= max_connections
            assert scaling_events > 0  # Pool should have scaled
