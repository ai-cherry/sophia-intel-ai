# AGENTS: How Sophia and Artemis Work (Read First)

This file explains where to code, how the repos connect, and how to start everything. If anything here changes, update this file and docs/AGENTS_CONTRACT.md immediately.

## Scope and Ownership

- Sophia (repo: ai-cherry/sophia-intel-ai)
  - Purpose: Business Intelligence product for Pay Ready.
  - Owns: business agents, integrations (Slack/Gong/etc.), memory (Weaviate), cache (Redis), platform APIs/dashboards, and MCP servers (Memory/FS/Git).
  - Production runtime lives here.

- Artemis (repo: ai-cherry/artemis-cli)
  - Purpose: AI Agent Factory + Orchestrator that codes Sophia.
  - Owns: Agent Designer, Swarm Composer, dev Chat, LLM routing/management, Voice (ElevenLabs), dev CLI/UI.
  - Sidecar only; never ships to prod directly. Submits PRs to Sophia.

## Integration (only these)

- MCP (from Sophia): Memory 8081, FS 8082, FS Artemis 8083 (optional), Git 8084
- HTTP (from Artemis): /health, /personas, /chat, /simulate, /agents, /swarms, /llms/*, /voice/preview

## Hard Rules

- No cross-imports between repos; integrate via MCP + HTTP only
- No secrets in repos; use ~/.config/artemis/env or a vault
- Sophia must not contain app/artemis/** or scripts/artemis_*
- Artemis must not contain app/sophia/** or Sophia code

## Simple Startup

- Sophia:
  - cd ~/sophia-intel-ai
  - source scripts/env.sh --quiet
  - make dev-all   # or: scripts/dev.sh all; make ui-up
  - Verify: make mcp-test; make ui-health; make ui-smoke

- Artemis:
  - cd ~/artemis-cli (clone with SSH)
  - docker compose up -d
  - Verify: curl -sf http://localhost:<chat_port>/health

- Optional FS Artemis:
  - In Sophia: export ARTEMIS_PATH=~/artemis-cli
  - docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis

## Keys

- Put all keys in ~/.config/artemis/env (never in repo)
- Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, PORTKEY_API_KEY, ELEVENLABS_API_KEY, JWT_SECRET, POSTGRES_URL, REDIS_URL, WEAVIATE_URL

## If Anything Changes

- Update this AGENTS.md and docs/AGENTS_CONTRACT.md
- Mirror changes in Artemis RUNBOOK/README

This is the source of truth for agents and humans. Follow it to avoid broken environments and mixed code.
