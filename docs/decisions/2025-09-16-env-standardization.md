# Decision Log: Environment Configuration Standardization

**Date**: 2025-09-16  
**Author**: Codex agent (environment consolidation lead)

## Context

Recent duplication analysis highlighted three competing environment configuration patterns in the repository (`.env.template`, `.env.template`, `.env.master`). Tooling and documentation disagree on which file is canonical, and several loader scripts apply conflicting assumptions about encryption and source of truth. This misalignment has created deployment instability and onboarding friction.

## Decision

1. Adopt `.env.template` as the canonical template that all onboarding, automation, and documentation reference.
2. Maintain an encrypted runtime copy managed by the existing secret tooling (`env_manager.py`) while keeping the plaintext template under version control.
3. Deprecate `.env.template`, `.env.master`, and ad-hoc environment bootstrap logic once migration tooling is ready.
4. Require that all shell scripts and Python utilities hydrate their configuration through a unified loader module that resolves `.env.template` + `config/*.yml` using Convict/Zod validation rules.

## Rationale

- `.env.template` already reflects the most complete coverage of configuration keys and is easier to diff review.
- Aligns with Codex CLI guardrails that expect a template + validated runtime merge.
- Reduces duplication between security automation and developer tooling by centralizing the load path.
- Simplifies CI/CD by enforcing a single entrypoint for environment variables.

## Status

- ✅ Alignment with platform and integrations teams requested via `/notify` (ref: `notify/env-standardization-2025-09-16`)
- ⏳ Migration tooling and documentation updates in progress

## Follow-Up Actions

- Implement repository-wide inventory tooling to surface non-conforming references.
- Provide automated migration script to switch scripts/docs to `.env.template`.
- Update `ENVIRONMENT.md`, onboarding docs, and CI pipelines when tooling lands.
- Archive deprecated env files and loaders with clear rollback instructions.

## Rollback Plan

If blockers surface during implementation, revert references to `.env.master` by restoring the previous onboarding docs and reinstituting legacy loader scripts from git history (commit prior to standardization). Document the issue in `/notify` and reschedule the migration after gaps are closed.
