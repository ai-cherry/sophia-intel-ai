# External UIs Overview

Repos/Worktrees (outside this repo):
- Forge UI (../worktrees/forge-ui, port 3100)
  - API: POST /api/coding/plan, POST /api/coding/patch?apply=true, POST /api/coding/validate, GET /api/providers/vk
  - Uses MCP FS/Git (8082/8084) and Portkey (server-side) with .env.master
  - Scaffold: scripts/scaffold_forge_ui.sh
- Workbench (../worktrees/workbench-ui, port 3200)
  - VK health, logs, routing views; Portkey-only server calls
  - Optional read-only MCP context panels
  - Scaffold: scripts/scaffold_workbench_ui.sh
- Sophia BI UI (../worktrees/sophia-bi-ui, port 3300)
  - Dashboards consuming BI API from this repo (http://localhost:8000)

Env Contract:
- Server-side load of <repo>/.env.master via absolute path (REPO_ENV_MASTER_PATH)
- Required: PORTKEY_API_KEY, VKs, MCP_* URLs, API base URL

Quick Start (Forge)
```bash
bash scripts/scaffold_forge_ui.sh  ../worktrees/forge-ui
cd ../worktrees/forge-ui
pnpm i || npm i
REPO_ENV_MASTER_PATH=$(pwd -P | sed 's|/worktrees/forge-ui||')/.env.master \
  MCP_MEMORY_URL=http://localhost:8081 \
  MCP_FS_URL=http://localhost:8082 \
  MCP_GIT_URL=http://localhost:8084 \
  PORTKEY_API_KEY=pk_live_xxx \
  npm run dev
# Test
curl -fsS http://localhost:3100/health
```

Quick Start (Workbench)
```bash
bash scripts/scaffold_workbench_ui.sh  ../worktrees/workbench-ui
cd ../worktrees/workbench-ui
pnpm i || npm i
REPO_ENV_MASTER_PATH=$(pwd -P | sed 's|/worktrees/workbench-ui||')/.env.master \
  PORTKEY_API_KEY=pk_live_xxx \
  npm run dev
# Test
curl -fsS http://localhost:3200/health
```

Deploy to Fly.io
```bash
# Forge UI (from its worktree)
flyctl apps create forge-ui-stg
flyctl deploy -c fly.toml -a forge-ui-stg

# Workbench UI (from its worktree)
flyctl apps create workbench-ui-stg
flyctl deploy -c fly.toml -a workbench-ui-stg
```

Production hardening
- Set `AUTH_BYPASS_TOKEN` in both apps (Bearer token) until SSO is in front.
- Prefer Cloudflare Access or GitHub OAuth at the edge (SSO) for desktop.
- Tighten CORS to your domains only.
