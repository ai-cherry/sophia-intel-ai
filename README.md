# slim-agno

Local-first AI swarm framework using Agno with Portkey → OpenRouter for LLM routing, Together AI for embeddings, and Weaviate for vector storage.

## Purpose

A lightweight, local-first implementation of AI agent swarms that:
- Runs entirely locally without cloud dependencies
- Routes all LLM traffic through Portkey → OpenRouter for unified access
- Uses Together AI for fast, cost-effective embeddings
- Leverages Weaviate as the single vector database
- Implements everything as swarms (teams with generator/critic/judge/lead/runner patterns)

## Rules

- **Local-first**: No cloud required to run the system
- **Portkey-only endpoint**: All LLM calls go through Portkey's OpenAI-compatible endpoint
- **Separate embeddings**: Together AI handles embeddings independently from chat models
- **Single vector DB**: Weaviate is the only vector database (local Docker)
- **Environment isolation**: One `.env` per machine; `.env.example` in repo; `.env` is git-ignored
- **Swarm architecture**: Everything is organized as teams with specialized agents

## Quickstart

### 1. Setup environment

```bash
cp .env.example .env
# Edit .env with your keys:
# - OPENAI_BASE_URL: Your Portkey OpenAI-compatible endpoint
# - OPENAI_API_KEY: Your Portkey Virtual Key (pk-live-...)
# - TOGETHER_API_KEY: Your Together AI API key
```

### 2. Start Weaviate

```bash
docker compose -f docker-compose.weaviate.yml up -d
```

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the playground

```bash
python -m app.playground
```

Visit http://localhost:7777 to access the Agno Playground.

### 5. (Optional) Agent UI

```bash
npx create-agent-ui@latest agent-ui
cd agent-ui
pnpm install
pnpm dev
```

Point the Agent UI to `http://localhost:7777`

## Architecture

```
slim-agno/
├── app/
│   ├── settings.py           # Environment configuration
│   ├── playground.py         # Agno Playground entry point
│   ├── models/
│   │   └── router.py        # LLM routing through Portkey
│   ├── memory/
│   │   ├── embed_together.py   # Together AI embeddings
│   │   ├── index_weaviate.py   # Weaviate vector operations
│   │   └── chunking.py        # Document/code chunking
│   ├── tools/
│   │   ├── code_search.py    # Vector search for code
│   │   ├── repo_fs.py        # File system operations
│   │   ├── git_ops.py        # Git operations
│   │   ├── test_ops.py       # Testing tools
│   │   ├── lint_ops.py       # Linting and formatting
│   │   └── ui_ops.py         # UI-related tools
│   └── swarms/
│       └── coding/
│           ├── team.py       # Coding team configuration
│           └── agents.py     # Individual agent definitions
```

## Swarms

### Coding Team

The Coding Team consists of:
- **Lead**: Coordinates work and makes architectural decisions
- **Coder-A**: Senior developer focused on implementation
- **Coder-B**: Developer focused on optimization and refactoring
- **Critic**: Code reviewer ensuring quality
- **Judge**: Final decision maker on code quality

## Configuration

All configuration is managed through environment variables:

- `OPENAI_BASE_URL`: Portkey's OpenAI-compatible endpoint
- `OPENAI_API_KEY`: Portkey Virtual Key
- `TOGETHER_API_KEY`: Together AI API key for embeddings
- `WEAVIATE_URL`: Weaviate instance URL (default: http://localhost:8080)
- `PLAYGROUND_PORT`: Port for Agno Playground (default: 7777)

## Development

### Adding new swarms

1. Create a new directory under `app/swarms/`
2. Define agents in `agents.py`
3. Create team composition in `team.py`
4. Register in `app/playground.py`

### Adding new tools

1. Create tool class extending `agno.Tool` in `app/tools/`
2. Import and add to relevant agents in swarm definitions

## License

MIT