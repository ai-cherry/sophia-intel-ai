# Environment Standardization Rollout Plan

**Target Canonical Template**: `.env.template`  
**Execution Window**: 2025-09-16 → 2025-09-23

## Objectives
- Provide automated visibility into legacy environment filename usage.
- Deliver a safe, reviewable migration path from `.env.master` / `.env.example` to `.env.template`.
- Unify loader logic around a single Convict + Zod validation pipeline.

## Tooling
- `scripts/env_inventory.py` – reports non-canonical references; supports CI gating via `--fail-noncanonical`.
- `scripts/migrate_env_references.py` – dry-run migration helper to rewrite legacy references to `.env.template`.

## Rollout Steps
1. **Inventory (Day 0)**
   - Run `python3 scripts/env_inventory.py --format table --fail-noncanonical` in CI dry-run to highlight blockers.
   - Owners triage high-risk references (deployment scripts, production automation).
2. **Migration Dry Run (Day 1-2)**
   - Execute `python3 scripts/migrate_env_references.py` without `--apply` in a dedicated worktree.
   - Capture diff and circulate for review across Platform, Integrations, and Security Ops.
3. **Loader Alignment (Day 2-3)**
   - Refactor `env_manager.py`/`environment_selector.py` to rely on `.env.template` + merged `config/*.yml` values.
   - Add Convict merge + Zod schema validation to Codex CLI init checks.
4. **Apply Migration (Day 3-4)**
   - Re-run migration script with `--apply` after approvals.
   - Remove `.env.master`/`.env.example` from repo, leaving archival copies under `backups/` if needed.
5. **Doc & CI Updates (Day 4-5)**
   - Update `ENVIRONMENT.md`, onboarding docs, deploy scripts.
   - Enforce `scripts/env_inventory.py --fail-noncanonical` in CI to prevent regressions.

## Validation
- `python3 scripts/env_inventory.py --fail-noncanonical` must pass with zero offenders.
- `pytest tests/test_environment.py` (to be updated) ensures loader behavior.
- Codex CLI `npm run test:codex-init` verifying convict/Zod integration.

## Rollback
- Restore `.env.master` and `.env.example` from git history if issues arise.
- Revert loader changes and disable CI gating command temporarily.
- Document rollback reason via `/notify` and update `docs/decisions/2025-09-16-env-standardization.md`.
