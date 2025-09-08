# AI Agent Environment Audit Report
**Date**: September 7, 2025  
**Scope**: CLI Setup Analysis for Grok, Claude Coder, Codex + MCP Integration Issues

## 🚨 CRITICAL FINDINGS (Original)

### 1. Virtual Environment Proliferation (HIGH PRIORITY)
**Issue**: Multiple scripts create/manage separate virtual environments, violating single-environment principle.

**Problematic Files**:
- `sophia.sh` - Manages 3 separate venvs: `venv-prod`, `venv-dev`, `venv-agent`
- `deploy.sh` - Creates dedicated `venv/` for deployment
- `start_mcp_memory.sh` - Activates `/workspace/.venv`
- `scripts/deploy.sh` - Creates project-specific virtual environment

**Evidence**:
```bash
# sophia.sh lines 45-52
for env in prod dev agent; do
    check_item "venv-$env exists" "[ -d '$SOPHIA_HOME/venv-$env' ]"
done

# deploy.sh lines 89-94  
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
```

**Risk**: AI agents will create conflicting environments, repository bloat, dependency conflicts.

### 2. Roo/Cline MCP Integration Contamination (HIGH PRIORITY)
**Issue**: Found dedicated MCP bridges for Roo and Cline that should be removed.

**File**: `mcp-bridge/central_registry_integration.py`
**Lines**: 156-215

**Evidence**:
```python
async def _register_roo_cursor_servers(self, ide_config: Dict[str, Any]):
    """Register Roo/Cursor MCP servers"""
    # 30+ lines of Roo-specific integration

async def _register_cline_servers(self, ide_config: Dict[str, Any]):
    """Register Cline MCP servers"""  
    # 30+ lines of Cline-specific integration
```

**Risk**: Creates parallel MCP infrastructure, confuses agent routing, duplicates resources.

### 3. AI Agent CLI Setup Analysis

#### A. **Grok Integration**
**Status**: ❌ NO DEDICATED CLI SETUP
**Current State**: 
- Model configurations exist (45+ references)
- API integration via OpenRouter/Portkey
- No direct CLI interface

**Found Configurations**:
```python
# backup_configs/portkey_configs/elite_portkey_config.py
GROK_4 = "x-ai/grok-4"  
GROK_CODE_FAST_1 = "x-ai/grok-code-fast-1"

# app/models/openrouter_latest.py
"x-ai/grok-code-fast-1": {"tier": ModelTier.BALANCED, "context": 128000}
"x-ai/grok-3": {"tier": ModelTier.PREMIUM, "context": 128000}
```

**Issue**: Grok is configured as API model only, no CLI agent setup.

#### B. **Claude Coder Integration**  
**Status**: ❌ NO DEDICATED CLI SETUP
**Current State**:
- Backend API references (`chat_service_no_mock.py`)
- Feature flag system exists
- No CLI agent interface

**Found Code**:
```python
# backend/services/chat_service_no_mock.py
priority_models = ['gpt-4', 'claude-3-opus', 'grok-beta']
'claude-3-sonnet': 'chat_claude'

# backend/services/feature_flags.py  
'chat_claude': bool(os.getenv('ANTHROPIC_API_KEY'))
```

**Issue**: Claude treated as chat API only, not as coding agent.

#### C. **Codex Integration**
**Status**: ❌ NO DEDICATED CLI SETUP  
**Current State**:
- References in model lists and configurations
- No dedicated agent interface
- Appears to be legacy/placeholder

**Found References**:
```python
# Multiple files reference "codex" but no actual implementation
# Appears to be GitHub Copilot integration assumption
```

**Issue**: No actual Codex agent implementation found.

### 4. Requirements File Proliferation (MEDIUM PRIORITY)
**Issue**: 15+ separate requirements files create dependency chaos.

**Found Files**:
- `requirements.txt` (main)
- `requirements-minimal.txt` 
- `requirements-dashboard.txt`
- `requirements-asip.txt`
- `requirements-dev.txt`
- `requirements-security.txt`
- `requirements_token_optimizer.txt`
- `backend/requirements.txt`
- Multiple service-specific requirements

**Risk**: Dependency conflicts, version mismatches, installation complexity.

### 5. Docker Compose Duplication (MEDIUM PRIORITY)
**Issue**: 6+ docker-compose files with unclear relationships.

**Files Found**:
- `docker-compose.yml`
- `docker-compose.enhanced.yml`
- `docker-compose.artemis.yml`  
- `docker-compose.sophia-intel-ai.yml`
- `deployment/cloud/docker-compose.gong.yml`

**Risk**: Configuration drift, deployment confusion, maintenance overhead.

## 🔧 REMEDIATION PLAN (Original)

### Phase 1: Environment Consolidation (IMMEDIATE)
1. **Remove Virtual Environment Scripts**:
   ```bash
   # Update sophia.sh to remove venv management
   # Modify deploy.sh to use system Python
   # Fix start_mcp_memory.sh to not activate venv
   ```

2. **Delete Roo/Cline MCP Bridges**:
   ```bash
   # Remove methods from mcp-bridge/central_registry_integration.py:
   # - _register_roo_cursor_servers() 
   # - _register_cline_servers()
   # - All related configuration handling
   ```

### Phase 2: AI Agent CLI Standardization
1. **Create Unified Agent Interface**:
   ```bash
   # New file: scripts/ai_agents_unified.py
   # Single entry point for Grok, Claude Coder, Codex
   # All agents use same environment, MCP servers, credentials
   ```

2. **Standardize Model Access**:
   ```python
   # Consolidate model configurations
   # Single routing system for all agents
   # Shared credential management
   ```

### Phase 3: Dependency Consolidation  
1. **Merge Requirements Files**:
   ```bash
   # Keep: requirements.txt (main)
   # Move: requirements-dev.txt → dev section in main
   # Delete: All other requirements-*.txt files
   ```

2. **Docker Compose Cleanup**:
   ```bash
   # Keep: docker-compose.yml (canonical)
   # Keep: docker-compose.enhanced.yml (development) 
   # Archive: All other docker-compose-*.yml files
   ```

## 📋 SPECIFIC ACTIONS REQUIRED (Original)

### 1. Remove Virtual Environment References
**Files to Modify**:
- `sophia.sh` - Remove venv-* management
- `deploy.sh` - Use system Python
- `start_mcp_memory.sh` - Remove venv activation  
- `scripts/mcp_bootstrap.sh` - Ensure no venv creation

### 2. Delete Roo/Cline Integrations
**Files to Modify**:
- `mcp-bridge/central_registry_integration.py` - Remove 60+ lines of Roo/Cline code
- Remove any Roo/Cline specific configuration files
- Update documentation to remove Roo/Cline references

### 3. Create Unified Agent CLI
**New Files Needed**:
- `scripts/grok_agent.py` - Direct Grok CLI interface
- `scripts/claude_coder_agent.py` - Claude as coding agent
- `scripts/codex_agent.py` - Codex integration (if needed)
- `scripts/unified_ai_agents.py` - Single entry point

### 4. Consolidate Model Configurations
**Files to Update**:
- Merge all model configs into single canonical file
- Remove duplicate/conflicting model definitions
- Create single routing system

## ✅ Post-Remediation Status (September 2025)

- Single shared environment for all agents (system Python; no in-repo venvs)
- Unified AI Agent CLI: `scripts/unified_ai_agents.py` (+ `grok_agent.py`, `claude_coder_agent.py`, `codex_agent.py`)
- Roo/Cline/Cursor integrations removed from active code paths; MCP standardized
- Canonical requirements: `requirements.txt` (infra-scoped `pulumi/*/requirements.txt` retained)
- Docker Compose reduced to two canonical files: `docker-compose.yml`, `docker-compose.enhanced.yml`
- Single startup entrypoint: `./start.sh`

### Usage

```bash
./start.sh
python3 scripts/unified_ai_agents.py --whoami
python3 scripts/grok_agent.py --mode code --task "hello"
```

### After Remediation:
- ✅ Single shared environment for all agents
- ✅ No Roo/Cline specific integrations
- ✅ Unified CLI interface for Grok, Claude Coder, Codex
- ✅ Single requirements.txt (with optional dev section)
- ✅ 2 docker-compose files maximum (main + dev)

## 🚀 IMPLEMENTATION ORDER

1. **Stop Environment Creation** (scripts/mcp_bootstrap.sh already implemented ✅)
2. **Remove Roo/Cline MCP bridges** - Delete integration code
3. **Eliminate virtual environment scripts** - Modify existing scripts  
4. **Create unified agent CLI** - New standardized interface
5. **Consolidate requirements** - Merge into single file
6. **Archive duplicate configs** - Clean up docker-compose files

## 📊 RISK ASSESSMENT

**High Risk** (Fix Immediately):
- Virtual environment proliferation
- Roo/Cline MCP contamination
- Missing agent CLI standards

**Medium Risk** (Fix Next):  
- Requirements file chaos
- Docker compose duplication
- Model configuration conflicts

**Low Risk** (Fix Later):
- Documentation cleanup
- Legacy code removal
- Test environment standardization

---

**Conclusion**: The repository has significant environment management issues that will cause AI agent conflicts. Priority should be eliminating virtual environment creation, removing Roo/Cline integrations, and creating standardized CLI interfaces for the three target agents (Grok, Claude Coder, Codex).
