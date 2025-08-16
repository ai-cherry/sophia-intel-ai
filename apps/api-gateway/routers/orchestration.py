"""Orchestration router - Single front door with rate limiting and error handling"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.orchestrator import orchestrator
from core.middleware import limiter
import structlog

logger = structlog.get_logger()
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
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def orchestrate_request(request: Request, orchestration_request: OrchestrationRequest):
    """Single front door for all AI orchestration requests - Rate Limited"""
    try:
        logger.info("orchestration_request", 
                   request_type=orchestration_request.request_type,
                   client_ip=get_remote_address(request))
        
        result = await orchestrator.handle_request(
            request_type=orchestration_request.request_type,
            payload=orchestration_request.payload,
            context=orchestration_request.context or {}
        )
        
        logger.info("orchestration_success", 
                   request_id=result.get("request_id"),
                   model_used=result.get("model_used"))
        
        return OrchestrationResponse(
            status="success",
            result=result,
            request_id=result.get("request_id", "unknown"),
            model_used=result.get("model_used"),
            cost_estimate=result.get("cost_estimate")
        )
        
    except Exception as e:
        logger.error("orchestration_failed", error=str(e), request_type=orchestration_request.request_type)
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")
