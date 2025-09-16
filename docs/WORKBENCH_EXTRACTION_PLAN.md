# Workbench Extraction Plan (History-Preserving)

Goal
- Move `workbench-ui/` out of this repo into its own repository (or an attached worktree) while preserving its Git history, aligning with AGENTS.md (no UI here), and keeping local DX smooth.

Approach Options
- A) Subtree split (recommended): preserves history for `workbench-ui/` only, clean independent repo.
- B) filter-repo (advanced): more control over history rewrite; requires `git-filter-repo` tool.
- C) Fresh repo + copy (fastest): no history; acceptable if you don’t need commit lineage.

Pre‑checks
- Ensure main branch is up to date and clean: `git status` shows no changes.
- Confirm Workbench path: `workbench-ui/` at the repo root (adjust commands if not).

A) Subtree Split (recommended)
1) Create split branch with only Workbench history
   - `git subtree split --prefix=workbench-ui -b workbench-ui-split`
   - This creates a branch `workbench-ui-split` with the filtered history.
2) Create the new repo (GitHub/GitLab or local)
   - Example: `gh repo create sophia-workbench-ui --private --description "Workbench UI"`
   - Or create an empty bare repo and note its remote URL.
3) Push split branch to new remote
   - `git checkout workbench-ui-split`
   - `git remote add workbench-origin <NEW_REMOTE_URL>`
   - `git push -u workbench-origin workbench-ui-split:main`
4) Clone or add a worktree for local dev (optional)
   - Worktree: `git worktree add ../worktrees/workbench-ui workbench-ui-split`
   - Or `git clone <NEW_REMOTE_URL> ../worktrees/workbench-ui`
5) Replace in‑repo folder with external reference (in this repo)
   - Remove directory in a PR: `git rm -r workbench-ui`
   - Add a README pointer and keep `scripts/scaffold_workbench_ui.sh` for devs to attach the worktree.
6) Update docs and links
   - Replace in‑repo references to `workbench-ui/` with links to the new repo.
   - Ensure `docs/EXTERNAL_UIS_README.md` and `docs/WORKBENCH_REPO_DECISION.md` reflect the move.
7) Team communication
   - Share the new repo URL and the worktree scaffold command with the team.

B) filter-repo (if you need more control)
1) Install: `pip install git-filter-repo`
2) Run from a fresh clone: `git filter-repo --path workbench-ui/ --force`
3) Push to new remote; result is a repo containing only the Workbench history.

C) New Repo (no history)
1) Create a new repo and copy files over.
2) Push initial commit; reference back to the original repo via a note in README.

New Workbench Repo Checklist
- Repo structure
  - `/` Next.js/Node app as before (or chosen framework)
  - `.env.master` based on backend schema, or consume via a small config package (e.g., `@sophia/config`) if you publish one.
- Config & env
  - Reuse `config/env.schema.json` if shared via package/submodule; otherwise copy and keep in sync.
  - Local dev: `.env.master` with placeholders; CI/CD injects real values from ESC.
- CI
  - Lint/test/build workflow
  - (Optional) `env-validate` job to validate `.env.master` against schema
  - (Optional) `no-real-secrets` job (same approach used here)
- Docs
  - README: quick start, env expectations, link back to this repo’s ENVIRONMENT.md
  - CONTRIBUTING.md: local dev + worktree instructions
- Release/versioning
  - Tag `v0.1.0` upon migration

Local Dev (Worktree) Flow
- From backend repo: `bash scripts/scaffold_workbench_ui.sh ../worktrees/workbench-ui`
- Work in `../worktrees/workbench-ui`; `.env.master` is synced on scaffold.
- Keep UI artifacts out of backend repo; IDE opens both workspaces.

Rollout Plan
- Step 1: Prepare new repo; push split branch to `main`.
- Step 2: PR in backend repo removing `workbench-ui/` and updating docs; link to new repo.
- Step 3: Merge PR.
- Step 4: Notify devs; announce the worktree scaffold command and new repo URL.

Rollback Plan
- If blockers arise, keep a tag of the pre-extraction commit.
- Revert the removal PR to restore `workbench-ui/` temporarily.
- The split repo remains; you can re-attempt later without losing history.

Notes
- Keep `.env.master` schemas consistent across repos. Prefer a small shared config package to avoid drift.
- If you need to preserve issues/PRs, move them at the platform level (GitHub issue transfer) after the split.
