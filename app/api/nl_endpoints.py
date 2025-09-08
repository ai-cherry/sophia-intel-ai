"""
Natural Language API Endpoints
FastAPI endpoints for NL processing and workflow integration
Enhanced with standardized responses, comprehensive logging, and swarm integration
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.nl_interface.intents import format_help_text, get_intent_pattern

# Import our NL components
from app.nl_interface.quicknlp import CommandIntent, ParsedCommand, QuickNLP

# Smart dispatcher (routes NL → swarms/orchestrator/memory)
try:
    from app.nl_interface.command_dispatcher import SmartCommandDispatcher
except Exception:
    SmartCommandDispatcher = None
from app.core.circuit_breaker import with_circuit_breaker
from app.core.connections import get_connection_manager, http_get, http_post
from app.nl_interface.memory_connector import NLInteraction, NLMemoryConnector

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
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

# Initialize smart dispatcher if available
try:
    dispatcher = SmartCommandDispatcher()
    logger.info("SmartCommandDispatcher initialized in nl_endpoints")
except Exception as _e:
    logger.warning(f"SmartCommandDispatcher unavailable: {_e}")
    dispatcher = None
memory_connector = None
smart_dispatcher = None


# Initialize components on startup
async def initialize_components():
    global memory_connector, smart_dispatcher

    # Initialize memory connector
    try:
        memory_connector = NLMemoryConnector()
        await memory_connector.connect()
        logger.info("Memory connector initialized successfully")
    except Exception as e:
        logger.warning(f"Memory connector initialization failed: {e}")
        memory_connector = None

    # Initialize smart dispatcher
    try:
        smart_dispatcher = SmartCommandDispatcher(
            config_file="app/config/nl_swarm_integration.json"
        )
        logger.info("SmartCommandDispatcher initialized successfully")
    except Exception as e:
        logger.warning(f"SmartCommandDispatcher initialization failed: {e}")
        smart_dispatcher = None


# ============================================
# Request/Response Models
# ============================================


class NLProcessRequest(BaseModel):
    """Request model for NL processing"""

    text: str = Field(..., description="Natural language command text")
    context: Optional[dict[str, Any]] = Field(
        default={}, description="Optional context for processing"
    )
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")


class StandardResponse(BaseModel):
    """Standardized response format for all endpoints - ENHANCED FOR PRODUCTION"""

    success: bool
    message: str = Field(..., description="Human-readable response message")
    response: str = Field("", description="Detailed response text")
    intent: Optional[str] = None
    data: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Structured data payload"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    execution_time_ms: Optional[float] = None
    rate_limited: bool = Field(False, description="Whether this request was rate limited")
    error: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure message is set if not provided
        if not self.message and self.response:
            self.message = (
                self.response[:100] + "..." if len(self.response) > 100 else self.response
            )


class NLProcessResponse(StandardResponse):
    """Enhanced response model for NL processing"""

    entities: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    security: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Security validation info"
    )


class WorkflowTriggerRequest(BaseModel):
    """Request model for workflow trigger"""

    workflow_id: str = Field(..., description="Workflow ID to trigger")
    payload: dict[str, Any] = Field(default={}, description="Payload for workflow")
    async_execution: bool = Field(default=False, description="Execute asynchronously")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""

    workflow_id: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    result: Optional[dict[str, Any]]
    error: Optional[str]


class IntentInfo(BaseModel):
    """Model for intent information"""

    name: str
    description: str
    examples: list[str]
    entities: list[str]


# ============================================
# Core Endpoints
# ============================================


@router.post("/process", response_model=NLProcessResponse)
@with_circuit_breaker("webhook")
async def process_natural_language(
    request: NLProcessRequest, background_tasks: BackgroundTasks, req: Request
) -> NLProcessResponse:
    """
    Process natural language command with intelligent routing via SmartCommandDispatcher
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    # Enhanced logging with comprehensive metadata
    client_ip = req.client.host if req.client else "unknown"
    user_agent = req.headers.get("user-agent", "unknown")

    logger.info(f"🔄 NL REQUEST - Session: {session_id[:8]}, IP: {client_ip}")
    logger.info(f"📝 Input: '{request.text[:100]}{'...' if len(request.text) > 100 else ''}'")
    logger.debug(f"🌐 User-Agent: {user_agent}")
    logger.debug(f"📋 Context size: {len(request.context)} | API Key: {bool(request.api_key)}")

    # Use SmartCommandDispatcher if available
    if smart_dispatcher:
        try:
            # Process with smart dispatcher for intelligent routing
            execution_result = await smart_dispatcher.process_command(
                text=request.text, session_id=session_id, user_context=request.context
            )

            # Extract response data
            response_data = (
                execution_result.response if isinstance(execution_result.response, dict) else {}
            )

            return NLProcessResponse(
                success=execution_result.success,
                intent=response_data.get("intent", "unknown"),
                response=str(response_data.get("response", execution_result.response)),
                data={
                    "execution_mode": execution_result.execution_mode.value,
                    "patterns_used": execution_result.patterns_used,
                    "quality_score": execution_result.quality_score,
                    "context": request.context,
                },
                workflow_id=response_data.get("workflow_id"),
                session_id=session_id,
                entities=response_data.get("entities", {}),
                confidence=response_data.get("confidence", execution_result.quality_score),
                execution_time_ms=execution_result.execution_time * 1000,
                error=execution_result.error,
            )

        except Exception as e:
            logger.error(f"SmartDispatcher failed, falling back to simple processing: {e}")
            # Fall through to simple processing

    # Fallback to simple processing if SmartDispatcher not available
    try:
        # Process the natural language text
        parsed_command: ParsedCommand = nlp_processor.process(request.text)

        logger.info(
            f"Parsed command - Intent: {parsed_command.intent.value}, Confidence: {parsed_command.confidence:.2f}"
        )
        logger.debug(f"Entities: {parsed_command.entities}")

        # Get intent pattern for response formatting
        intent_pattern = get_intent_pattern(parsed_command.intent.value)

        # Prepare response text
        if intent_pattern:
            response_text = intent_pattern.response_template.format(
                **parsed_command.entities,
                **{"status_details": "Processing...", "execution_result": "Started"},
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
                workflow_id=parsed_command.workflow_trigger,
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
                    "session_id": session_id,
                },
            )

        # Handle special intents
        if parsed_command.intent == CommandIntent.HELP:
            response_text = format_help_text()
        elif parsed_command.intent == CommandIntent.RUN_AGENT:
            agent_name = parsed_command.entities.get("agent_name", "default")
            logger.info(f"Starting agent execution: {agent_name}")
            background_tasks.add_task(execute_agent_async, session_id, request.text, agent_name)
            response_text = f"Starting agent '{agent_name}'..."

        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Request processed successfully in {execution_time:.2f}ms")

        return NLProcessResponse(
            success=True,
            intent=parsed_command.intent.value,
            response=response_text,
            data={
                "entities": parsed_command.entities,
                "context": request.context,
                "execution_mode": "simple",
            },
            workflow_id=parsed_command.workflow_trigger,
            session_id=session_id,
            entities=parsed_command.entities,
            confidence=parsed_command.confidence,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error processing NL command: {e}", exc_info=True)

        return NLProcessResponse(
            success=False,
            response=f"Failed to process command: {str(e)}",
            session_id=session_id,
            execution_time_ms=execution_time,
            error=str(e),
        )


@router.get("/intents", response_model=list[IntentInfo])
async def list_available_intents() -> list[IntentInfo]:
    """
    List all available intents with examples
    """
    try:
        commands = nlp_processor.get_available_commands()
        intents = [
            IntentInfo(
                name=cmd["intent"],
                description=cmd["description"],
                examples=cmd["examples"],
                entities=[],
            )
            for cmd in commands
        ]
        return intents
    except Exception as e:
        logger.error(f"Error listing intents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/trigger")
@with_circuit_breaker("webhook")
async def trigger_workflow(
    request: WorkflowTriggerRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Trigger an n8n workflow
    """
    try:
        execution_id = str(uuid.uuid4())

        if request.async_execution:
            # Execute in background
            background_tasks.add_task(trigger_workflow_async, request.workflow_id, request.payload)

            return {
                "success": True,
                "execution_id": execution_id,
                "status": "started",
                "message": "Workflow triggered asynchronously",
            }
        else:
            # Execute synchronously
            result = await trigger_workflow_async(request.workflow_id, request.payload)

            return {
                "success": True,
                "execution_id": execution_id,
                "status": "completed",
                "result": result,
            }

    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/status/{execution_id}", response_model=WorkflowStatusResponse)
@with_circuit_breaker("webhook")
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
            error=None,
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
    background_tasks: BackgroundTasks = None,
) -> dict[str, Any]:
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
            "monitor": AgentRole.MONITOR,
        }

        agent_role = agent_role_map.get(agent_name.lower())
        if not agent_role:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")

        # Execute agent workflow
        if background_tasks:
            background_tasks.add_task(execute_agent_workflow, session_id, task, [agent_role])

            return {
                "success": True,
                "session_id": session_id,
                "agent": agent_name,
                "status": "started",
                "message": f"Agent {agent_name} execution started",
            }
        else:
            # Execute synchronously
            context = await agent_orchestrator.execute_workflow(
                session_id=session_id,
                user_request=task,
                workflow_name=f"{agent_name}_workflow",
                agents_chain=[agent_role],
            )

            return {
                "success": True,
                "session_id": session_id,
                "agent": agent_name,
                "status": "completed",
                "result": context.state,
            }

    except Exception as e:
        logger.error(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/list")
async def list_agents() -> dict[str, Any]:
    """
    List available agents
    """
    try:
        agents = agent_orchestrator.get_available_agents()

        return {
            "success": True,
            "agents": agents,
            "default_workflow": agent_orchestrator.get_default_workflow(),
        }

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status/{session_id}")
async def get_agent_status(session_id: str) -> dict[str, Any]:
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
            "tasks": context.get("tasks", []),
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
@with_circuit_breaker("webhook")
async def get_system_status() -> dict[str, Any]:
    """
    Get system status including all services
    """
    try:
        status = {"timestamp": datetime.now().isoformat(), "services": {}, "health": "healthy"}

        # Check Ollama
        try:
            response = await http_get("http://localhost:11434/api/tags", timeout=2)
            status["services"]["ollama"] = "running" if response.status_code == 200 else "error"
        except:
            status["services"]["ollama"] = "offline"

        # Check Weaviate
        try:
            response = await http_get("http://localhost:8080/v1/.well-known/ready", timeout=2)
            status["services"]["weaviate"] = "running" if response.status_code == 200 else "error"
        except:
            status["services"]["weaviate"] = "offline"

        # Check Redis
        try:
            r = await get_connection_manager().get_redis()
            r.ping()
            status["services"]["redis"] = "running"
        except:
            status["services"]["redis"] = "offline"

        # Check n8n
        try:
            response = await http_get("http://localhost:5678/healthz", timeout=2)
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
@with_circuit_breaker("webhook")
async def workflow_callback(
    workflow_id: str,
    status: str,
    execution_id: str,
    timestamp: str,
    result: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
    session_id: Optional[str] = None,
) -> StandardResponse:
    """
    Handle workflow completion callbacks from n8n
    """
    logger.info(
        f"Received workflow callback - ID: {workflow_id}, Status: {status}, Execution: {execution_id}"
    )

    try:
        # Store callback information
        callback_data = {
            "workflow_id": workflow_id,
            "status": status,
            "execution_id": execution_id,
            "timestamp": timestamp,
            "result": result,
            "error": error,
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
            workflow_id=workflow_id,
        )

    except Exception as e:
        logger.error(f"Error processing workflow callback: {e}", exc_info=True)
        return StandardResponse(
            success=False, response="Failed to process workflow callback", error=str(e)
        )


# ============================================
# Helper Functions
# ============================================


@with_circuit_breaker("external_api")
async def trigger_workflow_async(workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Trigger n8n workflow asynchronously
    """
    logger.debug(f"Triggering workflow {workflow_id} with payload: {payload}")

    try:
        # Add completion webhook to payload
        payload["completion_webhook"] = "http://api:8003/api/nl/workflows/callback"

        # Call n8n webhook endpoint
        response = await http_post(
            f"http://localhost:5678/webhook/{workflow_id}", json=payload, timeout=30
        )

        if response.status_code == 200:
            logger.info(f"Workflow {workflow_id} triggered successfully")
            return response
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
            "default": AgentRole.RESEARCHER,
        }

        agent_role = agent_role_map.get(agent_name.lower(), AgentRole.RESEARCHER)

        result = await agent_orchestrator.execute_workflow(
            session_id=session_id,
            user_request=task,
            workflow_name=f"{agent_name}_workflow",
            agents_chain=[agent_role],
        )

        logger.info(f"Agent {agent_name} execution completed for session {session_id[:8]}")
        return result

    except Exception as e:
        logger.error(f"Error executing agent: {e}", exc_info=True)
        raise


async def execute_agent_workflow(session_id: str, task: str, agents_chain: list[AgentRole]):
    """
    Execute agent workflow
    """
    try:
        await agent_orchestrator.execute_workflow(
            session_id=session_id,
            user_request=task,
            workflow_name="custom_workflow",
            agents_chain=agents_chain,
        )
    except Exception as e:
        logger.error(f"Error executing agent workflow: {e}")


# ============================================
# Swarm Integration Endpoints
# ============================================


@router.get("/swarm/status/{session_id}")
async def get_swarm_status(session_id: str) -> dict[str, Any]:
    """
    Get real-time swarm execution status for a session
    """
    if not smart_dispatcher:
        raise HTTPException(status_code=503, detail="SmartDispatcher not available")

    try:
        status = await smart_dispatcher.get_session_status(session_id)
        return {"success": True, **status}
    except Exception as e:
        logger.error(f"Error getting swarm status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/swarm/performance")
async def get_swarm_performance() -> dict[str, Any]:
    """
    Get comprehensive swarm performance metrics
    """
    if not smart_dispatcher:
        raise HTTPException(status_code=503, detail="SmartDispatcher not available")

    try:
        metrics = smart_dispatcher._get_performance_metrics()
        return {"success": True, "timestamp": datetime.now().isoformat(), **metrics}
    except Exception as e:
        logger.error(f"Error getting swarm performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/swarm/optimize")
async def optimize_swarm_mode(
    session_id: str = Query(..., description="Session ID to optimize"),
    optimization_goal: str = Query(
        "balanced", description="Optimization goal: speed, quality, or balanced"
    ),
) -> dict[str, Any]:
    """
    Optimize swarm execution mode for a specific session
    """
    if not smart_dispatcher:
        raise HTTPException(status_code=503, detail="SmartDispatcher not available")

    if optimization_goal not in ["speed", "quality", "balanced"]:
        raise HTTPException(status_code=400, detail="Invalid optimization goal")

    try:
        result = await smart_dispatcher.optimize_for_session(session_id, optimization_goal)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error optimizing swarm mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/swarm/modes")
async def get_execution_modes() -> dict[str, Any]:
    """
    Get available execution modes and their configurations
    """
    return {
        "success": True,
        "modes": {
            "lite": {
                "name": "Lite Mode",
                "description": "Fast, simple execution for basic commands",
                "complexity_threshold": 0.3,
                "patterns": ["quick_nlp", "simple_execution"],
            },
            "balanced": {
                "name": "Balanced Mode",
                "description": "Balanced speed and quality for moderate complexity",
                "complexity_threshold": 0.7,
                "patterns": ["memory_enrichment", "orchestrator", "quality_gates"],
            },
            "quality": {
                "name": "Quality Mode",
                "description": "High-quality execution for complex tasks",
                "complexity_threshold": 1.0,
                "patterns": ["memory_enrichment", "swarm", "debate", "quality_gates", "consensus"],
            },
        },
    }


@router.post("/swarm/reset")
async def reset_swarm_metrics() -> dict[str, Any]:
    """
    Reset swarm performance metrics (useful for testing)
    """
    if not smart_dispatcher:
        raise HTTPException(status_code=503, detail="SmartDispatcher not available")

    try:
        smart_dispatcher.optimizer.reset_metrics()
        smart_dispatcher.execution_stats = {
            "total_commands": 0,
            "success_count": 0,
            "failure_count": 0,
            "mode_usage": {"lite": 0, "balanced": 0, "quality": 0},
            "avg_execution_time": 0,
            "total_execution_time": 0,
        }

        return {
            "success": True,
            "message": "Swarm metrics reset successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error resetting swarm metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Health Check
# ============================================


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "natural-language-interface",
        "timestamp": datetime.now().isoformat(),
        "smart_dispatcher": "available" if smart_dispatcher else "unavailable",
    }
