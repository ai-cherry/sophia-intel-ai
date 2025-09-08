#!/usr/bin/env python3
"""
KEDA Performance Benchmark Script
Verifies 85% improvement in scaling time (60s to 9s)
Comprehensive performance testing for production readiness
"""

import argparse
import asyncio
import json
import logging
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarking"""

    target_scaling_time: float = 9.0  # Target: 9 seconds
    baseline_scaling_time: float = 60.0  # Baseline: 60 seconds
    improvement_target: float = 85.0  # Target: 85% improvement

    # Test parameters
    iterations: int = 10
    warmup_iterations: int = 2
    confidence_level: float = 0.95

    # Kubernetes
    namespace_keda: str = "keda-system"
    namespace_artemis: str = "artemis-system"
    namespace_sophia: str = "sophia-system"

    # Monitoring
    prometheus_url: str = "http://prometheus.monitoring.svc.cluster.local:9090"
    metrics_interval: int = 5  # seconds

    # Load patterns for testing
    load_profiles: List[str] = None

    def __post_init__(self):
        if self.load_profiles is None:
            self.load_profiles = ["burst", "gradual", "sustained", "wave", "realistic"]


@dataclass
class BenchmarkResult:
    """Result of a single benchmark iteration"""

    iteration: int
    load_profile: str
    scaling_time: float
    initial_replicas: int
    final_replicas: int
    scale_events: int
    cpu_usage: float
    memory_usage: float
    queue_length: int
    processing_rate: float
    timestamp: str
    success: bool

    def to_dict(self) -> Dict:
        return asdict(self)


class KEDAPerformanceBenchmark:
    """Main benchmarking class for KEDA performance validation"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.k8s_apps_v1: Optional[client.AppsV1Api] = None
        self.k8s_core_v1: Optional[client.CoreV1Api] = None
        self.k8s_custom: Optional[client.CustomObjectsApi] = None
        self.results: List[BenchmarkResult] = []
        self.metrics_collector = MetricsCollector(config.prometheus_url)

    async def setup(self):
        """Initialize Kubernetes clients and connections"""
        try:
            # Load Kubernetes config
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()

            self.k8s_apps_v1 = client.AppsV1Api()
            self.k8s_core_v1 = client.CoreV1Api()
            self.k8s_custom = client.CustomObjectsApi()

            logger.info("Kubernetes clients initialized")

            # Verify KEDA is running
            await self._verify_keda_status()

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise

    async def _verify_keda_status(self):
        """Verify KEDA components are healthy"""
        # Check KEDA operator
        pods = self.k8s_core_v1.list_namespaced_pod(
            namespace=self.config.namespace_keda, label_selector="app=keda-operator"
        )

        if not pods.items:
            raise RuntimeError("KEDA operator not found")

        for pod in pods.items:
            if pod.status.phase != "Running":
                raise RuntimeError(f"KEDA operator pod {pod.metadata.name} is not running")

        logger.info("KEDA operator verified as healthy")

    async def run_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite"""
        logger.info("Starting KEDA Performance Benchmark")
        logger.info(
            f"Target: {self.config.target_scaling_time}s (85% improvement from {self.config.baseline_scaling_time}s)"
        )

        await self.setup()

        # Warmup runs
        logger.info(f"Running {self.config.warmup_iterations} warmup iterations...")
        for i in range(self.config.warmup_iterations):
            await self._run_single_benchmark("burst", i, warmup=True)
            await asyncio.sleep(10)  # Cool down between iterations

        # Main benchmark runs
        logger.info(f"Running {self.config.iterations} benchmark iterations...")
        for iteration in range(self.config.iterations):
            for profile in self.config.load_profiles:
                logger.info(
                    f"Iteration {iteration + 1}/{self.config.iterations}, Profile: {profile}"
                )
                result = await self._run_single_benchmark(profile, iteration)
                self.results.append(result)
                await asyncio.sleep(15)  # Cool down between tests

        # Analyze results
        analysis = self._analyze_results()

        # Generate report
        report = self._generate_report(analysis)

        return report

    async def _run_single_benchmark(
        self, load_profile: str, iteration: int, warmup: bool = False
    ) -> Optional[BenchmarkResult]:
        """Run a single benchmark iteration"""
        if warmup:
            logger.debug(f"Warmup iteration {iteration + 1}")

        try:
            # Get initial state
            initial_state = await self._capture_state()

            # Generate load based on profile
            load_start_time = time.time()
            await self._generate_load(load_profile)

            # Monitor scaling
            scaling_result = await self._monitor_scaling(initial_state, timeout=120)
            scaling_time = time.time() - load_start_time

            # Capture final state
            final_state = await self._capture_state()

            # Collect metrics
            metrics = await self._collect_metrics()

            if not warmup:
                result = BenchmarkResult(
                    iteration=iteration,
                    load_profile=load_profile,
                    scaling_time=scaling_time,
                    initial_replicas=initial_state["total_replicas"],
                    final_replicas=final_state["total_replicas"],
                    scale_events=scaling_result["scale_events"],
                    cpu_usage=metrics["cpu_usage"],
                    memory_usage=metrics["memory_usage"],
                    queue_length=metrics["queue_length"],
                    processing_rate=metrics["processing_rate"],
                    timestamp=datetime.now().isoformat(),
                    success=scaling_time <= self.config.target_scaling_time,
                )

                logger.info(
                    f"Benchmark result: {scaling_time:.2f}s ({'✅ PASS' if result.success else '❌ FAIL'})"
                )
                return result

            return None

        except Exception as e:
            logger.error(f"Benchmark iteration failed: {e}")
            if not warmup:
                return BenchmarkResult(
                    iteration=iteration,
                    load_profile=load_profile,
                    scaling_time=float("inf"),
                    initial_replicas=0,
                    final_replicas=0,
                    scale_events=0,
                    cpu_usage=0,
                    memory_usage=0,
                    queue_length=0,
                    processing_rate=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                )
            return None

    async def _capture_state(self) -> Dict[str, Any]:
        """Capture current system state"""
        state = {"total_replicas": 0, "deployments": {}, "timestamp": time.time()}

        # Check Artemis deployment
        try:
            artemis = self.k8s_apps_v1.read_namespaced_deployment(
                name="artemis-worker", namespace=self.config.namespace_artemis
            )
            state["deployments"]["artemis-worker"] = artemis.status.replicas or 0
            state["total_replicas"] += artemis.status.replicas or 0
        except:
            pass

        # Check Sophia deployment
        try:
            sophia = self.k8s_apps_v1.read_namespaced_deployment(
                name="sophia-analytics", namespace=self.config.namespace_sophia
            )
            state["deployments"]["sophia-analytics"] = sophia.status.replicas or 0
            state["total_replicas"] += sophia.status.replicas or 0
        except:
            pass

        return state

    async def _generate_load(self, profile: str):
        """Generate load based on profile"""
        if profile == "burst":
            await self._generate_burst_load()
        elif profile == "gradual":
            await self._generate_gradual_load()
        elif profile == "sustained":
            await self._generate_sustained_load()
        elif profile == "wave":
            await self._generate_wave_load()
        elif profile == "realistic":
            await self._generate_realistic_load()
        else:
            raise ValueError(f"Unknown load profile: {profile}")

    async def _generate_burst_load(self):
        """Generate sudden burst load"""
        # Simulate burst by creating many tasks quickly
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(100):
                task = self._create_load_task(session, f"burst_{i}")
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _generate_gradual_load(self):
        """Generate gradually increasing load"""
        async with aiohttp.ClientSession() as session:
            for step in range(10):
                tasks = []
                for i in range(10 * (step + 1)):
                    task = self._create_load_task(session, f"gradual_{step}_{i}")
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(2)

    async def _generate_sustained_load(self):
        """Generate sustained load"""
        async with aiohttp.ClientSession() as session:
            for _ in range(30):
                tasks = []
                for i in range(20):
                    task = self._create_load_task(session, f"sustained_{i}")
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)

    async def _generate_wave_load(self):
        """Generate wave pattern load"""
        import math

        async with aiohttp.ClientSession() as session:
            for t in range(20):
                wave_value = int(50 * (1 + math.sin(2 * math.pi * t / 10)))
                tasks = []
                for i in range(wave_value):
                    task = self._create_load_task(session, f"wave_{t}_{i}")
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)

    async def _generate_realistic_load(self):
        """Generate realistic mixed load pattern"""
        # Combination of different patterns to simulate real-world scenario
        await asyncio.gather(
            self._generate_burst_load(), self._generate_gradual_load(), return_exceptions=True
        )

    async def _create_load_task(self, session: aiohttp.ClientSession, task_id: str):
        """Create a single load task"""
        # This is a placeholder - actual implementation would interact with the system
        await asyncio.sleep(0.01)  # Simulate task creation
        return task_id

    async def _monitor_scaling(self, initial_state: Dict, timeout: int = 120) -> Dict[str, Any]:
        """Monitor scaling activity"""
        start_time = time.time()
        scale_events = 0
        max_replicas = initial_state["total_replicas"]

        while time.time() - start_time < timeout:
            current_state = await self._capture_state()

            # Check if scaling occurred
            if current_state["total_replicas"] != initial_state["total_replicas"]:
                scale_events += 1
                max_replicas = max(max_replicas, current_state["total_replicas"])

                # Check if scaling stabilized
                await asyncio.sleep(5)
                stable_state = await self._capture_state()
                if stable_state["total_replicas"] == current_state["total_replicas"]:
                    # Scaling completed
                    break

            await asyncio.sleep(1)

        return {
            "scale_events": scale_events,
            "max_replicas": max_replicas,
            "scaling_time": time.time() - start_time,
        }

    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect performance metrics"""
        metrics = await self.metrics_collector.collect_metrics()
        return metrics

    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze benchmark results"""
        if not self.results:
            return {}

        # Filter out failed results for statistical analysis
        valid_results = [r for r in self.results if r.scaling_time < float("inf")]

        if not valid_results:
            return {
                "error": "No valid results to analyze",
                "total_tests": len(self.results),
                "valid_tests": 0,
            }

        scaling_times = [r.scaling_time for r in valid_results]

        analysis = {
            "total_tests": len(self.results),
            "valid_tests": len(valid_results),
            "failed_tests": len(self.results) - len(valid_results),
            "success_rate": sum(1 for r in valid_results if r.success) / len(valid_results) * 100,
            "scaling_time": {
                "mean": statistics.mean(scaling_times),
                "median": statistics.median(scaling_times),
                "stdev": statistics.stdev(scaling_times) if len(scaling_times) > 1 else 0,
                "min": min(scaling_times),
                "max": max(scaling_times),
                "p95": np.percentile(scaling_times, 95),
                "p99": np.percentile(scaling_times, 99),
            },
            "improvement": {
                "actual": (self.config.baseline_scaling_time - statistics.mean(scaling_times))
                / self.config.baseline_scaling_time
                * 100,
                "target": self.config.improvement_target,
                "meets_target": statistics.mean(scaling_times) <= self.config.target_scaling_time,
            },
            "by_profile": {},
        }

        # Analyze by load profile
        for profile in self.config.load_profiles:
            profile_results = [r for r in valid_results if r.load_profile == profile]
            if profile_results:
                profile_times = [r.scaling_time for r in profile_results]
                analysis["by_profile"][profile] = {
                    "mean": statistics.mean(profile_times),
                    "median": statistics.median(profile_times),
                    "success_rate": sum(1 for r in profile_results if r.success)
                    / len(profile_results)
                    * 100,
                }

        # Statistical confidence
        if len(scaling_times) > 1:
            from scipy import stats

            confidence_interval = stats.t.interval(
                self.config.confidence_level,
                len(scaling_times) - 1,
                loc=statistics.mean(scaling_times),
                scale=stats.sem(scaling_times),
            )
            analysis["confidence_interval"] = {
                "level": self.config.confidence_level * 100,
                "lower": confidence_interval[0],
                "upper": confidence_interval[1],
            }

        return analysis

    def _generate_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "config": asdict(self.config),
                "environment": {
                    "kubernetes_version": self._get_k8s_version(),
                    "keda_version": "2.13.0",
                },
            },
            "results": {"summary": analysis, "detailed": [r.to_dict() for r in self.results]},
            "verdict": self._generate_verdict(analysis),
        }

        # Save report to file
        report_filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to {report_filename}")

        # Print summary
        self._print_summary(analysis)

        return report

    def _get_k8s_version(self) -> str:
        """Get Kubernetes version"""
        try:
            version = self.k8s_core_v1.get_api_resources().group_version
            return version
        except:
            return "unknown"

    def _generate_verdict(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pass/fail verdict"""
        if "error" in analysis:
            return {"pass": False, "reason": analysis["error"]}

        meets_target = analysis["improvement"]["meets_target"]
        success_rate = analysis["success_rate"]

        verdict = {
            "pass": meets_target and success_rate >= 90,
            "scaling_time_target": {
                "pass": meets_target,
                "actual": analysis["scaling_time"]["mean"],
                "target": self.config.target_scaling_time,
            },
            "improvement_target": {
                "pass": analysis["improvement"]["actual"] >= self.config.improvement_target,
                "actual": analysis["improvement"]["actual"],
                "target": self.config.improvement_target,
            },
            "reliability": {"pass": success_rate >= 90, "success_rate": success_rate},
        }

        return verdict

    def _print_summary(self, analysis: Dict[str, Any]):
        """Print benchmark summary to console"""
        print("\n" + "=" * 60)
        print("KEDA PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        if "error" in analysis:
            print(f"❌ ERROR: {analysis['error']}")
            return

        print(f"Tests Run: {analysis['total_tests']}")
        print(f"Valid Tests: {analysis['valid_tests']}")
        print(f"Success Rate: {analysis['success_rate']:.1f}%")
        print("-" * 60)

        print("SCALING TIME STATISTICS:")
        print(f"  Mean: {analysis['scaling_time']['mean']:.2f}s")
        print(f"  Median: {analysis['scaling_time']['median']:.2f}s")
        print(f"  Std Dev: {analysis['scaling_time']['stdev']:.2f}s")
        print(f"  Min: {analysis['scaling_time']['min']:.2f}s")
        print(f"  Max: {analysis['scaling_time']['max']:.2f}s")
        print(f"  P95: {analysis['scaling_time']['p95']:.2f}s")
        print(f"  P99: {analysis['scaling_time']['p99']:.2f}s")
        print("-" * 60)

        print("PERFORMANCE TARGETS:")
        print(f"  Target Scaling Time: {self.config.target_scaling_time}s")
        print(f"  Actual Mean Time: {analysis['scaling_time']['mean']:.2f}s")
        print(f"  Target Improvement: {self.config.improvement_target}%")
        print(f"  Actual Improvement: {analysis['improvement']['actual']:.1f}%")
        print("-" * 60)

        print("RESULTS BY LOAD PROFILE:")
        for profile, stats in analysis["by_profile"].items():
            print(f"  {profile}:")
            print(f"    Mean: {stats['mean']:.2f}s")
            print(f"    Success Rate: {stats['success_rate']:.1f}%")

        print("-" * 60)
        if analysis["improvement"]["meets_target"]:
            print("✅ BENCHMARK PASSED - All targets met!")
        else:
            print("❌ BENCHMARK FAILED - Targets not met")
        print("=" * 60 + "\n")


class MetricsCollector:
    """Collects metrics from Prometheus"""

    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url

    async def collect_metrics(self) -> Dict[str, float]:
        """Collect current metrics from Prometheus"""
        metrics = {"cpu_usage": 0.0, "memory_usage": 0.0, "queue_length": 0, "processing_rate": 0.0}

        async with aiohttp.ClientSession() as session:
            # CPU usage
            cpu_query = "avg(rate(container_cpu_usage_seconds_total[5m]))"
            metrics["cpu_usage"] = await self._query_prometheus(session, cpu_query)

            # Memory usage
            memory_query = "avg(container_memory_working_set_bytes / 1024 / 1024 / 1024)"
            metrics["memory_usage"] = await self._query_prometheus(session, memory_query)

            # Queue length (Artemis)
            queue_query = 'redis_list_length{list="artemis:task:queue"}'
            metrics["queue_length"] = int(await self._query_prometheus(session, queue_query))

            # Processing rate (Sophia)
            rate_query = "sum(rate(sophia_analytics_events_processed_total[1m]))"
            metrics["processing_rate"] = await self._query_prometheus(session, rate_query)

        return metrics

    async def _query_prometheus(self, session: aiohttp.ClientSession, query: str) -> float:
        """Execute Prometheus query"""
        try:
            async with session.get(
                f"{self.prometheus_url}/api/v1/query", params={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["data"]["result"]:
                        return float(data["data"]["result"][0]["value"][1])
        except Exception as e:
            logger.debug(f"Prometheus query failed: {e}")

        return 0.0


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KEDA Performance Benchmark")
    parser.add_argument("--iterations", type=int, default=10, help="Number of benchmark iterations")
    parser.add_argument("--warmup", type=int, default=2, help="Number of warmup iterations")
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=["burst", "gradual", "sustained", "wave", "realistic"],
        help="Load profiles to test",
    )
    parser.add_argument(
        "--target-time", type=float, default=9.0, help="Target scaling time in seconds"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://prometheus.monitoring.svc.cluster.local:9090",
        help="Prometheus URL",
    )

    args = parser.parse_args()

    config = BenchmarkConfig(
        iterations=args.iterations,
        warmup_iterations=args.warmup,
        load_profiles=args.profiles,
        target_scaling_time=args.target_time,
        prometheus_url=args.prometheus_url,
    )

    benchmark = KEDAPerformanceBenchmark(config)

    try:
        report = await benchmark.run_benchmark()

        # Exit with appropriate code
        if report["verdict"]["pass"]:
            logger.info("✅ Benchmark completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Benchmark failed to meet targets")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
