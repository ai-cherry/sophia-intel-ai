from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis

try:
    import weaviate
    from weaviate.classes.query import Filter
except Exception:  # optional
    weaviate = None
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
WEAVIATE_URL = os.getenv("WEAVIATE_URL", None)
_r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
_wv: Optional[weaviate.WeaviateClient] = None
if WEAVIATE_URL and weaviate is not None:
    try:
        _wv = weaviate.connect_to_local(
            host=WEAVIATE_URL.replace("http://", "").replace("https://", "")
        )
    except Exception:
        _wv = None

CLASS_NAME = "MemoryItem"

app = FastAPI(title="MCP Memory Server")


@app.get("/health")
async def health() -> Dict[str, Any]:
    try:
        pong = _r.ping()
    except Exception:
        pong = False
    wv = False
    if _wv is not None:
        try:
            _ = _wv.is_ready()
            wv = True
        except Exception:
            wv = False
    return {"status": "ok" if pong else "degraded", "weaviate": wv}


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
    # Optional: upsert into Weaviate for semantic/BM25 search
    if _wv is not None:
        try:
            # Ensure class exists (BM25-ready)
            if CLASS_NAME not in _wv.collections.list_all():
                _wv.collections.create(
                    CLASS_NAME,
                    vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
                    properties=[
                        weaviate.classes.config.Property(
                            name="content", data_type=weaviate.classes.config.DataType.TEXT
                        ),
                        weaviate.classes.config.Property(
                            name="namespace", data_type=weaviate.classes.config.DataType.TEXT
                        ),
                        weaviate.classes.config.Property(
                            name="metadata", data_type=weaviate.classes.config.DataType.TEXT
                        ),
                        weaviate.classes.config.Property(
                            name="timestamp", data_type=weaviate.classes.config.DataType.TEXT
                        ),
                    ],
                )
            coll = _wv.collections.get(CLASS_NAME)
            coll.data.insert(
                {
                    "content": req.content,
                    "namespace": req.namespace,
                    "metadata": json.dumps(req.metadata),
                    "timestamp": item["timestamp"],
                }
            )
        except Exception:
            pass
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
    # Optionally augment from Weaviate BM25
    if _wv is not None and len(results) < req.limit:
        try:
            coll = _wv.collections.get(CLASS_NAME)
            resp = coll.query.bm25(
                query=req.query,
                limit=req.limit,
                filters=Filter.by_property("namespace").equal(req.namespace),
            )
            for o in resp.objects or []:
                content = o.properties.get("content", "")
                metadata = o.properties.get("metadata")
                ts = o.properties.get("timestamp")
                item = {
                    "content": content,
                    "metadata": json.loads(metadata) if metadata else {},
                    "timestamp": ts,
                }
                if all(item.get("content") != r.get("content") for r in results):
                    results.append(item)
                if len(results) >= req.limit:
                    break
        except Exception:
            pass
    return {"results": results}
