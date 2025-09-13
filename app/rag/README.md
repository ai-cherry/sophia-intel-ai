Sophia/Sophia RAG Services

Overview
- Two optional microservices provide domain-scoped memory for RAG:
  - sophia_memory (BI context) on port 8767
  - sophia_memory (code context) on port 8768
- Start via Docker profile toggles in `infra/docker-compose.yml` or extend `scripts/dev/start_local_unified.sh` to include RAG services.

Health & Version
- GET `/health` → `{ status, domain, backends, warnings }`
- GET `/ready` → `{ status: "ready", domain }`
- GET `/live` → `{ status: "alive", domain }`
- GET `/version` → `{ version, service }`

Core Endpoints
- POST `/index` (both services)
  - Body: `{ content: string, metadata?: object, source?: string, type?: string, id?: string }`
  - 413 on oversized content (configurable)
- POST `/index-code` (sophia only)
  - Body: `{ code: string, filepath: string, metadata?: object, language?: string, id?: string }`
- POST `/query`
  - Body: `{ query: string, domain?: string, limit?: number, include_context?: boolean, filters?: object }`
  - Response: `{ results: [...], domain, timestamp, context_used, total_results }`
- GET `/stats` → backend and count info

Authentication
- Bearer auth is configurable; when enabled:
  - Send header: `Authorization: Bearer <token>`
  - On 401, response sets `WWW-Authenticate: Bearer` and JSON envelope: `{ error: { code, type, message } }`
  - OpenAPI defines `BearerAuth` security scheme.

Rate Limiting
- Enabled when Redis is available.
- On 429, JSON envelope: `{ error: { code: 429, type: "rate_limit", message: "Rate limit exceeded" } }`
- Header `Retry-After: <seconds>` indicates when to retry.
- Limiter fails open if Redis is down (no blocking).

Fallbacks
- Weaviate optional. If unavailable, searches fall back to:
  - Redis keyword/index lookups
  - File-tier JSON cache under `/tmp/<domain>_memory/docs` when persistence enabled
- Health endpoint reports backends and warnings (e.g., no vector storage).

Examples (curl)
- Health: `curl -s http://localhost:8767/health | jq`
- Index (sophia):
  `curl -s -X POST http://localhost:8767/index -H 'Content-Type: application/json' -d '{"content":"Q2 revenue up 14%","metadata":{"source":"analytics"}}'`
- Index code (sophia):
  `curl -s -X POST http://localhost:8768/index-code -H 'Content-Type: application/json' -d '{"code":"def add(a,b): return a+b","filepath":"app/util/math.py"}'`
- Query:
  `curl -s -X POST http://localhost:8767/query -H 'Content-Type: application/json' -d '{"query":"revenue growth","limit":5}' | jq`

Auth Header Example
- `curl -H 'Authorization: Bearer $MEMORY_API_KEY' http://localhost:8767/health`

Notes
- For local development on macOS with potential wheel/arch mismatches, prefer devcontainer or run `scripts/agents_env_check.py` for remediation steps.
