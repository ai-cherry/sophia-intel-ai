from __future__ import annotations
import asyncio
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dev_mcp_unified.core.context_engine import ContextEngine
from dev_mcp_unified.core.job_queue import Job, JobQueue
from dev_mcp_unified.core.simple_key_manager import get_key, KeyProvider
from dev_mcp_unified.llm_adapters.base_adapter import LLMRequest
from dev_mcp_unified.llm_adapters.claude_adapter import ClaudeAdapter
from dev_mcp_unified.llm_adapters.openai_adapter import OpenAIAdapter
from dev_mcp_unified.llm_adapters.qwen_adapter import QwenAdapter
from dev_mcp_unified.llm_adapters.deepseek_adapter import DeepSeekAdapter
from dev_mcp_unified.tools.semantic_search import semantic_search
from dev_mcp_unified.tools.symbol_lookup import symbol_lookup
from dev_mcp_unified.tools.test_runner import run_tests
from dev_mcp_unified.tools.doc_extractor import extract_docs


app = FastAPI(title="MCP Unified Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = ContextEngine(repo_root=os.getenv("MCP_INDEX_PATH"))
queue = JobQueue(workers=2)


class QueryRequest(BaseModel):
    task: str = "general"
    question: str
    llm: Optional[str] = None
    file: Optional[str] = None


@app.on_event("startup")
async def on_start():
    await queue.start()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "watch": bool(os.getenv("MCP_WATCH")), "index": os.getenv("MCP_INDEX_PATH")}


@app.post("/query")
async def query(req: QueryRequest):
    # 1) Select routing
    action = engine.select_action(req.task)
    provider = (req.llm or action.get("provider") or "claude").lower()
    strategy = action.get("context_strategy", "snippet_with_completions")

    # 2) Build context
    ctx = engine.build_context(strategy, target_file=req.file)

    # 3) Adapter map
    adapters = {
        "claude": ClaudeAdapter(get_key(KeyProvider.ANTHROPIC)),
        "openai": OpenAIAdapter(get_key(KeyProvider.OPENAI)),
        "qwen": QwenAdapter(get_key(KeyProvider.QWEN)),
        "deepseek": DeepSeekAdapter(get_key(KeyProvider.DEEPSEEK)),
    }
    adapter = adapters.get(provider) or adapters[engine.select_action("general").get("provider","claude")]

    # 4) Execute (streaming could be added via SSE later)
    llm_req = LLMRequest(prompt=req.question, context=asdict(ctx))
    resp = await adapter.complete(llm_req)
    return asdict(resp)


class RunJobRequest(BaseModel):
    kind: str
    payload: Dict[str, Any] = {}


@app.post("/background/run")
async def background_run(req: RunJobRequest):
    job = Job(id=str(uuid.uuid4()), kind=req.kind, payload=req.payload)
    queue.register("index", lambda j: j.log.append("indexing not implemented in this stub"))
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


@app.post("/tools/symbols")
def tool_symbols(body: Dict[str, Any]):
    return symbol_lookup(body.get("file"))


@app.post("/tools/tests")
def tool_tests(body: Dict[str, Any]):
    return {"log": run_tests(body.get("path","."))}


@app.post("/tools/docs")
def tool_docs(body: Dict[str, Any]):
    return extract_docs(body.get("file"))

