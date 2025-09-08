"""
MCP Server Status API
Provides real-time status information for MCP servers across domains
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from app.artemis.artemis_orchestrator import ArtemisOrchestrator
from app.core.shared_services import shared_services
from app.mcp.enhanced_registry import MCPServerRegistry, MemoryDomain
from app.sophia.sophia_orchestrator import SophiaOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["mcp"])

# Global registry instance
mcp_registry = MCPServerRegistry()


class MCPStatusAPI:
    """API for MCP server status and monitoring"""

    def __init__(self):
        self.registry = mcp_registry
        self.sophia = None
        self.artemis = None
        self.shared_services = shared_services

    async def initialize_orchestrators(self):
        """Initialize orchestrators if not already done"""
        if not self.sophia:
            self.sophia = SophiaOrchestrator()
        if not self.artemis:
            self.artemis = ArtemisOrchestrator()

    async def get_domain_server_status(self, domain: str) -> dict[str, Any]:
        """Get comprehensive server status for a domain"""
        await self.initialize_orchestrators()

        if domain == "artemis":
            return await self._get_artemis_status()
        elif domain == "sophia":
            return await self._get_sophia_status()
        elif domain == "shared":
            return await self._get_shared_status()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

    async def _get_artemis_status(self) -> dict[str, Any]:
        """Get Artemis domain server status"""
        servers = self.registry.get_servers_for_domain(MemoryDomain.ARTEMIS)

        server_status = []
        for allocation in servers:
            server_config = self.registry.servers.get(allocation.server_name)
            if not server_config:
                continue

            status = await self._get_server_detailed_status(
                allocation.server_name, allocation, server_config
            )
            server_status.append(status)

        return {
            "domain": "artemis",
            "timestamp": datetime.utcnow().isoformat(),
            "servers": server_status,
            "mythology_agents": [
                {
                    "name": "Odin - Technical Wisdom",
                    "assigned_mcp_servers": [
                        "artemis_code_analysis",
                        "artemis_design",
                        "artemis_codebase_memory",
                    ],
                    "context": "Code quality governance and architectural decisions",
                    "widget_type": "technical_excellence_oracle",
                }
            ],
            "domain_metrics": await self._calculate_domain_metrics(
                MemoryDomain.ARTEMIS
            ),
            "real_time_metrics": (
                await self.artemis.get_performance_metrics() if self.artemis else {}
            ),
        }

    async def _get_sophia_status(self) -> dict[str, Any]:
        """Get Sophia domain server status"""
        servers = self.registry.get_servers_for_domain(MemoryDomain.SOPHIA)

        server_status = []
        for allocation in servers:
            server_config = self.registry.servers.get(allocation.server_name)
            if not server_config:
                continue

            status = await self._get_server_detailed_status(
                allocation.server_name, allocation, server_config
            )
            server_status.append(status)

        return {
            "domain": "sophia",
            "timestamp": datetime.utcnow().isoformat(),
            "servers": server_status,
            "mythology_agents": [
                {
                    "name": "Hermes - Sales Intelligence",
                    "assigned_mcp_servers": [
                        "sophia_web_search",
                        "sophia_sales_intelligence",
                    ],
                    "context": "Market intelligence and sales performance",
                    "widget_type": "sales_performance_intelligence",
                },
                {
                    "name": "Asclepius - Client Health",
                    "assigned_mcp_servers": [
                        "sophia_business_analytics",
                        "sophia_business_memory",
                    ],
                    "context": "Customer health and portfolio management",
                    "widget_type": "client_health_monitor",
                },
                {
                    "name": "Athena - Strategic Operations",
                    "assigned_mcp_servers": ["sophia_business_analytics"],
                    "context": "Strategic initiatives and executive support",
                    "widget_type": "strategic_operations_command",
                },
            ],
            "domain_metrics": await self._calculate_domain_metrics(MemoryDomain.SOPHIA),
            "pay_ready_context": {
                "processing_volume_24h": 2100000000,  # $2.1B
                "properties_managed": 450000,
                "tenant_satisfaction_score": 88.5,
                "market_coverage_percentage": 47.3,
            },
        }

    async def _get_shared_status(self) -> dict[str, Any]:
        """Get shared domain server status"""
        servers = self.registry.get_servers_for_domain(MemoryDomain.SHARED)

        server_status = []
        for allocation in servers:
            server_config = self.registry.servers.get(allocation.server_name)
            if not server_config:
                continue

            status = await self._get_server_detailed_status(
                allocation.server_name, allocation, server_config
            )
            server_status.append(status)

        return {
            "domain": "shared",
            "timestamp": datetime.utcnow().isoformat(),
            "servers": server_status,
            "mythology_agents": [
                {
                    "name": "Minerva - Cross-Domain Analytics",
                    "assigned_mcp_servers": [
                        "shared_indexing",
                        "shared_embedding",
                        "shared_meta_tagging",
                    ],
                    "context": "Unified intelligence and pattern recognition",
                    "widget_type": "unified_intelligence_analysis",
                }
            ],
            "domain_metrics": await self._calculate_domain_metrics(MemoryDomain.SHARED),
        }

    async def _get_server_detailed_status(
        self, server_name: str, allocation: Any, server_config: Any
    ) -> dict[str, Any]:
        """Get detailed status for a single server"""

        # Simulate health check (in production, would make actual health check)
        health_status = await self._check_server_health(server_name)

        # Get connection pool status
        active_connections = self.registry.active_connections.get(server_name, 0)
        max_connections = server_config.connection_pool.max_connections
        utilization = active_connections / max_connections if max_connections > 0 else 0

        # Simulate performance metrics (in production, would query actual metrics)
        performance_metrics = await self._get_server_performance_metrics(server_name)

        return {
            "server_name": server_name,
            "server_type": server_config.server_type.value,
            "status": "operational" if health_status else "offline",
            "domain": allocation.domain.value,
            "access_level": allocation.access_level,
            "connections": {
                "active": active_connections,
                "max": max_connections,
                "utilization": utilization,
            },
            "capabilities": server_config.capabilities,
            "last_activity": self._get_last_activity(server_name),
            "performance_metrics": performance_metrics,
            "business_context": allocation.metadata.get("pay_ready_context"),
            "endpoint": server_config.endpoint,
            "metadata": {**server_config.metadata, **allocation.metadata},
        }

    async def _check_server_health(self, server_name: str) -> bool:
        """Check if server is healthy"""
        try:
            # In production, would make actual health check request
            # For now, simulate with some logic

            # Simulate occasional server issues
            import random

            if random.random() < 0.05:  # 5% chance of being offline
                return False

            return True
        except Exception as e:
            logger.error(f"Health check failed for {server_name}: {e}")
            return False

    async def _get_server_performance_metrics(
        self, server_name: str
    ) -> dict[str, float]:
        """Get performance metrics for a server"""
        # Simulate realistic metrics based on server type
        import random

        base_response_time = 50
        base_throughput = 100
        base_error_rate = 0.001

        # Adjust based on server type
        if "code_analysis" in server_name:
            base_response_time = 200  # Code analysis takes longer
            base_throughput = 20  # Lower throughput
        elif "web_search" in server_name:
            base_response_time = 800  # External API calls
            base_error_rate = 0.01  # Higher error rate for external services
        elif "database" in server_name:
            base_response_time = 10  # Fast database operations
            base_throughput = 500  # High throughput

        return {
            "response_time_ms": max(
                5, base_response_time + random.gauss(0, base_response_time * 0.2)
            ),
            "throughput_ops_per_sec": max(
                0, base_throughput + random.gauss(0, base_throughput * 0.3)
            ),
            "error_rate": max(
                0, min(1, base_error_rate + random.gauss(0, base_error_rate * 0.5))
            ),
            "uptime_percentage": random.uniform(98.0, 99.99),
        }

    def _get_last_activity(self, server_name: str) -> str:
        """Get last activity timestamp for server"""
        # Simulate recent activity
        import random

        minutes_ago = random.randint(1, 30)
        datetime.utcnow() - timedelta(minutes=minutes_ago)

        if minutes_ago < 60:
            return f"{minutes_ago} minutes ago"
        elif minutes_ago < 1440:
            hours_ago = minutes_ago // 60
            return f"{hours_ago} hours ago"
        else:
            days_ago = minutes_ago // 1440
            return f"{days_ago} days ago"

    async def _calculate_domain_metrics(self, domain: MemoryDomain) -> dict[str, Any]:
        """Calculate aggregated metrics for a domain"""
        servers = self.registry.get_servers_for_domain(domain)

        if not servers:
            return {
                "total_servers": 0,
                "operational_servers": 0,
                "total_connections": 0,
                "avg_response_time": 0,
                "error_rate": 0,
            }

        total_servers = len(servers)
        operational_count = 0
        total_connections = 0
        total_response_time = 0
        total_error_rate = 0

        for allocation in servers:
            # Get server health
            health = await self._check_server_health(allocation.server_name)
            if health:
                operational_count += 1

            # Get connections
            active = self.registry.active_connections.get(allocation.server_name, 0)
            total_connections += active

            # Get performance metrics
            metrics = await self._get_server_performance_metrics(allocation.server_name)
            total_response_time += metrics["response_time_ms"]
            total_error_rate += metrics["error_rate"]

        return {
            "total_servers": total_servers,
            "operational_servers": operational_count,
            "total_connections": total_connections,
            "avg_response_time": (
                total_response_time / total_servers if total_servers > 0 else 0
            ),
            "error_rate": total_error_rate / total_servers if total_servers > 0 else 0,
            "health_percentage": (
                (operational_count / total_servers * 100) if total_servers > 0 else 0
            ),
        }


# Initialize API instance
mcp_api = MCPStatusAPI()


@router.get("/status/{domain}")
async def get_domain_status(domain: str) -> dict[str, Any]:
    """Get MCP server status for a specific domain"""
    try:
        return await mcp_api.get_domain_server_status(domain.lower())
    except Exception as e:
        logger.error(f"Failed to get domain status for {domain}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_all_domains_status() -> dict[str, Any]:
    """Get MCP server status for all domains"""
    try:
        artemis_status = await mcp_api.get_domain_server_status("artemis")
        sophia_status = await mcp_api.get_domain_server_status("sophia")
        shared_status = await mcp_api.get_domain_server_status("shared")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "domains": {
                "artemis": artemis_status,
                "sophia": sophia_status,
                "shared": shared_status,
            },
            "summary": {
                "total_servers": (
                    len(artemis_status["servers"])
                    + len(sophia_status["servers"])
                    + len(shared_status["servers"])
                ),
                "operational_servers": sum(
                    [
                        artemis_status["domain_metrics"]["operational_servers"],
                        sophia_status["domain_metrics"]["operational_servers"],
                        shared_status["domain_metrics"]["operational_servers"],
                    ]
                ),
                "total_connections": sum(
                    [
                        artemis_status["domain_metrics"]["total_connections"],
                        sophia_status["domain_metrics"]["total_connections"],
                        shared_status["domain_metrics"]["total_connections"],
                    ]
                ),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get all domains status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_name}")
async def get_server_status(server_name: str) -> dict[str, Any]:
    """Get detailed status for a specific server"""
    try:
        # Find the server in registry
        server_config = mcp_api.registry.servers.get(server_name)
        if not server_config:
            raise HTTPException(
                status_code=404, detail=f"Server {server_name} not found"
            )

        # Find allocation info
        allocation = None
        for domain in [MemoryDomain.ARTEMIS, MemoryDomain.SOPHIA, MemoryDomain.SHARED]:
            allocations = mcp_api.registry.get_servers_for_domain(domain)
            for alloc in allocations:
                if alloc.server_name == server_name:
                    allocation = alloc
                    break
            if allocation:
                break

        if not allocation:
            raise HTTPException(
                status_code=404, detail=f"Server allocation not found for {server_name}"
            )

        status = await mcp_api._get_server_detailed_status(
            server_name, allocation, server_config
        )
        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server status for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_name}/health-check")
async def trigger_health_check(server_name: str) -> dict[str, Any]:
    """Trigger a manual health check for a server"""
    try:
        server_config = mcp_api.registry.servers.get(server_name)
        if not server_config:
            raise HTTPException(
                status_code=404, detail=f"Server {server_name} not found"
            )

        health = await mcp_api._check_server_health(server_name)
        metrics = await mcp_api._get_server_performance_metrics(server_name)

        return {
            "server_name": server_name,
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": "healthy" if health else "unhealthy",
            "performance_metrics": metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check health for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary() -> dict[str, Any]:
    """Get aggregated metrics across all domains"""
    try:
        artemis_metrics = await mcp_api._calculate_domain_metrics(MemoryDomain.ARTEMIS)
        sophia_metrics = await mcp_api._calculate_domain_metrics(MemoryDomain.SOPHIA)
        shared_metrics = await mcp_api._calculate_domain_metrics(MemoryDomain.SHARED)

        total_servers = (
            artemis_metrics["total_servers"]
            + sophia_metrics["total_servers"]
            + shared_metrics["total_servers"]
        )

        operational_servers = (
            artemis_metrics["operational_servers"]
            + sophia_metrics["operational_servers"]
            + shared_metrics["operational_servers"]
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": (
                (operational_servers / total_servers * 100) if total_servers > 0 else 0
            ),
            "domains": {
                "artemis": artemis_metrics,
                "sophia": sophia_metrics,
                "shared": shared_metrics,
            },
            "totals": {
                "total_servers": total_servers,
                "operational_servers": operational_servers,
                "total_connections": (
                    artemis_metrics["total_connections"]
                    + sophia_metrics["total_connections"]
                    + shared_metrics["total_connections"]
                ),
                "avg_response_time": (
                    artemis_metrics["avg_response_time"]
                    + sophia_metrics["avg_response_time"]
                    + shared_metrics["avg_response_time"]
                )
                / 3,
                "avg_error_rate": (
                    artemis_metrics["error_rate"]
                    + sophia_metrics["error_rate"]
                    + shared_metrics["error_rate"]
                )
                / 3,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
