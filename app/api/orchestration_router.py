"""
Production Orchestration Router
Integrates the SuperOrchestrator with Pydantic validation models
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

from app.core.super_orchestrator import get_orchestrator
from app.models.orchestration_models import (
    AgentRequest,
    ChatRequest,
    ChatResponse,
    CommandRequest,
    CommandResponse,
    OrchestrationRequest,
    OrchestrationResponse,
    QueryRequest,
    QueryResponse,
    TaskPriority,
    TaskStatus,
    TaskType,
    create_error_response,
    create_orchestration_task,
    sanitize_content,
)
from app.security.auth_middleware import get_current_user, verify_admin_access

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Chat Endpoints
# ============================================


@router.post("/chat", response_model=ChatResponse, summary="Chat with AI")
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user),
):
    """
    Chat endpoint with full validation and response handling
    """
    start_time = time.time()

    try:
        orchestrator = get_orchestrator()

        # Convert to orchestrator format
        orchestrator_request = {
            "type": "chat",
            "message": request.message,
            "conversation_id": request.conversation_id,
            "metadata": {
                **request.metadata,
                "user_id": current_user.get("user_id") if current_user else None,
                "model_preference": request.model_preference,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
        }

        # Execute request
        result = await orchestrator.process_request(orchestrator_request)

        processing_time = (time.time() - start_time) * 1000

        # Convert response
        response = ChatResponse(
            request_id=request.request_id,
            status="success",
            processing_time_ms=processing_time,
            message=result.get("message", ""),
            conversation_id=request.conversation_id,
            model_used=result.get("model_used"),
            tokens_used=result.get("tokens_used"),
            confidence_score=result.get("confidence"),
            citations=result.get("citations", []),
            needs_confirmation=result.get("needs_confirmation", False),
            metadata=result.get("metadata", {}),
        )

        # Log chat interaction
        background_tasks.add_task(_log_chat_interaction, request, response, current_user)

        return response

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        processing_time = (time.time() - start_time) * 1000

        return ChatResponse(
            request_id=request.request_id,
            status="error",
            processing_time_ms=processing_time,
            message=f"Chat request failed: {str(e)}",
            metadata={"error": str(e)},
        )


@router.post("/chat/stream", summary="Streaming chat response")
async def streaming_chat_endpoint(
    request: ChatRequest, current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Streaming chat endpoint for real-time responses
    """

    async def generate_response():
        try:
            orchestrator = get_orchestrator()

            # This would implement actual streaming
            # For now, simulate streaming response
            message_parts = [
                "I'm processing your request...",
                "Analyzing the information...",
                "Generating response based on your query...",
            ]

            for i, part in enumerate(message_parts):
                chunk = {
                    "request_id": request.request_id,
                    "chunk_id": i,
                    "content": part,
                    "is_final": i == len(message_parts) - 1,
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.5)  # Simulate processing delay

        except Exception as e:
            error_chunk = {
                "request_id": request.request_id,
                "error": str(e),
                "is_final": True,
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {error_chunk}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================
# Command Endpoints
# ============================================


@router.post("/command", response_model=CommandResponse, summary="Execute system command")
async def command_endpoint(
    request: CommandRequest, current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Execute system commands with proper validation and authorization
    """
    # Check permissions for sensitive commands
    sensitive_commands = {"deploy", "scale", "heal", "restart"}
    if request.command in sensitive_commands and (
        not current_user or "admin" not in current_user.get("permissions", set())
    ):
        raise HTTPException(status_code=403, detail="Admin permissions required for this command")

    start_time = time.time()

    try:
        orchestrator = get_orchestrator()

        orchestrator_request = {
            "type": "command",
            "command": request.command,
            "params": request.parameters,
            "metadata": {
                **request.metadata,
                "user_id": current_user.get("user_id") if current_user else None,
                "require_confirmation": request.require_confirmation,
            },
        }

        result = await orchestrator.process_request(orchestrator_request)
        processing_time = (time.time() - start_time) * 1000

        return CommandResponse(
            request_id=request.request_id,
            status="success",
            processing_time_ms=processing_time,
            command=request.command,
            result=result.get("result", {}),
            success=result.get("success", True),
            error_message=result.get("error_message"),
            affected_resources=result.get("affected_resources", []),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        processing_time = (time.time() - start_time) * 1000

        return CommandResponse(
            request_id=request.request_id,
            status="error",
            processing_time_ms=processing_time,
            command=request.command,
            result={},
            success=False,
            error_message=str(e),
        )


# ============================================
# Query Endpoints
# ============================================


@router.post("/query", response_model=QueryResponse, summary="Query system data")
async def query_endpoint(
    request: QueryRequest, current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Query system data with validation and pagination
    """
    start_time = time.time()

    try:
        orchestrator = get_orchestrator()

        orchestrator_request = {
            "type": "query",
            "query_type": request.query_type,
            "parameters": request.parameters,
            "filters": request.filters,
            "limit": request.limit,
            "offset": request.offset,
            "metadata": {
                **request.metadata,
                "user_id": current_user.get("user_id") if current_user else None,
            },
        }

        result = await orchestrator.process_request(orchestrator_request)
        processing_time = (time.time() - start_time) * 1000

        return QueryResponse(
            request_id=request.request_id,
            status="success",
            processing_time_ms=processing_time,
            query_type=request.query_type,
            data=result.get("data", {}),
            total_count=result.get("total_count"),
            page_info=result.get("page_info"),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        processing_time = (time.time() - start_time) * 1000

        return QueryResponse(
            request_id=request.request_id,
            status="error",
            processing_time_ms=processing_time,
            query_type=request.query_type,
            data={"error": str(e)},
        )


# ============================================
# Agent Management Endpoints
# ============================================


@router.post("/agent", summary="Manage agents")
async def agent_endpoint(
    request: AgentRequest, current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Agent management with proper authorization
    """
    # Check admin permissions for agent operations
    if not current_user or "admin" not in current_user.get("permissions", set()):
        raise HTTPException(
            status_code=403, detail="Admin permissions required for agent management"
        )

    start_time = time.time()

    try:
        orchestrator = get_orchestrator()

        orchestrator_request = {
            "type": "agent",
            "action": request.action,
            "config": request.agent_config,
            "agent_id": request.agent_id,
            "metadata": {**request.metadata, "user_id": current_user.get("user_id")},
        }

        result = await orchestrator.process_request(orchestrator_request)
        processing_time = (time.time() - start_time) * 1000

        return {
            "request_id": request.request_id,
            "status": "success",
            "processing_time_ms": processing_time,
            "action": request.action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Agent operation failed: {e}")
        processing_time = (time.time() - start_time) * 1000

        return {
            "request_id": request.request_id,
            "status": "error",
            "processing_time_ms": processing_time,
            "action": request.action,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================
# Orchestration Endpoint
# ============================================


@router.post("/orchestrate", response_model=OrchestrationResponse, summary="General orchestration")
async def orchestration_endpoint(
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user),
):
    """
    General orchestration endpoint with full validation and task tracking
    """
    start_time = time.time()

    try:
        # Create validated task
        task = create_orchestration_task(
            content=request.content,
            task_type=request.type,
            priority=request.priority,
            budget=request.budget,
            metadata={
                **request.metadata,
                **request.context,
                "user_id": current_user.get("user_id") if current_user else None,
                "orchestrator_preference": request.orchestrator.value,
            },
        )

        orchestrator = get_orchestrator()

        # Convert task to orchestrator format
        orchestrator_request = {
            "type": task.type.value,
            "content": task.content,
            "priority": task.priority.value,
            "budget": task.budget,
            "metadata": task.metadata,
            "task_id": task.id,
        }

        result = await orchestrator.process_request(orchestrator_request)
        processing_time = (time.time() - start_time) * 1000

        # Format response
        response = OrchestrationResponse(
            request_id=request.request_id,
            status="success",
            processing_time_ms=processing_time,
            task_id=task.id,
            type=task.type,
            result=result,
            orchestrator_used="super_orchestrator",
            confidence_score=result.get("confidence"),
            citations=result.get("citations", []),
            cost_estimate=result.get("cost_estimate"),
            metadata=result.get("metadata", {}),
        )

        # Log orchestration request
        background_tasks.add_task(
            _log_orchestration_request, request, response, current_user, processing_time
        )

        return response

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        processing_time = (time.time() - start_time) * 1000

        return OrchestrationResponse(
            request_id=request.request_id,
            status="error",
            processing_time_ms=processing_time,
            task_id="error",
            type=request.type,
            orchestrator_used="super_orchestrator",
            result={"error": str(e)},
            metadata={"error": str(e)},
        )


# ============================================
# WebSocket Endpoint
# ============================================


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time orchestration
    """
    try:
        orchestrator = get_orchestrator()
        await orchestrator.connect_websocket(websocket)

        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                # Validate message structure
                if "type" not in data:
                    await websocket.send_json(
                        {
                            "error": "Message must have 'type' field",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    continue

                # Process based on message type
                if data["type"] == "chat":
                    # Validate chat request
                    try:
                        chat_req = ChatRequest(**data)
                        orchestrator_request = {
                            "type": "chat",
                            "message": chat_req.message,
                            "metadata": {"websocket": True, **chat_req.metadata},
                        }
                    except Exception as e:
                        await websocket.send_json(
                            {
                                "error": f"Invalid chat request: {e}",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        continue

                elif data["type"] == "command":
                    try:
                        cmd_req = CommandRequest(**data)
                        orchestrator_request = {
                            "type": "command",
                            "command": cmd_req.command,
                            "params": cmd_req.parameters,
                            "metadata": {"websocket": True, **cmd_req.metadata},
                        }
                    except Exception as e:
                        await websocket.send_json(
                            {
                                "error": f"Invalid command request: {e}",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        continue

                else:
                    # Generic orchestration
                    orchestrator_request = {
                        **data,
                        "metadata": {**data.get("metadata", {}), "websocket": True},
                    }

                # Execute request
                result = await orchestrator.process_request(orchestrator_request)

                # Send response
                await websocket.send_json(
                    {
                        "type": "response",
                        "request_type": data["type"],
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")
                try:
                    await websocket.send_json(
                        {"error": str(e), "timestamp": datetime.now().isoformat()}
                    )
                except:
                    break  # Connection might be closed

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        try:
            orchestrator = get_orchestrator()
            await orchestrator.disconnect_websocket(websocket)
        except:
            pass  # Already disconnected


# ============================================
# Status and Monitoring Endpoints
# ============================================


@router.get("/status", summary="Get orchestrator status")
async def orchestrator_status():
    """
    Get current orchestrator status and metrics
    """
    try:
        orchestrator = get_orchestrator()
        metrics = await orchestrator._collect_metrics()

        return {
            "status": "operational",
            "uptime_seconds": int(time.time() - orchestrator.start_time),
            "metrics": metrics,
            "active_connections": len(orchestrator.connections),
            "active_tasks": len(orchestrator.tasks.active_tasks),
            "completed_tasks": len(orchestrator.tasks.completed_tasks),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", summary="Get task status")
async def get_tasks(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: Optional[Dict] = Depends(get_current_user),
):
    """
    Get task status and history
    """
    try:
        orchestrator = get_orchestrator()

        tasks = {
            "active": list(orchestrator.tasks.active_tasks.values()),
            "completed": orchestrator.tasks.completed_tasks[-limit:],
        }

        if status:
            if status == "active":
                tasks = {"active": tasks["active"]}
            elif status == "completed":
                tasks = {"completed": tasks["completed"]}

        return {
            "tasks": tasks,
            "total_active": len(orchestrator.tasks.active_tasks),
            "total_completed": len(orchestrator.tasks.completed_tasks),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Task query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Background Task Functions
# ============================================


async def _log_chat_interaction(request: ChatRequest, response: ChatResponse, user: Optional[Dict]):
    """Log chat interaction for analytics"""
    try:
        # This would log to a proper analytics system
        logger.info(
            f"Chat interaction: user={user.get('user_id') if user else 'anonymous'}, "
            f"tokens={response.tokens_used}, confidence={response.confidence_score}"
        )
    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")


async def _log_orchestration_request(
    request: OrchestrationRequest,
    response: OrchestrationResponse,
    user: Optional[Dict],
    processing_time: float,
):
    """Log orchestration request for analytics"""
    try:
        logger.info(
            f"Orchestration: type={request.type.value}, "
            f"user={user.get('user_id') if user else 'anonymous'}, "
            f"time={processing_time:.2f}ms, status={response.status}"
        )
    except Exception as e:
        logger.error(f"Failed to log orchestration request: {e}")
