"""Orchestration router - Single front door for all AI requests"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.orchestrator import orchestrator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class OrchestrationRequest(BaseModel):
    request_type: str  # chat, code, memory, research
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class OrchestrationResponse(BaseModel):
    status: str
    result: Dict[str, Any]
    request_id: str
    model_used: Optional[str] = None
    cost_estimate: Optional[float] = None

@router.post("/api/orchestration", response_model=OrchestrationResponse)
async def orchestrate_request(request: OrchestrationRequest):
    """Single front door for all AI orchestration requests"""
    try:
        logger.info(f"Orchestrating {request.request_type} request")
        
        result = await orchestrator.handle_request(
            request_type=request.request_type,
            payload=request.payload,
            context=request.context or {}
        )
        
        return OrchestrationResponse(
            status="success",
            result=result,
            request_id=result.get("request_id", "unknown"),
            model_used=result.get("model_used"),
            cost_estimate=result.get("cost_estimate")
        )
        
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
