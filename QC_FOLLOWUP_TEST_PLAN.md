# Quality Control Follow‑Up: Improvements and Testing Plan

This document captures the next layer of hardening and tests for the multi‑agent stack. It complements existing health checks with concrete, automated smoke and policy tests to keep the stack fast, resilient, and correct.

## Objectives
- Prove critical paths work across WebUI → Router → MCP → Storage.
- Catch regressions via CI smoke (fast, deterministic; no secrets required).
- Exercise policies (FS deny, Git protected branches), and memory/search round‑trip.

## Scope (v1)
- WebUI backend: /health, /agents/complete, /tools/invoke (fs|git|memory)
- MCP: memory|fs|git /health endpoints
- Policy: FS deny (.env write), Git protected branch push denial (status only in v1)

## Approach
- Use docker‑compose to start the minimum set of services:
  - redis, weaviate, mcp-memory, mcp-filesystem-sophia, mcp-git, swarm-orchestrator, webui
- Wait for health; run a Python smoke script (scripts/ci_smoke_test.py) that:
  - Confirms WebUI /health is OK
  - Calls /agents/complete with a minimal generation task (max tokens by default)
  - Calls /tools/invoke memory.store + memory.search
  - Calls /tools/invoke fs.list on repo root
  - Attempts /tools/invoke fs.write to .env (expect 403)
  - Confirms MCP /health endpoints respond (ports 8081–8084)

## Acceptance Criteria
- All health checks return 200; smoketest returns success (exit 0)
- FS write to `.env` is denied with 403 and actionable message
- Memory store/search round‑trip succeeds
- Router selection returns route metadata (provider/model) in /agents/complete

## Future Additions
- WS token streaming envelope tests (per‑session queue)
- Router circuit breaker/budgets + metrics assertions
- Indexer tombstones + symbol/doc upserts; provenance injection to router/WebUI
- Git PR path for protected branches

