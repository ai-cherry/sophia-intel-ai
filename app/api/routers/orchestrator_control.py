"""
SuperOrchestrator Control API
Provides complete visibility and control over all AI systems
"""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.ai_logger import logger
from app.core.super_orchestrator import get_orchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.websocket("/ws")
async def orchestrator_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time orchestrator control.
    This is the main interface for the UI dashboard.
    """
    await websocket.accept()
    orchestrator = get_orchestrator()

    # Add connection to orchestrator
    orchestrator.connections.append(websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to SuperOrchestrator",
            "timestamp": datetime.now().isoformat()
        })

        # Start monitoring task for this connection
        monitor_task = asyncio.create_task(
            send_monitoring_updates(websocket, orchestrator)
        )

        # Handle incoming commands
        while True:
            data = await websocket.receive_json()

            try:
                # Process command through orchestrator
                result = await orchestrator.handle_ui_command(websocket, data)

                # Send response
                await websocket.send_json({
                    "type": "command_response",
                    "command": data,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error("Error processing command", {"error": str(e)})
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "command": data
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error", {"error": str(e)})
    finally:
        # Clean up
        if websocket in orchestrator.connections:
            orchestrator.connections.remove(websocket)
        if 'monitor_task' in locals():
            monitor_task.cancel()


async def send_monitoring_updates(websocket: WebSocket, orchestrator):
    """Send periodic monitoring updates to the WebSocket client"""
    try:
        while True:
            # Get current system state
            overview = await orchestrator.get_system_overview()

            # Send update
            await websocket.send_json({
                "type": "system_state",
                "overview": overview,
                "timestamp": datetime.now().isoformat()
            })

            # Also send metrics if available
            if orchestrator.monitor:
                metrics = await orchestrator.monitor.collect_metrics()
                alerts = orchestrator.monitor.check_alerts(metrics)

                await websocket.send_json({
                    "type": "metrics_update",
                    "metrics": metrics,
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(2)  # Update every 2 seconds

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Monitoring error", {"error": str(e)})


@router.post("/command")
async def execute_command(command: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a command through the orchestrator.
    Supports natural language and structured commands.
    """
    orchestrator = get_orchestrator()

    try:
        # Process based on command type
        if command.get("type") == "natural_language":
            result = await orchestrator.process_natural_language(
                command.get("text", ""),
                command.get("context", {})
            )
        else:
            # Process as structured command
            result = await orchestrator.process_request(command)

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error("Command execution failed", {
            "command": command,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spawn-swarm/{swarm_type}")
async def spawn_micro_swarm(swarm_type: str, task: dict[str, Any] = None) -> dict[str, Any]:
    """
    Spawn a micro-swarm of the specified type.
    Optionally provide a task to execute immediately.
    """
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.spawn_micro_swarm(swarm_type, task)

        if result.get("success"):
            logger.info("Spawned micro-swarm", {
                "type": swarm_type,
                "swarm_id": result.get("swarm_id")
            })

        return result

    except Exception as e:
        logger.error("Failed to spawn swarm", {
            "type": swarm_type,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_system_overview() -> dict[str, Any]:
    """
    Get complete overview of all AI systems.
    Provides visibility into everything running.
    """
    orchestrator = get_orchestrator()

    try:
        overview = await orchestrator.get_system_overview()
        return overview

    except Exception as e:
        logger.error("Failed to get overview", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/systems")
async def list_all_systems() -> list[dict[str, Any]]:
    """
    List all registered AI systems with their status.
    """
    orchestrator = get_orchestrator()

    try:
        systems = []
        for system in orchestrator.registry.systems.values():
            systems.append({
                "id": system.id,
                "name": system.name,
                "type": system.type.value,
                "status": system.status.value,
                "capabilities": system.capabilities,
                "last_activity": system.last_activity.isoformat(),
                "error_count": system.error_count,
                "metrics": system.metrics
            })

        return systems

    except Exception as e:
        logger.error("Failed to list systems", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/systems/{system_id}")
async def get_system_details(system_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific system.
    """
    orchestrator = get_orchestrator()

    if system_id not in orchestrator.registry.systems:
        raise HTTPException(status_code=404, detail="System not found")

    system = orchestrator.registry.systems[system_id]

    return {
        "id": system.id,
        "name": system.name,
        "type": system.type.value,
        "status": system.status.value,
        "capabilities": system.capabilities,
        "config": system.config,
        "metrics": system.metrics,
        "connections": list(system.connections),
        "last_activity": system.last_activity.isoformat(),
        "error_count": system.error_count,
        "metadata": system.metadata
    }


@router.post("/systems/{system_id}/execute")
async def execute_on_system(system_id: str, task: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a task on a specific system.
    """
    orchestrator = get_orchestrator()

    if system_id not in orchestrator.registry.systems:
        raise HTTPException(status_code=404, detail="System not found")

    try:
        # Check if it's a micro-swarm
        if system_id in orchestrator.micro_swarms:
            result = await orchestrator.execute_micro_swarm_task(system_id, task)
        else:
            # Generic execution
            result = await orchestrator.process_request({
                "type": "execute",
                "system_id": system_id,
                "task": task
            })

        return result

    except Exception as e:
        logger.error("Execution failed", {
            "system_id": system_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def list_all_capabilities() -> list[str]:
    """
    List all unique capabilities across all systems.
    """
    orchestrator = get_orchestrator()
    return orchestrator._get_all_capabilities()


@router.get("/health")
async def get_health_report() -> dict[str, Any]:
    """
    Get comprehensive health report of all systems.
    """
    orchestrator = get_orchestrator()
    return orchestrator.registry.get_health_report()


@router.post("/natural-language")
async def process_natural_language(request: dict[str, str]) -> dict[str, Any]:
    """
    Process a natural language command.
    This is the main NL interface for the UI.
    """
    orchestrator = get_orchestrator()

    command = request.get("command", "")
    context = request.get("context", {})

    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    try:
        result = await orchestrator.process_natural_language(command, context)

        logger.info("Processed NL command", {
            "command": command,
            "success": result.get("success", False)
        })

        return result

    except Exception as e:
        logger.error("NL processing failed", {
            "command": command,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
