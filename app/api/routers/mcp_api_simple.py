"""
Simple MCP API - Speed First, No Security Bloat
26% latency improvement without overkill
"""
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..mcp.streams_optimized import MCPStreamSystem, create_mcp_system
logger = logging.getLogger(__name__)
# Global system instance
mcp_system: Optional[MCPStreamSystem] = None
router = APIRouter(prefix="/api/mcp", tags=["MCP Streams"])
class StreamRequest(BaseModel):
    """Simple stream request"""
    user_id: str
    query: Optional[str] = None
    context: Optional[Dict] = None
class StreamResponse(BaseModel):
    """Simple stream response"""
    success: bool
    stream_id: Optional[str] = None
    data: Optional[Dict] = None
    latency_ms: Optional[float] = None
    message: str
async def get_mcp_system() -> MCPStreamSystem:
    """Get MCP system instance"""
    global mcp_system
    if mcp_system is None:
        mcp_system = await create_mcp_system(latency_target_ms=162)
    return mcp_system
@router.post("/stream", response_model=StreamResponse)
async def create_stream(request: StreamRequest):
    """Create stream - fast and simple"""
    try:
        system = await get_mcp_system()
        stream_id = await system.create_stream(request.user_id)
        return StreamResponse(
            success=True,
            stream_id=stream_id,
            message="Stream created successfully",
            data={
                "user_id": request.user_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Stream creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/query", response_model=StreamResponse)
async def query_stream(request: StreamRequest):
    """Execute BI query - optimized for speed"""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query required")
    try:
        system = await get_mcp_system()
        # Create stream if not provided
        if not hasattr(request, "stream_id") or not request.stream_id:
            stream_id = await system.create_stream(request.user_id)
        else:
            stream_id = request.stream_id
        # Process query
        result = await system.process_bi_query(
            stream_id=stream_id, query=request.query, context=request.context
        )
        return StreamResponse(
            success=result["success"],
            stream_id=stream_id,
            data=result.get("response"),
            latency_ms=result.get("latency_ms"),
            message=f"Query processed in {result.get('latency_ms', 0):.1f}ms",
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    try:
        system = await get_mcp_system()
        metrics = await system.get_metrics()
        return {
            "metrics": metrics,
            "evolution_status": "Phase 3 - Speed Optimized MCP",
            "target_improvement": "26% latency reduction",
            "security_approach": "minimal_overhead",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/stream/{stream_id}")
async def close_stream(stream_id: str):
    """Close stream"""
    try:
        system = await get_mcp_system()
        await system.close_stream(stream_id)
        return {"success": True, "message": "Stream closed"}
    except Exception as e:
        logger.error(f"Stream close failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/health")
async def health_check():
    """Simple health check"""
    try:
        system = await get_mcp_system()
        metrics = await system.get_metrics()
        return {
            "status": "healthy" if metrics["target_met"] else "optimizing",
            "latency_target_met": metrics["target_met"],
            "avg_latency_ms": metrics["avg_latency_ms"],
            "active_streams": metrics["active_streams"],
            "approach": "speed_first_minimal_security",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
