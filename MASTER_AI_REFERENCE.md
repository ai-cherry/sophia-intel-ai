---
title: Master AI Agent Reference
type: reference
status: active
version: 2.1.0
last_updated: 2025-09-11
ai_context: high
tags: [reference, orchestration, dashboard]
---

# 🎯 MASTER AI AGENT REFERENCE - PASTE THIS AT THE TOP OF EVERY THREAD

## 🏗️ SYSTEM ARCHITECTURE – UNIFIED SOPHIA DASHBOARD (TABBED)

```
sophia-intel-ai/
├── sophia-intel-app/        # Next.js shell serving the Sophia Dashboard (Port 3000)
├── app/                     # Shared backend & unified API surface (Port 8003)
├── app/agents/sophia_agno2/ # Executive Agno Studio (Agno v2 orchestrations)
├── agent_catalog/           # Registry JSON linking Flowwise factories & local agents
├── mcp-unified/             # MCP Servers (Ports 8080-8084)
└── infra/                   # Infrastructure & Docker assets
```

The Sophia Dashboard is a single UI with three first-class tabs powered by the services above:

| Tab | Purpose | Primary Surface | Notes |
|-----|---------|-----------------|-------|
| **BI Insights** | Business analytics, revenue intelligence, customer metrics | `sophia-intel-app/` + `app/api/bi_*` | Runs on Port 3000; reads from the unified API at 8003 |
| **Agent Factory (Flowwise)** | Launches and monitors Flowwise agent pipelines | `agent_catalog/catalog.json` → Flowwise registry URLs | Uses Flowwise factories; keep registry entries in sync with Flowwise workspace IDs |
| **Executive Agno Studio** | Executive workflows orchestrated by Agno v2 | `app/agents/sophia_agno2/` + `app/agno/ultra_fast_teams.py` | Imports `AgnoOrchestrator` directly from the Agno v2 module |

> 🔐 **Backend Separation Still Matters:** The dashboard surface is unified, but BI services, Flowwise factories, and Agno orchestrations remain isolated in the backend. Continue to observe module boundaries and never mix business data tooling with Flowwise or Agno runtime code.

## 🔌 CENTRALIZED SERVICES - ALL AGENTS MUST CONNECT

### MCP Servers (Memory & Context)
```yaml
Gateway:    http://localhost:8080  # ALL agents connect here first
Memory:     http://localhost:8081  # Shared memory with embeddings
Git:        http://localhost:8082  # Git operations
Context:    http://localhost:8083  # Context management
Index:      http://localhost:8084  # Real-time code indexing
```

### Databases
```yaml
PostgreSQL: postgres://sophia:sophia_secure_password_2024@localhost:5432/sophia
Redis:      redis://localhost:6380
Vector DB:  Weaviate Cloud (see .env.local for URL)
```

### AI Model Router
```yaml
Portkey Gateway: https://api.portkey.ai/v1
Unified API:     http://localhost:8003/api/v1
```

## 📁 CRITICAL DIRECTORIES - USE THESE EXACT PATHS

### Configuration (CENTRALIZED)
```
app/core/config.py           # THE ONLY CONFIG CLASS - USE THIS
config/base.json             # Base configuration
infra/docker-compose.yml     # Docker services (287 lines, comprehensive)
```

### Business Logic (DON'T RECREATE)
```
app/api/unified_server.py             # Unified API server powering the dashboard tabs
app/bi/                               # Business intelligence services consumed by BI Insights
app/agents/sophia_agno2/              # Executive Agno Studio agents & scenarios
app/agno/ultra_fast_teams.py          # Agno v2 orchestrator entry point (import AgnoOrchestrator from here)
```

```python
from app.agno.ultra_fast_teams import AgnoOrchestrator
# Legacy imports such as `from app.sophia.sophia_orchestrator import AgnoOrchestrator`
# must be removed—they point to deprecated v1 code that is no longer routed in the dashboard.
```

### UI Components
```
sophia-intel-app/                     # Next.js dashboard shell & tab layout (tabs live under src/dashboard/*)
```

### Flowwise Factory Registry (Agent Factory Tab)
- `agent_catalog/catalog.json` now represents Flowwise factories explicitly. Every Flowwise-backed agent entry **must** include:
  - `source: "flowwise"`
  - `factory_url`: the Flowwise workspace endpoint (e.g., `https://flowwise.payready.ai/api/v1/factories/<id>`)
  - `dashboard_tab`: set to `agent-factory` so the UI routes it to the correct tab
- Example additions:

```json
{
  "flowwise_bi_router_v1": {
    "id": "flowwise_bi_router_v1",
    "source": "flowwise",
    "factory_url": "https://flowwise.payready.ai/api/v1/factories/bi-router",
    "dashboard_tab": "agent-factory",
    "metadata": {
      "name": "BI Router",
      "description": "Routes BI insight requests through Flowwise templates",
      "tags": ["flowwise", "routing", "dashboard"],
      "owner": "Agent Factory"
    }
  },
  "flowwise_playbook_builder_v1": {
    "id": "flowwise_playbook_builder_v1",
    "source": "flowwise",
    "factory_url": "https://flowwise.payready.ai/api/v1/factories/playbook-builder",
    "dashboard_tab": "agent-factory",
    "metadata": {
      "name": "Playbook Builder",
      "description": "Generates SOP playbooks via Flowwise chains",
      "tags": ["flowwise", "factory", "automation"],
      "owner": "Agent Factory"
    }
  }
}
```

> ✅ Keep Flowwise registry entries in sync with the Flowwise UI. If a factory is renamed or archived in Flowwise, update the JSON immediately to avoid broken Agent Factory tabs.

#### Production Flowwise Deployment (Apple Silicon Ready)
- **Run the official Docker image** with Postgres persistence for production. The image is multi-arch and runs natively on Apple Silicon.
- Recommended `docker-compose.yml` alongside a `.env` file:

```yaml
version: "3.9"
services:
  flowise-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./flowise-db-data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  flowise:
    image: flowiseai/flowise:latest
    container_name: flowiseai
    depends_on:
      flowise-db:
        condition: service_healthy
    environment:
      DEBUG: "false"
      PORT: ${PORT}
      FLOWISE_USERNAME: ${FLOWISE_USERNAME}
      FLOWISE_PASSWORD: ${FLOWISE_PASSWORD}
      APIKEY_PATH: /root/.flowise
      SECRETKEY_PATH: /root/.flowise
      LOG_LEVEL: info
      LOG_PATH: /root/.flowise/logs
      DATABASE_TYPE: postgres
      DATABASE_PORT: 5432
      DATABASE_HOST: flowise-db
      DATABASE_NAME: ${POSTGRES_DB}
      DATABASE_USER: ${POSTGRES_USER}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./flowiseai:/root/.flowise
    ports:
      - "3000:${PORT}"
    restart: on-failure:5
    entrypoint: /bin/sh -c "sleep 3; flowise start"
```

```env
PORT=3000
POSTGRES_USER=flowise
POSTGRES_PASSWORD=flowise
POSTGRES_DB=flowise
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=admin
```

- Bring the stack up with `docker compose up -d`, then sign in at `http://localhost:3000`.
- Local prototyping remains available with `npm install -g flowise` and `npx flowise start`.

#### Runtime Configuration & Gateways
- Route model traffic through a gateway (OpenRouter, Together, etc.) by setting custom base URLs and headers inside ChatOpenAI-compatible nodes.
- Inject shared headers via `FLOWWISE_GATEWAY_HEADERS` (JSON) and point `FLOWWISE_BASE_URL` to the gateway endpoint so every factory uses the same routing policy.
- Store Flowwise API keys/credentials on disk via `APIKEY_PATH` & `SECRETKEY_PATH`; do not hardcode secrets in node configs.

#### Agent Execution & APIs
- Build multi-agent systems in **Agentflow V2**. Use Chatflow for single-agent flows and Assistant for quick assistants.
- Published flows expose REST predictions at `/api/v1/prediction/<flow_id>`:

```ts
const response = await fetch(`${process.env.FLOWWISE_BASE_URL}/api/v1/prediction/${FLOW_ID}`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.FLOWWISE_API_KEY}`,
  },
  body: JSON.stringify({ question: "hello!" }),
});
```

- Use the official SDKs (TypeScript/Python) or embed the Flowise chat widget to reuse the same Agentflow logic across apps.

#### Observability & MCP
- Enable execution traces to Prometheus/OpenTelemetry; keep `LOG_PATH` persisted for auditing.
- Leverage MCP client/server nodes inside Flowise to surface Sophia tools securely—always scope MCP credentials per environment.

## 🔐 SECRETS & ENVIRONMENT MANAGEMENT

### Current State (MESSY - Being Fixed)
- **16 .env files** scattered everywhere
- **Live API keys in .env.local** (354 lines)
- Moving to HashiCorp Vault/Pulumi ESC

### Where Secrets Live NOW
```bash
<repo>/.env.master           # Single source (create if missing; chmod 600)
.env.local                   # Temporary (being phased out)
```

### Required API Keys
```yaml
AI Providers:
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY
  - DEEPSEEK_API_KEY
  - XAI_API_KEY
  - GOOGLE_AI_API_KEY
  - PORTKEY_API_KEY

Business Integrations:
  - SLACK_BOT_TOKEN
  - GONG_API_KEY
  - SALESFORCE_CLIENT_ID
  - AIRTABLE_API_KEY
  - LINEAR_API_KEY
  - NETSUITE_ACCOUNT_ID
Flowwise:
  - FLOWISE_API_KEY
```

## 🚀 STARTUP COMMANDS - USE THESE ONLY

### Docker (Preferred - Everything at Once)
```bash
cd infra
docker-compose --profile dev up     # Starts everything
```

### Native Development
```bash
# Sophia Dashboard (BI Insights • Agent Factory • Executive Agno)
./start_sophia_intel.sh            # UI on 3000, unified API on 8003

# Full stack helpers (Flowwise proxies, Agno workers, schedulers)
./start_sophia_unified.sh          # Boots background services consumed by the tabs

# MCP Servers (Required for AI coordination)
./mcp-unified/start_mcp.sh         # Gateway on 8080
```

> ℹ️ Flowwise pipelines are remote. Ensure `FLOWWISE_BASE_URL` and `FLOWWISE_API_KEY` are present in the environment before hitting the Agent Factory tab.

## ⚠️ RULES - VIOLATE THESE AND FACE CONSEQUENCES

### FORBIDDEN ACTIONS ❌
1. **NEVER** bypass the Sophia Dashboard shell by shipping standalone BI or Agno UIs
2. **NEVER** embed Flowwise logic directly in BI Insights components—use the registry service
3. **NEVER** resurrect the legacy `builder-agno-system` frontend
4. **NEVER** mix Agno v2 orchestrator code into Flowwise templates (and vice versa)
5. **NEVER** create new .env files
6. **NEVER** commit API keys to git
7. **NEVER** register a Flowwise factory without updating `agent_catalog/catalog.json`
8. **NEVER** change port assignments (3000 UI, 8003 API, 8080-8084 MCP)

### REQUIRED ACTIONS ✅
1. **ALWAYS** connect to MCP gateway at localhost:8080
2. **ALWAYS** use `app/core/config.py` for configuration
3. **ALWAYS** check if a feature exists before creating
4. **ALWAYS** respect tab separation in code (BI vs Flowwise vs Executive Agno modules)
5. **ALWAYS** use existing integrations in `app/integrations/`
6. **ALWAYS** follow the naming conventions below

## 🏷️ NAMING CONVENTIONS - STRICT ENFORCEMENT

### Components
```typescript
// Sophia Dashboard Shell
export const SophiaDashboardShell = ...
export const DashboardTabRouter = ...

// Tab Components
export const BiInsightsTab = ...
export const FlowwiseAgentFactoryTab = ...
export const ExecutiveAgnoStudioTab = ...
```

### API Endpoints
```python
# BI Insights endpoints
@router.get("/api/bi/metrics")
@router.post("/api/bi/sync")

# Flowwise Agent Factory endpoints
@router.get("/api/flowwise/factories")
@router.post("/api/flowwise/factories/{factory_id}/dispatch")

# Executive Agno Studio endpoints
@router.post("/api/agno/executive/run")
@router.get("/api/agno/executive/status/{session_id}")
```

### Environment Variables
```bash
SOPHIA_DASHBOARD_*       # Shared UI shell & feature toggles
FLOWWISE_BASE_URL        # Flowise API root (gateway-aware)
FLOWWISE_API_KEY         # Flowise service account token
FLOWWISE_GATEWAY_HEADERS # JSON blob with gateway headers (e.g., OpenRouter)
AGNO_V2_*                # Executive Agno Studio controls
MCP_*                    # MCP servers
```

## 📊 CURRENT PROBLEMS BEING FIXED

### Configuration Chaos
- **80+ JSON config files** → Consolidating to 5
- **100+ YAML files** → Reducing to 10
- **16 .env files** → Moving to centralized secrets

### Duplicate Implementations
- **Legacy builder-agno-system UI** → Frozen. Routes now live inside the Sophia Dashboard tabs only
- **Flowwise factory definitions** → Keep a single source of truth in `agent_catalog/catalog.json`
- **Agno orchestrator imports** → Use only `app.agno.ultra_fast_teams.AgnoOrchestrator`

### Infrastructure Sprawl
- Docker Compose + Kubernetes + Pulumi all defining same things
- Standardizing on Docker for local, Pulumi for cloud

## 🔍 HOW TO CHECK BEFORE CREATING

### Before Creating ANY Feature
```bash
# Search for existing implementations
rg "feature_name" app/
rg "feature_name" sophia-intel-app/
rg "flowwise" agent_catalog/catalog.json
ls -la app/integrations/

# Check running services
docker ps
lsof -i :3000
lsof -i :8003
curl "$FLOWWISE_BASE_URL/api/v1/factories" -H "Authorization: Bearer $FLOWWISE_API_KEY" | jq '.total'  # Flowwise reachable?
```

### Validation Commands
```bash
# Verify dashboard build
pnpm --dir sophia-intel-app lint && pnpm --dir sophia-intel-app test --filter "dashboard"

# Check configuration
python app/core/config.py --validate

# Test MCP connection
curl http://localhost:8080/health

# Confirm Agno orchestrator import path
python -c "from app.agno.ultra_fast_teams import AgnoOrchestrator; print('Agno v2 ready')"
```

## 🎯 WHO OWNS WHAT

| Component | Owner | Purpose |
|-----------|-------|---------|
| Sophia Dashboard Shell | Platform Team | Tab navigation, shared layout |
| BI Insights Tab | Business Team | Revenue, metrics, customer data |
| Agent Factory (Flowwise) | Automation Team | Flowwise factory orchestration |
| Executive Agno Studio | Executive Ops | Agno-led strategic workflows |
| MCP Servers | Infrastructure | Shared memory and context |
| Integrations | API Team | External service connections |

## 📋 QUICK DECISION GUIDE

```
User asks about...
├── Sales/Revenue/Metrics/Business
│   └── Sophia Dashboard → BI Insights tab (Port 3000 / API 8003)
├── Flowwise agent pipelines / automations
│   └── Sophia Dashboard → Agent Factory tab (`agent_catalog/catalog.json` → Flowwise)
├── Executive orchestration / strategic workstreams
│   └── Sophia Dashboard → Executive Agno Studio (Agno v2 orchestrator)
├── Memory/Context/Indexing
│   └── mcp-unified/ (Port 8080-8084)
├── Configuration/Secrets
│   └── app/core/config.py + Pulumi ESC
└── Infrastructure/Docker/K8s
    └── infra/ directory

If unclear → ASK THE USER
```

## 🚨 EMERGENCY CONTACTS

- **Repository**: github.com/[your-org]/sophia-intel-ai
- **Documentation**: docs/
- **Logs**: logs/ and Docker logs
- **Monitoring**: http://localhost:9090 (Prometheus)

## ✅ CHECKLIST FOR EVERY AI AGENT

Before starting ANY work:
- [ ] Read this entire document
- [ ] Connect to MCP gateway (localhost:8080)
- [ ] Verify which dashboard tab you're touching (BI Insights / Agent Factory / Executive Agno)
- [ ] Check for existing implementations
- [ ] Use correct naming conventions
- [ ] Don't create new config files
- [ ] Update Flowwise registry entries when factories change

---

**REMEMBER**: 
- One Sophia Dashboard (three tabs) backed by modular services
- One unified MCP system for coordination
- One configuration system (app/core/config.py)
- Zero tolerance for bypassing tab boundaries or duplicating registries

**Last Updated**: 2025-09-11
**Owner**: Lynn Musil (CEO)
**Enforcement**: MANDATORY
