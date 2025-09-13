MCP Canonical Servers

Canonical Servers (FastAPI)
- Memory: `mcp/memory_server.py` → 8081
- Filesystem: `mcp/filesystem/server.py` → 8082
- Git: `mcp/git/server.py` → 8084
- Vector: `mcp/vector/server.py` → 8085

Start Commands
- `python3 -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081`
- `python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082`
- `python3 -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084`
- `python3 -m uvicorn mcp.vector.server:app --host 0.0.0.0 --port 8085`

Forbidden
- `mcp/filesystem.py` and `mcp/git_server.py` are legacy and must not exist or be referenced.

Smoke/Health
- Start all: `./sophia start`
- Status: `./sophia status` (shows 8081, 8082, 8084 health)
- Direct health: `curl -fsS http://localhost:8081/health && echo OK`
                `curl -fsS http://localhost:8082/health && echo OK`
                `curl -fsS http://localhost:8084/health && echo OK`
                `curl -fsS http://localhost:8085/health && echo OK`
