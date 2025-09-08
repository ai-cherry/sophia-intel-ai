# Artemis Runbook (Sidecar Dev)

Artemis is the AI Agent Factory and dev Orchestrator for coding Sophia. It lives in `ai-cherry/artemis-cli` and integrates with Sophia via MCP + HTTP APIs.

## Prerequisites
- Docker Desktop + Docker Compose
- SSH access to GitHub (clone with SSH)
- Secrets in `~/.config/artemis/env` (shared with Sophia)
  - Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, PORTKEY_API_KEY, ELEVENLABS_API_KEY, JWT_SECRET, POSTGRES_URL, REDIS_URL, WEAVIATE_URL

## Clone and Start
- Clone with SSH:
  - `git clone git@github.com:ai-cherry/artemis-cli.git ~/artemis-cli`
  - `cd ~/artemis-cli`
- Start sidecar services:
  - `docker compose up -d`
- Verify chat service:
  - `curl -sf http://localhost:<chat_port>/health`

## Link to Sophia (Filesystem)
- In Sophia repo:
  - `export ARTEMIS_PATH=~/artemis-cli`
  - `docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis`

## Keys Check (suggested target for artemis-cli)
- Add a simple env loader like Sophia’s `scripts/env.sh` and a `keys-check` target.
- Verify required keys are present and well‑formed.

## Development Workflow
- Agent Designer (UI/API): create and edit `config/agents/*.json`
- Swarm Composer (UI/API): create and edit `config/swarms/*.json`
- LLM Management: configure providers/models/routing in `config/llms/*`
- Voice: set ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID; preview TTS via `/voice/preview`
- Persist changes via Git MCP commits (commit messages include persona/task context).
- Artemis opens PRs to Sophia; no direct pushes to Sophia main.

## Endpoints (example)
- `GET /health`
- `GET /personas`
- `POST /chat { persona_id, messages, voice? } → { text, audio_url?, route }`
- `POST /simulate { swarm_id, messages } → { steps, tools, tokens, cost }`
- `GET/POST /agents`, `GET/POST /swarms`, `GET/POST /llms/*`
- `POST /voice/preview { text, voice_id } → { audio_url }`

## Tests (Artemis)
- Unit tests for chat/registry/voice/llm routing.
- Integration tests call MCP endpoints (Sophia must be up): FS/Git/Memory.

## One‑Click Ideas (to add in artemis-cli)
- `make artemis-up`: docker compose up -d
- `make artemis-health`: curl /health and provider checks
- `make keys-check`: mirrors Sophia’s env doctor for Artemis keys

Artemis never imports Sophia. All collaboration flows through MCP + HTTP.

