"""
FastAPI endpoints for Resilient WebSocket Management
Provides HTTP and WebSocket endpoints for MCP communication
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel

from app.core.resilient_websocket import (
    ReconnectionConfig,
    ResilientWebSocketClient,
    mcp_ws_manager,
)

router = APIRouter(prefix="/ws", tags=["websocket", "mcp"])
logger = logging.getLogger(__name__)


# Request/Response Models
class MCPMessageRequest(BaseModel):
    server: str
    method: str
    params: Optional[dict[str, Any]] = None
    expect_response: bool = True
    timeout: float = 30.0


class ReconnectionConfigModel(BaseModel):
    max_attempts: int = 10
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: float = 0.1
    circuit_breaker_timeout: float = 300.0


class MCPServerConfig(BaseModel):
    name: str
    url: str
    reconnect_config: Optional[ReconnectionConfigModel] = None


async def get_ws_manager():
    """Dependency to get initialized WebSocket manager"""
    if not mcp_ws_manager.mcp_clients:
        await mcp_ws_manager.initialize()
    return mcp_ws_manager


@router.websocket("/connect/{client_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, session_id: str, ws_manager=Depends(get_ws_manager)
):
    """
    Main WebSocket endpoint for client connections
    Supports real-time communication with MCP servers
    """
    await ws_manager.websocket_endpoint(websocket, client_id, session_id)


@router.post("/mcp/send")
async def send_mcp_message(request: MCPMessageRequest, ws_manager=Depends(get_ws_manager)):
    """
    Send message to MCP server and optionally wait for response
    """
    try:
        response = await ws_manager.send_to_mcp_server(
            server=request.server,
            method=request.method,
            params=request.params,
            expect_response=request.expect_response,
        )

        if response is None and request.expect_response:
            raise HTTPException(
                status_code=503, detail=f"No response from MCP server '{request.server}'"
            )

        return {
            "success": True,
            "response": response,
            "server": request.server,
            "method": request.method,
        }

    except Exception as e:
        logger.error(f"Failed to send MCP message: {e}")
        raise HTTPException(status_code=500, detail=f"MCP message failed: {str(e)}")


@router.get("/mcp/health")
async def get_mcp_health(ws_manager=Depends(get_ws_manager)):
    """
    Get health status of all MCP server connections
    """
    try:
        health_status = await ws_manager.get_mcp_health()
        return health_status

    except Exception as e:
        logger.error(f"Failed to get MCP health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/mcp/metrics")
async def get_mcp_metrics(ws_manager=Depends(get_ws_manager)):
    """
    Get detailed metrics for all MCP connections
    """
    try:
        metrics = {}

        for server_name, client in ws_manager.mcp_clients.items():
            metrics[server_name] = client.get_metrics()

        # Add WebSocket manager metrics
        metrics["websocket_manager"] = ws_manager.get_metrics()

        return {
            "mcp_servers": metrics,
            "summary": {
                "total_servers": len(ws_manager.mcp_clients),
                "connected_servers": sum(
                    1
                    for client in ws_manager.mcp_clients.values()
                    if client.state.value == "connected"
                ),
                "active_websocket_connections": ws_manager.metrics["active_connections"],
            },
        }

    except Exception as e:
        logger.error(f"Failed to get MCP metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.post("/mcp/server/add")
async def add_mcp_server(config: MCPServerConfig, ws_manager=Depends(get_ws_manager)):
    """
    Add new MCP server connection
    """
    try:
        if config.name in ws_manager.mcp_clients:
            raise HTTPException(
                status_code=409, detail=f"MCP server '{config.name}' already exists"
            )

        # Build reconnection config
        reconnect_config = None
        if config.reconnect_config:
            reconnect_config = ReconnectionConfig(**config.reconnect_config.dict())

        # Create new client
        client = ResilientWebSocketClient(
            url=config.url,
            reconnect_config=reconnect_config,
            message_handlers={
                "memory_update": ws_manager._handle_memory_update,
                "tool_result": ws_manager._handle_tool_result,
                "status_update": ws_manager._handle_status_update,
            },
        )

        # Set up callbacks
        client.on_connected = lambda: ws_manager._on_mcp_connected(config.name)
        client.on_disconnected = lambda: ws_manager._on_mcp_disconnected(config.name)
        client.on_error = lambda e: ws_manager._on_mcp_error(config.name, e)

        # Add to manager
        ws_manager.mcp_clients[config.name] = client
        ws_manager.mcp_servers[config.name] = config.url

        # Attempt initial connection
        connected = await client.connect()

        return {
            "success": True,
            "server": config.name,
            "url": config.url,
            "connected": connected,
            "message": f"MCP server '{config.name}' added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add server: {str(e)}")


@router.delete("/mcp/server/{server_name}")
async def remove_mcp_server(server_name: str, ws_manager=Depends(get_ws_manager)):
    """
    Remove MCP server connection
    """
    try:
        if server_name not in ws_manager.mcp_clients:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")

        # Disconnect and remove client
        client = ws_manager.mcp_clients[server_name]
        await client.disconnect(reason="Server removed")

        del ws_manager.mcp_clients[server_name]
        ws_manager.mcp_servers.pop(server_name, None)

        return {"success": True, "message": f"MCP server '{server_name}' removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove server: {str(e)}")


@router.post("/mcp/server/{server_name}/reconnect")
async def reconnect_mcp_server(server_name: str, ws_manager=Depends(get_ws_manager)):
    """
    Force reconnection to MCP server
    """
    try:
        if server_name not in ws_manager.mcp_clients:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")

        client = ws_manager.mcp_clients[server_name]

        # Disconnect if connected
        if client.state.value == "connected":
            await client.disconnect(reason="Manual reconnection")

        # Reset reconnection state
        client.reconnect_attempts = 0
        client.circuit_breaker_open = False

        # Attempt reconnection
        connected = await client.connect()

        return {
            "success": True,
            "server": server_name,
            "connected": connected,
            "message": f"Reconnection attempt for '{server_name}' completed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reconnect MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Reconnection failed: {str(e)}")


@router.get("/mcp/servers")
async def list_mcp_servers(ws_manager=Depends(get_ws_manager)):
    """
    List all configured MCP servers
    """
    servers = {}

    for server_name, client in ws_manager.mcp_clients.items():
        servers[server_name] = {
            "name": server_name,
            "url": client.url,
            "state": client.state.value,
            "connected": client.state.value == "connected",
            "last_connection": (
                client.last_connection_time.isoformat() if client.last_connection_time else None
            ),
            "reconnect_attempts": client.reconnect_attempts,
            "circuit_breaker_open": client.circuit_breaker_open,
        }

    return {
        "servers": servers,
        "total": len(servers),
        "connected": sum(1 for s in servers.values() if s["connected"]),
    }


@router.post("/mcp/broadcast")
async def broadcast_to_websocket_clients(
    channel: str, message: dict[str, Any], ws_manager=Depends(get_ws_manager)
):
    """
    Broadcast message to WebSocket clients on specific channel
    """
    try:
        await ws_manager.broadcast(channel, message)

        subscriber_count = len(ws_manager.channels.get(channel, set()))

        return {
            "success": True,
            "channel": channel,
            "subscribers": subscriber_count,
            "message": "Broadcast sent successfully",
        }

    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@router.get("/channels")
async def list_websocket_channels(ws_manager=Depends(get_ws_manager)):
    """
    List all active WebSocket channels and their subscribers
    """
    channels = {}

    for channel_name, subscribers in ws_manager.channels.items():
        channels[channel_name] = {
            "name": channel_name,
            "subscribers": len(subscribers),
            "subscriber_ids": list(subscribers),
        }

    return {
        "channels": channels,
        "total_channels": len(channels),
        "total_subscribers": sum(len(subs) for subs in ws_manager.channels.values()),
    }


@router.get("/status")
async def get_websocket_status(ws_manager=Depends(get_ws_manager)):
    """
    Get overall WebSocket system status
    """
    mcp_health = await ws_manager.get_mcp_health()
    ws_metrics = ws_manager.get_metrics()

    return {
        "websocket_manager": {
            "active_connections": ws_metrics["active_connections"],
            "total_connections": ws_metrics["total_connections"],
            "messages_sent": ws_metrics["messages_sent"],
            "messages_failed": ws_metrics["messages_failed"],
            "channels": len(ws_manager.channels),
        },
        "mcp_servers": {
            "total": len(ws_manager.mcp_clients),
            "healthy": sum(1 for status in mcp_health["servers"].values() if status["healthy"]),
            "overall_healthy": mcp_health["overall_healthy"],
        },
        "system_healthy": mcp_health["overall_healthy"] and ws_metrics["active_connections"] >= 0,
    }


# Health check endpoint for load balancers
@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    try:
        if not mcp_ws_manager.mcp_clients:
            await mcp_ws_manager.initialize()

        return {
            "status": "healthy",
            "service": "resilient-websocket",
            "mcp_servers": len(mcp_ws_manager.mcp_clients),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
