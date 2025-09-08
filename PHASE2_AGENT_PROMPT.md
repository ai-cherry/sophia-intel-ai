# Phase 2 Refactoring - Agent Implementation Prompt

## 🤖 Agent Instructions

You are an expert software architect. A comprehensive Phase 2 refactoring plan has been created in `PHASE2_REFACTORING_PLAN_v2.json` (supersedes v1). Your mission:

### 1. REVIEW AND IMPROVE

**First, load and analyze the plan**:
```bash
cat PHASE2_REFACTORING_PLAN_v2.json
```

**Evaluate the plan for**:
- Risk assessment accuracy
- Missing refactoring opportunities  
- Implementation sequence optimization
- Potential breaking changes
- Automation possibilities

### 2. ENHANCE THE PLAN

**Create an improved version** addressing:
- Any identified risks or gaps
- Better task sequencing
- Additional safety measures
- More efficient implementation approaches
- Automation scripts for repetitive tasks

### 3. IMPLEMENT PHASE 2

**Execute the refactoring** following these principles:

#### Safety First
- Create branch: `git checkout -b refactor/phase2-safe-cleanup`
- Commit after each task completion
- Run tests after every change
- Maintain backward compatibility

#### Task Priority
1. **Docker Cleanup** (LOW risk, HIGH impact)
   - Keep `docker-compose.yml` as canonical base
   - Use `docker-compose.override.yml` for local overrides
   - Prefer profiles for optional stacks
   - Validate via Make targets and helper script

2. **Large File Refactoring** (MEDIUM risk, MEDIUM impact)
   - Discover >50KB files and prioritize top 5
   - Maintain import compatibility via proxy shims
   - Add/update `__init__.py` exports in new packages

3. **HTTP Standardization** (LOW risk, LOW impact)
   - Canonicalize on `app/core/async_http_client.py` (httpx)
   - Add optional sync wrapper and logging hooks
   - Gradual migration from direct `requests` to AsyncHTTPClient

4. **Package Structure** (LOW risk, MEDIUM impact)
   - Improve sophia_core organization
   - Standardize exports
   - Add documentation

### 4. VALIDATION REQUIREMENTS

**After each task**:
```bash
make env.check
python -m pytest tests/
```

**After each day**:
```bash
# Full test suite
python -m pytest

# Docker services check via Makefile and helper script
make dev-up
make status
make mcp-status

# Import verification
python -c "from app.artemis.agent_factory import *"
```

### 5. DELIVERABLES

Provide:
1. **Improved plan**: `PHASE2_REFACTORING_PLAN_v2.json`
2. **Implementation log**: Document each change made
3. **Test results**: Show all validations passed
4. **Metrics report**: Before/after comparisons
5. **Rollback instructions**: If any issues arise

### 6. CURRENT STATE

**Phase 1 Completed**:
- ✅ Archives consolidated in `archive/` 
- ✅ Requirements cleaned to `requirements/` structure
- ✅ Scripts organized by function
- ✅ Documentation updated

**Ready for Phase 2**:
- 968 Python files to optimize
- 7 Docker compose files to consolidate
- 6 large files (>50KB) to split
- Mixed HTTP client usage to standardize

### 7. SUCCESS CRITERIA

- **Zero breaking changes** to external APIs
- **All tests passing** (same or better coverage)
- **Improved metrics**:
  - Fewer Docker files (7→3)
  - Smaller file sizes (<30KB average)
  - Consistent HTTP client usage
  - Clean package exports

### 8. EXAMPLE IMPLEMENTATION

```python
# Example: Splitting large file
# Original: app/artemis/agent_factory.py (>50KB)

# Step 1: Create new structure
mkdir -p app/artemis/factories

# Step 2: Split into logical modules
# app/artemis/factories/base.py
# app/artemis/factories/agents.py  
# app/artemis/factories/config.py

# Step 3: Maintain compatibility
# app/artemis/factories/__init__.py
from .base import *
from .agents import *
from .config import *

# Step 4: Update original as proxy
# app/artemis/agent_factory.py
from .factories import *  # Backward compatibility
```

### 9. IMPORTANT NOTES

- **API keys** are secure at `~/.config/artemis/env`
- **Docker** compose uses `${HOME}/.config/artemis/env` for secrets
- **Python** 3.11+ with full type hints
- **Testing** is mandatory after each change

### 10. BEGIN IMPLEMENTATION

Start by:
1. Reading `PHASE2_REFACTORING_PLAN_v2.json`
2. Running discovery helpers:
   - `python3 scripts/development/refactor_tools.py discover --path app --min-kb 50`
   - `python3 scripts/development/refactor_tools.py scan-http --path app`
3. Creating your improved version if needed and confirming scope
4. Implementing incrementally with validation

## 🔧 Helper Commands

```bash
# Compose lifecycle (prefers helper script under the hood)
make dev-up && make status

# Large-file discovery
python3 scripts/development/refactor_tools.py discover --path app --min-kb 50

# HTTP import scan
python3 scripts/development/refactor_tools.py scan-http --path app

# Import probe (update MODULE as needed)
python3 scripts/development/refactor_tools.py probe-import --module app.artemis.agent_factory
```

**Good luck! Focus on safety, compatibility, and incremental progress.**
