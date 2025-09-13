"""
AI Agent Gateway API
Provides natural language interface and observability for AI agents
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import json
import asyncio
from collections import defaultdict

from app.core.service_registry import ServiceRegistry
from app.core.service_orchestrator import get_orchestrator
from app.core.unified_config import get_config

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Agent context storage (in production, use Redis)
agent_contexts = defaultdict(dict)
agent_subscriptions = {}

class AgentQuery(BaseModel):
    """Natural language query from an AI agent"""
    query: str
    agent_id: str = Field(default="default-agent")
    context: Dict[str, Any] = Field(default_factory=dict)
    include_examples: bool = True

class AgentAction(BaseModel):
    """Action request from an agent"""
    action: str
    target: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str = Field(default="default-agent")

class AgentResponse(BaseModel):
    """Structured response for AI agents"""
    success: bool
    answer: str
    data: Optional[Dict[str, Any]] = None
    actions_available: List[Dict[str, Any]] = Field(default_factory=list)
    relevant_endpoints: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    context_id: Optional[str] = None

@router.post("/query", response_model=AgentResponse)
async def agent_query(query: AgentQuery):
    """
    Natural language interface for agents to discover and execute capabilities
    
    Examples:
    - "What services are currently running?"
    - "Show me any unhealthy services"
    - "How do I restart the Redis service?"
    - "What's the system status?"
    """
    orchestrator = get_orchestrator()
    q = query.query.lower()
    
    # Parse intent from query
    if any(word in q for word in ["status", "running", "health", "healthy"]):
        # Get service status
        status = orchestrator.get_status_report()
        
        running_services = []
        stopped_services = []
        for name, info in status["services"].items():
            if info["state"] in ["running", "external"]:
                running_services.append(name)
            else:
                stopped_services.append(name)
        
        answer = f"System has {len(running_services)} running services and {len(stopped_services)} stopped services."
        
        if "unhealthy" in q or "failed" in q or "problem" in q:
            # Focus on problems
            if stopped_services:
                answer = f"The following services are not running: {', '.join(stopped_services)}"
            else:
                answer = "All services are running normally."
        
        return AgentResponse(
            success=True,
            answer=answer,
            data={
                "running": running_services,
                "stopped": stopped_services,
                "total": len(status["services"])
            },
            actions_available=[
                {
                    "action": "start_service",
                    "description": "Start a stopped service",
                    "endpoint": "/api/services/{service_name}/start",
                    "method": "POST"
                },
                {
                    "action": "get_details",
                    "description": "Get detailed status",
                    "endpoint": "/api/services/status",
                    "method": "GET"
                }
            ],
            relevant_endpoints=[
                "/api/services/status",
                "/api/services/health",
                "/api/services/ports"
            ],
            examples=[
                "curl http://localhost:8000/api/services/status",
                "curl -X POST http://localhost:8000/api/services/redis/start"
            ] if query.include_examples else []
        )
    
    elif any(word in q for word in ["start", "stop", "restart"]):
        # Service management query
        action = "start" if "start" in q else "stop" if "stop" in q else "restart"
        
        # Try to identify service name
        services = list(ServiceRegistry.SERVICES.keys())
        target_service = None
        for service in services:
            if service in q:
                target_service = service
                break
        
        if target_service:
            answer = f"To {action} {target_service}, use: POST /api/services/{target_service}/{action}"
        else:
            answer = f"To {action} a service, use: POST /api/services/{{service_name}}/{action}"
        
        return AgentResponse(
            success=True,
            answer=answer,
            actions_available=[
                {
                    "action": f"{action}_service",
                    "endpoint": f"/api/services/{{service_name}}/{action}",
                    "method": "POST",
                    "available_services": services
                }
            ],
            relevant_endpoints=[
                f"/api/services/{{service_name}}/{action}",
                "/api/services/status"
            ],
            examples=[
                f"curl -X POST http://localhost:8000/api/services/redis/{action}",
                f"curl -X POST http://localhost:8000/api/services/postgres/{action}"
            ] if query.include_examples else []
        )
    
    elif "port" in q:
        # Port information
        from app.core.service_registry import ServiceRegistry
        ports = ServiceRegistry.get_all_ports()
        
        answer = f"System uses {len(ports)} service ports."
        
        return AgentResponse(
            success=True,
            answer=answer,
            data={"ports": ports},
            relevant_endpoints=["/api/services/ports"],
            examples=["curl http://localhost:8000/api/services/ports"]
        )
    
    elif "help" in q or "how" in q or "what" in q:
        # Help query
        answer = "I can help you manage services, check health, view ports, and monitor the system."
        
        return AgentResponse(
            success=True,
            answer=answer,
            actions_available=[
                {
                    "category": "Service Management",
                    "actions": [
                        {"name": "Start Service", "endpoint": "/api/services/{name}/start"},
                        {"name": "Stop Service", "endpoint": "/api/services/{name}/stop"},
                        {"name": "Get Status", "endpoint": "/api/services/status"}
                    ]
                },
                {
                    "category": "Monitoring",
                    "actions": [
                        {"name": "Health Check", "endpoint": "/api/services/health"},
                        {"name": "View Ports", "endpoint": "/api/services/ports"},
                        {"name": "Dependencies", "endpoint": "/api/services/dependencies"}
                    ]
                }
            ],
            relevant_endpoints=[
                "/api/agent/capabilities",
                "/api/agent/docs"
            ]
        )
    
    else:
        # Unknown query
        return AgentResponse(
            success=False,
            answer="I don't understand that query. Try asking about service status, health, ports, or how to start/stop services.",
            actions_available=[
                {
                    "action": "get_help",
                    "endpoint": "/api/agent/capabilities",
                    "description": "Get list of all capabilities"
                }
            ]
        )

@router.get("/capabilities")
async def get_capabilities():
    """
    Returns all available capabilities in agent-friendly format
    """
    return {
        "system": "Sophia Intel AI",
        "version": "1.0.0",
        "capabilities": {
            "service_management": {
                "description": "Start, stop, restart, and monitor services",
                "queries": [
                    "What services are running?",
                    "Start the Redis service",
                    "Show unhealthy services",
                    "Restart all MCP services"
                ],
                "endpoints": [
                    {
                        "path": "/api/services/status",
                        "method": "GET",
                        "description": "Get status of all services"
                    },
                    {
                        "path": "/api/services/{name}/start",
                        "method": "POST",
                        "description": "Start a specific service"
                    },
                    {
                        "path": "/api/services/{name}/stop",
                        "method": "POST",
                        "description": "Stop a specific service"
                    }
                ]
            },
            "health_monitoring": {
                "description": "Monitor system and service health",
                "queries": [
                    "Is the system healthy?",
                    "Check database connections",
                    "Show performance metrics"
                ],
                "endpoints": [
                    {
                        "path": "/api/services/health",
                        "method": "GET",
                        "description": "Aggregated health status"
                    },
                    {
                        "path": "/api/health/detailed",
                        "method": "GET",
                        "description": "Detailed health report"
                    }
                ]
            },
            "configuration": {
                "description": "View and manage configuration",
                "queries": [
                    "What ports are configured?",
                    "Show service dependencies",
                    "List environment variables"
                ],
                "endpoints": [
                    {
                        "path": "/api/services/ports",
                        "method": "GET",
                        "description": "Get all port mappings"
                    },
                    {
                        "path": "/api/services/dependencies",
                        "method": "GET",
                        "description": "Service dependency graph"
                    }
                ]
            }
        },
        "integration_points": {
            "mcp_tools": "MCP server available at port 8081-8084",
            "websocket": "Real-time events at /ws",
            "rest_api": "Full REST API at /api/*"
        }
    }

@router.get("/context/{agent_id}")
async def get_agent_context(agent_id: str):
    """
    Retrieve preserved context for a specific agent
    """
    context = agent_contexts.get(agent_id, {})
    
    return {
        "agent_id": agent_id,
        "context": context,
        "last_seen": context.get("last_seen", "never"),
        "action_count": len(context.get("recent_actions", [])),
        "observations": context.get("observations", [])
    }

@router.post("/context/{agent_id}")
async def update_agent_context(agent_id: str, context: Dict[str, Any]):
    """
    Update context for an agent
    """
    if agent_id not in agent_contexts:
        agent_contexts[agent_id] = {
            "created_at": datetime.now().isoformat(),
            "recent_actions": [],
            "observations": []
        }
    
    agent_contexts[agent_id].update(context)
    agent_contexts[agent_id]["last_seen"] = datetime.now().isoformat()
    
    return {"success": True, "agent_id": agent_id}

@router.post("/action", response_model=AgentResponse)
async def execute_agent_action(action: AgentAction):
    """
    Execute a specific action on behalf of an agent
    """
    orchestrator = get_orchestrator()
    
    try:
        if action.action == "start":
            success = await orchestrator.start_service(action.target)
            answer = f"Service {action.target} {'started successfully' if success else 'failed to start'}"
            
        elif action.action == "stop":
            await orchestrator.stop_service(action.target)
            success = True
            answer = f"Service {action.target} stopped"
            
        elif action.action == "restart":
            await orchestrator.stop_service(action.target)
            success = await orchestrator.start_service(action.target)
            answer = f"Service {action.target} restarted"
            
        else:
            success = False
            answer = f"Unknown action: {action.action}"
        
        # Update agent context
        if action.agent_id not in agent_contexts:
            agent_contexts[action.agent_id] = {"recent_actions": []}
        
        agent_contexts[action.agent_id]["recent_actions"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action.action,
            "target": action.target,
            "success": success
        })
        
        return AgentResponse(
            success=success,
            answer=answer,
            data={"service": action.target, "action": action.action}
        )
        
    except Exception as e:
        return AgentResponse(
            success=False,
            answer=f"Action failed: {str(e)}"
        )

@router.get("/docs")
async def get_agent_documentation():
    """
    Returns documentation specifically formatted for AI agents
    """
    return {
        "quick_start": {
            "description": "How to use this API as an AI agent",
            "steps": [
                "1. Start with /api/agent/query to ask questions in natural language",
                "2. Use the returned endpoints to perform specific actions",
                "3. Monitor system state via /api/services/status",
                "4. Subscribe to events for real-time updates"
            ]
        },
        "common_workflows": {
            "health_check": {
                "description": "Check and maintain system health",
                "steps": [
                    "GET /api/services/health - Check overall health",
                    "GET /api/services/status - Get detailed status",
                    "POST /api/services/{name}/restart - Restart unhealthy services"
                ]
            },
            "service_management": {
                "description": "Manage service lifecycle",
                "steps": [
                    "GET /api/services/dependencies - Check dependencies",
                    "POST /api/services/{name}/start - Start service",
                    "GET /api/services/status/{name} - Verify running"
                ]
            }
        },
        "best_practices": [
            "Always check dependencies before starting services",
            "Monitor health after making changes",
            "Use context preservation for multi-step operations",
            "Subscribe to events for services you're managing"
        ],
        "rate_limits": {
            "queries": "100 per minute",
            "actions": "20 per minute",
            "health_checks": "unlimited"
        }
    }

@router.websocket("/events")
async def agent_event_stream(websocket: WebSocket, agent_id: str = "default"):
    """
    WebSocket endpoint for real-time event streaming to agents
    """
    await websocket.accept()
    agent_subscriptions[agent_id] = websocket
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and send events
        while True:
            # In production, this would receive events from the event bus
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        del agent_subscriptions[agent_id]
    except Exception as e:
        print(f"WebSocket error for agent {agent_id}: {e}")
        if agent_id in agent_subscriptions:
            del agent_subscriptions[agent_id]