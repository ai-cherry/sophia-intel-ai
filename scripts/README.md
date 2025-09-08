# Scripts Directory Organization

**Reorganized**: September 8, 2024  
**Purpose**: Organized utility scripts by function for better maintainability

## 📁 Directory Structure

```
scripts/
├── README.md (this file)
├── testing/           # Test and validation scripts
├── monitoring/        # Health checks, monitoring, benchmarks
├── deployment/        # Setup, deployment, installation scripts
├── development/       # Development utilities, validation tools
├── maintenance/       # Cleanup, backup, migration, fix scripts
└── [root scripts]     # Core scripts (sophia.py, unified_*, etc.)
```

## 🔧 Core Scripts (Root Level)

**Primary Interfaces**:
- `sophia.py` - Main Sophia agent CLI
- `sophia_cli.py` - Swarm and memory CLI wrapper
- `unified_orchestrator.py` - Unified AI orchestrator
- `unified_ai_agents.py` - Unified AI agents interface
- `agents_env_check.py` - Environment validation

**Specialized Scripts**:
- `quick-grok-test.sh` - One-off Grok integration test
- `multi-agent-docker-env.sh` - Docker environment manager

## 🧪 testing/ Directory

**Test Scripts**:
- Integration tests (`test_*_integration.py`)
- Swarm connectivity tests
- Provider API tests (OpenRouter, Together, etc.)
- Model validation tests
- RAG system tests

**Usage**: `python3 scripts/testing/test_swarm_connectivity.py`

## 📊 monitoring/ Directory

**Health & Monitoring**:
- `mcp_health_monitor.py` - MCP service health monitoring
- `llm_api_health.py` - LLM provider health checks
- `benchmark_agno_embeddings.py` - Performance benchmarks
- `monitor_artemis_swarm.py` - Swarm monitoring
- Various health check scripts

**Usage**: `python3 scripts/monitoring/mcp_health_monitor.py`

## 🚀 deployment/ Directory

**Setup & Deployment**:
- `setup_complete_portkey.py` - Portkey configuration
- `deploy_artemis_simple.py` - Artemis deployment
- Environment setup scripts
- Infrastructure automation
- Service startup scripts

**Usage**: `bash scripts/deployment/setup_artemis_env.sh`

## 🛠️ development/ Directory

**Development Tools**:
- Validation scripts (`validate_*.py`)
- Code optimization tools
- Development environment helpers
- Experimental feature validators
- Startup validation tools

**Usage**: `python3 scripts/development/validate_memory_integration.py`

## 🧹 maintenance/ Directory

**Maintenance & Fixes**:
- Cleanup scripts (`cleanup_*.sh`)
- Migration tools (`*_migration.py`)
- Bug fix scripts (`fix_*.py`)
- Backup utilities
- System maintenance tools

**Usage**: `bash scripts/maintenance/cleanup_artemis_daily.sh`

## 🔍 Finding Scripts

### By Function
```bash
# Find all test scripts
ls scripts/testing/

# Find monitoring tools
ls scripts/monitoring/

# Find deployment scripts
ls scripts/deployment/
```

### By Pattern
```bash
# Find all Python scripts
find scripts/ -name "*.py"

# Find all shell scripts
find scripts/ -name "*.sh"

# Search by keyword
grep -r "portkey" scripts/
```

## 📋 Script Index

### High-Priority Scripts
1. **`agents_env_check.py`** - Always run first to validate environment
2. **`sophia.py`** - Primary agent interface
3. **`unified_orchestrator.py`** - Core orchestration system
4. **`quick-grok-test.sh`** - Quick Grok validation

### Development Workflow
1. **Environment**: `agents_env_check.py`
2. **Testing**: `scripts/testing/test_swarm_connectivity.py`
3. **Deployment**: `scripts/deployment/setup_complete_portkey.py`
4. **Monitoring**: `scripts/monitoring/mcp_health_monitor.py`

## 🔄 Migration Notes

**Moved Scripts** (2024-09-08):
- All `test_*.py` → `testing/`
- All `*monitor*.py`, `*health*.py`, `*benchmark*.py` → `monitoring/`
- All `*deploy*.py`, `*setup*.py` → `deployment/`
- All `*validate*.py` → `development/`
- All `*backup*.py`, `*clean*.py`, `*fix*.py`, `*migration*.py` → `maintenance/`

**Backward Compatibility**:
- Core scripts remain at root level
- Directory structure is additive, not breaking
- All import paths unchanged for core functionality

## 🎯 Usage Examples

### Quick Development Check
```bash
# Full environment validation
python3 scripts/agents_env_check.py

# Test connectivity
python3 scripts/testing/test_swarm_connectivity.py

# Monitor services
python3 scripts/monitoring/mcp_health_monitor.py
```

### Deployment Workflow
```bash
# Setup environment
bash scripts/deployment/setup_artemis_env.sh

# Validate setup
python3 scripts/development/validate_memory_integration.py

# Deploy services
python3 scripts/deployment/deploy_artemis_simple.py
```

### Maintenance Tasks
```bash
# Daily cleanup
bash scripts/maintenance/cleanup_artemis_daily.sh

# Fix broken imports
python3 scripts/maintenance/fix_broken_imports.py

# Database migration
python3 scripts/maintenance/weaviate_migration.py
```

---

**This organization improves maintainability while preserving all existing functionality.**