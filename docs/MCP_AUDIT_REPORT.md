MCP Servers Audit and Improvement Plan

Date: 2025-09-13
Owner: Codex (agent_codex)

Summary
- Canonical MCP servers are present and healthy: memory (8081), filesystem (8082), git (8084).
- Additional vector search servers exist (8085 target) with overlapping purposes and inconsistent integration.
- Integrations with Forge and Portkey are partially implemented but fragmented. Key client/server endpoint mismatches exist.
- Deployment paths are duplicated across multiple scripts with inconsistent startup styles.
- Policy configuration contains a correctness issue (duplicate YAML keys overriding intended rules).

Servers and Purpose
- Memory (mcp/memory_server.py, 8081)
  - Purpose: Session memory storage with Redis; list/clear/search entries.
  - Auth: Optional bearer via MCP_TOKEN; dev bypass supported.
  - Gaps: Docstring claims embeddings; no embedding endpoints implemented. Client in app/services expects /memory/search while server exposes /search.

- Filesystem (mcp/filesystem/server.py, 8082)
  - Purpose: FS ops (list/read/write/delete), repository search/read/list, simple symbol indexing and dependency graph.
  - Indexing: In-memory symbol index; ephemeral and process-local. No persistent store or background refresh.
  - Policies: Loads from mcp/policies/filesystem.yml keyed by workspace.
  - Gaps: No direct integration to Portkey or vector stores; no hooks to update vector index on write/delete.

- Git (mcp/git/server.py, 8084)
  - Purpose: Git status/commit/push/log with policy enforcement (protected branches, force-push rules).
  - Policies: mcp/policies/git.yml (commit template, branch protection).
  - Notes: Exposes minimal VCS capabilities; no repo graph or PR integration here.

- Vector Search (mcp/vector_search_server.py; also enhanced_vector_server.py, simple_vector_server.py)
  - Purpose: Codebase semantic indexing and search (Weaviate + Postgres + Redis) with embeddings via OpenRouter.
  - Variants: A simplified SQLite variant (simple_vector_server.py) and an alternative enhanced server.
  - Gaps: Uses OpenRouter directly; Portkey is the governance gateway in this repo. Multiple variants create fragmentation.

Redundancies and Fragmentation
- Vector servers:
  - Three implementations exist (vector_search_server.py, enhanced_vector_server.py, simple_vector_server.py) with overlapping scope.
  - Only vector_search_server.py is referenced in deploy_local_complete.sh (port 8085). Others appear as legacy/demos.
  - Risk: Divergent behavior and maintenance burden; unclear which is authoritative.

- Forge MCP control:
  - builder-cli/forge.py imports MCPManager from builder_cli.lib.mcp, but builder_cli/lib contains no such module. Forge cannot manage MCP lifecycle as-is.
  - Risk: Broken orchestration path from Forge to MCP.

- Startup inconsistency:
  - bin/sophia-cli-v2 starts memory via `python3 mcp/memory_server.py` and others via `uvicorn module:app`.
  - Several scripts duplicate MCP startup logic: deploy_swarm_local.sh, deploy_local_complete.sh, scripts/start_all_mcp.sh, scripts/dev/bootstrap_all.sh, scripts/mcp_master_startup.py.
  - Risk: Drift and inconsistent flags/env across entrypoints.

Integration with Portkey and Forge
- Portkey
  - Strong usage for LLM routing (app/core/portkey_manager.py) and a dedicated embedding gateway (app/embeddings/portkey_integration.py).
  - MCP servers do not leverage Portkey directly (vector server uses OpenRouter; filesystem/memory have no Portkey hooks).

- Forge (builder_cli)
  - CLI integrates agents, router, bridge, and references MCPManager, but library module is missing; MCP orchestration via Forge is currently inoperable.
  - Bridge/Router exist, but no direct wiring observed from Forge to the filesystem index/symbols for contextual prompts.

Client/Server Contract Mismatches
- Memory: Client expects `/memory/search` with `{namespace, query, limit}` (app/services/mcp_context.py: memory_search), server exposes `/search` with `{query, session_id?, limit}`.
- Filesystem: Client uses `/repo/list`, `/repo/search`, `/repo/read` — server implements these (OK). FS tests also expect these routes.
- Auth headers: app/services/mcp_context injects Authorization when MCP_TOKEN is set (OK).

Policies and Configuration Issues
- mcp/policies/filesystem.yml contains duplicate `sophia` keys; YAML will keep only the last, dropping allowed paths from the first block.
- Git policy loading is correct; FS policy loader may silently misconfigure due to duplicate keys.

Deployment (Local and Cloud)
- Local: Multiple startup scripts; canonical listing in docs/MCP_CANONICAL_SERVERS.md matches ports 8081/8082/8084. Vector server (8085) starts in deploy_local_complete.sh only.
- Cloud: Istio/Pulumi references for MCP ports exist; vector (8085) referenced in infrastructure/pulumi/esc-config.yaml.
- Health checks: scripts/smoke_test.py and others check 8081/8082/8084; vector health not uniformly checked.

Indexing, Meta-Tagging, and Update Flows
- Filesystem server provides:
  - Repo listing/search and symbol index in-process; no persistence, no background refresh.
  - No meta-tagging beyond language inference and basic symbol kind.
- Vector servers provide:
  - Content hashing, summaries, embeddings, and DB storage; current embeddings via OpenRouter, not Portkey.
  - No observed trigger from FS writes/deletes to re-index; indexing appears on-demand via `/index`.
- Memory server does not store meta-tags for code or provide embeddings; only session text entries.

Security and Governance
- MCP_TOKEN-based auth middleware exists on all three canonical servers; dev bypass supported via MCP_DEV_BYPASS.
- Git server enforces protected branch rules; Filesystem policies restrict writes.
- Missing: rate limiting on MCP endpoints; audit logging beyond basic logs; secret scanning on write paths.

Risks and Impact
- Fragmentation (vector servers, startup scripts) increases drift and operational complexity.
- Contract mismatch (memory search) breaks context building for agents relying on MCP.
- Lack of Portkey integration in vector/embedding path bypasses governance and observability.
- FS policy duplication may permit unintended writes or deny intended paths.

Recommendations (Target State)
1) Canonicalize MCP servers
   - Keep: memory (8081), filesystem (8082), git (8084), vector (8085).
   - Deprecate: enhanced_vector_server.py and simple_vector_server.py; fold capabilities into a single vector server with configuration toggles:
     - Mode: `sqlite` (local dev) vs `pg+weaviate` (prod).
     - Embeddings through Portkey gateway (provider/model configurable).

2) Fix client/server contracts
   - Memory: Add `/memory/search` alias accepting `{namespace, query, limit}` and map to existing `/search` parameters (namespace→session_id). Or update app/services/mcp_context to use `/search` consistently.
   - Provide `/memory/store` alias for clarity (optional), mapped to `/sessions/{id}/memory`.

3) Wire indexing updates
   - Filesystem server: on `/fs/write` and `/fs/delete`, enqueue re-index tasks (POST to vector `/index` for changed paths) with debounce to avoid thrash.
   - Expose `/symbols/index` and `/dep/graph` snapshots to vector server for enriched metadata.

4) Integrate Portkey for embeddings
   - Replace OpenRouter calls in `mcp/vector_search_server.py` with `app/embeddings/portkey_integration.PortkeyGateway.create_embeddings` using configurable provider/model.
   - Include request metadata (repo, file path, commit hash) for observability.

5) Standardize startup and health
   - Use `uvicorn mcp.<module>:app` for all four servers.
   - Consolidate startup logic into one script (scripts/start_all_mcp.sh) and have others delegate to it.
   - Add `/health` to vector server returning backend connectivity.

6) Repair Forge integration
   - Implement `builder_cli/lib/mcp.py` with `MCPManager` providing start/status/stop via uvicorn programmatic API or subprocess.
   - Ensure Forge’s `forge mcp status` aligns with ports 8081/8082/8084/8085.

7) Fix FS policy YAML
   - Merge duplicate `sophia` blocks; ensure allowed/denied paths include intended directories; validate on server startup.

8) Security hardening
   - Add rate limiting (e.g., via SlowAPI) and request logging with correlation IDs.
   - Enforce MCP_TOKEN in non-dev and add CSP/CORS tightening.
   - Validate FS write content for secrets (lightweight GitLeaks rules) before writing.

Improvement Plan (Phased)
- Phase 0: Contract and config fixes (low risk)
  - Add compatibility alias for memory `/memory/search` or update client to `/search`.
  - Fix `mcp/policies/filesystem.yml` duplicate keys; add startup validation with clear error.
  - Standardize server start commands to uvicorn across scripts.

- Phase 1: Canonicalize vector server
  - Choose `mcp/vector_search_server.py` as canonical; add `MODE=sqlite|pg_weaviate` with env-driven config to subsume simple/enhanced variants.
  - Implement `/health` to verify DB/vector backends; add tests.

- Phase 2: Portkey integration
  - Replace embedding calls with Portkey gateway; configure provider/model via env and route through `app/core/portkey_manager.py` to preserve governance.
  - Add audit logs for embedding requests (file path, size, latency, cached).

- Phase 3: FS→Vector reindex hooks
  - Filesystem server: after successful `/fs/write` or `/fs/delete`, POST to vector `/index` with the changed file/dir; include debounce and a toggle `INDEX_ON_WRITE`.
  - Add retry/backoff and offline queue if vector server unavailable.

- Phase 4: Forge MCP lifecycle
  - Implement `builder_cli/lib/mcp.py` (MCPManager) to start/stop/status MCP servers and call `/symbols/index` after startup.
  - Update Forge tasks to build code context via MCP before codegen/review.

- Phase 5: Security & Observability
  - Rate limiting middleware; structured logs with request IDs; uniform auth checks.
  - Extend `/health` with version/build info; add `/metrics` (Prometheus) optional.

Validation Checklist
- Unit tests for:
  - Memory search alias behavior and parameter mapping.
  - FS write/delete triggering reindex (mock vector endpoint).
  - Vector embedding through Portkey gateway with provider/model variations.
  - Policy loader catching duplicate keys.
- Integration tests:
  - End-to-end index on fresh repo; symbol search + vector search produce coherent results.
  - Forge MCP start/status works; context built before codegen.

Open Issues to Track
- Missing builder_cli MCPManager module; Forge commands currently fail.
- Multiple startup scripts can be retired once a single canonical runner is adopted.
- Vector server health not currently covered by smoke tests.

Research Agent Prompt (Best Practices Refresh)
Use this prompt with a web research agent to gather current best practices for MCP-like services (FastAPI microservices) for code intelligence and memory in AI engineering stacks:

"""
Research goals:
- Modern best practices (2024–2025) for:
  - Code intelligence microservices: repository search, symbol indexing, dependency graphs, and semantic code search.
  - Vector indexing for code: model selection, chunking strategies, metadata (repo, path, language, symbol boundaries), and background refresh.
  - Memory services for AI agents: schemas, TTL/retention, embeddings vs. text storage, retrieval patterns, and auth.
  - Governance/routing through API gateways (e.g., Portkey) for embeddings and LLM calls.
  - Observability: request tracing, metrics, structured logs, and cost tracking for AI calls.
  - Security: endpoint auth, rate limiting, secret scanning on writes, policy enforcement.

Context (stack):
- FastAPI-based MCP servers: memory (Redis), filesystem (local FS), git (CLI), vector (Weaviate+Postgres or SQLite mode).
- LLM/Embeddings via Portkey gateway; prefer provider-agnostic routing and caching.
- Agents/CLI: Forge (builder_cli) orchestrates coding tasks, needs up-to-date repo context.

Questions:
1. What are the current best practices for code-aware indexing (symbols, AST, cross-file deps) and syncing indexes on write/CI?
2. Recommended embedding models/pipelines for code (accuracy vs. cost), and how to route via gateways like Portkey.
3. How to structure memory services for multi-agent systems (namespacing, TTL, vector vs. keyword search, privacy controls).
4. Operational patterns for microservices: health/metrics, rate limiting, auth, configuration, blue/green deploys.
5. Proven designs to bridge FS actions to indexing updates reliably (webhooks, queues, idempotency).
6. Techniques to avoid duplication and keep a single source of truth across services and scripts.

Deliverables:
- A concise set of actionable recommendations tailored to the stated stack, with references to recent authoritative sources (2024–2025).
"""

Appendix: Notable Files
- Servers: mcp/memory_server.py, mcp/filesystem/server.py, mcp/git/server.py, mcp/vector_search_server.py
- Policies: mcp/policies/filesystem.yml, mcp/policies/git.yml
- Clients/Services: app/services/mcp_context.py, tests/test_mcp_context.py
- Portkey: app/core/portkey_manager.py, app/embeddings/portkey_integration.py
- Startup: bin/sophia-cli-v2, scripts/start_all_mcp.sh, deploy_local_complete.sh

