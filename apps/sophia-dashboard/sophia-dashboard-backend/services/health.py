# apps/dashboard-backend/services/health.py
import os
import time
import socket
from contextlib import closing
from typing import Dict, Any

try:
    import httpx
except ImportError:
    import requests as httpx  # Fallback

DEFAULT_TIMEOUT = float(os.getenv("HEALTH_TIMEOUT_SECONDS", "3.0"))

def _ok(name: str, detail: str = None) -> Dict[str, Any]:
    return {"name": name, "status": "ok", "detail": detail or ""}

def _bad(name: str, detail: str) -> Dict[str, Any]:
    return {"name": name, "status": "error", "detail": detail}

def _degraded(name: str, detail: str) -> Dict[str, Any]:
    return {"name": name, "status": "degraded", "detail": detail}

def check_tcp(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    """Check TCP connectivity to host:port"""
    try:
        with closing(socket.create_connection((host, int(port)), timeout=timeout)):
            return True, "connected"
    except Exception as e:
        return False, str(e)

def check_openrouter() -> Dict[str, Any]:
    """Check OpenRouter API connectivity"""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return _degraded("openrouter", "missing OPENROUTER_API_KEY")
    
    try:
        if hasattr(httpx, 'get'):
            # Using httpx
            r = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=DEFAULT_TIMEOUT,
            )
            status_code = r.status_code
        else:
            # Using requests fallback
            r = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=DEFAULT_TIMEOUT,
            )
            status_code = r.status_code
            
        return _ok("openrouter", f"HTTP {status_code}") if status_code == 200 else _degraded("openrouter", f"HTTP {status_code}")
    except Exception as e:
        return _degraded("openrouter", str(e))

def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant vector database"""
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_API_KEY")
    if not url:
        return _degraded("qdrant", "missing QDRANT_URL")
    
    try:
        headers = {}
        if key:
            headers["api-key"] = key
            
        if hasattr(httpx, 'get'):
            r = httpx.get(f"{url.rstrip('/')}/collections", headers=headers, timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
        else:
            r = httpx.get(f"{url.rstrip('/')}/collections", headers=headers, timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
            
        return _ok("qdrant", f"HTTP {status_code}") if status_code == 200 else _degraded("qdrant", f"HTTP {status_code}")
    except Exception as e:
        return _degraded("qdrant", str(e))

def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL database connectivity"""
    host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST") or os.getenv("NEON_HOST")
    port = os.getenv("PGPORT", "5432")
    
    if not host:
        return _degraded("postgres", "missing PGHOST/POSTGRES_HOST/NEON_HOST")
    
    ok, detail = check_tcp(host, port)
    return _ok("postgres", detail) if ok else _degraded("postgres", detail)

def check_minio() -> Dict[str, Any]:
    """Check MinIO object storage"""
    host = os.getenv("MINIO_HOST", "localhost")
    port = os.getenv("MINIO_PORT", "9000")
    
    ok, detail = check_tcp(host, port)
    return _ok("minio", detail) if ok else _degraded("minio", detail)

def check_mcp() -> Dict[str, Any]:
    """Check MCP Code Server"""
    url = os.getenv("MCP_CODE_SERVER_URL") or os.getenv("MCP_BASE_URL")
    if not url:
        return _degraded("mcp", "missing MCP_CODE_SERVER_URL")
    
    try:
        if hasattr(httpx, 'get'):
            r = httpx.get(f"{url.rstrip('/')}/health", timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
        else:
            r = httpx.get(f"{url.rstrip('/')}/health", timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
            
        return _ok("mcp", f"HTTP {status_code}") if status_code == 200 else _degraded("mcp", f"HTTP {status_code}")
    except Exception as e:
        return _degraded("mcp", str(e))

def check_airbyte() -> Dict[str, Any]:
    """Check Airbyte server"""
    url = os.getenv("AIRBYTE_API_URL", "http://localhost:8000")
    
    try:
        if hasattr(httpx, 'get'):
            r = httpx.get(f"{url.rstrip('/')}/api/v1/health", timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
        else:
            r = httpx.get(f"{url.rstrip('/')}/api/v1/health", timeout=DEFAULT_TIMEOUT)
            status_code = r.status_code
            
        return _ok("airbyte", f"HTTP {status_code}") if status_code == 200 else _degraded("airbyte", f"HTTP {status_code}")
    except Exception as e:
        return _degraded("airbyte", str(e))

def check_all_components() -> Dict[str, Any]:
    """Check all system components with timeout protection"""
    start = time.time()
    
    # Import here to avoid circular imports
    try:
        from .airbyte import check_airbyte_health
        airbyte_check = check_airbyte_health
    except ImportError:
        airbyte_check = check_airbyte
    
    # Run all checks
    parts = [
        check_openrouter(),
        check_qdrant(),
        check_postgres(),
        check_minio(),
        check_mcp(),
        airbyte_check(),
    ]
    
    # Determine overall status
    status = "ok"
    if any(p["status"] == "error" for p in parts):
        status = "error"
    elif any(p["status"] == "degraded" for p in parts):
        status = "degraded"
    
    return {
        "status": status,
        "elapsed_ms": int((time.time() - start) * 1000),
        "components": {p["name"]: p for p in parts},
        "timestamp": time.time()
    }

