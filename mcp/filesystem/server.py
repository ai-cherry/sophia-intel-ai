from __future__ import annotations
import base64
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import fnmatch
import hashlib
import re
import ast
import yaml
from fastapi import FastAPI, HTTPException, Request
import json
import time
from config.python_settings import settings_from_env
_settings = settings_from_env()
try:
    import redis  # type: ignore
    _redis_url = _settings.REDIS_URL or os.getenv("REDIS_URL", "redis://localhost:6379/1")
    _rq = redis.Redis.from_url(_redis_url)
except Exception:
    _rq = None
QUEUE_KEY = os.getenv("VECTOR_INDEX_QUEUE", "fs:index:queue")
from fastapi.responses import JSONResponse, Response
from time import perf_counter
from collections import deque
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
class FSListRequest(BaseModel):
    path: str = "."
class FSReadRequest(BaseModel):
    path: str
    as_base64: bool = False
class FSWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True
class FSDeleteRequest(BaseModel):
    path: str
    recursive: bool = False
@dataclass
class Policy:
    write_allowed: List[str]
    write_denied: List[str]
    backup_on_write: bool
def load_policy(workspace_name: str, root: Path) -> Policy:
    cfg = root / "mcp" / "policies" / "filesystem.yml"
    data = {}
    if cfg.exists():
        data = yaml.safe_load(cfg.read_text()) or {}
    fs = (data.get("filesystem_policies") or {}).get(workspace_name, {})
    return Policy(
        write_allowed=list(fs.get("write_allowed_paths", [])),
        write_denied=list(fs.get("write_denied_paths", [])),
        backup_on_write=bool(fs.get("backup_on_write", True)),
    )
def within(sub: Path, parent: Path) -> bool:
    try:
        sub.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False
def allowed_to_write(path: Path, policy: Policy) -> bool:
    p = str(path)
    for deny in policy.write_denied:
        if p.startswith(deny):
            return False
    if not policy.write_allowed:
        return True
    return any(p.startswith(allow) for allow in policy.write_allowed)
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/workspace"))
WORKSPACE_NAME = os.getenv("WORKSPACE_NAME", "sophia")
READ_ONLY = (_settings.READ_ONLY == "1")
app = FastAPI(title=f"MCP Filesystem Server ({WORKSPACE_NAME})")
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
    # Allow health without auth
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
    # Rate limit (skip health/metrics)
    try:
        if _rate_limit_rpm > 0 and request.url.path not in ("/health", "/metrics"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
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
        REQ_COUNTER.labels("filesystem", request.method, request.url.path, str(resp.status_code)).inc()
        REQ_LATENCY.labels("filesystem", request.url.path).observe(perf_counter() - start)
    except Exception:
        pass
    return resp
_policy = load_policy(WORKSPACE_NAME, Path("/app"))
# -----------------------------
# Repo/Code Intelligence models
# -----------------------------
class RepoListRequest(BaseModel):
    root: str | None = None
    globs: List[str] | None = None
    exclude: List[str] | None = None
    limit: int = 1000
class RepoReadRequest(BaseModel):
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
class RepoSearchRequest(BaseModel):
    query: str
    globs: List[str] | None = None
    regex: bool = False
    case_sensitive: bool = False
    limit: int = 200
class Symbol(BaseModel):
    name: str
    kind: str  # function|class|var
    lang: str
    file: str
    line: int
class SymbolsIndexRequest(BaseModel):
    paths: List[str] | None = None
    languages: List[str] | None = None
class SymbolsSearchRequest(BaseModel):
    kind: Optional[str] = None
    name: Optional[str] = None
    lang: Optional[str] = None
class DepGraphRequest(BaseModel):
    root: str | None = None
    globs: List[str] | None = None
    exclude: List[str] | None = None
# -----------------------------
# In-memory indices (simple)
# -----------------------------
_symbol_index: List[Symbol] = []
_dep_graph: Dict[str, List[str]] = {}
DEFAULT_EXCLUDES = [
    "**/.git/**",
    "**/.hg/**",
    "**/.svn/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.next/**",
    "**/dist/**",
    "**/build/**",
    "**/.venv/**",
    # Archives and backups (prevent AI agents from indexing confusing copies)
    "**/archive/**",
    "archive/**",
    "**/backups/**",
    "**/backup/**",
    "**/artifacts/**",
    "**/deployment_backup_*/**",
    "**/cli_backup_*/**",
]
def _is_excluded(path: Path, exclude: List[str]) -> bool:
    sp = str(path)
    return any(fnmatch.fnmatch(sp, pat) for pat in exclude)
def _iter_files(
    base: Path,
    globs: Optional[List[str]],
    exclude: List[str],
    max_count: Optional[int] = None,
    time_budget_seconds: Optional[float] = None,
) -> List[Path]:
    base = base.resolve()
    patterns = globs or ["**/*"]
    seen: set[Path] = set()
    unique: List[Path] = []
    start = perf_counter()
    for pat in patterns:
        for p in base.glob(pat):
            if time_budget_seconds is not None and (perf_counter() - start) > time_budget_seconds:
                return unique
            if not p.is_file():
                continue
            if _is_excluded(p, exclude):
                continue
            if not within(p, base):
                continue
            rp = p.resolve()
            if rp in seen:
                continue
            unique.append(p)
            seen.add(rp)
            if max_count is not None and len(unique) >= max_count:
                return unique
    return unique
def _detect_lang(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
        ".go": "go",
        ".java": "java",
        ".rs": "rust",
    }.get(ext, ext.lstrip("."))
def _read_text_safely(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return p.read_text(errors="replace")
        except Exception:
            return None
    except Exception:
        return None
def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def _index_python_symbols(path: Path, content: str) -> List[Symbol]:
    out: List[Symbol] = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                out.append(
                    Symbol(
                        name=node.name,
                        kind="function",
                        lang="python",
                        file=str(path.relative_to(WORKSPACE_PATH)),
                        line=getattr(node, "lineno", 1),
                    )
                )
            elif isinstance(node, ast.ClassDef):
                out.append(
                    Symbol(
                        name=node.name,
                        kind="class",
                        lang="python",
                        file=str(path.relative_to(WORKSPACE_PATH)),
                        line=getattr(node, "lineno", 1),
                    )
                )
    except Exception:
        pass
    return out
_JS_FUNC_RE = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(")
_JS_CLASS_RE = re.compile(r"^(?:export\s+)?class\s+([A-Za-z0-9_]+)\b")
_JS_VAR_FUNC_RE = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>")
def _index_js_like_symbols(path: Path, content: str, lang: str) -> List[Symbol]:
    out: List[Symbol] = []
    for idx, line in enumerate(content.splitlines(), start=1):
        if m := _JS_FUNC_RE.match(line.strip()):
            out.append(
                Symbol(
                    name=m.group(1),
                    kind="function",
                    lang=lang,
                    file=str(path.relative_to(WORKSPACE_PATH)),
                    line=idx,
                )
            )
        if m := _JS_CLASS_RE.match(line.strip()):
            out.append(
                Symbol(
                    name=m.group(1),
                    kind="class",
                    lang=lang,
                    file=str(path.relative_to(WORKSPACE_PATH)),
                    line=idx,
                )
            )
        if m := _JS_VAR_FUNC_RE.match(line.strip()):
            out.append(
                Symbol(
                    name=m.group(1),
                    kind="function",
                    lang=lang,
                    file=str(path.relative_to(WORKSPACE_PATH)),
                    line=idx,
                )
            )
    return out
def _extract_deps_for_file(path: Path, content: str, lang: str) -> List[str]:
    deps: List[str] = []
    if lang == "python":
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("import "):
                parts = line.split()
                if len(parts) >= 2:
                    deps.append(parts[1])
            elif line.startswith("from "):
                parts = line.split()
                if len(parts) >= 2:
                    deps.append(parts[1])
    elif lang in {"js", "jsx", "ts", "tsx"}:
        for line in content.splitlines():
            line = line.strip()
            m = re.search(r"from\s+['\"]([^'\"]+)['\"]", line)
            if m:
                deps.append(m.group(1))
            m2 = re.match(r"import\s+['\"]([^'\"]+)['\"]", line)
            if m2:
                deps.append(m2.group(1))
    return deps
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "workspace": str(WORKSPACE_PATH),
        "name": WORKSPACE_NAME,
        "read_only": READ_ONLY,
        "capabilities": [
            "fs.list",
            "fs.read",
            "fs.write",
            "fs.delete",
            "repo.list",
            "repo.read",
            "repo.search",
            "symbols.index",
            "symbols.search",
            "dep.graph",
        ],
    }

@app.get("/metrics")
async def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
@app.post("/fs/list")
async def fs_list(req: FSListRequest) -> Dict[str, Any]:
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not target.exists():
        return {"entries": []}
    entries = []
    for child in sorted(target.iterdir()):
        entries.append(
            {
                "name": child.name,
                "path": str(child.relative_to(WORKSPACE_PATH)),
                "type": "dir" if child.is_dir() else "file",
                "size": child.stat().st_size,
            }
        )
    return {"entries": entries}
@app.post("/fs/read")
async def fs_read(req: FSReadRequest) -> Dict[str, Any]:
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH) or not target.exists() or target.is_dir():
        raise HTTPException(400, detail="invalid path")
    data = target.read_bytes()
    if req.as_base64:
        return {"content_base64": base64.b64encode(data).decode("ascii")}
    try:
        return {"content": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"content_base64": base64.b64encode(data).decode("ascii")}
@app.post("/fs/write")
async def fs_write(req: FSWriteRequest) -> Dict[str, Any]:
    if READ_ONLY:
        raise HTTPException(403, detail="server is read-only")
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not allowed_to_write(target, _policy):
        raise HTTPException(403, detail="write blocked by policy")
    if req.create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)
    if _policy.backup_on_write and target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)
    target.write_text(req.content)
    # best-effort index event
    try:
        if _rq is not None:
            evt = {"path": str(target.relative_to(WORKSPACE_PATH)), "ts": time.time()}
            _rq.lpush(QUEUE_KEY, json.dumps(evt))
    except Exception:
        pass
    return {"ok": True, "path": str(target.relative_to(WORKSPACE_PATH))}
@app.post("/fs/delete")
async def fs_delete(req: FSDeleteRequest) -> Dict[str, Any]:
    if READ_ONLY:
        raise HTTPException(403, detail="server is read-only")
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH):
        raise HTTPException(400, detail="path escapes workspace")
    if not allowed_to_write(target, _policy):
        raise HTTPException(403, detail="delete blocked by policy")
    if target.is_dir():
        if req.recursive:
            shutil.rmtree(target)
        else:
            target.rmdir()
    else:
        target.unlink(missing_ok=True)
    # best-effort index event (delete)
    try:
        if _rq is not None:
            evt = {"path": str(target.relative_to(WORKSPACE_PATH)), "ts": time.time(), "op": "delete"}
            _rq.lpush(QUEUE_KEY, json.dumps(evt))
    except Exception:
        pass
    return {"ok": True}
# -----------------------------
# Repo endpoints (unified)
# -----------------------------
@app.post("/repo/list")
async def repo_list(req: RepoListRequest) -> Dict[str, Any]:
    base = (WORKSPACE_PATH / (req.root or ".")).resolve()
    if not within(base, WORKSPACE_PATH):
        raise HTTPException(400, detail="root escapes workspace")
    exclude = list(DEFAULT_EXCLUDES)
    if req.exclude:
        exclude += req.exclude
    files = _iter_files(
        base,
        req.globs,
        exclude,
        max_count=(max(0, req.limit) or None),
        time_budget_seconds=3.5,
    )
    out = []
    for p in files:
        try:
            st = p.stat()
            out.append(
                {
                    "path": str(p.relative_to(WORKSPACE_PATH)),
                    "size": st.st_size,
                    "lang": _detect_lang(p),
                }
            )
        except Exception:
            continue
    return {"files": out}
@app.post("/repo/read")
async def repo_read(req: RepoReadRequest) -> Dict[str, Any]:
    target = (WORKSPACE_PATH / req.path).resolve()
    if not within(target, WORKSPACE_PATH) or not target.exists() or target.is_dir():
        raise HTTPException(400, detail="invalid path")
    data = target.read_bytes()
    text: Optional[str] = None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    sha = _sha256_bytes(data)
    path_str = str(target.relative_to(WORKSPACE_PATH))
    if text is None:
        # Binary: return base64
        return {"content": None, "content_base64": base64.b64encode(data).decode("ascii"), "path": path_str, "sha": sha}
    lines = text.splitlines()
    start = req.start_line - 1 if req.start_line and req.start_line > 0 else 0
    end = req.end_line if req.end_line and req.end_line > 0 else len(lines)
    start = max(0, min(start, len(lines)))
    end = max(start, min(end, len(lines)))
    sliced = "\n".join(lines[start:end])
    return {"content": sliced, "path": path_str, "sha": sha}
@app.post("/repo/search")
async def repo_search(req: RepoSearchRequest) -> Dict[str, Any]:
    base = WORKSPACE_PATH
    exclude = list(DEFAULT_EXCLUDES)
    files = _iter_files(base, req.globs, exclude, time_budget_seconds=4.0)
    matches = []
    flags = 0 if req.case_sensitive else re.IGNORECASE
    pattern: Optional[re.Pattern[str]] = None
    if req.regex:
        try:
            pattern = re.compile(req.query, flags)
        except re.error as e:
            raise HTTPException(400, detail=f"invalid regex: {e}")
    for p in files:
        text = _read_text_safely(p)
        if text is None:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            found: List[Tuple[int, int]] = []
            if pattern is not None:
                for m in pattern.finditer(line):
                    found.append((m.start() + 1, m.end()))
            else:
                hay = line if req.case_sensitive else line.lower()
                needle = req.query if req.case_sensitive else req.query.lower()
                start_pos = 0
                while True:
                    pos = hay.find(needle, start_pos)
                    if pos == -1:
                        break
                    found.append((pos + 1, pos + len(needle)))
                    start_pos = pos + len(needle)
            for col_start, col_end in found:
                matches.append(
                    {
                        "path": str(p.relative_to(WORKSPACE_PATH)),
                        "line_number": idx,
                        "column_start": col_start,
                        "column_end": col_end,
                        "line": line[:1000],
                    }
                )
                if len(matches) >= req.limit:
                    return {"matches": matches}
    return {"matches": matches}
# Correct regex override for JS function pattern
_JS_FUNC_RE = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(")
@app.post("/symbols/index")
async def symbols_index(req: SymbolsIndexRequest) -> Dict[str, Any]:
    global _symbol_index
    _symbol_index = []
    base = WORKSPACE_PATH
    targets: List[Path] = []
    if req.paths:
        for p in req.paths:
            tp = (base / p).resolve()
            if within(tp, base):
                if tp.is_dir():
                    targets.extend(_iter_files(tp, ["**/*"], DEFAULT_EXCLUDES, max_count=5000, time_budget_seconds=3.5))
                elif tp.is_file():
                    targets.append(tp)
    else:
        targets = _iter_files(base, ["**/*"], DEFAULT_EXCLUDES, max_count=5000, time_budget_seconds=3.5)
    allowed_langs = set(req.languages or [])
    for p in targets:
        lang = _detect_lang(p)
        if allowed_langs and lang not in allowed_langs:
            continue
        content = _read_text_safely(p)
        if content is None:
            continue
        if lang == "python":
            _symbol_index.extend(_index_python_symbols(p, content))
        elif lang in {"js", "jsx", "ts", "tsx"}:
            _symbol_index.extend(_index_js_like_symbols(p, content, lang))
        # Other languages: noop for now
    return {"indexed": len(targets), "symbols": [s.model_dump() for s in _symbol_index]}
@app.post("/symbols/search")
async def symbols_search(req: SymbolsSearchRequest) -> Dict[str, Any]:
    results = []
    for s in _symbol_index:
        if req.kind and s.kind != req.kind:
            continue
        if req.lang and s.lang != req.lang:
            continue
        if req.name and req.name.lower() not in s.name.lower():
            continue
        results.append(s.model_dump())
    return {"symbols": results}
@app.post("/dep/graph")
async def dep_graph(req: DepGraphRequest) -> Dict[str, Any]:
    global _dep_graph
    _dep_graph = {}
    base = (WORKSPACE_PATH / (req.root or ".")).resolve()
    if not within(base, WORKSPACE_PATH):
        raise HTTPException(400, detail="root escapes workspace")
    files = _iter_files(base, req.globs or ["**/*"], list(DEFAULT_EXCLUDES) + (req.exclude or []))
    for p in files:
        lang = _detect_lang(p)
        content = _read_text_safely(p)
        if content is None:
            continue
        deps = _extract_deps_for_file(p, content, lang)
        _dep_graph[str(p.relative_to(WORKSPACE_PATH))] = deps
    nodes = list(_dep_graph.keys())
    edges = []
    for src, ds in _dep_graph.items():
        for d in ds:
            edges.append({"from": src, "to": d})
    return {"nodes": nodes, "edges": edges}
