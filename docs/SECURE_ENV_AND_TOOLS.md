Secure Env and API Tool Registry (Deprecated)

- Deprecated: Use repo-local `.env.master` as the single source, server-side only. See `docs/CENTRAL_ENV_AND_GITHUB.md`.

- Load order is now: `.env.master` only (server-side), then OS env overrides.

- Centralized loader: `app/core/env.py` and `builder_cli/lib/env.py`.

- Updated code now requires `PORTKEY_API_KEY` at runtime; no hardcoded defaults remain in core modules.

## Provider Keys (Developer Tools)

- Do not store provider keys (e.g., `CODEX_API_KEY`) in this repo or in `.env.master`.
- Local developer setup: add to your shell profile only, e.g. `~/.zshrc`:
  - `export CODEX_API_KEY="sk-xxxxx"`
  - Reload: `source ~/.zshrc`
- GitHub Actions (downstream opt‑in): add `CODEX_API_KEY` as a repository Secret and use the provided template under `.github/workflow-templates/codex-review.yml`.
- Reference: `docs/development/codex-cli.md` for installation, verification, and troubleshooting on Apple Silicon.
