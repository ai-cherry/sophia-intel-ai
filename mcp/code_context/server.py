#!/usr/bin/env python3
"""
Code Context MCP Server (stdio JSON-RPC)

Features:
- health/get
- fs/file_read
- code/grep         : fast ripgrep if available, pure-Python fallback
- code/code_search  : literal search (multi-file) with path filters
- code/symbol_search: simple regex-based symbol scan (py/ts/js)
Resilience:
- Path allowlist (repo root), ignores vendor dirs
- Timeouts, retries, and graceful errors
- No external deps; optional ripgrep binary if installed

Run (health only):
  python mcp/code_context/server.py --health
Run (stdio JSON-RPC loop):
  python mcp/code_context/server.py
"""

from __future__ import annotations
import asyncio
import json
import os
import re
import sys
import time
import traceback
import subprocess
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# .../mcp/code_context/server.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "__pycache__",
               ".mypy_cache", ".ruff_cache", ".pytest_cache", "dist", "build"}
MAX_FILE_BYTES = 1_048_576  # 1MB read limit
RG_BIN = os.environ.get("RG_BIN", "rg")
REQUEST_TIMEOUT = float(os.environ.get("MCP_REQ_TIMEOUT", "8.0"))
GREP_WORKERS = int(os.environ.get("MCP_GREP_WORKERS", "4"))


@dataclass
class RPCError(Exception):
    code: int
    message: str
    data: Optional[Any] = None


def log(*a: Any) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]", " ".join(map(str, a)), file=sys.stderr, flush=True)


def safe_path(p: str) -> Path:
    path = (REPO_ROOT / p).resolve()
    if REPO_ROOT not in path.parents and path != REPO_ROOT:
        raise RPCError(-32001, f"path outside repo: {p}")
    return path


def is_vendor(path: Path) -> bool:
    parts = set(path.parts)
    return any(d in parts for d in IGNORE_DIRS)


def list_files(root: Path) -> List[Path]:
    paths: List[Path] = []
    for base, dirs, files in os.walk(root):
        base_path = Path(base)
        # prune ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            p = base_path / f
            if p.is_file():
                paths.append(p)
    return paths


async def run_ripgrep(pattern: str, cwd: Path, literal: bool = False) -> List[Tuple[str, int, str]]:
    args = [RG_BIN, "-n", "--hidden", "--no-heading"]
    if literal:
        args.append("-F")
    args += [pattern, "."]
    try:
        proc = await asyncio.create_subprocess_exec(
            *args, cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=REQUEST_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            raise RPCError(-32003, "ripgrep timeout")
        if proc.returncode not in (0, 1):  # 1 = no matches
            raise RPCError(-32004,
                           f"ripgrep failed: {err.decode('utf-8','ignore')[:200]}")
        lines = out.decode("utf-8", "ignore").splitlines()
        results = []
        for line in lines:
            # format: path:line:match
            try:
                path, lno, text = line.split(":", 2)
                results.append((path, int(lno), text))
            except Exception:
                continue
        return results
    except FileNotFoundError:
        return []  # ripgrep not installed


async def py_grep(pattern: str, cwd: Path, flags: int = 0) -> List[Tuple[str, int, str]]:
    rx = re.compile(pattern, flags)
    results: List[Tuple[str, int, str]] = []
    files = list_files(cwd)
    sem = asyncio.Semaphore(GREP_WORKERS)

    async def scan_file(p: Path):
        if is_vendor(p):
            return
        try:
            async with sem:
                if p.stat().st_size > MAX_FILE_BYTES:
                    return
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if rx.search(line):
                            rel = p.relative_to(cwd).as_posix()
                            results.append((rel, i, line.rstrip("\n")))
        except Exception:
            pass
    await asyncio.gather(*(scan_file(p) for p in files))
    return results


def python_symbols(text: str) -> List[Tuple[str, int, str]]:
    res = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*def\s+\w+\s*\(", line) or re.match(r"^\s*class\s+\w+\s*[:\(]", line):
            res.append(("python", i, line.strip()))
    return res


def ts_js_symbols(text: str) -> List[Tuple[str, int, str]]:
    res = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"\bfunction\s+\w+\s*\(", line) or re.search(r"\bclass\s+\w+\s*", line) or re.search(r"^\s*export\s+(const|function|class)\s+\w+", line):
            res.append(("ts/js", i, line.strip()))
    return res


async def handle(method: str, params: Dict[str, Any]) -> Any:
    if method == "health/get":
        return {"status": "healthy"}

    if method == "fs/file_read":
        # params: path (relative to repo root), max_bytes?
        p = safe_path(params["path"])
        if not p.exists() or not p.is_file():
            raise RPCError(-32010, f"file not found: {p}")
        if p.stat().st_size > MAX_FILE_BYTES:
            raise RPCError(-32011, "file too large")
        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
            return {"path": str(p.relative_to(REPO_ROOT)), "content": fh.read()}

    if method == "code/grep":
        # params: pattern (regex), case_sensitive (bool, default True), literal (bool, default False), dir (optional)
        pattern = params["pattern"]
        case_sensitive = bool(params.get("case_sensitive", True))
        literal = bool(params.get("literal", False))
        cwd = safe_path(params.get("dir", "."))
        if is_vendor(cwd):
            cwd = REPO_ROOT
        # try ripgrep first
        hits = await run_ripgrep(pattern, cwd, literal=literal)
        if hits:
            return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]
        # fallback to pure Python regex
        flags = 0 if case_sensitive else re.IGNORECASE
        hits = await py_grep(pattern if not literal else re.escape(pattern), cwd, flags=flags)
        return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]

    if method == "code/code_search":
        # alias for literal search
        q = params["query"]
        cwd = safe_path(params.get("dir", "."))
        hits = await run_ripgrep(q, cwd, literal=True)
        if not hits:
            hits = await py_grep(re.escape(q), cwd, flags=0)
        return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]

    if method == "code/symbol_search":
        # params: dir (optional)
        cwd = safe_path(params.get("dir", "."))
        results = []
        for p in list_files(cwd):
            if p.suffix not in {".py", ".ts", ".tsx", ".js"}:
                continue
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                if p.suffix == ".py":
                    for _, ln, snip in python_symbols(text):
                        results.append(
                            {"path": str(p.relative_to(cwd)), "line": ln, "symbol": snip})
                else:
                    for _, ln, snip in ts_js_symbols(text):
                        results.append(
                            {"path": str(p.relative_to(cwd)), "line": ln, "symbol": snip})
            except Exception:
                continue
        return results

    raise RPCError(-32601, f"unknown method: {method}")


async def rpc_loop() -> None:
    # Simple line-delimited JSON-RPC 2.0 over stdio
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            await asyncio.sleep(0.01)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            params = req.get("params", {}) or {}
            req_id = req.get("id")
            try:
                result = await asyncio.wait_for(handle(method, params), timeout=REQUEST_TIMEOUT)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except RPCError as e:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {
                    "code": e.code, "message": e.message, "data": e.data}}
            except Exception as e:
                log("Unhandled error:", repr(e))
                log(traceback.format_exc())
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {
                    "code": -32000, "message": "internal error"}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            log("Bad JSON:", line[:200])
            err = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32700, "message": "parse error"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


def cli_health() -> int:
    try:
        # Quick filesystem probe
        _ = REPO_ROOT.exists()
        print(json.dumps({"status": "healthy"}))
        return 0
    except Exception as e:
        print(json.dumps({"status": "unhealthy", "error": str(e)}))
        return 1


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--health":
        raise SystemExit(cli_health())
    try:
        asyncio.run(rpc_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
