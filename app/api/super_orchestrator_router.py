"""
SuperOrchestrator API Router with Personality
Provides endpoints for the personality-enhanced orchestrator
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.super_orchestrator import get_orchestrator

router = APIRouter(tags=["super-orchestrator"])


class NaturalLanguageCommand(BaseModel):
    """Natural language command request"""
    command: str
    context: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """Chat message for personality-enhanced interaction"""
    message: str
    include_suggestions: bool = True


class SystemCommand(BaseModel):
    """System command request"""
    command: str
    params: Optional[Dict[str, Any]] = {}


class SwarmDeployment(BaseModel):
    """Micro-swarm deployment request"""
    task: str
    agent_count: int = 3
    capabilities: List[str] = ["analyze", "execute", "report"]
    priority: str = "normal"


@router.post("/chat")
async def chat_with_personality(request: ChatMessage):
    """
    Chat with the personality-enhanced orchestrator.
    Includes pushback, suggestions, and natural conversation.
    """
    orchestrator = get_orchestrator()
    
    response = await orchestrator.process_request({
        "type": "chat",
        "message": request.message
    })
    
    # Add personality flair to the response
    if request.include_suggestions:
        current_context = {
            "error_count": sum(1 for s in orchestrator.registry.systems.values() 
                             if s.status.value == "error"),
            "cost_today": orchestrator._calculate_cost(),
            "idle_systems": sum(1 for s in orchestrator.registry.systems.values() 
                               if s.status.value == "idle")
        }
        suggestions = orchestrator.suggestions.get_contextual_suggestions(current_context)
        response["suggestions"] = suggestions
    
    return response


@router.post("/command/natural")
async def process_natural_language(request: NaturalLanguageCommand):
    """
    Process natural language commands.
    Examples:
    - "spawn 5 agents to analyze the logs"
    - "show me what's running"
    - "optimize the system for cost"
    - "holy shit what's causing all these errors?"
    """
    orchestrator = get_orchestrator()
    
    # Process with personality and NL controller
    result = await orchestrator.process_natural_language(request.command)
    
    # Track command for learning
    orchestrator.suggestions.track_command(
        request.command, 
        result.get("success", True)
    )
    
    return result


@router.post("/command/system")
async def execute_system_command(request: SystemCommand):
    """
    Execute system commands with personality responses.
    Commands: deploy, scale, optimize, analyze, heal
    """
    orchestrator = get_orchestrator()
    
    response = await orchestrator.process_request({
        "type": "command",
        "command": request.command,
        "params": request.params
    })
    
    return response


@router.post("/swarm/deploy")
async def deploy_micro_swarm(request: SwarmDeployment):
    """
    Deploy a micro-swarm for a specific task.
    Returns personality-enhanced status updates.
    """
    orchestrator = get_orchestrator()
    
    # Check if this is risky
    risk_analysis = orchestrator.personality.analyze_command_risk(
        f"spawn {request.agent_count} agents"
    )
    
    if risk_analysis["should_pushback"] and request.agent_count > 20:
        alternatives = orchestrator.personality.suggest_alternatives(
            f"spawn {request.agent_count}"
        )
        return {
            "status": "needs_confirmation",
            "message": orchestrator.personality.generate_response(
                "processing", 
                command=f"spawn {request.agent_count}"
            ),
            "alternatives": alternatives
        }
    
    # Deploy the swarm
    swarm_id = f"swarm_{request.task.replace(' ', '_')}_{datetime.now().timestamp()}"
    
    # Register swarm with registry
    from app.core.orchestrator_enhancements import RegisteredSystem, SystemStatus, SystemType
    
    swarm = RegisteredSystem(
        id=swarm_id,
        name=f"Micro-swarm: {request.task}",
        type=SystemType.MICRO_SWARM,
        status=SystemStatus.ACTIVE,
        capabilities=request.capabilities,
        metadata={"agent_count": request.agent_count, "task": request.task}
    )
    
    await orchestrator.registry.register(swarm)
    
    # Generate personality response
    success_msg = orchestrator.personality.generate_response(
        "success",
        data={"metrics": f"Micro-swarm deployed: {request.agent_count} agents"}
    )
    
    return {
        "swarm_id": swarm_id,
        "status": "deployed",
        "message": success_msg,
        "agents": request.agent_count,
        "task": request.task
    }


@router.get("/status")
async def get_system_status():
    """
    Get complete system status with personality commentary.
    """
    orchestrator = get_orchestrator()
    
    # Get all systems
    systems = list(orchestrator.registry.systems.values())
    
    # Get personality-formatted status
    status_message = orchestrator.personality.format_system_status([
        {"status": s.status.value, "type": s.type.value} 
        for s in systems
    ])
    
    # Get health report
    health = orchestrator.registry.get_health_report()
    
    # Get personality analysis
    personality_analysis = orchestrator.personality.generate_response(
        "analysis",
        data={
            "health_score": health["health_score"],
            "active_systems": len(orchestrator.registry.get_active_systems()),
            "cost": orchestrator._calculate_cost()
        }
    )
    
    return {
        "status": status_message,
        "health": health,
        "analysis": personality_analysis,
        "systems": {
            "total": len(systems),
            "by_type": {t.value: len(orchestrator.registry.get_by_type(t)) 
                       for t in SystemType},
            "by_status": {s.value: len([sys for sys in systems if sys.status == s]) 
                         for s in SystemStatus}
        }
    }


@router.get("/suggestions")
async def get_smart_suggestions():
    """
    Get AI-powered suggestions based on current context.
    """
    orchestrator = get_orchestrator()
    
    current_context = {
        "error_count": sum(1 for s in orchestrator.registry.systems.values() 
                         if s.status.value == "error"),
        "cost_today": orchestrator._calculate_cost(),
        "idle_systems": sum(1 for s in orchestrator.registry.systems.values() 
                           if s.status.value == "idle"),
        "active_systems": len(orchestrator.registry.get_active_systems())
    }
    
    suggestions = orchestrator.suggestions.get_contextual_suggestions(current_context)
    
    return {
        "suggestions": suggestions,
        "context": current_context,
        "personality_comment": "Here's what I think you should do next:"
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket connection for real-time updates with personality.
    """
    orchestrator = get_orchestrator()
    await orchestrator.connect_websocket(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process based on message type
            if data.get("type") == "chat":
                response = await orchestrator.process_request({
                    "type": "chat",
                    "message": data.get("message")
                })
            elif data.get("type") == "command":
                response = await orchestrator.process_natural_language(
                    data.get("command")
                )
            else:
                response = {"error": "Unknown message type"}
            
            # Send response
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        await orchestrator.disconnect_websocket(websocket)


@router.get("/personality/test")
async def test_personality():
    """
    Test the personality system with various scenarios.
    """
    orchestrator = get_orchestrator()
    
    tests = {
        "greeting": orchestrator.personality.generate_response("greeting"),
        "success": orchestrator.personality.generate_response(
            "success", 
            data={"metrics": "Everything running smoothly"}
        ),
        "error": orchestrator.personality.generate_response(
            "error",
            data={"error": "Database connection failed"}
        ),
        "risky_command": orchestrator.personality.generate_response(
            "processing",
            command="delete all systems"
        ),
        "thinking": orchestrator.personality.generate_response("thinking")
    }
    
    return {
        "personality_test": tests,
        "message": "Hell yeah! Personality system is working perfectly! 🔥"
    }


# Import datetime for swarm deployment
from datetime import datetime
# Import SystemType and SystemStatus for the status endpoint
from app.core.orchestrator_enhancements import SystemType, SystemStatus