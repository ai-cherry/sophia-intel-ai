"""
MCP Server - Main Application
Memory and tool management service with Model Context Protocol support.
Consolidated from enhanced_memory.py, supermemory_mcp.py, and enhanced_mcp_server.py
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import uvicorn
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from unified_memory import UnifiedMemorySystem

app = FastAPI(
    title="MCP Server - Memory & Tool Management",
    description="Unified memory service with Model Context Protocol support",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory system instance
memory_system = None

# Request/Response Models
class MemoryAddRequest(BaseModel):
    content: str
    topic: str
    source: str = "mcp-server"
    tags: List[str] = []
    memory_type: str = "semantic"

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10
    memory_type: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    systems: Dict[str, bool]
    version: str

@app.on_event("startup")
async def startup_event():
    """Initialize the unified memory system on startup."""
    global memory_system
    try:
        memory_system = UnifiedMemorySystem()
        await memory_system.initialize()
        print("✅ MCP Server: Unified memory system initialized")
    except Exception as e:
        print(f"❌ MCP Server: Failed to initialize memory system: {e}")
        # Don't fail startup, but log the error
        memory_system = None

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global memory_system
    if memory_system:
        await memory_system.cleanup()
        print("🧹 MCP Server: Memory system cleaned up")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    systems_status = {
        "memory_system": memory_system is not None,
        "sqlite_backend": True,  # Always available
        "redis_backend": os.getenv("REDIS_URL") is not None,
        "weaviate_backend": os.getenv("WEAVIATE_URL") is not None
    }
    
    return HealthResponse(
        status="healthy" if memory_system else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        systems=systems_status,
        version="2.0.0"
    )

@app.post("/mcp/memory/add")
async def add_memory(request: MemoryAddRequest):
    """Add entry to unified memory system."""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        result = await memory_system.add_memory(
            content=request.content,
            topic=request.topic,
            source=request.source,
            tags=request.tags,
            memory_type=request.memory_type
        )
        return {"status": "success", "id": result.get("id"), "message": "Memory added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")

@app.post("/mcp/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Search unified memory system."""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        results = await memory_system.search_memory(
            query=request.query,
            limit=request.limit,
            memory_type=request.memory_type
        )
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/mcp/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    if not memory_system:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        stats = await memory_system.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/mcp/memory/types")
async def get_memory_types():
    """Get supported memory types."""
    return {
        "supported_types": ["semantic", "episodic", "procedural"],
        "default": "semantic",
        "descriptions": {
            "semantic": "Factual knowledge and concepts",
            "episodic": "Specific events and experiences", 
            "procedural": "How-to knowledge and processes"
        }
    }

# Tool management endpoints
@app.get("/tools/list")
async def list_available_tools():
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "memory_add",
                "description": "Add content to memory",
                "parameters": ["content", "topic", "source", "tags", "memory_type"]
            },
            {
                "name": "memory_search", 
                "description": "Search memory content",
                "parameters": ["query", "limit", "memory_type"]
            },
            {
                "name": "memory_stats",
                "description": "Get memory system statistics",
                "parameters": []
            }
        ]
    }

@app.post("/tools/execute")
async def execute_tool(request: Dict[str, Any]):
    """Execute MCP tool."""
    tool_name = request.get("tool")
    params = request.get("parameters", {})
    
    if tool_name == "memory_add":
        add_req = MemoryAddRequest(**params)
        return await add_memory(add_req)
    elif tool_name == "memory_search":
        search_req = MemorySearchRequest(**params) 
        return await search_memory(search_req)
    elif tool_name == "memory_stats":
        return await get_memory_stats()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

if __name__ == "__main__":
    print("🚀 Starting MCP Server...")
    print("=" * 50)
    print("✅ Memory & Tool Management Service")
    print("✅ Model Context Protocol Support")
    print("✅ Unified Memory Backend")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("MCP_SERVER_PORT", "8004")),
        log_level="info"
    )