from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger
from config.config import settings
from .memory_service import MemoryService
import time

app = FastAPI(
    title="Sophia MCP Server",
    version="0.1.0",
    description="Model Context Protocol server for Sophia Intel platform",
)

# Initialize memory service
mem = MemoryService()


# Request/Response Models
class StoreContextRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Content to store")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata"
    )
    context_type: Optional[str] = Field(
        default="general", description="Type of context"
    )


class QueryContextRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Query string for context search")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    global_search: bool = Field(default=False, description="Search across all sessions")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )


class ContextResult(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    session_id: str
    timestamp: str


class StoreResponse(BaseModel):
    success: bool
    id: str
    message: str


class QueryResponse(BaseModel):
    success: bool
    results: List[ContextResult]
    query: str
    total_found: int


# Health endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        # Test memory service connection
        await mem.health_check()
        return {"status": "healthy", "timestamp": time.time(), "service": "mcp-server"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Store context endpoint
@app.post("/context/store", response_model=StoreResponse)
async def store_context(req: StoreContextRequest):
    """Store context in memory service."""
    try:
        logger.info(f"Storing context for session {req.session_id}")
        result = await mem.store_context(
            session_id=req.session_id,
            content=req.content,
            metadata={**req.metadata, "context_type": req.context_type},
        )

        return StoreResponse(
            success=True, id=str(result["id"]), message="Context stored successfully"
        )
    except Exception as e:
        logger.error(f"Failed to store context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Query context endpoint
@app.post("/context/query", response_model=QueryResponse)
async def query_context(req: QueryContextRequest):
    """Query context from memory service."""
    try:
        logger.info(
            f"Querying context for session {req.session_id}: {req.query[:50]}..."
        )
        results = await mem.query_context(
            session_id=req.session_id,
            query=req.query,
            top_k=req.top_k,
            global_search=req.global_search,
            threshold=req.threshold,
        )

        # Convert results to response format
        context_results = [
            ContextResult(
                id=str(r.get("id", "")),
                content=r.get("content", ""),
                metadata=r.get("metadata", {}),
                score=r.get("score", 0.0),
                session_id=r.get("session_id", ""),
                timestamp=r.get("timestamp", ""),
            )
            for r in results
        ]

        return QueryResponse(
            success=True,
            results=context_results,
            query=req.query,
            total_found=len(context_results),
        )
    except Exception as e:
        logger.error(f"Failed to query context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Clear session context endpoint
@app.delete("/context/session/{session_id}")
async def clear_session_context(session_id: str):
    """Clear all context for a specific session."""
    try:
        logger.info(f"Clearing context for session {session_id}")
        result = await mem.clear_session(session_id)
        return {"success": True, "deleted_count": result.get("deleted_count", 0)}
    except Exception as e:
        logger.error(f"Failed to clear session context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get session statistics endpoint
@app.get("/context/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get statistics for a specific session."""
    try:
        stats = await mem.get_session_stats(session_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500, content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.MCP_PORT)
