# Agents Contract: Sophia ⇄ Artemis (Sidecar)

This document is the contract that keeps humans and AI agents aligned. It defines clear scope, ownership, interfaces, startup flow, and hard rules that prevent code mixing between repos.

## Ownership and Purpose

- Sophia (repo: `ai-cherry/sophia-intel-ai`)
  - Purpose: Business Intelligence platform for Pay Ready.
  - Owns: business agents, integrations (Slack, Gong, etc.), memory (Weaviate), cache (Redis), platform APIs, production dashboards, and MCP servers (Memory/FS/Git).
  - Production runtime lives here.

- Artemis (repo: `ai-cherry/artemis-cli`)
  - Purpose: AI Agent Factory + Orchestrator that builds and maintains Sophia.
  - Owns: Agent Designer, Swarm Composer, Chat service, LLM routing/management, Voice (ElevenLabs), developer CLI/UI.
  - Artemis is a sidecar dev tool and never ships to production directly; it raises PRs to Sophia.

## Interfaces (how they talk)

- MCP (from Sophia)
  - Memory MCP (default dev port): `http://localhost:8081`
  - FS Sophia MCP: `http://localhost:8082`
  - FS Artemis MCP (opt‑in): `http://localhost:8083` (enabled when `ARTEMIS_PATH` is set)
  - Git MCP: `http://localhost:8084`

- HTTP (from Artemis)
  - `GET /health`
  - `GET /personas`
  - `POST /chat { persona_id, messages, voice? } → { text, audio_url?, route }`
  - `POST /simulate { swarm_id, messages } → { steps, tools, tokens, cost }`
  - `GET/POST /agents` (CRUD AgentConfig; updates persisted via Git MCP commits)
  - `GET/POST /swarms` (CRUD SwarmGraph; persisted via Git MCP commits)
  - `GET/POST /llms/*` (LLM providers, models, routing policies)
  - `POST /voice/preview { text, voice_id } → { audio_url }`

## Hard Rules (enforced by CI/Pre‑commit)

- No cross‑imports: Artemis must never import Sophia; Sophia must never import Artemis.
- Integration is ONLY via MCP + HTTP endpoints.
- No secrets in repos. All secrets in `~/.config/artemis/env` (local) or a vault (prod).
- Sophia’s root: only whitelisted `.md`; only `.env`, `.env.local`, `.env.template` allowed.
- Sophia repo must not contain `app/artemis/**` or `scripts/artemis_*`.
- Artemis repo must not contain `app/sophia/**` or Sophia code.

## Startup (dev)

- Sophia side:
  - `cd ~/sophia-intel-ai`
  - `source scripts/env.sh --quiet`
  - `scripts/dev.sh all`  (starts Redis/Postgres/Weaviate + MCP; health checks)
  - `make mcp-test`

- Artemis side:
  - `cd ~/artemis-cli`
  - `docker compose up -d`  (chat/UI if defined in that repo)
  - Verify: `curl -sf http://localhost:<artemis_chat_port>/health`

- Link FS Artemis (optional):
  - In Sophia: `export ARTEMIS_PATH=~/artemis-cli`
  - `docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis`

- UI backend (host‑run in Sophia):
  - `export MCP_MEMORY_URL=http://localhost:8081`
  - `export MCP_FILESYSTEM_SOPHIA_URL=http://localhost:8082`
  - `export MCP_GIT_URL=http://localhost:8084`
  - `export MCP_FILESYSTEM_ARTEMIS_URL=http://localhost:8083` (if FS Artemis enabled)
  - `export ARTEMIS_CHAT_URL=http://localhost:<artemis_chat_port>`
  - `make ui-up` → `make ui-health` → `make ui-smoke`

## Keys and Secrets

- All secrets are stored in `~/.config/artemis/env`.
- Required keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PORTKEY_API_KEY`, `ELEVENLABS_API_KEY`, `JWT_SECRET`, `POSTGRES_URL`, `REDIS_URL`, `WEAVIATE_URL`.
- Optional: `GROK/XAI`, `OPENROUTER`, `SLACK_API_TOKEN`, `GONG_ACCESS_KEY`.

## Agent & Swarm Schema (high‑level)

- AgentConfig: persona (voice/model), llm settings, tools (MCP allowlist), memory scope, safety (allow_commit), version metadata.
- SwarmGraph: nodes (agents), edges (routing conditions), policies (routing/cost/concurrency), version metadata.

## CI/Pre‑commit Guardrails

- Sophia: block Artemis paths; enforce root doc whitelist; env variant guard; CODEOWNERS for env/compose/webui/mcp.
- Artemis: block Sophia paths; enforce MCP/HTTP only; CODEOWNERS for chat/registry/ui.

This contract is the source of truth. Any change to responsibilities or interfaces must update this file and both repos.

