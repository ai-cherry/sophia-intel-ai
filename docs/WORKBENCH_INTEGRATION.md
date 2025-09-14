# Workbench UI Integration (Fast Path)

The Workbench UI now lives in a separate repository. Use a git worktree for co-development.

- New repository: <NEW_REPO_URL>
- Local worktree (recommended): `../worktrees/workbench-ui`
- Shared env: Load the backend repo’s `.env.master` via `REPO_ENV_MASTER_PATH`

Quick Start (Local)
- Attach worktree (from backend repo):
  - `bash scripts/extract_workbench_repo.sh`
  - `bash scripts/finish_workbench_extraction.sh <owner/repo> private` (uses GitHub CLI)
- Or clone separately:
  - `git clone <NEW_REPO_URL> ../worktrees/workbench-ui`

Run (Workbench repo)
```bash
cd ../worktrees/workbench-ui
npm i
REPO_ENV_MASTER_PATH=$(pwd -P | sed 's|/worktrees/workbench-ui||')/.env.master \
  npm run dev
```

MCP Connectivity
- Default HTTP mode (centralized):
  - `MCP_MEMORY_URL=http://localhost:8081`
  - `MCP_FILESYSTEM_URL=http://localhost:8082`
  - `MCP_GIT_URL=http://localhost:8084`
  - `MCP_VECTOR_URL=http://localhost:8085`
  - Optional: `MCP_TOKEN` (Bearer) when not in dev
- Optional stdio: use `examples/mcp/mcp.local.json` and import in IDE/CLI

Providers
- Flexible routing via env:
  - `AI_ROUTER=portkey|openrouter|direct`
  - `AI_PROVIDER=openai|anthropic|gemini|mistral|groq|xai|cohere|ai21`
- Portkey VK for OpenAI:
  - `PORTKEY_API_KEY=pk-...`
  - `PORTKEY_VK_OPENAI=@openai-vk-xxxxxx` (note the `@`)

Post-Extraction Code Adjustments
- Paths in `src/server.ts` for config files should be repo-root relative:
  - From: `path.join(process.cwd(), 'workbench-ui', 'config', '...')`
  - To:   `path.join(process.cwd(), 'config', '...')`

