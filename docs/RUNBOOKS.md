# Runbooks

Env Validation (Local)
- `python scripts/validate_env_schema.py` – validates `.env.master` against `config/env.schema.json`.
- `python config/python_settings.py` – prints resolved settings summary.
- `node config/tsSchema.ts` (or `ts-node`) – prints resolved settings summary.

CI Checks
- `env-validate` workflow ensures schema compliance.
- `no-real-secrets` workflow prevents committing obvious secrets.

Pulumi ESC
- See `docs/PULUMI_ESC_GUIDE.md` for environment setup and rotation.

Workbench Worktree
- `scripts/scaffold_workbench_ui.sh` – attach external repo as worktree under `../worktrees/workbench-ui`.

