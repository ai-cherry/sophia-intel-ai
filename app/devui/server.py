from __future__ import annotations

import asyncio
import os
import subprocess
from collections import deque
from pathlib import Path
from typing import AsyncGenerator, Deque, Dict, List, Optional, Tuple

import requests
from fastapi import FastAPI, HTTPException, Path as FPath, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse, JSONResponse

# Paths
REPO_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
SCRIPT_DIR = REPO_DIR
LOG_DIR = REPO_DIR / "logs"
MANAGER = REPO_DIR / "unified-system-manager.sh"
VALIDATOR = REPO_DIR / "scripts" / "validate_startup_guide.sh"
INDEX_HTML = REPO_DIR / "app" / "devui" / "static" / "index.html"

# Known service logs
SERVICE_LOGS: Dict[str, str] = {
    "litellm": "litellm.log",
    "mcp-memory": "mcp-memory.log",
    "mcp-filesystem": "mcp-filesystem.log",
    "mcp-git": "mcp-git.log",
    "redis": "redis.log",
    "gateway": "gateway.log",
    "api": "api.log",
    "ws": "ws.log",
    "unified-api": "unified-api.log",
}

# App
app = FastAPI(title="Sophia Dev Command Center API", version="0.3.0")

# CORS (local-only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8095",
        "http://127.0.0.1:8095",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_executable(path: Path) -> None:
    try:
        path.chmod(path.stat().st_mode | 0o111)
    except Exception:
        pass


def _run_subproc(cmd: List[str], timeout: Optional[int] = 120) -> Tuple[int, str, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_DIR),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out or "", err or ""
    except subprocess.TimeoutExpired:
        proc.kill()
        return 124, "", "Timed out"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    if INDEX_HTML.exists():
        return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))

    # Minimal inline UI shell for convenience
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Sophia Dev Command Center</title>
  <style>
    body { font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    button { padding: 8px 12px; margin-right: 8px; }
    pre { background: #111; color: #eee; padding: 1rem; border-radius: 6px; overflow-x: auto; max-height: 360px; }
  </style>
</head>
<body>
  <h1>Sophia Dev Command Center</h1>
  <div class="card">
    <h3>System Actions</h3>
    <button onclick="sys('start')">Start All</button>
    <button onclick="sys('stop')">Stop All</button>
    <button onclick="sys('restart')">Restart</button>
    <button onclick="sys('status')">Status</button>
    <button onclick="validate()">Validate</button>
    <pre id="out"></pre>
  </div>
  <script>
  async function sys(action) {
    const res = await fetch(`/api/system/${action}`, { method: 'POST' });
    const txt = await res.text();
    document.getElementById('out').textContent = txt;
  }
  async function validate() {
    const res = await fetch(`/api/tools/validate`, { method: 'POST' });
    const txt = await res.text();
    document.getElementById('out').textContent = txt;
  }
  </script>
</body>
</html>"""
    return HTMLResponse(html)


@app.post("/api/system/{action}", response_class=PlainTextResponse)
def system_action(action: str = FPath(..., description="start|stop|restart|status|health|logs|clean")) -> PlainTextResponse:
    allowed = {"start", "stop", "restart", "status", "health", "logs", "clean"}
    if action not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")
    if not MANAGER.exists():
        raise HTTPException(status_code=500, detail="unified-system-manager.sh not found")
    _ensure_executable(MANAGER)
    rc, out, err = _run_subproc([str(MANAGER), action], timeout=180)
    if rc != 0:
        raise HTTPException(status_code=500, detail=err or out or f"Manager returned {rc}")
    return PlainTextResponse(out or "OK")


@app.get("/api/health/services")
def health_services() -> Dict[str, object]:
    """Run validator or fallback to manager health, return summarized status."""
    summary: Dict[str, object] = {"ok": False, "raw": "", "errors": []}
    if VALIDATOR.exists():
        _ensure_executable(VALIDATOR)
        rc, out, err = _run_subproc(["bash", str(VALIDATOR)], timeout=180)
        ok = "Validation complete:" in out and "core service(s) responding" in out
        summary.update({"ok": ok, "raw": out})
        if rc != 0 and not ok:
            summary["errors"] = [err] if err else ["Validator returned non-zero"]
    else:
        _ensure_executable(MANAGER)
        rc, out, err = _run_subproc([str(MANAGER), "health"], timeout=60)
        summary.update({"ok": rc == 0, "raw": out})
        if rc != 0:
            summary["errors"] = [err or "Manager health returned non-zero"]
    return summary


@app.post("/api/tools/validate", response_class=PlainTextResponse)
def run_validate() -> PlainTextResponse:
    """Execute the validator and return plain text output."""
    if VALIDATOR.exists():
        _ensure_executable(VALIDATOR)
        rc, out, err = _run_subproc(["bash", str(VALIDATOR)], timeout=180)
        if rc != 0 and not out:
            raise HTTPException(status_code=500, detail=err or f"Validator returned {rc}")
        return PlainTextResponse(out or f"Validator returned {rc}")
    # fallback
    if not MANAGER.exists():
        raise HTTPException(status_code=500, detail="No validator and no manager present")
    _ensure_executable(MANAGER)
    rc, out, err = _run_subproc([str(MANAGER), "health"], timeout=60)
    if rc != 0 and not out:
        raise HTTPException(status_code=500, detail=err or f"Health returned {rc}")
    return PlainTextResponse(out or f"Health returned {rc}")


def _service_log_path(service: str) -> Path:
    if service not in SERVICE_LOGS:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")
    return LOG_DIR / SERVICE_LOGS[service]


def _tail_lines(path: Path, lines: int = 200) -> str:
    if not path.exists():
        return ""
    dq: Deque[str] = deque(maxlen=max(1, lines))
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            dq.append(ln)
    return "".join(dq)


@app.get("/api/logs/{service}", response_class=PlainTextResponse)
def get_logs(
    service: str = FPath(..., description="Service name (e.g., litellm, mcp-memory)"),
    lines: int = Query(200, ge=1, le=5000),
) -> PlainTextResponse:
    """Return the last N lines of the service log."""
    p = _service_log_path(service)
    content = _tail_lines(p, lines=lines)
    return PlainTextResponse(content)


async def _stream_log(path: Path, poll_interval: float = 0.5) -> AsyncGenerator[bytes, None]:
    """Simple async tail -f style streamer."""
    last_size = 0
    # Send initial tail
    yield _tail_lines(path, lines=200).encode("utf-8", errors="ignore")
    while True:
        try:
            if path.exists():
                size = path.stat().st_size
                if size > last_size:
                    with path.open("r", encoding="utf-8", errors="ignore") as f:
                        f.seek(last_size)
                        chunk = f.read()
                        if chunk:
                            yield chunk.encode("utf-8", errors="ignore")
                    last_size = size
            await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            yield f"\n[stream-error] {e}\n".encode("utf-8", errors="ignore")
            await asyncio.sleep(1.0)


@app.get("/api/logs/{service}/stream")
def stream_logs(service: str = FPath(...)) -> StreamingResponse:
    """Stream the service log (text/plain streaming)."""
    p = _service_log_path(service)
    return StreamingResponse(_stream_log(p), media_type="text/plain")


@app.post("/api/tools/probe-model")
def probe_model(
    model: Optional[str] = Query(None, description="Model name; defaults to a cheap profile if configured"),
    prompt: Optional[str] = Query("say ok"),
    max_tokens: int = Query(8, ge=1, le=64),
    temperature: float = Query(0.0, ge=0.0, le=2.0),
) -> JSONResponse:
    """
    Minimal chat completion probe via LiteLLM (localhost:4000).
    Accepts optional Authorization via LITELLM_MASTER_KEY env.
    """
    url = "http://127.0.0.1:4000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    token = os.getenv("LITELLM_MASTER_KEY")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "model": model or "cheap",
        "messages": [{"role": "user", "content": prompt or "say ok"}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        data = {
            "status": resp.status_code,
            "ok": resp.ok,
            "json": None,
            "text": None,
        }
        try:
            data["json"] = resp.json()
        except Exception:
            data["text"] = resp.text
        return JSONResponse(data, status_code=200 if resp.ok else 502)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Probe error: {e}")
