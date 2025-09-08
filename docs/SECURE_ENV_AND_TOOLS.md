Secure Env and API Tool Registry

- Store secrets outside the repo in `~/.config/artemis/env` using KEY=VALUE lines. Example:
  - PORTKEY_API_KEY=pk_live_...
  - ELEVENLABS_API_KEY=...
  - OPENAI_API_KEY=...

- Load order:
  1) OS env vars
  2) `~/.config/artemis/env`

- New modules:
  - `app/core/security/secure_env.py`: `SecureEnvironmentManager` to retrieve required keys.
  - `app/core/api_tool_registry.py`: `APIToolRegistry` centralizes external tools (env names, capabilities).

- Updated code now requires `PORTKEY_API_KEY` at runtime; no hardcoded defaults remain in core modules.

