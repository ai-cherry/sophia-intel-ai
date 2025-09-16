Portkey-Only Policy

Routing
- Only Portkey Gateway with Virtual Keys (VKs). No alternate local gateways or proxies.

Keys
- Single source: `./.env.master`, loaded by `./sophia` and inherited by processes it spawns.
- Never prompt for keys. If missing, log once and fail fast.

Runtime Code Rules
- Do not import dotenv or read `~/.config` (no fallbacks anywhere under app/, backend/, services/, mcp/).
- All errors that reference missing keys must say: "Set it in ./.env.master and start via ./sophia".
- All LLM calls in this repo must go through Portkey (server-side). No provider SDKs.

Examples
- Good: use `PORTKEY_API_KEY` and VKs (e.g., `PORTKEY_VK_ANTHROPIC`) from the environment populated by `./sophia`.
- Good: server-side HTTP to Portkey base URL with VK routing headers.
- Bad: `from dotenv import load_dotenv` or reading `~/.config/...`.
- Bad: direct calls to `api.openai.com`, `api.anthropic.com`, `api.x.ai`.

CI Rules
- CI fails on references to: local proxy ports (`:8090`, `:4000`), `builder-agno-system`, in-repo `sophia-intel-app`, `/frontend\b`, `mcp/filesystem.py`, `mcp/git_server.py`, `api.x.ai`, `XAI_API_KEY`, and `grok` (except in EXTERNAL_TOOLS docs).
