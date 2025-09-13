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
- This repo never references these CLIs in code, scripts, or CI.
- Portkey Gateway and MCP are the only in-repo runtime integrations.

