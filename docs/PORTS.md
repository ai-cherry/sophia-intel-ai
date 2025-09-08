**Local Ports Reference**

This document summarizes standard local ports used by the Sophia Intel AI stack for a consistent developer experience.

Core services
- API (Unified): external `8003`
  - `make api-dev` runs on `8003`
  - `start_server.sh` uses `AGENT_API_PORT` (defaults to `8003`)
  - `docker-compose.enhanced.yml` maps host `UNIFIED_API_PORT:8003` -> container `8000`
- UI (Next.js): `3000`
- Telemetry Service: `5003`
  - `webui/telemetry_endpoint.py` serves monitoring endpoints
- Redis: `6379`
- Postgres: `5432`
- Weaviate: `8080`

MCP servers
- Memory MCP: `8081`
- Filesystem (Sophia) MCP: `8082`
- Filesystem (Artemis) MCP: `8083` (optional, requires sidecar)
- Git MCP: `8084`
- Vector MCP: `8085` (optional)
- Graph MCP: `8086` (optional)

UI defaults and env
- `NEXT_PUBLIC_API_URL`: defaults to `http://localhost:8003`
- Debug flags:
  - `NEXT_PUBLIC_SHOW_METRICS_DEBUG=1|true`
  - `NEXT_PUBLIC_USE_REALTIME_MANAGER=1|true`
  - `NEXT_PUBLIC_USE_UNIFIED_CHAT=1|true` (planned)

Health and checks
- `make phase1.verify` checks env, infra, MCP, and runs a health script.
- `scripts/phase1_health.py` verifies MCP ports (8081–8086), Redis, Postgres.
- `Makefile mcp-test` checks 8081/8082/8084; vector/graph are optional.

Notes
- `sophia.sh` now respects `AGENT_API_PORT` (defaults to `8000` for backward compatibility) to avoid breaking existing deployments. Set `AGENT_API_PORT=8003` to align with the unified API default.
- For docker-based dev, host `8003` proxies container `8000` for the API.

