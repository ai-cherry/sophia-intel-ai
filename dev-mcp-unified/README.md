# MCP Unified - Local AI Coding Assistant Server

Unified local MCP server that provides code indexing, context building, and tools for Claude, Qwen, OpenAI (Codex-like), and DeepSeek. Runs on your machine, keeps code local, and routes tasks intelligently.

## Ports & Endpoints

- Server: http://127.0.0.1:3333
- Health: GET /healthz
- Query: POST /query
- Background jobs: POST /background/run, GET /background/list, GET /background/logs
- Tools: POST /tools/search, POST /tools/symbols, POST /tools/tests, POST /tools/docs

## Quick Start

Prereqs: Python 3.11+, optional: `chromadb` for vector storage.

1) Configure keys via environment variables (local only; no secrets stored here):

export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export QWEN_API_KEY=...
export DEEPSEEK_API_KEY=...

2) Start the server:

./mcp start --index "$HOME/projects" --watch

Or directly:

python -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333

3) Test:

curl -s http://127.0.0.1:3333/healthz
curl -s -X POST http://127.0.0.1:3333/query -H 'Content-Type: application/json' -d '{"task":"explain_architecture","question":"Explain this repo"}'

## Rules & Context Strategies

See `config/rules.yaml`. You can customize per task → provider and context strategy. Example:

rules:
  - match: { task: explain_architecture }
    action: { provider: claude, context_strategy: full_file_with_dependencies }
  - match: { task: optimize_algorithm }
    action: { provider: qwen, context_strategy: ast_tree_with_symbols }
  - match: { task: generate_boilerplate }
    action: { provider: openai, context_strategy: snippet_with_completions }
  - match: { task: find_security_issues }
    action: { provider: deepseek, context_strategy: pattern_matching_context }

## Design

- Single server with pluggable adapters and tools
- Background worker queue for indexer/tests/static analysis
- Context engine builds LLM-specific bundles (AST-aware for code)
- No secrets committed; keys read from environment at runtime

## Optional: Vector Store

Install `chromadb` to enable persistent embeddings. Without it, an in-memory store is used.

pip install chromadb

## CLI

./mcp start --index <path> --watch
./mcp status
./mcp query --llm claude "explain this code"
./mcp test all

## Notes

- Security is kept simple for local use only.
- All code stays on your machine unless an API adapter is used.

