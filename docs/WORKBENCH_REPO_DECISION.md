# Workbench Repository Decision

Decision: Make Workbench a separate repository (or attached via git worktree) to keep this repo focused on backends/integrations and MCP. This aligns with AGENTS.md and reduces artifact drift (.next, node_modules).

Benefits
- Cleaner backend CI and Docker contexts
- Clear ownership and release cadence for UI
- Avoids committing large build artifacts and dependency trees in this repo

Developer Workflow
- Use `scripts/scaffold_workbench_ui.sh` to attach the external worktree at `../worktrees/workbench-ui`.
- Copy `.env.master` schema into the worktree automatically.
- The Workbench repo should depend on the same env schema (`config/env.schema.json`) for consistency.

Migration Outline
1) Create the new Workbench repo.
2) Move `workbench-ui/` code there; retain history if desired via git subtree or filter-repo.
3) Add a small README here pointing devs to the external repo and the scaffold script.
4) Optional: add a CI guard to block re-introduction of UI directories here.

Rollback Plan
- If issues arise, keep a stable tag of the in-repo Workbench and reattach temporarily.

