"""
Shared Services Registry - Central registry for shared infrastructure services
Provides common tools and services that both Artemis and Sophia can use
Maintains domain isolation while sharing infrastructure
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from app.memory.unified_memory_router import MemoryDomain

logger = logging.getLogger(__name__)

# ==============================================================================
# SERVICE TYPES AND ENUMS
# ==============================================================================


class ServiceType(str, Enum):
    """Types of shared services"""

    MEMORY = "memory"
    MONITORING = "monitoring"
    LOGGING = "logging"
    TRACING = "tracing"
    CACHING = "caching"
    QUEUE = "queue"
    SCHEDULER = "scheduler"
    CONFIG = "configuration"
    METRICS = "metrics"
    ALERTS = "alerts"
    NOTIFICATIONS = "notifications"
    STORAGE = "storage"


class ServiceStatus(str, Enum):
    """Service health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class ServicePriority(str, Enum):
    """Service priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass
class ServiceConfig:
    """Configuration for a shared service"""

    name: str
    type: ServiceType
    enabled: bool = True
    priority: ServicePriority = ServicePriority.NORMAL
    max_connections: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """Health status of a service"""

    service_name: str
    status: ServiceStatus
    last_check: str
    uptime_seconds: float
    error_count: int = 0
    response_time_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceMetrics:
    """Metrics for a service"""

    service_name: str
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput: float = 0.0
    last_reset: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ==============================================================================
# BASE SERVICE INTERFACE
# ==============================================================================


class BaseService:
    """Base class for all shared services"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.status = ServiceStatus.INITIALIZING
        self.start_time = datetime.now(timezone.utc)
        self.metrics = ServiceMetrics(service_name=config.name)
        self._connections: set[str] = set()

    async def initialize(self) -> bool:
        """Initialize the service"""
        try:
            logger.info(f"Initializing service: {self.config.name}")
            # Service-specific initialization
            await self._initialize_impl()
            self.status = ServiceStatus.HEALTHY
            return True
        except Exception as e:
            logger.error(f"Failed to initialize service {self.config.name}: {e}")
            self.status = ServiceStatus.UNHEALTHY
            return False

    async def _initialize_impl(self):
        """Service-specific initialization (override in subclasses)"""
        pass

    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        start_time = datetime.now(timezone.utc)

        try:
            # Service-specific health check
            is_healthy = await self._health_check_impl()

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

            return ServiceHealth(
                service_name=self.config.name,
                status=ServiceStatus.HEALTHY if is_healthy else ServiceStatus.DEGRADED,
                last_check=datetime.now(timezone.utc).isoformat(),
                uptime_seconds=uptime,
                error_count=self.metrics.error_count,
                response_time_ms=response_time,
                details={
                    "connections": len(self._connections),
                    "max_connections": self.config.max_connections,
                },
            )
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return ServiceHealth(
                service_name=self.config.name,
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.now(timezone.utc).isoformat(),
                uptime_seconds=0,
                error_count=self.metrics.error_count + 1,
                details={"error": str(e)},
            )

    async def _health_check_impl(self) -> bool:
        """Service-specific health check (override in subclasses)"""
        return True

    def get_metrics(self) -> ServiceMetrics:
        """Get service metrics"""
        return self.metrics

    async def shutdown(self):
        """Shutdown the service"""
        logger.info(f"Shutting down service: {self.config.name}")
        self.status = ServiceStatus.OFFLINE
        await self._shutdown_impl()

    async def _shutdown_impl(self):
        """Service-specific shutdown (override in subclasses)"""
        pass


# ==============================================================================
# MEMORY SERVICE
# ==============================================================================


class UnifiedMemoryService(BaseService):
    """Unified memory service for both domains"""

    def __init__(self):
        config = ServiceConfig(
            name="UnifiedMemoryService",
            type=ServiceType.MEMORY,
            priority=ServicePriority.CRITICAL,
            max_connections=1000,
        )
        super().__init__(config)
        self.domain_isolation = True
        self._memory_stores: dict[MemoryDomain, dict] = {
            MemoryDomain.ARTEMIS: {},
            MemoryDomain.SOPHIA: {},
        }

    async def store(
        self,
        domain: MemoryDomain,
        key: str,
        value: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Store data in domain-specific memory"""
        try:
            if domain not in self._memory_stores:
                raise ValueError(f"Invalid domain: {domain}")

            self._memory_stores[domain][key] = {
                "value": value,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self.metrics.request_count += 1
            return True
        except Exception as e:
            logger.error(f"Memory store failed: {e}")
            self.metrics.error_count += 1
            return False

    async def retrieve(self, domain: MemoryDomain, key: str) -> Optional[Any]:
        """Retrieve data from domain-specific memory"""
        try:
            if domain not in self._memory_stores:
                raise ValueError(f"Invalid domain: {domain}")

            data = self._memory_stores[domain].get(key)
            self.metrics.request_count += 1

            return data.get("value") if data else None
        except Exception as e:
            logger.error(f"Memory retrieve failed: {e}")
            self.metrics.error_count += 1
            return None

    async def _health_check_impl(self) -> bool:
        """Check memory service health"""
        # Simple check: can we access both memory stores
        return (
            MemoryDomain.ARTEMIS in self._memory_stores
            and MemoryDomain.SOPHIA in self._memory_stores
        )


# ==============================================================================
# MONITORING SERVICE
# ==============================================================================


class MonitoringService(BaseService):
    """Prometheus-based monitoring service"""

    def __init__(self):
        config = ServiceConfig(
            name="PrometheusMonitoring",
            type=ServiceType.MONITORING,
            priority=ServicePriority.HIGH,
        )
        super().__init__(config)
        self._metrics_registry: dict[str, list[float]] = {}
        self._alerts: list[dict[str, Any]] = []

    async def record_metric(
        self, metric_name: str, value: float, labels: Optional[dict[str, str]] = None
    ):
        """Record a metric"""
        try:
            if metric_name not in self._metrics_registry:
                self._metrics_registry[metric_name] = []

            self._metrics_registry[metric_name].append(value)

            # Keep only last 1000 values per metric
            if len(self._metrics_registry[metric_name]) > 1000:
                self._metrics_registry[metric_name] = self._metrics_registry[
                    metric_name
                ][-1000:]

            self.metrics.request_count += 1
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            self.metrics.error_count += 1

    async def get_metric(
        self, metric_name: str, aggregation: str = "avg"
    ) -> Optional[float]:
        """Get aggregated metric value"""
        try:
            if metric_name not in self._metrics_registry:
                return None

            values = self._metrics_registry[metric_name]
            if not values:
                return None

            if aggregation == "avg":
                return sum(values) / len(values)
            elif aggregation == "sum":
                return sum(values)
            elif aggregation == "max":
                return max(values)
            elif aggregation == "min":
                return min(values)
            elif aggregation == "count":
                return len(values)

            return None
        except Exception as e:
            logger.error(f"Failed to get metric: {e}")
            return None

    async def create_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Create an alert"""
        alert = {
            "id": f"alert_{uuid4().hex[:8]}",
            "name": alert_name,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._alerts.append(alert)
        logger.warning(f"Alert created: {alert_name} - {message}")


# ==============================================================================
# LOGGING SERVICE
# ==============================================================================


class StructuredLoggingService(BaseService):
    """Structured logging service"""

    def __init__(self):
        config = ServiceConfig(
            name="StructuredLogging",
            type=ServiceType.LOGGING,
            priority=ServicePriority.HIGH,
        )
        super().__init__(config)
        self._log_buffer: list[dict[str, Any]] = []
        self._max_buffer_size = 10000

    async def log(
        self,
        level: str,
        message: str,
        domain: Optional[MemoryDomain] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Log a structured message"""
        try:
            log_entry = {
                "id": f"log_{uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": message,
                "domain": domain.value if domain else None,
                "metadata": metadata or {},
            }

            self._log_buffer.append(log_entry)

            # Rotate buffer if too large
            if len(self._log_buffer) > self._max_buffer_size:
                self._log_buffer = self._log_buffer[-self._max_buffer_size :]

            self.metrics.request_count += 1

            # Also log to standard logger
            log_func = getattr(logger, level.lower(), logger.info)
            log_func(f"[{domain.value if domain else 'SYSTEM'}] {message}")

        except Exception as e:
            logger.error(f"Logging failed: {e}")
            self.metrics.error_count += 1

    async def query_logs(
        self,
        domain: Optional[MemoryDomain] = None,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query logs with filters"""
        logs = self._log_buffer

        if domain:
            logs = [log for log in logs if log.get("domain") == domain.value]

        if level:
            logs = [log for log in logs if log.get("level") == level]

        # Return most recent logs
        return logs[-limit:]


# ==============================================================================
# TRACING SERVICE
# ==============================================================================


class TracingService(BaseService):
    """OpenTelemetry-based distributed tracing"""

    def __init__(self):
        config = ServiceConfig(
            name="OpenTelemetryTracing",
            type=ServiceType.TRACING,
            priority=ServicePriority.NORMAL,
        )
        super().__init__(config)
        self._active_spans: dict[str, dict[str, Any]] = {}
        self._completed_spans: list[dict[str, Any]] = []

    async def start_span(
        self,
        name: str,
        domain: MemoryDomain,
        parent_span_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> str:
        """Start a new trace span"""
        span_id = f"span_{uuid4().hex[:8]}"

        span = {
            "id": span_id,
            "name": name,
            "domain": domain.value,
            "parent_id": parent_span_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
            "events": [],
        }

        self._active_spans[span_id] = span
        self.metrics.request_count += 1

        return span_id

    async def end_span(
        self,
        span_id: str,
        status: str = "ok",
        attributes: Optional[dict[str, Any]] = None,
    ):
        """End a trace span"""
        if span_id not in self._active_spans:
            logger.warning(f"Span {span_id} not found")
            return

        span = self._active_spans.pop(span_id)
        span["end_time"] = datetime.now(timezone.utc).isoformat()
        span["status"] = status

        if attributes:
            span["attributes"].update(attributes)

        # Calculate duration
        start = datetime.fromisoformat(span["start_time"])
        end = datetime.fromisoformat(span["end_time"])
        span["duration_ms"] = (end - start).total_seconds() * 1000

        self._completed_spans.append(span)

        # Keep only last 1000 spans
        if len(self._completed_spans) > 1000:
            self._completed_spans = self._completed_spans[-1000:]

    async def add_span_event(
        self, span_id: str, event_name: str, attributes: Optional[dict[str, Any]] = None
    ):
        """Add an event to a span"""
        if span_id not in self._active_spans:
            logger.warning(f"Span {span_id} not found")
            return

        event = {
            "name": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        }

        self._active_spans[span_id]["events"].append(event)


# ==============================================================================
# CACHE SERVICE
# ==============================================================================


class CacheService(BaseService):
    """Redis-like caching service"""

    def __init__(self):
        config = ServiceConfig(
            name="RedisCache", type=ServiceType.CACHING, priority=ServicePriority.NORMAL
        )
        super().__init__(config)
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl_tasks: dict[str, asyncio.Task] = {}

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        domain: Optional[MemoryDomain] = None,
    ) -> bool:
        """Set a cache value with optional TTL"""
        try:
            cache_key = f"{domain.value}:{key}" if domain else key

            self._cache[cache_key] = {
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl_seconds,
            }

            # Cancel existing TTL task if any
            if cache_key in self._ttl_tasks:
                self._ttl_tasks[cache_key].cancel()
                del self._ttl_tasks[cache_key]

            # Set up TTL if specified
            if ttl_seconds:
                self._ttl_tasks[cache_key] = asyncio.create_task(
                    self._expire_key(cache_key, ttl_seconds)
                )

            self.metrics.request_count += 1
            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            self.metrics.error_count += 1
            return False

    async def get(
        self, key: str, domain: Optional[MemoryDomain] = None
    ) -> Optional[Any]:
        """Get a cache value"""
        try:
            cache_key = f"{domain.value}:{key}" if domain else key

            if cache_key in self._cache:
                self.metrics.request_count += 1
                return self._cache[cache_key]["value"]

            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self.metrics.error_count += 1
            return None

    async def delete(self, key: str, domain: Optional[MemoryDomain] = None) -> bool:
        """Delete a cache value"""
        try:
            cache_key = f"{domain.value}:{key}" if domain else key

            if cache_key in self._cache:
                del self._cache[cache_key]

                # Cancel TTL task if exists
                if cache_key in self._ttl_tasks:
                    self._ttl_tasks[cache_key].cancel()
                    del self._ttl_tasks[cache_key]

                return True

            return False

        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False

    async def _expire_key(self, key: str, ttl_seconds: int):
        """Expire a key after TTL"""
        await asyncio.sleep(ttl_seconds)
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl_tasks:
            del self._ttl_tasks[key]


# ==============================================================================
# SHARED SERVICES REGISTRY
# ==============================================================================


class SharedServiceRegistry:
    """Central registry for all shared services"""

    def __init__(self):
        self.services: dict[str, BaseService] = {}
        self._initialized = False
        self._health_check_tasks: dict[str, asyncio.Task] = {}

        logger.info("🔧 Shared Service Registry initialized")

    async def initialize(self):
        """Initialize all services"""
        if self._initialized:
            logger.warning("Services already initialized")
            return

        # Create service instances
        self.services["memory"] = UnifiedMemoryService()
        self.services["monitoring"] = MonitoringService()
        self.services["logging"] = StructuredLoggingService()
        self.services["tracing"] = TracingService()
        self.services["caching"] = CacheService()

        # Initialize all services
        for name, service in self.services.items():
            success = await service.initialize()
            if success:
                logger.info(f"✅ Service {name} initialized successfully")
                # Start health check task
                self._health_check_tasks[name] = asyncio.create_task(
                    self._periodic_health_check(service)
                )
            else:
                logger.error(f"❌ Service {name} initialization failed")

        self._initialized = True
        logger.info("🚀 All shared services initialized")

    async def _periodic_health_check(self, service: BaseService):
        """Run periodic health checks for a service"""
        while True:
            try:
                await asyncio.sleep(service.config.health_check_interval)
                health = await service.health_check()

                if health.status == ServiceStatus.UNHEALTHY:
                    logger.error(f"Service {service.config.name} is unhealthy")
                    # Could trigger alerts or recovery actions here

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {service.config.name}: {e}")

    def get_service(self, service_type: str) -> Optional[BaseService]:
        """Get a service by type"""
        return self.services.get(service_type)

    def get_memory_service(self) -> Optional[UnifiedMemoryService]:
        """Get memory service"""
        return self.services.get("memory")

    def get_monitoring_service(self) -> Optional[MonitoringService]:
        """Get monitoring service"""
        return self.services.get("monitoring")

    def get_logging_service(self) -> Optional[StructuredLoggingService]:
        """Get logging service"""
        return self.services.get("logging")

    def get_tracing_service(self) -> Optional[TracingService]:
        """Get tracing service"""
        return self.services.get("tracing")

    def get_cache_service(self) -> Optional[CacheService]:
        """Get cache service"""
        return self.services.get("caching")

    async def get_all_health_statuses(self) -> dict[str, ServiceHealth]:
        """Get health status of all services"""
        health_statuses = {}

        for name, service in self.services.items():
            health_statuses[name] = await service.health_check()

        return health_statuses

    def get_all_metrics(self) -> dict[str, ServiceMetrics]:
        """Get metrics for all services"""
        metrics = {}

        for name, service in self.services.items():
            metrics[name] = service.get_metrics()

        return metrics

    async def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down all shared services...")

        # Cancel health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()

        # Shutdown all services
        for name, service in self.services.items():
            await service.shutdown()
            logger.info(f"Service {name} shut down")

        self._initialized = False
        logger.info("All shared services shut down")


# ==============================================================================
# GLOBAL INSTANCE
# ==============================================================================

# Global registry instance
shared_services = SharedServiceRegistry()

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================


async def log_structured(
    level: str,
    message: str,
    domain: Optional[MemoryDomain] = None,
    metadata: Optional[dict[str, Any]] = None,
):
    """Convenience function for structured logging"""
    logging_service = shared_services.get_logging_service()
    if logging_service:
        await logging_service.log(level, message, domain, metadata)
    else:
        logger.warning("Logging service not available")


async def record_metric(
    metric_name: str, value: float, labels: Optional[dict[str, str]] = None
):
    """Convenience function for recording metrics"""
    monitoring_service = shared_services.get_monitoring_service()
    if monitoring_service:
        await monitoring_service.record_metric(metric_name, value, labels)
    else:
        logger.warning("Monitoring service not available")


async def start_trace(
    name: str,
    domain: MemoryDomain,
    parent_span_id: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """Convenience function for starting a trace span"""
    tracing_service = shared_services.get_tracing_service()
    if tracing_service:
        return await tracing_service.start_span(
            name, domain, parent_span_id, attributes
        )
    else:
        logger.warning("Tracing service not available")
        return None


async def end_trace(
    span_id: str, status: str = "ok", attributes: Optional[dict[str, Any]] = None
):
    """Convenience function for ending a trace span"""
    tracing_service = shared_services.get_tracing_service()
    if tracing_service:
        await tracing_service.end_span(span_id, status, attributes)
    else:
        logger.warning("Tracing service not available")


async def cache_set(
    key: str,
    value: Any,
    ttl_seconds: Optional[int] = None,
    domain: Optional[MemoryDomain] = None,
) -> bool:
    """Convenience function for setting cache value"""
    cache_service = shared_services.get_cache_service()
    if cache_service:
        return await cache_service.set(key, value, ttl_seconds, domain)
    else:
        logger.warning("Cache service not available")
        return False


async def cache_get(key: str, domain: Optional[MemoryDomain] = None) -> Optional[Any]:
    """Convenience function for getting cache value"""
    cache_service = shared_services.get_cache_service()
    if cache_service:
        return await cache_service.get(key, domain)
    else:
        logger.warning("Cache service not available")
        return None


# ==============================================================================
# SERVICE HEALTH MONITOR
# ==============================================================================


class ServiceHealthMonitor:
    """Monitors health of all shared services"""

    def __init__(self, registry: SharedServiceRegistry):
        self.registry = registry
        self.unhealthy_services: set[str] = set()
        self.health_history: dict[str, list[ServiceHealth]] = {}
        self.alert_threshold = 3  # Number of consecutive unhealthy checks before alert

    async def check_all_services(self) -> dict[str, ServiceHealth]:
        """Check health of all services"""
        health_statuses = await self.registry.get_all_health_statuses()

        for name, health in health_statuses.items():
            # Track health history
            if name not in self.health_history:
                self.health_history[name] = []

            self.health_history[name].append(health)

            # Keep only last 10 health checks
            if len(self.health_history[name]) > 10:
                self.health_history[name] = self.health_history[name][-10:]

            # Check for unhealthy services
            if health.status in [ServiceStatus.UNHEALTHY, ServiceStatus.OFFLINE]:
                if name not in self.unhealthy_services:
                    self.unhealthy_services.add(name)
                    logger.error(f"Service {name} is unhealthy: {health.status}")

                    # Check if we should alert
                    recent_unhealthy = sum(
                        1
                        for h in self.health_history[name][-self.alert_threshold :]
                        if h.status in [ServiceStatus.UNHEALTHY, ServiceStatus.OFFLINE]
                    )

                    if recent_unhealthy >= self.alert_threshold:
                        await self._send_alert(name, health)
            else:
                if name in self.unhealthy_services:
                    self.unhealthy_services.remove(name)
                    logger.info(f"Service {name} recovered")

        return health_statuses

    async def _send_alert(self, service_name: str, health: ServiceHealth):
        """Send alert for unhealthy service"""
        monitoring_service = self.registry.get_monitoring_service()
        if monitoring_service:
            await monitoring_service.create_alert(
                alert_name=f"service_unhealthy_{service_name}",
                severity="critical",
                message=f"Service {service_name} has been unhealthy for {self.alert_threshold} consecutive checks",
                metadata={
                    "service": service_name,
                    "status": health.status.value,
                    "error_count": health.error_count,
                    "details": health.details,
                },
            )

    def get_service_availability(self, service_name: str) -> float:
        """Calculate service availability percentage"""
        if service_name not in self.health_history:
            return 0.0

        history = self.health_history[service_name]
        if not history:
            return 0.0

        healthy_count = sum(
            1
            for h in history
            if h.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
        )

        return (healthy_count / len(history)) * 100


# ==============================================================================
# INITIALIZATION
# ==============================================================================


async def initialize_shared_services():
    """Initialize all shared services"""
    await shared_services.initialize()
    logger.info("All shared services initialized and ready")


async def shutdown_shared_services():
    """Shutdown all shared services"""
    await shared_services.shutdown()
    logger.info("All shared services shut down")
