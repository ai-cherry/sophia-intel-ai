from __future__ import annotations
# Canonical MCP Vector server (port 8085): endpoints /health, /index, /search
import os
import time
import hashlib
import json
from typing import Any, Dict, Optional, List

import requests
from config.python_settings import settings_from_env
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
import time as _time
from time import perf_counter
from collections import deque
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST


_settings = settings_from_env()
WEAVIATE_URL = _settings.WEAVIATE_URL or os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
CLASS_NAME = os.getenv("VECTOR_CLASS", "BusinessDocument")

app = FastAPI(title="MCP Vector Server")
_mcp_token = _settings.MCP_TOKEN or os.getenv("MCP_TOKEN")
_dev_bypass = (_settings.MCP_DEV_BYPASS == "1")
_rate_limit_rpm = int(_settings.RATE_LIMIT_RPM)
_rate_buckets: dict[str, deque] = {}

# Metrics
REGISTRY = CollectorRegistry()
REQ_COUNTER = Counter("mcp_requests_total", "Total HTTP requests", ["server", "method", "path", "status"], registry=REGISTRY)
REQ_LATENCY = Histogram("mcp_request_latency_seconds", "Request latency seconds", ["server", "path"], registry=REGISTRY)

@app.middleware("http")
async def mcp_auth(request: Request, call_next):
    if request.url.path in ("/health", "/metrics"):
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
    # Rate limit
    try:
        if _rate_limit_rpm > 0 and request.url.path not in ("/health", "/metrics"):
            ip = request.client.host if request.client else "unknown"
            now = _time.time()
            q = _rate_buckets.setdefault(ip, deque())
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= _rate_limit_rpm:
                return JSONResponse({"error": "rate_limited"}, status_code=429)
            q.append(now)
    except Exception:
        pass
    start = perf_counter()
    resp = await call_next(request)
    try:
        REQ_COUNTER.labels("vector", request.method, request.url.path, str(resp.status_code)).inc()
        REQ_LATENCY.labels("vector", request.url.path).observe(perf_counter() - start)
    except Exception:
        pass
    return resp


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if WEAVIATE_API_KEY:
        h["Authorization"] = f"Bearer {WEAVIATE_API_KEY}"
    return h


def _weaviate_ready() -> bool:
    try:
        r = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _ensure_class() -> None:
    schema_url = f"{WEAVIATE_URL}/v1/schema"
    r = requests.get(schema_url, headers=_headers(), timeout=5)
    r.raise_for_status()
    classes = {c.get("class") for c in r.json().get("classes", [])}
    if CLASS_NAME in classes:
        return
    payload = {
        "class": CLASS_NAME,
        "vectorizer": "text2vec-openai",  # placeholder; Weaviate may ignore if not enabled
        "properties": [
            {"name": "path", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
            {"name": "contentHash", "dataType": ["text"]},
            {"name": "metadata", "dataType": ["text"]},
            {"name": "timestamp", "dataType": ["number"]},
        ],
    }
    cr = requests.post(f"{WEAVIATE_URL}/v1/schema/classes", headers=_headers(), data=json.dumps(payload), timeout=8)
    if cr.status_code not in (200, 201):
        raise HTTPException(500, f"Failed to create Weaviate class: {cr.text}")


class IndexRequest(BaseModel):
    path: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy" if _weaviate_ready() else "unhealthy",
        "weaviate": WEAVIATE_URL,
        "class": CLASS_NAME,
    }

@app.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/index")
def index_doc(req: IndexRequest) -> Dict[str, Any]:
    if not _weaviate_ready():
        raise HTTPException(503, "Weaviate not ready")
    if not (req.content or req.path):
        raise HTTPException(400, "Provide content or path")
    _ensure_class()
    content = req.content if req.content is not None else ""
    chash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    data = {
        "class": CLASS_NAME,
        "properties": {
            "path": req.path or "",
            "content": content,
            "contentHash": chash,
            "metadata": json.dumps(req.metadata or {}),
            "timestamp": time.time(),
        },
    }
    # Upsert via /objects (Weaviate will create a new object). For dedupe, delete existing with same hash first.
    try:
        # delete existing by contentHash
        del_payload = {"where": {"path": ["contentHash"], "operator": "Equal", "valueString": chash}}
        requests.post(f"{WEAVIATE_URL}/v1/objects/{CLASS_NAME}/delete", headers=_headers(), data=json.dumps(del_payload), timeout=8)
    except Exception:
        pass
    r = requests.post(f"{WEAVIATE_URL}/v1/objects", headers=_headers(), data=json.dumps(data), timeout=10)
    if r.status_code not in (200, 201):
        raise HTTPException(502, f"Weaviate upsert failed: {r.text}")
    return {"indexed": True, "hash": chash}


@app.post("/search")
def search(req: SearchRequest) -> Dict[str, Any]:
    if not _weaviate_ready():
        raise HTTPException(503, "Weaviate not ready")
    # Basic BM25 text search on content
    payload = {
        "query": f"{{ Get {{ {CLASS_NAME}(bm25: {{ query: \"{req.query}\" }}, limit: {req.limit}) {{ path content contentHash metadata }} }} }}"
    }
    r = requests.post(f"{WEAVIATE_URL}/v1/graphql", headers=_headers(), data=json.dumps(payload), timeout=8)
    if r.status_code != 200:
        raise HTTPException(502, f"Weaviate search failed: {r.text}")
    data = r.json().get("data", {}).get("Get", {}).get(CLASS_NAME, [])
    return {"results": data}
