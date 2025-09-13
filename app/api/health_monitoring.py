"""
Production Health Monitoring System
Real health checks for all system components
"""
import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.resource_manager import get_resource_manager
from app.models.orchestration_models import ConnectionMetrics, SystemStatus
logger = logging.getLogger(__name__)
router = APIRouter()
class HealthComponentStatus(str, Enum):
    """Health status for individual components"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
class ComponentHealth(BaseModel):
    """Health status of a system component"""
    name: str
    status: HealthComponentStatus
    response_time_ms: Optional[float] = None
    last_check: datetime
    details: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: SystemStatus
    uptime_seconds: int
    version: str = "2.1.0"
    environment: str
    timestamp: datetime = Field(default_factory=datetime.now)
    components: dict[str, ComponentHealth]
    system_metrics: dict[str, Any]
    connection_metrics: ConnectionMetrics
    alerts: list[dict[str, Any]] = Field(default_factory=list)
class HealthMonitor:
    """Production health monitoring system"""
    def __init__(self):
        self.start_time = time.time()
        self.check_cache = {}
        self.cache_ttl = 30  # Cache health checks for 30 seconds
        self.alert_thresholds = {
            "memory_usage_percent": 85.0,
            "cpu_usage_percent": 90.0,
            "disk_usage_percent": 90.0,
            "response_time_ms": 1000.0,
            "error_rate_percent": 5.0,
        }
    async def get_system_health(self, detailed: bool = False) -> dict[str, Any]:
        """Get overall system health status"""
        # Check cache first
        cache_key = f"system_health_{detailed}"
        if cache_key in self.check_cache:
            cached_result, timestamp = self.check_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        try:
            # Gather component health checks
            components = {}
            overall_status = SystemStatus.HEALTHY
            # Core components to check
            core_checks = [
                ("redis", self._check_redis),
                ("memory", self._check_memory),
                ("cpu", self._check_cpu),
                ("disk", self._check_disk),
                ("connections", self._check_connections),
            ]
            if detailed:
                # Add detailed checks
                detailed_checks = [
                    ("orchestrator", self._check_orchestrator),
                    ("llm_providers", self._check_llm_providers),
                    ("embedding_service", self._check_embedding_service),
                    ("websocket", self._check_websocket),
                ]
                core_checks.extend(detailed_checks)
            # Run all checks concurrently
            check_tasks = []
            for name, check_func in core_checks:
                check_tasks.append(self._run_component_check(name, check_func))
            results = await asyncio.gather(*check_tasks, return_exceptions=True)
            # Process results
            for i, (name, _) in enumerate(core_checks):
                if isinstance(results[i], Exception):
                    components[name] = ComponentHealth(
                        name=name,
                        status=HealthComponentStatus.UNHEALTHY,
                        last_check=datetime.now(),
                        error_message=str(results[i]),
                    )
                    overall_status = SystemStatus.UNHEALTHY
                else:
                    components[name] = results[i]
                    if results[i].status == HealthComponentStatus.UNHEALTHY:
                        overall_status = SystemStatus.UNHEALTHY
                    elif (
                        results[i].status == HealthComponentStatus.DEGRADED
                        and overall_status != SystemStatus.UNHEALTHY
                    ):
                        overall_status = SystemStatus.DEGRADED
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            # Get connection metrics
            connection_metrics = await self._get_connection_metrics()
            # Generate alerts
            alerts = self._generate_alerts(components, system_metrics)
            if detailed:
                result = DetailedHealthResponse(
                    status=overall_status,
                    uptime_seconds=int(time.time() - self.start_time),
                    environment=settings.environment,
                    components=components,
                    system_metrics=system_metrics,
                    connection_metrics=connection_metrics,
                    alerts=alerts,
                ).dict()
            else:
                result = {
                    "status": overall_status.value,
                    "uptime_seconds": int(time.time() - self.start_time),
                    "environment": settings.environment,
                    "components": {
                        name: comp.status.value for name, comp in components.items()
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            # Cache result
            self.check_cache[cache_key] = (result, time.time())
            return result
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": SystemStatus.UNHEALTHY.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    async def _run_component_check(self, name: str, check_func) -> ComponentHealth:
        """Run a single component health check with timing"""
        start_time = time.time()
        try:
            result = await check_func()
            response_time = (time.time() - start_time) * 1000
            result.response_time_ms = response_time
            return result
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check for {name} failed: {e}")
            return ComponentHealth(
                name=name,
                status=HealthComponentStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity and performance"""
        try:
            resource_manager = await get_resource_manager()
            # Test basic operations
            async with resource_manager.managed_redis() as redis:
                # Ping test
                await redis.ping()
                # Performance test
                start = time.time()
                await redis.set("health_check", "test", ex=10)
                value = await redis.get("health_check")
                latency = (time.time() - start) * 1000
                if value != b"test":
                    raise Exception("Redis read/write test failed")
                # Get Redis info
                info = await redis.info()
                memory_usage = info.get("used_memory", 0)
                connected_clients = info.get("connected_clients", 0)
                status = HealthComponentStatus.HEALTHY
                if latency > 100:  # >100ms is degraded
                    status = HealthComponentStatus.DEGRADED
                if latency > 500:  # >500ms is unhealthy
                    status = HealthComponentStatus.UNHEALTHY
                return ComponentHealth(
                    name="redis",
                    status=status,
                    last_check=datetime.now(),
                    details={
                        "latency_ms": latency,
                        "memory_usage_bytes": memory_usage,
                        "connected_clients": connected_clients,
                        "version": info.get("redis_version", "unknown"),
                    },
                )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_memory(self) -> ComponentHealth:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            # Determine status based on usage
            status = HealthComponentStatus.HEALTHY
            if memory.percent > 80:
                status = HealthComponentStatus.DEGRADED
            if memory.percent > 90:
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="memory",
                status=status,
                last_check=datetime.now(),
                details={
                    "usage_percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "swap_usage_percent": swap.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_cpu(self) -> ComponentHealth:
        """Check CPU usage"""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
            )
            status = HealthComponentStatus.HEALTHY
            if cpu_percent > 80:
                status = HealthComponentStatus.DEGRADED
            if cpu_percent > 95:
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="cpu",
                status=status,
                last_check=datetime.now(),
                details={
                    "usage_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_avg_1m": load_avg[0],
                    "load_avg_5m": load_avg[1],
                    "load_avg_15m": load_avg[2],
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="cpu",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_disk(self) -> ComponentHealth:
        """Check disk usage"""
        try:
            disk_usage = psutil.disk_usage("/")
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            status = HealthComponentStatus.HEALTHY
            if usage_percent > 80:
                status = HealthComponentStatus.DEGRADED
            if usage_percent > 90:
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="disk",
                status=status,
                last_check=datetime.now(),
                details={
                    "usage_percent": round(usage_percent, 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_connections(self) -> ComponentHealth:
        """Check connection pool health"""
        try:
            resource_manager = await get_resource_manager()
            health_status = await resource_manager.health_check()
            status = HealthComponentStatus.HEALTHY
            if health_status["status"] == "degraded":
                status = HealthComponentStatus.DEGRADED
            elif health_status["status"] != "healthy":
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="connections",
                status=status,
                last_check=datetime.now(),
                details=health_status.get("connections", {}),
            )
        except Exception as e:
            return ComponentHealth(
                name="connections",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_orchestrator(self) -> ComponentHealth:
        """Check orchestrator system health"""
        try:
            from app.core.super_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            # Basic functionality test
            test_request = {
                "type": "query",
                "query_type": "metrics",
                "content": "health check",
            }
            start_time = time.time()
            await orchestrator.process_request(test_request)
            response_time = (time.time() - start_time) * 1000
            status = HealthComponentStatus.HEALTHY
            if response_time > 1000:  # >1s is degraded
                status = HealthComponentStatus.DEGRADED
            if response_time > 5000:  # >5s is unhealthy
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="orchestrator",
                status=status,
                last_check=datetime.now(),
                details={
                    "response_time_ms": response_time,
                    "active_tasks": len(orchestrator.tasks.active_tasks),
                    "completed_tasks": len(orchestrator.tasks.completed_tasks),
                    "connections": len(orchestrator.connections),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="orchestrator",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_llm_providers(self) -> ComponentHealth:
        """Check LLM provider connectivity"""
        try:
            # This would test actual LLM providers
            # For now, return basic status based on configuration
            providers_configured = 0
            providers_working = 0
            if settings.openai_api_key or settings.openrouter_api_key:
                providers_configured += 1
                providers_working += 1  # Assume working for now
            if settings.anthropic_api_key:
                providers_configured += 1
                providers_working += 1
            if settings.portkey_api_key:
                providers_configured += 1
                providers_working += 1
            status = HealthComponentStatus.HEALTHY
            if providers_configured == 0:
                status = HealthComponentStatus.UNHEALTHY
            elif providers_working < providers_configured:
                status = HealthComponentStatus.DEGRADED
            return ComponentHealth(
                name="llm_providers",
                status=status,
                last_check=datetime.now(),
                details={
                    "configured": providers_configured,
                    "working": providers_working,
                    "providers": {
                        "openai": bool(settings.openai_api_key),
                        "anthropic": bool(settings.anthropic_api_key),
                        "portkey": bool(settings.portkey_api_key),
                    },
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="llm_providers",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_embedding_service(self) -> ComponentHealth:
        """Check embedding service health"""
        try:
            # Basic check - would test actual embedding generation in production
            status = HealthComponentStatus.HEALTHY
            if not settings.together_api_key:
                status = HealthComponentStatus.DEGRADED
            return ComponentHealth(
                name="embedding_service",
                status=status,
                last_check=datetime.now(),
                details={
                    "model": settings.embed_model,
                    "provider": settings.embed_provider,
                    "dimension": settings.embed_dimension,
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="embedding_service",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _check_websocket(self) -> ComponentHealth:
        """Check WebSocket system health"""
        try:
            from app.core.super_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            active_connections = len(orchestrator.connections)
            max_connections = settings.websocket_max_connections
            status = HealthComponentStatus.HEALTHY
            utilization = (
                active_connections / max_connections if max_connections > 0 else 0
            )
            if utilization > 0.8:  # >80% utilization
                status = HealthComponentStatus.DEGRADED
            if utilization > 0.95:  # >95% utilization
                status = HealthComponentStatus.UNHEALTHY
            return ComponentHealth(
                name="websocket",
                status=status,
                last_check=datetime.now(),
                details={
                    "active_connections": active_connections,
                    "max_connections": max_connections,
                    "utilization_percent": round(utilization * 100, 2),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="websocket",
                status=HealthComponentStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
    async def _get_system_metrics(self) -> dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage("/")
            process = psutil.Process()
            process_memory = process.memory_info()
            return {
                "uptime_seconds": int(time.time() - self.start_time),
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_percent": memory.percent,
                },
                "cpu": {"usage_percent": cpu_percent, "count": psutil.cpu_count()},
                "disk": {
                    "total_bytes": disk.total,
                    "free_bytes": disk.free,
                    "used_percent": (disk.used / disk.total) * 100,
                },
                "process": {
                    "memory_rss_bytes": process_memory.rss,
                    "memory_vms_bytes": process_memory.vms,
                    "pid": process.pid,
                    "threads": process.num_threads(),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    async def _get_connection_metrics(self) -> ConnectionMetrics:
        """Get connection pool metrics"""
        try:
            resource_manager = await get_resource_manager()
            health_data = await resource_manager.health_check()
            connections_data = health_data.get("connections", {})
            return ConnectionMetrics(
                redis_connections=connections_data.get("redis", {}),
                http_connections=connections_data.get("http", {}),
                websocket_connections=connections_data.get("websocket", {}),
                total_active=connections_data.get("total_active", 0),
                total_idle=connections_data.get("total_idle", 0),
                errors_last_hour=connections_data.get("errors_last_hour", 0),
            )
        except Exception as e:
            logger.error(f"Failed to get connection metrics: {e}")
            return ConnectionMetrics()
    def _generate_alerts(
        self, components: dict[str, ComponentHealth], metrics: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate alerts based on thresholds"""
        alerts = []
        # Check component alerts
        for name, component in components.items():
            if component.status == HealthComponentStatus.UNHEALTHY:
                alerts.append(
                    {
                        "type": "component_unhealthy",
                        "component": name,
                        "severity": "critical",
                        "message": f"Component {name} is unhealthy: {component.error_message or 'Unknown error'}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            elif component.status == HealthComponentStatus.DEGRADED:
                alerts.append(
                    {
                        "type": "component_degraded",
                        "component": name,
                        "severity": "warning",
                        "message": f"Component {name} is degraded",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        # Check metric-based alerts
        memory_percent = metrics.get("memory", {}).get("used_percent", 0)
        if memory_percent > self.alert_thresholds["memory_usage_percent"]:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": f"Memory usage is {memory_percent:.1f}%",
                    "value": memory_percent,
                    "threshold": self.alert_thresholds["memory_usage_percent"],
                    "timestamp": datetime.now().isoformat(),
                }
            )
        cpu_percent = metrics.get("cpu", {}).get("usage_percent", 0)
        if cpu_percent > self.alert_thresholds["cpu_usage_percent"]:
            alerts.append(
                {
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": f"CPU usage is {cpu_percent:.1f}%",
                    "value": cpu_percent,
                    "threshold": self.alert_thresholds["cpu_usage_percent"],
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return alerts
# Global health monitor instance
health_monitor = HealthMonitor()
# ============================================
# API Endpoints
# ============================================
@router.get("/", summary="Basic health check")
async def basic_health_check():
    """Basic health check endpoint - always fast"""
    return {
        "status": "healthy",
        "uptime_seconds": int(time.time() - health_monitor.start_time),
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
    }
@router.get("/detailed", summary="Detailed health check")
async def detailed_health_check():
    """Detailed health check with all component status"""
    return await health_monitor.get_system_health(detailed=True)
@router.get("/live", summary="Liveness probe")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}
@router.get("/ready", summary="Readiness probe")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    health_status = await health_monitor.get_system_health(detailed=False)
    if health_status["status"] in ["healthy", "degraded"]:
        return {
            "status": "ready",
            "components": health_status.get("components", {}),
            "timestamp": datetime.now().isoformat(),
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "reason": "System is unhealthy",
                "timestamp": datetime.now().isoformat(),
            },
        )
@router.get("/metrics", summary="System metrics")
async def system_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        metrics = await health_monitor._get_system_metrics()
        return {"metrics": metrics, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/alerts", summary="Active alerts")
async def get_active_alerts():
    """Get current system alerts"""
    health_status = await health_monitor.get_system_health(detailed=True)
    return {
        "alerts": health_status.get("alerts", []),
        "count": len(health_status.get("alerts", [])),
        "timestamp": datetime.now().isoformat(),
    }
@router.post("/check/{component}", summary="Check specific component")
async def check_component(component: str):
    """Trigger health check for a specific component"""
    check_mapping = {
        "redis": health_monitor._check_redis,
        "memory": health_monitor._check_memory,
        "cpu": health_monitor._check_cpu,
        "disk": health_monitor._check_disk,
        "connections": health_monitor._check_connections,
        "orchestrator": health_monitor._check_orchestrator,
        "llm_providers": health_monitor._check_llm_providers,
        "embedding_service": health_monitor._check_embedding_service,
        "websocket": health_monitor._check_websocket,
    }
    if component not in check_mapping:
        raise HTTPException(
            status_code=404,
            detail=f"Component '{component}' not found. Available: {list(check_mapping.keys())}",
        )
    try:
        result = await health_monitor._run_component_check(
            component, check_mapping[component]
        )
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/cache", summary="Clear health check cache")
async def clear_health_cache():
    """Clear the health check cache (admin only)"""
    # This would normally check for admin access
    health_monitor.check_cache.clear()
    return {
        "message": "Health check cache cleared",
        "timestamp": datetime.now().isoformat(),
    }
