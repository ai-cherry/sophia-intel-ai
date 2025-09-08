# Unified Development Environment

This repository uses a single, canonical dev stack centered on `docker-compose.dev.yml`.

Core workflow
- Start: `docker compose -f docker-compose.dev.yml up -d`
- Shell: `docker compose -f docker-compose.dev.yml exec agent-dev bash`
- Stop:  `docker compose -f docker-compose.dev.yml down`

Environment
- Copy: `cp .env.template .env` and adjust for local dev.
- Secrets: Store provider keys in `~/.config/artemis/env` via `make artemis-setup`.
- Validate: `make env.check`

MCP endpoints (for Cursor/Cline)
- Filesystem: `http://localhost:8082`
- Memory:     `http://localhost:8081`
- Git:        `http://localhost:8084`
- VS Code settings are written in `.vscode/settings.json` and should work out-of-the-box.

SSH (Git via SSH agent)
- Ensure SSH agent is running and key loaded (`ssh-add -l`).
- Compose forwards `SSH_AUTH_SOCK` into containers that need it.

Artemis (optional)
- Some services reference `../artemis-cli`. We will gate this behind a profile and `${ARTEMIS_PATH}` in a follow-up change so daily dev remains single-repo by default.

Notes
- `Makefile.dev` is deprecated; use `Makefile` targets.
- Other compose variants (`docker-compose.yml`, `*.enhanced.yml`, `*.multi-agent.yml`) are non-canonical for daily dev.

