"""
SOPHIA Intel Chat API
Exposes SOPHIA orchestrator functionality as API endpoints
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from ..orchestrator import orchestrator

# Define the router
router = APIRouter(
    prefix="/swarm-chat",
    tags=["sophia-chat"],
    responses={404: {"description": "Not found"}},
)

# Define request/response models
class SwarmChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    agent_type: Optional[str] = None
    budget: Optional[str] = "premium"
    context: Optional[Dict[str, Any]] = None

class SwarmChatResponse(BaseModel):
    response: str
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None

class SessionStatusResponse(BaseModel):
    session_id: str
    message_count: int
    task_count: int
    models_used: list
    total_cost: float
    avg_response_time: float
    task_distribution: Optional[Dict[str, int]] = None
    last_activity: Optional[str] = None

@router.post("/", response_model=SwarmChatResponse)
async def chat_with_sophia(request: SwarmChatRequest):
    """
    Process a chat message with SOPHIA Intel orchestrator
    """
    try:
        result = await orchestrator.process_message(
            message=request.message,
            session_id=request.user_id or "default",
            agent_type=request.agent_type,
            budget=request.budget or "premium"
        )
        
        if result["success"]:
            return SwarmChatResponse(
                response=result["response"],
                metadata=result["metadata"],
                success=True
            )
        else:
            return SwarmChatResponse(
                response=result.get("fallback_response", "An error occurred"),
                metadata={"error": result["error"]},
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@router.post("/code", response_model=SwarmChatResponse)
async def chat_with_coding_agent(request: SwarmChatRequest):
    """
    Process a message with SOPHIA's coding specialist
    """
    try:
        result = await orchestrator.process_message(
            message=request.message,
            session_id=request.user_id or "default",
            agent_type="coding",
            budget=request.budget or "premium"
        )
        
        if result["success"]:
            return SwarmChatResponse(
                response=result["response"],
                metadata=result["metadata"],
                success=True
            )
        else:
            return SwarmChatResponse(
                response=result.get("fallback_response", "An error occurred"),
                metadata={"error": result["error"]},
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing coding request: {str(e)}")

@router.post("/research", response_model=SwarmChatResponse)
async def chat_with_research_agent(request: SwarmChatRequest):
    """
    Process a message with SOPHIA's research specialist
    """
    try:
        result = await orchestrator.process_message(
            message=request.message,
            session_id=request.user_id or "default",
            agent_type="research",
            budget=request.budget or "premium"
        )
        
        if result["success"]:
            return SwarmChatResponse(
                response=result["response"],
                metadata=result["metadata"],
                success=True
            )
        else:
            return SwarmChatResponse(
                response=result.get("fallback_response", "An error occurred"),
                metadata={"error": result["error"]},
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing research request: {str(e)}")

@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str = "default"):
    """
    Get session status and statistics
    """
    try:
        status = await orchestrator.get_session_status(session_id)
        return SessionStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session status: {str(e)}")

@router.post("/reset/{session_id}")
async def reset_chat_session(session_id: str = "default"):
    """
    Reset the chat conversation history for a session
    """
    try:
        result = await orchestrator.reset_session(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

@router.get("/models")
async def get_available_models():
    """
    Get information about available AI models
    """
    try:
        models = orchestrator.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@router.get("/health")
async def get_orchestrator_health():
    """
    Get orchestrator health status
    """
    try:
        health = orchestrator.get_health_status()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health status: {str(e)}")
