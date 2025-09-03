"""
Performance Benchmarking System for Business Intelligence Integrations

This module provides comprehensive performance testing and benchmarking for all BI integrations:
- Response time measurements
- Throughput testing
- Concurrent user simulation
- Load testing scenarios
- Performance regression detection
- SLA compliance monitoring
"""

import asyncio
import time
import statistics
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import httpx
import logging
import psutil
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for a single request"""
    endpoint: str
    method: str = "GET"
    response_time_ms: float = 0.0
    status_code: int = 0
    response_size_bytes: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_message: Optional[str] = None
    connection_time_ms: float = 0.0
    dns_time_ms: float = 0.0
    ssl_time_ms: float = 0.0

@dataclass  
class BenchmarkConfig:
    """Configuration for performance benchmarks"""
    name: str
    endpoint: str
    method: str = "GET"
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    concurrent_users: int = 1
    total_requests: int = 10
    duration_seconds: Optional[int] = None
    ramp_up_seconds: int = 0
    think_time_ms: int = 0
    timeout_seconds: int = 30
    
@dataclass
class SLAThresholds:
    """SLA performance thresholds"""
    max_response_time_ms: float = 5000
    max_p95_response_time_ms: float = 8000
    max_p99_response_time_ms: float = 15000
    min_success_rate: float = 0.95
    max_error_rate: float = 0.05
    min_throughput_rps: float = 1.0

@dataclass
class BenchmarkResults:
    """Results from performance benchmark"""
    config: BenchmarkConfig
    start_time: datetime
    end_time: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    metrics: List[PerformanceMetrics] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        return self.failed_requests / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def throughput_rps(self) -> float:
        return self.total_requests / self.duration_seconds if self.duration_seconds > 0 else 0.0
    
    @property 
    def avg_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        return statistics.mean(response_times) if response_times else 0.0
    
    @property
    def median_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        return statistics.median(response_times) if response_times else 0.0
    
    @property
    def p95_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        if response_times:
            return sorted(response_times)[int(len(response_times) * 0.95)]
        return 0.0
    
    @property
    def p99_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        if response_times:
            return sorted(response_times)[int(len(response_times) * 0.99)]
        return 0.0
    
    @property
    def min_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        return min(response_times) if response_times else 0.0
    
    @property
    def max_response_time_ms(self) -> float:
        response_times = [m.response_time_ms for m in self.metrics if m.success]
        return max(response_times) if response_times else 0.0

class SystemResourceMonitor:
    """Monitor system resources during performance tests"""
    
    def __init__(self):
        self.monitoring = False
        self.samples: List[Dict[str, Any]] = []
        
    async def start_monitoring(self, interval_seconds: float = 1.0):
        """Start monitoring system resources"""
        self.monitoring = True
        self.samples = []
        
        while self.monitoring:
            sample = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
                "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
            self.samples.append(sample)
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop monitoring system resources"""
        self.monitoring = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        if not self.samples:
            return {"error": "No samples collected"}
        
        cpu_values = [s["cpu_percent"] for s in self.samples if s["cpu_percent"] is not None]
        memory_values = [s["memory_percent"] for s in self.samples]
        
        return {
            "sample_count": len(self.samples),
            "duration_seconds": self.samples[-1]["timestamp"] - self.samples[0]["timestamp"],
            "cpu": {
                "avg_percent": statistics.mean(cpu_values) if cpu_values else 0,
                "max_percent": max(cpu_values) if cpu_values else 0,
                "min_percent": min(cpu_values) if cpu_values else 0
            },
            "memory": {
                "avg_percent": statistics.mean(memory_values),
                "max_percent": max(memory_values),
                "min_percent": min(memory_values),
                "avg_used_mb": statistics.mean([s["memory_used_mb"] for s in self.samples]),
                "max_used_mb": max([s["memory_used_mb"] for s in self.samples])
            }
        }

class BIPerformanceBenchmarker:
    """Main performance benchmarking class for BI integrations"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3333"):
        self.base_url = base_url
        self.resource_monitor = SystemResourceMonitor()
        self.benchmark_history: List[BenchmarkResults] = []
        
    # ==============================================================================
    # INDIVIDUAL REQUEST PERFORMANCE 
    # ==============================================================================
    
    async def measure_single_request(self, config: BenchmarkConfig) -> PerformanceMetrics:
        """Measure performance of a single request"""
        
        url = f"{self.base_url}{config.endpoint}"
        headers = config.headers or {}
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                if config.method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif config.method.upper() == "POST":
                    response = await client.post(url, json=config.payload, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {config.method}")
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                return PerformanceMetrics(
                    endpoint=config.endpoint,
                    method=config.method,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    response_size_bytes=len(response.content),
                    success=response.status_code < 400,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return PerformanceMetrics(
                endpoint=config.endpoint,
                method=config.method,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    # ==============================================================================
    # LOAD TESTING 
    # ==============================================================================
    
    async def run_load_test(self, config: BenchmarkConfig) -> BenchmarkResults:
        """Run load test with specified configuration"""
        
        logger.info(f"Starting load test: {config.name}")
        logger.info(f"Endpoint: {config.endpoint}")
        logger.info(f"Concurrent users: {config.concurrent_users}")
        logger.info(f"Total requests: {config.total_requests}")
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())
        
        start_time = datetime.now()
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def make_request() -> PerformanceMetrics:
            async with semaphore:
                metric = await self.measure_single_request(config)
                if config.think_time_ms > 0:
                    await asyncio.sleep(config.think_time_ms / 1000)
                return metric
        
        # Create tasks for all requests
        tasks = []
        
        if config.duration_seconds:
            # Duration-based test
            end_time = time.time() + config.duration_seconds
            while time.time() < end_time:
                task = asyncio.create_task(make_request())
                tasks.append(task)
                
                # Add ramp-up delay
                if config.ramp_up_seconds > 0:
                    delay = config.ramp_up_seconds / config.concurrent_users
                    await asyncio.sleep(delay)
        else:
            # Request count-based test
            for i in range(config.total_requests):
                task = asyncio.create_task(make_request())
                tasks.append(task)
                
                # Add ramp-up delay
                if config.ramp_up_seconds > 0 and i % config.concurrent_users == 0:
                    delay = config.ramp_up_seconds / (config.total_requests / config.concurrent_users)
                    await asyncio.sleep(delay)
        
        # Wait for all requests to complete
        metrics = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        monitor_task.cancel()
        
        end_time = datetime.now()
        
        # Filter out exceptions and process metrics
        valid_metrics = [m for m in metrics if isinstance(m, PerformanceMetrics)]
        
        successful_requests = sum(1 for m in valid_metrics if m.success)
        failed_requests = len(valid_metrics) - successful_requests
        
        results = BenchmarkResults(
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_requests=len(valid_metrics),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            metrics=valid_metrics
        )
        
        self.benchmark_history.append(results)
        
        logger.info(f"Load test completed: {config.name}")
        logger.info(f"Requests: {results.total_requests}")
        logger.info(f"Success rate: {results.success_rate:.2%}")
        logger.info(f"Avg response time: {results.avg_response_time_ms:.2f}ms")
        logger.info(f"Throughput: {results.throughput_rps:.2f} RPS")
        
        return results
    
    # ==============================================================================
    # BENCHMARK SUITES
    # ==============================================================================
    
    async def run_standard_benchmark_suite(self) -> Dict[str, BenchmarkResults]:
        """Run standard benchmark suite for all BI endpoints"""
        
        benchmark_configs = [
            # Basic connectivity tests
            BenchmarkConfig(
                name="health_check_baseline",
                endpoint="/healthz",
                concurrent_users=1,
                total_requests=5
            ),
            
            # Gong integration performance
            BenchmarkConfig(
                name="gong_calls_light_load",
                endpoint="/business/gong/recent?days=7",
                concurrent_users=2,
                total_requests=20
            ),
            BenchmarkConfig(
                name="gong_calls_medium_load", 
                endpoint="/business/gong/recent?days=30",
                concurrent_users=5,
                total_requests=50
            ),
            
            # CRM integration performance
            BenchmarkConfig(
                name="crm_contacts_performance",
                endpoint="/api/business/crm/contacts?limit=50",
                concurrent_users=3,
                total_requests=30
            ),
            BenchmarkConfig(
                name="crm_pipeline_performance",
                endpoint="/api/business/crm/pipeline",
                concurrent_users=2,
                total_requests=20
            ),
            
            # Business dashboard performance
            BenchmarkConfig(
                name="dashboard_load_test",
                endpoint="/api/business/dashboard",
                concurrent_users=4,
                total_requests=40
            ),
            
            # Projects overview performance
            BenchmarkConfig(
                name="projects_overview_stress",
                endpoint="/api/business/projects/overview",
                concurrent_users=3,
                total_requests=25
            ),
            
            # Workflow automation performance
            BenchmarkConfig(
                name="workflow_trigger_performance",
                endpoint="/api/business/workflows/trigger",
                method="POST",
                payload={"type": "lead_qualification"},
                concurrent_users=2,
                total_requests=15
            ),
            
            # High concurrency test
            BenchmarkConfig(
                name="high_concurrency_test",
                endpoint="/api/business/dashboard",
                concurrent_users=10,
                total_requests=100,
                ramp_up_seconds=5
            )
        ]
        
        results = {}
        
        for config in benchmark_configs:
            try:
                logger.info(f"\n🚀 Running benchmark: {config.name}")
                result = await self.run_load_test(config)
                results[config.name] = result
                
                # Brief pause between tests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Benchmark failed: {config.name} - {str(e)}")
        
        return results
    
    # ==============================================================================
    # SLA COMPLIANCE CHECKING
    # ==============================================================================
    
    def check_sla_compliance(self, results: BenchmarkResults, 
                           thresholds: Optional[SLAThresholds] = None) -> Dict[str, Any]:
        """Check if benchmark results meet SLA thresholds"""
        
        thresholds = thresholds or SLAThresholds()
        
        compliance = {
            "overall_compliant": True,
            "checks": {},
            "violations": [],
            "summary": {}
        }
        
        # Response time checks
        checks = [
            ("max_response_time", results.max_response_time_ms <= thresholds.max_response_time_ms),
            ("p95_response_time", results.p95_response_time_ms <= thresholds.max_p95_response_time_ms),
            ("p99_response_time", results.p99_response_time_ms <= thresholds.max_p99_response_time_ms),
            ("success_rate", results.success_rate >= thresholds.min_success_rate),
            ("error_rate", results.error_rate <= thresholds.max_error_rate),
            ("throughput", results.throughput_rps >= thresholds.min_throughput_rps)
        ]
        
        for check_name, passed in checks:
            compliance["checks"][check_name] = passed
            if not passed:
                compliance["overall_compliant"] = False
                compliance["violations"].append(check_name)
        
        # Detailed summary
        compliance["summary"] = {
            "max_response_time_ms": results.max_response_time_ms,
            "p95_response_time_ms": results.p95_response_time_ms,
            "p99_response_time_ms": results.p99_response_time_ms,
            "success_rate": results.success_rate,
            "error_rate": results.error_rate,
            "throughput_rps": results.throughput_rps,
            "thresholds": {
                "max_response_time_ms": thresholds.max_response_time_ms,
                "max_p95_response_time_ms": thresholds.max_p95_response_time_ms,
                "max_p99_response_time_ms": thresholds.max_p99_response_time_ms,
                "min_success_rate": thresholds.min_success_rate,
                "max_error_rate": thresholds.max_error_rate,
                "min_throughput_rps": thresholds.min_throughput_rps
            }
        }
        
        return compliance
    
    # ==============================================================================
    # PERFORMANCE REGRESSION DETECTION
    # ==============================================================================
    
    def detect_performance_regression(self, current: BenchmarkResults, 
                                    baseline: BenchmarkResults,
                                    regression_threshold: float = 0.2) -> Dict[str, Any]:
        """Detect performance regression compared to baseline"""
        
        regression_analysis = {
            "regression_detected": False,
            "metrics_comparison": {},
            "significant_changes": [],
            "summary": {}
        }
        
        # Compare key metrics
        comparisons = [
            ("avg_response_time_ms", current.avg_response_time_ms, baseline.avg_response_time_ms),
            ("p95_response_time_ms", current.p95_response_time_ms, baseline.p95_response_time_ms),
            ("p99_response_time_ms", current.p99_response_time_ms, baseline.p99_response_time_ms),
            ("success_rate", current.success_rate, baseline.success_rate),
            ("throughput_rps", current.throughput_rps, baseline.throughput_rps)
        ]
        
        for metric_name, current_value, baseline_value in comparisons:
            if baseline_value > 0:
                change_ratio = (current_value - baseline_value) / baseline_value
                change_percent = change_ratio * 100
                
                regression_analysis["metrics_comparison"][metric_name] = {
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": change_percent,
                    "regression": False
                }
                
                # Check for significant regression
                if metric_name in ["avg_response_time_ms", "p95_response_time_ms", "p99_response_time_ms"]:
                    # Higher response times are regressions
                    if change_ratio > regression_threshold:
                        regression_analysis["regression_detected"] = True
                        regression_analysis["metrics_comparison"][metric_name]["regression"] = True
                        regression_analysis["significant_changes"].append({
                            "metric": metric_name,
                            "type": "degradation",
                            "change_percent": change_percent
                        })
                
                elif metric_name in ["success_rate", "throughput_rps"]:
                    # Lower success rate/throughput are regressions  
                    if change_ratio < -regression_threshold:
                        regression_analysis["regression_detected"] = True
                        regression_analysis["metrics_comparison"][metric_name]["regression"] = True
                        regression_analysis["significant_changes"].append({
                            "metric": metric_name,
                            "type": "degradation", 
                            "change_percent": change_percent
                        })
        
        return regression_analysis
    
    # ==============================================================================
    # REPORTING AND EXPORT
    # ==============================================================================
    
    def generate_performance_report(self, results: Dict[str, BenchmarkResults], 
                                  sla_thresholds: Optional[SLAThresholds] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_benchmarks": len(results),
                "total_requests": sum(r.total_requests for r in results.values()),
                "total_duration_seconds": sum(r.duration_seconds for r in results.values()),
                "overall_success_rate": sum(r.successful_requests for r in results.values()) / 
                                      sum(r.total_requests for r in results.values()) if results else 0
            },
            "benchmark_results": {},
            "sla_compliance": {},
            "system_resources": self.resource_monitor.get_summary(),
            "recommendations": []
        }
        
        # Process each benchmark result
        for name, result in results.items():
            # Basic metrics
            report["benchmark_results"][name] = {
                "config": {
                    "endpoint": result.config.endpoint,
                    "method": result.config.method,
                    "concurrent_users": result.config.concurrent_users,
                    "total_requests": result.config.total_requests
                },
                "performance": {
                    "duration_seconds": result.duration_seconds,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "success_rate": result.success_rate,
                    "error_rate": result.error_rate,
                    "throughput_rps": result.throughput_rps,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "median_response_time_ms": result.median_response_time_ms,
                    "p95_response_time_ms": result.p95_response_time_ms,
                    "p99_response_time_ms": result.p99_response_time_ms,
                    "min_response_time_ms": result.min_response_time_ms,
                    "max_response_time_ms": result.max_response_time_ms
                }
            }
            
            # SLA compliance check
            if sla_thresholds:
                compliance = self.check_sla_compliance(result, sla_thresholds)
                report["sla_compliance"][name] = compliance
        
        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(results)
        
        return report
    
    def _generate_performance_recommendations(self, results: Dict[str, BenchmarkResults]) -> List[str]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        
        # Analyze results for patterns
        high_response_times = []
        low_success_rates = []
        low_throughput = []
        
        for name, result in results.items():
            if result.avg_response_time_ms > 5000:
                high_response_times.append(name)
            
            if result.success_rate < 0.95:
                low_success_rates.append(name)
            
            if result.throughput_rps < 1.0:
                low_throughput.append(name)
        
        # Generate specific recommendations
        if high_response_times:
            recommendations.append(
                f"High response times detected in: {', '.join(high_response_times)}. "
                "Consider optimizing database queries, adding caching, or scaling backend services."
            )
        
        if low_success_rates:
            recommendations.append(
                f"Low success rates in: {', '.join(low_success_rates)}. "
                "Investigate error handling, increase timeout values, or improve retry logic."
            )
        
        if low_throughput:
            recommendations.append(
                f"Low throughput in: {', '.join(low_throughput)}. "
                "Consider horizontal scaling, connection pooling, or async processing."
            )
        
        # Resource-based recommendations
        resource_summary = self.resource_monitor.get_summary()
        if resource_summary.get("cpu", {}).get("max_percent", 0) > 80:
            recommendations.append("High CPU usage detected. Consider CPU optimization or scaling.")
        
        if resource_summary.get("memory", {}).get("max_percent", 0) > 85:
            recommendations.append("High memory usage detected. Investigate memory leaks or increase memory allocation.")
        
        return recommendations
    
    def export_results(self, results: Dict[str, BenchmarkResults], filename: str = None):
        """Export benchmark results to JSON file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bi_performance_benchmark_{timestamp}.json"
        
        # Generate comprehensive report
        report = self.generate_performance_report(results)
        
        # Export to file
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance report exported to: {output_path.absolute()}")
        return output_path

# ==============================================================================
# COMMAND LINE INTERFACE  
# ==============================================================================

async def main():
    """Main function for running performance benchmarks"""
    
    print("⚡ BI Integration Performance Benchmarking")
    print("=" * 60)
    
    benchmarker = BIPerformanceBenchmarker()
    
    try:
        # Run standard benchmark suite
        print("\n🚀 Running standard benchmark suite...")
        results = await benchmarker.run_standard_benchmark_suite()
        
        print(f"\n✅ Completed {len(results)} benchmarks")
        
        # Generate and display summary
        report = benchmarker.generate_performance_report(results)
        
        print(f"\n📊 Performance Summary:")
        print(f"Total requests: {report['test_summary']['total_requests']}")
        print(f"Overall success rate: {report['test_summary']['overall_success_rate']:.2%}")
        
        # Show top performers and problem areas
        best_performance = min(results.items(), key=lambda x: x[1].avg_response_time_ms)
        worst_performance = max(results.items(), key=lambda x: x[1].avg_response_time_ms)
        
        print(f"\n🏆 Best performance: {best_performance[0]} ({best_performance[1].avg_response_time_ms:.2f}ms avg)")
        print(f"⚠️  Needs attention: {worst_performance[0]} ({worst_performance[1].avg_response_time_ms:.2f}ms avg)")
        
        # Export detailed report
        output_file = benchmarker.export_results(results)
        print(f"\n📄 Detailed report saved to: {output_file}")
        
        # Show recommendations
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. {rec}")
        
        print(f"\n🎯 Performance benchmarking complete!")
        
    except Exception as e:
        logger.error(f"Benchmarking failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())