"""
Production Resource Management System
Handles proper cleanup of Redis, WebSocket, and HTTP connections
"""

import asyncio
import logging
import signal
import sys
import weakref
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set

from app.core.config import settings
from app.core.connections import get_connection_manager

logger = logging.getLogger(__name__)


class ResourceTracker:
    """Tracks all active resources for proper cleanup"""

    def __init__(self):
        self._resources: Set[weakref.ReferenceType] = set()
        self._cleanup_handlers: List[callable] = []
        self._shutdown_initiated = False

    def register_resource(self, resource: Any) -> None:
        """Register a resource for tracking"""
        if hasattr(resource, "close") or hasattr(resource, "cleanup"):
            weak_ref = weakref.ref(resource, self._on_resource_deleted)
            self._resources.add(weak_ref)

    def register_cleanup_handler(self, handler: callable) -> None:
        """Register a cleanup handler function"""
        self._cleanup_handlers.append(handler)

    def _on_resource_deleted(self, weak_ref: weakref.ReferenceType) -> None:
        """Called when a tracked resource is garbage collected"""
        self._resources.discard(weak_ref)

    async def cleanup_all(self) -> None:
        """Cleanup all tracked resources"""
        if self._shutdown_initiated:
            return

        self._shutdown_initiated = True
        logger.info("Starting resource cleanup...")

        # Run cleanup handlers first
        for handler in self._cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Cleanup handler failed: {e}")

        # Cleanup tracked resources
        active_resources = [ref() for ref in self._resources if ref() is not None]

        for resource in active_resources:
            try:
                if hasattr(resource, "close"):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                elif hasattr(resource, "cleanup"):
                    if asyncio.iscoroutinefunction(resource.cleanup):
                        await resource.cleanup()
                    else:
                        resource.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup resource {type(resource)}: {e}")

        logger.info(f"Cleaned up {len(active_resources)} resources")


class ProductionResourceManager:
    """Production-ready resource manager with proper lifecycle management"""

    def __init__(self):
        self.tracker = ResourceTracker()
        self._connection_manager = None
        self._signal_handlers_registered = False

    async def initialize(self) -> None:
        """Initialize all resources"""
        logger.info("Initializing production resource manager...")

        # Initialize connection manager
        self._connection_manager = await get_connection_manager()
        self.tracker.register_resource(self._connection_manager)

        # Register signal handlers for graceful shutdown
        if not self._signal_handlers_registered:
            self._register_signal_handlers()

        logger.info("Production resource manager initialized")

    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self._signal_handlers_registered = True

    async def get_redis_client(self):
        """Get Redis client with tracking"""
        if not self._connection_manager:
            await self.initialize()
        return await self._connection_manager.get_redis()

    async def get_http_session(self):
        """Get HTTP session with tracking"""
        if not self._connection_manager:
            await self.initialize()
        return await self._connection_manager.get_http_session()

    @asynccontextmanager
    async def managed_redis(self):
        """Context manager for Redis operations"""
        try:
            redis_client = await self.get_redis_client()
            yield redis_client
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise
        # Connection cleanup is handled by connection manager

    @asynccontextmanager
    async def managed_http_session(self):
        """Context manager for HTTP operations"""
        try:
            session = await self.get_http_session()
            yield session
        except Exception as e:
            logger.error(f"HTTP operation failed: {e}")
            raise
        # Connection cleanup is handled by connection manager

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {"status": "healthy", "resources": {}, "connections": {}}

        try:
            # Check Redis
            async with self.managed_redis() as redis:
                await redis.ping()
                health_status["resources"]["redis"] = "healthy"
        except Exception as e:
            health_status["resources"]["redis"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"

        try:
            # Check connection manager metrics
            if self._connection_manager:
                metrics = self._connection_manager.get_metrics()
                health_status["connections"] = metrics
        except Exception as e:
            logger.error(f"Failed to get connection metrics: {e}")

        return health_status

    async def shutdown(self) -> None:
        """Graceful shutdown with timeout"""
        logger.info("Starting graceful shutdown...")

        try:
            # Wait for ongoing operations with timeout
            await asyncio.wait_for(
                self.tracker.cleanup_all(), timeout=settings.request_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning("Graceful shutdown timeout, forcing cleanup...")

        logger.info("Resource manager shutdown complete")

        # Exit cleanly
        sys.exit(0)


# Global instance
_resource_manager: Optional[ProductionResourceManager] = None


async def get_resource_manager() -> ProductionResourceManager:
    """Get or create the global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ProductionResourceManager()
        await _resource_manager.initialize()
    return _resource_manager


# Convenience functions
async def get_managed_redis():
    """Get managed Redis client"""
    manager = await get_resource_manager()
    return await manager.get_redis_client()


async def get_managed_http_session():
    """Get managed HTTP session"""
    manager = await get_resource_manager()
    return await manager.get_http_session()


async def cleanup_resources():
    """Cleanup all resources"""
    if _resource_manager:
        await _resource_manager.shutdown()
