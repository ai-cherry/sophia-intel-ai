# Top Local MCP Server Setups (Sept 2025)

Purpose
- Curated, high‑performance local MCP servers for coding workflows.
- Focus on stdio transport (lowest latency; easy IDE/CLI sharing), zero cloud dependency, and team‑shareable configs.

Why stdio
- Zero network hops; works across VS Code, Cursor, JetBrains, Claude Desktop, CLI tools.
- Share a single `mcp.json` checked into your personal dotfiles (not this repo).

Recommended Servers
- GitHub MCP Server (Repo automation)
  - Why: Go‑based; sub‑100ms; token caching; monorepo semantic search.
  - Run: `docker run -i --rm -e GITHUB_TOKEN=$GITHUB_TOKEN ghcr.io/github/github-mcp-server stdio`
  - Config key: `github`
- Filesystem MCP Server (Local file ops)
  - Why: Rust/TS hybrid; sandboxing; blazing file ops; no external deps.
  - Run: `node dist/index.js --root /your/project stdio`
  - Config key: `fs`
- Docker MCP Server (Build/run/test automation)
  - Why: Native Docker socket; parallel builds; great for devops tasks.
  - Run: `docker run -i --rm -v /var/run/docker.sock:/var/run/docker.sock modelcontextprotocol/server-docker stdio`
  - Config key: `docker`
- Python Code Interpreter MCP (Sandboxed code exec)
  - Why: Pyodide/Deno isolation; WASM accel; fast REPL.
  - Run: `python server.py --sandbox stdio`
  - Config key: `python`
- Memory MCP Server (Persistent context)
  - Why: SQLite‑backed; fast queries; accumulates context across sessions.
  - Run: `npx -y @modelcontextprotocol/server-memory stdio --db local.db`
  - Config key: `memory`

Usage
- Example config at `examples/mcp/mcp.local.json` (do not commit real tokens to this repo).
- Import into IDE:
  - Cursor: Settings → MCP → Import JSON
  - VS Code: MCP Extension → Add config
  - JetBrains: MCP plugin → Add
  - CLI: `mcp-use-cli <server> --config mcp.local.json`

Notes
- Prefer stdio for perf; scope access (e.g., `--root`) to reduce risk.
- Keep `mcp.local.json` out of this repo; store under user config with proper ignore rules.

