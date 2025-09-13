"""
MCP Memory Server with Redis persistence.
Provides session memory, context management, and embeddings for all agents.
"""

import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="MCP Memory Server")

# Redis connection (use DB 1 for memory)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
redis_client: Optional[redis.Redis] = None

# Minimal auth scaffolding (optional):
# If MCP_TOKEN is set, require Authorization: Bearer <token>.
# If not set and MCP_DEV_BYPASS=true, allow unauthenticated (dev-friendly).
_mcp_token = os.getenv("MCP_TOKEN")
_dev_bypass = os.getenv("MCP_DEV_BYPASS", "false").lower() in ("1", "true", "yes")


@app.middleware("http")
async def mcp_auth(request: Request, call_next):
    # Always allow health without auth
    if request.url.path == "/health":
        return await call_next(request)
    if not _mcp_token:
        if _dev_bypass:
            return await call_next(request)
        return JSONResponse({"error": "MCP_TOKEN not set"}, status_code=401)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    token = auth.split(" ", 1)[1]
    if token != _mcp_token:
        return JSONResponse({"error": "Invalid token"}, status_code=401)
    return await call_next(request)


class MemoryEntry(BaseModel):
    """Memory entry with content and metadata."""
    content: str
    role: str = "user"
    timestamp: Optional[float] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SessionContext(BaseModel):
    """Session context with memory entries."""
    session_id: str
    entries: List[MemoryEntry] = []
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = {}


async def get_redis() -> redis.Redis:
    """Get or create Redis connection."""
    global redis_client
    if not redis_client:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup."""
    await get_redis()


@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        r = await get_redis()
        await r.ping()
        return {"status": "healthy", "server": "memory", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "server": "memory", "error": str(e)}


@app.post("/sessions/{session_id}/memory")
async def store_memory(session_id: str, entry: MemoryEntry):
    """Store a memory entry in a session."""
    r = await get_redis()
    
    # Set timestamp if not provided
    if entry.timestamp is None:
        entry.timestamp = time.time()
    
    entry.session_id = session_id
    
    # Create memory ID
    memory_id = f"memory:{session_id}:{int(entry.timestamp * 1000)}"
    
    # Store entry
    entry_data = entry.model_dump()
    await r.hset(memory_id, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                                      for k, v in entry_data.items()})
    
    # Add to session timeline
    await r.lpush(f"session:{session_id}:timeline", memory_id)
    
    # Update session metadata
    await r.hset(f"session:{session_id}:meta", mapping={
        "updated_at": str(time.time()),
        "entry_count": str(await r.llen(f"session:{session_id}:timeline"))
    })
    
    # Set expiry (7 days)
    await r.expire(memory_id, 604800)
    await r.expire(f"session:{session_id}:timeline", 604800)
    
    return {"memory_id": memory_id, "stored": True}


@app.get("/sessions/{session_id}/memory")
async def get_session_memory(session_id: str, limit: int = 50) -> SessionContext:
    """Get memory entries for a session."""
    r = await get_redis()
    
    # Get timeline
    timeline = await r.lrange(f"session:{session_id}:timeline", 0, limit - 1)
    
    if not timeline:
        # Create new session
        meta = {
            "created_at": str(time.time()),
            "updated_at": str(time.time()),
            "entry_count": "0"
        }
        await r.hset(f"session:{session_id}:meta", mapping=meta)
        return SessionContext(
            session_id=session_id,
            entries=[],
            created_at=float(meta["created_at"]),
            updated_at=float(meta["updated_at"])
        )
    
    # Get entries
    entries = []
    for memory_id in timeline:
        data = await r.hgetall(memory_id)
        if data:
            entry = MemoryEntry(
                content=data.get("content", ""),
                role=data.get("role", "user"),
                timestamp=float(data.get("timestamp", 0)),
                session_id=data.get("session_id", session_id),
                metadata=json.loads(data.get("metadata", "{}"))
            )
            entries.append(entry)
    
    # Get metadata
    meta = await r.hgetall(f"session:{session_id}:meta")
    
    return SessionContext(
        session_id=session_id,
        entries=entries,
        created_at=float(meta.get("created_at", 0)),
        updated_at=float(meta.get("updated_at", 0)),
        metadata={"entry_count": int(meta.get("entry_count", 0))}
    )


@app.delete("/sessions/{session_id}/memory")
async def clear_session_memory(session_id: str):
    """Clear all memory for a session."""
    r = await get_redis()
    
    # Get all memory IDs
    timeline = await r.lrange(f"session:{session_id}:timeline", 0, -1)
    
    # Delete all entries
    if timeline:
        await r.delete(*timeline)
    
    # Delete session data
    await r.delete(f"session:{session_id}:timeline")
    await r.delete(f"session:{session_id}:meta")
    
    return {"cleared": True, "entries_removed": len(timeline)}


@app.get("/sessions")
async def list_sessions(limit: int = 100) -> List[Dict[str, Any]]:
    """List all active sessions."""
    r = await get_redis()
    
    # Find all session meta keys
    sessions = []
    cursor = 0
    pattern = "session:*:meta"
    
    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        
        for key in keys:
            session_id = key.split(":")[1]
            meta = await r.hgetall(key)
            
            if meta:
                sessions.append({
                    "session_id": session_id,
                    "created_at": float(meta.get("created_at", 0)),
                    "updated_at": float(meta.get("updated_at", 0)),
                    "entry_count": int(meta.get("entry_count", 0))
                })
        
        if cursor == 0 or len(sessions) >= limit:
            break
    
    # Sort by updated_at desc
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return sessions[:limit]


@app.post("/search")
async def search_memory(query: str, session_id: Optional[str] = None, limit: int = 20):
    """Search across memory entries."""
    r = await get_redis()
    results = []
    
    # Determine search scope
    if session_id:
        patterns = [f"memory:{session_id}:*"]
    else:
        patterns = ["memory:*"]
    
    for pattern in patterns:
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                data = await r.hgetall(key)
                if data and query.lower() in data.get("content", "").lower():
                    results.append({
                        "memory_id": key,
                        "content": data.get("content", ""),
                        "role": data.get("role", "user"),
                        "timestamp": float(data.get("timestamp", 0)),
                        "session_id": data.get("session_id", "")
                    })
            
            if cursor == 0 or len(results) >= limit:
                break
    
    # Sort by timestamp desc
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"results": results[:limit], "query": query}


# Compatibility alias for clients expecting a namespaced memory search route
@app.post("/memory/search")
async def search_memory_alias(query: str, session_id: Optional[str] = None, limit: int = 20):
    return await search_memory(query=query, session_id=session_id, limit=limit)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
