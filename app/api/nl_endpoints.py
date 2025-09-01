"""
Natural Language API Endpoints
FastAPI endpoints for NL processing and workflow integration
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import requests

# Import our NL components
from app.nl_interface.quicknlp import QuickNLP, CommandIntent, ParsedCommand
from app.nl_interface.intents import get_intent_pattern, format_help_text
from app.agents.simple_orchestrator import SimpleAgentOrchestrator, AgentRole

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/nl",
    tags=["natural-language"],
    responses={404: {"description": "Not found"}},
)

# Initialize components
nlp_processor = QuickNLP()
agent_orchestrator = SimpleAgentOrchestrator()


# ============================================
# Request/Response Models
# ============================================

class NLProcessRequest(BaseModel):
    """Request model for NL processing"""
    text: str = Field(..., description="Natural language command text")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Optional context for processing")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")


class NLProcessResponse(BaseModel):
    """Response model for NL processing"""
    success: bool
    intent: str
    entities: Dict[str, Any]
    confidence: float
    workflow_trigger: Optional[str]
    session_id: str
    response_text: str
    timestamp: str


class WorkflowTriggerRequest(BaseModel):
    """Request model for workflow trigger"""
    workflow_id: str = Field(..., description="Workflow ID to trigger")
    payload: Dict[str, Any] = Field(default={}, description="Payload for workflow")
    async_execution: bool = Field(default=False, description="Execute asynchronously")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""
    workflow_id: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class IntentInfo(BaseModel):
    """Model for intent information"""
    name: str
    description: str
    examples: List[str]
    entities: List[str]


# ============================================
# Core Endpoints
# ============================================

@router.post("/process", response_model=NLProcessResponse)
async def process_natural_language(
    request: NLProcessRequest,
    background_tasks: BackgroundTasks
) -> NLProcessResponse:
    """
    Process natural language command and execute corresponding workflow
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process the natural language text
        parsed_command: ParsedCommand = nlp_processor.process(request.text)
        
        # Get intent pattern for response formatting
        intent_pattern = get_intent_pattern(parsed_command.intent.value)
        
        # Prepare response text
        if intent_pattern:
            response_text = intent_pattern.response_template.format(
                **parsed_command.entities,
                **{"status_details": "Processing...", "execution_result": "Started"}
            )
        else:
            response_text = f"Processing command: {parsed_command.intent.value}"
        
        # If workflow trigger is available, execute it
        if parsed_command.workflow_trigger:
            # Execute workflow in background
            background_tasks.add_task(
                trigger_workflow_async,
                parsed_command.workflow_trigger,
                {
                    "command": request.text,
                    "intent": parsed_command.intent.value,
                    "entities": parsed_command.entities,
                    "session_id": session_id
                }
            )
        
        # Handle special intents
        if parsed_command.intent == CommandIntent.HELP:
            response_text = format_help_text()
        elif parsed_command.intent == CommandIntent.RUN_AGENT:
            # Trigger agent execution
            agent_name = parsed_command.entities.get("agent_name", "default")
            background_tasks.add_task(
                execute_agent_async,
                session_id,
                request.text,
                agent_name
            )
            response_text = f"Starting agent '{agent_name}'..."
        
        return NLProcessResponse(
            success=True,
            intent=parsed_command.intent.value,
            entities=parsed_command.entities,
            confidence=parsed_command.confidence,
            workflow_trigger=parsed_command.workflow_trigger,
            session_id=session_id,
            response_text=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing NL command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents", response_model=List[IntentInfo])
async def list_available_intents() -> List[IntentInfo]:
    """
    List all available intents with examples
    """
    try:
        commands = nlp_processor.get_available_commands()
        
        intents = []
        for cmd in commands:
            intents.append(IntentInfo(
                name=cmd["intent"],
                description=cmd["description"],
                examples=cmd["examples"],
                entities=[]  # Extract from patterns if needed
            ))
        
        return intents
        
    except Exception as e:
        logger.error(f"Error listing intents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/trigger")
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Trigger an n8n workflow
    """
    try:
        execution_id = str(uuid.uuid4())
        
        if request.async_execution:
            # Execute in background
            background_tasks.add_task(
                trigger_workflow_async,
                request.workflow_id,
                request.payload
            )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "started",
                "message": "Workflow triggered asynchronously"
            }
        else:
            # Execute synchronously
            result = await trigger_workflow_async(
                request.workflow_id,
                request.payload
            )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "completed",
                "result": result
            }
            
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: str) -> WorkflowStatusResponse:
    """
    Get workflow execution status
    """
    try:
        # In a real implementation, this would query n8n or a database
        # For now, return a mock status
        return WorkflowStatusResponse(
            workflow_id="unknown",
            execution_id=execution_id,
            status="running",
            started_at=datetime.now().isoformat(),
            completed_at=None,
            result=None,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Agent Endpoints
# ============================================

@router.post("/agents/execute")
async def execute_agent(
    agent_name: str = Query(..., description="Name of agent to execute"),
    task: str = Query(..., description="Task for the agent"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Execute a specific agent
    """
    try:
        session_id = session_id or str(uuid.uuid4())
        
        # Map agent name to role
        agent_role_map = {
            "researcher": AgentRole.RESEARCHER,
            "coder": AgentRole.CODER,
            "reviewer": AgentRole.REVIEWER,
            "executor": AgentRole.EXECUTOR,
            "monitor": AgentRole.MONITOR
        }
        
        agent_role = agent_role_map.get(agent_name.lower())
        if not agent_role:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")
        
        # Execute agent workflow
        if background_tasks:
            background_tasks.add_task(
                execute_agent_workflow,
                session_id,
                task,
                [agent_role]
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "agent": agent_name,
                "status": "started",
                "message": f"Agent {agent_name} execution started"
            }
        else:
            # Execute synchronously
            context = await agent_orchestrator.execute_workflow(
                session_id=session_id,
                user_request=task,
                workflow_name=f"{agent_name}_workflow",
                agents_chain=[agent_role]
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "agent": agent_name,
                "status": "completed",
                "result": context.state
            }
            
    except Exception as e:
        logger.error(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/list")
async def list_agents() -> Dict[str, Any]:
    """
    List available agents
    """
    try:
        agents = agent_orchestrator.get_available_agents()
        
        return {
            "success": True,
            "agents": agents,
            "default_workflow": agent_orchestrator.get_default_workflow()
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status/{session_id}")
async def get_agent_status(session_id: str) -> Dict[str, Any]:
    """
    Get agent execution status
    """
    try:
        context = await agent_orchestrator.get_context(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "session_id": session_id,
            "status": context.get("state", {}),
            "current_step": context.get("current_step", 0),
            "tasks": context.get("tasks", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# System Status Endpoints
# ============================================

@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get system status including all services
    """
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "health": "healthy"
        }
        
        # Check Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            status["services"]["ollama"] = "running" if response.status_code == 200 else "error"
        except:
            status["services"]["ollama"] = "offline"
        
        # Check Weaviate
        try:
            response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=2)
            status["services"]["weaviate"] = "running" if response.status_code == 200 else "error"
        except:
            status["services"]["weaviate"] = "offline"
        
        # Check Redis
        try:
            import redis
            r = redis.from_url("redis://localhost:6379")
            r.ping()
            status["services"]["redis"] = "running"
        except:
            status["services"]["redis"] = "offline"
        
        # Check n8n
        try:
            response = requests.get("http://localhost:5678/healthz", timeout=2)
            status["services"]["n8n"] = "running" if response.status_code == 200 else "error"
        except:
            status["services"]["n8n"] = "offline"
        
        # Overall health
        offline_services = [k for k, v in status["services"].items() if v == "offline"]
        if offline_services:
            status["health"] = "degraded"
            status["offline_services"] = offline_services
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Helper Functions
# ============================================

async def trigger_workflow_async(workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger n8n workflow asynchronously
    """
    try:
        # Call n8n webhook endpoint
        response = requests.post(
            f"http://localhost:5678/webhook/{workflow_id}",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Workflow trigger failed: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        return {"error": str(e)}


async def execute_agent_async(session_id: str, task: str, agent_name: str):
    """
    Execute agent asynchronously
    """
    try:
        agent_role_map = {
            "researcher": AgentRole.RESEARCHER,
            "coder": AgentRole.CODER,
            "reviewer": AgentRole.REVIEWER,
            "default": AgentRole.RESEARCHER
        }
        
        agent_role = agent_role_map.get(agent_name.lower(), AgentRole.RESEARCHER)
        
        await agent_orchestrator.execute_workflow(
            session_id=session_id,
            user_request=task,
            workflow_name=f"{agent_name}_workflow",
            agents_chain=[agent_role]
        )
    except Exception as e:
        logger.error(f"Error executing agent: {e}")


async def execute_agent_workflow(
    session_id: str,
    task: str,
    agents_chain: List[AgentRole]
):
    """
    Execute agent workflow
    """
    try:
        await agent_orchestrator.execute_workflow(
            session_id=session_id,
            user_request=task,
            workflow_name="custom_workflow",
            agents_chain=agents_chain
        )
    except Exception as e:
        logger.error(f"Error executing agent workflow: {e}")


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "natural-language-interface",
        "timestamp": datetime.now().isoformat()
    }