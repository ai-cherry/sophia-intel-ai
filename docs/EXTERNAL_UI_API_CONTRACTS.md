External UI API Contracts (Forge + Portkey)

Scope
- These contracts are for server-only UIs in sibling worktrees (not in this repo).
- All secrets are server-side via `<repo>/.env.master`; never expose keys client-side.

Forge UI (port 3100)
- POST `/api/coding/plan`
  - Request: `{ "task": "Add health route", "context_paths": ["app/api"], "model": "<server-curated-id>" }`
  - Behavior: Calls Portkey (server-side) with curated model; returns a plan with steps.
  - Response: `{ "plan_id": "p_123", "steps": [ {"id":"s1","title":"...","desc":"..."} ] }`

- POST `/api/coding/patch?apply=true|false`
  - Request: `{ "edits": [ {"path":"mcp/filesystem/server.py","patch":"...unified diff..."} ], "branch": "feature/auto-<session>" }`
  - Behavior: When `apply=true`, writes via MCP FS (`/fs/write`) and commits via MCP Git; branch-per-session recommended.
  - Response: `{ "applied": true, "commit": "abc123", "branch": "feature/auto-...", "errors": [] }`

- POST `/api/coding/validate`
  - Request: `{ "checks": ["lint","unit"], "paths": ["mcp/"] }`
  - Behavior: Runs repo scripts for lint/unit subset; streams logs server-side; returns pass/fail with summary.
  - Response: `{ "ok": true, "logs": "...tail...", "summary": {"lint":"ok","unit":"ok"} }`

- GET `/api/providers/vk`
  - Response: `{ "vk": { "openai": "PORTKEY_VK_OPENAI", "anthropic": "PORTKEY_VK_ANTHROPIC", ... }, "gateway": "https://api.portkey.ai/v1" }`

Workbench (port 3200)
- GET `/api/portkey/health`
  - Behavior: Calls `GET https://api.portkey.ai/v1/models` with `x-portkey-api-key` header.
  - Response: `{ "ok": true, "models_count": 50, "latency_ms": 123 }` (on success)

- GET `/api/portkey/logs`
  - Behavior: Placeholder; return `{ "items": [] }` until wired to real analytics.

- POST `/api/portkey/console`
  - Request: `{ "model": "<curated-id>", "messages": [{"role":"user","content":"..."}], "stream": false }`
  - Behavior: Server-only call to Portkey chat/completions; model must be in curated top-50.
  - Response: `{ "id": "cmpl_...", "message": {"role":"assistant","content":"..."} }`

Notes
- MCP endpoints used by Forge must be configurable via env: `MCP_MEMORY_URL`, `MCP_FS_URL`, `MCP_GIT_URL`.
- Never embed provider SDKs in UIs; route all LLM calls through Portkey only.
- Curated model list is server-side to prevent leakage or misuse.
