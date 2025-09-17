"""MCP receivers for workbench-ui integrations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.agno_workspaces import agno_workspace_service
from app.services.flowwise_gateway import flowwise_gateway

if TYPE_CHECKING:  # pragma: no cover - circular type checking only
    from app.mcp.server_template import SophiaMCPServer

WORKBENCH_CHANNELS = ("flowwise", "agno")


def register_workbench_receivers(server: "SophiaMCPServer") -> None:
    """Register workbench tools on the unified MCP server."""

    @server.mcp_tool("workbench.flowwise.dispatch")
    async def dispatch_flowwise(factory_id: str, agent_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = await flowwise_gateway.dispatch_agent(factory_id, agent_id, payload)
        return {
            "factory_id": factory_id,
            "agent_id": agent_id,
            "status": "submitted",
            "result": result,
        }

    @server.mcp_tool("workbench.agno.dispatch")
    async def dispatch_agno(workspace_id: str, agent_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = await agno_workspace_service.trigger_agent(workspace_id, agent_id, payload)
        return {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "status": "submitted",
            "result": result,
        }
