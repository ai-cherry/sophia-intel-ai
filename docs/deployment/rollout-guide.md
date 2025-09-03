---
title: Fly-First Rollout Guide
status: active
version: 2.1.0
last_updated: 2025-09-03
---

# Fly-First Rollout Guide

This guide standardizes local and cloud deploys for Sophia Intel AI. It aligns ports, health endpoints, and Fly configs with the actual build artifacts.

## Service Ports

- Unified API: 8003 (health: /healthz)
- MCP Server: 8004 (health: /health)
- Vector Store: 8005 (health: /health)
- Weaviate: 8080 (health: /v1/.well-known/ready)
- Bridge: 7777 (health: /healthz)
- Agent UI: 3000

## Local Development

Use the enhanced local script (repository‑relative, health checks, ADR‑006 validation):

```bash
# From repo root
./start-local.sh start     # or: ./start-local.sh status|logs|health|clean

# Alternate one-shot launcher
./deploy_local.sh --clean
```

Verify health locally:

```bash
curl -f http://localhost:8003/healthz
curl -f http://localhost:7777/healthz
curl -f http://localhost:8080/v1/.well-known/ready
```

## Fly.io Deployment

1. Configure secrets per app (never commit secrets):

```bash
fly secrets set OPENROUTER_API_KEY=... PORTKEY_API_KEY=... --app sophia-api
fly secrets set AGNO_API_KEY=... --app sophia-bridge
fly secrets set ... --app sophia-mcp
fly secrets set ... --app sophia-vector
```

2. Deploy services using existing Dockerfile:

```bash
fly deploy --config fly-unified-api.toml     # Unified API (8003)
fly deploy --config fly-agno-bridge.toml     # Bridge (7777)
fly deploy --config fly-mcp-server.toml      # MCP (8004)
fly deploy --config fly-vector-store.toml    # Vector Store (8005)
fly deploy --config fly-agent-ui.toml        # Agent UI (3000)
```

3. Health checks (public URLs shown; adjust per app name/region):

```bash
curl -f https://sophia-api.fly.dev/healthz
curl -f https://sophia-bridge.fly.dev/healthz
curl -f https://sophia-mcp.fly.dev/health
curl -f https://sophia-vector.fly.dev/health
```

## Notes

- Dockerfile now exposes 8003 and implements /healthz for the Unified API.
- Fly TOMLs no longer reference missing Dockerfiles and do not enable Consul.
- Bridge CORS defaults are restricted for production; override via Fly secrets if necessary.
- Agent UI proxies to http://localhost:8003 during local development.

