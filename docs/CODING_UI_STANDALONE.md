One True Coding UI (Standalone)

Purpose
- The ONLY coding UI. Lives outside this repo. Builds the Sophia Intel BI app using MCP context and Portkey VKs.

Architecture
- Frontend: Next.js 15 (server-only env; no client secrets)
- Backend routes:
  - `POST /api/coding/plan` → calls Portkey and MCP for repo context
  - `POST /api/coding/patch` → generates unified diff; `apply=true` writes via MCP FS (8082)
  - `POST /api/coding/validate` → runs tests via MCP FS/Git
  - `GET /api/providers/vk` → reports present VKs
- Clients:
  - Portkey client: timeouts, retries, SSE; uses `PORTKEY_API_KEY` and VKs
  - MCP clients: Filesystem(8082), Memory(8081), Git(8084)

API Contracts
- POST /api/coding/plan
  - Request: `{ task: string, context?: { repoMap?: boolean, search?: string } }`
  - Response: `{ plan: { steps: string[] }, impacts: { filesTouched: string[] } }`
- POST /api/coding/patch
  - Request: `{ task: string, apply?: boolean, selections?: string[] }`
  - Response: `{ diff: string, applied: boolean, notes?: string[] }`
  - Rule: `apply=true` writes via MCP FS; `apply=false` returns diff only
- POST /api/coding/validate
  - Request: `{ scope?: string[], tests?: string[] }`
  - Response: `{ result: 'pass'|'fail', stats: { passed: number, failed: number }, logs?: string }`
- GET /api/providers/vk
  - Response: `{ present: string[], count: number }`

Environment
- Single source: path to this repo `.env.master` loaded server-side only
- Required: `PORTKEY_API_KEY`
- Recommended VKs: `PORTKEY_VK_OPENAI`, `PORTKEY_VK_ANTHROPIC`, `PORTKEY_VK_GROQ`, `PORTKEY_VK_XAI`, `PORTKEY_VK_OPENROUTER`, `PORTKEY_VK_TOGETHER`, `PORTKEY_VK_PERPLEXITY`, `PORTKEY_VK_GITHUB`, `PORTKEY_VK_STABILITY`, `PORTKEY_VK_GEMINI`
- Optional fallback: `OPENROUTER_API_KEY`

One True Flow
- Start Sophia MCP from the BI repo: `./sophia start` (8081, 8082, 8084)
- Start Coding UI (external project): read same `.env.master` via explicit path
- Use Plan → Implement → Validate; apply patches via MCP FS
- Commit changes in the BI repo

Performance Targets
- Cold start ≤ 3s (dev)
- Plan/patch ≤ 5s p50 for small changes
- MCP ops < 200ms p95 locally

Cloud Ready
- Containerize the UI; inject only server-side env (`PORTKEY_API_KEY` + VKs)
- Same routes, same behavior; zero client-side secrets
