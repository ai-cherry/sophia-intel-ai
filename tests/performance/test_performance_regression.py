"""
Comprehensive Performance Regression Tests
Monitors system performance and detects regressions across all components
"""
import asyncio
import json
import os
import sqlite3
import statistics
# Performance testing utilities
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import aiohttp
import memory_profiler
import numpy as np
import psutil
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
@dataclass
class PerformanceBaseline:
    """Performance baseline metrics"""
    component: str
    metric_name: str
    baseline_value: float
    unit: str
    timestamp: datetime
    test_conditions: Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "timestamp": self.timestamp.isoformat()}
@dataclass
class PerformanceMetrics:
    """Performance test results"""
    component: str
    test_name: str
    duration: float
    response_times: List[float]
    throughput: float
    memory_usage: float
    cpu_usage: float
    error_rate: float
    timestamp: datetime
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return np.percentile(self.response_times, 95)
    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return np.percentile(self.response_times, 99)
@dataclass
class RegressionResult:
    """Performance regression analysis result"""
    component: str
    metric_name: str
    current_value: float
    baseline_value: float
    regression_percentage: float
    is_regression: bool
    severity: str  # 'low', 'medium', 'high', 'critical'
    @property
    def regression_factor(self) -> float:
        if self.baseline_value == 0:
            return float("inf") if self.current_value > 0 else 1.0
        return self.current_value / self.baseline_value
class PerformanceDatabase:
    """SQLite database for storing performance metrics"""
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.init_database()
    def init_database(self):
        """Initialize performance metrics database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    test_conditions TEXT NOT NULL,
                    UNIQUE(component, metric_name)
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    duration REAL NOT NULL,
                    avg_response_time REAL NOT NULL,
                    p95_response_time REAL NOT NULL,
                    p99_response_time REAL NOT NULL,
                    throughput REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    cpu_usage REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS regressions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    regression_percentage REAL NOT NULL,
                    severity TEXT NOT NULL,
                    detected_at TEXT NOT NULL
                )
            """
            )
            conn.commit()
        finally:
            conn.close()
    def store_baseline(self, baseline: PerformanceBaseline):
        """Store performance baseline"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO baselines 
                (component, metric_name, baseline_value, unit, timestamp, test_conditions)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    baseline.component,
                    baseline.metric_name,
                    baseline.baseline_value,
                    baseline.unit,
                    baseline.timestamp.isoformat(),
                    json.dumps(baseline.test_conditions),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    def get_baseline(
        self, component: str, metric_name: str
    ) -> Optional[PerformanceBaseline]:
        """Get performance baseline"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT component, metric_name, baseline_value, unit, timestamp, test_conditions
                FROM baselines WHERE component = ? AND metric_name = ?
            """,
                (component, metric_name),
            )
            row = cursor.fetchone()
            if row:
                return PerformanceBaseline(
                    component=row[0],
                    metric_name=row[1],
                    baseline_value=row[2],
                    unit=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    test_conditions=json.loads(row[5]),
                )
            return None
        finally:
            conn.close()
    def store_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO metrics 
                (component, test_name, duration, avg_response_time, p95_response_time, 
                 p99_response_time, throughput, memory_usage, cpu_usage, error_rate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.component,
                    metrics.test_name,
                    metrics.duration,
                    metrics.avg_response_time,
                    metrics.p95_response_time,
                    metrics.p99_response_time,
                    metrics.throughput,
                    metrics.memory_usage,
                    metrics.cpu_usage,
                    metrics.error_rate,
                    metrics.timestamp.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    def store_regression(self, regression: RegressionResult):
        """Store regression detection result"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO regressions 
                (component, metric_name, current_value, baseline_value, 
                 regression_percentage, severity, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    regression.component,
                    regression.metric_name,
                    regression.current_value,
                    regression.baseline_value,
                    regression.regression_percentage,
                    regression.severity,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
class PerformanceMonitor:
    """System performance monitoring utilities"""
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring_active = False
        self.metrics_history = []
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring"""
        self.monitoring_active = True
        self.metrics_history = []
        def monitor_loop():
            while self.monitoring_active:
                try:
                    metrics = {
                        "timestamp": time.time(),
                        "cpu_percent": self.process.cpu_percent(),
                        "memory_mb": self.process.memory_info().rss / 1024 / 1024,
                        "memory_percent": self.process.memory_percent(),
                        "threads": self.process.num_threads(),
                        "open_files": len(self.process.open_files()),
                        "connections": len(self.process.connections()),
                    }
                    self.metrics_history.append(metrics)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                time.sleep(interval)
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring_active = False
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=2.0)
        if not self.metrics_history:
            return {
                "avg_cpu_percent": 0.0,
                "max_cpu_percent": 0.0,
                "avg_memory_mb": 0.0,
                "max_memory_mb": 0.0,
                "avg_threads": 0.0,
                "max_connections": 0,
            }
        cpu_values = [m["cpu_percent"] for m in self.metrics_history]
        memory_values = [m["memory_mb"] for m in self.metrics_history]
        thread_values = [m["threads"] for m in self.metrics_history]
        connection_values = [m["connections"] for m in self.metrics_history]
        return {
            "avg_cpu_percent": statistics.mean(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "avg_memory_mb": statistics.mean(memory_values),
            "max_memory_mb": max(memory_values),
            "avg_threads": statistics.mean(thread_values),
            "max_connections": max(connection_values) if connection_values else 0,
        }
class PerformanceTester:
    """Core performance testing functionality"""
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.monitor = PerformanceMonitor()
        self.session = None
    async def setup(self):
        """Setup performance tester"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
    async def teardown(self):
        """Cleanup performance tester"""
        if self.session:
            await self.session.close()
    async def benchmark_endpoint(
        self,
        component: str,
        test_name: str,
        url: str,
        method: str = "GET",
        payload: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        concurrent_requests: int = 10,
        total_requests: int = 100,
        warmup_requests: int = 10,
    ) -> PerformanceMetrics:
        """Benchmark API endpoint performance"""
        print(
            f"🔥 Benchmarking {component}/{test_name}: {concurrent_requests} concurrent, {total_requests} total requests"
        )
        # Start monitoring
        self.monitor.start_monitoring()
        test_start = time.time()
        # Warmup requests
        print("   Warming up...")
        await self._execute_requests(url, method, payload, headers, warmup_requests, 1)
        # Actual performance test
        print("   Running benchmark...")
        response_times, errors = await self._execute_requests(
            url, method, payload, headers, total_requests, concurrent_requests
        )
        test_duration = time.time() - test_start
        # Stop monitoring and get system metrics
        system_metrics = self.monitor.stop_monitoring()
        # Calculate performance metrics
        throughput = len(response_times) / test_duration if test_duration > 0 else 0
        error_rate = (
            len(errors) / (len(response_times) + len(errors))
            if (len(response_times) + len(errors)) > 0
            else 0
        )
        metrics = PerformanceMetrics(
            component=component,
            test_name=test_name,
            duration=test_duration,
            response_times=response_times,
            throughput=throughput,
            memory_usage=system_metrics["max_memory_mb"],
            cpu_usage=system_metrics["avg_cpu_percent"],
            error_rate=error_rate,
            timestamp=datetime.now(),
        )
        print(
            f"   Results: {metrics.avg_response_time:.3f}s avg, {metrics.throughput:.1f} RPS, {error_rate:.1%} errors"
        )
        # Store metrics in database
        self.db.store_metrics(metrics)
        return metrics
    async def _execute_requests(
        self,
        url: str,
        method: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        total_requests: int,
        concurrent_requests: int,
    ) -> Tuple[List[float], List[str]]:
        """Execute HTTP requests with specified concurrency"""
        semaphore = asyncio.Semaphore(concurrent_requests)
        response_times = []
        errors = []
        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    async with self.session.request(
                        method=method, url=url, json=payload, headers=headers or {}
                    ) as response:
                        await response.read()  # Ensure full response is received
                        response_time = time.time() - start_time
                        if response.status < 400:
                            response_times.append(response_time)
                        else:
                            errors.append(f"HTTP {response.status}")
                except Exception as e:
                    errors.append(str(e))
        # Execute all requests concurrently
        tasks = [make_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        return response_times, errors
    def analyze_regression(
        self,
        component: str,
        current_metrics: PerformanceMetrics,
        regression_thresholds: Dict[str, float] = None,
    ) -> List[RegressionResult]:
        """Analyze performance regression against baselines"""
        if regression_thresholds is None:
            regression_thresholds = {
                "avg_response_time": 0.20,  # 20% slower
                "p95_response_time": 0.25,  # 25% slower
                "throughput": -0.15,  # 15% less throughput (negative = worse)
                "memory_usage": 0.30,  # 30% more memory
                "error_rate": 0.05,  # 5% more errors (absolute)
            }
        regressions = []
        # Check each metric against its baseline
        metrics_to_check = {
            "avg_response_time": current_metrics.avg_response_time,
            "p95_response_time": current_metrics.p95_response_time,
            "throughput": current_metrics.throughput,
            "memory_usage": current_metrics.memory_usage,
            "error_rate": current_metrics.error_rate,
        }
        for metric_name, current_value in metrics_to_check.items():
            baseline = self.db.get_baseline(component, metric_name)
            if baseline is None:
                # Create baseline if it doesn't exist
                baseline = PerformanceBaseline(
                    component=component,
                    metric_name=metric_name,
                    baseline_value=current_value,
                    unit=self._get_metric_unit(metric_name),
                    timestamp=datetime.now(),
                    test_conditions={},
                )
                self.db.store_baseline(baseline)
                continue
            # Calculate regression
            threshold = regression_thresholds.get(metric_name, 0.20)
            if metric_name == "throughput":
                # For throughput, lower is worse
                regression_pct = (
                    baseline.baseline_value - current_value
                ) / baseline.baseline_value
                is_regression = regression_pct > abs(threshold)
            elif metric_name == "error_rate":
                # For error rate, use absolute difference
                regression_pct = current_value - baseline.baseline_value
                is_regression = regression_pct > threshold
            else:
                # For response time and memory, higher is worse
                regression_pct = (
                    current_value - baseline.baseline_value
                ) / baseline.baseline_value
                is_regression = regression_pct > threshold
            if is_regression:
                severity = self._determine_severity(regression_pct, threshold)
                regression = RegressionResult(
                    component=component,
                    metric_name=metric_name,
                    current_value=current_value,
                    baseline_value=baseline.baseline_value,
                    regression_percentage=regression_pct,
                    is_regression=True,
                    severity=severity,
                )
                regressions.append(regression)
                self.db.store_regression(regression)
                print(
                    f"⚠️  Regression detected in {component}.{metric_name}: "
                    f"{regression_pct:.1%} worse than baseline ({severity})"
                )
        return regressions
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        units = {
            "avg_response_time": "seconds",
            "p95_response_time": "seconds",
            "p99_response_time": "seconds",
            "throughput": "requests/second",
            "memory_usage": "MB",
            "cpu_usage": "percent",
            "error_rate": "percent",
        }
        return units.get(metric_name, "unknown")
    def _determine_severity(self, regression_pct: float, threshold: float) -> str:
        """Determine regression severity"""
        if regression_pct >= threshold * 3:
            return "critical"
        elif regression_pct >= threshold * 2:
            return "high"
        elif regression_pct >= threshold * 1.5:
            return "medium"
        else:
            return "low"
class TestUnifiedMCPServerPerformance:
    """Performance regression tests for Unified MCP Server"""
    @pytest.fixture
    async def perf_tester(self):
        """Performance tester fixture"""
        db = PerformanceDatabase("test_performance.db")
        tester = PerformanceTester(db)
        await tester.setup()
        yield tester
        await tester.teardown()
    @pytest.mark.asyncio
    async def test_routing_performance(self, perf_tester):
        """Test Unified MCP Server routing performance"""
        base_url = "${SOPHIA_API_ENDPOINT}"
        # Test simple routing performance
        metrics = await perf_tester.benchmark_endpoint(
            component="unified_mcp",
            test_name="simple_routing",
            url=f"{base_url}/route",
            method="POST",
            payload={
                "target": "",
                "request": {"type": "simple_task", "data": "test"},
            },
            concurrent_requests=20,
            total_requests=200,
        )
        # Analyze for regressions
        regressions = perf_tester.analyze_regression("unified_mcp", metrics)
        # Performance assertions
        assert (
            metrics.avg_response_time <= 0.1
        ), f"Average response time {metrics.avg_response_time:.3f}s exceeds 100ms"
        assert (
            metrics.p95_response_time <= 0.2
        ), f"P95 response time {metrics.p95_response_time:.3f}s exceeds 200ms"
        assert (
            metrics.throughput >= 100
        ), f"Throughput {metrics.throughput:.1f} RPS below 100 RPS"
        assert (
            metrics.error_rate <= 0.01
        ), f"Error rate {metrics.error_rate:.1%} exceeds 1%"
        # Check for critical regressions
        critical_regressions = [r for r in regressions if r.severity == "critical"]
        assert (
            len(critical_regressions) == 0
        ), f"Critical performance regressions detected: {critical_regressions}"
        return metrics
    @pytest.mark.asyncio
    async def test_cache_performance(self, perf_tester):
        """Test caching system performance"""
        base_url = "${SOPHIA_API_ENDPOINT}"
        # Test cache hit performance
        cache_hit_metrics = await perf_tester.benchmark_endpoint(
            component="unified_mcp",
            test_name="cache_hits",
            url=f"{base_url}/cache/test_key",
            method="GET",
            concurrent_requests=50,
            total_requests=500,
        )
        # Test cache miss performance
        cache_miss_metrics = await perf_tester.benchmark_endpoint(
            component="unified_mcp",
            test_name="cache_misses",
            url=f"{base_url}/cache/nonexistent_key",
            method="GET",
            concurrent_requests=50,
            total_requests=500,
        )
        # Cache hits should be significantly faster
        assert (
            cache_hit_metrics.avg_response_time < cache_miss_metrics.avg_response_time
        )
        assert (
            cache_hit_metrics.avg_response_time <= 0.005
        ), "Cache hits should be under 5ms"
        # Analyze regressions
        hit_regressions = perf_tester.analyze_regression(
            "unified_mcp_cache_hits", cache_hit_metrics
        )
        miss_regressions = perf_tester.analyze_regression(
            "unified_mcp_cache_misses", cache_miss_metrics
        )
        return {
            "cache_hits": cache_hit_metrics,
            "cache_misses": cache_miss_metrics,
            "hit_regressions": hit_regressions,
            "miss_regressions": miss_regressions,
        }
    @pytest.mark.asyncio
    async def test_concurrent_connections_performance(self, perf_tester):
        """Test performance under high concurrent connections"""
        base_url = "${SOPHIA_API_ENDPOINT}"
        # Test with increasing concurrent load
        concurrency_levels = [10, 25, 50, 100]
        results = []
        for concurrency in concurrency_levels:
            print(f"   Testing {concurrency} concurrent connections...")
            metrics = await perf_tester.benchmark_endpoint(
                component="unified_mcp",
                test_name=f"concurrency_{concurrency}",
                url=f"{base_url}/health",
                method="GET",
                concurrent_requests=concurrency,
                total_requests=concurrency * 10,  # 10 requests per connection
            )
            results.append(
                {
                    "concurrency": concurrency,
                    "metrics": metrics,
                    "regressions": perf_tester.analyze_regression(
                        f"unified_mcp_concurrency_{concurrency}", metrics
                    ),
                }
            )
        # Verify performance doesn't degrade drastically with concurrency
        baseline_result = results[0]
        highest_result = results[-1]
        # Response time shouldn't increase more than 3x
        response_time_factor = (
            highest_result["metrics"].avg_response_time
            / baseline_result["metrics"].avg_response_time
        )
        assert (
            response_time_factor <= 3.0
        ), f"Response time increased {response_time_factor:.1f}x under high concurrency"
        # Throughput per connection shouldn't drop below 50%
        baseline_throughput_per_conn = (
            baseline_result["metrics"].throughput / baseline_result["concurrency"]
        )
        highest_throughput_per_conn = (
            highest_result["metrics"].throughput / highest_result["concurrency"]
        )
        throughput_ratio = highest_throughput_per_conn / baseline_throughput_per_conn
        assert (
            throughput_ratio >= 0.5
        ), f"Per-connection throughput dropped to {throughput_ratio:.1%} under high concurrency"
        return results
class TestSwarmPerformance:
    """Performance regression tests for  Swarm Orchestrator"""
    @pytest.fixture
    async def perf_tester(self):
        db = PerformanceDatabase("test_performance.db")
        tester = PerformanceTester(db)
        await tester.setup()
        yield tester
        await tester.teardown()
    @pytest.mark.asyncio
    async def test_workflow_creation_performance(self, perf_tester):
        """Test workflow creation performance"""
        base_url = "http://localhost:8081"
        workflow_payload = {
            "workflow_type": "performance_test",
            "tasks": [
                {"agent": "plannr", "task": "plan_task"},
                {"agent": "coder", "task": "code_task", "dependencies": ["plan_task"]},
                {"agent": "tester", "task": "test_task", "dependencies": ["code_task"]},
            ],
            "priority": "normal",
        }
        metrics = await perf_tester.benchmark_endpoint(
            component="_swarm",
            test_name="workflow_creation",
            url=f"{base_url}/workflows",
            method="POST",
            payload=workflow_payload,
            concurrent_requests=15,
            total_requests=150,
        )
        regressions = perf_tester.analyze_regression("_swarm", metrics)
        # Workflow creation should be reasonably fast
        assert (
            metrics.avg_response_time <= 0.5
        ), f"Workflow creation avg {metrics.avg_response_time:.3f}s exceeds 500ms"
        assert (
            metrics.p95_response_time <= 1.0
        ), f"Workflow creation P95 {metrics.p95_response_time:.3f}s exceeds 1s"
        assert (
            metrics.error_rate <= 0.05
        ), f"Workflow creation error rate {metrics.error_rate:.1%} exceeds 5%"
        return {"metrics": metrics, "regressions": regressions}
    @pytest.mark.asyncio
    async def test_agent_allocation_performance(self, perf_tester):
        """Test agent allocation performance"""
        base_url = "http://localhost:8081"
        # Test agent allocation for different agent types
        agent_types = ["plannr", "coder", "tester", "deployer", "evolver"]
        allocation_results = []
        for agent_type in agent_types:
            allocation_payload = {
                "agent_type": agent_type,
                "task_priority": "high",
                "estimated_duration": 300,
            }
            metrics = await perf_tester.benchmark_endpoint(
                component="_swarm",
                test_name=f"agent_allocation_{agent_type}",
                url=f"{base_url}/agents/allocate",
                method="POST",
                payload=allocation_payload,
                concurrent_requests=10,
                total_requests=100,
            )
            regressions = perf_tester.analyze_regression(
                f"_agent_{agent_type}", metrics
            )
            allocation_results.append(
                {
                    "agent_type": agent_type,
                    "metrics": metrics,
                    "regressions": regressions,
                }
            )
            # Agent allocation should be very fast
            assert (
                metrics.avg_response_time <= 0.05
            ), f"{agent_type} allocation avg {metrics.avg_response_time:.3f}s exceeds 50ms"
        return allocation_results
    @pytest.mark.asyncio
    @memory_profiler.profile
    async def test_memory_usage_under_load(self, perf_tester):
        """Test memory usage under sustained load"""
        base_url = "http://localhost:8081"
        # Create many workflows to test memory management
        workflow_payload = {
            "workflow_type": "memory_test",
            "tasks": [
                {"agent": "plannr", "task": f"memory_task_{i}"} for i in range(10)
            ],
            "priority": "low",
        }
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        metrics = await perf_tester.benchmark_endpoint(
            component="_swarm",
            test_name="memory_load_test",
            url=f"{base_url}/workflows/batch",
            method="POST",
            payload={"workflows": [workflow_payload for _ in range(20)]},
            concurrent_requests=5,
            total_requests=25,
        )
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        print(
            f"   Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)"
        )
        # Memory increase should be reasonable
        assert (
            memory_increase <= 100
        ), f"Memory increased by {memory_increase:.1f}MB, exceeds 100MB limit"
        # Check for memory-related regressions
        regressions = perf_tester.analyze_regression("_memory_test", metrics)
        return {
            "metrics": metrics,
            "memory_increase_mb": memory_increase,
            "regressions": regressions,
        }
class TestMemorySystemPerformance:
    """Performance regression tests for Memory System (Mem0)"""
    @pytest.fixture
    async def perf_tester(self):
        db = PerformanceDatabase("test_performance.db")
        tester = PerformanceTester(db)
        await tester.setup()
        yield tester
        await tester.teardown()
    @pytest.mark.asyncio
    async def test_memory_storage_performance(self, perf_tester):
        """Test memory storage performance"""
        base_url = "http://localhost:8083"
        memory_payload = {
            "content": "Performance test memory content " * 10,  # ~300 chars
            "memory_type": "semantic",
            "tags": ["performance", "test", "benchmark"],
            "importance_score": 0.7,
        }
        metrics = await perf_tester.benchmark_endpoint(
            component="mem0_server",
            test_name="memory_storage",
            url=f"{base_url}/memories",
            method="POST",
            payload=memory_payload,
            concurrent_requests=20,
            total_requests=200,
        )
        regressions = perf_tester.analyze_regression("mem0_server", metrics)
        # Memory storage should be fast
        assert (
            metrics.avg_response_time <= 0.1
        ), f"Memory storage avg {metrics.avg_response_time:.3f}s exceeds 100ms"
        assert (
            metrics.throughput >= 50
        ), f"Memory storage throughput {metrics.throughput:.1f} below 50 RPS"
        return {"metrics": metrics, "regressions": regressions}
    @pytest.mark.asyncio
    async def test_memory_search_performance(self, perf_tester):
        """Test memory search performance with different query types"""
        base_url = "http://localhost:8083"
        search_queries = [
            {"query": "performance test", "limit": 10},
            {"query": "specific memory content", "limit": 25},
            {"query": "complex search with multiple terms", "limit": 50},
        ]
        search_results = []
        for i, query in enumerate(search_queries):
            metrics = await perf_tester.benchmark_endpoint(
                component="mem0_server",
                test_name=f"memory_search_{i}",
                url=f"{base_url}/memories/search",
                method="GET",
                payload=query,
                concurrent_requests=15,
                total_requests=150,
            )
            regressions = perf_tester.analyze_regression(f"mem0_search_{i}", metrics)
            search_results.append(
                {"query": query, "metrics": metrics, "regressions": regressions}
            )
            # Search should be fast
            assert (
                metrics.avg_response_time <= 0.2
            ), f"Search query {i} avg {metrics.avg_response_time:.3f}s exceeds 200ms"
        return search_results
    @pytest.mark.asyncio
    async def test_correlation_performance(self, perf_tester):
        """Test memory correlation performance"""
        base_url = "http://localhost:8083"
        correlation_payload = {
            "memory_id": "test_memory_123",
            "correlation_threshold": 0.7,
            "max_results": 20,
        }
        metrics = await perf_tester.benchmark_endpoint(
            component="mem0_server",
            test_name="memory_correlation",
            url=f"{base_url}/memories/correlate",
            method="POST",
            payload=correlation_payload,
            concurrent_requests=8,
            total_requests=80,
        )
        regressions = perf_tester.analyze_regression("mem0_correlation", metrics)
        # Correlation can be slower due to complexity
        assert (
            metrics.avg_response_time <= 1.0
        ), f"Correlation avg {metrics.avg_response_time:.3f}s exceeds 1s"
        assert (
            metrics.error_rate <= 0.10
        ), f"Correlation error rate {metrics.error_rate:.1%} exceeds 10%"
        return {"metrics": metrics, "regressions": regressions}
class TestBIServerPerformance:
    """Performance regression tests for Business Intelligence Server"""
    @pytest.fixture
    async def perf_tester(self):
        db = PerformanceDatabase("test_performance.db")
        tester = PerformanceTester(db)
        await tester.setup()
        yield tester
        await tester.teardown()
    @pytest.mark.asyncio
    async def test_analytics_query_performance(self, perf_tester):
        """Test BI analytics query performance"""
        base_url = "http://localhost:8082"
        analytics_queries = [
            {"type": "revenue_analysis", "period": "last_month"},
            {"type": "customer_segmentation", "industry": "technology"},
            {"type": "conversion_metrics", "funnel": "sales_pipeline"},
        ]
        query_results = []
        for query in analytics_queries:
            metrics = await perf_tester.benchmark_endpoint(
                component="bi_server",
                test_name=f"analytics_{query['type']}",
                url=f"{base_url}/analytics/query",
                method="POST",
                payload=query,
                concurrent_requests=5,  # Lower concurrency for complex analytics
                total_requests=50,
            )
            regressions = perf_tester.analyze_regression(f"bi_{query['type']}", metrics)
            query_results.append(
                {
                    "query_type": query["type"],
                    "metrics": metrics,
                    "regressions": regressions,
                }
            )
            # Analytics queries can be slower
            assert (
                metrics.avg_response_time <= 5.0
            ), f"{query['type']} avg {metrics.avg_response_time:.3f}s exceeds 5s"
        return query_results
    @pytest.mark.asyncio
    async def test_integration_caching_performance(self, perf_tester):
        """Test BI integration caching performance"""
        base_url = "http://localhost:8082"
        # Test different integration endpoints
        integration_tests = [
            {"integration": "apollo", "endpoint": "/integrations/apollo/companies"},
            {"integration": "hubspot", "endpoint": "/integrations/hubspot/deals"},
            {"integration": "gong", "endpoint": "/integrations/gong/calls"},
        ]
        integration_results = []
        for test in integration_tests:
            # First request (cache miss)
            cache_miss_metrics = await perf_tester.benchmark_endpoint(
                component="bi_server",
                test_name=f"{test['integration']}_cache_miss",
                url=f"{base_url}{test['endpoint']}",
                method="GET",
                concurrent_requests=3,
                total_requests=15,
            )
            # Second request (should be cached)
            cache_hit_metrics = await perf_tester.benchmark_endpoint(
                component="bi_server",
                test_name=f"{test['integration']}_cache_hit",
                url=f"{base_url}{test['endpoint']}",
                method="GET",
                concurrent_requests=10,
                total_requests=50,
            )
            # Cache hits should be significantly faster
            cache_improvement = (
                cache_miss_metrics.avg_response_time
                - cache_hit_metrics.avg_response_time
            ) / cache_miss_metrics.avg_response_time
            integration_results.append(
                {
                    "integration": test["integration"],
                    "cache_miss_metrics": cache_miss_metrics,
                    "cache_hit_metrics": cache_hit_metrics,
                    "cache_improvement": cache_improvement,
                }
            )
            assert (
                cache_improvement >= 0.5
            ), f"{test['integration']} cache only improved by {cache_improvement:.1%}"
            print(
                f"   {test['integration']} cache improvement: {cache_improvement:.1%}"
            )
        return integration_results
class TestSystemWidePerformance:
    """System-wide performance regression tests"""
    @pytest.fixture
    async def perf_tester(self):
        db = PerformanceDatabase("test_performance.db")
        tester = PerformanceTester(db)
        await tester.setup()
        yield tester
        await tester.teardown()
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_performance(self, perf_tester):
        """Test complete end-to-end workflow performance"""
        # Simulate complete user workflow
        workflow_steps = [
            # Step 1: Create customer in BI system
            {
                "name": "create_customer",
                "url": "http://localhost:8082/customers",
                "method": "POST",
                "payload": {"name": "Test Corp", "industry": "Technology"},
            },
            # Step 2: Store context in memory
            {
                "name": "store_context",
                "url": "http://localhost:8083/memories",
                "method": "POST",
                "payload": {
                    "content": "Customer onboarding context",
                    "memory_type": "episodic",
                },
            },
            # Step 3: Create workflow in 
            {
                "name": "create_workflow",
                "url": "http://localhost:8081/workflows",
                "method": "POST",
                "payload": {"workflow_type": "customer_onboarding", "priority": "high"},
            },
            # Step 4: Route through Unified MCP
            {
                "name": "unified_routing",
                "url": "${SOPHIA_API_ENDPOINT}/route",
                "method": "POST",
                "payload": {"target": "", "request": {"type": "status_check"}},
            },
        ]
        workflow_results = []
        for step in workflow_steps:
            print(f"   Testing {step['name']}...")
            metrics = await perf_tester.benchmark_endpoint(
                component="system_wide",
                test_name=step["name"],
                url=step["url"],
                method=step["method"],
                payload=step["payload"],
                concurrent_requests=5,
                total_requests=25,
            )
            regressions = perf_tester.analyze_regression(f"e2e_{step['name']}", metrics)
            workflow_results.append(
                {"step": step["name"], "metrics": metrics, "regressions": regressions}
            )
        # Calculate total workflow time
        total_avg_time = sum(
            result["metrics"].avg_response_time for result in workflow_results
        )
        total_p95_time = sum(
            result["metrics"].p95_response_time for result in workflow_results
        )
        print(
            f"   Total E2E workflow time: {total_avg_time:.3f}s avg, {total_p95_time:.3f}s P95"
        )
        # End-to-end workflow should complete reasonably quickly
        assert (
            total_avg_time <= 2.0
        ), f"E2E workflow avg {total_avg_time:.3f}s exceeds 2s"
        assert (
            total_p95_time <= 5.0
        ), f"E2E workflow P95 {total_p95_time:.3f}s exceeds 5s"
        return workflow_results
    @pytest.mark.asyncio
    async def test_system_stability_under_load(self, perf_tester):
        """Test system stability under sustained load"""
        # Run sustained load test across all services
        services = [
            ("unified_mcp", "${SOPHIA_API_ENDPOINT}/health"),
            ("", "http://localhost:8081/health"),
            ("bi_server", "http://localhost:8082/health"),
            ("mem0", "http://localhost:8083/health"),
        ]
        # Run load test for 2 minutes
        load_duration = 120  # 2 minutes
        concurrent_requests = 20
        stability_results = []
        for service_name, health_url in services:
            print(f"   Load testing {service_name} for {load_duration}s...")
            # Calculate requests needed for duration
            requests_per_second = 10
            total_requests = load_duration * requests_per_second
            start_time = time.time()
            metrics = await perf_tester.benchmark_endpoint(
                component="system_stability",
                test_name=f"{service_name}_sustained_load",
                url=health_url,
                method="GET",
                concurrent_requests=concurrent_requests,
                total_requests=total_requests,
            )
            actual_duration = time.time() - start_time
            actual_rps = metrics.throughput
            stability_results.append(
                {
                    "service": service_name,
                    "metrics": metrics,
                    "actual_duration": actual_duration,
                    "actual_rps": actual_rps,
                    "target_rps": requests_per_second,
                }
            )
            # Service should maintain stability
            assert (
                metrics.error_rate <= 0.05
            ), f"{service_name} error rate {metrics.error_rate:.1%} exceeds 5% under load"
            assert (
                actual_rps >= requests_per_second * 0.8
            ), f"{service_name} RPS {actual_rps:.1f} below 80% of target"
            print(
                f"     {service_name}: {actual_rps:.1f} RPS, {metrics.error_rate:.1%} errors"
            )
        return stability_results
if __name__ == "__main__":
    # Run performance regression tests
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--durations=20",  # Show 20 slowest tests
            "-m",
            "not slow",  # Skip slow tests by default
        ]
    )
