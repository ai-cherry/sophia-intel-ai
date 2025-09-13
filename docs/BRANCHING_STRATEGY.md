# Branching, PR, and Release Strategy

## Branches
- `main` (protected): default branch; always deployable; all merges via PR with passing CI.
- `legacy-main`: snapshot of prior trunk for reference/rollback; no new commits; PRs targeting this branch are disallowed.
- Feature branches: `feat/*`, `fix/*`, `chore/*`, `docs/*` scoped to a single change set.
- PR branches created from features (e.g., `pr/3`, `pr/4`, `pr/7`) should rebase on `main` before merge.

## Rules
- No direct pushes to `main`; use PRs.
- Require CI green + at least 1 review for `main` merges.
- Disallow merge commits (squash or rebase preferred) to keep history linear.
- Disallow UI code in this repo; external UIs live in `../worktrees/*`. CI guards enforce this.
- MCP canonical ports: memory 8081, filesystem 8082, git 8084; contracts must be stable.

## Versioning & Tags
- Tag releases as `vX.Y.Z` on `main` after successful CI.
- Changelog updates accompany release tags.

## Backports & Hotfixes
- Hotfix branches off `main` → PR → `main`.
- Backports to `legacy-main` are discouraged; prefer forward-fix on `main`.

## Branch Protection (desired)
- Protect `main`: require status checks, reviews, disallow force-push.
- Lock `legacy-main`: administer-only pushes; no PR merges.

## External UIs
- `forge-ui` (3100), `portkey-ui` (3200), `sophia-bi-ui` (3300) live as separate repos/worktrees; never inside this repo.

