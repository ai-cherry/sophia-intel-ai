# SOPHIA Repository Consolidation Plan
**Generated:** 2025-08-10 (Step 0-A: Full Repository Re-Audit)  
**MEGA PROMPT Compliance:** Infrastructure-First Approach

## 🎯 Consolidation Objectives
- ✅ **Zero duplication** policy (target: <2% by lines)
- ✅ **Zero conflicts** between modules  
- ✅ **Single canonical interface** per concern
- ✅ **Refactor-in-place** (no parallel modules)

## 📊 Current State Analysis
> *Will be populated by repo_audit.py results*

### Repository Statistics
- **Python Files:** TBD
- **Total Lines:** TBD  
- **Config Files:** TBD
- **Duplication %:** TBD

### Issues Identified
- **Config Mismatches:** TBD
- **Circular Imports:** TBD
- **Unused Imports:** TBD (~50 from ruff check)
- **Dead Code:** TBD

## 🔧 Duplicates to Merge/Delete
> *To be filled based on audit results*

### Embedding/Memory System
- **Current:** [`mcp_servers/memory_service.py`](mcp_servers/memory_service.py) (hash fallback)
- **Target:** Upgrade to real embeddings with provider switching
- **Action:** Enhance existing, remove hash fallback post-migration

### Configuration System  
- **Issue:** EMBEDDING_DIMENSION mismatch (384 vs 1536)
- **Current:** [`config/sophia.yaml`](config/sophia.yaml) + [`config/config.py`](config/config.py) + [`.env.example`](.env.example)
- **Action:** Consolidate dimension value, standardize config keys

### Agent Framework
- **Current:** [`agents/base_agent.py`](agents/base_agent.py) + [`agents/coding_agent.py`](agents/coding_agent.py) 
- **Status:** ✅ Well-structured, keep as canonical
- **Action:** Clean unused imports, add guardrails integration

## 📋 Canonical Modules Per Concern

### 🧠 Memory & Embeddings
- **Embeddings:** `services/embeddings.py` (NEW - provider switching)
- **Memory Client:** `services/memory_client.py` (NEW - enhanced Qdrant)  
- **Indexer:** `tools/index_repo.py` (NEW - repo indexing)
- **MCP Server:** [`mcp_servers/unified_mcp_server.py`](mcp_servers/unified_mcp_server.py) (ENHANCE)

### 🤖 Agent System
- **Base Framework:** [`agents/base_agent.py`](agents/base_agent.py) (KEEP)
- **Coding Agent:** [`agents/coding_agent.py`](agents/coding_agent.py) (ENHANCE)
- **CEO Assistant:** `agents/ceo_assistant_agent.py` (NEW)
- **CEO Coach:** `agents/ceo_coach_agent.py` (NEW)
- **Sales Coach:** `agents/sales_coach_agent.py` (NEW)
- **Client Health:** `agents/client_health_agent.py` (NEW)

### 🔧 Core Services  
- **Portkey Client:** [`services/portkey_client.py`](services/portkey_client.py) (KEEP)
- **Orchestrator:** [`services/orchestrator.py`](services/orchestrator.py) (ENHANCE)
- **Guardrails:** `services/guardrails.py` (NEW - JSON validation)

### 🔗 Integrations
- **Notion Client:** `integrations/notion_client.py` (NEW)
- **Asana Client:** `integrations/asana_client.py` (NEW)
- **Linear Client:** `integrations/linear_client.py` (NEW) 
- **Slack Client:** `integrations/slack_client.py` (NEW)
- **Project Normalizer:** `services/project_normalizer.py` (NEW)

### 📊 Dashboards  
- **Project Visibility API:** `dashboards/project_visibility.py` (NEW)
- **UI Components:** `ui/project-dashboard/` (NEW)

### ⚙️ Configuration
- **Settings:** [`config/config.py`](config/config.py) (ENHANCE - resolve mismatches)
- **YAML Config:** [`config/sophia.yaml`](config/sophia.yaml) (CONSOLIDATE)
- **Env Template:** [`.env.example`](.env.example) (SYNC)

## 🚀 Refactor-in-Place Steps

### Phase 1: Immediate Cleanup (PR #1)
1. **Fix unused imports** (ruff --fix)
2. **Standardize formatting** (black .)
3. **Resolve config mismatches** (EMBEDDING_DIMENSION alignment)
4. **Remove dead code** (junk.py, unused variables)

### Phase 2: Memory System Enhancement (PR #2-3)  
1. **Create `services/embeddings.py`** with provider switching
2. **Enhance `mcp_servers/memory_service.py`** to use real embeddings
3. **Create `tools/index_repo.py`** for repository indexing
4. **Test end-to-end** memory storage and retrieval

### Phase 3: Agent & Integration Framework (PR #4-8)
1. **Add `services/guardrails.py`** for output validation
2. **Enhance `agents/coding_agent.py`** with guardrails
3. **Create integration clients** (Notion, Asana, Linear, Slack)
4. **Build project normalizer** for unified schema
5. **Create coaching agents** (4 agents)

### Phase 4: Dashboard & UI (PR #9-10)
1. **Create project visibility API**
2. **Build minimal dashboard UI**
3. **Add agent UI enhancements** (memory panel, patch preview)

## ✅ Quality Gates

### Step 0-A Gate (Current)
- [ ] Duplication < 2% by lines
- [ ] Zero circular imports  
- [ ] Config consistency validated
- [ ] Lint baseline green

### Step 2 Gate (Memory Enhancement)  
- [ ] Real embeddings working with fallbacks
- [ ] Repository indexer functional
- [ ] MCP server e2e smoke test passes

### Final Gate (Step 9)
- [ ] All tests green  
- [ ] jscpd duplication report < 2%
- [ ] Zero orphaned/parallel modules
- [ ] Config keys single-source

## 🎯 Success Metrics

### Before (Current State)
- **Duplication:** TBD%
- **Config Issues:** TBD
- **Lint Violations:** ~50 (ruff)
- **Circular Imports:** TBD

### After (Target State)  
- **Duplication:** <2%
- **Config Issues:** 0
- **Lint Violations:** 0  
- **Circular Imports:** 0
- **Test Coverage:** >80%

## 📦 PR Sequence Strategy

Following MEGA PROMPT size budgets: **≤25 files, ≤200 lines per PR**

1. **chore(audit): repo audit & consolidation plan** ← *Current*
2. **chore(cleanup): fix imports, formatting, config alignment**  
3. **feat(embeddings): provider switching + real embeddings**
4. **feat(indexer): repository indexing tool** 
5. **feat(guardrails): json validation + agent enhancement**
6. **feat(integrations): notion/asana/linear/slack clients**
7. **feat(normalizer): unified project schema**
8. **feat(agents): 4 coaching agents implementation**
9. **feat(dashboard): project visibility api + ui**
10. **test(comprehensive): full test suite + cleanliness proof**

---

**Next Action:** Review audit results → Create PR #1 with immediate cleanup fixes