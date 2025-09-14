# Sophia ↔ Sophia Sidecar Architecture

Purpose
- Sophia (repo: ai-cherry/sophia-cli) is the engineering sidecar: MCP servers, CLI, orchestrators, and agents that build, maintain, and enhance Sophia.
- Sophia (this repo) is the business intelligence system: APIs, memory, integrations (Slack, Gong, etc.), its own agent factory and dashboard.

Boundaries
- Sophia repo must not contain Sophia orchestrators/servers/CLI (blocked by CI).
- Sophia repo must provide MCP/HTTP endpoints consumed by Sophia during development or CI.

Integration
- Local dev (recommended): clone both repos side-by-side and set `SOPHIA_PATH` in `.env`.
- Compose: `docker-compose.dev.yml` supports an `sophia` profile to connect to Sophia sidecar.
- Protocols:
  - MCP: filesystem, git, memory, code-analysis (http://localhost:8081/8082/8084, or as configured)
  - HTTP: Sophia technical API if exposed by sophia-cli

Setup (combined)
1) Clone both repos:
   - `git clone git@github.com:ai-cherry/sophia-intel-ai.git`
   - `git clone git@github.com:ai-cherry/sophia-cli.git ../sophia-cli`
2) Environment:
   - `cp .env.template .env && make env.doctor.merge`
   - Set `SOPHIA_PATH=/absolute/path/to/sophia-cli` in `.env`
3) Start:
   - `docker compose --env-file .env.local -f docker-compose.dev.yml --profile sophia up -d`

CI/Guardrails
- `.github/workflows/anti-fragmentation.yml` blocks Sophia-specific paths in this repo.
- Pre-commit and CI also block env/doc sprawl.
