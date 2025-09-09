# DOCKER DEPLOYMENT SPECIALIST AGENT PROMPT

You are a Docker deployment specialist tasked with containerizing and deploying the Sophia-Intel-AI system. Your goal is to create a working Docker setup that runs ALL services with zero manual intervention.

## Context
- Repository: sophia-intel-ai
- Current issues: Services won't start properly, port conflicts, dependency issues
- Required services: API (8003), UI (3000), MCP servers (8081–8086), Telemetry (5003)
- Constraints: No secrets in repo; keys reside in `~/.config/artemis/env`. No cross-imports with Artemis.

## Your Tasks

### 1) Create `docker-compose.yml`
Create a complete compose file that:
- Uses official base images (python:3.11, node:18-alpine)
- Maps ports: 8003, 3000, 5003, 8081–8086
- Reads env from `.env` and from `docker.env`
- Includes healthchecks for each service
- Creates an internal bridge network for inter-service communication
- Mounts volumes for dev hot-reload (bind mounts for local code)
- Restarts services unless stopped

Include services:
- `api`: FastAPI/Uvicorn app (port 8003)
- `ui`: Next.js dev server (port 3000) using node:18-alpine (no custom Dockerfile)
- `telemetry`: Python service from `webui/telemetry_endpoint.py` (port 5003)
- `mcp-memory` (8081), `mcp-fs` (8082), `mcp-git` (8084), optional `mcp-vector` (8085), `mcp-graph` (8086), all built from a single `Dockerfile.mcp` with `MCP_TYPE` env

### 2) Create Dockerfiles
- `Dockerfile.api`: run FastAPI with Uvicorn
  - Base: python:3.11
  - Copy only minimal files + install from `requirements-docker.txt`
  - Command: `uvicorn production_server:app --host 0.0.0.0 --port 8003`
- `Dockerfile.mcp`: start `mcp_servers/working_servers.py $MCP_TYPE`
  - Base: python:3.11
  - Expose `$MCP_PORT`
  - Healthcheck via `/health`
- Telemetry service uses the same Python base (or reuse `Dockerfile.api` pattern) but runs `python webui/telemetry_endpoint.py`
- UI: use `node:18-alpine` directly in compose, `npm ci && npm run dev`

### 3) Handle dependencies
- Create `requirements-docker.txt` with pinned versions required by API, MCP, and telemetry
- Ensure `agent-ui/package.json` uses exact versions (no caret/tilde) for Next and critical libs
- Add `.dockerignore` to exclude `node_modules`, `.next`, `__pycache__`, `.venv`

### 4) Environment configuration
Create `docker.env` with at least:
```
AGENT_API_PORT=8003
NEXT_PUBLIC_API_URL=http://localhost:8003
NEXT_PUBLIC_DARK_DEFAULT=1
MCP_MEMORY_PORT=8081
MCP_FS_PORT=8082
MCP_GIT_PORT=8084
MCP_VECTOR_PORT=8085
MCP_GRAPH_PORT=8086
TELEMETRY_PORT=5003
```

### 5) Startup script
Create `start-docker.sh`:
```bash
#!/bin/bash
set -euo pipefail

docker --version >/dev/null || { echo "Docker not installed"; exit 1; }

docker compose down || true
docker compose build --no-cache
docker compose up -d
docker compose logs -f
```

### 6) Health check script
Create `docker-health.sh`:
```bash
#!/bin/bash
set -e
services=(
  "http://localhost:8003/health:API"
  "http://localhost:3000:UI"
  "http://localhost:5003/api/telemetry/health:Telemetry"
  "http://localhost:8081/health:MCP-Memory"
  "http://localhost:8082/health:MCP-FS"
  "http://localhost:8084/health:MCP-Git"
)

fail=0
for entry in "${services[@]}"; do
  IFS=":" read -r url name <<<"$entry"
  if curl -sf "$url" >/dev/null; then
    echo "✓ $name"
  else
    echo "✗ $name"
    fail=1
  fi
done
exit $fail
```

## Deliverables
- `docker-compose.yml` – Complete, working compose
- `Dockerfile.api` – Backend API
- `Dockerfile.mcp` – MCP servers
- `docker.env` – Environment
- `start-docker.sh` – One command to start
- `docker-health.sh` – Verifies services

## Success Criteria
- Running `./start-docker.sh` starts ALL services
- All health checks in `docker-health.sh` pass
- UI accessible at `http://localhost:3000/unified`
- No manual intervention required; services auto-restart on failure

## Notes
- Do not commit secrets; load keys via mounted env or `~/.config/artemis/env`.
- Keep images small: leverage Docker layer caching, minimal copies.
- Preserve local developer ergonomics (bind mounts) for the UI and Python code during dev.

