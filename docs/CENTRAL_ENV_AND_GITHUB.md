Central Env and GitHub App

Single environment source
- `.env.master` at repo root is the only runtime env file.
- Load server-side only; never expose values to clients.
- Use `app.core.env.load_env_once()` or `builder_cli.lib.env.load_central_env()` to load idempotently.

Required keys (common)
- `PORTKEY_API_KEY` — Portkey virtual key; no direct provider SDKs.
- `MCP_TOKEN` (optional) — protects MCP servers; pair with `MCP_DEV_BYPASS` for local.
- `REDIS_URL` — e.g., `redis://localhost:6379/1`.
- `WEAVIATE_URL` — e.g., `http://localhost:8080`.

GitHub App pushes
- Use `scripts/gh_app_set_remote.sh` to set the remote with an installation token.
- Env vars:
  - `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_APP_INSTALLATION_ID`
  - Optional: `REMOTE` (default `origin`), `REPO` (e.g., `org/repo`)
- Token mint helper: `scripts/gh_app_token.py`.

Local validation
- `bash scripts/start_all_and_validate.sh` starts Redis/Weaviate, MCP servers, validates env/endpoints, seeds vector, and starts a queue worker.
- On any failure it exits non-zero; logs under `logs/`.

