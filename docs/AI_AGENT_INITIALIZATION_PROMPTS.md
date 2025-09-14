# AI Agent Initialization Prompts
## For Dual-Repository Development Environment

---

## 1. Workspace-UI Context Prompt (For Cursor/Cline in workspace-ui repository)

```markdown
You are working in the workspace-ui repository, a TypeScript/Next.js frontend application with Agno AI v2 framework integration. This is the UI and agent orchestration layer of the Sophia Intel AI system.

## Repository Context
- **Location**: ~/worktrees/workbench-ui or ~/workbench-ui
- **Purpose**: Frontend UI with AI agent orchestration
- **Stack**: TypeScript, Next.js, Fastify, React
- **Port**: 3201 (main server)

## Key Components
1. **Agno AI Framework** (v2.0)
   - Location: ./agno/
   - Agents: Architect, Coder, Reviewer, Tester
   - Config: ./agno/config.yaml

2. **Portkey Integration**
   - Provider: ./agno/providers/portkey.ts
   - Virtual Keys: Use @-prefixed keys in SDK
   - Models: claude-opus-4.1, grok-5, deepseek-v3

3. **MCP Client Connections**
   - Memory Server: http://localhost:8081
   - Filesystem Server: http://localhost:8082
   - Git Server: http://localhost:8084
   - Vector Server: http://localhost:8085
   - Client Pool: ./agno/providers/mcp-client.ts

## Key Rules
- ✅ Agno framework is ONLY in this repository
- ✅ Connect to MCP servers via HTTP clients
- ✅ Use TypeScript with strict mode
- ✅ Follow React best practices
- ✅ Use Zod for runtime validation
- ❌ NO backend MCP server code here
- ❌ NO Python code in this repository
- ❌ NO direct database connections

## Available Commands
- `npm run dev` - Start development server
- `npm run agno:init` - Initialize Agno framework
- `npm run agno:agents` - List available agents
- `npm run agno:chain` - Run agent chains
- `npm run agno:test` - Run Agno tests

## Environment Variables
- PORTKEY_API_KEY - Main Portkey API key
- ANTHROPIC_VK_B - Virtual key for Anthropic (@anthropic-vk-b)
- OPENAI_VK_C - Virtual key for OpenAI (@openai-vk-c)
- GROK_VK_E - Virtual key for Grok (@grok-vk-e)
- REPO_ENV_MASTER_PATH - Path to sophia-intel-ai/.env.master

## File Patterns
- Components: src/components/*.tsx
- Agents: agno/agents/*.ts
- Providers: agno/providers/*.ts
- API Routes: src/api/*.ts
```

---

## 2. Sophia-Intel-AI Context Prompt (For Cursor/Cline in sophia-intel-ai repository)

```markdown
You are working in the sophia-intel-ai repository, a Python backend system providing MCP (Model Context Protocol) servers and AI infrastructure. This is the backend layer of the Sophia Intel AI system.

## Repository Context
- **Location**: ~/sophia-intel-ai
- **Purpose**: Backend MCP servers and AI infrastructure
- **Stack**: Python, FastAPI, Pydantic
- **Architecture**: MCP servers only, no UI

## Key Components
1. **MCP Servers**
   - Memory Server: Port 8081 (mcp/memory_server.py)
   - Filesystem Server: Port 8082 (mcp/filesystem/server.py)
   - Git Server: Port 8084 (mcp/git/server.py)
   - Vector Server: Port 8085 (mcp/vector/server.py)

2. **Sophia CLI**
   - Location: ./sophia_cli/cli.py
   - Commands: plan, code, apply, status
   - Config: ./config/

3. **Portkey Configuration**
   - Virtual Keys: ./config/portkey_virtual_keys.json
   - Model Aliases: ./config/model_aliases.json
   - Auth: x-portkey-api-key header

## Key Rules
- ✅ MCP servers only, no UI components
- ✅ Python 3.11+ with type hints
- ✅ FastAPI for all servers
- ✅ Follow PEP 8 and PEP 484
- ✅ Use pydantic for validation
- ❌ NO frontend code in this repository
- ❌ NO Agno framework here
- ❌ NO React/TypeScript UI code

## Available Commands
- `./dev start-mcp` - Start all MCP servers
- `./dev stop-mcp` - Stop all MCP servers
- `./sophia status` - Check system status
- `./sophia plan <task>` - Plan a task
- `./sophia code` - Generate code
- `./sophia apply` - Apply changes

## Environment Variables (.env.master)
- PORTKEY_USER_KEY - Main Portkey user key
- PORTKEY_VIRTUAL_KEY_* - Virtual key IDs (without @ prefix)
- ANTHROPIC_API_KEY - Direct Anthropic key
- OPENAI_API_KEY - Direct OpenAI key

## File Patterns
- MCP Servers: mcp/**/*.py
- CLI: sophia_cli/*.py
- Config: config/*.json
- Scripts: scripts/*.sh
```

---

## 3. Workspace-UI Terminal CLI Prompt

```bash
# Workspace-UI Development Environment Initialization
# This prompt is for terminal/CLI operations in the workspace-ui repository

# Navigate to workspace-ui repository
cd ~/worktrees/workbench-ui  # or cd ~/workbench-ui

# Environment Setup
export REPO_ENV_MASTER_PATH=~/sophia-intel-ai/.env.master
export NODE_ENV=development
export PORT=3201

# Install dependencies (if needed)
npm install

# Install Agno v2 packages (already in package.json)
# @agno-agi/core@^2.0.0
# @agno-agi/ui@^2.0.0
# portkey-ai@latest

# Start development server with MCP connection
npm run dev

# In another terminal - Agno CLI commands
npm run agno:init          # Initialize Agno framework
npm run agno:agents        # List available agents
npm run agno:chain run development  # Run development workflow
npm run agno:ui            # Start Agno UI in hybrid mode
npm run agno:health        # Check system health

# TypeScript compilation
npx tsc --noEmit          # Type check
npx tsc --watch           # Watch mode

# Testing
npm test                   # Run all tests
npm run agno:test         # Test Agno components

# Agent interaction via CLI
npx tsx agno/scripts/agent.ts interact --agent architect --message "Design a new feature"
npx tsx agno/scripts/chain.ts execute --workflow feature_development

# MCP connection testing
curl http://localhost:8081/health  # Memory server
curl http://localhost:8082/health  # Filesystem server
curl http://localhost:8084/health  # Git server
curl http://localhost:8085/health  # Vector server

# Git operations (workspace-ui is separate repo)
git add -A
git commit -m "feat(agno): implement agent orchestration"
git push origin main
```

---

## 4. Sophia-Intel-AI Terminal CLI Prompt

```bash
# Sophia-Intel-AI Backend Environment Initialization
# This prompt is for terminal/CLI operations in the sophia-intel-ai repository

# Navigate to sophia-intel-ai repository
cd ~/sophia-intel-ai

# Environment Setup
source .env.master  # Load master environment
export PYTHONPATH=$PWD:$PYTHONPATH

# Start MCP servers (all at once)
./dev start-mcp
# Or individually:
python mcp/memory_server.py &        # Port 8081
python mcp/filesystem/server.py &    # Port 8082
python mcp/git/server.py &           # Port 8084
python mcp/vector/server.py &        # Port 8085

# Check MCP server status
./dev status
# Or:
./sophia status

# Sophia CLI workflow
./sophia plan "Implement a new API endpoint"
./sophia code
./sophia apply

# Test MCP servers
python -m pytest mcp/tests/
python test_system_complete.py

# MCP server health checks
for port in 8081 8082 8084 8085; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health | jq .
done

# Portkey testing
python test_cli_bypass.py  # Test direct Portkey integration

# Log monitoring
tail -f logs/mcp_memory.log
tail -f logs/mcp_filesystem.log
tail -f logs/sophia_cli.log

# Git operations (backend repo)
git add -A
git commit -m "feat(mcp): enhance memory server capabilities"
git push origin main

# System validation
python scripts/validate_system.py
./scripts/health_check_all.sh

# Stop MCP servers
./dev stop-mcp
# Or:
pkill -f "python mcp/"
```

---

## 🔄 Context Switching Guidelines

### When switching between repositories:

1. **From sophia-intel-ai to workspace-ui:**
   - Ensure MCP servers are running
   - Switch mental model from Python to TypeScript
   - Focus on UI/UX and agent orchestration
   - Use Agno framework and Portkey SDK

2. **From workspace-ui to sophia-intel-ai:**
   - Ensure frontend is not dependent on current changes
   - Switch mental model from TypeScript to Python
   - Focus on backend services and MCP protocol
   - Use FastAPI and Pydantic

### Key Differences:
| Aspect | workspace-ui | sophia-intel-ai |
|--------|-------------|-----------------|
| Language | TypeScript | Python |
| Framework | Next.js/React | FastAPI |
| AI Framework | Agno v2 | None (MCP only) |
| Port Range | 3200-3299 | 8081-8085 |
| Package Manager | npm | pip/poetry |
| Config Format | JSON/YAML | JSON/Python |
| Testing | Jest | Pytest |

---

## 🚀 Quick Start Commands

### Full System Startup (both repos):
```bash
# Terminal 1: Start MCP servers
cd ~/sophia-intel-ai && ./dev start-mcp

# Terminal 2: Start workspace-ui
cd ~/worktrees/workbench-ui
export REPO_ENV_MASTER_PATH=~/sophia-intel-ai/.env.master
npm run dev

# Terminal 3: Monitor logs
cd ~/sophia-intel-ai
tail -f logs/*.log
```

### System Health Check:
```bash
# From sophia-intel-ai
./sophia status

# From workspace-ui
npm run agno:health
```

---

*These prompts provide complete context for AI assistants working in either repository or terminal environment.*