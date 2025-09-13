# Sophia Intel AI – Canonical Ports

- 3000 – Agent UI (Next.js)
- 8000 – Unified API (FastAPI, backend/main.py)
- 8080 – Optional proxy (Nginx; use 8085 if 8080 conflicts)
- 8081 – MCP Memory
- 8082 – MCP Filesystem
- 8084 – MCP Git
- 9090 – Prometheus (dev)
- 3001 – Grafana (dev)

Defaults are exported by `scripts/lib/ports.sh`. Override via env.
