"""
Resource Manager for Autonomous Evolution System
Implements cleanup, rollback, and resource management for production deployment
"""

import asyncio
import logging
import signal
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources managed by the system"""

    MEMORY_SESSION = "memory_session"
    AGNO_TEAM = "agno_team"
    API_CONNECTION = "api_connection"
    CIRCUIT_BREAKER = "circuit_breaker"
    BACKGROUND_TASK = "background_task"
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"


@dataclass
class ResourceMetrics:
    """Resource usage metrics"""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_connections: int = 0
    open_files: int = 0
    active_tasks: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ManagedResource:
    """Managed resource with cleanup capabilities"""

    resource_id: str
    resource_type: ResourceType
    resource_object: Any
    cleanup_func: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ResourceManager:
    """
    Comprehensive resource manager for autonomous evolution system
    Handles cleanup, rollback, and resource monitoring
    """

    def __init__(self):
        self.resources: dict[str, ManagedResource] = {}
        self.resource_locks: dict[str, asyncio.Lock] = {}
        self.cleanup_registry: dict[ResourceType, list[Callable]] = {
            resource_type: [] for resource_type in ResourceType
        }
        self.shutdown_handlers: list[Callable] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.metrics_history: list[ResourceMetrics] = []
        self.max_history = 100
        self.cleanup_interval = 300  # 5 minutes
        self.is_shutting_down = False

        # Resource limits
        self.max_memory_usage = 85.0  # percent
        self.max_cpu_usage = 90.0  # percent
        self.max_open_files = 1000
        self.resource_timeout = timedelta(hours=2)  # Auto cleanup after 2 hours

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        try:
            for sig in [signal.SIGTERM, signal.SIGINT]:
                signal.signal(sig, self._signal_handler)
        except ValueError:
            # Signal handling might not work in all environments
            logger.warning(
                "Could not setup signal handlers - graceful shutdown may be limited"
            )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.graceful_shutdown())

    async def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        resource_object: Any,
        cleanup_func: Optional[Callable] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Register a resource for management"""

        async with self._get_lock(resource_id):
            if resource_id in self.resources:
                logger.warning(
                    f"Resource {resource_id} already registered, updating..."
                )
                await self._cleanup_resource(resource_id)

            managed_resource = ManagedResource(
                resource_id=resource_id,
                resource_type=resource_type,
                resource_object=resource_object,
                cleanup_func=cleanup_func,
                metadata=metadata or {},
            )

            self.resources[resource_id] = managed_resource
            logger.debug(f"Registered resource: {resource_id} ({resource_type.value})")

            return resource_id

    async def access_resource(self, resource_id: str) -> Optional[Any]:
        """Access a managed resource and update access metrics"""
        if resource_id not in self.resources:
            logger.warning(f"Resource {resource_id} not found")
            return None

        async with self._get_lock(resource_id):
            resource = self.resources[resource_id]
            resource.last_accessed = datetime.now()
            resource.access_count += 1
            return resource.resource_object

    async def unregister_resource(self, resource_id: str) -> bool:
        """Unregister and cleanup a resource"""
        if resource_id not in self.resources:
            return False

        async with self._get_lock(resource_id):
            success = await self._cleanup_resource(resource_id)
            if success:
                del self.resources[resource_id]
                if resource_id in self.resource_locks:
                    del self.resource_locks[resource_id]
            return success

    async def _cleanup_resource(self, resource_id: str) -> bool:
        """Internal resource cleanup"""
        try:
            resource = self.resources.get(resource_id)
            if not resource:
                return True

            # Execute custom cleanup function
            if resource.cleanup_func:
                if asyncio.iscoroutinefunction(resource.cleanup_func):
                    await resource.cleanup_func(resource.resource_object)
                else:
                    resource.cleanup_func(resource.resource_object)

            # Execute type-specific cleanup
            for cleanup_func in self.cleanup_registry[resource.resource_type]:
                try:
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func(resource.resource_object)
                    else:
                        cleanup_func(resource.resource_object)
                except Exception as e:
                    logger.warning(f"Cleanup function failed for {resource_id}: {e}")

            logger.debug(f"Cleaned up resource: {resource_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup resource {resource_id}: {e}")
            return False

    def register_cleanup_handler(
        self, resource_type: ResourceType, cleanup_func: Callable
    ):
        """Register a cleanup handler for a resource type"""
        self.cleanup_registry[resource_type].append(cleanup_func)

    def register_shutdown_handler(self, handler: Callable):
        """Register a shutdown handler"""
        self.shutdown_handlers.append(handler)

    async def start_monitoring(self):
        """Start resource monitoring task"""
        if self.monitoring_task and not self.monitoring_task.done():
            return

        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")

    async def stop_monitoring(self):
        """Stop resource monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.monitoring_task
        logger.info("Resource monitoring stopped")

    async def _monitoring_loop(self):
        """Resource monitoring loop"""
        try:
            while not self.is_shutting_down:
                await self._collect_metrics()
                await self._cleanup_expired_resources()
                await self._check_resource_limits()
                await asyncio.sleep(self.cleanup_interval)
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")

    async def _collect_metrics(self):
        """Collect system metrics"""
        try:
            process = psutil.Process()

            metrics = ResourceMetrics(
                cpu_usage=process.cpu_percent(),
                memory_usage=process.memory_percent(),
                network_connections=len(process.connections()),
                open_files=len(process.open_files()),
                active_tasks=len([t for t in asyncio.all_tasks() if not t.done()]),
            )

            self.metrics_history.append(metrics)

            # Keep history size manageable
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)

            logger.debug(
                f"Metrics: CPU {metrics.cpu_usage:.1f}%, "
                f"Memory {metrics.memory_usage:.1f}%, "
                f"Tasks {metrics.active_tasks}"
            )

        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")

    async def _cleanup_expired_resources(self):
        """Clean up expired resources"""
        current_time = datetime.now()
        expired_resources = []

        for resource_id, resource in self.resources.items():
            if current_time - resource.last_accessed > self.resource_timeout:
                expired_resources.append(resource_id)

        for resource_id in expired_resources:
            logger.info(f"Cleaning up expired resource: {resource_id}")
            await self.unregister_resource(resource_id)

    async def _check_resource_limits(self):
        """Check if resource usage is within limits"""
        if not self.metrics_history:
            return

        latest_metrics = self.metrics_history[-1]

        warnings = []
        if latest_metrics.memory_usage > self.max_memory_usage:
            warnings.append(f"Memory usage high: {latest_metrics.memory_usage:.1f}%")

        if latest_metrics.cpu_usage > self.max_cpu_usage:
            warnings.append(f"CPU usage high: {latest_metrics.cpu_usage:.1f}%")

        if latest_metrics.open_files > self.max_open_files:
            warnings.append(f"Too many open files: {latest_metrics.open_files}")

        if warnings:
            logger.warning("Resource limits exceeded: " + ", ".join(warnings))
            # Trigger cleanup of least recently used resources
            await self._emergency_cleanup()

    async def _emergency_cleanup(self):
        """Emergency cleanup of least recently used resources"""
        # Sort by last access time and clean up oldest 10%
        sorted_resources = sorted(
            self.resources.items(), key=lambda x: x[1].last_accessed
        )

        cleanup_count = max(1, len(sorted_resources) // 10)

        for resource_id, _ in sorted_resources[:cleanup_count]:
            logger.info(f"Emergency cleanup of resource: {resource_id}")
            await self.unregister_resource(resource_id)

    async def _get_lock(self, resource_id: str) -> asyncio.Lock:
        """Get or create lock for resource"""
        if resource_id not in self.resource_locks:
            self.resource_locks[resource_id] = asyncio.Lock()
        return self.resource_locks[resource_id]

    async def graceful_shutdown(self):
        """Perform graceful shutdown of all resources"""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        logger.info("Starting graceful resource shutdown...")

        # Stop monitoring
        await self.stop_monitoring()

        # Execute shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.warning(f"Shutdown handler failed: {e}")

        # Clean up all resources
        resource_ids = list(self.resources.keys())
        cleanup_tasks = [self.unregister_resource(rid) for rid in resource_ids]

        try:
            await asyncio.wait_for(
                asyncio.gather(*cleanup_tasks, return_exceptions=True), timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning("Resource cleanup timed out")

        logger.info(
            f"Graceful shutdown complete. Cleaned up {len(resource_ids)} resources"
        )

    def get_resource_summary(self) -> dict[str, Any]:
        """Get summary of managed resources"""
        summary = {
            "total_resources": len(self.resources),
            "by_type": {},
            "oldest_resource": None,
            "newest_resource": None,
            "most_accessed": None,
        }

        if not self.resources:
            return summary

        # Count by type
        for resource in self.resources.values():
            type_name = resource.resource_type.value
            summary["by_type"][type_name] = summary["by_type"].get(type_name, 0) + 1

        # Find oldest, newest, most accessed
        sorted_by_created = sorted(self.resources.values(), key=lambda x: x.created_at)
        sorted_by_accessed = sorted(
            self.resources.values(), key=lambda x: x.access_count, reverse=True
        )

        summary["oldest_resource"] = {
            "id": sorted_by_created[0].resource_id,
            "created": sorted_by_created[0].created_at.isoformat(),
            "type": sorted_by_created[0].resource_type.value,
        }

        summary["newest_resource"] = {
            "id": sorted_by_created[-1].resource_id,
            "created": sorted_by_created[-1].created_at.isoformat(),
            "type": sorted_by_created[-1].resource_type.value,
        }

        summary["most_accessed"] = {
            "id": sorted_by_accessed[0].resource_id,
            "access_count": sorted_by_accessed[0].access_count,
            "type": sorted_by_accessed[0].resource_type.value,
        }

        return summary

    @asynccontextmanager
    async def managed_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        resource_object: Any,
        cleanup_func: Optional[Callable] = None,
    ):
        """Context manager for automatic resource management"""
        try:
            await self.register_resource(
                resource_id, resource_type, resource_object, cleanup_func
            )
            yield resource_object
        finally:
            await self.unregister_resource(resource_id)


# Global resource manager instance
resource_manager = ResourceManager()


# Helper functions for common resource patterns
async def cleanup_agno_team(team_object):
    """Standard cleanup for AGNO teams"""
    try:
        if hasattr(team_object, "shutdown"):
            if asyncio.iscoroutinefunction(team_object.shutdown):
                await team_object.shutdown()
            else:
                team_object.shutdown()

        if hasattr(team_object, "agents"):
            for agent in getattr(team_object, "agents", []):
                # Clear agent resources
                if hasattr(agent, "_session"):
                    agent._session = None
    except Exception as e:
        logger.warning(f"AGNO team cleanup warning: {e}")


async def cleanup_memory_session(memory_session):
    """Standard cleanup for memory sessions"""
    try:
        if hasattr(memory_session, "close"):
            if asyncio.iscoroutinefunction(memory_session.close):
                await memory_session.close()
            else:
                memory_session.close()
    except Exception as e:
        logger.warning(f"Memory session cleanup warning: {e}")


async def cleanup_api_connection(connection):
    """Standard cleanup for API connections"""
    try:
        if hasattr(connection, "close"):
            if asyncio.iscoroutinefunction(connection.close):
                await connection.close()
            else:
                connection.close()
    except Exception as e:
        logger.warning(f"API connection cleanup warning: {e}")


# Register standard cleanup handlers
resource_manager.register_cleanup_handler(ResourceType.AGNO_TEAM, cleanup_agno_team)
resource_manager.register_cleanup_handler(
    ResourceType.MEMORY_SESSION, cleanup_memory_session
)
resource_manager.register_cleanup_handler(
    ResourceType.API_CONNECTION, cleanup_api_connection
)
