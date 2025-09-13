"""
AIML Enhanced Router
Provides repository-aware chat completions via AIMLAPI and MCP
"""

import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import field_validator as _field_validator
except Exception:
    # Fallback for v1
    from pydantic import validator as _field_validator

from app.config.aimlapi import get_settings
from app.config.models import get_model_profile, list_model_profiles
from app.services.aiml_client import get_aiml_client
from app.services.mcp_context import get_mcp_context_manager
from app.core.metrics import inc_counter
import time
import asyncio

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/aiml",
    tags=["AIML Enhanced"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


# Request/Response models
class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role (system/user/assistant)")
    content: str = Field(..., description="Message content")
    
    @_field_validator("role")
    def validate_role(cls, v):
        if v not in ["system", "user", "assistant"]:
            raise ValueError("Role must be system, user, or assistant")
        return v


class ChatRequest(BaseModel):
    """Chat completion request"""
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: Optional[str] = Field("sophia-general", description="Model profile ID")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens")
    stream: bool = Field(False, description="Stream the response")
    include_context: bool = Field(True, description="Include repository context")
    
    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Analyze the MCP architecture"}
                ],
                "model": "sophia-architect",
                "stream": False,
                "include_context": True
            }
        }


class ChatResponse(BaseModel):
    """Chat completion response"""
    id: str = Field(..., description="Response ID")
    object: str = Field("chat.completion", description="Response type")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")


class RepositoryAnalysis(BaseModel):
    """Repository analysis response"""
    structure: Dict[str, Any] = Field(..., description="Repository structure")
    git_status: Dict[str, Any] = Field(..., description="Git status")
    statistics: Dict[str, Any] = Field(..., description="Repository statistics")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


# Dependency for optional auth
async def verify_auth(
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Verify optional bearer token if configured
    
    Args:
        authorization: Authorization header
        
    Returns:
        True if authorized
        
    Raises:
        HTTPException: If unauthorized
    """
    settings = get_settings()
    
    # If no router token configured, allow all
    if not settings.router_token:
        return True
    
    # Check bearer token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token = authorization.replace("Bearer ", "")
    if token != settings.router_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True


_RATE_LIMIT: dict[str, list[float]] = {}
_RATE_WINDOW = 10.0  # seconds
_RATE_MAX = 30       # requests per IP per window


def _rate_limit(remote_ip: str) -> bool:
    now = time.time()
    q = _RATE_LIMIT.setdefault(remote_ip, [])
    while q and (now - q[0]) > _RATE_WINDOW:
        q.pop(0)
    if len(q) >= _RATE_MAX:
        return False
    q.append(now)
    return True


@router.post("/chat", response_model=None)
async def chat_completion(
    request: ChatRequest,
    authorized: bool = Depends(verify_auth)
):
    """
    Send chat completion request with optional repository context
    
    This endpoint proxies to AIMLAPI with intelligent context injection
    from MCP servers when include_context=true.
    """
    settings = get_settings()
    
    if not settings.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AIMLAPI not configured. Please set AIMLAPI_API_KEY in environment."
        )
    
    # Get model profile
    profile = get_model_profile(request.model)
    
    # Convert messages to dict format
    messages = [msg.dict() for msg in request.messages]
    
    # Inject repository context if requested
    if request.include_context:
        try:
            context_manager = await get_mcp_context_manager()
            context = await context_manager.build_compact_context()

            # Create context message
            context_msg = {
                "role": "system",
                "content": (
                    f"{profile.system_prompt}\n\n"
                    f"Repository Context:\n{json.dumps(context, indent=2)}"
                )
            }

            # Inject or merge with existing system message
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = f"{messages[0]['content']}\n\n{context_msg['content']}"
            else:
                messages.insert(0, context_msg)

            logger.info(f"Injected repository context for model {profile.id}")

        except Exception as e:
            logger.warning(f"Failed to get repository context: {e}")
            # Continue without context
    
    # Use profile settings or request overrides
    temperature = request.temperature if request.temperature is not None else profile.temperature
    max_tokens = request.max_tokens if request.max_tokens is not None else profile.max_tokens
    
    # Get AIML client
    client = get_aiml_client()
    
    try:
        if request.stream:
            # Stream response
            async def generate():
                inc_counter("aiml_requests_total", label=profile.id)
                try:
                    async for chunk in client.stream_chat(
                        messages=messages,
                        model_id=profile.model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        yield chunk
                except asyncio.CancelledError:
                    logger.info("Stream cancelled by client")
                    return
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    error_data = json.dumps({"error": str(e)})
                    yield f"data: {error_data}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Non-streaming response
            inc_counter("aiml_requests_total", label=profile.id)
            result = await client.chat(
                messages=messages,
                model_id=profile.model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Add model info to response
            result["model"] = profile.id
            
            return result
            
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(
    authorized: bool = Depends(verify_auth)
):
    """
    List available model profiles
    
    Returns configured model profiles with their capabilities.
    """
    return {
        "object": "list",
        "data": list_model_profiles()
    }


@router.post("/repository/analyze", response_model=RepositoryAnalysis)
async def analyze_repository(
    authorized: bool = Depends(verify_auth)
):
    """
    Analyze repository structure and provide insights
    
    Lightweight analysis using MCP servers, results are cached.
    """
    try:
        context_manager = await get_mcp_context_manager()
        # Get repository info
        structure = await context_manager.get_repository_structure()
        git_status = await context_manager.get_git_status()

        # Calculate statistics
        statistics = {
            "total_files": structure.get("total_files", 0),
            "directories": len(structure.get("key_directories", [])),
            "modified_files": git_status.get("modified_count", 0),
            "current_branch": git_status.get("branch", "unknown")
        }

        # Generate recommendations
        recommendations = []
        if git_status.get("untracked_count", 0) > 10:
            recommendations.append("Consider reviewing untracked files")
        if git_status.get("modified_count", 0) > 20:
            recommendations.append("Large number of modifications - consider committing")
        if statistics.get("total_files", 0) > 1000:
            recommendations.append("Large repository - consider modularization")

        return RepositoryAnalysis(
            structure=structure,
            git_status=git_status,
            statistics=statistics,
            recommendations=recommendations
        )
            
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Check AIML router health
    
    Verifies configuration and connectivity.
    """
    settings = get_settings()
    
    health = {
        "status": "healthy" if settings.is_configured else "degraded",
        "configured": settings.is_configured,
        "enabled": settings.enabled,
        "has_api_key": bool(settings.api_key),
        "base_url": settings.base_url
    }
    
    # Check MCP connectivity
    try:
        context_manager = await get_mcp_context_manager()
        # Quick connectivity test
        structure = await context_manager.get_repository_structure()
        health["mcp_connected"] = not structure.get("error")
    except:
        health["mcp_connected"] = False
    
    return health


# Optional: Mount this router in the main app
def setup_router(app):
    """
    Setup AIML enhanced router
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    
    if settings.enabled:
        app.include_router(router)
        logger.info("AIML enhanced router mounted at /api/aiml")
    else:
        logger.info("AIML enhanced router disabled (AIML_ENHANCED_ENABLED=false)")
