# Sophia Intel AI — Canonical Local Deployment (Native-First)

This is the single source of truth for running Sophia locally.

## Overview

- Infra in containers: Redis (6379), Weaviate (8080)
- API native: FastAPI on `:8003`
- UI native: Next.js on `:3000`
- Environment: `<repo>/.env.master` (single source)

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker

## Environment

Create `<repo>/.env.master`:

```
PORTKEY_API_KEY=...
OPENROUTER_API_KEY=...
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
# Optional
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

## Run

Use Make targets:

```
make local        # start infra + API + UI
make local-status # show API/UI PIDs
make local-stop   # stop API/UI and containers
```

Behind the scenes these run `scripts/local_up.sh` and `scripts/local_down.sh`.

## Verify

```
curl -sf http://localhost:8003/health
curl -sf http://localhost:8080/v1/.well-known/ready
open http://localhost:3000
```

## Notes

- The API will initialize external providers via Portkey/OpenRouter if keys are present; otherwise it will boot and log a warning.
- Logs: `logs/api.log`, `logs/ui.log` — PIDs: `.pids/api.pid`, `.pids/ui.pid`
- To change the API port, set `AGENT_API_PORT` before `make local`.
