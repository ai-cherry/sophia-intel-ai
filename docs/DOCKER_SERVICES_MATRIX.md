# Docker Services Matrix

Purpose: summarize which services appear in each compose file and clarify the canonical workflow for Phase 2.

Canonical usage in this repo currently prefers `docker-compose.multi-agent.yml` via `scripts/multi-agent-docker-env.sh` and Make targets (e.g., `make dev-up`). This matrix helps ensure parity as we consolidate configuration and adopt overrides/profiles.

Note: This matrix is generated heuristically from YAML indentation and may include minor inaccuracies for legacy/archived files. Validate with `docker compose config -f <file>` in an environment with Docker installed.

## Service Presence

| Service | docker-compose.yml | docker-compose.dev.yml | docker-compose.multi-agent.yml | docker-compose.enhanced.yml | archive/optimized | archive/sophia-intel-ai | archive/sophia |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| redis | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| weaviate | ✓ | ✓ | ✓ | ✓ |  |  | ✓ |
| postgres | ✓ |  | ✓ | ✓ | ✓ | ✓ |  |
| neo4j |  | ✓ | ✓ |  |  |  |  |
| agent-dev |  | ✓ | ✓ |  |  |  |  |
| mcp-memory |  | ✓ | ✓ |  |  |  |  |
| mcp-filesystem-sophia |  | ✓ | ✓ |  |  |  |  |
| mcp-filesystem-sophia |  | ✓ | ✓ |  |  |  |  |
| mcp-git |  | ✓ | ✓ |  |  |  |  |
| swarm-orchestrator |  | ✓ | ✓ |  |  |  |  |
| indexer |  |  | ✓ |  |  |  |  |
| webui |  | ✓ | ✓ |  |  |  |  |
| api/unified-api | ✓ |  |  | ✓ |  |  |  |
| prometheus |  | ✓ |  | ✓ | ✓ | ✓ |  |
| grafana |  | ✓ |  | ✓ | ✓ | ✓ |  |

Legend: ✓ = service present in file (best-effort detection). Archived files are under `archive/docker-compose/`.

## Canonical Workflow

- Primary entrypoint: `make dev-up` (uses `scripts/multi-agent-docker-env.sh` with `docker-compose.multi-agent.yml`).
- Local overrides: `docker-compose.override.yml` (Phase 2 creates/uses this for strictly local changes).
- Profiles: use Compose profiles to toggle optional stacks (MCP, UI, observability) when consolidating.

## Validation

Recommended checks after any Compose consolidation:
- `make dev-up && make status`
- `make mcp-status`
- `docker compose -f docker-compose.multi-agent.yml config --services` (lists services for sanity)

If changing canonical base in future, ensure Make targets and `scripts/multi-agent-docker-env.sh` remain consistent.

