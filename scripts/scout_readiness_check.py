#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path
readiness = {
    "mcp_stdio": False,
    "weaviate": False,
    "redis": bool(os.getenv("REDIS_URL")),
    "portkey": bool(os.getenv("PORTKEY_API_KEY")),
    "llm": {
        "force": {
            "provider": bool(os.getenv("LLM_FORCE_PROVIDER")),
            "model": bool(os.getenv("LLM_FORCE_MODEL")),
        },
        "analyst": {
            "provider": bool(os.getenv("LLM_ANALYST_PROVIDER")),
            "model": bool(os.getenv("LLM_ANALYST_MODEL")),
        },
        "strategist": {
            "provider": bool(os.getenv("LLM_STRATEGIST_PROVIDER")),
            "model": bool(os.getenv("LLM_STRATEGIST_MODEL")),
        },
        "validator": {
            "provider": bool(os.getenv("LLM_VALIDATOR_PROVIDER")),
            "model": bool(os.getenv("LLM_VALIDATOR_MODEL")),
        },
    },
    "warnings": [],
}
# MCP stdio
try:
    from app.mcp.clients.stdio_client import StdioMCPClient
    c = StdioMCPClient(Path.cwd())
    readiness["mcp_stdio"] = bool(c.initialize())
except Exception:
    readiness["mcp_stdio"] = False
# Weaviate
try:
    import weaviate
    from weaviate.auth import AuthApiKey
    url = os.getenv("WEAVIATE_URL")
    key = os.getenv("WEAVIATE_API_KEY")
    if url and key:
        wc = weaviate.Client(url=url, auth_client_secret=AuthApiKey(key))
        readiness["weaviate"] = wc.is_ready()
    else:
        readiness["warnings"].append(
            "WEAVIATE_URL/WEAVIATE_API_KEY not set; vector search disabled"
        )
except Exception:
    readiness["weaviate"] = False
    readiness["warnings"].append("Weaviate client import/connection failed")
# LLM keys checks
if not readiness["portkey"]:
    readiness["warnings"].append(
        "PORTKEY_API_KEY missing; embeddings and routed LLM calls may fail"
    )
roles = ("analyst", "strategist", "validator")
if not any(
    readiness["llm"][r]["provider"] and readiness["llm"][r]["model"] for r in roles
):
    if not (
        readiness["llm"]["force"]["provider"] and readiness["llm"]["force"]["model"]
    ):
        readiness["warnings"].append(
            "No per-role LLM_* vars set and no LLM_FORCE_* defaults; set either to run swarms"
        )
print(json.dumps(readiness, indent=2))
