"""
Natural Language API Endpoints
FastAPI endpoints for NL processing and workflow integration
Enhanced with standardized responses and comprehensive logging
"""

import uuid
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
import requests

# Import our NL components
from app.nl_interface.quicknlp import QuickNLP, CommandIntent, ParsedCommand
from app.nl_interface.intents import get_intent_pattern, format_help_text
from app.agents.simple_orchestrator import SimpleAgentOrchestrator, AgentRole
from app.nl_interface.memory_connector import NLMemoryConnector, NLInteraction

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
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
memory_connector = None

# Initialize memory connector on startup
async def initialize_memory():
    global memory_connector
    try:
        memory_connector = NLMemoryConnector()
        await memory_connector.connect()
        logger.info("Memory connector initialized successfully")
    except Exception as e:
        logger.warning(f"Memory connector initialization failed: {e}")
        memory_connector = None


# ============================================
# Request/Response Models
# ============================================

class NLProcessRequest(BaseModel):
    """Request model for NL processing"""
    text: str = Field(..., description="Natural language command text")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Optional context for processing")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")


class StandardResponse(BaseModel):
    """Standardized response format for all endpoints"""
    success: bool
    intent: Optional[str] = None
    response: str
    data: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None

class NLProcessResponse(StandardResponse):
    """Response model for NL processing"""
    entities: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


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
    background_tasks: BackgroundTasks,
    req: Request
) -> NLProcessResponse:
    """
    Process natural language command and execute corresponding workflow
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    
    # Log incoming request
    logger.info(f"Processing NL request - Session: {session_id[:8]}, Text: '{request.text}'")
    
    try:
        # Process the natural language text
        parsed_command: ParsedCommand = nlp_processor.process(request.text)
        
        logger.info(f"Parsed command - Intent: {parsed_command.intent.value}, Confidence: {parsed_command.confidence:.2f}")
        logger.debug(f"Entities: {parsed_command.entities}")
        
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
        
        # Store interaction in memory if available
        if memory_connector:
            interaction = NLInteraction(
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                user_input=request.text,
                intent=parsed_command.intent.value,
                entities=parsed_command.entities,
                confidence=parsed_command.confidence,
                response=response_text,
                workflow_id=parsed_command.workflow_trigger
            )
            background_tasks.add_task(memory_connector.store_interaction, interaction)
        
        # If workflow trigger is available, execute it
        if parsed_command.workflow_trigger:
            logger.info(f"Triggering workflow: {parsed_command.workflow_trigger}")
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
            agent_name = parsed_command.entities.get("agent_name", "default")
            logger.info(f"Starting agent execution: {agent_name}")
            background_tasks.add_task(
                execute_agent_async,
                session_id,
                request.text,
                agent_name
            )
            response_text = f"Starting agent '{agent_name}'..."
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Request processed successfully in {execution_time:.2f}ms")
        
        return NLProcessResponse(
            success=True,
            intent=parsed_command.intent.value,
            response=response_text,
            data={
                "entities": parsed_command.entities,
                "context": request.context
            },
            workflow_id=parsed_command.workflow_trigger,
            session_id=session_id,
            entities=parsed_command.entities,
            confidence=parsed_command.confidence,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error processing NL command: {e}", exc_info=True)
        
        return NLProcessResponse(
            success=False,
            response=f"Failed to process command: {str(e)}",
            session_id=session_id,
            execution_time_ms=execution_time,
            error=str(e)
        )


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
# Workflow Callback Handler
# ============================================

@router.post("/workflows/callback")
async def workflow_callback(
    workflow_id: str,
    status: str,
    execution_id: str,
    timestamp: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    session_id: Optional[str] = None
) -> StandardResponse:
    """
    Handle workflow completion callbacks from n8n
    """
    logger.info(f"Received workflow callback - ID: {workflow_id}, Status: {status}, Execution: {execution_id}")
    
    try:
        # Store callback information
        callback_data = {
            "workflow_id": workflow_id,
            "status": status,
            "execution_id": execution_id,
            "timestamp": timestamp,
            "result": result,
            "error": error
        }
        
        # Update memory if available
        if memory_connector and session_id:
            # Retrieve the original interaction and update it
            history = await memory_connector.retrieve_session_history(session_id, limit=1)
            if history:
                interaction = history[0]
                interaction["execution_result"] = callback_data
                # Store updated interaction
                await memory_connector.store_interaction(NLInteraction(**interaction))
        
        logger.info(f"Workflow {workflow_id} completed with status: {status}")
        
        return StandardResponse(
            success=True,
            response=f"Workflow {workflow_id} callback processed",
            data=callback_data,
            workflow_id=workflow_id
        )
        
    except Exception as e:
        logger.error(f"Error processing workflow callback: {e}", exc_info=True)
        return StandardResponse(
            success=False,
            response="Failed to process workflow callback",
            error=str(e)
        )

# ============================================
# Helper Functions
# ============================================

async def trigger_workflow_async(workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger n8n workflow asynchronously
    """
    logger.debug(f"Triggering workflow {workflow_id} with payload: {payload}")
    
    try:
        # Add completion webhook to payload
        payload["completion_webhook"] = "http://api:8003/api/nl/workflows/callback"
        
        # Call n8n webhook endpoint
        response = requests.post(
            f"http://localhost:5678/webhook/{workflow_id}",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Workflow {workflow_id} triggered successfully")
            return response.json()
        else:
            logger.error(f"Workflow trigger failed with status {response.status_code}")
            return {"error": f"Workflow trigger failed: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}", exc_info=True)
        return {"error": str(e)}


async def execute_agent_async(session_id: str, task: str, agent_name: str):
    """
    Execute agent asynchronously
    """
    logger.debug(f"Executing agent {agent_name} for session {session_id[:8]}")
    
    try:
        agent_role_map = {
            "researcher": AgentRole.RESEARCHER,
            "coder": AgentRole.CODER,
            "reviewer": AgentRole.REVIEWER,
            "default": AgentRole.RESEARCHER
        }
        
        agent_role = agent_role_map.get(agent_name.lower(), AgentRole.RESEARCHER)
        
        result = await agent_orchestrator.execute_workflow(
            session_id=session_id,
            user_request=task,
            workflow_name=f"{agent_name}_workflow",
            agents_chain=[agent_role]
        )
        
        logger.info(f"Agent {agent_name} execution completed for session {session_id[:8]}")
        return result
        
    except Exception as e:
        logger.error(f"Error executing agent: {e}", exc_info=True)
        raise


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