# Sophia Intel App — Deep Quality Control Audit

Generated from repository analysis of the Sophia Intel app (backend FastAPI + frontend Next.js) and related integrations. This audit identifies strengths, risks, and concrete improvements to elevate reliability, security, performance, and developer experience.

## Executive Summary

- Overall maturity: Strong architecture and modularity; several production-readiness gaps remain.
- Highlights:
  - Unified FastAPI server with clean routers for Projects, Gong, Brain Ingest, Repository, Memory, etc.
  - ConnectorRegistry abstracts integrations (Slack, Gong, Asana, Linear, Airtable) with defensive fallbacks.
  - Solid Python tooling present (ruff/black/mypy/pytest configured in `pyproject.toml`).
  - Next.js app is modern (Next 15, Tailwind, React Query in places), with typed TS setup.
- Top risks (shortlist):
  - Lax CORS defaults (allow-all) in multiple FastAPI apps; rate limiter middleware not enabled.
  - Telemetry exists but is not initialized in the unified server; limited tracing/metrics coverage.
  - UI TypeScript `strict` disabled; raw `fetch` dispersed without centralized timeouts/validation; some hardcoded URLs.
  - 300+ TODO/FIXME/HACK markers indicate meaningful technical debt.
  - A few `pickle.load` usages and JSON file reads without robust trust boundaries or schema checks.

## Architecture & Scope (Conformance to AGENTS.md)

- Single unified backend on FastAPI (`app/api/unified_server.py`) wiring all feature routers, including:
  - Projects: `/api/projects/overview`, `/api/projects/sync-status`
  - Gong: `/api/gong/calls`, `/api/gong/client-health`
  - Brain: `POST /api/brain/ingest`
  - Repository, Memory, WS, Infrastructure, Integration Intelligence, etc.
- Next.js app located at `sophia-intel-app` (Next 15, app router) — compliant with “all dashboards live here”.
- MCP integration roles are present; tools exposed via repo/memory gateways.
- No cross-repo imports detected; secrets referenced via env (compliant with “no secrets committed”).

## Integrations Audit

- Connectors (Slack/Gong/Asana/Linear/Airtable) are well-factored via `ConnectorRegistry`:
  - `configured()` checks env presence; `fetch_recent()` guarded by retries in some (Asana/Linear/Airtable) and fallbacks to empty payloads.
  - Gong endpoints provide conservative, non-fatal fallbacks when credentials missing.
- Risks & improvements:
  - Standardize HTTP client: enforce `httpx.AsyncClient` with global timeouts, retry/backoff, and connection pooling for all connectors.
  - Circuit breaking: add breaker for flaky services and exponential backoff.
  - Rate limits & caching: cache recent results for read-heavy endpoints (short TTL Redis); avoid hammering APIs.
  - Credential validation endpoint: expose `/api/integrations/validate` to proactively test keys (non-invasive).
  - Observability: wrap calls with tracing spans and attributes (service, endpoint, latency, error cause).

## Backend API Quality (FastAPI)

- Strengths:
  - Routers are separated and prefixed; payloads defensive; memory ingest validates size and auth.
  - Pydantic models used for request bodies in sensitive endpoints (e.g., Brain Ingest).
- Gaps:
  - CORS: multiple apps allow `allow_origins=["*"]`. Recommendation: use environment-driven allowed origins (already present in `production_server.py`), and unify across servers.
  - Rate limiting: `app/api/middleware/rate_limit.py` exists but not enabled in unified server — enable with sensible defaults and endpoint overrides.
  - Authentication: ensure sensitive endpoints (ingest, cost dashboards, infra) enforce auth consistently. Brain Ingest has opt-in auth; recommend default-on via env.
  - Response models: add explicit response `pydantic` models for all endpoints to guarantee schema stability (use OpenAPI docs for verification).
  - Input validation: add stricter validation for query params (e.g., min/max limits on `limit`, `days`).
  - Error handling: central exception handlers mapping to structured error envelopes with correlation IDs.
  - Security hygiene: audit `pickle.load` usages to ensure only trusted, controlled paths; prefer safer serialization (JSON/MessagePack) or signed pickles limited to internal data.

## UI Quality (Next.js)

- Strengths:
  - Modern stack (Next 15), Tailwind, Radix UI, React Query used in parts.
  - Linting, formatting, and typecheck scripts defined.
- Gaps:
  - `tsconfig.json` has `strict: false`. Enable `strict: true` and resolve errors progressively (allow per-folder exceptions if needed).
  - Dispersed `fetch` without timeouts/validation; add an API client wrapper (AbortController-based timeouts, JSON parse, zod validation). Promote React Query for caching and retries.
  - Hardcoded URLs (e.g., `http://localhost:8005` in `ModelControlDashboard.tsx`). Replace with environment-driven base URLs (`NEXT_PUBLIC_API_BASE`).
  - Validation: add `zod` schemas for API responses and integrate with React Query (`zod` + `zod-fetch` or custom parser).
  - Testing: add Playwright E2E for primary flows and React Testing Library for critical components (dashboards, chat, ingest panel).
  - Accessibility: ensure focus management, ARIA attributes for dynamic components; run `eslint-plugin-jsx-a11y` checks.

## Observability & SRE

- Telemetry module is robust (`app/api/monitoring/opentelemetry_config.py`) with OTLP/Jaeger/Prometheus support but not initialized by default in the unified server.
- Recommendations:
  - Initialize telemetry during unified server startup (respecting `ENVIRONMENT`).
  - Add structured logging (JSON) with request IDs across ASGI stack; propagate correlation IDs to connectors.
  - Define SLOs for key endpoints (p95 latency, error rates), and wire alerts.
  - Expose `/metrics` and ensure Prometheus scraper config aligns with deployment.

## Security

- Strengths: Rate-limiter middleware implementation; optional auth for Brain Ingest; environment-based keys; documentation warns against secrets in repo.
- Gaps & actions:
  - Tighten CORS to configured origins; avoid `*` in production.
  - Enforce auth across sensitive endpoints; standardize auth dependency.
  - Validate payload sizes (already done in Brain Ingest); replicate for other upload endpoints.
  - Remove or sandbox `pickle.load` where possible; add integrity checks or sign data.
  - Add Content Security Policy (CSP) headers at proxy (Nginx) and Next.js security headers.
  - Dependency auditing: run `pip-audit`/`safety` and `npm audit` in CI; pin key backend deps if not already.

## Testing & CI

- Python: `ruff`, `black`, `mypy`, and `pytest` configured in `pyproject.toml` with coverage settings.
- Frontend: ESLint + Prettier configured; no visible component/E2E tests.
- Recommendations:
  - CI stages: lint (ruff, eslint), format check, typecheck (mypy, tsc --noEmit), backend tests (pytest), frontend tests (vitest/RTL), E2E (Playwright), security scan (bandit/safety/pip-audit, npm audit), image build (if applicable).
  - Coverage thresholds: enforce minimal coverage for app modules; track trend.
  - Pre-commit: extend with `ruff`, `black`, `mypy --strict` on changed files; UI `eslint --max-warnings=0`.

## Performance

- Standardize `httpx.AsyncClient` creation with connection pooling and timeouts; provide a shared factory.
- Cache read-heavy endpoints (e.g., project overviews) with short TTL; add ETags/If-None-Match.
- Use task groups for concurrent IO where safe; bound concurrency to avoid rate limits.
- UI: enable React Query for all data fetches; memoize selectors; avoid unnecessary re-renders in dashboards.

## Documentation & DevEx

- Clear AGENTS.md and deployment docs; ensure any changes update `docs/AGENTS_CONTRACT.md`.
- Add “Integration Readiness” docs page surfacing `/api/projects/sync-status` and credential setup.
- Add “Local Troubleshooting” for common errors (CORS, env, proxies) and a quick self-test checklist.

## Immediate Fixes (P0)

1) Backend security hygiene
   - Replace allow-all CORS in unified server with allowed origins list from settings.
   - Enable rate limiter middleware in unified server with tuned endpoint limits.
2) Observability
   - Initialize telemetry in unified server; add spans for connector calls.
3) UI correctness
   - Remove hardcoded URLs; use `NEXT_PUBLIC_API_BASE` consistently.
   - Enable `tsconfig.json` `strict: true` (phased, start with core pages + key components).

## Near-Term Improvements (P1)

4) API hardening
   - Add response models for major endpoints and paginate where needed.
   - Add auth dependency to sensitive routes and consistent 401/403 handling.
5) Integration resilience
   - Centralize HTTP client factory with retries/backoff and circuit-breaking.
   - Add short TTL caching for overview/health endpoints.
6) UI DX & Validation
   - Introduce `zod` schemas and API client wrapper with AbortController-based timeouts.
   - Adopt React Query across all API calls; add error boundaries and loading skeletons.

## Medium-Term (P2)

7) Testing regimen
   - Add React Testing Library unit tests for dashboards; Playwright E2E for core flows.
   - Establish realistic coverage thresholds; track in CI.
8) Security & dependency health
   - Replace/guard `pickle.load`; add content integrity checks.
   - Add `bandit` and `pip-audit` to CI; track npm advisories.
9) SRE & performance
   - Define SLOs and alerts; add metrics dashboards.
   - Introduce ETags and caching headers where responses are stable.

## Code Change Sketches (Illustrative)

- Unified CORS and rate limiting in `app/api/unified_server.py`:

```python
from app.api.config.settings import settings
from app.api.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
```

- Initialize telemetry:

```python
from app.api.monitoring.opentelemetry_config import initialize_telemetry, SophiaAITelemetryConfig

initialize_telemetry(SophiaAITelemetryConfig())
```

- UI API client wrapper with timeout and zod validation:

```ts
// src/lib/apiClient.ts
export async function getJson<T>(url: string, schema: z.ZodSchema<T>, opts?: RequestInit & { timeoutMs?: number }) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), opts?.timeoutMs ?? 15000);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    return schema.parse(data);
  } finally {
    clearTimeout(id);
  }
}
```

## Appendix — Evidence Extracts

- Endpoints wired in unified server (includes projects, gong, brain ingest): `app/api/unified_server.py`
- Project management endpoints: `app/api/routers/projects.py`
- Gong endpoints: `app/api/routers/gong_intelligence.py`
- Brain ingest: `app/api/routers/brain_ingest.py`
- CORS wide-open usage: `app/api/unified_server.py` (allow `*`)
- Rate limiter exists but not enabled: `app/api/middleware/rate_limit.py`
- Telemetry present, not called: `app/api/monitoring/opentelemetry_config.py`
- UI strict disabled: `sophia-intel-app/tsconfig.json`
- Hardcoded URL: `sophia-intel-app/src/components/llm-control/ModelControlDashboard.tsx`
- TODO/FIXME/HACK markers: 300+ across repo

