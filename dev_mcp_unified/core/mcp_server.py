from __future__ import annotations
import asyncio
import os
import uuid
from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from dev_mcp_unified.core.context_engine import ContextEngine
from dev_mcp_unified.core.job_queue import Job, JobQueue
from dev_mcp_unified.core.simple_key_manager import get_key, KeyProvider
from dev_mcp_unified.llm_adapters.base_adapter import LLMRequest
from dev_mcp_unified.llm_adapters.claude_adapter import ClaudeAdapter
from dev_mcp_unified.llm_adapters.openai_adapter import OpenAIAdapter
from dev_mcp_unified.llm_adapters.qwen_adapter import QwenAdapter
from dev_mcp_unified.llm_adapters.deepseek_adapter import DeepSeekAdapter
from dev_mcp_unified.llm_adapters.openrouter_adapter import OpenRouterAdapter
from dev_mcp_unified.tools.semantic_search import semantic_search
from dev_mcp_unified.tools.symbol_lookup import symbol_lookup
from dev_mcp_unified.tools.test_runner import run_tests
from dev_mcp_unified.tools.doc_extractor import extract_docs
from dev_mcp_unified.embeddings.local_provider import LocalDeterministicEmbedding
from dev_mcp_unified.embeddings.openai_provider import OpenAIEmbedding
from dev_mcp_unified.storage.vector_store import InMemoryVectorStore, ChromaVectorStore
from dev_mcp_unified.indexing.indexer import index_path
import httpx
from starlette.responses import StreamingResponse
from datetime import datetime, timedelta


app = FastAPI(title="MCP Unified Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = ContextEngine(repo_root=os.getenv("MCP_INDEX_PATH"))
queue = JobQueue(workers=2)
_embedder = None
_vstore = None


class QueryRequest(BaseModel):
    task: str = "general"
    question: str
    llm: Optional[str] = None
    model: Optional[str] = None  # Specific model override
    file: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@app.on_event("startup")
async def on_start():
    await queue.start()
    # Initialize embeddings + vector store (Chroma if available; else in-memory)
    global _embedder, _vstore
    # Provider selection: OpenAI default, then Ollama, then deterministic
    if os.getenv("OPENAI_API_KEY"):
        _embedder = OpenAIEmbedding(api_key=os.getenv("OPENAI_API_KEY"))
    else:
        # Try local Ollama as a fallback
        try:
            import asyncio
            async def _probe():
                async with httpx.AsyncClient(timeout=2.0) as c:
                    await c.get("http://127.0.0.1:11434/api/tags")
            asyncio.get_event_loop().run_until_complete(_probe())
            from dev_mcp_unified.embeddings.ollama_provider import OllamaEmbedding
            _embedder = OllamaEmbedding(model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
        except Exception:
            _embedder = LocalDeterministicEmbedding(dims=256)

    # Vector store: prefer Chroma (open-source) if installed
    try:
        _vstore = ChromaVectorStore(dims=_embedder.dims)
    except Exception:
        _vstore = InMemoryVectorStore(dims=_embedder.dims)


@app.get("/healthz")
def healthz():
    count = None
    try:
        if hasattr(_vstore, "_col"):
            count = _vstore._col.count()
    except Exception:
        count = None
    return {"status": "ok", "watch": bool(os.getenv("MCP_WATCH")), "index": os.getenv("MCP_INDEX_PATH"), "vectors": count}


@app.post("/query")
async def query(req: QueryRequest):
    action = engine.select_action(req.task)
    provider = (req.llm or action.get("provider") or "claude").lower()
    strategy = action.get("context_strategy", "snippet_with_completions")
    ctx = engine.build_context(strategy, target_file=req.file)
    adapters = {
        "claude": ClaudeAdapter(get_key(KeyProvider.ANTHROPIC) or os.getenv("ANTHROPIC_API_KEY")),
        "openai": OpenAIAdapter(get_key(KeyProvider.OPENAI)),
        "qwen": QwenAdapter(get_key(KeyProvider.QWEN)),
        "deepseek": DeepSeekAdapter(get_key(KeyProvider.DEEPSEEK)),
        "openrouter": OpenRouterAdapter(os.getenv("OPENROUTER_API_KEY")),
    }
    adapter = adapters.get(provider, adapters["claude"]) 
    
    # Add model selection to context
    context = asdict(ctx)
    if req.model:
        context['model'] = req.model
    context['task'] = req.task
    
    llm_req = LLMRequest(
        prompt=req.question, 
        context=context,
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    resp = await adapter.complete(llm_req)
    return asdict(resp)


@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    """Streaming endpoint for real-time responses"""
    async def generate():
        action = engine.select_action(req.task)
        provider = (req.llm or action.get("provider") or "claude").lower()
        strategy = action.get("context_strategy", "snippet_with_completions")
        ctx = engine.build_context(strategy, target_file=req.file)
        
        # Prepare adapter
        adapters = {
            "claude": ClaudeAdapter(get_key(KeyProvider.ANTHROPIC) or os.getenv("ANTHROPIC_API_KEY")),
            "openai": OpenAIAdapter(get_key(KeyProvider.OPENAI)),
            "qwen": QwenAdapter(get_key(KeyProvider.QWEN)),
            "deepseek": DeepSeekAdapter(get_key(KeyProvider.DEEPSEEK)),
            "openrouter": OpenRouterAdapter(os.getenv("OPENROUTER_API_KEY")),
        }
        adapter = adapters.get(provider, adapters["claude"])
        
        # Add model selection to context
        context = asdict(ctx)
        if req.model:
            context['model'] = req.model
        context['task'] = req.task
        
        # Send initial metadata
        yield f"data: {json.dumps({'type': 'start', 'provider': provider, 'task': req.task, 'model': req.model})}\n\n"
        
        # Get response (for now, non-streaming - can be enhanced)
        llm_req = LLMRequest(
            prompt=req.question, 
            context=context,
            max_tokens=req.max_tokens,
            temperature=req.temperature
        )
        resp = await adapter.complete(llm_req)
        
        # Stream the response in chunks for UI effect
        text = resp.text
        chunk_size = 20  # chars per chunk
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
            await asyncio.sleep(0.01)  # Small delay for streaming effect
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done', 'usage': resp.usage})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


class RunJobRequest(BaseModel):
    kind: str
    payload: Dict[str, Any] = {}


@app.post("/background/run")
async def background_run(req: RunJobRequest):
    job = Job(id=str(uuid.uuid4()), kind=req.kind, payload=req.payload)
    def do_index(j: Job):
        root = j.payload.get("path") or os.getenv("MCP_INDEX_PATH") or os.getcwd()
        if _embedder and _vstore:
            stats = index_path(root, _embedder, _vstore)
            j.log.append(f"indexed {stats['added']} chunks from {root}")
        else:
            j.log.append("indexing unavailable (no embedder/store)")
    queue.register("index", do_index)
    queue.register("tests", lambda j: j.log.extend(run_tests(j.payload.get("path","."))))
    queue.register("static_analysis", lambda j: j.log.append("analysis stub"))
    await queue.enqueue(job)
    return {"job_id": job.id}


@app.get("/background/list")
def background_list():
    return [{"id": j.id, "kind": j.kind, "status": j.status} for j in queue.jobs.values()]


@app.get("/background/logs")
def background_logs(job_id: str):
    j = queue.jobs.get(job_id)
    if not j:
        return {"error":"not_found"}
    return {"id": j.id, "status": j.status, "log": j.log}


@app.post("/tools/search")
def tool_search(body: Dict[str, Any]):
    return {"results": semantic_search(body.get("query",""), root=os.getenv("MCP_INDEX_PATH") or ".")}


@app.post("/tools/vec_search")
def tool_vec_search(body: Dict[str, Any]):
    """Vector search against open-source vector DB (Chroma if available)."""
    query = body.get("query", "")
    if not query:
        return {"results": []}
    if not (_embedder and _vstore):
        return {"results": [], "error": "vector store not initialized"}
    qvec = _embedder.embed_batch([query])[0]
    hits = _vstore.query(qvec, top_k=int(body.get("k", 5)))
    return {"results": hits}


class ORChatRequest(BaseModel):
    model: str
    messages: list[dict]
    temperature: float | None = None
    max_tokens: int | None = None


@app.post("/proxy/openrouter")
async def proxy_openrouter(req: ORChatRequest):
    """Server-side proxy to OpenRouter chat/completions to avoid exposing keys in the browser."""
    or_key = os.getenv("OPENROUTER_API_KEY")
    if not or_key:
        return {"error": "missing OPENROUTER_API_KEY"}
    payload = {
        "model": req.model,
        "messages": req.messages,
    }
    if req.temperature is not None:
        payload["temperature"] = req.temperature
    if req.max_tokens is not None:
        payload["max_tokens"] = req.max_tokens
    headers = {
        "Authorization": f"Bearer {or_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        try:
            data = resp.json()
        except Exception:
            return {"error": f"openrouter bad response {resp.status_code}", "text": resp.text[:400]}
    # capture rate limit headers if present
    rate = {k.lower(): v for k, v in resp.headers.items() if k.lower().startswith("x-ratelimit")}
    # normalize to minimal shape used by UI
    content = None
    try:
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        pass
    return {"raw": data, "text": content, "rate": rate}


@app.post("/proxy/openrouter/stream")
async def proxy_openrouter_stream(req: ORChatRequest):
    """SSE stream from OpenRouter to the browser."""
    or_key = os.getenv("OPENROUTER_API_KEY")
    if not or_key:
        async def bad():
            yield b"event: error\n"
            yield b"data: missing OPENROUTER_API_KEY\n\n"
        return StreamingResponse(bad(), media_type="text/event-stream")

    async def gen():
        headers = {
            "Authorization": f"Bearer {or_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": req.model, "messages": req.messages, "stream": True}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as r:
                # forward chunks
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    yield (f"data: {line}\n\n").encode()
                # at end, send rate meta if present
                rate = {k.lower(): v for k, v in r.headers.items() if k.lower().startswith("x-ratelimit")}
                if rate:
                    import json as _json
                    meta = _json.dumps({"meta": {"rate": rate}})
                    yield (f"data: {meta}\n\n").encode()
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/index/stats")
def index_stats():
    try:
        if hasattr(_vstore, "_col"):
            return {"count": _vstore._col.count(), "store": "chroma"}
    except Exception as e:
        return {"error": str(e)}
    return {"count": None, "store": "memory"}


# --- Business: Gong integration (basic recent calls) ---
def _gong_auth_header() -> dict:
    ak = os.getenv("GONG_ACCESS_KEY")
    cs = os.getenv("GONG_CLIENT_SECRET")
    if not ak or not cs:
        return {}
    import base64
    token = base64.b64encode(f"{ak}:{cs}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@app.get("/business/gong/recent")
async def gong_recent(days: int = 7):
    base = os.getenv("GONG_BASE_URL", "https://api.gong.io")
    headers = _gong_auth_header()
    if not headers:
        return {"error": "missing GONG_ACCESS_KEY/GONG_CLIENT_SECRET"}
    start = (datetime.utcnow() - timedelta(days=max(1, days))).strftime("%Y-%m-%d")
    url = f"{base}/v2/calls?fromDate={start}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, headers=headers)
            data = r.json()
            # Normalize minimal shape
            calls = data.get("calls") or data.get("items") or data
            out = []
            for c in (calls if isinstance(calls, list) else []):
                out.append({
                    "callId": c.get("id") or c.get("callId"),
                    "date": c.get("startTime") or c.get("date"),
                    "topic": c.get("title") or c.get("topic"),
                    "durationSec": c.get("durationSeconds") or c.get("duration"),
                    "participants": c.get("participants"),
                })
            return {"fromDate": start, "count": len(out), "calls": out[:50]}
    except Exception as e:
        return {"error": str(e)}


@app.post("/tools/symbols")
def tool_symbols(body: Dict[str, Any]):
    return symbol_lookup(body.get("file"))


@app.post("/tools/tests")
def tool_tests(body: Dict[str, Any]):
    return {"log": run_tests(body.get("path","."))}


@app.post("/tools/docs")
def tool_docs(body: Dict[str, Any]):
    return extract_docs(body.get("file"))
