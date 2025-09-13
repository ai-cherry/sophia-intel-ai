# One True Dev Flow – No UI In This Repo

- This repository contains: BI backends/integrations and MCP Core only.
- No UI code is permitted here (no Next.js/React/Vite/Nx). CI blocks reintroduction.

External UIs (separate repos/worktrees):
- ../worktrees/forge-ui (port 3100): Agentic coding (Plan→Patch→Validate) using MCP FS/Git and Portkey.
- ../worktrees/portkey-ui (port 3200): Model routing/VK health/logs; Portkey-only.
- ../worktrees/sophia-bi-ui (port 3300): Pay‑ready dashboards consuming BI API (this repo :8000).

MCP and Env Contracts:
- MCP ports: memory 8081, filesystem 8082, git 8084.
- Single env source: <repo>/.env.master (server-side load only). Required: PORTKEY_API_KEY + VKs; BI integrations as needed.

Runbook:
- ./sophia start (starts API + MCP) → use external UIs against these endpoints.
- Secrets go in ./.env.master only. No dotenv or ~/.config at runtime.

