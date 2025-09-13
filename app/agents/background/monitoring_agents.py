#!/usr/bin/env python3
"""
Background Monitoring Agents for Sophia-Intel-AI
Provides continuous system health monitoring and auto-remediation
"""
import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import psutil
from app.core.websocket_manager import WebSocketManager
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@dataclass
class HealthMetric:
    """Health metric data point"""
    name: str
    value: float
    timestamp: datetime
    status: str  # healthy, warning, critical
    metadata: dict[str, Any] = field(default_factory=dict)
@dataclass
class Alert:
    """System alert"""
    level: str  # info, warning, error, critical
    source: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    auto_remediation: Optional[str] = None
class BaseMonitoringAgent:
    """Base class for all monitoring agents"""
    def __init__(self, name: str, check_interval: int = 30):
        self.name = name
        self.check_interval = check_interval
        self.metrics_history: deque[HealthMetric] = deque(maxlen=1000)
        self.alerts: list[Alert] = []
        self.running = False
        self.ws_manager = WebSocketManager()
    async def run_continuous(self):
        """Run continuous monitoring"""
        self.running = True
        logger.info(f"Starting {self.name} monitoring agent")
        while self.running:
            try:
                metrics = await self.collect_metrics()
                await self.analyze_metrics(metrics)
                await self.broadcast_status(metrics)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"{self.name} error: {e}")
                await asyncio.sleep(5)
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect metrics - override in subclasses"""
        raise NotImplementedError
    async def analyze_metrics(self, metrics: list[HealthMetric]):
        """Analyze metrics and generate alerts"""
        for metric in metrics:
            self.metrics_history.append(metric)
            if metric.status == "critical":
                alert = Alert(
                    level="critical",
                    source=self.name,
                    message=f"{metric.name} is critical: {metric.value}",
                )
                await self.send_alert(alert)
            elif metric.status == "warning":
                alert = Alert(
                    level="warning",
                    source=self.name,
                    message=f"{metric.name} warning: {metric.value}",
                )
                await self.send_alert(alert)
    async def send_alert(self, alert: Alert):
        """Send alert via WebSocket and logging"""
        self.alerts.append(alert)
        logger.warning(f"Alert: {alert.message}")
        # Broadcast via WebSocket
        await self.ws_manager.broadcast(
            "monitoring_alerts",
            {
                "type": "monitoring_alert",
                "alert": {
                    "level": alert.level,
                    "source": alert.source,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "remediation": alert.auto_remediation,
                },
            },
        )
    async def broadcast_status(self, metrics: list[HealthMetric]):
        """Broadcast current status via WebSocket"""
        await self.ws_manager.broadcast(
            "monitoring_updates",
            {
                "type": "monitoring_update",
                "agent": self.name,
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "status": m.status,
                        "timestamp": m.timestamp.isoformat(),
                    }
                    for m in metrics
                ],
            },
        )
    def stop(self):
        """Stop monitoring"""
        self.running = False
class MemoryGuardAgent(BaseMonitoringAgent):
    """Monitors memory usage and prevents leaks"""
    def __init__(self):
        super().__init__("MemoryGuard", check_interval=10)
        self.memory_threshold_warning = 70  # %
        self.memory_threshold_critical = 85  # %
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect memory metrics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        metrics = []
        # RAM usage
        ram_percent = memory.percent
        ram_status = self._get_status(ram_percent)
        metrics.append(
            HealthMetric(
                name="ram_usage",
                value=ram_percent,
                timestamp=datetime.now(),
                status=ram_status,
                metadata={
                    "used_gb": memory.used / (1024**3),
                    "total_gb": memory.total / (1024**3),
                },
            )
        )
        # Swap usage
        swap_status = "healthy" if swap.percent < 50 else "warning"
        metrics.append(
            HealthMetric(
                name="swap_usage",
                value=swap.percent,
                timestamp=datetime.now(),
                status=swap_status,
            )
        )
        # Auto-remediation if critical
        if ram_status == "critical":
            await self.auto_cleanup_memory()
        return metrics
    def _get_status(self, percent: float) -> str:
        """Get status based on threshold"""
        if percent >= self.memory_threshold_critical:
            return "critical"
        elif percent >= self.memory_threshold_warning:
            return "warning"
        return "healthy"
    async def auto_cleanup_memory(self):
        """Automatic memory cleanup"""
        logger.info("Initiating automatic memory cleanup")
        # Clear caches
        import gc
        gc.collect()
        # Send cleanup alert
        alert = Alert(
            level="info",
            source=self.name,
            message="Automatic memory cleanup initiated",
            auto_remediation="Garbage collection and cache clearing",
        )
        await self.send_alert(alert)
class CostTrackerAgent(BaseMonitoringAgent):
    """Tracks LLM API costs and usage"""
    def __init__(self):
        super().__init__("CostTracker", check_interval=60)
        self.daily_budget = 100.0  # $100 default
        self.costs_by_provider = defaultdict(float)
        self.requests_by_provider = defaultdict(int)
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect cost metrics"""
        metrics = []
        # Calculate total daily cost
        total_cost = sum(self.costs_by_provider.values())
        budget_percent = (total_cost / self.daily_budget) * 100
        status = "healthy"
        if budget_percent > 90:
            status = "critical"
        elif budget_percent > 70:
            status = "warning"
        metrics.append(
            HealthMetric(
                name="daily_cost",
                value=total_cost,
                timestamp=datetime.now(),
                status=status,
                metadata={
                    "budget_percent": budget_percent,
                    "providers": dict(self.costs_by_provider),
                },
            )
        )
        # Track cost per provider
        for provider, cost in self.costs_by_provider.items():
            metrics.append(
                HealthMetric(
                    name=f"cost_{provider}",
                    value=cost,
                    timestamp=datetime.now(),
                    status="healthy",
                    metadata={"requests": self.requests_by_provider[provider]},
                )
            )
        return metrics
    def track_request(self, provider: str, cost: float):
        """Track an LLM request"""
        self.costs_by_provider[provider] += cost
        self.requests_by_provider[provider] += 1
class PerformanceAgent(BaseMonitoringAgent):
    """Monitors system performance metrics"""
    def __init__(self):
        super().__init__("Performance", check_interval=15)
        self.response_times: deque[float] = deque(maxlen=100)
        self.error_count = 0
        self.success_count = 0
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect performance metrics"""
        metrics = []
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = (
            "healthy"
            if cpu_percent < 70
            else "warning" if cpu_percent < 90 else "critical"
        )
        metrics.append(
            HealthMetric(
                name="cpu_usage",
                value=cpu_percent,
                timestamp=datetime.now(),
                status=cpu_status,
            )
        )
        # Response time (if available)
        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)
            p95_response = sorted(self.response_times)[
                int(len(self.response_times) * 0.95)
            ]
            response_status = (
                "healthy"
                if p95_response < 1000
                else "warning" if p95_response < 3000 else "critical"
            )
            metrics.append(
                HealthMetric(
                    name="response_time_p95",
                    value=p95_response,
                    timestamp=datetime.now(),
                    status=response_status,
                    metadata={"avg": avg_response},
                )
            )
        # Error rate
        total_requests = self.error_count + self.success_count
        if total_requests > 0:
            error_rate = (self.error_count / total_requests) * 100
            error_status = (
                "healthy"
                if error_rate < 1
                else "warning" if error_rate < 5 else "critical"
            )
            metrics.append(
                HealthMetric(
                    name="error_rate",
                    value=error_rate,
                    timestamp=datetime.now(),
                    status=error_status,
                )
            )
        return metrics
    def track_response(self, response_time: float, success: bool):
        """Track a response"""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
class LogMonitorAgent(BaseMonitoringAgent):
    """Monitors application logs for errors and patterns"""
    def __init__(self, log_path: str = "logs/app.log"):
        super().__init__("LogMonitor", check_interval=30)
        self.log_path = Path(log_path)
        self.last_position = 0
        self.error_patterns = ["ERROR", "CRITICAL", "Exception", "Failed", "Timeout"]
        self.error_counts = defaultdict(int)
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect log metrics"""
        metrics = []
        if not self.log_path.exists():
            return metrics
        # Read new log entries
        with open(self.log_path) as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()
        # Analyze new lines
        for line in new_lines:
            for pattern in self.error_patterns:
                if pattern in line:
                    self.error_counts[pattern] += 1
        # Create metrics
        total_errors = sum(self.error_counts.values())
        status = (
            "healthy"
            if total_errors < 10
            else "warning" if total_errors < 50 else "critical"
        )
        metrics.append(
            HealthMetric(
                name="log_errors",
                value=total_errors,
                timestamp=datetime.now(),
                status=status,
                metadata={"error_types": dict(self.error_counts)},
            )
        )
        return metrics
class HealthCheckAgent(BaseMonitoringAgent):
    """Performs health checks on critical services"""
    def __init__(self):
        super().__init__("HealthCheck", check_interval=60)
        self.services = {
            "database": self.check_database,
            "redis": self.check_redis,
            "llm_providers": self.check_llm_providers,
        }
    async def collect_metrics(self) -> list[HealthMetric]:
        """Collect health check metrics"""
        metrics = []
        for service_name, check_func in self.services.items():
            try:
                is_healthy = await check_func()
                status = "healthy" if is_healthy else "critical"
                value = 1.0 if is_healthy else 0.0
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                status = "critical"
                value = 0.0
            metrics.append(
                HealthMetric(
                    name=f"health_{service_name}",
                    value=value,
                    timestamp=datetime.now(),
                    status=status,
                )
            )
        return metrics
    async def check_database(self) -> bool:
        """Check database connectivity"""
        # Implement actual database check
        return True  # Placeholder
    async def check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            return True
        except:
            return False
    async def check_llm_providers(self) -> bool:
        """Check LLM provider availability"""
        # Check if at least 3 providers are available
        # This would integrate with the LLM connection checker
        return True  # Placeholder
class BackgroundAgentManager:
    """Manages all background monitoring agents"""
    def __init__(self):
        self.agents = {
            "memory_guard": MemoryGuardAgent(),
            "cost_tracker": CostTrackerAgent(),
            "performance": PerformanceAgent(),
            "log_monitor": LogMonitorAgent(),
            "health_check": HealthCheckAgent(),
        }
        self.tasks = []
    async def start_all(self):
        """Start all monitoring agents"""
        logger.info("Starting all background monitoring agents")
        for name, agent in self.agents.items():
            task = asyncio.create_task(agent.run_continuous())
            self.tasks.append(task)
            logger.info(f"Started {name} agent")
        # Start dashboard updater
        asyncio.create_task(self.update_dashboard())
    async def stop_all(self):
        """Stop all monitoring agents"""
        logger.info("Stopping all background monitoring agents")
        for agent in self.agents.values():
            agent.stop()
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
    async def update_dashboard(self):
        """Update monitoring dashboard periodically"""
        while True:
            try:
                dashboard_data = self.get_dashboard_data()
                await self.broadcast_dashboard(dashboard_data)
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(10)
    def get_dashboard_data(self) -> dict[str, Any]:
        """Get current dashboard data"""
        data = {"timestamp": datetime.now().isoformat(), "agents": {}}
        for name, agent in self.agents.items():
            # Get latest metrics
            latest_metrics = (
                list(agent.metrics_history)[-10:] if agent.metrics_history else []
            )
            data["agents"][name] = {
                "status": "running" if agent.running else "stopped",
                "alerts": len(agent.alerts),
                "latest_metrics": [
                    {"name": m.name, "value": m.value, "status": m.status}
                    for m in latest_metrics
                ],
            }
        return data
    async def broadcast_dashboard(self, data: dict[str, Any]):
        """Broadcast dashboard data via WebSocket"""
        ws_manager = WebSocketManager()
        await ws_manager.broadcast(
            "monitoring_dashboard", {"type": "monitoring_dashboard", "data": data}
        )
    def get_agent(self, name: str) -> Optional[BaseMonitoringAgent]:
        """Get specific agent"""
        return self.agents.get(name)
# Singleton instance
_manager_instance = None
def get_monitoring_manager() -> BackgroundAgentManager:
    """Get singleton monitoring manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = BackgroundAgentManager()
    return _manager_instance
async def main():
    """Test monitoring agents"""
    manager = get_monitoring_manager()
    await manager.start_all()
    # Run for a while
    await asyncio.sleep(300)  # 5 minutes
    await manager.stop_all()
if __name__ == "__main__":
    asyncio.run(main())
