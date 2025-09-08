# Unified Local Development and Deployment Plan

This is the single source of truth for setting up, running, and deploying the project locally. It replaces scattered guides and conflicting instructions.

Goals
- One canonical local dev workflow (Docker-based) with a single compose file.
- One environment template and one way to load environment variables.
- Clear deployment paths for local and production-like runs.

Prerequisites
- Docker and Docker Compose
- Python 3.11+ (optional for scripts/tests outside containers)
- SSH agent running with your GitHub key loaded (for SSH operations)

Environment Setup
- Copy the template and adjust as needed:
  - `cp .env.template .env`
- Put all provider API keys securely in `~/.config/artemis/env` (outside git):
  - Run: `make artemis-setup` (creates and documents the secure store)
  - Validate: `make env.check` then `make env.doctor`
- Optional: auto-load env with direnv
  - Install direnv and run: `direnv allow`
  - Or source once per shell: `source scripts/env.sh`

MCP Endpoints (for Cursor/Cline)
- Filesystem: `http://localhost:8082`
- Memory:     `http://localhost:8081`
- Git:        `http://localhost:8084`
- VS Code settings are in `.vscode/settings.json` (tracked) and should work out of the box.

Single Local Startup (Canonical)
1) Start dev infra + MCP and Sophia UI
   - `make dev-all`
   - Starts Redis, Weaviate, MCP (Memory/FS/Git), and Next.js UI.
2) Start the Sophia API (another terminal)
   - `make api-dev` (http://localhost:8003)
3) Open the UI
   - Dashboard: http://localhost:3000/(sophia)/dashboard
   - Chat:      http://localhost:3000/(sophia)/chat
4) If CORS errors occur
   - Set `CORS_ORIGINS=http://localhost:3000` in your env and restart the API.

Optional Profiles
- Artemis integration (only if you need a second repo):
  - One-time setup (SSH): `make artemis.sidecar-setup` (clones to `~/artemis-cli`)
  - Set `ARTEMIS_PATH` in your `.env` or shell to the absolute path of your artemis repo
  - Start services with profile: `docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis`

Shut Down and Cleanup
- Stop: `docker compose -f docker-compose.dev.yml down`
- Clean Docker resources (caution): `make clean`

Deployment Plan (Production-like)
- Minimal services for a lean deployment are defined in `docker-compose.yml`.
  - Configure `.env` from `.env.template` and your secure keys.
  - Bring up required services:
    - `docker compose up -d redis weaviate postgres`
    - Run your API or orchestrator service as documented in app/ or scripts/
  - Health checks:
    - Redis: `redis-cli -h localhost -p 6379 ping`
    - Weaviate: `curl -sf http://localhost:8080/v1/.well-known/ready`
    - Postgres: `pg_isready -U <user> -h localhost -p 5432`

AI Coding Agent Rules (Non-Negotiable)
- Do not create new `.env*` variants. Only use `.env.template` and local `.env`/`.env.local`.
- Do not write new Markdown files in the repo root. Use `docs/` and the established structure.
- Do not create new assistant directories; use `.ai/` only.
- Before creating a new doc or script, search for an existing one. Consolidate instead of duplicating.
- When updating dev workflow or Docker services, update this document.

Troubleshooting
- Env not loading: `make env.doctor`, `source scripts/env.sh`, verify `~/.config/artemis/env` exists.
- MCP endpoints unreachable: ensure `docker-compose.dev.yml` is running and ports 8081/8082/8084 are free.
- SSH operations failing in containers: ensure `SSH_AUTH_SOCK` is set and your agent has keys (`ssh-add -l`).
 - CORS in browser: set `CORS_ORIGINS=http://localhost:3000` and restart the API.
 - Voice endpoints: set `ELEVENLABS_API_KEY` (TTS) and `OPENAI_API_KEY` (STT).

Complete Startup Sequence (with verification)
1) Start infrastructure
- `docker compose -f docker-compose.dev.yml up -d redis postgres weaviate`
2) Verify infrastructure
- `make health-infra`
3) Start MCP servers
- `docker compose -f docker-compose.dev.yml up -d mcp-memory mcp-filesystem-sophia mcp-git`
4) Verify MCP servers
- `curl -sf http://localhost:8081/health`
- `curl -sf http://localhost:8082/health`
- `curl -sf http://localhost:8084/health`
5) Start Sophia dev shell
- `docker compose -f docker-compose.dev.yml up -d agent-dev`
- `docker compose -f docker-compose.dev.yml exec agent-dev bash`
6) Optional: Connect Artemis sidecar
- Local sidecar:
  - `export ARTEMIS_PATH=/absolute/path/to/artemis-cli`
  - `docker compose -f docker-compose.dev.yml --profile artemis up -d`
- Remote Artemis (HTTP):
  - Set `ARTEMIS_URL=http://artemis-host:8090` (HTTP bridge planned; currently not integrated)

MCP Integration Verification
- Filesystem: `curl -sf http://localhost:8082/health`
- Memory:     `curl -sf http://localhost:8081/health`
- Git:        `curl -sf http://localhost:8084/health`
