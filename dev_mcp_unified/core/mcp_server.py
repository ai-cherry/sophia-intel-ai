from __future__ import annotations
import asyncio
import os
import uuid
import shutil
import hashlib
import sqlite3
import time
import subprocess
import re
import secrets
from dataclasses import asdict
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import jwt
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

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


@app.get("/")
def root():
    return {"status": "ok", "app": "mcp-unified", "docs": "/docs"}


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
    """Server-side proxy to OpenRouter chat/completions with repository context."""
    or_key = os.getenv("OPENROUTER_API_KEY")
    if not or_key:
        return {"error": "missing OPENROUTER_API_KEY"}
    
    # Enhance messages with repository context via vector search and context engine
    messages = req.messages.copy()
    if messages and len(messages) > 0:
        last_msg = messages[-1].get("content", "")
        
        # Use vector search if available
        try:
            from app.indexing.vector_store import VectorStore
            store = VectorStore()
            # Get embeddings for the query
            results = store.search(last_msg, k=10)
            if results:
                context_msg = "\n[Repository Context from Vector Search]\n"
                for r in results:
                    context_msg += f"- {r['file']}: {r['snippet'][:200]}...\n"
                messages.insert(0, {"role": "system", "content": context_msg})
        except Exception:
            pass
        
        # Use context engine for structured context
        try:
            ctx_engine = ContextEngine(repo_root="/Users/lynnmusil/sophia-intel-ai")
            # Determine task type from message
            task = "code_analysis" if "swarm" in last_msg.lower() else "general"
            action = ctx_engine.select_action(task)
            
            # Build context bundle
            strategy = action.get("context_strategy", "snippet_with_completions")
            bundle = ctx_engine.build_context(strategy)
            
            if bundle.files:
                context_msg = f"\n[Repository Structure - Strategy: {strategy}]\n"
                for file_path, content in bundle.files.items():
                    context_msg += f"\nFile: {file_path}\n{content[:500]}...\n"
                messages.insert(0, {"role": "system", "content": context_msg})
        except Exception:
            pass
        
        # Fallback to semantic search
        code_keywords = ["code", "repository", "function", "class", "swarm", "implement", "file", "module", "agent", "orchestr"]
        if any(kw in last_msg.lower() for kw in code_keywords):
            # Extract key terms for search
            import re
            terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*|[a-z]+', last_msg)
            important_terms = [t for t in terms if len(t) > 3 and t.lower() not in ["what", "where", "which", "how", "when", "that", "this", "with", "exists"]]
            
            all_results = []
            for term in important_terms[:3]:
                results = semantic_search(term, root="/Users/lynnmusil/sophia-intel-ai")
                all_results.extend(results[:5])
            
            if all_results:
                context_msg = "\n[Repository Context - Files in /Users/lynnmusil/sophia-intel-ai]\n"
                seen = set()
                for r in all_results[:15]:
                    if r['file'] not in seen:
                        seen.add(r['file'])
                        context_msg += f"- {r['file']}\n"
                context_msg += "\nYou are analyzing the sophia-intel-ai repository. Answer based on the actual files listed above.\n"
                messages.insert(0, {"role": "system", "content": context_msg})
                print(f"Added context with {len(seen)} files")
    
    payload = {
        "model": req.model,
        "messages": messages,
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
        msg = data.get("choices", [{}])[0].get("message", {})
        content = msg.get("content")
        if not content:
            # Some providers place output in 'reasoning' or 'reasoning_details'
            content = msg.get("reasoning")
            if not content:
                details = msg.get("reasoning_details")
                if isinstance(details, list) and details:
                    # concatenate any reasoning.text fragments
                    parts = []
                    for d in details:
                        t = d.get("text") or d.get("content")
                        if t:
                            parts.append(t)
                    if parts:
                        content = "".join(parts)
    except Exception:
        content = None
    return {"raw": data, "text": content or "", "rate": rate}


@app.post("/proxy/openrouter/stream")
async def proxy_openrouter_stream(req: ORChatRequest):
    """SSE stream from OpenRouter to the browser with repository context."""
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
        
        # Enhance messages with repository context via vector search and context engine
        messages = req.messages.copy()
        if messages and len(messages) > 0:
            last_msg = messages[-1].get("content", "")
            
            # Use vector search if available
            try:
                from app.indexing.vector_store import VectorStore
                store = VectorStore()
                # Get embeddings for the query
                results = store.search(last_msg, k=10)
                if results:
                    context_msg = "\n[Repository Context from Vector Search]\n"
                    for r in results:
                        context_msg += f"- {r['file']}: {r['snippet'][:200]}...\n"
                    messages.insert(0, {"role": "system", "content": context_msg})
            except Exception:
                pass
            
            # Use context engine for structured context
            try:
                ctx_engine = ContextEngine(repo_root="/Users/lynnmusil/sophia-intel-ai")
                # Determine task type from message
                task = "code_analysis" if "swarm" in last_msg.lower() else "general"
                action = ctx_engine.select_action(task)
                
                # Build context bundle
                strategy = action.get("context_strategy", "snippet_with_completions")
                bundle = ctx_engine.build_context(strategy)
                
                if bundle.files:
                    context_msg = f"\n[Repository Structure - Strategy: {strategy}]\n"
                    for file_path, content in bundle.files.items():
                        context_msg += f"\nFile: {file_path}\n{content[:500]}...\n"
                    messages.insert(0, {"role": "system", "content": context_msg})
            except Exception:
                pass
            
            # Fallback to semantic search
            code_keywords = ["code", "repository", "function", "class", "swarm", "implement", "file", "module", "agent", "orchestr"]
            if any(kw in last_msg.lower() for kw in code_keywords):
                # Extract key terms for search
                import re
                terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*|[a-z]+', last_msg)
                important_terms = [t for t in terms if len(t) > 3 and t.lower() not in ["what", "where", "which", "how", "when", "that", "this", "with", "exists"]]
                
                all_results = []
                for term in important_terms[:3]:
                    results = semantic_search(term, root="/Users/lynnmusil/sophia-intel-ai")
                    all_results.extend(results[:5])
                
                if all_results:
                    context_msg = "\n[Repository Context - Files in /Users/lynnmusil/sophia-intel-ai]\n"
                    seen = set()
                    for r in all_results[:15]:
                        if r['file'] not in seen:
                            seen.add(r['file'])
                            context_msg += f"- {r['file']}\n"
                    context_msg += "\nYou are analyzing the sophia-intel-ai repository. Answer based on the actual files listed above.\n"
                    messages.insert(0, {"role": "system", "content": context_msg})
                    print(f"Added context with {len(seen)} files")
        
        payload = {"model": req.model, "messages": messages, "stream": True}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as r:
                # forward chunks
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    # Skip SSE comments (lines starting with ':')
                    if line.startswith(':'):
                        continue
                    # Already has "data:" prefix from OpenRouter
                    if line.startswith('data:'):
                        yield (f"{line}\n\n").encode()
                    else:
                        yield (f"data: {line}\n\n").encode()
                # at end, send rate meta if present
                rate = {k.lower(): v for k, v in r.headers.items() if k.lower().startswith("x-ratelimit")}
                if rate:
                    import json as _json
                    meta = _json.dumps({"meta": {"rate": rate}})
                    yield (f"data: {meta}\n\n").encode()
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/proxy/openrouter/models")
async def proxy_openrouter_models():
    """List available models from OpenRouter with enhanced metadata."""
    or_key = os.getenv("OPENROUTER_API_KEY")
    if not or_key:
        return {"error": "missing OPENROUTER_API_KEY", "models": []}
    headers = {
        "Authorization": f"Bearer {or_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
            data = r.json()
            # Normalize to enhanced set with categorization
            items = data.get("data") or data.get("models") or []
            models = []
            
            # Categorization helpers
            capability_patterns = {
                "code": ["code", "coder", "codestral", "starcoder"],
                "vision": ["vision", "4v", "multimodal", "gemini-pro-vision"],
                "reasoning": ["o1", "reasoning", "think", "r1"],
                "fast": ["fast", "turbo", "flash", "haiku", "mini"],
                "long_context": ["32k", "64k", "128k", "200k", "turbo-128k"],
            }
            
            for it in items:
                mid = it.get("id") or it.get("name")
                if not mid:
                    continue
                    
                # Detect capabilities
                mid_lower = mid.lower()
                capabilities = []
                for cap, patterns in capability_patterns.items():
                    if any(p in mid_lower for p in patterns):
                        capabilities.append(cap)
                if not capabilities:
                    capabilities.append("chat")
                
                # Parse pricing
                pricing = {}
                if it.get("pricing"):
                    pricing = {
                        "prompt": float(it["pricing"].get("prompt", 0)) * 1000000,
                        "completion": float(it["pricing"].get("completion", 0)) * 1000000
                    }
                
                models.append({
                    "id": mid,
                    "name": it.get("name") or mid,
                    "context": it.get("context_length") or it.get("context_length_tokens"),
                    "provider": (it.get("owned_by") or '').split('/')[0] if it.get("owned_by") else mid.split('/')[0] if '/' in mid else None,
                    "capabilities": capabilities,
                    "is_free": ":free" in mid.lower() or pricing.get("prompt", 1) == 0,
                    "pricing": pricing,
                    "max_tokens": it.get("top_provider", {}).get("max_completion_tokens")
                })
            
            # Sort by provider and name
            models.sort(key=lambda x: (x.get("provider", ""), x.get("name", "")))
            
            return {"count": len(models), "models": models}
    except Exception as e:
        return {"error": str(e), "models": []}


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


@app.get("/routes")
def list_routes():
    try:
        routes = []
        for r in app.routes:
            routes.append({"path": getattr(r, 'path', None), "name": getattr(r, 'name', None)})
        return {"count": len(routes), "routes": routes}
    except Exception as e:
        return {"error": str(e)}


# ---- Sophia Business: signals, leads, message preview, analytics (stubs) ----
@app.get("/business/signals")
async def business_signals():
    # stubbed signals; replace with UserGems/HubSpot wiring next
    now = datetime.utcnow().isoformat()
    items = [
        {"id": "sig-001", "source": "usergems", "person": "Alex Lee", "title": "VP Sales", "company": "Acme Corp", "signalType": "PastChampion", "signalStrength": 0.92, "updatedAt": now},
        {"id": "sig-002", "source": "usergems", "person": "Sam Patel", "title": "Dir Ops", "company": "Northwind", "signalType": "NewRole", "signalStrength": 0.78, "updatedAt": now},
        {"id": "sig-003", "source": "news",     "person": "Jamie Chen", "title": "CFO", "company": "Globex",    "signalType": "FundingRound", "signalStrength": 0.66, "updatedAt": now},
    ]
    return {"count": len(items), "items": items}


@app.get("/business/leads")
async def business_leads():
    # prioritize based on signal strength and persona match (stub logic)
    signals = (await business_signals())["items"]
    prioritized = []
    rank = 1
    for s in sorted(signals, key=lambda x: x["signalStrength"], reverse=True):
        prioritized.append({
            "leadId": f"lead-{rank:03d}",
            "person": s["person"],
            "title": s["title"],
            "company": s["company"],
            "signalType": s["signalType"],
            "signalStrength": s["signalStrength"],
            "owner": "unassigned",
            "personaMatch": s["title"].lower().find("sales") >= 0,
            "nextAction": "preview_message",
            "updatedAt": s["updatedAt"],
        })
        rank += 1
    return {"count": len(prioritized), "items": prioritized}


class PreviewRequest(BaseModel):
    leadId: str
    signalType: str | None = None
    persona: str | None = None
    company: str | None = None
    person: str | None = None
    title: str | None = None


@app.post("/business/message/preview")
async def business_message_preview(req: PreviewRequest):
    # very basic template; real version will blend snippets + persona pain points
    persona_line = f"As a {req.persona}, " if req.persona else ""
    opening = f"Hi {req.person or 'there'},\n\n"
    reason = f"Congrats on the new role at {req.company}. " if (req.signalType == 'PastChampion' or req.signalType == 'NewRole') else "Following recent updates, "
    body = f"{persona_line}we thought this would matter to you: reduced delinquencies, faster collections, and fully automated resident comms across the lifecycle.\n"
    cta = "\nWould you be open to a 15‑minute chat this week?\n\n— PayReady Team"
    return {"leadId": req.leadId, "draft": opening + reason + body + cta}


@app.get("/business/analytics")
async def business_analytics():
    sigs = (await business_signals())["items"]
    by_type = {}
    for s in sigs:
        by_type[s["signalType"]] = by_type.get(s["signalType"], 0) + 1
    return {"signalsByType": by_type, "totalSignals": len(sigs)}


@app.post("/tools/symbols")
def tool_symbols(body: Dict[str, Any]):
    return symbol_lookup(body.get("file"))


@app.post("/tools/tests")
def tool_tests(body: Dict[str, Any]):
    return {"log": run_tests(body.get("path","."))}


@app.post("/tools/docs")
def tool_docs(body: Dict[str, Any]):
    return extract_docs(body.get("file"))


# =============================================================================
# CODE MANAGEMENT FEATURES
# =============================================================================

# Security configuration from .env.local
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
MCP_PASSWORD = os.getenv("MCP_PASSWORD", "sophia-dev")
REPO_ROOT = Path("/Users/lynnmusil/sophia-intel-ai").resolve()
BACKUP_DIR = REPO_ROOT / ".mcp_backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Configuration constants
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "24"))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
rate_limit_cache: Dict[str, List[float]] = {}

# Database connection management
@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(REPO_ROOT / "mcp_audit.db"))
    try:
        yield conn
    finally:
        conn.close()

# Initialize audit database
def init_audit_db():
    """Initialize audit database for tracking changes."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                operation TEXT,
                file_path TEXT,
                user TEXT,
                details TEXT,
                backup_path TEXT
            )
        """)
        conn.commit()

init_audit_db()

def log_change(operation: str, file_path: str, details: str = "", backup_path: str = "", user: str = "mcp-server"):
    """Log file changes for audit trail."""
    with get_db_connection() as conn:
        # Validate operation parameter to prevent injection
        allowed_operations = ["read", "write", "edit", "create", "delete", "backup"]
        if operation not in allowed_operations:
            operation = "unknown"
        
        conn.execute(
            "INSERT INTO changes (timestamp, operation, file_path, user, details, backup_path) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), operation, file_path, user, details, backup_path)
        )
        conn.commit()

# Authentication
class AuthRequest(BaseModel):
    password: str

# Simple rate limiting
def check_rate_limit(key: str) -> bool:
    """Check if request is within rate limit."""
    now = time.time()
    if key not in rate_limit_cache:
        rate_limit_cache[key] = []
    
    # Clean old entries
    rate_limit_cache[key] = [t for t in rate_limit_cache[key] if now - t < RATE_LIMIT_WINDOW]
    
    if len(rate_limit_cache[key]) >= RATE_LIMIT_REQUESTS:
        return False
    
    rate_limit_cache[key].append(now)
    return True

@app.post("/auth/login")
async def login(req: AuthRequest, request: Request):
    """Simple password auth for local development with rate limiting."""
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"login_{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many login attempts")
    
    if req.password != MCP_PASSWORD:
        # Log failed attempt
        log_change("auth", "login_attempt", f"Failed login from {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create JWT token
    token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS), "user": "artemis"},
        SECRET_KEY,
        algorithm="HS256"
    )
    
    log_change("auth", "login_success", f"Successful login from {client_ip}")
    return {"token": token, "expires_in": TOKEN_EXPIRATION_HOURS * 3600}

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token."""
    if not authorization:
        return None  # Allow read-only access without auth
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user")
    except:
        return None

# File operations
class FileReadRequest(BaseModel):
    file_path: str

class FilePreviewRequest(BaseModel):
    file_path: str
    changes: str
    
class FileWriteRequest(BaseModel):
    file_path: str
    content: str
    create_backup: bool = True

class FileEditRequest(BaseModel):
    file_path: str
    old_content: str
    new_content: str

def is_safe_path(file_path: str) -> bool:
    """Check if path is safe to access with enhanced protection."""
    try:
        # Resolve to absolute path, following symlinks
        target_path = (REPO_ROOT / file_path).resolve(strict=False)
        
        # Must be within repository
        if not str(target_path).startswith(str(REPO_ROOT)):
            return False
        
        # Check against sensitive patterns
        sensitive_patterns = [
            "*.key", "*.pem", "*.env", ".env*", "**/secrets/*", "**/credentials/*",
            ".git/config", ".git/credentials", "**/node_modules/*", "**/__pycache__/*",
            "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dylib", "*.dll", "*.exe"
        ]
        
        from fnmatch import fnmatch
        target_str = str(target_path)
        for pattern in sensitive_patterns:
            if fnmatch(target_str, pattern) or fnmatch(target_path.name, pattern):
                return False
        
        # Additional check for hidden files (except .gitignore, etc)
        if target_path.name.startswith('.') and target_path.name not in ['.gitignore', '.prettierrc', '.eslintrc']:
            return False
        
        return True
    except Exception:
        return False

@app.post("/files/read")
async def read_file(req: FileReadRequest):
    """Read file contents (no auth required)."""
    if not is_safe_path(req.file_path):
        return {"error": "Access denied to this file"}
    
    target_path = REPO_ROOT / req.file_path
    
    if not target_path.exists():
        return {"error": "File not found"}
    
    try:
        content = target_path.read_text()
        return {
            "path": req.file_path,
            "content": content,
            "size": len(content),
            "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/files/preview")
async def preview_changes(req: FilePreviewRequest):
    """Preview what changes would be made to a file."""
    if not is_safe_path(req.file_path):
        return {"error": "Access denied to this file"}
    
    target_path = REPO_ROOT / req.file_path
    
    if not target_path.exists():
        # New file preview
        return {
            "path": req.file_path,
            "exists": False,
            "preview": req.changes,
            "operation": "create",
            "lines_added": len(req.changes.splitlines()),
            "lines_removed": 0
        }
    
    # Existing file - show diff
    current_content = target_path.read_text()
    
    # Simple diff calculation
    current_lines = current_content.splitlines()
    new_lines = req.changes.splitlines()
    
    # Find differences
    import difflib
    diff = list(difflib.unified_diff(
        current_lines, new_lines,
        fromfile=req.file_path,
        tofile=req.file_path,
        lineterm=""
    ))
    
    return {
        "path": req.file_path,
        "exists": True,
        "current_size": len(current_content),
        "new_size": len(req.changes),
        "diff": "\n".join(diff),
        "operation": "modify",
        "lines_added": sum(1 for line in diff if line.startswith("+")),
        "lines_removed": sum(1 for line in diff if line.startswith("-"))
    }

@app.post("/files/write")
async def write_file(req: FileWriteRequest, request: Request, user: Optional[str] = Depends(verify_token)):
    """Write or create a file (requires auth) with size validation."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"write_{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many write requests")
    
    # Validate file size
    content_size = len(req.content.encode('utf-8'))
    if content_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB")
    
    if not is_safe_path(req.file_path):
        log_change("write", req.file_path, "Access denied", user=user)
        raise HTTPException(status_code=403, detail="Access denied to this file")
    
    target_path = REPO_ROOT / req.file_path
    backup_path = ""
    
    # Create backup if file exists
    if req.create_backup and target_path.exists():
        timestamp = int(time.time())
        backup_name = f"{target_path.name}.backup.{timestamp}"
        backup_path_obj = BACKUP_DIR / backup_name
        shutil.copy2(target_path, backup_path_obj)
        backup_path = str(backup_path_obj.relative_to(REPO_ROOT))
    
    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    try:
        target_path.write_text(req.content)
        
        # Log the change
        log_change(
            "create" if not target_path.exists() else "write",
            req.file_path,
            f"Size: {content_size} bytes",
            backup_path,
            user=user
        )
        
        return {
            "success": True,
            "path": req.file_path,
            "size": content_size,
            "backup": backup_path if backup_path else None
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Write failed: {str(e)}")

@app.post("/files/edit")
async def edit_file(req: FileEditRequest, request: Request, user: Optional[str] = Depends(verify_token)):
    """Edit existing file with conflict detection (requires auth)."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"edit_{client_ip}"):
        raise HTTPException(status_code=429, detail="Too many edit requests")
    
    # Validate content size
    new_size = len(req.new_content.encode('utf-8'))
    if new_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Content too large. Max size: {MAX_FILE_SIZE_MB}MB")
    
    if not is_safe_path(req.file_path):
        log_change("edit", req.file_path, "Access denied", user=user)
        raise HTTPException(status_code=403, detail="Access denied to this file")
    
    target_path = REPO_ROOT / req.file_path
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        current_content = target_path.read_text()
    except PermissionError:
        raise HTTPException(status_code=403, detail="Cannot read file - permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    # Check for conflicts
    if req.old_content not in current_content:
        log_change("edit", req.file_path, "Conflict detected", user=user)
        raise HTTPException(status_code=409, detail="Content mismatch - file may have changed")
    
    # Create backup
    timestamp = int(time.time())
    backup_name = f"{target_path.name}.backup.{timestamp}"
    backup_path = BACKUP_DIR / backup_name
    try:
        shutil.copy2(target_path, backup_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")
    
    # Apply edit
    new_content = current_content.replace(req.old_content, req.new_content, 1)
    
    try:
        target_path.write_text(new_content)
        
        # Log the change
        log_change(
            "edit",
            req.file_path,
            f"Replaced {len(req.old_content)} chars with {len(req.new_content)} chars",
            str(backup_path.relative_to(REPO_ROOT)),
            user=user
        )
        
        return {
            "success": True,
            "path": req.file_path,
            "backup": str(backup_path.relative_to(REPO_ROOT))
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Cannot write file - permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

@app.get("/audit/recent")
async def get_audit_log(limit: int = 50):
    """Get recent changes (no auth required for viewing)."""
    if limit > 100:  # Prevent excessive queries
        limit = 100
    
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM changes ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
    
    return {"changes": [
        {
            "id": row[0],
            "timestamp": row[1],
            "operation": row[2],
            "file_path": row[3],
            "user": row[4],
            "details": row[5],
            "backup_path": row[6] if len(row) > 6 else None
        }
        for row in rows
    ]}

# Git operations (simplified, read-only for now)
@app.get("/git/status")
async def git_status():
    """Get repository status (no auth required)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status, path = line[:2], line[3:]
                files.append({"status": status.strip(), "path": path})
        
        # Get branch info
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "branch": branch_result.stdout.strip(),
            "files": files,
            "total_changes": len(files)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/git/diff/{file_path:path}")
async def git_diff(file_path: str):
    """Get diff for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", file_path],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "path": file_path,
            "diff": result.stdout
        }
    except Exception as e:
        return {"error": str(e)}


# ==============================================================================
# AGENT FACTORY ENDPOINTS
# ==============================================================================

class ExpertiseProfile(BaseModel):
    primary_domains: List[str] = []
    programming_languages: List[Dict[str, str]] = []  # [{"lang": "python", "level": "expert"}]
    frameworks_libraries: List[str] = []
    methodologies: List[str] = []
    specializations: List[str] = []

class PersonalityTraits(BaseModel):
    traits: List[str] = []  # ["methodical", "creative", "security_focused"]
    work_style: str = "collaborative"  # "collaborative", "independent", "methodical"
    decision_making: str = "analytical"  # "analytical", "intuitive", "consensus_driven"
    risk_tolerance: str = "moderate"  # "conservative", "moderate", "aggressive"

class CommunicationStyle(BaseModel):
    style: str = "detailed"  # "concise", "detailed", "conversational", "formal"
    format_preference: List[str] = ["structured"]  # ["structured", "narrative", "bullet_points"]
    explanation_depth: str = "detailed"  # "high_level", "detailed", "implementation_focused"
    feedback_approach: str = "constructive"  # "constructive", "direct", "encouraging"

class BehavioralPatterns(BaseModel):
    code_review_focus: List[str] = ["security", "maintainability"]
    testing_methodology: List[str] = ["unit_first"]
    documentation_style: str = "thorough"  # "minimal", "thorough", "inline_focused"
    refactoring_tendency: str = "moderate"  # "conservative", "moderate", "aggressive"

class AgentPersona(BaseModel):
    id: str
    name: str
    description: str
    suitable_roles: List[str] = []
    expertise: ExpertiseProfile
    personality: PersonalityTraits
    communication: CommunicationStyle
    behavior: BehavioralPatterns

class AgentDefinition(BaseModel):
    name: str
    role: str
    model: str
    temperature: float = 0.7
    instructions: str
    capabilities: List[str] = []
    persona_id: Optional[str] = None
    persona: Optional[AgentPersona] = None

class SwarmBlueprint(BaseModel):
    name: str
    description: str = ""
    swarm_type: str = "STANDARD"
    execution_mode: str = "hierarchical"
    agents: List[AgentDefinition]
    pattern: str = "hierarchical"
    memory_enabled: bool = True
    namespace: str = "artemis"

# Enhanced persona library
persona_library = {
    "backend_specialist": AgentPersona(
        id="backend_specialist",
        name="Backend Systems Specialist", 
        description="Expert in scalable backend architecture and API design",
        suitable_roles=["planner", "generator", "critic"],
        expertise=ExpertiseProfile(
            primary_domains=["backend_development", "system_architecture", "database_design"],
            programming_languages=[
                {"lang": "python", "level": "expert"},
                {"lang": "go", "level": "advanced"}, 
                {"lang": "rust", "level": "intermediate"}
            ],
            frameworks_libraries=["fastapi", "django", "postgresql", "redis", "kafka"],
            methodologies=["microservices", "api_first", "event_driven", "ddd"]
        ),
        personality=PersonalityTraits(
            traits=["methodical", "security_focused", "performance_oriented"],
            work_style="systematic",
            decision_making="analytical",
            risk_tolerance="conservative"
        ),
        communication=CommunicationStyle(
            style="detailed",
            format_preference=["structured", "diagram_focused"],
            explanation_depth="architectural",
            feedback_approach="analytical"
        ),
        behavior=BehavioralPatterns(
            code_review_focus=["security", "performance", "scalability"],
            testing_methodology=["integration_focused", "load_testing"],
            documentation_style="thorough",
            refactoring_tendency="conservative"
        )
    ),
    "frontend_creative": AgentPersona(
        id="frontend_creative",
        name="Creative Frontend Developer",
        description="User-focused frontend developer with strong UX sensibilities", 
        suitable_roles=["generator", "critic"],
        expertise=ExpertiseProfile(
            primary_domains=["frontend_development", "user_experience", "design_systems"],
            programming_languages=[
                {"lang": "typescript", "level": "expert"},
                {"lang": "javascript", "level": "expert"}
            ],
            frameworks_libraries=["react", "vue", "nextjs", "tailwindcss", "framer"],
            methodologies=["component_driven", "accessibility_first", "mobile_first"]
        ),
        personality=PersonalityTraits(
            traits=["creative", "user_focused", "detail_oriented", "iterative"],
            work_style="collaborative", 
            decision_making="user_centered",
            risk_tolerance="moderate"
        ),
        communication=CommunicationStyle(
            style="conversational",
            format_preference=["visual", "prototype_driven"],
            explanation_depth="implementation_focused",
            feedback_approach="encouraging"
        ),
        behavior=BehavioralPatterns(
            code_review_focus=["usability", "accessibility", "performance"],
            testing_methodology=["e2e_comprehensive", "visual_testing"],
            documentation_style="inline_focused",
            refactoring_tendency="moderate"
        )
    ),
    "security_auditor": AgentPersona(
        id="security_auditor",
        name="Security & Code Quality Auditor",
        description="Security-first developer focused on vulnerability detection and code quality",
        suitable_roles=["critic", "quality_reviewer"],
        expertise=ExpertiseProfile(
            primary_domains=["security", "code_quality", "vulnerability_assessment"],
            programming_languages=[
                {"lang": "python", "level": "expert"},
                {"lang": "typescript", "level": "advanced"},
                {"lang": "go", "level": "advanced"}
            ],
            frameworks_libraries=["owasp", "security_scanners", "static_analysis"],
            methodologies=["security_by_design", "threat_modeling", "secure_coding"]
        ),
        personality=PersonalityTraits(
            traits=["thorough", "security_focused", "quality_oriented", "systematic"],
            work_style="methodical",
            decision_making="risk_based",
            risk_tolerance="very_conservative"
        ),
        communication=CommunicationStyle(
            style="detailed",
            format_preference=["structured", "evidence_based"],
            explanation_depth="detailed",
            feedback_approach="direct"
        ),
        behavior=BehavioralPatterns(
            code_review_focus=["security", "quality", "maintainability", "performance"],
            testing_methodology=["security_testing", "unit_first"],
            documentation_style="thorough",
            refactoring_tendency="conservative"
        )
    )
}

# Global factory storage
factory_swarms = {}
factory_templates = {
    "coding": {
        "id": "coding",
        "name": "Coding Swarm",
        "description": "Code generation, review, and optimization",
        "type": "CODING",
        "category": "development",
        "pattern": "hierarchical",
        "recommended_for": ["code_generation", "code_review", "debugging"],
        "agents": [
            {
                "name": "Code Planner",
                "role": "planner", 
                "model": "qwen/qwen3-30b-a3b",
                "temperature": 0.3,
                "instructions": "Analyze requirements and create implementation plan. Focus on architecture and design patterns.",
                "capabilities": ["planning", "architecture"]
            },
            {
                "name": "Code Generator",
                "role": "generator",
                "model": "x-ai/grok-code-fast-1", 
                "temperature": 0.7,
                "instructions": "Generate clean, efficient code based on the plan. Follow best practices and include error handling.",
                "capabilities": ["code_generation", "best_practices"]
            },
            {
                "name": "Code Reviewer",
                "role": "critic",
                "model": "openai/gpt-5-chat",
                "temperature": 0.2,
                "instructions": "Review generated code for bugs, security issues, and improvements. Be thorough but constructive.",
                "capabilities": ["code_review", "security_analysis"]
            },
            {
                "name": "Code Quality Reviewer",
                "role": "quality_reviewer",
                "model": "anthropic/claude-sonnet-4",
                "temperature": 0.1,
                "instructions": "Perform comprehensive code quality analysis focusing on: security vulnerabilities, performance optimization, code style compliance (PEP 8, ESLint), maintainability, design patterns, and best practices. Provide specific, actionable recommendations with code examples.",
                "capabilities": ["quality_analysis", "security_scanning", "performance_review", "style_compliance", "maintainability_assessment"]
            }
        ]
    },
    "debate": {
        "id": "debate",
        "name": "Debate Swarm",
        "description": "Adversarial analysis and decision making",
        "type": "DEBATE",
        "category": "analysis",
        "pattern": "debate",
        "recommended_for": ["decision_making", "analysis", "risk_assessment"],
        "agents": [
            {
                "name": "Advocate",
                "role": "generator",
                "model": "anthropic/claude-sonnet-4",
                "temperature": 0.8,
                "instructions": "Argue strongly in favor of the proposed solution. Present compelling evidence.",
                "capabilities": ["argumentation", "evidence_gathering"]
            },
            {
                "name": "Critic",
                "role": "critic",
                "model": "openai/gpt-5-chat",
                "temperature": 0.8,
                "instructions": "Challenge the proposal with counter-arguments. Identify weaknesses and risks.",
                "capabilities": ["critical_analysis", "risk_identification"]
            },
            {
                "name": "Judge",
                "role": "judge",
                "model": "x-ai/grok-4",
                "temperature": 0.3,
                "instructions": "Evaluate both sides objectively and provide balanced conclusion.",
                "capabilities": ["evaluation", "synthesis"]
            }
        ]
    },
    "consensus": {
        "id": "consensus", 
        "name": "Consensus Building Swarm",
        "description": "Multi-perspective analysis and consensus building",
        "type": "CONSENSUS",
        "category": "collaboration",
        "pattern": "consensus",
        "recommended_for": ["complex_decisions", "multi_stakeholder", "strategic_planning"],
        "agents": [
            {
                "name": "Technical Analyst",
                "role": "generator",
                "model": "deepseek/deepseek-chat",
                "temperature": 0.5,
                "instructions": "Provide analysis from technical perspective. Focus on feasibility and implementation.",
                "capabilities": ["technical_analysis", "feasibility_assessment"]
            },
            {
                "name": "Business Analyst",
                "role": "generator",
                "model": "qwen/qwen3-30b-a3b",
                "temperature": 0.5,
                "instructions": "Provide analysis from business perspective. Focus on value and ROI.",
                "capabilities": ["business_analysis", "roi_calculation"]
            },
            {
                "name": "Synthesizer",
                "role": "judge",
                "model": "openai/gpt-5-chat",
                "temperature": 0.3,
                "instructions": "Synthesize all perspectives into unified recommendation. Balance competing concerns.",
                "capabilities": ["synthesis", "consensus_building"]
            }
        ]
    }
}

# ===== PERSONA API ENDPOINTS =====
@app.get("/api/factory/personas")
async def get_all_personas():
    """Get all available agent personas"""
    return {
        "personas": [persona.dict() for persona in persona_library.values()],
        "count": len(persona_library)
    }

@app.get("/api/factory/personas/{persona_id}")
async def get_persona(persona_id: str):
    """Get specific persona details"""
    if persona_id not in persona_library:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona_library[persona_id].dict()

@app.post("/api/factory/personas")
async def create_custom_persona(persona: AgentPersona):
    """Create new custom agent persona"""
    if persona.id in persona_library:
        raise HTTPException(status_code=409, detail="Persona ID already exists")
    persona_library[persona.id] = persona
    return {"status": "created", "persona_id": persona.id}

# ===== BUSINESS INTELLIGENCE ENDPOINTS (SOPHIA TAB) =====

# CRM Integration (HubSpot)
@app.get("/api/business/crm/contacts")
async def get_crm_contacts(limit: int = 50):
    """Get recent CRM contacts with AI insights"""
    # Placeholder for HubSpot integration
    return {
        "contacts": [
            {
                "id": "contact_001",
                "name": "John Smith",
                "company": "TechCorp Inc",
                "status": "qualified_lead",
                "last_activity": "2025-09-03T09:30:00Z",
                "ai_insights": {
                    "engagement_score": 8.5,
                    "likelihood_to_close": 0.75,
                    "recommended_action": "Schedule demo meeting",
                    "suggested_agents": ["backend_specialist", "frontend_creative"]
                }
            },
            {
                "id": "contact_002",
                "name": "Sarah Johnson",
                "company": "StartupXYZ",
                "status": "demo_scheduled",
                "last_activity": "2025-09-02T15:45:00Z",
                "ai_insights": {
                    "engagement_score": 9.2,
                    "likelihood_to_close": 0.85,
                    "recommended_action": "Prepare technical presentation",
                    "suggested_agents": ["security_auditor"]
                }
            }
        ],
        "count": 2,
        "ai_summary": {
            "total_qualified_leads": 15,
            "conversion_trend": "+12%",
            "recommended_focus": "technical_demos"
        }
    }

@app.get("/api/business/crm/pipeline")
async def get_crm_pipeline():
    """Get CRM pipeline status with AI recommendations"""
    return {
        "pipeline": [
            {
                "stage": "Qualified Lead",
                "count": 23,
                "value": 125000,
                "ai_recommendation": "Deploy lead nurturing agents"
            },
            {
                "stage": "Demo Scheduled",
                "count": 8,
                "value": 89000,
                "ai_recommendation": "Create technical presentation materials"
            },
            {
                "stage": "Proposal Sent",
                "count": 5,
                "value": 67000,
                "ai_recommendation": "Follow-up with personalized content"
            }
        ],
        "ai_insights": {
            "bottleneck_stage": "Proposal Sent",
            "recommended_action": "Deploy proposal optimization agent",
            "success_probability": 0.72
        }
    }

# Call Analysis Integration (Gong)
@app.get("/api/business/calls/recent")
async def get_recent_calls(days: int = 7):
    """Get recent call analysis with AI insights"""
    return {
        "calls": [
            {
                "id": "call_001",
                "date": "2025-09-03T14:30:00Z",
                "duration": 3600,
                "participants": ["John Smith", "Sales Rep"],
                "type": "discovery",
                "ai_analysis": {
                    "sentiment": "positive",
                    "engagement_score": 8.7,
                    "key_topics": ["technical_requirements", "budget", "timeline"],
                    "concerns_raised": ["security", "scalability"],
                    "next_steps": ["Technical demo", "Security review"],
                    "suggested_followup": "Deploy security audit agent for compliance review"
                }
            },
            {
                "id": "call_002", 
                "date": "2025-09-02T11:00:00Z",
                "duration": 2700,
                "participants": ["Sarah Johnson", "CTO", "Sales Rep"],
                "type": "demo",
                "ai_analysis": {
                    "sentiment": "very_positive",
                    "engagement_score": 9.4,
                    "key_topics": ["architecture", "integration", "roadmap"],
                    "concerns_raised": [],
                    "next_steps": ["Proposal preparation", "Technical deep-dive"],
                    "suggested_followup": "Create custom proposal using backend specialist agent"
                }
            }
        ],
        "ai_summary": {
            "total_calls": 12,
            "average_sentiment": "positive",
            "success_indicators": ["High engagement", "Technical interest", "Budget confirmed"],
            "recommended_actions": [
                "Deploy technical demo agent for next meetings",
                "Create security compliance documentation",
                "Generate custom proposals for qualified leads"
            ]
        }
    }

@app.post("/api/business/calls/{call_id}/analyze")
async def analyze_call_with_ai(call_id: str):
    """Trigger AI analysis for specific call"""
    return {
        "call_id": call_id,
        "analysis_status": "completed",
        "agents_deployed": ["backend_specialist"],
        "insights_generated": {
            "action_items": [
                "Follow up on security requirements",
                "Prepare technical architecture diagram",
                "Schedule stakeholder alignment call"
            ],
            "risks_identified": ["Budget constraints", "Timeline pressure"],
            "opportunities": ["Upsell potential", "Expansion opportunity"]
        }
    }

# Project Management Integration (Asana, Linear, Notion)
@app.get("/api/business/projects/overview")
async def get_project_overview():
    """Get project management overview with AI insights"""
    return {
        "projects": [
            {
                "id": "proj_001",
                "name": "Customer Portal Redesign",
                "platform": "asana",
                "status": "in_progress",
                "completion": 0.65,
                "team_size": 4,
                "deadline": "2025-09-15T00:00:00Z",
                "ai_insights": {
                    "on_track": True,
                    "risk_level": "low",
                    "suggested_optimization": "Deploy frontend creative agent for UI review",
                    "blockers": []
                }
            },
            {
                "id": "proj_002",
                "name": "API Security Audit",
                "platform": "linear",
                "status": "review",
                "completion": 0.90,
                "team_size": 2,
                "deadline": "2025-09-08T00:00:00Z",
                "ai_insights": {
                    "on_track": True,
                    "risk_level": "medium",
                    "suggested_optimization": "Deploy security auditor agent for final review",
                    "blockers": ["Pending stakeholder approval"]
                }
            },
            {
                "id": "proj_003",
                "name": "Documentation Updates",
                "platform": "notion",
                "status": "not_started",
                "completion": 0.0,
                "team_size": 1,
                "deadline": "2025-09-20T00:00:00Z",
                "ai_insights": {
                    "on_track": False,
                    "risk_level": "high",
                    "suggested_optimization": "Deploy backend specialist agent for automated documentation",
                    "blockers": ["Resource allocation"]
                }
            }
        ],
        "ai_summary": {
            "total_projects": 3,
            "on_track": 2,
            "at_risk": 1,
            "recommended_agent_deployments": [
                "Deploy documentation agent for automated updates",
                "Use security auditor for compliance review"
            ]
        }
    }

@app.post("/api/business/projects/{project_id}/optimize")
async def optimize_project_with_ai(project_id: str):
    """Deploy AI agents to optimize specific project"""
    return {
        "project_id": project_id,
        "optimization_started": True,
        "agents_deployed": ["backend_specialist", "security_auditor"],
        "expected_completion_time": "2 hours",
        "estimated_improvement": {
            "time_saved": "4 hours",
            "quality_increase": "15%",
            "risk_reduction": "medium"
        }
    }

# Business Intelligence Dashboard
@app.get("/api/business/dashboard")
async def get_business_dashboard():
    """Get unified business intelligence dashboard data"""
    return {
        "overview": {
            "leads_this_week": 23,
            "deals_in_pipeline": 156000,
            "active_projects": 12,
            "ai_optimizations": 8
        },
        "ai_insights": {
            "revenue_forecast": 189000,
            "conversion_probability": 0.78,
            "bottlenecks": ["proposal_approval", "technical_demo"],
            "opportunities": ["upsell_existing", "referral_program"]
        },
        "recommended_actions": [
            {
                "action": "Deploy lead qualification agents",
                "impact": "high",
                "effort": "low",
                "estimated_value": 25000
            },
            {
                "action": "Automate proposal generation",
                "impact": "medium", 
                "effort": "medium",
                "estimated_value": 15000
            }
        ],
        "agent_performance": {
            "total_deployments": 45,
            "success_rate": 0.92,
            "average_task_time": "2.3 hours",
            "business_value_generated": 78000
        }
    }

# Workflow Automation
@app.post("/api/business/workflows/trigger")
async def trigger_business_workflow(workflow: Dict[str, Any]):
    """Trigger automated business workflow with AI agents"""
    workflow_type = workflow.get("type")
    
    if workflow_type == "lead_qualification":
        return {
            "workflow_id": "wf_001",
            "type": "lead_qualification",
            "agents_deployed": ["backend_specialist", "frontend_creative"],
            "status": "running",
            "expected_completion": "30 minutes",
            "steps": [
                "Analyze lead requirements",
                "Generate custom proposal",
                "Create technical demo materials"
            ]
        }
    
    elif workflow_type == "project_optimization":
        return {
            "workflow_id": "wf_002", 
            "type": "project_optimization",
            "agents_deployed": ["security_auditor"],
            "status": "running",
            "expected_completion": "2 hours",
            "steps": [
                "Audit project security",
                "Generate compliance report",
                "Recommend optimizations"
            ]
        }
    
    else:
        return {
            "error": "Unknown workflow type",
            "supported_types": ["lead_qualification", "project_optimization", "call_analysis"]
        }

# ===== REPOSITORY INTEGRATION ENDPOINTS =====
@app.post("/api/factory/agents/{agent_id}/deploy")
async def deploy_agent_to_repository(agent_id: str, config: Dict[str, Any]):
    """Deploy agent to work on repository with file/git access"""
    # Implementation for repository deployment
    return {
        "status": "deployed",
        "agent_id": agent_id,
        "repository_access": True,
        "monitoring_url": f"/api/factory/agents/{agent_id}/monitor"
    }

@app.get("/api/factory/agents/{agent_id}/monitor")
async def monitor_agent_execution(agent_id: str):
    """Get real-time agent execution status and actions"""
    # Implementation for live monitoring
    return {
        "agent_id": agent_id,
        "status": "working",
        "current_action": "Analyzing code structure...",
        "files_accessed": ["src/auth.py", "tests/test_auth.py"],
        "pending_changes": [],
        "requires_approval": False
    }

@app.post("/api/factory/agents/{agent_id}/approve")
async def approve_agent_action(agent_id: str, action: Dict[str, Any]):
    """Approve or reject agent file operations"""
    # Implementation for approval workflow
    return {
        "action_id": action.get("id"),
        "status": "approved",
        "timestamp": datetime.utcnow().isoformat()
    }

# ===== ENHANCED FACTORY ENDPOINTS =====
@app.get("/api/factory/templates")
async def factory_get_templates():
    """Get all available swarm templates"""
    return list(factory_templates.values())

@app.get("/api/factory/patterns")
async def factory_get_patterns():
    """Get all available execution patterns"""
    return [
        {
            "name": "hierarchical",
            "description": "Manager coordinates agent execution in hierarchy",
            "compatible_swarms": ["coding", "consensus", "standard"]
        },
        {
            "name": "debate",
            "description": "Agents argue opposing viewpoints to reach conclusion",
            "compatible_swarms": ["debate", "analysis"]
        },
        {
            "name": "consensus",
            "description": "All agents contribute to collaborative decision",
            "compatible_swarms": ["consensus", "collaboration"]
        },
        {
            "name": "sequential",
            "description": "Agents execute one after another in sequence",
            "compatible_swarms": ["coding", "standard"]
        },
        {
            "name": "parallel",
            "description": "All agents execute simultaneously",
            "compatible_swarms": ["analysis", "research"]
        },
        {
            "name": "evolutionary",
            "description": "Agents evolve solutions through iterations",
            "compatible_swarms": ["optimization", "creative"]
        }
    ]

@app.post("/api/factory/create")
async def factory_create_swarm(blueprint: SwarmBlueprint):
    """Create a new swarm from blueprint"""
    # Generate unique swarm ID
    import uuid
    swarm_id = str(uuid.uuid4())
    
    # Validate blueprint
    if not blueprint.name:
        return {"error": "Swarm name is required"}
    
    if len(blueprint.agents) < 1:
        return {"error": "At least one agent is required"}
    
    # Store blueprint
    factory_swarms[swarm_id] = {
        "id": swarm_id,
        "blueprint": blueprint.dict(),
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "executions": 0
    }
    
    return {
        "swarm_id": swarm_id,
        "status": "created",
        "name": blueprint.name,
        "agents": len(blueprint.agents),
        "pattern": blueprint.pattern,
        "endpoints": {
            "execute": f"/api/factory/swarms/{swarm_id}/execute",
            "status": f"/api/factory/swarms/{swarm_id}/status",
            "info": f"/api/factory/swarms/{swarm_id}"
        }
    }

@app.post("/api/factory/swarms/{swarm_id}/execute")
async def factory_execute_swarm(swarm_id: str, request: dict):
    """Execute a factory-created swarm"""
    if swarm_id not in factory_swarms:
        return {"error": f"Swarm {swarm_id} not found"}
    
    task = request.get("task", "")
    if not task:
        return {"error": "Task is required"}
    
    swarm_data = factory_swarms[swarm_id]
    blueprint = swarm_data["blueprint"]
    
    # Simulate swarm execution
    start_time = time.time()
    
    # For now, simulate by calling OpenRouter with context
    try:
        # Use the first agent's model as primary
        primary_agent = blueprint["agents"][0]
        model = primary_agent["model"]
        
        # Build enhanced prompt with swarm context
        enhanced_prompt = f"""
You are part of a {blueprint['name']} with the following agents:

"""
        for agent in blueprint["agents"]:
            enhanced_prompt += f"- {agent['name']} ({agent['role']}): {agent['instructions']}\n"
        
        enhanced_prompt += f"\nExecuting in {blueprint['pattern']} pattern.\n\nTask: {task}\n\nProvide a comprehensive response coordinating all agent perspectives."
        
        # Call OpenRouter
        or_request = {
            "model": model,
            "messages": [{"role": "user", "content": enhanced_prompt}],
            "temperature": primary_agent.get("temperature", 0.7),
            "max_tokens": 2000
        }
        
        # Reuse existing OpenRouter proxy logic
        or_key = os.getenv("OPENROUTER_API_KEY")
        if or_key:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=or_request,
                    headers={
                        "Authorization": f"Bearer {or_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                    token_usage = data.get("usage", {})
                    
                    execution_time = time.time() - start_time
                    
                    # Update execution count
                    factory_swarms[swarm_id]["executions"] += 1
                    
                    return {
                        "swarm_id": swarm_id,
                        "task": task,
                        "result": {
                            "response": result,
                            "agents_participated": [agent["name"] for agent in blueprint["agents"]],
                            "pattern_used": blueprint["pattern"]
                        },
                        "execution_time": execution_time,
                        "token_usage": token_usage,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "swarm_id": swarm_id, 
                        "task": task,
                        "result": {"error": f"OpenRouter API error: {resp.status_code}"},
                        "success": False,
                        "timestamp": datetime.now().isoformat()
                    }
        else:
            return {
                "swarm_id": swarm_id,
                "task": task, 
                "result": {"error": "OpenRouter API key not configured"},
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "swarm_id": swarm_id,
            "task": task,
            "result": {"error": str(e)},
            "success": False,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/factory/swarms/{swarm_id}")
async def factory_get_swarm_info(swarm_id: str):
    """Get information about a specific swarm"""
    if swarm_id not in factory_swarms:
        return {"error": f"Swarm {swarm_id} not found"}
    
    return factory_swarms[swarm_id]

@app.get("/api/factory/swarms")
async def factory_list_swarms():
    """List all created swarms"""
    return list(factory_swarms.values())

@app.delete("/api/factory/swarms/{swarm_id}")
async def factory_delete_swarm(swarm_id: str):
    """Delete a created swarm"""
    if swarm_id not in factory_swarms:
        return {"error": f"Swarm {swarm_id} not found"}
    
    del factory_swarms[swarm_id]
    return {"success": True, "swarm_id": swarm_id}

@app.get("/api/factory/health")
async def factory_health_check():
    """Health check for factory service"""
    return {
        "status": "healthy",
        "active_swarms": len(factory_swarms),
        "templates_available": len(factory_templates),
        "timestamp": datetime.now().isoformat()
    }
