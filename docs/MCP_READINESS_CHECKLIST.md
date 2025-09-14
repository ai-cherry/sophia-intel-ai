# MCP Servers — Best State and Format (Readiness Checklist)

Purpose: Make all MCP servers consistent, secure, testable, and easy to consume by MCP clients (Cline, Roo/Claude) and internal automation.

This repository already includes:
- Stdio MCP server: tools/mcp/fs_memory_stdio.py (fs, memory, repo.index, git)
- Canonical HTTP FastAPI servers:
  - Memory: mcp/memory_server.py → 8081
  - Filesystem: mcp/filesystem/server.py → 8082
  - Git: mcp/git/server.py → 8084
  - Vector: mcp/vector/server.py → 8085

This document defines “best state and format” for both stdio and HTTP MCP services.

Preferred vs. Canonical
- Preferred transport model (for AI clients Cline/Roo/Claude): stdio MCP servers launched as processes, speaking JSONL over stdin/stdout. Use tools/mcp/fs_memory_stdio.py or additional *_stdio.py servers for low-latency local repo ops.
- Canonical service modules (for HTTP/internal services): fixed FastAPI apps used by scripts/infra as the single source of truth for REST-style access and standardized boot:
  - mcp/memory_server.py → 8081
  - mcp/filesystem/server.py → 8082
  - mcp/git/server.py → 8084
  - mcp/vector/server.py → 8085

In short: preferred = how AI clients connect (stdio). canonical = which module/port infra runs (HTTP). Keep both in sync; stdio serves interactive/local tool calls, while HTTP powers dashboards/automation and external integrations.

-------------------------------------------------------------------------------

1) Transport Standards

Stdio (preferred for AI clients like Cline/Roo/Claude)
- Requirement:
  - Single process spawned by the client with command + args (no ports)
  - Newline-delimited JSON (one response per line) with request.id echoed
  - initialize method returning:
    - server identifier (e.g., fs-memory-stdio)
    - capabilities list (e.g., fs.* / memory.* / repo.index / git.*)
- Error format:
  - Always include {"id": <orig id>, "error": "<message>"} on failures
- Determinism:
  - Idempotent read/search/list methods
  - Side-effecting methods documented and safe

HTTP (for internal REST integrations and services)
- Requirement:
  - FastAPI/uvicorn
  - Consistent base paths and standard endpoints:
    - GET /health → {"status":"healthy"} 200
    - Optional: /metrics (Prometheus) if enabled
- Security:
  - Auth headers/tokens for production
  - CORS as needed for specific UIs
- Deployment:
  - Use uvicorn with explicit host/port and graceful shutdown
  - Avoid auto-reload in production

-------------------------------------------------------------------------------

2) Naming, Layout, and File Structure

- Stdio servers:
  - Location: tools/mcp/<server_name>_stdio.py
  - One module per server; clear capabilities list in initialize()
- HTTP servers:
  - Location: mcp/<domain>/server.py or mcp/<domain>_server.py
  - FastAPI app named app
  - Start with: python3 -m uvicorn mcp.<module_path>:app --host 0.0.0.0 --port <PORT>
- Policies and configs:
  - mcp/policies/<domain>.yml (allowlists, constraints)
- Tests:
  - tests/mcp/test_<server>_stdio.py (stdio contract tests)
  - tests/integration/test_mcp_servers.py (HTTP health + basic routes)

Forbidden/Deprecated
- Legacy modules: mcp/filesystem.py, mcp/git_server.py, mcp/vector_search_server.py, mcp/enhanced_vector_server.py, mcp/simple_vector_server.py
- Any references to LiteLLM (removed across env/docs/scripts)

-------------------------------------------------------------------------------

3) Tool Design (Contract and Schema)

- Each tool must define:
  - name (short, lowercase + dot segments, e.g., fs.read, git.status)
  - description (concise, actionable)
  - input schema (JSON Schema) with "type": "object", properties, required list
- Input validation:
  - Reject unknown fields or sanitize/ignore them; return structured error
- Examples:
  - fs.read
    - properties: { "path": {"type":"string"}, "max_bytes": {"type":"number"} }
    - required: ["path"]
  - repo.index
    - properties: { "root": {"type":"string"}, "max_bytes_per_file": {"type":"number"} }
    - required: ["root"]

-------------------------------------------------------------------------------

4) Security Baselines

- Never hardcode secrets (use .env.master; CI injects for prod)
- Minimal surface:
  - Stdio servers operate on a fixed workspace root
  - For filesystem ops, enforce:
    - Path sandboxing: Realpath must start with REPO_ROOT
    - Allowlist of extensions or explicit policies
- Timeouts:
  - Bound expensive operations (searches, repo.index) with caps (max files/bytes)
- Rate limiting and bulkhead (HTTP):
  - Use uvicorn workers + middleware timeouts as needed
- Logging:
  - No secrets in logs; redact tokens/keys; structured JSON or key=value
- Auth (HTTP prod):
  - Header token (e.g., MCP_TOKEN) with dev bypass OFF:
    - ENV: MCP_DEV_BYPASS=false; token required

-------------------------------------------------------------------------------

5) Observability and Logs

- Stdio:
  - Write to stdout ONLY for protocol; stderr for server logs if needed
  - Include timestamps and minimal fields in stderr logs
- HTTP:
  - logs/mcp-*.log for each service (rotated by logrotate or systemd)
- Metrics (optional):
  - Expose Prometheus /metrics
  - Report counts/latency for tools and errors

-------------------------------------------------------------------------------

6) Configuration and Environment

- Single source: .env.master (already enforced repository-wide)
- Variables:
  - MCP_DEV_BYPASS=true (dev only), false in production
  - MCP_TOKEN for HTTP servers when dev_bypass=false
  - Ports:
    - 8081 memory, 8082 fs, 8084 git, 8085 vector (avoid collisions)
- Client settings (Cline/Roo):
  - Always include disabled=false and autoApprove=[] in mcpServers entries
  - Absolute paths to command args (macOS spaces-safe)
- Example (already registered):
  "fs-memory": {
    "command": "python3",
    "args": ["/Users/lynnmusil/sophia-intel-ai/tools/mcp/fs_memory_stdio.py"],
    "env": {},
    "disabled": false,
    "autoApprove": []
  }

-------------------------------------------------------------------------------

7) Health and Readiness

- Stdio readiness (one-liner):
  printf '%s\n' '{"id":"1","method":"initialize"}' | python3 tools/mcp/fs_memory_stdio.py
  - Expect: {"id":"1","result":{"server":"fs-memory-stdio", ...}}
- HTTP readiness (curl):
  curl -sS http://localhost:8081/health
  curl -sS http://localhost:8082/health
  curl -sS http://localhost:8084/health
  curl -sS http://localhost:8085/health
  - Expect: {"status":"healthy"} with 200

-------------------------------------------------------------------------------

8) Testing and CI

- Unit tests (stdio):
  - initialize returns capabilities
  - Each tool validates inputs and returns success/error predictably
- Integration tests (HTTP):
  - /health and minimal tool routes if applicable
- Contract tests:
  - JSON schema conformance (types, required)
  - Path sandbox guarantees for fs tools
- Coverage target: ≥80%
- Pre-commit:
  - ruff/flake8 (Python), black formatting, mypy types (type hints required)
- CI pipeline steps:
  - Lint → Type-check → Unit tests → Integration tests
  - Fail CI if legacy servers or litellm remnants are detected

-------------------------------------------------------------------------------

9) Performance & Resource Limits

- Stdio:
  - Avoid loading entire repo in memory; stream reads; cap search results
- HTTP:
  - uvicorn --workers=N for parallelism (CPU cores)
  - HTTP timeouts; keep-alive pooling when calling out (if any)
- Vector/Index:
  - Batch sizes; chunk sizes; backpressure when indexing large repos

-------------------------------------------------------------------------------

10) Operations and Lifecycle

- Unified startup (dev): ./unified-system-manager.sh start
  - Ensures 8081/8082/8084/8085 active; logs in logs/mcp-*.log
- Cleanup:
  - ./sophia clean stops services, clears PID files, releases ports
- Versioning:
  - Semver-ish tags for server changes; CHANGELOG.md entries
- Backups:
  - When editing MCP client settings, back up JSON before patching
  - Scripted edits only via jq (atomic tmp → mv)

-------------------------------------------------------------------------------

11) Migration and Consistency

- Ensure all docs/scripts refer ONLY to canonical paths:
  - mcp/memory_server.py
  - mcp/filesystem/server.py
  - mcp/git/server.py
  - mcp/vector/server.py
- Remove/guard legacy variants:
  - mcp/filesystem.py (legacy) — must not exist in usage
  - mcp/git_server.py (legacy) — must not exist in usage
- Confirm no LiteLLM mentions across env/docs/scripts (Portkey-only routing policy)

-------------------------------------------------------------------------------

12) Quick Readiness Checklist (Actionable)

- [ ] .env.master present and chmod 600; MCP_DEV_BYPASS set for env (true in dev, false in prod)
- [ ] Stdio server tools/mcp/fs_memory_stdio.py responds to initialize (one-liner sanity check)
- [ ] Cline and Roo/Claude configs contain fs-memory entry (disabled=false, autoApprove=[])
- [ ] HTTP servers healthy on 8081/8082/8084/8085 (curl /health returns 200) when used
- [ ] FS/Git path sandboxing enforced; policies/allowlists present if applicable
- [ ] No legacy modules referenced (mcp/filesystem.py, mcp/git_server.py)
- [ ] No LiteLLM references; Portkey-only policy enforced
- [ ] Unit + integration tests ≥ 80% coverage; pre-commit hooks pass (lint, type-check)
- [ ] Logs redact secrets; optional metrics consistent if enabled
- [ ] Unified startup works; ports free; cleanup script stops services

Quick commands

- Stdio init: printf '%s\n' '{"id":"1","method":"initialize"}' | python3 tools/mcp/fs_memory_stdio.py
- Start HTTP servers: ./unified-system-manager.sh start
- Verify ports: lsof -i :8081,:8082,:8084,:8085 || python3 tools/validate_ports.py
- Re-register client entries: bash ./register_mcp_clients.sh

Appendix: Client Config Examples

Cline (Cursor) — ~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
{
  "mcpServers": {
    "fs-memory": {
      "command": "python3",
      "args": ["/Users/lynnmusil/sophia-intel-ai/tools/mcp/fs_memory_stdio.py"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}

Claude Desktop / Roo — ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "fs-memory": {
      "command": "python3",
      "args": ["/Users/lynnmusil/sophia-intel-ai/tools/mcp/fs_memory_stdio.py"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
