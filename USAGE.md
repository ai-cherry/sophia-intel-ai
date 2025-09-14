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

## CLI Guard Flags

- `--max-input <int>`: hard cap on estimated input tokens; fails fast when exceeded.
- `--max-output <int>`: cap on requested output tokens for the call.
- `--max-cost <float>`: cap on estimated USD cost (rough heuristic per model); blocks over-budget calls.
- `--thinking`: required to use models tagged as thinking (e.g., `magistral-medium-2506-thinking`).

Examples:

- `./bin/sophia plan --alias magistral-small --task "Add /ready endpoint" --max-input 4000 --max-output 800`
- `./bin/sophia code --alias grok-fast --task "Add ready" --paths app/api --out artifacts/cli/patch.json --max-cost 0.5`
- `./bin/sophia apply artifacts/cli/patch.json --task "Add ready" --no-validate`

See also:
- `docs/ONE_TRUE_DEV_FLOW.md`
- `docs/CODING_UI_STANDALONE.md`
