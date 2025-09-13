"\nService Discovery Module for Sophia AI\nProvides service registration and discovery capabilities for MCP servers and other services\n"
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)
class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"
@dataclass
class ServiceInfo:
    """Service information container"""
    name: str
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_heartbeat: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        if self.status != ServiceStatus.HEALTHY:
            return False
        if self.last_heartbeat is None:
            return False
        return datetime.now() - self.last_heartbeat < timedelta(seconds=60)
class ServiceDiscovery:
    """Service discovery and health management"""
    def __init__(self):
        self.services: dict[str, ServiceInfo] = {}
        self.health_check_interval = 30
        self._health_check_task: asyncio.Task | None = None
    async def start(self):
        """Start the service discovery system"""
        logger.info("🚀 Starting service discovery...")
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    async def stop(self):
        """Stop the service discovery system"""
        logger.info("🛑 Stopping service discovery...")
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    async def register_service(self, service_info: ServiceInfo) -> bool:
        """Register a service"""
        try:
            service_info.last_heartbeat = datetime.now()
            service_info.status = ServiceStatus.STARTING
            if await self._check_service_health(service_info):
                service_info.status = ServiceStatus.HEALTHY
                self.services[service_info.name] = service_info
                logger.info(
                    f"✅ Registered service: {service_info.name} at {service_info.host}:{service_info.port}"
                )
                return True
            else:
                service_info.status = ServiceStatus.UNHEALTHY
                self.services[service_info.name] = service_info
                logger.warning(f"⚠️  Registered unhealthy service: {service_info.name}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to register service {service_info.name}: {e}")
            return False
    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service"""
        if service_name in self.services:
            service_info = self.services[service_name]
            service_info.status = ServiceStatus.STOPPING
            del self.services[service_name]
            logger.info(f"✅ Unregistered service: {service_name}")
            return True
        else:
            logger.warning(f"⚠️  Service not found for unregistration: {service_name}")
            return False
    async def get_service(self, service_name: str) -> ServiceInfo | None:
        """Get service information"""
        return self.services.get(service_name)
    async def get_healthy_services(self) -> list[ServiceInfo]:
        """Get all healthy services"""
        return [service for service in self.services.values() if service.is_healthy]
    async def get_all_services(self) -> dict[str, ServiceInfo]:
        """Get all registered services"""
        return self.services.copy()
    async def heartbeat(self, service_name: str) -> bool:
        """Update service heartbeat"""
        if service_name in self.services:
            self.services[service_name].last_heartbeat = datetime.now()
            return True
        return False
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    async def _perform_health_checks(self):
        """Perform health checks on all services"""
        if not self.services:
            return
        tasks = []
        for service_info in self.services.values():
            task = asyncio.create_task(self._update_service_health(service_info))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
    async def _update_service_health(self, service_info: ServiceInfo):
        """Update health status for a single service"""
        try:
            is_healthy = await self._check_service_health(service_info)
            old_status = service_info.status
            if is_healthy:
                service_info.status = ServiceStatus.HEALTHY
                service_info.last_heartbeat = datetime.now()
            else:
                service_info.status = ServiceStatus.UNHEALTHY
            if old_status != service_info.status:
                logger.info(
                    f"🔄 Service {service_info.name} status changed: {old_status.value} → {service_info.status.value}"
                )
        except Exception as e:
            logger.error(f"Health check failed for {service_info.name}: {e}")
            service_info.status = ServiceStatus.UNKNOWN
    async def _check_service_health(self, service_info: ServiceInfo) -> bool:
        """Check if a service is healthy"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(service_info.host, service_info.port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    async def get_health_summary(self) -> dict[str, Any]:
        """Get health summary of all services"""
        total_services = len(self.services)
        healthy_services = len(await self.get_healthy_services())
        status_counts = {}
        for status in ServiceStatus:
            status_counts[status.value] = sum(
                1 for service in self.services.values() if service.status == status
            )
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "health_percentage": (
                healthy_services / total_services * 100 if total_services > 0 else 0
            ),
            "status_breakdown": status_counts,
            "last_check": datetime.now().isoformat(),
        }
_service_discovery: ServiceDiscovery | None = None
async def get_service_discovery() -> ServiceDiscovery:
    """Get or create the global service discovery instance"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.start()
    return _service_discovery
async def register_mcp_server(
    name: str, host: str, port: int, metadata: dict[str, Any] = None
) -> bool:
    """Convenience function to register an MCP server"""
    service_discovery = await get_service_discovery()
    service_info = ServiceInfo(
        name=f"mcp-{name}",
        host=host,
        port=port,
        metadata=metadata or {"type": "mcp_server", "server_name": name},
    )
    return await service_discovery.register_service(service_info)
async def get_mcp_servers() -> list[ServiceInfo]:
    """Get all registered MCP servers"""
    service_discovery = await get_service_discovery()
    all_services = await service_discovery.get_healthy_services()
    return [
        service
        for service in all_services
        if service.metadata.get("type") == "mcp_server"
    ]
