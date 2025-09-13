# Sophia Intel AI – Canonical Ports

- 3000 – Agent UI (Next.js)
- 8000 – Unified API (FastAPI, backend/main.py)
- 8080 – Weaviate (vector DB)
- 8081 – MCP Memory
- 8082 – MCP Filesystem
- 8084 – MCP Git
- 8085 – MCP Vector (Weaviate-backed)
- 9090 – Prometheus (dev)
- 3001 – Grafana (dev)

Defaults are exported by `scripts/lib/ports.sh`. Override via env.

External server-only UIs (kept in sibling repos):
- 3100 – Forge UI (server-only Fastify)
- 3200 – Workbench (server-only Fastify)
