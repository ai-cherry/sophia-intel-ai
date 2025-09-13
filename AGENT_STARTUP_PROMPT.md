# 🧠 **AGENT STARTUP PROMPT**
*Essential context for AI agents starting new terminal sessions*

## 📋 **IMMEDIATE CONTEXT LOADING**

When starting a new terminal session with AI agents, **ALWAYS read these files first**:

1. **Primary Context** (MANDATORY):
   ```bash
   # Central command hub - read this FIRST
   cat AGENT_INTELLIGENCE_HUB.md
   
   # Critical architecture rules - NEVER violate these
   cat docs/CENTRALIZED_RULES.md
   
   # Available tools and services
   cat docs/TOOLS_REGISTRY.md
   
   # Learning from past mistakes
   cat docs/CONTINUOUS_LEARNING.md
   ```

2. **Environment Setup** (AUTO-LOAD):
   ```bash
   # Load centralized secrets
   source ./.env.master
   
   # Verify MCP services are running
   curl -s http://localhost:8081/health  # Memory MCP
   curl -s http://localhost:8082/health  # Filesystem MCP
   curl -s http://localhost:8084/health  # Git MCP
   curl -s http://localhost:8000/api/health  # Unified API
   ```

## 🏗️ **TWO-APP ARCHITECTURE AWARENESS**

**CRITICAL**: This repository has **TWO SEPARATE APPLICATIONS**:

### 1. **Sophia Intel App** (Business Intelligence)
- **URL**: http://localhost:3000
- **Purpose**: PayReady business intelligence, analytics, dashboards
- **Start**: `bash scripts/dev/bootstrap_all.sh`
- **Domain**: Business logic, reporting, customer data

### 2. **Builder Agno System** (Code & Infrastructure)
- **URL**: http://localhost:8005 (or 8006)
- **Purpose**: Code generation, infrastructure, technical agents
- **Start**: `bash start_builder_agno.sh`
- **Domain**: Development tools, coding assistance, DevOps

**🚨 NEVER CREATE ADDITIONAL DASHBOARD APPS**
- All dashboards must be tabs/pages within existing apps
- No standalone UI services
- No one-off dashboard URLs

### Non-Negotiable Separation (Do Not Consolidate)
- Do not propose, plan, or implement any unification of the two apps.
- Builder Agno System (code/infrastructure) and Sophia Intel App (business intelligence) remain separate UIs and domains.
- No cross-imports between their UI code or direct embedding of one app’s components into the other.
- Shared functionality must be accessed via the unified API or MCP services only.

## ✅ **DIRECTORIES CLEANED: SINGLE SOPHIA DIRECTORY**

**RESOLVED**: Multiple sophia directories issue has been **ELIMINATED**:
- ✅ **Only 1 directory remains**: `/Users/lynnmusil/sophia-intel-ai` (719MB freed!)
- ✅ **All backups removed** and archived to `~/sophia-backup-20250909.tar.gz`
- ✅ **Port conflicts resolved** - no more competing processes
- ✅ **Automated monitoring active** - prevents future directory conflicts

**ALWAYS work from**: `/Users/lynnmusil/sophia-intel-ai` (auto-verified on startup)

## 🤖 **AUTOMATED MONITORING & ENFORCEMENT** 

**FIRST STEP**: AI-powered system integrity check (automatically runs on startup):

```bash
# AUTOMATED: Comprehensive monitoring system (runs automatically in background)
~/.config/sophia/enforcement/startup_monitor.sh

# This AI-powered system automatically:
# ✅ Prevents new sophia directory conflicts (Directory Guard)
# ✅ Resolves port conflicts in real-time (Port Monitor) 
# ✅ Verifies MCP service health (Service Monitor)
# ✅ Trains AI factory agents with current rules (Factory Trainer)
# ✅ Sends periodic reminders to orchestrators (Reminder System)
# ✅ Enforces two-app architecture separation (Architecture Guard)

# Manual cleanup available if needed:
./scripts/cleanup_processes.sh

# Start applications (after automated verification):
./scripts/start_apps_properly.sh
```

## 🧠 **AI ORCHESTRATOR INTEGRATION**

**NEW**: Both app factories now have AI orchestrator personas with centralized rules:

### **Sophia AI Factory** (Business Intelligence Domain):
- 🎯 **Domain**: Business intelligence, analytics, reporting ONLY
- 🚫 **Auto-rejects**: Code generation, infrastructure tasks  
- 🔄 **5-min reminders**: Centralized rules and MCP service status
- 📊 **Trained on**: PayReady business logic, customer analytics

### **Builder AI Factory** (Technical Domain):
- 🛠️ **Domain**: Code generation, infrastructure, DevOps ONLY
- 🚫 **Auto-rejects**: Business intelligence, reporting tasks
- 🔄 **5-min reminders**: Development tools, deployment configs
- ⚙️ **Trained on**: Technical architecture, MCP integrations

## 🔧 **ESSENTIAL SERVICES STATUS**

After cleanup, verify these services:

```bash
# MCP Services (Core Infrastructure)
curl -s http://localhost:8081/health | jq .  # Memory
curl -s http://localhost:8082/health | jq .  # Filesystem  
curl -s http://localhost:8084/health | jq .  # Git

# Unified API (Backend)
curl -s http://localhost:8000/api/health | jq .
# OR
curl -s http://localhost:8010/api/health | jq .

# Verify correct directory
pwd  # Should be /Users/lynnmusil/sophia-intel-ai

# Check apps are running from CORRECT directory
ps aux | grep -E "(next|npm|node)" | grep sophia-intel-ai
```

## 📊 **KNOWLEDGE BASE QUICK REFERENCE**

### **Success Patterns** (USE THESE):
- Centralized configuration at `<repo>/.env.master`
- MCP services for all data operations
- Two-app separation with no cross-contamination
- Haystack/Qdrant for repository indexing
- Portkey for LLM routing and governance

### **Failure Patterns** (AVOID THESE):
- Creating separate dashboard apps
- Scattered .env files
- Cross-domain agent contamination
- Bypassing centralized configuration
- Using deprecated AI models

### **Approved AI Models** (2025):
- **Allowed**: gpt-5, claude-4.1-sonnet, claude-4.1-opus, grok-code-fast-1
- **Blocked**: gpt-4o, claude-3.5-sonnet, claude-3-haiku, legacy families

## 🎯 **AGENT QUICK START CHECKLIST**

1. **[ ]** **CRITICAL**: Verify you're in `/Users/lynnmusil/sophia-intel-ai`
2. **[ ]** **MANDATORY**: Run `./scripts/cleanup_processes.sh` first
3. **[ ]** Read `AGENT_INTELLIGENCE_HUB.md`
4. **[ ]** Load centralized secrets from `<repo>/.env.master`
5. **[ ]** Start apps: `./scripts/start_apps_properly.sh`
6. **[ ]** Verify all MCP services healthy (8081, 8082, 8084)
7. **[ ]** Check Unified API status (8000/8010)
8. **[ ]** Identify which app domain you're working in (Sophia vs Builder)
9. **[ ]** Review relevant success/failure patterns
10. **[ ]** Connect to appropriate MCP services
11. **[ ]** Follow centralized rules and architecture

## 💡 **COMMON TASKS QUICK COMMANDS**

### **Repository Indexing**:
```bash
# Index repository for semantic search
python3 scripts/index_repository.py --system qdrant

# Check indexing status
python3 scripts/index_repository.py --list-indexed
```

### **System Health**:
```bash
# Full system health check
curl -s http://localhost:8081/health && \
curl -s http://localhost:8082/health && \
curl -s http://localhost:8084/health && \
curl -s http://localhost:8000/api/health
```

### **Start Applications** (UPDATED PROCESS):
```bash
# CRITICAL: Always clean up first (multiple sophia directories cause conflicts)
./scripts/cleanup_processes.sh

# Start both applications properly from correct directory
./scripts/start_apps_properly.sh

# Alternative: Start individually (after cleanup)
cd sophia-intel-app && npm run dev &    # Port 3000
cd ../builder-agno-system && npm run dev -- --port 8005 &  # Port 8005
```

## 🔍 **DEBUGGING COMMON ISSUES**

### **MCP Services Not Responding**:
```bash
# Check if services are running
ps aux | grep -E "mcp|uvicorn" | grep -v grep

# Restart MCP services
bash scripts/start_centralized_mcp.py
```

### **Port Conflicts (MAJOR ISSUE)**:
```bash
# CRITICAL: Multiple sophia directories cause port conflicts
# Solution: Always clean up first
./scripts/cleanup_processes.sh

# Check what's using critical ports
lsof -i :3000 -i :8000 -i :8005 -i :8081 -i :8082 -i :8084

# Manual cleanup if needed
kill -9 $(lsof -ti:3000) 2>/dev/null
kill -9 $(lsof -ti:8005) 2>/dev/null
```

### **Authentication Issues**:
```bash
# Verify MCP_TOKEN is set
echo $MCP_TOKEN

# Test authenticated MCP access
curl -H "Authorization: Bearer $MCP_TOKEN" http://localhost:8082/symbols/search?query=function
```

## 📚 **ARCHITECTURAL PRINCIPLES**

1. **Single Source of Truth**: All configuration in centralized location
2. **Domain Separation**: Business vs. Technical - never mix
3. **Service-Oriented**: Use MCP services for all operations
4. **Knowledge Persistence**: Learn from failures, reuse success patterns
5. **AI Governance**: Only use approved, latest models

---

## 🎭 **AGENT PERSONA ACTIVATION**

**You are now a knowledgeable agent in the Sophia Intel AI ecosystem.**

- You understand the two-app architecture and will never violate it
- You use centralized services and configuration
- You learn from documented patterns and avoid known failures
- You follow the principle of controlled knowledge sharing
- You prioritize system integrity and architectural compliance

**Ready to assist with business intelligence (Sophia) or technical development (Builder) tasks.**

---

*This prompt ensures every AI agent starts with complete context and follows established patterns.*
