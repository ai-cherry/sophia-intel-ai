External Toolbox CLIs (Required)

Policy
- Provider CLIs are external-only. Do not add or invoke them from this repo.
- Install to your user PATH (e.g., ~/.local/bin) and use directly.

Defaults
- Grok (xAI): x-ai/grok-code-fast-1 for coding
- Codex (OpenAI): chatgpt-5 for coding
- Claude (Anthropic): opus-4.1 for deep analysis

Quick Usage (examples)
- grok: grok chat -m x-ai/grok-code-fast-1 -p "Write unit test skeletons"
- codex: codex chat --model chatgpt-5 -p "Refactor config loader"
- claude: claude -m opus-4.1 -p "Outline MCP smoke plan"

Notes
- Portkey Gateway and MCP are the only in-repo runtime integrations.
- A PR review workflow is provided and enabled (`.github/workflows/codex-review.yml`) that uses a GitHub Action; it includes an optional CLI fallback that only runs if a `codex` binary is on PATH. Remove or move the workflow to `workflow-templates` if you prefer to keep CI completely provider‑tool free.

See Also
- Codex CLI details and ARM64 setup: `Development → Codex CLI` (docs/development/codex-cli.md)
- A PR Review GitHub Action is provided as a template under `.github/workflow-templates/` for downstream opt‑in.
