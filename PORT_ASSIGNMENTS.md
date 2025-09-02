# OFFICIAL PORT ASSIGNMENTS - SOPHIA INTEL AI
## DO NOT CHANGE THESE WITHOUT UPDATING THIS DOCUMENT

### PRODUCTION PORT ASSIGNMENTS:

| Port | Service | Status | Process |
|------|---------|--------|---------|
| 3000 | Next.js UI (agent-ui) | ✅ ACTIVE | `npm run dev` |
| 6379 | Redis Server | ✅ ACTIVE | `redis-server` |
| 8000 | ~~MCP Memory Server~~ | ❌ CONFLICT | Something else using it |
| 8001 | MCP Memory Server | ✅ ACTIVE | `app.mcp.server_v2` |
| 8002 | Metrics/Monitoring | ⚠️ RESERVED | Prometheus |
| 8003 | MCP Code Review Server | ✅ ACTIVE | `code_review_server/index.ts` |
| 8004 | Vector Store Service | ⚠️ RESERVED | Weaviate bridge |
| 8005 | **MAIN SWARM API** | ✅ ACTIVE | `app.api.unified_server` |
| 8006 | Backup/Testing | 🚫 FREE | Available |
| 8007 | Development | 🚫 FREE | Available |
| 8008 | Development | 🚫 FREE | Available |
| 8080 | Weaviate Vector DB | ⚠️ RESERVED | Docker |
| 8082 | Unknown Process | ❓ CHECK | Unknown |
| 8501 | Streamlit UI | ✅ ACTIVE | `streamlit run` |

### ENVIRONMENT VARIABLES:
```bash
# Main API Server (Swarm + Embeddings + Teams)
AGENT_API_PORT=8005

# MCP Servers
MCP_MEMORY_PORT=8000
MCP_CODE_REVIEW_PORT=8003

# UI Ports
NEXT_PUBLIC_API_URL=http://localhost:8005
AGENT_UI_PORT=3000
STREAMLIT_PORT=8501

# Database Ports
REDIS_PORT=6379
WEAVIATE_PORT=8080
```

### TO START EVERYTHING:
```bash
# 1. Redis (if not running)
redis-server

# 2. Main Swarm API with AI Models
cd /Users/lynnmusil/sophia-intel-ai
OPENROUTER_API_KEY=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 \
PORTKEY_API_KEY=nYraiE8dOR9A1gDwaRNpSSXRkXBc \
AGENT_API_PORT=8005 \
python3 -m app.api.unified_server

# 3. UI (already running on 3000)
cd agent-ui && npm run dev

# 4. MCP Code Review (already running on 8003)
npm exec ts-node --esm app/mcp/code_review_server/index.ts
```

### API ENDPOINTS:
- Main API: http://localhost:8005
- Teams: POST http://localhost:8005/teams/run
- Embeddings: POST http://localhost:8005/mcp/embeddings
- WebSocket: ws://localhost:8005/ws/bus
- UI: http://localhost:3000
- Swarm UI: http://localhost:3000/swarm-ui.html

### NEVER USE THESE PORTS:
- 3000 - Next.js UI
- 6379 - Redis
- 8003 - MCP Code Review
- 8005 - Main Swarm API
- 8501 - Streamlit

### AVAILABLE FOR NEW SERVICES:
- 8000 - Can be used for MCP Memory when fixed
- 8001 - Can be used for WebSocket when needed
- 8002 - Can be used for metrics
- 8004 - Can be used for vector store
- 8006-8008 - Free for development

## THIS IS THE SINGLE SOURCE OF TRUTH FOR PORTS!