#!/usr/bin/env python3
"""
Test Memory Server for Sophia Intel AI
Minimal server to test memory endpoints functionality
"""
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Request models for memory endpoints
class MemoryStoreRequest(BaseModel):
    session_id: str
    messages: List[Dict]
    metadata: Optional[Dict] = None
class MemorySearchRequest(BaseModel):
    query: str
    filters: Optional[Dict] = None
    top_k: int = 10
class MemoryUpdateRequest(BaseModel):
    memory_id: str
    content: str
    metadata: Optional[Dict] = None
class MemoryDeleteRequest(BaseModel):
    memory_id: str
# Create test app
app = FastAPI(
    title="Sophia Memory Test Server",
    description="Test server for memory endpoints",
    version="1.0.0",
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# In-memory storage for testing
memory_store = {}
memory_counter = 1
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sophia Memory Test Server",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": {
            "api_memory_store": "/api/memory/store",
            "api_memory_retrieve": "/api/memory/retrieve/{session_id}",
            "mcp_memory_store": "/mcp/memory/store",
            "mcp_memory_search": "/mcp/memory/search",
            "mcp_memory_update": "/mcp/memory/update",
            "mcp_memory_delete": "/mcp/memory/delete",
        },
    }
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "memory_store_count": len(memory_store),
    }
# API Memory endpoints (from app/api/memory/memory_endpoints.py)
@app.post("/api/memory/store")
async def api_store_memory(request: MemoryStoreRequest):
    """Store memory via API endpoint"""
    global memory_counter
    memory_id = f"api_mem_{memory_counter}"
    memory_counter += 1
    memory_entry = {
        "id": memory_id,
        "session_id": request.session_id,
        "messages": request.messages,
        "metadata": request.metadata or {},
        "created_at": datetime.now().isoformat(),
        "type": "api_conversation",
    }
    memory_store[memory_id] = memory_entry
    return {
        "status": "success",
        "memory_id": memory_id,
        "message": f"Stored {len(request.messages)} messages for session {request.session_id}",
        "timestamp": datetime.now().isoformat(),
    }
@app.get("/api/memory/retrieve/{session_id}")
async def api_retrieve_memory(
    session_id: str, last_n: int = 10, include_system: bool = False
):
    """Retrieve memory via API endpoint"""
    # Find memories for this session
    session_memories = [
        mem for mem in memory_store.values() if mem.get("session_id") == session_id
    ]
    # Sort by creation time and limit
    session_memories.sort(key=lambda x: x["created_at"], reverse=True)
    recent_memories = session_memories[:last_n]
    return {
        "session_id": session_id,
        "memories": recent_memories,
        "total_found": len(session_memories),
        "returned": len(recent_memories),
        "timestamp": datetime.now().isoformat(),
    }
# MCP Memory endpoints (from app/api/unified_gateway.py)
@app.post("/mcp/memory/store")
async def mcp_store_memory(request: Dict):
    """Store memory via MCP endpoint"""
    global memory_counter
    memory_id = f"mcp_mem_{memory_counter}"
    memory_counter += 1
    memory_entry = {
        "id": memory_id,
        "content": request.get("content", ""),
        "metadata": request.get("metadata", {}),
        "created_at": datetime.now().isoformat(),
        "type": "mcp_content",
    }
    memory_store[memory_id] = memory_entry
    return {
        "status": "success",
        "memory_id": memory_id,
        "message": "MCP memory stored successfully",
        "timestamp": datetime.now().isoformat(),
    }
@app.post("/mcp/memory/search")
async def mcp_search_memory(request: MemorySearchRequest):
    """Search memory via MCP endpoint"""
    query_lower = request.query.lower()
    # Simple search through stored memories
    matches = []
    for memory in memory_store.values():
        content = ""
        if isinstance(memory.get("content"), str):
            content = memory["content"]
        elif isinstance(memory.get("messages"), list):
            content = " ".join(
                [
                    msg.get("content", "")
                    for msg in memory["messages"]
                    if isinstance(msg, dict)
                ]
            )
        if query_lower in content.lower():
            matches.append(
                {
                    "memory_id": memory["id"],
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "score": 1.0,  # Simple scoring
                    "metadata": memory.get("metadata", {}),
                    "created_at": memory["created_at"],
                }
            )
    # Sort by creation time and limit
    matches.sort(key=lambda x: x["created_at"], reverse=True)
    results = matches[: request.top_k]
    return {
        "results": results,
        "total_matches": len(matches),
        "query": request.query,
        "timestamp": datetime.now().isoformat(),
    }
@app.post("/mcp/memory/update")
async def mcp_update_memory(request: MemoryUpdateRequest):
    """Update memory via MCP endpoint"""
    if request.memory_id not in memory_store:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory = memory_store[request.memory_id]
    memory["content"] = request.content
    memory["metadata"] = request.metadata or memory.get("metadata", {})
    memory["updated_at"] = datetime.now().isoformat()
    return {
        "status": "success",
        "memory_id": request.memory_id,
        "message": "Memory updated successfully",
        "timestamp": datetime.now().isoformat(),
    }
@app.post("/mcp/memory/delete")
async def mcp_delete_memory(request: MemoryDeleteRequest):
    """Delete memory via MCP endpoint"""
    if request.memory_id not in memory_store:
        raise HTTPException(status_code=404, detail="Memory not found")
    del memory_store[request.memory_id]
    return {
        "status": "success",
        "memory_id": request.memory_id,
        "message": "Memory deleted successfully",
        "timestamp": datetime.now().isoformat(),
    }
# Test endpoint to show all stored memories
@app.get("/test/memories")
async def test_list_memories():
    """List all stored memories for testing"""
    return {
        "total_memories": len(memory_store),
        "memories": list(memory_store.values()),
        "timestamp": datetime.now().isoformat(),
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
