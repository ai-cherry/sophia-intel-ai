Sophia Intel AI — Start Here (Single-Dev Onramp)

Goal
- Fastest path to a productive, contextual AI coding + BI environment.

1) Environment (One Source Only)
- Single source of truth: `<repo>/.env.master` (git-ignored)
- Create/manage quickly:
  - `./bin/keys edit`  # creates if missing, sets chmod 600
  - Other options: `./bin/keys show`, `./bin/keys path`
- Example keys (edit `.env.master`):
  - `ANTHROPIC_API_KEY=...`, `OPENAI_API_KEY=...`, `OPENROUTER_API_KEY=...`
  - Optional: `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, etc.
- Important: No fallbacks (no `~/.config`); no prompts. If missing, you’ll see one line with the fix.

2) Bring services up
- From repo root:
  - `./sophia start`    # Uses Portkey gateway; starts MCP servers (8081/8082/8084)
  - `./sophia status`   # Quick status + recent logs
  - `./sophia test`     # Validation without changing env policy
  - `./sophia stop`     # Stop all

3) Terminal agents (developer convenience)
- Unified CLI examples:
  - `./dev ai claude -p "Summarize pipeline trends"`
  - `./dev ai codex  "Write SQL to aggregate MRR by month"`
  - `./dev ai lite   --usecase analysis.large_context -p "Analyze anomalies"`
- OpenCode even if PATH is broken: `./dev opencode --version`

4) Cursor IDE MCP context
- `.cursor/mcp.json` configured for local MCP:
  - memory:  http://127.0.0.1:8081
  - fs:      http://127.0.0.1:8082
  - git:     http://127.0.0.1:8084
- Start services first (`./sophia start`).

5) Security & auth
- Dev: `MCP_DEV_BYPASS=true` (default). For production, set:
  - `MCP_DEV_BYPASS=false`
  - `MCP_TOKEN=your-secure-token`
- Keys are never prompted; they flow from `.env.master` to all services started via `./sophia`.

6) Daily flow
- Start of day: `./sophia start`
- If a key changes: `./bin/keys edit` then `./sophia restart`
- That’s it. No more “where are the keys?”

7) References
- Conventions: CONVENTIONS.md
- Models: MODELS.md
- Policies: POLICIES.md
