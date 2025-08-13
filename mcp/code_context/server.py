#!/usr/bin/env python
"""
SOPHIA Code Context MCP (stdio)

Purpose:
  Provide Continue.dev with fast, local code context tools via MCP:
    - code_index(globs)            -> (re)builds an in-memory code index
    - code_search(query, top_k)    -> ranked file+snippets (BM25 + ripgrep)
    - symbol_search(query, top_k)  -> symbols from a lightweight tag index
    - file_read(path)              -> bounded, safe file read
    - grep(pattern, glob?, max)    -> ripgrep lines

Protocol:
  Model Context Protocol over stdio (JSON-RPC 2.0). No HTTP server.
  Autostarted by Continue "mcpServers" config.
"""
from __future__ import annotations
import os
import sys
import json
import re
import subprocess
import pathlib
import time
import threading
from typing import Any, Dict, List, Optional, Tuple

ROOT = pathlib.Path(os.environ.get("SOPHIA_WORKDIR", ".")).resolve()
MAX_FILE_BYTES = int(os.environ.get(
    "SOPHIA_CODE_MCP_MAX_FILE_BYTES", "524288"))  # 512KB
DEFAULT_GLOBS = os.environ.get(
    "SOPHIA_CODE_MCP_GLOBS", "agents/**,apps/**,libs/**,mcp/**,schemas/**,docs/**,*.md").split(",")

# --- Minimal in-process indices ------------------------------------------------
_FILE_LIST: List[pathlib.Path] = []
_SYMBOLS: List[Tuple[str, str]] = []  # (symbol, file:line)


def _list_files(globs: List[str]) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    for g in globs:
        for p in ROOT.glob(g.strip()):
            if p.is_file():
                files.append(p)
    # filter obvious junk
    filtered = []
    for p in files:
        s = str(p)
        if any(s.endswith(x) for x in [".png", ".jpg", ".jpeg", ".webp", ".pdf", ".lock", ".zip", ".tar", ".gz", ".ico"]):
            continue
        if any(seg.startswith(".") for seg in p.parts if seg != "."):
            # allow .env.sophia but generally skip hidden trees; adjust below if needed
            pass
        filtered.append(p)
    return filtered


def _index_symbols(paths: List[pathlib.Path]) -> List[Tuple[str, str]]:
    # Lightweight Python/TS symbol scrape (quick & dirty; no new deps)
    out: List[Tuple[str, str]] = []
    func_re = re.compile(
        r"^(async\s+def|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", re.M)
    cls_re = re.compile(r"^class\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", re.M)
    ts_fn = re.compile(
        r"function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(|([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\(", re.M)
    for f in paths:
        try:
            if f.stat().st_size > MAX_FILE_BYTES:  # skip huge files for symbol pass
                continue
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        for m in func_re.finditer(text):
            name = m.group(2)
            line = text.count("\n", 0, m.start()) + 1
            out.append((name, f"{f}:{line}"))
        for m in cls_re.finditer(text):
            name = m.group(1)
            line = text.count("\n", 0, m.start()) + 1
            out.append((name, f"{f}:{line}"))
        for m in ts_fn.finditer(text):
            name = m.group(1) or m.group(2)
            if name:
                line = text.count("\n", 0, m.start()) + 1
                out.append((name, f"{f}:{line}"))
    return out


def _bm25_rank(query: str, files: List[pathlib.Path], top_k: int = 10) -> List[Tuple[float, pathlib.Path]]:
    # Very simple term count scoring; ripgrep augments precision later.
    q = [t.lower() for t in re.findall(r"[a-zA-Z0-9_]+", query)]
    scores: List[Tuple[float, pathlib.Path]] = []
    for f in files:
        try:
            if f.stat().st_size > MAX_FILE_BYTES:  # skip large
                continue
            text = f.read_text(errors="ignore").lower()
        except Exception:
            continue
        score = sum(text.count(t) for t in q)
        if score > 0:
            scores.append((float(score), f))
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:top_k]


def _ripgrep(pattern: str, glob: Optional[str], max_results: int) -> List[Dict[str, Any]]:
    args = ["rg", "--line-number", "--no-heading",
            "--color", "never", pattern, str(ROOT)]
    if glob:
        args = ["rg", "--line-number", "--no-heading",
                "--color", "never", "-g", glob, pattern, str(ROOT)]
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=False, text=True)
        lines = proc.stdout.splitlines()
    except FileNotFoundError:
        return [{"file": "<ripgrep not installed>", "line": 0, "text": ""}]
    out = []
    for ln in lines[:max_results]:
        # /abs/path:lineno:content
        try:
            file_part, line_part, text = ln.split(":", 2)
            out.append(
                {"file": file_part, "line": int(line_part), "text": text})
        except ValueError:
            continue
    return out


# --- MCP plumbing (very small JSON-RPC loop) ----------------------------------
_ID = 0


def _resp(id: int, result: Any = None, error: Dict[str, Any] | None = None) -> None:
    msg = {"jsonrpc": "2.0", "id": id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _result_ok(data: Any) -> Dict[str, Any]:
    return {"success": True, "data": data}


def _err(msg: str, code: int = -32000) -> Dict[str, Any]:
    return {"code": code, "message": msg}


def handle(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    global _FILE_LIST, _SYMBOLS
    if method == "tools/list":
        return {
            "tools": [
                {"name": "code_index", "description": "(Re)index repo files and symbols", "inputSchema": {
                    "type": "object", "properties": {"globs": {"type": "array", "items": {"type": "string"}}}}},
                {"name": "code_search", "description": "Search code (BM25 + ripgrep)", "inputSchema": {
                    "type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}}},
                {"name": "symbol_search", "description": "Search symbols (functions/classes)", "inputSchema": {
                    "type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}}},
                {"name": "file_read", "description": "Read a file (size-limited)", "inputSchema": {
                    "type": "object", "properties": {"path": {"type": "string"}}}},
                {"name": "grep", "description": "ripgrep lines", "inputSchema": {"type": "object", "properties": {
                    "pattern": {"type": "string"}, "glob": {"type": "string"}, "max_results": {"type": "integer"}}}}
            ]
        }
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "code_index":
            globs = args.get("globs") or DEFAULT_GLOBS
            _FILE_LIST = _list_files(globs)
            _SYMBOLS = _index_symbols(_FILE_LIST)
            return _result_ok({"files": len(_FILE_LIST), "symbols": len(_SYMBOLS)})
        if name == "code_search":
            query = args.get("query", "").strip()
            top_k = int(args.get("top_k", 10))
            ranked = _bm25_rank(query, _FILE_LIST or _list_files(
                DEFAULT_GLOBS), top_k=top_k)
            # add a ripgrep pass for snippet evidence
            rg = _ripgrep(query, None, max_results=top_k*5) if query else []
            return _result_ok({
                "files": [{"score": s, "path": str(p)} for s, p in ranked],
                "snippets": rg
            })
        if name == "symbol_search":
            query = args.get("query", "").lower()
            top_k = int(args.get("top_k", 10))
            hits = [s for s in _SYMBOLS if query in s[0].lower()][:top_k]
            return _result_ok([{"symbol": s, "location": loc} for s, loc in hits])
        if name == "file_read":
            path = args.get("path", "")
            p = (ROOT / path).resolve()
            if not str(p).startswith(str(ROOT)):
                return {"success": False, "error": {"type": "path_error", "message": "Outside repo root"}}
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    return {"success": False, "error": {"type": "size_limit", "message": "File too large"}}
                return _result_ok({"path": str(p.relative_to(ROOT)), "text": p.read_text(errors="ignore")})
            except Exception as e:
                return {"success": False, "error": {"type": "io_error", "message": str(e)}}
        if name == "grep":
            patt = args.get("pattern", "")
            glob = args.get("glob")
            maxr = int(args.get("max_results", 50))
            return _result_ok(_ripgrep(patt, glob, maxr))
        return {"success": False, "error": {"type": "unknown_tool", "message": name}}
    if method == "health/get":
        return {"status": "healthy", "service": "sophia-code-mcp", "timestamp": int(time.time())}
    return {"error": _err(f"Unknown method: {method}", -32601)}


def main() -> None:
    # Send a ready banner for clients that expect initial info
    sys.stdout.write(json.dumps(
        {"jsonrpc": "2.0", "method": "health/event", "params": {"status": "starting"}})+"\n")
    sys.stdout.flush()
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except Exception:
            continue
        if "method" in req and "id" in req:
            res = handle(req["method"], req.get("params") or {})
            _resp(req["id"], res if "error" not in res else None,
                  res.get("error"))
        elif "id" in req:
            _resp(req["id"], error=_err("Invalid request", -32600))


if __name__ == "__main__":
    main()
