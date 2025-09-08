# Multi-Agent Plan Addendum (Supersession, Env, Immediate Steps)

This addendum reconciles prior plans with the finalized terminal-first design, clarifies environment separation, and records the concrete artifacts added in this update.

- Single source of truth: TERMINAL_FIRST_MULTI_AGENT_ECOSYSTEM_MASTER_PLAN.md
- Supersedes overlapping runtime/compose instructions in older docs; use the files and commands below.

## Environment Separation
- .env.sophia → Infra/business only (no LLM keys). Example: .env.sophia.example
- .env.mcp → MCP runtime ports/settings. Example: .env.mcp.example
- .env (optional) → Local CLI convenience for quick tests only.
- .env.artemis (external, in artemis-cli) → IDE/CLI provider keys: OPENAI, ANTHROPIC, XAI, OPENROUTER.

Policy: Keep provider keys out of this repo’s infra envs. Rotate any previously exposed secrets; ensure logs redact secrets.

## New/Updated Artifacts
- docker-compose.multi-agent.yml → Canonical dev stack (agent-dev, redis, weaviate, MCP servers, swarm, webui).
- scripts/quick-grok-test.sh → One-off Grok test in python:3.11-slim.
- scripts/multi-agent-docker-env.sh → Compose wrapper (up/down/logs/shell/status).
- scripts/sophia_cli.py → Minimal CLI stub for Makefile.dev references (swarm start/status; memory placeholder).
- Makefile → Terminal-first targets: dev-up, dev-down, dev-shell, status, logs, grok-test, swarm-start, memory-search.
- .env.sophia.example and .env.mcp.example → Clean examples per domain.

## Quick Start
- make env-check
- make dev-up && make status
- make grok-test
- make swarm-start TASK="Create authentication endpoint"

Refer to the master plan file for architecture, acceptance criteria, and phased rollout.
