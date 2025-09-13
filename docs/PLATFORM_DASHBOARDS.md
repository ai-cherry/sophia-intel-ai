Platform Dashboards Alignment

Overview
- Sophia Intel App UI (Next.js) is the single consolidated dashboard for business users.
- Builder Agno Dashboard is a developer utility for codegen workflows.
- Both are separate but coordinated; neither duplicates the other’s purpose.

Ports
- 3000: Agent UI (Next.js; Sophia dashboards)
- 8003: Sophia API (FastAPI; consumed by Agent UI)
- 8004: Builder Bridge API (FastAPI; dev codegen backend)
- 8005: Builder Dashboard (static HTML; dev-only)
- 8081/8082/8084: MCP (memory/filesystem/git)

Routing & Integration
- Agent UI proxies `/api/*` to `8003` via `next.config.js` rewrites. Pages may safely call `fetch('/api/...')`.
- Builder Dashboard talks to Bridge API on `8004`. The CLI `builder_cli/forge.py approve` opens Agent UI by default.

Environment Loading
- Canonical: `<repo>/.env.master` (loaded by `./sophia`).
- App fallbacks: `.env`, `.env.local` (via `app.core.env.load_env_once`).

Do/Don’t
- Do: Add/extend dashboards under `sophia-intel-app/` only.
- Don’t: Create parallel dashboards outside `sophia-intel-app/` for business features.
- Do: Keep Builder dashboard at `builder-system/` strictly for dev workflows.

Verification
- UI: http://localhost:3000
- API: curl -sf http://localhost:8003/healthz
- Builder: http://localhost:8005 and http://localhost:8004/health
