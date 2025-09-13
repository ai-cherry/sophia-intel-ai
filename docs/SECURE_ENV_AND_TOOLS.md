Secure Env and API Tool Registry (Deprecated)

- Deprecated: Use repo-local `.env.master` as the single source, server-side only. See `docs/CENTRAL_ENV_AND_GITHUB.md`.

- Load order is now: `.env.master` only (server-side), then OS env overrides.

- Centralized loader: `app/core/env.py` and `builder_cli/lib/env.py`.

- Updated code now requires `PORTKEY_API_KEY` at runtime; no hardcoded defaults remain in core modules.
