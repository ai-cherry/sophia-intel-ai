#!/usr/bin/env python3
"""
KEDA Load Testing Suite for AI Workload Scaling
Tests the autoscaling response to various AI workload patterns
Target: Verify scaling from baseline to target within 9 seconds
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import redis
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""

    redis_host: str = "redis.artemis-system.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    prometheus_url: str = "http://prometheus.monitoring.svc.cluster.local:9090"
    namespace_artemis: str = "artemis-system"
    namespace_sophia: str = "sophia-system"
    target_scaling_time: int = 9  # Target scaling time in seconds
    baseline_scaling_time: int = 60  # Baseline scaling time
    test_duration: int = 300  # Test duration in seconds

    # Load patterns
    burst_multiplier: float = 3.0
    gradual_increase_rate: float = 1.5
    wave_amplitude: int = 20
    wave_period: int = 60


class KEDALoadTester:
    """Main load testing class for KEDA autoscaling"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.k8s_apps_v1: Optional[client.AppsV1Api] = None
        self.k8s_core_v1: Optional[client.CoreV1Api] = None
        self.metrics: Dict[str, List[float]] = {
            "scaling_times": [],
            "queue_lengths": [],
            "replica_counts": [],
            "processing_rates": [],
        }
        self.start_time = time.time()

    async def setup(self):
        """Initialize connections and clients"""
        try:
            # Redis connection
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info("Redis connection established")

            # Kubernetes client
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()

            self.k8s_apps_v1 = client.AppsV1Api()
            self.k8s_core_v1 = client.CoreV1Api()
            logger.info("Kubernetes client initialized")

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    async def generate_artemis_load(self, pattern: str = "burst") -> None:
        """Generate load on Artemis task queue"""
        logger.info(f"Generating Artemis load with pattern: {pattern}")

        if pattern == "burst":
            await self._burst_load()
        elif pattern == "gradual":
            await self._gradual_load()
        elif pattern == "wave":
            await self._wave_load()
        elif pattern == "mixed":
            await self._mixed_load()
        else:
            raise ValueError(f"Unknown load pattern: {pattern}")

    async def _burst_load(self) -> None:
        """Generate sudden burst of tasks"""
        base_load = 100
        burst_load = int(base_load * self.config.burst_multiplier)

        # Add burst of tasks
        tasks = [f"task_{i}_{time.time()}" for i in range(burst_load)]
        for task in tasks:
            self.redis_client.rpush(
                "artemis:task:queue",
                json.dumps(
                    {
                        "id": task,
                        "type": "ai_processing",
                        "priority": random.randint(1, 5),
                        "created_at": datetime.now().isoformat(),
                    }
                ),
            )

        logger.info(f"Added {burst_load} tasks to queue (burst)")
        await asyncio.sleep(1)

    async def _gradual_load(self) -> None:
        """Generate gradually increasing load"""
        initial_load = 10
        steps = 10

        for step in range(steps):
            current_load = int(initial_load * (self.config.gradual_increase_rate**step))
            tasks = [f"task_{i}_{step}_{time.time()}" for i in range(current_load)]

            for task in tasks:
                self.redis_client.rpush(
                    "artemis:task:queue",
                    json.dumps(
                        {
                            "id": task,
                            "type": "ai_processing",
                            "priority": 3,
                            "created_at": datetime.now().isoformat(),
                        }
                    ),
                )

            logger.info(f"Added {current_load} tasks (gradual step {step})")
            await asyncio.sleep(5)

    async def _wave_load(self) -> None:
        """Generate wave pattern load"""
        base_load = 50

        for i in range(self.config.wave_period):
            # Sine wave pattern
            import math

            wave_value = math.sin(2 * math.pi * i / self.config.wave_period)
            current_load = int(base_load + self.config.wave_amplitude * wave_value)

            tasks = [f"task_wave_{i}_{time.time()}" for _ in range(max(1, current_load))]

            for task in tasks:
                self.redis_client.rpush(
                    "artemis:task:queue",
                    json.dumps(
                        {
                            "id": task,
                            "type": "ai_processing",
                            "priority": 3,
                            "created_at": datetime.now().isoformat(),
                        }
                    ),
                )

            await asyncio.sleep(1)

    async def _mixed_load(self) -> None:
        """Generate mixed pattern load"""
        patterns = ["burst", "gradual", "wave"]
        for _ in range(3):
            pattern = random.choice(patterns)
            if pattern == "burst":
                await self._burst_load()
            elif pattern == "gradual":
                await self._gradual_load()
            else:
                await self._wave_load()
            await asyncio.sleep(10)

    async def generate_sophia_metrics_load(self) -> None:
        """Generate synthetic metrics for Sophia Prometheus scaler"""
        logger.info("Generating Sophia metrics load")

        async with aiohttp.ClientSession() as session:
            # Push metrics to Prometheus pushgateway if available
            pushgateway_url = "http://pushgateway.monitoring.svc.cluster.local:9091"

            for i in range(100):
                # Generate varying processing rates
                processing_rate = random.uniform(50, 500)

                metrics_data = f"""
                # TYPE sophia_analytics_events_processed_total counter
                sophia_analytics_events_processed_total {{job="sophia-analytics"}} {processing_rate * i}
                # TYPE sophia_model_memory_usage gauge
                sophia_model_memory_usage {{job="sophia-analytics"}} {random.uniform(60, 90)}
                """

                try:
                    async with session.post(
                        f"{pushgateway_url}/metrics/job/sophia-load-test",
                        data=metrics_data,
                        headers={"Content-Type": "text/plain"},
                    ) as response:
                        if response.status == 200:
                            logger.debug(f"Pushed metrics: rate={processing_rate}")
                except Exception as e:
                    logger.warning(f"Failed to push metrics: {e}")

                await asyncio.sleep(1)

    async def measure_scaling_performance(self) -> Dict[str, Any]:
        """Measure actual scaling performance"""
        logger.info("Measuring scaling performance")

        initial_replicas = {}
        final_replicas = {}
        scaling_times = {}

        deployments = [
            ("artemis-worker", self.config.namespace_artemis),
            ("sophia-analytics", self.config.namespace_sophia),
            ("ai-workload-processor", self.config.namespace_sophia),
        ]

        # Record initial state
        for deployment_name, namespace in deployments:
            try:
                deployment = self.k8s_apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=namespace
                )
                initial_replicas[deployment_name] = deployment.status.replicas or 0
                logger.info(
                    f"{deployment_name}: initial replicas = {initial_replicas[deployment_name]}"
                )
            except Exception as e:
                logger.error(f"Failed to read deployment {deployment_name}: {e}")

        # Generate load
        load_start = time.time()
        await asyncio.gather(
            self.generate_artemis_load("burst"), self.generate_sophia_metrics_load()
        )

        # Monitor scaling
        max_wait = 60  # Maximum wait time
        check_interval = 1  # Check every second
        elapsed = 0

        while elapsed < max_wait:
            all_scaled = True

            for deployment_name, namespace in deployments:
                try:
                    deployment = self.k8s_apps_v1.read_namespaced_deployment(
                        name=deployment_name, namespace=namespace
                    )
                    current_replicas = deployment.status.replicas or 0

                    if deployment_name not in final_replicas:
                        final_replicas[deployment_name] = current_replicas

                    # Check if scaling occurred
                    if current_replicas > initial_replicas[deployment_name]:
                        if deployment_name not in scaling_times:
                            scaling_times[deployment_name] = elapsed
                            logger.info(
                                f"{deployment_name}: scaled to {current_replicas} replicas in {elapsed}s"
                            )
                    else:
                        all_scaled = False

                    final_replicas[deployment_name] = max(
                        final_replicas[deployment_name], current_replicas
                    )

                except Exception as e:
                    logger.error(f"Failed to check deployment {deployment_name}: {e}")

            if all_scaled and len(scaling_times) == len(deployments):
                break

            await asyncio.sleep(check_interval)
            elapsed = time.time() - load_start

        # Calculate metrics
        avg_scaling_time = (
            sum(scaling_times.values()) / len(scaling_times) if scaling_times else float("inf")
        )
        improvement = (
            (
                (self.config.baseline_scaling_time - avg_scaling_time)
                / self.config.baseline_scaling_time
                * 100
            )
            if avg_scaling_time < float("inf")
            else 0
        )

        results = {
            "initial_replicas": initial_replicas,
            "final_replicas": final_replicas,
            "scaling_times": scaling_times,
            "average_scaling_time": avg_scaling_time,
            "improvement_percentage": improvement,
            "target_met": avg_scaling_time <= self.config.target_scaling_time,
            "timestamp": datetime.now().isoformat(),
        }

        self.metrics["scaling_times"].append(avg_scaling_time)

        return results

    async def verify_circuit_breaker(self) -> Dict[str, Any]:
        """Test circuit breaker functionality"""
        logger.info("Testing circuit breaker")

        # Generate rapid scaling events
        events_generated = 0
        circuit_breaker_triggered = False

        for _ in range(10):  # Try to generate 10 events quickly
            await self.generate_artemis_load("burst")
            events_generated += 1

            # Check if circuit breaker triggered (would see HPA takeover)
            await asyncio.sleep(6)  # Wait 6 seconds between bursts

            # Query Prometheus for circuit breaker status
            async with aiohttp.ClientSession() as session:
                query = "rate(keda_scaled_object_events_total[1m])"
                try:
                    async with session.get(
                        f"{self.config.prometheus_url}/api/v1/query", params={"query": query}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data["data"]["result"]:
                                rate = float(data["data"]["result"][0]["value"][1])
                                if rate > 3:
                                    circuit_breaker_triggered = True
                                    logger.info(f"Circuit breaker triggered at {rate} events/min")
                                    break
                except Exception as e:
                    logger.error(f"Failed to query Prometheus: {e}")

        return {
            "events_generated": events_generated,
            "circuit_breaker_triggered": circuit_breaker_triggered,
            "test_passed": circuit_breaker_triggered,
            "timestamp": datetime.now().isoformat(),
        }

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive load test suite"""
        logger.info("Starting comprehensive KEDA load test")

        await self.setup()

        test_results = {
            "start_time": datetime.now().isoformat(),
            "config": self.config.__dict__,
            "tests": {},
        }

        # Test 1: Burst load scaling
        logger.info("Test 1: Burst load scaling")
        test_results["tests"]["burst_scaling"] = await self.measure_scaling_performance()
        await asyncio.sleep(30)  # Cool down

        # Test 2: Circuit breaker
        logger.info("Test 2: Circuit breaker verification")
        test_results["tests"]["circuit_breaker"] = await self.verify_circuit_breaker()
        await asyncio.sleep(30)  # Cool down

        # Test 3: Sustained load
        logger.info("Test 3: Sustained load test")
        sustained_results = []
        for i in range(5):
            result = await self.measure_scaling_performance()
            sustained_results.append(result)
            await asyncio.sleep(10)

        test_results["tests"]["sustained_load"] = {
            "iterations": sustained_results,
            "average_scaling_time": sum(r["average_scaling_time"] for r in sustained_results)
            / len(sustained_results),
            "all_targets_met": all(r["target_met"] for r in sustained_results),
        }

        # Calculate overall success
        test_results["end_time"] = datetime.now().isoformat()
        test_results["duration"] = time.time() - self.start_time
        test_results["overall_success"] = (
            test_results["tests"]["burst_scaling"]["target_met"]
            and test_results["tests"]["circuit_breaker"]["test_passed"]
            and test_results["tests"]["sustained_load"]["all_targets_met"]
        )

        # Generate report
        self._generate_report(test_results)

        return test_results

    def _generate_report(self, results: Dict[str, Any]) -> None:
        """Generate test report"""
        logger.info("\n" + "=" * 60)
        logger.info("KEDA LOAD TEST REPORT")
        logger.info("=" * 60)
        logger.info(f"Test Duration: {results['duration']:.2f} seconds")
        logger.info(
            f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}"
        )
        logger.info("-" * 60)

        # Burst scaling results
        burst = results["tests"]["burst_scaling"]
        logger.info("Burst Scaling Test:")
        logger.info(f"  Average Scaling Time: {burst['average_scaling_time']:.2f}s")
        logger.info(f"  Improvement: {burst['improvement_percentage']:.1f}%")
        logger.info(f"  Target Met (≤9s): {'✅' if burst['target_met'] else '❌'}")

        # Circuit breaker results
        cb = results["tests"]["circuit_breaker"]
        logger.info("Circuit Breaker Test:")
        logger.info(f"  Triggered: {'✅' if cb['circuit_breaker_triggered'] else '❌'}")
        logger.info(f"  Events Generated: {cb['events_generated']}")

        # Sustained load results
        sustained = results["tests"]["sustained_load"]
        logger.info("Sustained Load Test:")
        logger.info(f"  Average Scaling Time: {sustained['average_scaling_time']:.2f}s")
        logger.info(f"  All Targets Met: {'✅' if sustained['all_targets_met'] else '❌'}")

        logger.info("=" * 60 + "\n")

        # Save detailed results to file
        with open(f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(results, f, indent=2)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KEDA Load Testing Suite")
    parser.add_argument(
        "--redis-host", default="redis.artemis-system.svc.cluster.local", help="Redis host address"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://prometheus.monitoring.svc.cluster.local:9090",
        help="Prometheus URL",
    )
    parser.add_argument("--test-duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument(
        "--pattern",
        choices=["burst", "gradual", "wave", "mixed", "comprehensive"],
        default="comprehensive",
        help="Load pattern to test",
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        redis_host=args.redis_host,
        prometheus_url=args.prometheus_url,
        test_duration=args.test_duration,
    )

    tester = KEDALoadTester(config)

    try:
        if args.pattern == "comprehensive":
            results = await tester.run_comprehensive_test()
            sys.exit(0 if results["overall_success"] else 1)
        else:
            await tester.setup()
            await tester.generate_artemis_load(args.pattern)
            results = await tester.measure_scaling_performance()
            logger.info(f"Results: {json.dumps(results, indent=2)}")
            sys.exit(0 if results["target_met"] else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
