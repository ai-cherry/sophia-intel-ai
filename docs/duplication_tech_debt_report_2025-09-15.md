# Duplication & Technical Debt Report — Sophia Intel AI

Generated: 2025-09-15

## Assumptions & Scope
- Scope: Static repo analysis for duplication patterns and technical debt across Python, MCP servers, infra, and scripts. No runtime validation performed.
- Goal: Identify highest‑leverage consolidation and hardening opportunities without changing behavior.

## Executive Summary
- Duplicate constructs detected across services and layers, notably: circuit breakers (10+ definitions), health checks (40+), multiple entrypoints (`main.py` in 9 locations), and overlapping orchestrator references.
- Security debt: Hardcoded secrets found in `test_gong_correct_api.py`, `config/user_models_config.yaml`, and `lambda_labs_scanner.py`.
- Maintainability risks: 4k+ `print()` usages bypass structured logging; scattered requirements files increase drift; many JSON artifacts in repo root add noise.
- Orchestrator facade reference exists in DI but file is missing (`app/orchestration/unified_facade.py`), indicating broken imports or moved code.

## Key Findings

1) Orchestrator/Facade Inconsistencies
- `UnifiedOrchestratorFacade` imported in `app/infrastructure/dependency_injection.py`, but `app/orchestration/unified_facade.py` not present; multiple docs refer to it. Likely moved/renamed; imports need correction or file restored.
- Numerous orchestrator mentions in ARCHITECTURE.md; prior duplication cleanup partially complete.

2) Class and Function Duplication (samples)
- CircuitBreaker: 10 definitions
  - app/mcp/connection_manager.py
  - app/core/memory_router.py
  - packages/sophia_core/utils/cbreaker.py
  - app/api/services/circuit_breaker.py
  - agents/specialized/prophecy_agent.py
  - app/core/resilience/circuit_breaker.py
  - app/core/circuit_breaker.py
  - app/api/core/conflict_resolution_engine.py
  - app/api/database/connection_pool.py
  - app/core/async_http_client.py
- HealthStatus: 8 definitions (Enum/Pydantic variants)
  - app/core/health_monitor.py, app/mcp/contracts/base_contract.py, app/api/contracts.py, etc.
- Top‑level `main` function names: 113 occurrences
- 9 distinct `main.py` entrypoints across services (services/*, app/*, backend/*, infrastructure/*)

3) Endpoint and Health‑Check Sprawl
- 40+ `@app.get("/health")` or `def health_check()` definitions across services and scripts; inconsistent response contracts.

4) Security and Secrets
- Hardcoded secrets found:
  - test_gong_correct_api.py: Bearer token string literal
  - config/user_models_config.yaml: api_key value present
  - lambda_labs_scanner.py: default API key literal
- `.env` examples and infra compose files contain default fallbacks like `MCP_SECRET_KEY: ${MCP_SECRET_KEY:-secret}` — acceptable for dev, but risky if propagated.

5) Logging & Observability Debt
- 4,244 `print(` usages in Python. AI logger exists (`app/core/ai_logger.py`) but is not consistently adopted.

6) Dependency Fragmentation
- Multiple requirements files: root `requirements.txt`, `requirements_arm64.txt`, plus `pulumi/*/requirements.txt`, `mcp/requirements.txt`, etc. Drift risk without a central constraints file.

7) Artifacts in Repo Root
- Numerous JSON/text report artifacts (audit, validation, test outputs) at root increase noise and risk merge conflicts.

8) Tests and Skips
- Many integration tests are `pytest.skip` gated on env; acceptable, but hides regressions unless CI matrix covers them.

## Recommendations (Prioritized)

1) Fix Orchestrator Facade Import (High)
- Decide canonical location for `UnifiedOrchestratorFacade` (e.g., `app/orchestration/unified_facade.py` or `app/ui/unified/`), then:
  - Implement or move the class to the canonical path.
  - Update `app/infrastructure/dependency_injection.py` import accordingly.
  - Add unit test that imports DI and resolves the facade.

2) Consolidate Core Contracts (High)
- CircuitBreaker: keep `app/core/resilience/circuit_breaker.py` as canonical; replace others with thin adapters or remove if equivalent.
- HealthStatus: define a single canonical Enum (e.g., `app/core/contracts/health.py`) and have FastAPI response models reference it.
- Provide a deprecation shim module for 1 release cycle to avoid breakage.

3) Health Endpoint Unification (High)
- Create a shared health mixin/util that standardizes shape: `{ status: "ok", version, deps: {...} }`.
- Replace scattered health handlers with wrapper/decorator to ensure uniform contract and metrics.

4) Secrets Hygiene (High)
- Immediately remove/rotate any hardcoded tokens in:
  - test_gong_correct_api.py
  - config/user_models_config.yaml
  - lambda_labs_scanner.py
- Add pre‑commit GitLeaks and CI secrets scanning; block on findings.

5) Logging Policy (Medium)
- Enforce `print` ban via Ruff rule (`T201`) and codemod prints → `app/core/ai_logger.py`.
- Add a compatibility `print` shim that calls logger in legacy scripts as a stopgap.

6) Dependencies Governance (Medium)
- Introduce a top‑level `constraints.txt` and require all service `requirements.txt` to pin via `-c constraints.txt`.
- Group per‑service `requirements-<service>.txt` under `requirements/` with clear ownership; remove duplicates.

7) Repo Hygiene for Artifacts (Medium)
- Move JSON/TXT analysis outputs to `artifacts/` (git‑ignored) or publish to CI artifacts store.
- Add a cleanup script and CI step that ensures repo root remains clean.

8) Entry Point Rationalization (Medium)
- Define a single canonical API entrypoint (e.g., `app/api/main.py`).
- Keep service‑specific `main.py` only where they represent separate deployables; otherwise route via a unified launcher.

9) CI/Pre‑commit Hardening (Medium)
- Enable `scripts/check_duplicates.py` in pre‑commit and CI.
- Add Ruff + Black + MyPy gates; fail on new prints, untyped defs in core, and duplicate detections.

10) Test Matrix (Low)
- Create a CI matrix with optional secrets to exercise integration tests; report skipped counts and fail if critical tests are perma‑skipped.

## Proposed Architecture Changes (Minimal Surface Area)
- Core contracts module: `app/core/contracts/`
  - `health.py`: `HealthStatus` enum; typed schemas for `/health` responses.
  - `resilience/circuit_breaker.py`: single canonical CircuitBreaker with policy injection.
- Shared service utilities: `app/core/service/health.py` for decorator/mixin unifying health endpoints.
- Deprecation policy: leave compatibility aliases in prior locations for one release.

## Interface Contracts
- Health endpoint: `GET /health -> { status: Literal["ok","degraded","down"], version: str, deps: dict[str, Literal["ok","down"]] }`
- Circuit breaker interface: `allow() -> bool`, `on_success()`, `on_failure(error: Exception)`; policy via dataclass config.

## Implementation Plan
- Week 1: Fix orchestrator facade path, add CI job for duplicate/secrets scan, add Ruff rule T201.
- Week 2: Consolidate CircuitBreaker and HealthStatus; ship deprecation shims; codemod top 500 prints in app/.
- Week 3: Introduce constraints.txt; relocate artifacts to artifacts/ with .gitignore; unify health endpoints via decorator.
- Week 4: Cleanup remaining duplicate classes; retire shims; finalize docs.

## Tests
- Unit: Import DI and resolve `UnifiedOrchestratorFacade`; ensure health decorator returns canonical shape.
- Integration: Hit `/health` across services and assert identical schema.
- Static: Run `scripts/check_duplicates.py` and `gitleaks` in CI; assert zero errors.

## Validation (Commands)
- Duplicates quick scan:
  - `rg -n "^class (CircuitBreaker|HealthStatus)\b" --type py`
  - `rg -n "@app\.get\(\s*['\"]/health" --type py`
  - `python scripts/check_duplicates.py` (ensure env has `pyyaml`)
- Prints:
  - `rg -n "^[ \t]*print\(" --type py | wc -l`
- Secrets:
  - `gitleaks detect --no-git -s .` (add to CI)

## Documentation
- Update ARCHITECTURE.md to reference single orchestrator facade and core contracts.
- Add coding standard: no `print`, health schema contract, constraints usage.

## Rollback Plan
- Tag before consolidation. Keep deprecation shims and feature flags to switch imports back if regressions appear.
- Maintain a `rollback.sh` that restores previous class locations and disables new CI gates temporarily.

---

Appendix: Key raw signals (captured via ripgrep)
- Prints: 4,244
- `main.py` files: 9
- `main` function names: 113
- Health endpoints: 40+ definitions
- CircuitBreaker classes: 10 definitions
- HealthStatus classes: 8 definitions
- Hardcoded secrets: found in 3 files (see Security section)

