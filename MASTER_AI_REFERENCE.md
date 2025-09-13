# 🎯 MASTER AI AGENT REFERENCE - PASTE THIS AT THE TOP OF EVERY THREAD

## 🏗️ SYSTEM ARCHITECTURE - TWO SEPARATE APPS

```
sophia-intel-ai/
├── sophia-intel-app/        # Business Intelligence UI (Port 3000)
├── builder-agno-system/     # Code Generation System (Port 8005)
├── app/                     # Shared Backend Services
├── mcp-unified/             # MCP Servers (Ports 8080-8084)
└── infra/                   # Infrastructure & Docker
```

### **NEVER CONSOLIDATE THESE TWO APPS**
| System | Purpose | Ports | Directory |
|--------|---------|-------|-----------|
| **Sophia Intel** | Business Intelligence for PayReady | 3000 (UI), 8003 (API) | `sophia-intel-app/` |
| **Builder Agno** | Code Generation & Agent Swarms | 8005 | `builder-agno-system/` |

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
app/sophia/sophia_orchestrator.py    # Main orchestrator
app/integrations/*.py                 # 21 existing integrations
app/api/unified_server.py            # Main API server
```

### UI Components
```
sophia-intel-app/src/           # Sophia UI (React/Next.js)
builder-agno-system/src/        # Builder UI (separate app)
```

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
```

## 🚀 STARTUP COMMANDS - USE THESE ONLY

### Docker (Preferred - Everything at Once)
```bash
cd infra
docker-compose --profile dev up     # Starts everything
```

### Native Development
```bash
# Sophia Intel (Business Intelligence)
./start_sophia_intel.sh            # UI on 3000, API on 8003

# Builder Agno (Code Generation)
./start_builder_agno.sh            # Combined UI/API on 8005

# MCP Servers (Required for AI coordination)
./mcp-unified/start_mcp.sh         # Gateway on 8080
```

## ⚠️ RULES - VIOLATE THESE AND FACE CONSEQUENCES

### FORBIDDEN ACTIONS ❌
1. **NEVER** consolidate Builder and Sophia into one app
2. **NEVER** create new UI frameworks or dashboards
3. **NEVER** create duplicate integrations
4. **NEVER** mix Builder components in Sophia or vice versa
5. **NEVER** create new .env files
6. **NEVER** commit API keys to git
7. **NEVER** create "unified" or "consolidated" UIs
8. **NEVER** change port assignments

### REQUIRED ACTIONS ✅
1. **ALWAYS** connect to MCP gateway at localhost:8080
2. **ALWAYS** use `app/core/config.py` for configuration
3. **ALWAYS** check if a feature exists before creating
4. **ALWAYS** maintain separation between apps
5. **ALWAYS** use existing integrations in `app/integrations/`
6. **ALWAYS** follow the naming conventions below

## 🏷️ NAMING CONVENTIONS - STRICT ENFORCEMENT

### Components
```typescript
// Sophia Intel Components
export const SophiaIntelDashboard = ...
export const SophiaIntelMetrics = ...

// Builder Agno Components  
export const BuilderAgnoEditor = ...
export const BuilderAgnoSwarm = ...
```

### API Endpoints
```python
# Sophia endpoints
@router.get("/api/sophia/metrics")
@router.post("/api/sophia/sync")

# Builder endpoints
@router.post("/api/builder/generate")
@router.get("/api/builder/swarms")
```

### Environment Variables
```bash
SOPHIA_INTEL_*     # For Sophia app
BUILDER_AGNO_*     # For Builder app
MCP_*              # For MCP servers
```

## 📊 CURRENT PROBLEMS BEING FIXED

### Configuration Chaos
- **80+ JSON config files** → Consolidating to 5
- **100+ YAML files** → Reducing to 10
- **16 .env files** → Moving to centralized secrets

### Duplicate Implementations
- **15+ UI directories** → Keeping only 2 (sophia-intel-app, builder-agno-system)
- **10+ MCP implementations** → Unified in mcp-unified/
- **20+ startup scripts** → Reduced to 3

### Infrastructure Sprawl
- Docker Compose + Kubernetes + Pulumi all defining same things
- Standardizing on Docker for local, Pulumi for cloud

## 🔍 HOW TO CHECK BEFORE CREATING

### Before Creating ANY Feature
```bash
# Search for existing implementations
grep -r "feature_name" app/
grep -r "FeatureName" sophia-intel-app/src/
ls -la app/integrations/

# Check running services
docker ps
lsof -i :3000
lsof -i :8003
lsof -i :8005
```

### Validation Commands
```bash
# Verify app separation
./validate_separation.sh

# Check configuration
python app/core/config.py --validate

# Test MCP connection
curl http://localhost:8080/health
```

## 🎯 WHO OWNS WHAT

| Component | Owner | Purpose |
|-----------|-------|---------|
| Sophia Intel App | Business Team | Revenue, metrics, customer data |
| Builder Agno | Dev Team | Code generation, development |
| MCP Servers | Infrastructure | Shared memory and context |
| Integrations | API Team | External service connections |

## 📋 QUICK DECISION GUIDE

```
User asks about...
├── Sales/Revenue/Metrics/Business
│   └── sophia-intel-app/ (Port 3000/8003)
├── Code/Development/Agents/Swarms
│   └── builder-agno-system/ (Port 8005)
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
- [ ] Verify which app you're working on (Sophia or Builder)
- [ ] Check for existing implementations
- [ ] Use correct naming conventions
- [ ] Don't create new config files
- [ ] Don't consolidate the apps

---

**REMEMBER**: 
- Two separate apps (Sophia Intel & Builder Agno)
- One unified MCP system for coordination
- One configuration system (app/core/config.py)
- Zero tolerance for consolidation attempts

**Last Updated**: 2025-01-11
**Owner**: Lynn Musil (CEO)
**Enforcement**: MANDATORY
