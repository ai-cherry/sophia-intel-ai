"""
Redis Health Monitoring Service for Sophia-Intel-AI
Provides comprehensive monitoring, alerting, and automatic recovery
for Redis infrastructure with Pay Ready business cycle awareness.
"""

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from app.core.redis_config import PAY_READY_REDIS_CONFIG
from app.core.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


@dataclass
class HealthAlert:
    """Health alert data structure"""

    level: HealthStatus
    component: str
    message: str
    timestamp: datetime
    metrics: dict[str, Any]
    suggested_actions: list[str]


class RedisHealthMonitor:
    """Comprehensive Redis health monitoring with business cycle awareness"""

    def __init__(self, redis_manager: Optional[RedisManager] = None):
        self.redis_manager = redis_manager or redis_manager
        self.alerts: list[HealthAlert] = []
        self.alert_callbacks: list[Callable] = []
        self.monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # Health thresholds
        self.thresholds = {
            "memory_warning": 0.8,
            "memory_critical": 0.9,
            "memory_emergency": 0.95,
            "connection_pool_warning": 0.7,
            "connection_pool_critical": 0.85,
            "slow_query_threshold": 1.0,
            "high_error_rate": 0.05,  # 5% error rate
            "response_time_warning": 0.5,
            "response_time_critical": 1.0,
        }

        # Pay Ready specific monitoring
        self.pay_ready_config = PAY_READY_REDIS_CONFIG
        self.spike_detection_window = timedelta(
            seconds=self.pay_ready_config["spike_detection_window"]
        )
        self.historical_metrics: list[dict[str, Any]] = []

    async def start_monitoring(self, interval: float = 30.0):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return

        self.monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info(f"Started Redis health monitoring with {interval}s interval")

    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task
        logger.info("Stopped Redis health monitoring")

    async def _monitoring_loop(self, interval: float):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                await self.comprehensive_health_check()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(interval)

    async def comprehensive_health_check(self) -> dict[str, Any]:
        """Perform comprehensive health assessment"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": HealthStatus.HEALTHY,
            "components": {},
            "alerts": [],
            "metrics": {},
            "pay_ready_status": {},
        }

        try:
            # Basic connectivity and metrics
            basic_health = await self.redis_manager.health_check()
            health_data["components"]["connectivity"] = basic_health

            if not basic_health["healthy"]:
                health_data["overall_status"] = HealthStatus.DOWN
                await self._create_alert(
                    HealthStatus.DOWN,
                    "connectivity",
                    "Redis connection failed",
                    basic_health,
                    [
                        "Check Redis server status",
                        "Verify network connectivity",
                        "Review connection pool settings",
                    ],
                )

            # Memory monitoring
            memory_health = await self._check_memory_health()
            health_data["components"]["memory"] = memory_health
            health_data["metrics"].update(memory_health["metrics"])

            # Connection pool monitoring
            pool_health = await self._check_connection_pool_health()
            health_data["components"]["connection_pool"] = pool_health

            # Performance monitoring
            perf_health = await self._check_performance_health()
            health_data["components"]["performance"] = perf_health

            # Pay Ready business cycle monitoring
            pay_ready_health = await self._check_pay_ready_health()
            health_data["pay_ready_status"] = pay_ready_health

            # Stream health monitoring
            streams_health = await self._check_streams_health()
            health_data["components"]["streams"] = streams_health

            # Determine overall status
            component_statuses = [
                comp.get("status", HealthStatus.HEALTHY)
                for comp in health_data["components"].values()
            ]

            if HealthStatus.DOWN in component_statuses:
                health_data["overall_status"] = HealthStatus.DOWN
            elif HealthStatus.CRITICAL in component_statuses:
                health_data["overall_status"] = HealthStatus.CRITICAL
            elif HealthStatus.WARNING in component_statuses:
                health_data["overall_status"] = HealthStatus.WARNING

            # Store metrics for trend analysis
            self._store_historical_metrics(health_data["metrics"])

            # Add recent alerts
            health_data["alerts"] = [
                {
                    "level": alert.level,
                    "component": alert.component,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "suggested_actions": alert.suggested_actions,
                }
                for alert in self.alerts[-10:]  # Last 10 alerts
            ]

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_data["overall_status"] = HealthStatus.CRITICAL
            health_data["error"] = str(e)

        return health_data

    async def _check_memory_health(self) -> dict[str, Any]:
        """Check Redis memory usage and health"""
        try:
            memory_stats = await self.redis_manager.get_memory_stats()

            # Calculate memory usage percentage
            used_memory = memory_stats["used_memory"]
            max_memory = memory_stats["maxmemory"]

            usage_percent = used_memory / max_memory if max_memory > 0 else 0

            status = HealthStatus.HEALTHY
            alerts = []

            if usage_percent >= self.thresholds["memory_emergency"]:
                status = HealthStatus.DOWN
                alerts.append("Memory usage critical - immediate action required")
                await self._create_alert(
                    HealthStatus.DOWN,
                    "memory",
                    f"Redis memory usage critical: {usage_percent:.2%}",
                    memory_stats,
                    [
                        "Increase Redis max memory",
                        "Clear expired keys",
                        "Review TTL policies",
                        "Scale Redis instance",
                    ],
                )
            elif usage_percent >= self.thresholds["memory_critical"]:
                status = HealthStatus.CRITICAL
                alerts.append("Memory usage critical")
                await self._create_alert(
                    HealthStatus.CRITICAL,
                    "memory",
                    f"Redis memory usage critical: {usage_percent:.2%}",
                    memory_stats,
                    [
                        "Monitor closely",
                        "Prepare for memory scaling",
                        "Review cache eviction policies",
                    ],
                )
            elif usage_percent >= self.thresholds["memory_warning"]:
                status = HealthStatus.WARNING
                alerts.append("Memory usage high")
                await self._create_alert(
                    HealthStatus.WARNING,
                    "memory",
                    f"Redis memory usage high: {usage_percent:.2%}",
                    memory_stats,
                    [
                        "Monitor memory trends",
                        "Review TTL configurations",
                        "Consider cache cleanup",
                    ],
                )

            return {
                "status": status,
                "usage_percent": usage_percent,
                "alerts": alerts,
                "metrics": {
                    "memory_usage_percent": usage_percent,
                    "used_memory_mb": used_memory / (1024 * 1024),
                    "max_memory_mb": (
                        max_memory / (1024 * 1024) if max_memory > 0 else None
                    ),
                    "memory_fragmentation_ratio": memory_stats.get(
                        "memory_fragmentation_ratio", 1.0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return {"status": HealthStatus.DOWN, "error": str(e), "metrics": {}}

    async def _check_connection_pool_health(self) -> dict[str, Any]:
        """Monitor Redis connection pool health"""
        try:
            # Get connection pool statistics
            async with self.redis_manager.get_connection() as redis:
                pool = redis.connection_pool

                created_connections = pool.created_connections
                available_connections = pool.available_connections
                in_use_connections = pool.in_use_connections
                max_connections = self.redis_manager.config.pool.max_connections

                pool_usage = (
                    in_use_connections / max_connections if max_connections > 0 else 0
                )

                status = HealthStatus.HEALTHY
                alerts = []

                if pool_usage >= self.thresholds["connection_pool_critical"]:
                    status = HealthStatus.CRITICAL
                    alerts.append("Connection pool usage critical")
                    await self._create_alert(
                        HealthStatus.CRITICAL,
                        "connection_pool",
                        f"Connection pool usage critical: {pool_usage:.2%}",
                        {
                            "pool_usage": pool_usage,
                            "in_use": in_use_connections,
                            "max_connections": max_connections,
                        },
                        [
                            "Increase max connections",
                            "Review connection leaks",
                            "Scale Redis infrastructure",
                        ],
                    )
                elif pool_usage >= self.thresholds["connection_pool_warning"]:
                    status = HealthStatus.WARNING
                    alerts.append("Connection pool usage high")

                return {
                    "status": status,
                    "pool_usage_percent": pool_usage,
                    "alerts": alerts,
                    "metrics": {
                        "pool_usage_percent": pool_usage,
                        "created_connections": created_connections,
                        "available_connections": available_connections,
                        "in_use_connections": in_use_connections,
                        "max_connections": max_connections,
                    },
                }

        except Exception as e:
            logger.error(f"Connection pool health check failed: {e}")
            return {"status": HealthStatus.DOWN, "error": str(e), "metrics": {}}

    async def _check_performance_health(self) -> dict[str, Any]:
        """Monitor Redis performance metrics"""
        try:
            metrics = await self.redis_manager.get_metrics()

            avg_response_time = metrics.get("avg_response_time", 0)
            slow_operations = metrics.get("slow_operations", 0)
            total_operations = metrics.get("total_operations", 1)
            failed_operations = metrics.get("failed_operations", 0)

            error_rate = (
                failed_operations / total_operations if total_operations > 0 else 0
            )

            status = HealthStatus.HEALTHY
            alerts = []

            # Check response time
            if avg_response_time >= self.thresholds["response_time_critical"]:
                status = HealthStatus.CRITICAL
                alerts.append(f"Response time critical: {avg_response_time:.3f}s")
            elif avg_response_time >= self.thresholds["response_time_warning"]:
                status = HealthStatus.WARNING
                alerts.append(f"Response time high: {avg_response_time:.3f}s")

            # Check error rate
            if error_rate >= self.thresholds["high_error_rate"]:
                status = max(status, HealthStatus.CRITICAL)
                alerts.append(f"High error rate: {error_rate:.2%}")
                await self._create_alert(
                    HealthStatus.CRITICAL,
                    "performance",
                    f"High Redis error rate: {error_rate:.2%}",
                    {"error_rate": error_rate, "failed_operations": failed_operations},
                    [
                        "Check Redis logs",
                        "Review network connectivity",
                        "Monitor resource usage",
                    ],
                )

            return {
                "status": status,
                "alerts": alerts,
                "metrics": {
                    "avg_response_time": avg_response_time,
                    "error_rate": error_rate,
                    "slow_operations": slow_operations,
                    "total_operations": total_operations,
                    "failed_operations": failed_operations,
                },
            }

        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return {"status": HealthStatus.DOWN, "error": str(e), "metrics": {}}

    async def _check_pay_ready_health(self) -> dict[str, Any]:
        """Monitor Pay Ready business cycle specific health"""
        try:
            now = datetime.utcnow()
            is_month_end = now.day >= 28 or now.day <= 2

            # Check for traffic spikes
            spike_detected = await self._detect_traffic_spike()

            # Get Pay Ready specific metrics
            async with self.redis_manager.get_connection() as redis:
                pay_ready_keys = []
                async for key in redis.scan_iter(match="pay_ready:*", count=100):
                    pay_ready_keys.append(key)

                pay_ready_memory = sum(
                    [await redis.memory_usage(key) or 0 for key in pay_ready_keys[:100]]
                )

            recommendations = []
            status = HealthStatus.HEALTHY

            if is_month_end and spike_detected:
                status = HealthStatus.WARNING
                recommendations.extend(
                    [
                        "Monitor cache hit ratios closely",
                        "Consider increasing Redis memory limits",
                        "Enable month-end optimizations",
                    ]
                )

            elif spike_detected:
                status = HealthStatus.WARNING
                recommendations.append("Traffic spike detected - monitor performance")

            return {
                "status": status,
                "is_month_end_period": is_month_end,
                "spike_detected": spike_detected,
                "pay_ready_keys_count": len(pay_ready_keys),
                "pay_ready_memory_usage": pay_ready_memory,
                "recommendations": recommendations,
                "metrics": {
                    "pay_ready_keys_count": len(pay_ready_keys),
                    "pay_ready_memory_mb": pay_ready_memory / (1024 * 1024),
                    "is_month_end_period": is_month_end,
                    "spike_detected": spike_detected,
                },
            }

        except Exception as e:
            logger.error(f"Pay Ready health check failed: {e}")
            return {"status": HealthStatus.DOWN, "error": str(e), "metrics": {}}

    async def _check_streams_health(self) -> dict[str, Any]:
        """Monitor Redis streams health and bounds"""
        try:
            stream_info = {}
            overall_status = HealthStatus.HEALTHY
            alerts = []

            # Common stream patterns to monitor
            stream_patterns = ["swarm:*", "pay_ready:*", "sophia:*", "artemis:*"]

            async with self.redis_manager.get_connection() as redis:
                for pattern in stream_patterns:
                    async for stream_key in redis.scan_iter(match=pattern, count=50):
                        try:
                            stream_key_str = (
                                stream_key.decode()
                                if isinstance(stream_key, bytes)
                                else stream_key
                            )
                            info = await redis.xinfo_stream(stream_key)

                            length = info.get("length", 0)
                            max_len = self.redis_manager.config.streams.max_len

                            # Check if stream is approaching bounds
                            usage_percent = length / max_len if max_len > 0 else 0

                            stream_info[stream_key_str] = {
                                "length": length,
                                "max_length": max_len,
                                "usage_percent": usage_percent,
                                "last_generated_id": info.get(
                                    "last-generated-id", "0-0"
                                ),
                                "groups": info.get("groups", 0),
                            }

                            if usage_percent >= 0.9:
                                overall_status = max(
                                    overall_status, HealthStatus.WARNING
                                )
                                alerts.append(
                                    f"Stream {stream_key_str} near capacity: {usage_percent:.1%}"
                                )

                        except Exception as e:
                            logger.warning(
                                f"Could not get info for stream {stream_key}: {e}"
                            )

            return {
                "status": overall_status,
                "alerts": alerts,
                "streams": stream_info,
                "metrics": {
                    "total_streams": len(stream_info),
                    "streams_near_capacity": len(
                        [s for s in stream_info.values() if s["usage_percent"] >= 0.8]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Streams health check failed: {e}")
            return {"status": HealthStatus.DOWN, "error": str(e), "metrics": {}}

    async def _detect_traffic_spike(self) -> bool:
        """Detect traffic spikes using recent metrics"""
        if len(self.historical_metrics) < 5:
            return False

        try:
            # Get recent metrics
            recent_metrics = self.historical_metrics[-5:]
            current_ops = recent_metrics[-1].get("total_operations", 0)

            # Calculate average of previous metrics
            prev_ops = [m.get("total_operations", 0) for m in recent_metrics[:-1]]
            avg_ops = sum(prev_ops) / len(prev_ops) if prev_ops else 0

            # Detect spike (operations > 150% of average)
            return bool(avg_ops > 0 and current_ops > avg_ops * 1.5)

        except Exception as e:
            logger.warning(f"Traffic spike detection failed: {e}")
            return False

    def _store_historical_metrics(self, metrics: dict[str, Any]):
        """Store metrics for trend analysis"""
        metrics["timestamp"] = datetime.utcnow().isoformat()
        self.historical_metrics.append(metrics)

        # Keep only recent metrics (last 100 entries)
        if len(self.historical_metrics) > 100:
            self.historical_metrics = self.historical_metrics[-100:]

    async def _create_alert(
        self,
        level: HealthStatus,
        component: str,
        message: str,
        metrics: dict[str, Any],
        suggested_actions: list[str],
    ):
        """Create and store health alert"""
        alert = HealthAlert(
            level=level,
            component=component,
            message=message,
            timestamp=datetime.utcnow(),
            metrics=metrics,
            suggested_actions=suggested_actions,
        )

        self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]

        # Log alert
        logger.log(
            (
                logging.ERROR
                if level == HealthStatus.DOWN
                else (
                    logging.WARNING
                    if level in [HealthStatus.CRITICAL, HealthStatus.WARNING]
                    else logging.INFO
                )
            ),
            f"Redis Health Alert [{level}] {component}: {message}",
        )

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def add_alert_callback(self, callback: Callable):
        """Add callback for health alerts"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable):
        """Remove alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    async def get_health_summary(self) -> dict[str, Any]:
        """Get concise health summary"""
        health_data = await self.comprehensive_health_check()

        return {
            "status": health_data["overall_status"],
            "timestamp": health_data["timestamp"],
            "critical_alerts": [
                alert
                for alert in health_data["alerts"]
                if alert["level"] in [HealthStatus.CRITICAL, HealthStatus.DOWN]
            ],
            "key_metrics": {
                "memory_usage": health_data["metrics"].get("memory_usage_percent", 0),
                "pool_usage": health_data["metrics"].get("pool_usage_percent", 0),
                "avg_response_time": health_data["metrics"].get("avg_response_time", 0),
                "error_rate": health_data["metrics"].get("error_rate", 0),
            },
            "recommendations": health_data["pay_ready_status"].get(
                "recommendations", []
            ),
        }


# Global health monitor instance
redis_health_monitor = RedisHealthMonitor()


# Convenience function for quick health checks
async def check_redis_health() -> dict[str, Any]:
    """Quick Redis health check"""
    return await redis_health_monitor.get_health_summary()
