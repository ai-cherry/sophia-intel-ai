# Contributing to Sophia Intel AI

We aim for zero tech debt and a clean, predictable developer experience.
This guide explains how to propose changes, coding standards, tests, and docs.

## Workflow
- Fork or branch from `main`.
- Create a focused branch: `feat/<area>-<short>` or `fix/<area>-<short>`.
- Plan → Implement → Validate → Document (in that order).
- Open a PR with a clear description and checklist (below).

## Pull Request Checklist
- Code builds locally; unit tests pass (`pytest -q`).
- Coverage ≥ 80% for touched files (add tests where needed).
- No secrets added (search for `API_KEY|TOKEN|SECRET`).
- Lint/format applied (Black for Python; Prettier/ESLint for TS where configured).
- Docs updated (README/START_HERE/ARCHITECTURE/DEPLOYMENT as appropriate).
- No duplicate docs or scripts created; consolidate or link.

## Coding Standards
- Python 3.11+ with type hints; follow PEP 8/484.
- Use async patterns for I/O-bound code; prefer FastAPI for services.
- Handle errors explicitly; avoid silent failures.
- Keep functions small and pure; avoid side effects where possible.
- No one-letter variable names (except idiomatic i/j for loops).

## Tests
- Unit tests near the code or under `tests/` following existing patterns.
- Add integration tests if you modify endpoints or adapters.
- Prefer deterministic tests; isolate network calls behind fakes/mocks.

## Documentation
- START_HERE.md: onboarding and daily flow (single source for start commands).
- README.md: high-level overview and quickstart.
- ARCHITECTURE.md + ADRs: design and decisions.
- DEPLOYMENT.md: deployment procedures; platform-specific docs under `docs/deployment/`.
- POLICIES.md + `POLICIES/*.yml`: authority/routing/access.
- Avoid duplicates; if a doc overlaps another, consolidate and link.

## Environment Policy (Enforced)
- Single source: `<repo>/.env.master` (git-ignored, chmod 600).
- Manage with `./bin/keys edit`; start with `./sophia start`.
- No prompts in scripts; missing env prints one clear line with the fix.

## Commit Message Conventions
- `feat:` new feature; `fix:` bug; `docs:` docs; `refactor:` internal change; `test:` tests.
- Keep subject ≤ 72 chars; include a short rationale.

## Security
- No hardcoded secrets; prefer env variables from `.env.master`.
- Validate inputs (API and CLIs); set secure headers; log security events where relevant.

## PR Review
- Small, focused changes are easier to review and merge.
- Address feedback promptly; keep discussion in the PR thread.

Thank you for contributing! Keeping this repo cohesive and debt‑free is a team effort.

