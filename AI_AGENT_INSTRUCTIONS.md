# 🚨 CRITICAL INSTRUCTIONS FOR AI AGENTS WORKING ON SOPHIA INTEL

One True Setup
- This repo = BI app (API + integrations) and MCP only. No coding UI lives here.
- Portkey-only LLM routing (with VKs). No alternate local proxies.
- Exactly one MCP suite: memory(8081), filesystem(8082), git(8084).
- Single env source: `<repo>/.env.master` loaded by `./sophia`.

Adding Features
- Check `app/integrations/` before creating anything.
- Coding experience (planning, patching) is done in the external Coding UI project. See `docs/CODING_UI_STANDALONE.md`.
- Use MCP for context and file ops.

Ports
- 8081: Memory MCP
- 8082: Filesystem MCP
- 8084: Git MCP

Startup
```bash
./sophia start   # starts MCP (8081/8082/8084)
```

Environment
- Put keys in `<repo>/.env.master`. Start via `./sophia`. Never prompt.

Forbidden
- Creating or starting any UI in this repo
- Using alternate local proxies
- Adding alternate env loaders (dotenv, ~/.config)
