# Environmental Separation Plan - Sophia Intel AI & Artemis CLI
**Date:** September 7, 2025  
**Status:** CRITICAL - Implementation Required

## 🎯 Core Principle: Absolute Environmental Clarity

### Repository Separation Matrix

| Component | Sophia Intel AI | Artemis CLI | Shared (MCP) |
|-----------|----------------|-------------|--------------|
| **Purpose** | Business Intelligence | AI Coding Agents | Bridge Layer |
| **Location** | `/Users/lynnmusil/sophia-intel-ai` | `https://github.com/ai-cherry/artemis-cli` | MCP Servers |
| **API Keys** | Business Services Only | AI Model Keys Only | None |
| **Startup** | `sophia-start.sh` | `artemis-start.sh` | Auto via orchestrator |

### 🔑 API Key Separation (CRITICAL)

#### Sophia Intel AI Keys (Business Services ONLY)
```env
# .env.sophia - BUSINESS SERVICES ONLY
APOLLO_API_KEY=xxx
SLACK_API_TOKEN=xxx
SALESFORCE_CLIENT_ID=xxx
AIRTABLE_API_KEY=xxx
ASANA_API_TOKEN=xxx
LINEAR_API_KEY=xxx
HUBSPOT_API_KEY=xxx
LOOKER_CLIENT_ID=xxx
NETSUITE_CLIENT_ID=xxx
INTERCOM_ACCESS_TOKEN=xxx

# Database & Infrastructure (Sophia manages)
POSTGRES_URL=xxx
REDIS_URL=xxx
QDRANT_API_KEY=xxx
WEAVIATE_API_KEY=xxx
```

#### Artemis CLI Keys (AI Models ONLY)
```env
# .env.artemis - AI MODELS ONLY (Local Environment)
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx
GROQ_API_KEY=xxx
GROK_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
MISTRAL_API_KEY=xxx
COHERE_API_KEY=xxx
PERPLEXITY_API_KEY=xxx
TOGETHER_AI_API_KEY=xxx

# Portkey Virtual Keys (Model Routing)
PORTKEY_API_KEY=xxx
anthropic-vk-xxx
openai-vk-xxx
groq-vk-xxx
```

#### Shared Infrastructure (MCP Managed)
```env
# .env.mcp - SHARED SERVICES
MCP_MEMORY_HOST=0.0.0.0
MCP_MEMORY_PORT=8765
MCP_BRIDGE_ENABLED=true
MCP_DOMAIN_ISOLATION=true
```

## 🚀 Unified Startup Architecture

### Single Entry Point System
```yaml
# startup-config.yml
version: "2.0"
environment: production

services:
  # Core Infrastructure (Start First)
  redis:
    command: "redis-server"
    port: 6379
    health_check: "redis-cli ping"
    
  postgres:
    command: "postgres"
    port: 5432
    health_check: "pg_isready"
    
  # MCP Bridge Layer (Start Second)
  mcp_memory:
    command: "python mcp_memory_server/main.py"
    port: 8765
    depends_on: [redis]
    env_file: .env.mcp
    
  mcp_bridge:
    command: "python mcp-bridge/server.py"
    port: 8766
    depends_on: [mcp_memory]
    env_file: .env.mcp
    
  # Domain Services (Start Third)
  sophia_backend:
    command: "python backend/main.py"
    port: 8000
    depends_on: [postgres, redis, mcp_bridge]
    env_file: .env.sophia
    
  artemis_agents:
    command: "python artemis/agent_server.py"
    port: 8100
    depends_on: [mcp_bridge]
    env_file: .env.artemis
```

## 🗑️ Removal List (Delete Immediately)

### Virtual Environment References
```bash
# Files to modify - remove venv management
- sophia.sh (lines 45-52)
- deploy.sh (lines 89-94)
- start_mcp_memory.sh (venv activation)
- scripts/deploy.sh (venv creation)
```

### Legacy IDE-Specific Integrations
```bash
# Remove any legacy IDE-specific sections from configs (Cursor/Cline/Roo)
- roo_cursor section (lines 104-193)
- cline section (lines 195-277)
- ide_specific_overrides mentioning roo/cline (lines 349-361)
```

### Duplicate Startup Scripts (Archive)
```bash
# Move to archive/old_scripts/
- start_system.sh (wrong directory reference)
- start_services.sh (Codespaces specific)
- start_essential_services.sh (unclear purpose)
- start_dashboard.sh
- start_server.sh
- start-local.sh
- scripts/redis-integration-startup.sh
- scripts/start-redis-optimized.sh
```

## 📝 New Unified Startup Script

```bash
#!/bin/bash
# unified-start.sh - Single entry point for all services

set -e

# Source environment configuration
source .env.mcp
source .env.sophia
# Note: .env.artemis loaded by Artemis CLI locally

# Start unified orchestrator
python3 scripts/unified_orchestrator.py \
  --config startup-config.yml \
  --environment ${ENVIRONMENT:-development} \
  --no-venv \
  --health-check \
  --log-level INFO

echo "✅ All services started successfully"
echo "📊 Sophia Backend: http://localhost:8000"
echo "🤖 Artemis Agents: http://localhost:8100"
echo "🧠 MCP Memory: http://localhost:8765"
```

## 🔧 AI Agent CLI Standardization

### Grok Agent Interface
```python
# scripts/agents/grok_agent.py
import os
from app.models.agent_base import AgentBase

class GrokAgent(AgentBase):
    def __init__(self):
        self.api_key = os.getenv('GROK_API_KEY')  # From Artemis env
        self.model = "x-ai/grok-code-fast-1"
        self.mcp_bridge = MCPBridge(domain='artemis')
    
    def execute(self, task):
        # Use MCP bridge for memory/context
        context = self.mcp_bridge.get_context(task)
        # Execute via Artemis domain
        return self.process_with_model(task, context)
```

### Claude Coder Agent Interface
```python
# scripts/agents/claude_coder_agent.py
class ClaudeCoderAgent(AgentBase):
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')  # From Artemis env
        self.model = "claude-3-opus-20240229"
        self.mcp_bridge = MCPBridge(domain='artemis')
        
    def code_task(self, request):
        # Coding tasks via Artemis domain
        return self.mcp_bridge.execute_artemis_task(request)
```

### Codex Agent Interface
```python
# scripts/agents/codex_agent.py
class CodexAgent(AgentBase):
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')  # From Artemis env
        self.model = "gpt-4-turbo-preview"
        self.mcp_bridge = MCPBridge(domain='artemis')
```

## 📋 Requirements Consolidation

### Single Requirements File
```txt
# requirements.txt - Consolidated dependencies

# Core Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# AI/ML Libraries
openai==1.6.0
anthropic==0.8.0
groq==0.3.0
langchain==0.1.0

# Business Integrations (Sophia)
slack-sdk==3.23.0
salesforce-bulk==2.2.0
airtable-python-wrapper==0.15.3

# Database & Storage
psycopg2-binary==2.9.9
redis==5.0.1
qdrant-client==1.7.0
weaviate-client==3.25.3

# MCP Bridge
websockets==12.0
jsonrpc==3.0.0

# Development (optional)
pytest==7.4.3
black==23.12.0
ruff==0.1.8
```

## 🐳 Docker Compose Cleanup

### Keep Only Two Files
```yaml
# docker-compose.yml - Production
version: '3.8'
services:
  sophia:
    build: .
    env_file: .env.sophia
    
  mcp-bridge:
    build: ./mcp-bridge
    env_file: .env.mcp

# docker-compose.dev.yml - Development
version: '3.8'
services:
  sophia:
    extends:
      file: docker-compose.yml
      service: sophia
    volumes:
      - .:/app
    environment:
      - DEBUG=true
```

## ✅ Implementation Checklist

### Phase 1: Environment Cleanup (TODAY)
- [ ] Remove all venv references from scripts
- [ ] Delete legacy IDE-specific sections from configs
- [ ] Archive old startup scripts
- [ ] Create .env.sophia, .env.artemis, .env.mcp files

### Phase 2: Unified Startup (TODAY)
- [ ] Create unified_orchestrator.py
- [ ] Write startup-config.yml
- [ ] Test unified-start.sh
- [ ] Remove all other startup scripts

### Phase 3: Agent Standardization (TOMORROW)
- [ ] Implement grok_agent.py
- [ ] Implement claude_coder_agent.py
- [ ] Implement codex_agent.py
- [ ] Create unified agent CLI interface

### Phase 4: Final Cleanup (TOMORROW)
- [ ] Consolidate requirements.txt
- [ ] Archive extra docker-compose files
- [ ] Update documentation
- [ ] Run full system test

## 🎯 Success Metrics

### Environment Health
```bash
# No virtual environments
find . -name "venv" -o -name ".venv" | wc -l  # Should be 0

# Clear separation
grep -r "SALESFORCE" .env.artemis  # Should be empty
grep -r "ANTHROPIC" .env.sophia    # Should be empty

# Single startup
ls start*.sh | wc -l  # Should be 1 (unified-start.sh)
```

### System Validation
```bash
# Test MCP bridge
curl http://localhost:8766/health

# Test Sophia (business)
curl http://localhost:8000/api/integrations

# Test Artemis (coding)
curl http://localhost:8100/api/agents
```

## 🚨 Critical Actions

1. **STOP** creating virtual environments immediately
2. **DELETE** Roo/Cline references from all configurations
3. **SEPARATE** API keys into correct .env files
4. **USE** only unified-start.sh for all startup needs
5. **TEST** each domain isolation before deployment

## 📊 Expected Outcomes

- **Startup Time:** Reduced from ~5 minutes to ~30 seconds
- **Script Count:** Reduced from 14+ to 1
- **Environment Conflicts:** Zero
- **API Key Leakage:** Zero
- **Agent Confusion:** Zero

---

**Implementation Owner:** Repository Maintainer  
**Timeline:** Complete Phase 1-2 TODAY, Phase 3-4 TOMORROW  
**Risk Level:** LOW (with proper testing)  
**Rollback:** Git history maintains all previous configurations
