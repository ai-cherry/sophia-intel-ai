# Setup Guide

This document consolidates the on-boarding instructions that previously lived across `START.md`, `STARTUP_GUIDE.md`, and assorted audit reports. Keep `START_HERE.md` for day-to-day checklists; use this page when you want a single source of truth for environment prep and service lifecycle commands.

## Environment Policy
- The only checked-in template is `.env.master`. Use `./bin/keys edit` to create or update it (600 permissions).  
- `.env`, `.env.local`, and `.env.local.example` have been archived under `.repo_backup_*` to avoid drift and prevent secrets from entering git history.
- Populate keys for: OpenAI, Anthropic, OpenRouter, Groq, DeepSeek, Gemini, Perplexity, Postgres/Redis/Neo4j, and any MCP services you enable.

## Bootstrap Checklist
1. **Install prerequisites**
   - Python 3.11+
   - Node.js 18+ (for auxiliary tooling)
   - Docker (optional, but required for certain MCP stacks)
2. **Configure secrets**
   ```bash
   ./bin/keys edit        # opens $EDITOR with .env.master
   ./bin/keys show        # verify values (redacted)
   ```
3. **Start the platform**
   ```bash
   ./sophia start         # launches FastAPI, agents, MCP servers
   ./sophia status        # health + port summary
   ./sophia test          # smoke validation; consult ./logs for details
   ```
4. **Stop services when finished**
   ```bash
   ./sophia stop
   ```

## Apple Silicon Hardening Checklist
- Install Homebrew natively under `/opt/homebrew` and prepend `/opt/homebrew/bin` to `PATH` to avoid mixing Intel binaries.
- Install Xcode Command Line Tools (`xcode-select --install`) and verify `xcode-select -p` returns `/Library/Developer/CommandLineTools`.
- Use `nvm`/`asdf` to manage Node; confirm `node -p "process.arch"` prints `arm64` before building native addons.
- Validate Python TLS support with `python3 -c "import ssl"`; if it fails, rebuild Python/pyenv with Homebrew OpenSSL/Zlib headers.
- Install mkcert for trusted local HTTPS (`brew install mkcert && mkcert -install`).
- Prefer native arm64 Docker images; add `--platform=linux/amd64` only to services that truly require emulation. Tools like Colima (`colima start --arch arm64`) let you toggle architectures when unavoidable.

Run `./scripts/dev-preflight.sh` to lint these items automatically. Set `RESET_NEXT_CACHE=1` to purge any `.next` caches discovered in this repository or the bundled `workbench-ui` checkout.

## IDE & MCP Integration
- Cursor and Cline configs live under `.cursor/` and `.ai/`. They expect MCP servers on `127.0.0.1:8081` (memory), `8082` (filesystem), `8084` (git), plus any optional analytics/vector services you enable.
- Before opening the IDE, run `./sophia start` so the MCP health checks pass.

## Backend & Agents
- Primary API entry point: `app/api/main.py` (FastAPI).  
- Agents orchestrate via `agents/` and `sophia_core/`. Use `./dev ai …` helpers for CLI access.
- The unified router policy lives in `agno/routing.yaml`; update through the UI or via the `src/app/api/models/policy` endpoints in the Workbench UI repo.

## Documentation Map
- `README.md` — executive overview and architecture context.
- `START_HERE.md` — quick on-ramp for developers (kept at repo root for visibility).
- `docs/ARCHITECTURE.md` — canonical system architecture reference.
- `docs/reports/` — archived audits, test runs, compliance findings (all moved out of the root by the cleanup scripts).

## Maintenance Tips
- Rerun `scripts/cleanup/sophia_cleanup.sh` whenever new audit/test dumps accumulate in the root directory.
- Confirm `git status` after running cleanup; move anything you still need out of `.repo_backup_*` before deleting the folder.
- Avoid recreating `.env.local`; rely on `.env.master` + runtime overrides to keep secrets centralized.

## Troubleshooting Runbooks
- **Clear stale Next.js caches** (for the workbench UI bundle): `RESET_NEXT_CACHE=1 ./scripts/dev-preflight.sh` or manually `rm -rf workbench-ui/.next` followed by a fresh `npm ci` + `npx next build --no-cache`.
- **Mock Service Worker** – ensure the worker is only registered in development. In the browser console: `window.worker?.stop()`.
- **Port hygiene** – identify and terminate stragglers: `sudo lsof -i :8000` / `sudo lsof -i :8081` then `kill -15 <PID>`.
- **Docker networking** – containers hitting host services must use `http://host.docker.internal:<port>` on macOS. Test connectivity with `docker run --rm alpine sh -lc "apk add --no-cache curl; curl -sv http://host.docker.internal:8080"`.
- **DNS cache** – flush with `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` when hostnames ignore your `/etc/hosts` edits.
- **HTTPS parity** – after generating certificates via mkcert, configure FastAPI/Next.js dev servers with the issued `localhost.pem`/`localhost-key.pem` to align with production TLS.
- **Docker engine choice** – Colima (`brew install colima`) or OrbStack can offer faster arm64 containers and optional x86 virtualization; prefer per-service platform overrides instead of a global emulation default.
