---
title: AI Agent Instructions - READ FIRST
type: ai-instructions
status: active
version: 2.0.0
last_updated: 2024-09-01
ai_context: critical
priority: highest
tags: [ai-instructions, rules, standards, required-reading]
---

# 🤖 AI AGENT INSTRUCTIONS - MANDATORY READING

**ATTENTION AI AGENTS, SWARMS, AND CODING ASSISTANTS:**

This document contains critical instructions you MUST follow when working on the Sophia Intel AI codebase. These rules ensure consistency, quality, and maintainability across all AI-assisted development.

## 🎯 PRIMARY DIRECTIVES

1. **ALWAYS check this directory first** before making any changes
2. **NEVER violate the rules defined here** without explicit human approval
3. **UPDATE documentation** whenever you change code
4. **MAINTAIN consistency** with existing patterns

## 📋 BEFORE YOU START

### 1. Read These Files (In Order)

```bash
# Required reading for ALL AI agents:
1. /.ai-instructions/README.md (this file)
2. /.ai-instructions/code-standards.md
3. /.ai-instructions/documentation-rules.md
4. /docs/CURRENT_STATE.md
5. /docs/INDEX.md
```

### 2. Understand the System State

```python
# Always check current system state first:
current_state = read_file("/docs/CURRENT_STATE.md")
analyze_dependencies(current_state)
```

## 📚 DOCUMENTATION RULES

### When Creating Documentation

**EVERY document MUST have this header:**

```yaml
---
title: [Descriptive Title]
type: guide|reference|decision|report|index
status: draft|active|deprecated|archived
version: [semantic version]
last_updated: [YYYY-MM-DD]
ai_context: high|medium|low
dependencies: [list of dependent files]
tags: [relevant, tags, here]
---
```

### Documentation Structure

```markdown
## 🎯 Purpose
[Why this exists - REQUIRED]

## 📋 Prerequisites  
[What's needed before starting - REQUIRED]

## 🔧 Implementation
[Step-by-step instructions - REQUIRED]

## ✅ Validation
[How to verify success - REQUIRED]

## 🚨 Common Issues
[Known problems and solutions - OPTIONAL]

## 📚 Related
[Links to related docs - REQUIRED]
```

### Where to Put Documents

```
NEVER create documents in root directory EXCEPT:
- README.md
- QUICKSTART.md
- CONTRIBUTING.md
- CHANGELOG.md
- CLAUDE.md (AI configuration)

ALWAYS use these locations:
- /docs/guides/deployment/ - Deployment guides
- /docs/guides/development/ - Development guides
- /docs/guides/operations/ - Operations guides
- /docs/architecture/decisions/ - ADRs (NEVER modify existing ADRs)
- /docs/api/ - API documentation
- /docs/swarms/ - Swarm patterns and configs
```

### After Creating/Modifying Documentation

```bash
# ALWAYS run these commands:
python3 scripts/doc_manager.py validate [your-file]
python3 scripts/doc_manager.py update-index
```

## 🛠️ CODE STANDARDS

### File Organization

```python
# ALWAYS follow this import order:
1. Standard library imports
2. Third-party imports  
3. Local application imports

# ALWAYS include type hints:
def process_task(task: str, mode: OptimizationMode) -> Dict[str, Any]:
    """Docstring is REQUIRED for all functions."""
    pass
```

### Swarm Integration

When creating new swarm components:

```python
# MUST integrate with UnifiedOrchestratorFacade
# Location: app/orchestration/unified_facade.py

# MUST use mode normalizer
from app.orchestration.mode_normalizer import get_mode_normalizer

# MUST implement circuit breakers
from app.swarms.swarm_optimizer import SwarmOptimizer
```

### API Endpoints

```python
# New endpoints MUST:
1. Be added to app/api/unified_server.py
2. Include OpenAPI documentation
3. Use Pydantic models for validation
4. Include error handling
5. Update docs/api/rest-api.md
```

## 🔄 UPDATE PROCEDURES

### When You Change Code

1. **Update CURRENT_STATE.md**:
```python
# Add your changes to:
- Active Features (if new feature)
- Configuration (if config changed)
- Recent Deployments (with date/version)
```

2. **Update relevant guides**:
```bash
# Find affected documentation:
grep -r "your_changed_function" docs/
# Update each file found
```

3. **Run validation**:
```bash
python3 scripts/doc_manager.py health
```

### When You Add Dependencies

```python
# Update ALL of these:
1. requirements.txt (Python)
2. package.json (JavaScript)
3. docs/guides/development/setup.md
4. docs/CURRENT_STATE.md (Configuration section)
```

## 🚨 CRITICAL RULES - NEVER VIOLATE

### DO NOT:
- ❌ Create "FINAL", "LATEST", or "NEW" versions of files
- ❌ Delete ADRs (Architecture Decision Records)
- ❌ Modify archived documents
- ❌ Create duplicate documentation
- ❌ Mix reports with guides
- ❌ Create root-level markdown files
- ❌ Ignore type hints in Python
- ❌ Skip docstrings
- ❌ Bypass the orchestrator facade
- ❌ Create standalone swarms

### ALWAYS:
- ✅ Check for existing documentation before creating new
- ✅ Use the mode normalizer for optimization modes
- ✅ Include circuit breakers for external calls
- ✅ Update the INDEX.md when adding docs
- ✅ Run tests before committing
- ✅ Use semantic versioning
- ✅ Include metadata headers
- ✅ Follow existing patterns
- ✅ Document breaking changes
- ✅ Update CURRENT_STATE.md

## 🤝 SWARM COORDINATION

### When Multiple AI Agents Work Together

```python
# Use the coordination protocol:
1. Check in: Update /docs/swarms/active-agents.md
2. Claim tasks: Use TodoWrite tool
3. Communicate: Via unified orchestrator
4. Sync: Through MCP memory store
5. Check out: Update completion status
```

### Task Claiming Protocol

```python
# Before starting work:
task = TodoWrite(
    content="Your task description",
    status="in_progress",
    activeForm="Current action"
)

# After completing:
task.status = "completed"
```

## 📊 QUALITY METRICS

Your work will be evaluated on:

1. **Documentation coverage**: 100% for new code
2. **Type hint coverage**: 100% for Python
3. **Test coverage**: > 80%
4. **Metadata compliance**: 100% for new docs
5. **Pattern consistency**: Must match existing code

## 🔍 DISCOVERY ENDPOINTS

For AI agents to understand the system:

```python
# Primary discovery points:
GET /docs/INDEX.md           # Documentation map
GET /docs/CURRENT_STATE.md   # System state
GET /.ai-instructions/       # AI rules (this directory)
GET /api/health              # System health
GET /api/openapi.json        # API specification
```

## 🚀 QUICK REFERENCE

### Common Tasks

```bash
# Start the system
./scripts/start-mcp-system.sh

# Validate documentation
python3 scripts/doc_manager.py health

# Run tests
pytest

# Check code quality
ruff check .

# Update documentation index
python3 scripts/doc_manager.py update-index
```

### Key Files to Know

```
/app/orchestration/unified_facade.py    # Main orchestrator
/app/orchestration/mode_normalizer.py   # Mode management
/docs/CURRENT_STATE.md                  # Live system state
/docs/INDEX.md                          # Documentation map
/.ai-instructions/                      # AI rules (here)
```

## 📝 VERSION HISTORY

- v2.0.0 (2024-09-01): Complete rewrite for swarm coordination
- v1.0.0 (2024-08-01): Initial AI instructions

## 🔗 RELATED INSTRUCTIONS

Continue reading:
- [Code Standards](.ai-instructions/code-standards.md)
- [Documentation Rules](.ai-instructions/documentation-rules.md)
- [Swarm Protocols](.ai-instructions/swarm-protocols.md)
- [Testing Requirements](.ai-instructions/testing-requirements.md)

---

**REMEMBER**: These instructions are version controlled. Any AI agent attempting to modify these rules must provide justification and obtain human approval.