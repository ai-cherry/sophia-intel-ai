# Environment Standard

This repository uses a single canonical `.env.master` for local development, validated against `config/env.schema.json`. Real secrets and environment-specific values are sourced from Pulumi ESC (dev/staging/prod) in CI/CD.

Principles
- Single source of truth for variable names and types.
- No real secrets in Git; `.env.master` contains safe placeholders.
- Local precedence: process env overrides `.env.master`.
- CI/CD: process env only, populated from ESC.

Files
- `config/env.schema.json` – JSON Schema for keys and types
- `config/ENV_KEYS.md` – human-readable summary
- `.env.master` – safe placeholders for local dev
- `esc/esc_mapping.yaml` – mapping from keys to ESC secret paths

Loaders
- Python: `config/python_settings.py` (`settings_from_env()`) reads `.env.master` in `APP_ENV=dev`, overlays with process env.
- TypeScript: `config/tsSchema.ts` (`loadConfig()`) does the same.

Developer Workflow
1) Edit `.env.master` placeholders if needed (don’t insert real keys).
2) Optionally run: `python config/python_settings.py` or `ts-node config/tsSchema.ts` to sanity check.
3) Services consume env via the language loaders, not ad-hoc `os.getenv`/`process.env` scattered across code.

CI Validation
- Schema validation job ensures `.env.master` is consistent.
- “No real secrets” job rejects probable credential patterns.

