Sophia Repository Conventions

Names and Roles
- Sophia Intel: Business intelligence app and dashboards
- Sophia Orchestrator: Agent/multi-tool orchestration and developer environment
- MCP Server: Tooling/context endpoint; always name by role (MCP Memory, MCP Filesystem, MCP Git)
- Gateway: Model routing layer (LiteLLM/Portkey)
- Router: Terminal AI router (bin/ai) and model control (bin/llm-models)
- Usecase: Named task profile mapping to an alias (e.g., coding.fast)
- Alias: Human-friendly label mapping to a concrete model (e.g., analytical → gemini-1.5-pro)

Ports and Services
- LiteLLM Proxy: 4000
- MCP Memory: 8081
- MCP Filesystem: 8082
- MCP Git: 8084

CLI and Scripts
- Canonical CLI: `./dev` (start/stop/status/health/check/test/ai/models/bi)
- Unified AI Router: `./dev ai …` (or bin/ai)
- Model Control: `./dev models …` (or bin/llm-models)
- Legacy scripts should note “legacy” and defer to ./dev

Environment
- Single source of truth: `<repo>/.env.master` (chmod 600)
- Manage with: `./bin/keys edit`; start with: `./sophia start`
- Dev auth scaffolding: `MCP_TOKEN` (optional), `MCP_DEV_BYPASS=true` (optional)

Code and Docs Style
- Python: lower_snake_case for files; FastAPI apps in mcp/<name>/server.py
- Shell: kebab-case or clear single-word names; keep under root or bin/
- Config: under config/ (e.g., config/models.json)
- Docs: use stable headings: Start Here, Local Development, Services and Ports, Models and Routing, MCP Servers, Security (Dev Scaffolding), Troubleshooting, Glossary

Glossary
- Agent: An LLM-powered component with a role/persona
- MCP Server: A service providing tools or context via HTTP/SSE/stdio
- Gateway: A system that routes model calls (e.g., LiteLLM/Portkey)
- Router: Local CLI wrapper that selects the model and dispatches (bin/ai)
- Usecase: A named task profile that resolves to an alias/model
- Alias: A label that maps to a concrete provider model

Guidance for AI Coding Agents
- Use `./dev` for orchestration; avoid introducing new top-level launchers
- Refer to MCP servers by role and port (MCP Memory 8081, etc.)
- Resolve models via `config/models.json` unless explicitly given a model
- Use consistent product names: “Sophia Intel”, “Sophia Orchestrator”
- When in doubt, prefer clarity over themed names for technical components
