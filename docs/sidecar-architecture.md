# Sophia ↔ Artemis Sidecar Architecture

Purpose
- Artemis (repo: ai-cherry/artemis-cli) is the engineering sidecar: MCP servers, CLI, orchestrators, and agents that build, maintain, and enhance Sophia.
- Sophia (this repo) is the business intelligence system: APIs, memory, integrations (Slack, Gong, etc.), its own agent factory and dashboard.

Boundaries
- Sophia repo must not contain Artemis orchestrators/servers/CLI (blocked by CI).
- Artemis repo must provide MCP/HTTP endpoints consumed by Sophia during development or CI.

Integration
- Local dev (recommended): clone both repos side-by-side and set `ARTEMIS_PATH` in `.env`.
- Compose: `docker-compose.dev.yml` supports an `artemis` profile to connect to Artemis sidecar.
- Protocols:
  - MCP: filesystem, git, memory, code-analysis (http://localhost:8081/8082/8084, or as configured)
  - HTTP: Artemis technical API if exposed by artemis-cli

Setup (combined)
1) Clone both repos:
   - `git clone git@github.com:ai-cherry/sophia-intel-ai.git`
   - `git clone git@github.com:ai-cherry/artemis-cli.git ../artemis-cli`
2) Environment:
   - `cp .env.template .env && make env.doctor.merge`
   - Set `ARTEMIS_PATH=/absolute/path/to/artemis-cli` in `.env`
3) Start:
   - `docker compose --env-file .env.local -f docker-compose.dev.yml --profile artemis up -d`

CI/Guardrails
- `.github/workflows/anti-fragmentation.yml` blocks Artemis-specific paths in this repo.
- Pre-commit and CI also block env/doc sprawl.

