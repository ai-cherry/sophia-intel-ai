"""
Sophia AI Fusion Systems - Performance Monitoring System
Week 2: Performance Optimization Implementation
Advanced performance monitoring with P95 latency tracking, endpoint-specific metrics,
and real-time alerting. Target: P95 latency <100ms with comprehensive observability.
"""
import asyncio
import json
import logging
import statistics
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
import numpy as np
import psutil
import redis.asyncio as redis
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@dataclass
class EndpointMetrics:
    """Metrics for a specific API endpoint"""
    endpoint: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    min_response_time_ms: float = float("inf")
    max_response_time_ms: float = 0.0
    error_rate: float = 0.0
    requests_per_minute: float = 0.0
    last_request_time: str = ""
    response_times: List[float] = field(default_factory=list)
@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    active_connections: int = 0
    load_average: List[float] = field(default_factory=list)
    timestamp: str = ""
@dataclass
class PerformanceAlert:
    """Performance alert definition"""
    alert_id: str
    severity: str  # 'warning', 'critical'
    message: str
    threshold: float
    current_value: float
    endpoint: Optional[str] = None
    timestamp: str = ""
    acknowledged: bool = False
class PerformanceMonitor:
    """
    Advanced performance monitoring system with real-time metrics collection
    """
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6380):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        # In-memory metrics storage
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.system_metrics_history: deque = deque(
            maxlen=1000
        )  # Keep last 1000 data points
        self.active_alerts: List[PerformanceAlert] = []
        # Configuration
        self.max_response_times = 1000  # Keep last 1000 response times per endpoint
        self.alert_thresholds = {
            "p95_latency_ms": 100.0,  # Alert if P95 > 100ms
            "error_rate_percent": 5.0,  # Alert if error rate > 5%
            "cpu_usage_percent": 80.0,  # Alert if CPU > 80%
            "memory_usage_percent": 85.0,  # Alert if memory > 85%
        }
        # Monitoring state
        self.monitoring_active = False
        self.last_system_check = time.time()
    async def connect(self) -> bool:
        """Connect to Redis for metrics persistence"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=2,  # Use separate DB for performance metrics
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(
                f"✅ Performance monitor connected to Redis at {self.redis_host}:{self.redis_port}"
            )
            # Load existing metrics
            await self._load_metrics()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.is_connected = False
            return False
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self._save_metrics()
            await self.redis_client.close()
            self.is_connected = False
            logger.info("🔌 Performance monitor disconnected from Redis")
    def track_request(self, endpoint: str, method: str = "GET"):
        """
        Decorator to track request performance
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                try:
                    # Execute the function
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    # Record metrics
                    response_time = (time.time() - start_time) * 1000
                    await self._record_request_metrics(
                        endpoint, method, response_time, success, error_message
                    )
            return wrapper
        return decorator
    async def _record_request_metrics(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Record metrics for a request"""
        endpoint_key = f"{method}:{endpoint}"
        # Get or create endpoint metrics
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = EndpointMetrics(
                endpoint=endpoint, method=method
            )
        metrics = self.endpoint_metrics[endpoint_key]
        # Update basic counters
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        # Update response times
        metrics.response_times.append(response_time_ms)
        if len(metrics.response_times) > self.max_response_times:
            metrics.response_times.pop(0)  # Remove oldest
        # Calculate statistics
        if metrics.response_times:
            metrics.avg_response_time_ms = statistics.mean(metrics.response_times)
            metrics.min_response_time_ms = min(metrics.response_times)
            metrics.max_response_time_ms = max(metrics.response_times)
            # Calculate percentiles
            sorted_times = sorted(metrics.response_times)
            metrics.p50_response_time_ms = np.percentile(sorted_times, 50)
            metrics.p95_response_time_ms = np.percentile(sorted_times, 95)
            metrics.p99_response_time_ms = np.percentile(sorted_times, 99)
        # Calculate error rate
        metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100
        # Update timestamp
        metrics.last_request_time = datetime.now().isoformat()
        # Calculate requests per minute (approximate)
        if metrics.total_requests > 1:
            time_window = 60  # 1 minute
            recent_requests = sum(
                1 for _ in metrics.response_times[-60:]
            )  # Approximate
            metrics.requests_per_minute = recent_requests
        # Check for alerts
        await self._check_endpoint_alerts(endpoint_key, metrics)
        # Log performance issues
        if response_time_ms > self.alert_thresholds["p95_latency_ms"]:
            logger.warning(f"⚠️ Slow request: {endpoint} took {response_time_ms:.1f}ms")
        if not success:
            logger.error(f"❌ Failed request: {endpoint} - {error_message}")
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            # Network metrics
            network = psutil.net_io_counters()
            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]  # Windows fallback
            # Active connections (approximate)
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            metrics = SystemMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections,
                load_average=load_avg,
                timestamp=datetime.now().isoformat(),
            )
            # Store in history
            self.system_metrics_history.append(metrics)
            # Check for system alerts
            await self._check_system_alerts(metrics)
            return metrics
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
            return SystemMetrics(timestamp=datetime.now().isoformat())
    async def _check_endpoint_alerts(self, endpoint_key: str, metrics: EndpointMetrics):
        """Check for endpoint-specific performance alerts"""
        alerts = []
        # P95 latency alert
        if metrics.p95_response_time_ms > self.alert_thresholds["p95_latency_ms"]:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"p95_latency_{endpoint_key}",
                    severity=(
                        "warning" if metrics.p95_response_time_ms < 200 else "critical"
                    ),
                    message=f"High P95 latency on {metrics.endpoint}: {metrics.p95_response_time_ms:.1f}ms",
                    threshold=self.alert_thresholds["p95_latency_ms"],
                    current_value=metrics.p95_response_time_ms,
                    endpoint=metrics.endpoint,
                    timestamp=datetime.now().isoformat(),
                )
            )
        # Error rate alert
        if metrics.error_rate > self.alert_thresholds["error_rate_percent"]:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"error_rate_{endpoint_key}",
                    severity="critical",
                    message=f"High error rate on {metrics.endpoint}: {metrics.error_rate:.1f}%",
                    threshold=self.alert_thresholds["error_rate_percent"],
                    current_value=metrics.error_rate,
                    endpoint=metrics.endpoint,
                    timestamp=datetime.now().isoformat(),
                )
            )
        # Add new alerts
        for alert in alerts:
            if not any(a.alert_id == alert.alert_id for a in self.active_alerts):
                self.active_alerts.append(alert)
                logger.warning(f"🚨 NEW ALERT: {alert.message}")
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system-wide performance alerts"""
        alerts = []
        # CPU usage alert
        if metrics.cpu_usage_percent > self.alert_thresholds["cpu_usage_percent"]:
            alerts.append(
                PerformanceAlert(
                    alert_id="high_cpu_usage",
                    severity=(
                        "warning" if metrics.cpu_usage_percent < 90 else "critical"
                    ),
                    message=f"High CPU usage: {metrics.cpu_usage_percent:.1f}%",
                    threshold=self.alert_thresholds["cpu_usage_percent"],
                    current_value=metrics.cpu_usage_percent,
                    timestamp=datetime.now().isoformat(),
                )
            )
        # Memory usage alert
        if metrics.memory_usage_percent > self.alert_thresholds["memory_usage_percent"]:
            alerts.append(
                PerformanceAlert(
                    alert_id="high_memory_usage",
                    severity=(
                        "warning" if metrics.memory_usage_percent < 95 else "critical"
                    ),
                    message=f"High memory usage: {metrics.memory_usage_percent:.1f}%",
                    threshold=self.alert_thresholds["memory_usage_percent"],
                    current_value=metrics.memory_usage_percent,
                    timestamp=datetime.now().isoformat(),
                )
            )
        # Add new alerts
        for alert in alerts:
            if not any(a.alert_id == alert.alert_id for a in self.active_alerts):
                self.active_alerts.append(alert)
                logger.warning(f"🚨 SYSTEM ALERT: {alert.message}")
    async def get_endpoint_metrics(
        self, endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for specific endpoint or all endpoints"""
        if endpoint:
            # Find matching endpoints
            matching = {k: v for k, v in self.endpoint_metrics.items() if endpoint in k}
            return {k: asdict(v) for k, v in matching.items()}
        else:
            return {k: asdict(v) for k, v in self.endpoint_metrics.items()}
    async def get_system_metrics(self, last_n: int = 100) -> List[Dict[str, Any]]:
        """Get recent system metrics"""
        recent_metrics = list(self.system_metrics_history)[-last_n:]
        return [asdict(m) for m in recent_metrics]
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.endpoint_metrics:
            return {"status": "no_data", "message": "No metrics collected yet"}
        # Calculate overall statistics
        all_p95_times = [
            m.p95_response_time_ms
            for m in self.endpoint_metrics.values()
            if m.p95_response_time_ms > 0
        ]
        all_error_rates = [m.error_rate for m in self.endpoint_metrics.values()]
        total_requests = sum(m.total_requests for m in self.endpoint_metrics.values())
        total_errors = sum(m.failed_requests for m in self.endpoint_metrics.values())
        # Get latest system metrics
        latest_system = (
            self.system_metrics_history[-1] if self.system_metrics_history else None
        )
        summary = {
            "overall_status": "healthy",
            "total_endpoints": len(self.endpoint_metrics),
            "total_requests": total_requests,
            "overall_error_rate": (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            ),
            "avg_p95_latency_ms": (
                statistics.mean(all_p95_times) if all_p95_times else 0
            ),
            "max_p95_latency_ms": max(all_p95_times) if all_p95_times else 0,
            "active_alerts": len(self.active_alerts),
            "critical_alerts": len(
                [a for a in self.active_alerts if a.severity == "critical"]
            ),
            "system_cpu_percent": (
                latest_system.cpu_usage_percent if latest_system else 0
            ),
            "system_memory_percent": (
                latest_system.memory_usage_percent if latest_system else 0
            ),
            "last_updated": datetime.now().isoformat(),
        }
        # Determine overall status
        if summary["critical_alerts"] > 0:
            summary["overall_status"] = "critical"
        elif summary["active_alerts"] > 0:
            summary["overall_status"] = "warning"
        elif summary["avg_p95_latency_ms"] > self.alert_thresholds["p95_latency_ms"]:
            summary["overall_status"] = "degraded"
        return summary
    async def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current alerts, optionally filtered by severity"""
        alerts = self.active_alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return [asdict(a) for a in alerts]
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"✅ Alert acknowledged: {alert_id}")
                return True
        return False
    async def clear_acknowledged_alerts(self):
        """Remove acknowledged alerts"""
        before_count = len(self.active_alerts)
        self.active_alerts = [a for a in self.active_alerts if not a.acknowledged]
        cleared_count = before_count - len(self.active_alerts)
        if cleared_count > 0:
            logger.info(f"🧹 Cleared {cleared_count} acknowledged alerts")
    async def _load_metrics(self):
        """Load metrics from Redis"""
        try:
            # Load endpoint metrics
            endpoint_data = await self.redis_client.get("sophia_perf:endpoints")
            if endpoint_data:
                data = json.loads(endpoint_data)
                for key, metrics_dict in data.items():
                    self.endpoint_metrics[key] = EndpointMetrics(**metrics_dict)
                logger.info(
                    f"📊 Loaded metrics for {len(self.endpoint_metrics)} endpoints"
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not load performance metrics: {e}")
    async def _save_metrics(self):
        """Save metrics to Redis"""
        try:
            # Save endpoint metrics
            endpoint_data = {k: asdict(v) for k, v in self.endpoint_metrics.items()}
            await self.redis_client.setex(
                "sophia_perf:endpoints",
                86400,  # 24 hour TTL
                json.dumps(endpoint_data, default=str),
            )
            logger.debug("💾 Saved performance metrics")
        except Exception as e:
            logger.warning(f"⚠️ Could not save performance metrics: {e}")
    async def start_monitoring(self, interval: int = 30):
        """Start continuous system monitoring"""
        self.monitoring_active = True
        logger.info(f"🔄 Started performance monitoring (interval: {interval}s)")
        while self.monitoring_active:
            try:
                await self.collect_system_metrics()
                await self.clear_acknowledged_alerts()
                # Save metrics periodically
                if time.time() - self.last_system_check > 300:  # Every 5 minutes
                    await self._save_metrics()
                    self.last_system_check = time.time()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("⏹️ Stopped performance monitoring")
    async def health_check(self) -> Dict[str, Any]:
        """Perform performance monitor health check"""
        return {
            "status": "healthy" if self.is_connected else "unhealthy",
            "redis_connected": self.is_connected,
            "monitoring_active": self.monitoring_active,
            "endpoints_tracked": len(self.endpoint_metrics),
            "active_alerts": len(self.active_alerts),
            "system_metrics_points": len(self.system_metrics_history),
            "last_updated": datetime.now().isoformat(),
        }
# Global performance monitor instance
_monitor_instance: Optional[PerformanceMonitor] = None
async def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
        await _monitor_instance.connect()
    return _monitor_instance
# Convenience decorator for tracking endpoint performance
def monitor_performance(endpoint: str, method: str = "GET"):
    """Decorator to monitor endpoint performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = await get_performance_monitor()
            return await monitor.track_request(endpoint, method)(func)(*args, **kwargs)
        return wrapper
    return decorator
# Example usage
@monitor_performance("/api/test", "GET")
async def example_api_endpoint():
    """Example API endpoint with performance monitoring"""
    # Simulate some work
    await asyncio.sleep(0.05)
    return {"status": "success", "data": "test"}
async def sophia_performance_monitor():
    """Test the performance monitoring system"""
    print("🧪 Testing Performance Monitor...")
    monitor = await get_performance_monitor()
    # Test endpoint monitoring
    for i in range(10):
        await example_api_endpoint()
    # Collect system metrics
    system_metrics = await monitor.collect_system_metrics()
    print(
        f"✅ System metrics: CPU {system_metrics.cpu_usage_percent:.1f}%, Memory {system_metrics.memory_usage_percent:.1f}%"
    )
    # Get performance summary
    summary = await monitor.get_performance_summary()
    print(
        f"📊 Performance summary: {summary['overall_status']}, {summary['total_requests']} requests"
    )
    # Get endpoint metrics
    endpoint_metrics = await monitor.get_endpoint_metrics()
    for endpoint, metrics in endpoint_metrics.items():
        print(
            f"🎯 {endpoint}: P95 {metrics['p95_response_time_ms']:.1f}ms, Error rate {metrics['error_rate']:.1f}%"
        )
    return True
if __name__ == "__main__":
    asyncio.run(sophia_performance_monitor())
