# Sophia Runbook (Local Dev)

This is the single source of truth for starting, validating, and using Sophia locally with Artemis as a sidecar.

## Prerequisites
- Docker Desktop + Docker Compose
- Python 3.11+ (host) for scripts/tests
- SSH agent with GitHub key loaded (ssh-add -l)
- Secrets in `~/.config/artemis/env`

## Environment
- Copy template and load env:
  - `cd ~/sophia-intel-ai`
  - `cp .env.template .env` (first time)
  - `source scripts/env.sh --quiet`
  - `make keys-check`

## One-Command Startup (Infra + MCP)
- `scripts/dev.sh all`
- Verifies Redis/Postgres/Weaviate and starts MCP (Memory 8081, FS 8082, Git 8084)
- `make mcp-test`

## UI Backend (host-run)
- Export MCP env (or rely on env.sh defaults if set):
  - `export MCP_MEMORY_URL=http://localhost:8081`
  - `export MCP_FILESYSTEM_SOPHIA_URL=http://localhost:8082`
  - `export MCP_GIT_URL=http://localhost:8084`
- Start backend:
  - `make ui-up`
  - Health: `make ui-health`
  - Smoke: `make ui-smoke`
- Open: http://localhost:3000/unified

## Optional: Artemis Filesystem
- `export ARTEMIS_PATH=~/artemis-cli`
- `docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis`
- (FS Artemis health at 8083 if needed)

## Tests (quick)
- Unit-focused: `pytest -q -k "not artemis"`
- Full (exclude Artemis tests): `pytest tests/ -v -k "not artemis" --cov=app --cov-fail-under=80`

## Troubleshooting
- `make health-infra`
- `make mcp-test`
- `docker compose -f docker-compose.dev.yml ps`
- `docker compose -f docker-compose.dev.yml logs <service>`

## Production-ish API
- Rebuild and start: `make api-restart`
- Verify: `sleep 15 && curl http://localhost:8003/openapi.json`
