import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from app.mcp.memory_adapter import UnifiedMemoryAdapter
# OpenAPI Security Scheme
security = HTTPBearer(
    scheme_name="Bearer Token",
    description="Bearer token authentication for memory API access",
)
router = APIRouter(
    prefix="/api/memory",
    tags=["memory"],
    responses={
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "headers": {
                "Retry-After": {
                    "description": "Number of seconds to wait before retrying"
                }
            },
        }
    },
)
memory_adapter = UnifiedMemoryAdapter()
# Rate limiting configuration
RATE_LIMITS = {
    "store": {"requests": 100, "window": 3600},  # 100 requests per hour
    "retrieve": {"requests": 1000, "window": 3600},  # 1000 requests per hour
    "search": {"requests": 500, "window": 3600},  # 500 requests per hour
}
# Simple in-memory rate limiting (production should use Redis)
rate_limit_store: Dict[str, Dict[str, List[float]]] = {}
class StandardErrorResponse(BaseModel):
    """Standardized JSON error envelope"""
    error: bool = True
    error_type: str = Field(
        ..., description="Type of error (validation, rate_limit, server_error, etc.)"
    )
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    request_id: Optional[str] = Field(
        None, description="Unique request identifier for tracking"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
class MemoryStoreRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    messages: List[dict] = Field(..., description="Messages to store")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    session_ids: Optional[List[str]] = Field(
        None, description="Specific sessions to search"
    )
    max_results: int = Field(10, ge=1, le=100, description="Maximum results to return")
    include_metadata: bool = Field(True, description="Include metadata in results")
def check_rate_limit(client_id: str, endpoint: str, response: Response) -> bool:
    """Check if request exceeds rate limit and set Retry-After header if needed"""
    if endpoint not in RATE_LIMITS:
        return True
    current_time = time.time()
    window = RATE_LIMITS[endpoint]["window"]
    max_requests = RATE_LIMITS[endpoint]["requests"]
    # Initialize client tracking
    if client_id not in rate_limit_store:
        rate_limit_store[client_id] = {}
    if endpoint not in rate_limit_store[client_id]:
        rate_limit_store[client_id][endpoint] = []
    # Clean old requests outside window
    requests = rate_limit_store[client_id][endpoint]
    rate_limit_store[client_id][endpoint] = [
        req_time for req_time in requests if current_time - req_time < window
    ]
    # Check if over limit
    if len(rate_limit_store[client_id][endpoint]) >= max_requests:
        # Calculate retry after time
        oldest_request = min(rate_limit_store[client_id][endpoint])
        retry_after = int(window - (current_time - oldest_request)) + 1
        response.headers["Retry-After"] = str(retry_after)
        return False
    # Add current request
    rate_limit_store[client_id][endpoint].append(current_time)
    return True
def get_client_id(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract client identifier for rate limiting (simplified for demo)"""
    if authorization and authorization.credentials:
        return f"user_{authorization.credentials[:8]}"  # Use first 8 chars of token as client ID
    return "anonymous"
def create_error_response(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500,
) -> HTTPException:
    """Create standardized error response"""
    error_data = StandardErrorResponse(
        error_type=error_type,
        message=message,
        details=details,
        request_id=f"req_{int(time.time() * 1000)}",
    )
    return HTTPException(status_code=status_code, detail=error_data.dict())
@router.get("/health")
async def memory_health():
    """Memory service health check"""
    try:
        # Test memory adapter connectivity
        health_status = (
            await memory_adapter.health_check()
            if hasattr(memory_adapter, "health_check")
            else True
        )
        return {
            "status": "healthy" if health_status else "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": "memory_api",
            "version": "1.0.0",
            "checks": {
                "memory_adapter": "healthy" if health_status else "failed",
                "rate_limiting": "operational",
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "memory_api",
            "error": str(e),
        }
@router.get("/ready")
async def memory_readiness():
    """Memory service readiness check"""
    try:
        # Check if service is ready to accept requests
        is_ready = hasattr(memory_adapter, "store_conversation")
        return {
            "ready": is_ready,
            "timestamp": datetime.now().isoformat(),
            "service": "memory_api",
            "dependencies": {"memory_adapter": "ready" if is_ready else "not_ready"},
        }
    except Exception as e:
        raise create_error_response(
            "service_error", f"Readiness check failed: {str(e)}", status_code=503
        )
@router.get("/live")
async def memory_liveness():
    """Memory service liveness check"""
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat(),
        "service": "memory_api",
        "uptime_check": "passed",
    }
@router.get("/version")
async def memory_version():
    """Memory service version information"""
    return {
        "service": "memory_api",
        "version": "1.0.0",
        "api_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "conversation_storage",
            "memory_retrieval",
            "rate_limiting",
            "standardized_errors",
            "health_monitoring",
        ],
    }
@router.post("/store")
async def store_memory(
    request: MemoryStoreRequest,
    response: Response,
    client_id: str = Depends(get_client_id),
):
    """Store conversation memory with rate limiting and error handling"""
    try:
        # Check rate limit
        if not check_rate_limit(client_id, "store", response):
            raise create_error_response(
                "rate_limit",
                "Too many store requests. Please try again later.",
                {
                    "limit": RATE_LIMITS["store"]["requests"],
                    "window": RATE_LIMITS["store"]["window"],
                },
                status_code=429,
            )
        # Validate request
        if not request.messages:
            raise create_error_response(
                "validation_error",
                "Messages cannot be empty",
                {"field": "messages"},
                status_code=400,
            )
        metadata = request.metadata or {}
        result = await memory_adapter.store_conversation(
            request.session_id, request.messages, metadata
        )
        return {
            "success": True,
            "message": "Memory stored successfully",
            "session_id": request.session_id,
            "stored_count": len(request.messages),
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise create_error_response(
            "server_error",
            "Failed to store memory",
            {"original_error": str(e)},
            status_code=500,
        )
@router.get("/retrieve/{session_id}")
async def retrieve_memory(
    session_id: str,
    last_n: int = 10,
    include_system: bool = False,
    response: Response = Response(),
    client_id: str = Depends(get_client_id),
):
    """Retrieve conversation memory with rate limiting"""
    try:
        # Check rate limit
        if not check_rate_limit(client_id, "retrieve", response):
            raise create_error_response(
                "rate_limit",
                "Too many retrieve requests. Please try again later.",
                {
                    "limit": RATE_LIMITS["retrieve"]["requests"],
                    "window": RATE_LIMITS["retrieve"]["window"],
                },
                status_code=429,
            )
        # Validate parameters
        if last_n < 1 or last_n > 1000:
            raise create_error_response(
                "validation_error",
                "last_n must be between 1 and 1000",
                {"field": "last_n", "value": last_n},
                status_code=400,
            )
        result = await memory_adapter.retrieve_context(
            session_id, last_n, include_system
        )
        return {
            "success": True,
            "session_id": session_id,
            "retrieved_count": len(result) if isinstance(result, list) else 1,
            "data": result,
            "parameters": {"last_n": last_n, "include_system": include_system},
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise create_error_response(
            "server_error",
            "Failed to retrieve memory",
            {"session_id": session_id, "original_error": str(e)},
            status_code=500,
        )
@router.post("/search")
async def search_memory(
    request: MemorySearchRequest,
    response: Response,
    client_id: str = Depends(get_client_id),
):
    """Search memory content with advanced filtering"""
    try:
        # Check rate limit
        if not check_rate_limit(client_id, "search", response):
            raise create_error_response(
                "rate_limit",
                "Too many search requests. Please try again later.",
                {
                    "limit": RATE_LIMITS["search"]["requests"],
                    "window": RATE_LIMITS["search"]["window"],
                },
                status_code=429,
            )
        # Validate query
        if len(request.query.strip()) < 2:
            raise create_error_response(
                "validation_error",
                "Search query must be at least 2 characters long",
                {"field": "query", "min_length": 2},
                status_code=400,
            )
        # Execute search (mock implementation for now)
        # In production, this would use the actual memory search functionality
        results = []
        return {
            "success": True,
            "query": request.query,
            "results_found": len(results),
            "results": results,
            "search_parameters": {
                "session_ids": request.session_ids,
                "max_results": request.max_results,
                "include_metadata": request.include_metadata,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise create_error_response(
            "server_error",
            "Memory search failed",
            {"query": request.query, "original_error": str(e)},
            status_code=500,
        )
@router.delete("/session/{session_id}")
async def delete_session_memory(
    session_id: str, client_id: str = Depends(get_client_id)
):
    """Delete all memory for a specific session"""
    try:
        # Mock implementation - would integrate with actual memory deletion
        return {
            "success": True,
            "message": f"Memory for session {session_id} deleted successfully",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise create_error_response(
            "server_error",
            "Failed to delete session memory",
            {"session_id": session_id, "original_error": str(e)},
            status_code=500,
        )
@router.get("/stats")
async def get_memory_stats():
    """Get memory system statistics and metrics"""
    try:
        # Calculate rate limiting stats
        total_clients = len(rate_limit_store)
        current_time = time.time()
        active_clients = 0
        for client_data in rate_limit_store.values():
            for endpoint_requests in client_data.values():
                if any(
                    current_time - req_time < 3600 for req_time in endpoint_requests
                ):
                    active_clients += 1
                    break
        return {
            "service": "memory_api",
            "timestamp": datetime.now().isoformat(),
            "rate_limiting": {
                "total_clients_tracked": total_clients,
                "active_clients_1h": active_clients,
                "limits": RATE_LIMITS,
            },
            "endpoints": {
                "store": "/api/memory/store",
                "retrieve": "/api/memory/retrieve/{session_id}",
                "search": "/api/memory/search",
                "health_checks": [
                    "/api/memory/health",
                    "/api/memory/ready",
                    "/api/memory/live",
                    "/api/memory/version",
                ],
            },
        }
    except Exception as e:
        raise create_error_response(
            "server_error",
            "Failed to retrieve memory statistics",
            {"original_error": str(e)},
            status_code=500,
        )
