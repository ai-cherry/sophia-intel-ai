from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class StoreRequest(BaseModel):
    namespace: str
    content: str
    metadata: Dict[str, Any] = {}


class SearchRequest(BaseModel):
    namespace: str
    query: str
    limit: int = 10


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
_r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="MCP Memory Server")


@app.get("/health")
async def health() -> Dict[str, Any]:
    try:
        pong = _r.ping()
    except Exception:
        pong = False
    return {"status": "ok" if pong else "degraded"}


@app.post("/memory/store")
async def memory_store(req: StoreRequest) -> Dict[str, Any]:
    item = {
        "content": req.content,
        "metadata": req.metadata,
        "timestamp": datetime.utcnow().isoformat(),
    }
    key = f"memory:{req.namespace}"
    _r.lpush(key, json.dumps(item))
    _r.ltrim(key, 0, 1000)
    return {"ok": True}


@app.post("/memory/search")
async def memory_search(req: SearchRequest) -> Dict[str, Any]:
    key = f"memory:{req.namespace}"
    raw = _r.lrange(key, 0, 1000)
    results: List[Dict[str, Any]] = []
    q = req.query.lower()
    for s in raw:
        item = json.loads(s)
        if q in item.get("content", "").lower():
            results.append(item)
        if len(results) >= req.limit:
            break
    return {"results": results}

