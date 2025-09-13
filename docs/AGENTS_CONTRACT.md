# Sophia Intel Agents Contract (Source of Truth)

This document defines canonical startup, deployment, and integration rules for the Sophia Intel repository. It complements AGENTS.md and must stay in sync with it.

## Canonical Runtime
- API: `app/api/unified_server:app` on port 8000 (all environments)
- UI: Next.js app under `sophia-intel-app` on port 3000
- MCP Servers: Memory 8081, Filesystem 8082, Git 8084 (started via `scripts/start_all_mcp.sh`)

## Local Development
- Docker (recommended): `make dev-docker` → `infra/docker-compose.yml --profile dev`
- Native (no Docker): `make dev-native` → `scripts/dev/start_local_unified.sh`

## Compose Profiles
- `infra/docker-compose.yml` holds both dev and prod profiles; avoid multiple compose files to reduce drift.
- Services: postgres, valkey(redis), weaviate, neo4j (optional), unified-api, sophia-intel-app, mcp-*.

## Ports (Canonical)
- Centralized in `infra/ports.env` and used by Docker and native scripts.
- Defaults:
  - 8000: API
  - 3000: UI
  - 8081/8082/8084: MCP (memory/fs/git)
  - 5432: Postgres, 6379: Redis/Valkey
  - 8080: Weaviate, 7474/7687: Neo4j

## Environment & Secrets
- No secrets in repo. Use `<repo>/.env.master` (single source) or platform secret store.
- UI base URL via `NEXT_PUBLIC_API_BASE` (dev: `http://localhost:8000`).
 - Cloud: Deploy on Fly.io using `deploy/fly-unified-api.toml` and `deploy/fly-ui.toml`.
 - GPU: Use Lambda Labs Cloud Services as needed. Keys: `LAMBDA_API_TOKEN`, `LAMBDA_CLOUD_ENDPOINT`.

## Quality Gates
- CI must run lint, typecheck, and basic tests. Block merges on failures.

## Deletions & Deprecations
- Removed duplicate/legacy starters: `start_unified.sh`, `unified-start.sh`, `start_all.sh`, `scripts/start-native.sh`, `sophia-intel-app/run.sh`.
- Removed legacy Fly configs; canonical files live under `deploy/`.
- Single canonical startup path prevents fragmentation.

## Change Process
- Any change to startup/deploy flows must update AGENTS.md and this contract.

## Domain Separation Policy (Non‑Negotiable)

- Sophia and Builder are distinct products with separate users, UIs, and APIs.
- Sophia must not mount or import Builder routers or UI assets; Builder must not import Sophia UI/API.
- Shared utilities may exist only in headless libs without domain logic and require dual ownership.
- CI enforces domain walls (see architecture guards workflow).

## LLM Strategy (Portkey‑Only)

- All LLM requests must route through Portkey’s OpenAI‑compatible endpoint using `PORTKEY_API_KEY`.
- OpenRouter virtual key and routing rules live inside Portkey; the repo must not contain or reference provider keys.
- Direct SDK usage (OpenAI/Anthropic) is prohibited in application code. Exceptions require explicit approval and are limited to gateway adapters.
- Prefer additive improvements that preserve the single canonical entrypoints.
