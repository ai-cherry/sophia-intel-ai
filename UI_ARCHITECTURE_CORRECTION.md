# 🚨 UI Architecture Correction & Agno 2.0 Migration Plan

## CRITICAL: Three Separate UI Systems Required

### Current Reality vs Required State

## ❌ CURRENT FUCKED UP STATE
- Only ONE main UI (Sophia Intel App)
- Builder components mixed into Sophia Intel
- No separate LiteLLM Squad UI
- Not using Agno 2.0 stateless architecture
- Missing Builder dashboard on Port 8005

## ✅ REQUIRED STATE (Three Separate UIs)

### 1. SOPHIA INTEL APP (Business Intelligence)
- **Port**: 8000
- **Location**: `/sophia-intel-app/`
- **Purpose**: Business intelligence, integrations, team management
- **Tech Stack**: Next.js 15, React 18, TypeScript
- **Status**: EXISTS ✅

### 2. BUILDER AGNO SYSTEM (Code Generation)
- **Port**: 8005
- **Location**: `/builder-agno-app/` (NEEDS CREATION)
- **Purpose**: Code generation, agent building, repository management
- **Tech Stack**: React + Vite, Agno 2.0 stateless agents
- **Bridge API**: Port 8004
- **Status**: MISSING UI ❌ (only has backend components)

### 3. LITELLM SQUAD APP (AI Routing)
- **Port**: 8003
- **Location**: `/litellm-squad-app/` (NEEDS CREATION)
- **Purpose**: Model routing, squad management, cost optimization
- **Tech Stack**: React + Vite, LiteLLM integration
- **Status**: MISSING UI ❌ (only has backend services)

## 🚀 Agno 2.0 Migration Requirements

### Breaking Changes to Address
1. **Stateless Architecture**
   - All agents must be stateless
   - Use unified `db` parameter
   - No more AgentMemory classes

2. **Unified Storage**
   ```python
   # OLD (1.x)
   from agno.storage.sqlite import SqliteStorage
   storage = SqliteStorage(mode="agent")
   
   # NEW (2.0)
   from agno.db.sqlite import SqliteDb
   db = SqliteDb(db_file="agno_v2.db")
   ```

3. **Media Handling**
   ```python
   from agno.media import Image, Audio, Video
   # Replace all ImageArtifact etc.
   ```

4. **Knowledge Management**
   ```python
   from agno.knowledge import Knowledge
   # Single unified Knowledge class
   ```

## 📋 Implementation Plan

### Phase 1: Create Missing UIs (Immediate)

#### A. Builder Agno App
```bash
# Create new React app for Builder
mkdir -p /Users/lynnmusil/sophia-intel-ai/builder-agno-app
cd /Users/lynnmusil/sophia-intel-ai/builder-agno-app
npm create vite@latest . -- --template react-ts

# Install Agno 2.0 dependencies
pip install -U agno[all]
```

#### B. LiteLLM Squad App
```bash
# Create new React app for LiteLLM
mkdir -p /Users/lynnmusil/sophia-intel-ai/litellm-squad-app
cd /Users/lynnmusil/sophia-intel-ai/litellm-squad-app
npm create vite@latest . -- --template react-ts
```

### Phase 2: Migrate to Agno 2.0

#### Database Migration
```bash
# Migrate existing DB
agno migrate-db --db-file=/Users/lynnmusil/sophia-intel-ai/agno.db
```

#### Update All Agents
```python
# Example migration for existing agents
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agno_v2.db")

# Builder Agent (stateless)
builder_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,  # Unified persistence
    enable_user_memories=True,
    instructions="Generate code with tests",
    markdown=True
)

# BI Agent (stateless)
bi_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    enable_user_memories=True,
    instructions="Analyze business data"
)
```

### Phase 3: UI Components for Each App

#### Builder Agno App Components
```typescript
// builder-agno-app/src/components/
- AgentWorkshop.tsx       // Visual agent builder
- CodeGenerationStudio.tsx // NL to code
- ResearchCenter.tsx      // Solution finder
- SwarmDesigner.tsx       // Multi-agent orchestration
- AgnoMonitor.tsx         // Real-time agent monitoring
```

#### LiteLLM Squad App Components
```typescript
// litellm-squad-app/src/components/
- ModelRouter.tsx         // Dynamic model selection
- CostAnalytics.tsx       // Cost optimization
- SquadManager.tsx        // Squad configuration
- PerformanceMonitor.tsx  // Latency tracking
- FallbackChains.tsx      // Reliability setup
```

### Phase 4: Startup Scripts

#### Master Startup Script
```bash
#!/bin/bash
# start_all_apps.sh

# Start Sophia Intel (Port 8000)
cd sophia-intel-app && npm run dev &

# Start Builder Agno (Port 8005)
cd ../builder-agno-app && npm run dev -- --port 8005 &

# Start LiteLLM Squad (Port 8003)
cd ../litellm-squad-app && npm run dev -- --port 8003 &

# Start Bridge API (Port 8004)
python app/api/builder_bridge.py &

# Start MCP Servers
./scripts/start_all_mcp.sh &

echo "All systems running:"
echo "  Sophia Intel: http://localhost:8000"
echo "  Builder Agno: http://localhost:8005"
echo "  LiteLLM Squad: http://localhost:8003"
```

## 🎨 Visual Identity for Each App

### Sophia Intel (Business)
- **Theme**: Professional Blue (#3B82F6)
- **Font**: Inter
- **Style**: Clean, executive

### Builder Agno (Technical)
- **Theme**: Purple/Cyan (#8B5CF6/#06B6D4)
- **Font**: JetBrains Mono
- **Style**: Dark, technical

### LiteLLM Squad (Performance)
- **Theme**: Green/Orange (#10B981/#F59E0B)
- **Font**: Space Grotesk
- **Style**: Data-focused, metrics

## 🔥 Critical Actions

1. **IMMEDIATELY**: Create the two missing UI apps
2. **TODAY**: Migrate all agents to Agno 2.0 stateless
3. **THIS WEEK**: Implement natural language in all three UIs
4. **ONGOING**: Keep apps separate but data unified via Agno DB

## 📊 Success Metrics

- [ ] Three separate UIs running on different ports
- [ ] All agents migrated to Agno 2.0
- [ ] Unified DB for persistence
- [ ] Natural language commands in each UI
- [ ] Background workflows for long tasks
- [ ] Multi-modal support (images/audio/video)

## 🚨 DO NOT
- Mix UI components between apps
- Use stateful agents (deprecated)
- Share ports between apps
- Forget to migrate the DB

---

**Status**: URGENT - Fix this clusterfuck immediately
**Priority**: P0 - Blocking everything else
**Owner**: Sophia Intel AI Team