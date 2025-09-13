MCP Servers (Canonical)

This repository provides three canonical HTTP MCP servers and a couple of minimal stdio servers for adapter demos.

Canonical servers (HTTP/FastAPI)
- Memory: `mcp/memory_server.py` -> port 8081
- Filesystem: `mcp/filesystem/server.py` -> port 8082
- Git: `mcp/git/server.py` -> port 8084

Notes
- The alternates `mcp/filesystem.py` and `mcp/git_server.py` are legacy variants and must not be used. Prefer the canonical servers above in scripts and Docker.
- The API exposes proxy endpoints under `/api/mcp/*` via the MCP orchestrator. These are convenience routes; the servers still run independently on their ports.

Quick checks
- Memory: `curl -sf http://localhost:8081/health`
- FS: `curl -sf http://localhost:8082/health`
- Git: `curl -sf http://localhost:8084/health`

Testing
- Run `pytest -q tests/mcp/test_mcp_api_basic.py` to validate the API proxies and server health.
