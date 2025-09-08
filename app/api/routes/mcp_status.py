"""
MCP Server Status and Health Monitoring API
Provides real-time status updates and health metrics for all MCP servers
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.middleware.auth import get_current_user
from app.core.websocket_manager import WebSocketManager
from app.mcp.connection_manager import MCPConnectionManager
from app.mcp.enhanced_registry import MCPServerRegistry, MemoryDomain

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp-status", tags=["mcp-status"])

# Global instances
mcp_registry = MCPServerRegistry()
connection_manager = MCPConnectionManager()
ws_manager = WebSocketManager()


# ==================== REQUEST/RESPONSE MODELS ====================


class MCPServerHealth(BaseModel):
    """MCP server health status model"""

    server_name: str
    server_type: str
    domain: str
    status: str  # operational, degraded, down, unknown
    uptime_percentage: float
    response_time_ms: int
    throughput_ops_per_sec: int
    error_rate: float
    last_activity: str
    connections: dict[str, Any]
    business_context: str | None = None


class MCPDomainSummary(BaseModel):
    """Domain-level MCP status summary"""

    domain: str
    total_servers: int
    operational_servers: int
    degraded_servers: int
    down_servers: int
    total_connections: int
    avg_response_time_ms: float
    overall_health_score: float
    pay_ready_context: dict[str, Any] | None = None


class MCPSystemOverview(BaseModel):
    """System-wide MCP status overview"""

    timestamp: str
    overall_status: str
    total_servers: int
    healthy_servers: int
    domain_summaries: list[MCPDomainSummary]
    system_metrics: dict[str, Any]
    mythology_agents: list[dict[str, Any]]


# ==================== HELPER FUNCTIONS ====================


async def _get_server_health_status(server_name: str, server_config: Any) -> MCPServerHealth:
    """Get detailed health status for a specific MCP server"""
    try:
        # Simulate health check - in production this would ping the actual server
        is_responsive = await _ping_server(server_name)

        # Get current connections
        active_connections = mcp_registry.active_connections.get(server_name, 0)
        max_connections = (
            server_config.connection_pool.max_connections
            if hasattr(server_config, "connection_pool")
            else 10
        )

        # Determine status
        if not is_responsive:
            status = "down"
        elif active_connections >= max_connections * 0.9:
            status = "degraded"  # High utilization
        else:
            status = "operational"

        # Get performance metrics (simulated for now)
        perf_metrics = await _get_server_performance_metrics(server_name)

        # Determine domain and business context
        domain = "shared"
        business_context = None

        # Check Artemis domain
        artemis_allocations = mcp_registry.get_servers_for_domain(MemoryDomain.ARTEMIS)
        if any(alloc.server_name == server_name for alloc in artemis_allocations):
            domain = "artemis"
            business_context = _get_artemis_business_context(server_name)

        # Check Sophia domain
        sophia_allocations = mcp_registry.get_servers_for_domain(MemoryDomain.SOPHIA)
        if any(alloc.server_name == server_name for alloc in sophia_allocations):
            domain = "sophia"
            business_context = _get_sophia_business_context(server_name)

        return MCPServerHealth(
            server_name=server_name,
            server_type=(
                server_config.server_type.value
                if hasattr(server_config, "server_type")
                else "unknown"
            ),
            domain=domain,
            status=status,
            uptime_percentage=perf_metrics.get("uptime_percentage", 99.0),
            response_time_ms=perf_metrics.get("response_time_ms", 150),
            throughput_ops_per_sec=perf_metrics.get("throughput_ops_per_sec", 50),
            error_rate=perf_metrics.get("error_rate", 0.01),
            last_activity=perf_metrics.get("last_activity", "2 minutes ago"),
            connections={
                "active": active_connections,
                "max": max_connections,
                "utilization": active_connections / max_connections if max_connections > 0 else 0.0,
            },
            business_context=business_context,
        )

    except Exception as e:
        logger.error(f"Failed to get health status for {server_name}: {e}")
        return MCPServerHealth(
            server_name=server_name,
            server_type="unknown",
            domain="unknown",
            status="unknown",
            uptime_percentage=0.0,
            response_time_ms=0,
            throughput_ops_per_sec=0,
            error_rate=1.0,
            last_activity="unknown",
            connections={"active": 0, "max": 0, "utilization": 0.0},
        )


async def _ping_server(server_name: str) -> bool:
    """Ping a server to check responsiveness"""
    try:
        # In production, this would make actual health check requests
        # For now, simulate with some logic
        await asyncio.sleep(0.1)  # Simulate network delay
        return True  # Assume servers are responsive for now
    except Exception:
        return False


async def _get_server_performance_metrics(server_name: str) -> dict[str, Any]:
    """Get performance metrics for a server"""
    # Simulated metrics - in production would come from monitoring systems
    base_metrics = {
        "uptime_percentage": 99.2,
        "response_time_ms": 150,
        "throughput_ops_per_sec": 75,
        "error_rate": 0.005,
        "last_activity": "2 minutes ago",
    }

    # Adjust metrics based on server type
    if "filesystem" in server_name:
        base_metrics.update(
            {"response_time_ms": 50, "throughput_ops_per_sec": 200, "uptime_percentage": 99.8}
        )
    elif "web_search" in server_name:
        base_metrics.update(
            {"response_time_ms": 650, "throughput_ops_per_sec": 45, "error_rate": 0.008}
        )
    elif "analytics" in server_name:
        base_metrics.update(
            {"response_time_ms": 180, "throughput_ops_per_sec": 125, "uptime_percentage": 99.8}
        )

    return base_metrics


def _get_artemis_business_context(server_name: str) -> str:
    """Get business context for Artemis servers"""
    context_map = {
        "artemis_filesystem": "code_repository_management",
        "artemis_code_analysis": "technical_debt_monitoring",
        "artemis_design": "architecture_documentation",
        "shared_database": "technical_metrics_storage",
        "shared_indexing": "code_search_optimization",
        "shared_embedding": "code_similarity_analysis",
    }
    return context_map.get(server_name, "technical_operations")


def _get_sophia_business_context(server_name: str) -> str:
    """Get business context for Sophia servers"""
    context_map = {
        "sophia_web_search": "market_intelligence_gathering",
        "sophia_analytics": "pay_ready_operations",
        "sophia_sales_intelligence": "property_sales_optimization",
        "shared_database": "business_metrics_storage",
        "shared_indexing": "business_search_optimization",
        "shared_embedding": "business_similarity_analysis",
    }
    return context_map.get(server_name, "business_operations")


async def _get_domain_summary(domain: str) -> MCPDomainSummary:
    """Get health summary for a specific domain"""
    domain_enum = {
        "artemis": MemoryDomain.ARTEMIS,
        "sophia": MemoryDomain.SOPHIA,
        "shared": MemoryDomain.SHARED,
    }.get(domain)

    if not domain_enum:
        raise ValueError(f"Invalid domain: {domain}")

    # Get all servers for the domain
    allocations = mcp_registry.get_servers_for_domain(domain_enum)
    server_healths = []

    for allocation in allocations:
        server_config = mcp_registry.servers.get(allocation.server_name)
        if server_config:
            health = await _get_server_health_status(allocation.server_name, server_config)
            server_healths.append(health)

    # Calculate summary metrics
    total_servers = len(server_healths)
    operational_servers = sum(1 for h in server_healths if h.status == "operational")
    degraded_servers = sum(1 for h in server_healths if h.status == "degraded")
    down_servers = sum(1 for h in server_healths if h.status == "down")

    total_connections = sum(h.connections["active"] for h in server_healths)
    avg_response_time = sum(h.response_time_ms for h in server_healths) / max(total_servers, 1)

    # Calculate overall health score
    health_score = (operational_servers * 100 + degraded_servers * 50) / max(total_servers * 100, 1)

    # Add Pay Ready context for Sophia domain
    pay_ready_context = None
    if domain == "sophia":
        pay_ready_context = {
            "processing_volume_today": 2100000000,  # $2.1B
            "market_share": 47.3,
            "properties_under_management": 15000,
            "compliance_score": 97.2,
        }

    return MCPDomainSummary(
        domain=domain,
        total_servers=total_servers,
        operational_servers=operational_servers,
        degraded_servers=degraded_servers,
        down_servers=down_servers,
        total_connections=total_connections,
        avg_response_time_ms=avg_response_time,
        overall_health_score=health_score,
        pay_ready_context=pay_ready_context,
    )


def _get_mythology_agents_status() -> list[dict[str, Any]]:
    """Get status of mythology agents and their MCP server assignments"""
    return [
        {
            "id": "hermes",
            "name": "Hermes",
            "domain": "sophia",
            "title": "Sales Intelligence & Market Analysis",
            "assigned_mcp_servers": ["sophia_web_search", "sophia_sales_intelligence"],
            "status": "operational",
            "primary_metric": {"label": "Processing Volume", "value": "$2.1B", "trend": "up"},
            "pay_ready_context": "property_management_sales",
        },
        {
            "id": "asclepius",
            "name": "Asclepius",
            "domain": "sophia",
            "title": "Client Health & Portfolio Management",
            "assigned_mcp_servers": ["sophia_analytics", "shared_database"],
            "status": "operational",
            "primary_metric": {"label": "Portfolio Health", "value": "88%", "trend": "stable"},
            "pay_ready_context": "tenant_landlord_satisfaction",
        },
        {
            "id": "athena",
            "name": "Athena",
            "domain": "sophia",
            "title": "Strategic Operations",
            "assigned_mcp_servers": ["sophia_analytics", "shared_knowledge_base"],
            "status": "operational",
            "primary_metric": {"label": "Strategic KPIs", "value": "94%", "trend": "up"},
            "pay_ready_context": "strategic_initiatives",
        },
        {
            "id": "odin",
            "name": "Odin",
            "domain": "artemis",
            "title": "Technical Command & Architecture",
            "assigned_mcp_servers": ["artemis_code_analysis", "artemis_design"],
            "status": "operational",
            "primary_metric": {"label": "Code Quality", "value": "94%", "trend": "up"},
            "pay_ready_context": "technical_excellence",
        },
        {
            "id": "apollo",
            "name": "Apollo",
            "domain": "artemis",
            "title": "Performance & Monitoring",
            "assigned_mcp_servers": ["artemis_filesystem", "shared_indexing"],
            "status": "operational",
            "primary_metric": {"label": "System Health", "value": "99.8%", "trend": "stable"},
            "pay_ready_context": "performance_optimization",
        },
    ]


# ==================== API ENDPOINTS ====================


@router.get("/", response_model=MCPSystemOverview)
async def get_mcp_system_overview(user: str = Depends(get_current_user)) -> MCPSystemOverview:
    """
    Get system-wide MCP status overview

    Returns comprehensive status of all MCP servers across domains
    """
    try:
        # Get domain summaries
        domain_summaries = []
        for domain in ["artemis", "sophia", "shared"]:
            summary = await _get_domain_summary(domain)
            domain_summaries.append(summary)

        # Calculate system-wide metrics
        total_servers = sum(s.total_servers for s in domain_summaries)
        healthy_servers = sum(s.operational_servers for s in domain_summaries)

        overall_status = "operational"
        if healthy_servers < total_servers * 0.5:
            overall_status = "critical"
        elif healthy_servers < total_servers * 0.8:
            overall_status = "degraded"

        # Get system metrics
        registry_metrics = mcp_registry.get_metrics()
        system_metrics = {
            "total_active_connections": registry_metrics["active_connections"],
            "server_utilization": registry_metrics["server_utilization"],
            "partition_count": registry_metrics["partition_count"],
            "websocket_connections": len(ws_manager.connections),
            "uptime_hours": 24.0,  # Simulated
            "last_restart": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
        }

        # Get mythology agents
        mythology_agents = _get_mythology_agents_status()

        return MCPSystemOverview(
            timestamp=datetime.utcnow().isoformat(),
            overall_status=overall_status,
            total_servers=total_servers,
            healthy_servers=healthy_servers,
            domain_summaries=domain_summaries,
            system_metrics=system_metrics,
            mythology_agents=mythology_agents,
        )

    except Exception as e:
        logger.error(f"Failed to get MCP system overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system overview: {str(e)}")


@router.get("/domain/{domain}", response_model=MCPDomainSummary)
async def get_domain_status(domain: str, user: str = Depends(get_current_user)) -> MCPDomainSummary:
    """
    Get detailed status for a specific domain

    Args:
        domain: Domain to query (artemis, sophia, shared)
    """
    try:
        if domain not in ["artemis", "sophia", "shared"]:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

        return await _get_domain_summary(domain)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get domain status for {domain}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain status: {str(e)}")


@router.get("/servers", response_model=list[MCPServerHealth])
async def get_all_servers_status(
    domain: str | None = Query(None, description="Filter by domain"),
    server_type: str | None = Query(None, description="Filter by server type"),
    status: str | None = Query(None, description="Filter by status"),
    user: str = Depends(get_current_user),
) -> list[MCPServerHealth]:
    """
    Get detailed status for all MCP servers with optional filtering

    Args:
        domain: Optional domain filter
        server_type: Optional server type filter
        status: Optional status filter
    """
    try:
        server_healths = []

        # Get all registered servers
        for server_name, server_config in mcp_registry.servers.items():
            health = await _get_server_health_status(server_name, server_config)
            server_healths.append(health)

        # Apply filters
        if domain:
            server_healths = [h for h in server_healths if h.domain == domain]
        if server_type:
            server_healths = [h for h in server_healths if h.server_type == server_type]
        if status:
            server_healths = [h for h in server_healths if h.status == status]

        return server_healths

    except Exception as e:
        logger.error(f"Failed to get servers status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get servers status: {str(e)}")


@router.get("/server/{server_name}", response_model=MCPServerHealth)
async def get_server_status(
    server_name: str, user: str = Depends(get_current_user)
) -> MCPServerHealth:
    """
    Get detailed status for a specific MCP server

    Args:
        server_name: Name of the server to query
    """
    try:
        server_config = mcp_registry.servers.get(server_name)
        if not server_config:
            raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")

        return await _get_server_health_status(server_name, server_config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server status for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")


@router.get("/mythology-agents", response_model=list[dict[str, Any]])
async def get_mythology_agents_status(
    user: str = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Get status of all mythology agents and their MCP server assignments
    """
    try:
        return _get_mythology_agents_status()
    except Exception as e:
        logger.error(f"Failed to get mythology agents status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get mythology agents status: {str(e)}"
        )


@router.post("/server/{server_name}/restart")
async def restart_server(server_name: str, user: str = Depends(get_current_user)) -> dict[str, Any]:
    """
    Restart a specific MCP server (if supported)

    Args:
        server_name: Name of the server to restart
    """
    try:
        server_config = mcp_registry.servers.get(server_name)
        if not server_config:
            raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")

        # In production, this would trigger actual server restart
        # For now, just simulate the action
        logger.info(f"Restart requested for server: {server_name}")

        # Broadcast restart event
        await ws_manager.broadcast(
            "mcp_server_events",
            {
                "type": "server_restart",
                "server_name": server_name,
                "initiated_by": user,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return {
            "success": True,
            "message": f"Restart initiated for {server_name}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart server {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {str(e)}")


# ==================== WEBSOCKET ENDPOINT ====================


@router.websocket("/ws/{client_id}")
async def websocket_mcp_status(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time MCP status updates

    Clients can subscribe to:
    - mcp_system_overview: System-wide status updates
    - mcp_domain_{domain}: Domain-specific updates
    - mcp_server_{server_name}: Server-specific updates
    - mcp_mythology_agents: Mythology agent status updates
    """
    session_id = f"mcp_status_{client_id}"

    try:
        await ws_manager.websocket_endpoint(websocket, client_id, session_id)

        # Auto-subscribe to system overview
        await ws_manager.subscribe(client_id, "mcp_system_overview")

        # Send initial status
        overview = await get_mcp_system_overview(user="system")
        await ws_manager.send_to_client(
            client_id,
            {
                "type": "mcp_status_update",
                "data": overview.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Keep connection alive and periodically send updates
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds

            try:
                # Get fresh overview
                overview = await get_mcp_system_overview(user="system")

                # Broadcast to all subscribers
                await ws_manager.broadcast(
                    "mcp_system_overview",
                    {
                        "type": "mcp_status_update",
                        "data": overview.dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            except Exception as e:
                logger.error(f"Failed to send periodic MCP status update: {e}")

    except WebSocketDisconnect:
        logger.info(f"MCP status WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"MCP status WebSocket error for {client_id}: {e}")
