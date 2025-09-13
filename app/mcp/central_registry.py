#!/usr/bin/env python3
"""
Central MCP Registry - Phase 2 Implementation
Centralized registration and management system for all MCP servers
Integrates with existing optimized_mcp_orchestrator.py
"""
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import redis.asyncio as redis
from pydantic import BaseModel, Field, validator
from .optimized_mcp_orchestrator import (
    MCPCapabilityType,
    MCPDomain,
    OptimizedMCPOrchestrator,
)
logger = logging.getLogger(__name__)
class ServerStatus(Enum):
    """MCP Server status enumeration"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"
class ConnectionType(Enum):
    """MCP Connection type enumeration"""
    WEBSOCKET = "websocket"
    HTTP = "http"
    STDIO = "stdio"
    TCP = "tcp"
class MCPServerRegistration(BaseModel):
    """MCP Server registration model"""
    server_id: str
    name: str
    domain: MCPDomain
    capabilities: list[MCPCapabilityType]
    endpoint: str
    connection_type: ConnectionType = ConnectionType.WEBSOCKET
    priority: int = Field(default=10, ge=1, le=100)
    max_connections: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    # Health check configuration
    health_check_interval: int = Field(default=30, ge=5, le=300)
    health_check_endpoint: str = "/health"
    max_consecutive_failures: int = Field(default=3, ge=1, le=10)
    # Metadata
    version: str = "1.0.0"
    description: str = ""
    tags: set[str] = set()
    created_at: datetime = Field(default_factory=datetime.now)
    # Runtime state (not stored in registration)
    status: ServerStatus = ServerStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    active_connections: int = 0
    @validator("server_id")
    def validate_server_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Server ID must be at least 3 characters")
        return v
    @validator("endpoint")
    def validate_endpoint(cls, v):
        if not v:
            raise ValueError("Endpoint is required")
        return v
    def dict(self, **kwargs):
        """Override to handle datetime serialization"""
        result = super().dict(**kwargs)
        # Convert datetime fields to ISO format
        if "created_at" in result and isinstance(result["created_at"], datetime):
            result["created_at"] = result["created_at"].isoformat()
        if "last_health_check" in result and isinstance(
            result["last_health_check"], datetime
        ):
            result["last_health_check"] = result["last_health_check"].isoformat()
        # Convert enums to values
        if "domain" in result:
            result["domain"] = (
                result["domain"].value
                if hasattr(result["domain"], "value")
                else str(result["domain"])
            )
        if "connection_type" in result:
            result["connection_type"] = (
                result["connection_type"].value
                if hasattr(result["connection_type"], "value")
                else str(result["connection_type"])
            )
        if "status" in result:
            result["status"] = (
                result["status"].value
                if hasattr(result["status"], "value")
                else str(result["status"])
            )
        if "capabilities" in result:
            result["capabilities"] = [
                c.value if hasattr(c, "value") else str(c)
                for c in result["capabilities"]
            ]
        if "tags" in result:
            result["tags"] = list(result["tags"])
        return result
class ServerLoadBalancer:
    """Load balancer for MCP servers"""
    def __init__(self):
        self.round_robin_counters: dict[str, int] = {}
    def select_server(
        self,
        servers: list[MCPServerRegistration],
        strategy: str = "priority",
        exclude_unhealthy: bool = True,
    ) -> Optional[MCPServerRegistration]:
        """Select a server based on load balancing strategy"""
        if not servers:
            return None
        # Filter out unhealthy servers if requested
        available_servers = [
            s
            for s in servers
            if not exclude_unhealthy
            or s.status in [ServerStatus.HEALTHY, ServerStatus.DEGRADED]
        ]
        if not available_servers:
            # If all are unhealthy but we have servers, return the first one as last resort
            return servers[0] if servers else None
        if strategy == "priority":
            # Sort by priority (lower number = higher priority) then by load
            return min(
                available_servers,
                key=lambda s: (s.priority, s.active_connections / s.max_connections),
            )
        elif strategy == "round_robin":
            domain_key = available_servers[0].domain.value
            counter = self.round_robin_counters.get(domain_key, 0)
            selected = available_servers[counter % len(available_servers)]
            self.round_robin_counters[domain_key] = counter + 1
            return selected
        elif strategy == "least_connections":
            return min(available_servers, key=lambda s: s.active_connections)
        else:
            # Default to priority
            return self.select_server(available_servers, "priority", False)
class CentralMCPRegistry:
    """
    Centralized MCP Registry for server discovery, health monitoring, and load balancing
    Integrates with existing optimized_mcp_orchestrator.py
    """
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.orchestrator: Optional[OptimizedMCPOrchestrator] = None
        # Registry storage
        self.registered_servers: dict[str, MCPServerRegistration] = {}
        self.domain_servers: dict[MCPDomain, list[str]] = {
            MCPDomain.CORE: [],
            MCPDomain.SOPHIA: [],
            MCPDomain.SHARED: [],
        }
        # Load balancer
        self.load_balancer = ServerLoadBalancer()
        # Health monitoring
        self.health_check_tasks: dict[str, asyncio.Task] = {}
        self.monitoring_enabled = True
        # Metrics
        self.metrics = {
            "total_registrations": 0,
            "health_checks_performed": 0,
            "failed_health_checks": 0,
            "server_status_changes": 0,
            "load_balancer_requests": 0,
            "last_registry_sync": None,
        }
    async def initialize(self) -> bool:
        """Initialize the registry with Redis and orchestrator"""
        try:
            # Initialize Redis connection
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                retry_on_timeout=True,
            )
            # Test Redis connection
            await self.redis.ping()
            logger.info("✅ Central MCP Registry Redis connection established")
            # Initialize orchestrator integration
            self.orchestrator = OptimizedMCPOrchestrator(self.redis_url)
            await self.orchestrator.initialize()
            logger.info("✅ MCP Orchestrator integration established")
            # Load existing registrations from Redis
            await self._load_registrations_from_storage()
            # Start health monitoring
            if self.monitoring_enabled:
                asyncio.create_task(self._health_monitoring_loop())
            # Start registry sync
            asyncio.create_task(self._registry_sync_loop())
            logger.info(
                f"🚀 Central MCP Registry initialized with {len(self.registered_servers)} servers"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Central MCP Registry: {e}")
            return False
    async def register_server(self, registration: MCPServerRegistration) -> bool:
        """Register a new MCP server"""
        try:
            server_id = registration.server_id
            # Validate registration
            if server_id in self.registered_servers:
                logger.warning(
                    f"Server {server_id} already registered, updating registration"
                )
            # Store registration
            self.registered_servers[server_id] = registration
            # Add to domain mapping
            if server_id not in self.domain_servers[registration.domain]:
                self.domain_servers[registration.domain].append(server_id)
            # Persist to Redis
            await self._persist_registration(registration)
            # Start health monitoring for this server
            if self.monitoring_enabled:
                await self._start_health_monitoring(server_id)
            # Update metrics
            self.metrics["total_registrations"] += 1
            logger.info(
                f"✅ Registered MCP server: {server_id} (domain: {registration.domain.value})"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to register server {registration.server_id}: {e}")
            return False
    async def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server"""
        try:
            if server_id not in self.registered_servers:
                logger.warning(f"Server {server_id} not found for unregistration")
                return False
            registration = self.registered_servers[server_id]
            # Stop health monitoring
            if server_id in self.health_check_tasks:
                self.health_check_tasks[server_id].cancel()
                del self.health_check_tasks[server_id]
            # Remove from domain mapping
            if server_id in self.domain_servers[registration.domain]:
                self.domain_servers[registration.domain].remove(server_id)
            # Remove from registry
            del self.registered_servers[server_id]
            # Remove from Redis
            await self._delete_registration(server_id)
            logger.info(f"✅ Unregistered MCP server: {server_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to unregister server {server_id}: {e}")
            return False
    async def discover_servers(
        self,
        domain: Optional[MCPDomain] = None,
        capabilities: Optional[list[MCPCapabilityType]] = None,
        status_filter: Optional[list[ServerStatus]] = None,
        tags: Optional[set[str]] = None,
    ) -> list[MCPServerRegistration]:
        """Discover servers based on criteria"""
        servers = list(self.registered_servers.values())
        # Filter by domain
        if domain:
            servers = [s for s in servers if s.domain == domain]
        # Filter by capabilities
        if capabilities:
            servers = [
                s for s in servers if any(cap in s.capabilities for cap in capabilities)
            ]
        # Filter by status
        if status_filter:
            servers = [s for s in servers if s.status in status_filter]
        # Filter by tags
        if tags:
            servers = [s for s in servers if tags.intersection(s.tags)]
        return servers
    async def get_server_for_request(
        self,
        domain: MCPDomain,
        capability: MCPCapabilityType,
        load_balance_strategy: str = "priority",
    ) -> Optional[MCPServerRegistration]:
        """Get the best server for a specific request"""
        # Find servers that can handle this capability
        candidate_servers = await self.discover_servers(
            domain=domain,
            capabilities=[capability],
            status_filter=[ServerStatus.HEALTHY, ServerStatus.DEGRADED],
        )
        if not candidate_servers:
            logger.warning(
                f"No servers found for domain {domain.value} with capability {capability.value}"
            )
            return None
        # Use load balancer to select best server
        selected = self.load_balancer.select_server(
            candidate_servers, load_balance_strategy
        )
        if selected:
            self.metrics["load_balancer_requests"] += 1
        return selected
    async def update_server_status(
        self, server_id: str, status: ServerStatus, details: Optional[dict] = None
    ):
        """Update server status"""
        if server_id not in self.registered_servers:
            return
        old_status = self.registered_servers[server_id].status
        self.registered_servers[server_id].status = status
        self.registered_servers[server_id].last_health_check = datetime.now()
        # Reset failure count on success
        if status == ServerStatus.HEALTHY:
            self.registered_servers[server_id].consecutive_failures = 0
        if old_status != status:
            self.metrics["server_status_changes"] += 1
            logger.info(
                f"Server {server_id} status changed: {old_status.value} → {status.value}"
            )
        # Persist status change
        await self._persist_registration(self.registered_servers[server_id])
    async def get_registry_status(self) -> dict[str, Any]:
        """Get comprehensive registry status"""
        status_counts = {}
        for status in ServerStatus:
            status_counts[status.value] = sum(
                1
                for server in self.registered_servers.values()
                if server.status == status
            )
        domain_counts = {}
        for domain in MCPDomain:
            domain_counts[domain.value] = len(self.domain_servers[domain])
        capability_counts = {}
        for capability in MCPCapabilityType:
            capability_counts[capability.value] = sum(
                1
                for server in self.registered_servers.values()
                if capability in server.capabilities
            )
        return {
            "timestamp": datetime.now().isoformat(),
            "total_servers": len(self.registered_servers),
            "status_distribution": status_counts,
            "domain_distribution": domain_counts,
            "capability_distribution": capability_counts,
            "metrics": self.metrics,
            "monitoring_enabled": self.monitoring_enabled,
            "redis_connected": self.redis is not None,
            "orchestrator_integrated": self.orchestrator is not None,
        }
    async def get_server_details(self, server_id: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a specific server"""
        if server_id not in self.registered_servers:
            return None
        server = self.registered_servers[server_id]
        # Get additional runtime metrics if available
        runtime_metrics = {}
        if self.orchestrator:
            try:
                # Try to get metrics from orchestrator
                health_status = await self.orchestrator.get_health_status()
                if server_id in health_status.get("health_checks", {}):
                    runtime_metrics = health_status["health_checks"][server_id]
            except Exception as e:
                logger.debug(f"Could not get runtime metrics for {server_id}: {e}")
        result = server.dict()
        result["runtime_metrics"] = runtime_metrics
        return result
    # Health Monitoring Methods
    async def _start_health_monitoring(self, server_id: str):
        """Start health monitoring for a server"""
        if server_id in self.health_check_tasks:
            self.health_check_tasks[server_id].cancel()
        self.health_check_tasks[server_id] = asyncio.create_task(
            self._health_check_loop(server_id)
        )
    async def _health_check_loop(self, server_id: str):
        """Health check loop for a specific server"""
        while server_id in self.registered_servers and self.monitoring_enabled:
            try:
                registration = self.registered_servers[server_id]
                await asyncio.sleep(registration.health_check_interval)
                # Perform health check
                is_healthy = await self._perform_health_check(server_id)
                if is_healthy:
                    await self.update_server_status(server_id, ServerStatus.HEALTHY)
                else:
                    registration.consecutive_failures += 1
                    if (
                        registration.consecutive_failures
                        >= registration.max_consecutive_failures
                    ):
                        await self.update_server_status(
                            server_id, ServerStatus.UNHEALTHY
                        )
                    else:
                        await self.update_server_status(
                            server_id, ServerStatus.DEGRADED
                        )
                self.metrics["health_checks_performed"] += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {server_id}: {e}")
                self.metrics["failed_health_checks"] += 1
                await asyncio.sleep(30)  # Wait before retrying
    async def _perform_health_check(self, server_id: str) -> bool:
        """Perform actual health check on a server"""
        try:
            self.registered_servers[server_id]
            # Use orchestrator for health check if available
            if self.orchestrator:
                # For now, we'll use a simple ping-style check
                # In production, this would make actual HTTP/WebSocket requests
                return True  # Placeholder - implement actual health check
            return False
        except Exception as e:
            logger.error(f"Health check failed for {server_id}: {e}")
            return False
    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(60)  # Overall monitoring check every minute
                # Cleanup completed tasks
                completed_tasks = [
                    server_id
                    for server_id, task in self.health_check_tasks.items()
                    if task.done()
                ]
                for server_id in completed_tasks:
                    del self.health_check_tasks[server_id]
                    # Restart health monitoring if server still registered
                    if server_id in self.registered_servers:
                        await self._start_health_monitoring(server_id)
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
    # Persistence Methods
    async def _persist_registration(self, registration: MCPServerRegistration):
        """Persist registration to Redis"""
        if not self.redis:
            return
        try:
            key = f"mcp:registry:server:{registration.server_id}"
            data = registration.dict()
            await self.redis.hset(key, mapping={"data": json.dumps(data)})
        except Exception as e:
            logger.error(
                f"Failed to persist registration {registration.server_id}: {e}"
            )
    async def _delete_registration(self, server_id: str):
        """Delete registration from Redis"""
        if not self.redis:
            return
        try:
            key = f"mcp:registry:server:{server_id}"
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete registration {server_id}: {e}")
    async def _load_registrations_from_storage(self):
        """Load existing registrations from Redis"""
        if not self.redis:
            return
        try:
            pattern = "mcp:registry:server:*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            for key in keys:
                try:
                    stored_data = await self.redis.hget(key, "data")
                    if stored_data:
                        data = json.loads(stored_data)
                        # Convert back to enums
                        data["domain"] = MCPDomain(data["domain"])
                        data["connection_type"] = ConnectionType(
                            data["connection_type"]
                        )
                        data["status"] = ServerStatus(data["status"])
                        data["capabilities"] = [
                            MCPCapabilityType(c) for c in data["capabilities"]
                        ]
                        data["tags"] = set(data["tags"])
                        # Handle datetime fields
                        if "created_at" in data:
                            data["created_at"] = datetime.fromisoformat(
                                data["created_at"]
                            )
                        if "last_health_check" in data and data["last_health_check"]:
                            data["last_health_check"] = datetime.fromisoformat(
                                data["last_health_check"]
                            )
                        registration = MCPServerRegistration(**data)
                        # Restore to registry
                        self.registered_servers[registration.server_id] = registration
                        if (
                            registration.server_id
                            not in self.domain_servers[registration.domain]
                        ):
                            self.domain_servers[registration.domain].append(
                                registration.server_id
                            )
                except Exception as e:
                    logger.error(f"Failed to load registration from {key}: {e}")
            logger.info(
                f"✅ Loaded {len(self.registered_servers)} registrations from storage"
            )
        except Exception as e:
            logger.error(f"Failed to load registrations from storage: {e}")
    async def _registry_sync_loop(self):
        """Periodic registry synchronization"""
        while True:
            try:
                await asyncio.sleep(300)  # Sync every 5 minutes
                # Update last sync time
                self.metrics["last_registry_sync"] = datetime.now().isoformat()
                # Sync with orchestrator if available
                if self.orchestrator:
                    orchestrator_capabilities = (
                        await self.orchestrator.get_capabilities()
                    )
                    # Auto-register orchestrator servers if not already registered
                    for server_id, config in orchestrator_capabilities.items():
                        if server_id not in self.registered_servers:
                            # Create registration from orchestrator config
                            registration = MCPServerRegistration(
                                server_id=server_id,
                                name=config["name"],
                                domain=MCPDomain(config["domain"]),
                                capabilities=[
                                    MCPCapabilityType(cap["name"])
                                    for cap in config["capabilities"]
                                    if cap["name"]
                                    in [c.value for c in MCPCapabilityType]
                                ],
                                endpoint="internal://orchestrator",
                                connection_type=ConnectionType.HTTP,
                                description="Auto-registered from orchestrator",
                                tags={"auto_registered", "orchestrator"},
                            )
                            await self.register_server(registration)
                            logger.info(
                                f"Auto-registered orchestrator server: {server_id}"
                            )
            except Exception as e:
                logger.error(f"Registry sync error: {e}")
    async def shutdown(self):
        """Graceful shutdown"""
        self.monitoring_enabled = False
        # Cancel all health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()
        # Wait for tasks to complete
        if self.health_check_tasks:
            await asyncio.gather(
                *self.health_check_tasks.values(), return_exceptions=True
            )
        # Close Redis connection
        if self.redis:
            await self.redis.close()
        # Shutdown orchestrator
        if self.orchestrator:
            await self.orchestrator.shutdown()
        logger.info("🔌 Central MCP Registry shut down gracefully")
# Global registry instance
_global_registry: Optional[CentralMCPRegistry] = None
async def get_central_registry() -> CentralMCPRegistry:
    """Get global central registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = CentralMCPRegistry()
        await _global_registry.initialize()
    return _global_registry
async def register_mcp_server(registration: MCPServerRegistration) -> bool:
    """Convenience function to register an MCP server"""
    registry = await get_central_registry()
    return await registry.register_server(registration)
async def discover_mcp_servers(
    domain: Optional[MCPDomain] = None,
    capabilities: Optional[list[MCPCapabilityType]] = None,
) -> list[MCPServerRegistration]:
    """Convenience function to discover MCP servers"""
    registry = await get_central_registry()
    return await registry.discover_servers(domain=domain, capabilities=capabilities)
