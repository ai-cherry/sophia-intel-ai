#!/usr/bin/env python3
from __future__ import annotations

import os

status = {
    "mcp_stdio": False,
    "weaviate": False,
    "redis": bool(os.getenv("REDIS_URL")),
    "portkey": bool(os.getenv("PORTKEY_API_KEY")),
}

try:
    from pathlib import Path

    from app.mcp.clients.stdio_client import StdioMCPClient

    c = StdioMCPClient(Path.cwd())
    status["mcp_stdio"] = bool(c.initialize())
except Exception:
    status["mcp_stdio"] = False

try:
    import weaviate
    from weaviate.auth import AuthApiKey

    url = os.getenv("WEAVIATE_URL")
    key = os.getenv("WEAVIATE_API_KEY")
    if url and key:
        wc = weaviate.Client(url=url, auth_client_secret=AuthApiKey(key))
        status["weaviate"] = wc.is_ready()
except Exception:
    status["weaviate"] = False

print(status)
