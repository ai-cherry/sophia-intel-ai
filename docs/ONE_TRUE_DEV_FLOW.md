One True Dev Flow (Final)

Purpose
- The only developer workflow for the Sophia Intel BI repo.
- Coding UI is a separate local/cloud project — never inside this repo.

Flow
- Start MCP: `./sophia start` → memory:8081, filesystem:8082, git:8084. Reads `./.env.master`. No prompts.
- Coding UI (external):
  - Reads the same `./.env.master` server‑side only.
  - Uses Portkey + VKs (no LiteLLM/local proxies).
  - Plan → Patch (via MCP FS) → Validate tests.
- Commit results in this BI repo.

Environment
- Single source: `<repo>/.env.master` loaded by `./sophia`.
- Required: `PORTKEY_API_KEY`.
- Recommended VKs: `PORTKEY_VK_OPENAI`, `PORTKEY_VK_ANTHROPIC`, `PORTKEY_VK_GROQ`, `PORTKEY_VK_XAI`, `PORTKEY_VK_OPENROUTER`, `PORTKEY_VK_TOGETHER`, `PORTKEY_VK_PERPLEXITY`, `PORTKEY_VK_GITHUB`, `PORTKEY_VK_STABILITY`, `PORTKEY_VK_GEMINI`.
- Optional fallback: `OPENROUTER_API_KEY`.

Forbidden
- No coding UI here. No TUI here. No LiteLLM. No local OpenRouter. No dotenv/`~/.config`.
