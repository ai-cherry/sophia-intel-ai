# Tracking Issue: Parameterize Legacy Scripts to Use AGENT_API_PORT (default 8003)

Summary
- Many legacy or auxiliary scripts still hardcode port 8000 (e.g., `http://localhost:8000`). Our standard for local development is API on 8003, UI on 3000, Telemetry on 5003. This issue tracks progressively replacing hardcoded `8000` with the environment variable `AGENT_API_PORT` (default 8003) in scripts that are part of the developer experience.

Why
- Consistency: UI defaults and docs now expect API on 8003.
- Flexibility: `AGENT_API_PORT` allows overriding without editing scripts.
- Fewer footguns: Avoids confusion where some tasks assume 8000 and others use 8003.

Scope
- Only scripts used in the current dev loop and health checks. Archived/one-off scripts can be deferred or marked as legacy.
- Examples flagged by audit (representative; not exhaustive):
  - Makefile: ui-up/ui-health/ui-smoke (fixed)
  - scripts/sophia.sh (fixed: `BACKEND_PORT=${AGENT_API_PORT:-8003}`)
  - scripts/redis-integration-startup.sh (lines 268–277)
  - scripts/verify_slack_webhook.py
  - scripts/start_centralized_mcp.py (status endpoints)
  - scripts/deploy.sh (bind/health checks)
  - scripts/setup_asip_complete.sh (multiple echoes and health calls)
  - scripts/load_testing.py (CLI default `--url`)
  - scripts/startup-validator.py (Backend API entry)
  - scripts/monitoring/* (health and metrics URLs)
  - docs/api/* (OpenAPI base url samples)

Approach
- Replace hardcoded `http://localhost:8000` occurrences with `http://localhost:${AGENT_API_PORT:-8003}` in scripts that run locally.
- For python scripts that print URLs, parameterize via `os.environ.get("AGENT_API_PORT", "8003")`.
- For Docker `-p` flags that deliberately map container 8000 → host: keep mappings intact if they are container-internal; only update user-facing host URLs.

Acceptance Criteria
- Running `scripts/start_local_stack.sh` prints 8003 for API.
- `make ui-up`, `ui-health`, and `ui-smoke` use `${AGENT_API_PORT:-8003}`.
- No remaining hardcoded `http://localhost:8000` in scripts that are part of the dev loop (dev, health, smoke, quick start).
- Docs reference API 8003 and `/unified` as the default UI route (already reflected in PORTS.md and INDEX.md).

Phased Plan
- Phase 1 (done): Makefile targets and `scripts/sophia.sh` updated.
- Phase 2 (next): Update `scripts/*health*.sh`, `setup_asip_complete.sh`, `verify_slack_webhook.py`, and quick-start validation scripts.
- Phase 3: Docs/OpenAPI sample URLs and monitoring helpers.
- Phase 4: Legacy/archived scripts reviewed; either parameterized or explicitly tagged as legacy with a note.

Validation
- `AGENT_API_PORT=8003 make ui-up` starts on 8003
- `AGENT_API_PORT=8004 make ui-up` starts on 8004 and health checks target 8004
- Grep sanity: `rg -n "http://localhost:8000|:8000\b" Makefile scripts -S` shows no matches in dev-loop scripts

Notes
- Do not store secrets in repo; ports are not secrets.
- No changes to MCP ports (8081/8082/8084) or telemetry (5003).

Assignee: TBD
Priority: Medium
Status: In Progress

