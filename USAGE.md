# Sophia Intel AI — Usage Guide (One-True-Dev)

## Quick Start

- Start MCP: `./sophia start` (memory:8081, filesystem:8082, git:8084). Reads `./.env.master`. No prompts.
- Coding UI: external project only. Use it to Plan → Patch (via MCP FS) → Validate. Do not run any UI from this repo.

## MCP Servers

- Memory (8081): `curl -sf http://localhost:8081/health`
- Filesystem (8082): `curl -sf http://localhost:8082/health`
- Git (8084): `curl -sf http://localhost:8084/health`

## Environment

- Single source: `<repo>/.env.master` loaded by `./sophia`.
- Required: `PORTKEY_API_KEY`. Recommended VKs: `PORTKEY_VK_*`.

## Policies

- Portkey-only routing; no LiteLLM or local OpenRouter.
- No UI in this repo. Coding UI is external (local/cloud).
- No dotenv or `~/.config` in runtime code.

See also:
- `docs/ONE_TRUE_DEV_FLOW.md`
- `docs/CODING_UI_STANDALONE.md`
