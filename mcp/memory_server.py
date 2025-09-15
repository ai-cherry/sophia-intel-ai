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
from config.python_settings import settings_from_env

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from time import perf_counter
import hmac
import hashlib as _hashlib
import json as _json
from collections import deque
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="MCP Memory Server")

# Redis connection (use DB 1 for memory)
_settings = settings_from_env()
REDIS_URL = _settings.REDIS_URL or os.getenv("REDIS_URL", "redis://localhost:6379/1")
redis_client: Optional[redis.Redis] = None

_mcp_jwt_secret = os.getenv("MCP_JWT_SECRET", "")
_mcp_audience = os.getenv("MCP_JWT_AUD", "memory")
_dev_bypass = (_settings.MCP_DEV_BYPASS == "1")
_rate_limit_rpm = int(_settings.RATE_LIMIT_RPM)
_rate_buckets: dict[str, deque] = {}

# Startup validation
if not _mcp_jwt_secret and not _dev_bypass:
    raise SystemExit("MCP_JWT_SECRET required for production. Set MCP_DEV_BYPASS=1 for development.")

# Metrics
REGISTRY = CollectorRegistry()
REQ_COUNTER = Counter("mcp_requests_total", "Total HTTP requests", ["server", "method", "path", "status"], registry=REGISTRY)
REQ_LATENCY = Histogram("mcp_request_latency_seconds", "Request latency seconds", ["server", "path"], registry=REGISTRY)


def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    import base64
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _verify_jwt_hs256(token: str, secret: str, aud: str) -> bool:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, _hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b64):
            return False
        payload = _json.loads(_b64url_decode(payload_b64))
        if "exp" in payload and int(payload["exp"]) < int(time.time()):
            return False
        pa = payload.get("aud")
        if isinstance(pa, list):
            return "memory" in pa or aud in pa
        if isinstance(pa, str):
            return pa in ("memory", aud)
        return False
    except Exception:
        return False


@app.middleware("http")
async def mcp_auth(request: Request, call_next):
    # Always allow health without auth
    if request.url.path in ("/health", "/metrics"):
        return await call_next(request)
    if not _mcp_jwt_secret:
        if _dev_bypass:
            return await call_next(request)
        return JSONResponse({"error": "MCP_JWT_SECRET required"}, status_code=401)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    token = auth.split(" ", 1)[1]
    if not _verify_jwt_hs256(token, _mcp_jwt_secret, _mcp_audience):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # Simple rate limiting per IP per minute (skip health/metrics)
    try:
        if _rate_limit_rpm > 0 and request.url.path not in ("/health", "/metrics"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            q = _rate_buckets.setdefault(ip, deque())
            # prune older than 60s
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= _rate_limit_rpm:
                return JSONResponse({"error": "rate_limited"}, status_code=429)
            q.append(now)
    except Exception:
        pass
    # Metrics timings
    start = perf_counter()
    resp = await call_next(request)
    try:
        REQ_COUNTER.labels("memory", request.method, request.url.path, str(resp.status_code)).inc()
        REQ_LATENCY.labels("memory", request.url.path).observe(perf_counter() - start)
    except Exception:
        pass
    return resp


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


@app.get("/metrics")
async def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


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


class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    limit: int = 20

@app.post("/search")
async def search_memory(req: SearchRequest):
    """Search across memory entries."""
    r = await get_redis()
    results: List[Dict[str, Any]] = []
    query = req.query
    session_id = req.session_id
    limit = req.limit
    
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
async def search_memory_alias(req: SearchRequest):
    return await search_memory(req=req)


# Compatibility endpoints for legacy clients (e.g., Agno MCP client)
# These mirror simple key/value semantics onto session-scoped memory.
class KVRequest(BaseModel):
    key: str
    value: Any | None = None


@app.post("/store")
async def kv_store(req: KVRequest):
    """Store a value under a session key, compatible with legacy /store.

    Maps to: POST /sessions/{key}/memory with content serialized.
    """
    content: str
    try:
        # Preserve strings as-is; serialize other types
        if isinstance(req.value, str):
            content = req.value
        else:
            content = json.dumps(req.value)
    except Exception:
        content = str(req.value)

    entry = MemoryEntry(content=content, role="assistant", metadata={"kv": True})
    result = await store_memory(session_id=req.key, entry=entry)
    return {"ok": True, "session": req.key, **result}


@app.get("/retrieve")
async def kv_retrieve(key: str):
    """Retrieve session memory for a key, compatible with legacy /retrieve.

    Returns the same structure as get_session_memory.
    """
    ctx = await get_session_memory(session_id=key, limit=100)
    return ctx


@app.delete("/delete")
async def kv_delete(key: str):
    """Delete all memory for a session key, compatible with legacy /delete."""
    r = await get_redis()
    # Remove timeline entries
    timeline_key = f"session:{key}:timeline"
    meta_key = f"session:{key}:meta"
    try:
        # Delete per-entry hashes referenced in the timeline
        ids = await r.lrange(timeline_key, 0, -1)
        if ids:
            await r.delete(*ids)
    except Exception:
        pass
    # Delete timeline and meta
    await r.delete(timeline_key)
    await r.delete(meta_key)
    # Also delete any stray memory:<key>:* entries
    try:
        cursor = 0
        pattern = f"memory:{key}:*"
        while True:
            cursor, keys = await r.scan(cursor, match=pattern, count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass
    return {"ok": True, "session": key, "deleted": True}


@app.get("/search")
async def kv_search(query: str, limit: int = 50):
    """GET-based search, compatible with legacy /search?query=..."""
    req = SearchRequest(query=query, limit=limit)
    return await search_memory(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
