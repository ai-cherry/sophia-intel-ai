# Sophia Intel AI - Updated Black Formatter Remediation Plan
**Current Status: 33 files remaining with syntax errors preventing Black formatting**

## Current Situation Assessment

### Progress Made
✅ **Black Formatter Run**: 245 files successfully reformatted, 634 files unchanged  
✅ **Syntax Error Fix**: Fixed `mcp_servers/artemis/__init__.py` (incomplete try-except block)  
✅ **Error Reduction**: Reduced from 34 to 33 files with parsing errors  
✅ **Tools Created**: `syntax_error_detector.py` and initial remediation plan  

### Current Status
❌ **33 files still cannot be formatted** by Black due to syntax errors  
❌ **Error Types**: Incomplete docstrings, malformed functions, incomplete code blocks  
❌ **Critical Files Affected**: Backend services, MCP servers, infrastructure scripts  

## Error Pattern Analysis

Based on Black error messages, the remaining 33 files fall into these categories:

### Category A: Incomplete Docstrings (High Priority - 8 files)
```
mcp_servers/artemis/agents/coder_agent.py:9:0: """
mcp_servers/artemis/agents/evolver_agent.py:9:0: """
mcp_servers/artemis/agents/planner_agent.py:9:0: """
mcp_servers/artemis/swarm_orchestrator.py:9:0: """
infrastructure/pulumi/production/lambda_labs.py:12:0: """
scripts/check_security_reports.py:10:0: """
scripts/generate_security_summary.py:10:0: """
```
**Fix**: Add proper docstring content or remove incomplete triple quotes

### Category B: Incomplete Function Definitions (High Priority - 6 files)
```
backend/orchestration/workflow_monitor.py:133:4: async def start_metrics_updater(
backend/services/service_discovery.py:63:4: async def register_service(
backend/rag/query.py:41:12: results = [
mcp_servers/base/prometheus_monitoring.py:35:8: def labels(self, **kwargs):
```
**Fix**: Complete function signatures and implementations

### Category C: Incomplete Code Blocks (Medium Priority - 10 files)
```
backend/database/connection_pool.py:275:8: if self.postgres_pool:
pipelines/neon_qdrant_analytics.py:35:8: def get_collections(self):
mcp_servers/hub_gateway.py:48:4: server_health[server['name']] = {
clear_all_caches.py:345:8: return total_size
```
**Fix**: Complete conditional blocks, function bodies, dictionary assignments

### Category D: Script/Utility Files (Lower Priority - 9 files)
```
scripts/final_cleanup_optimization.py:27:4: print(f"  📊 Python files: {len(python_files)}")
scripts/update_claude_to_opus41.py:120:4: return content
scripts/validate_mcp_servers.py:195:12: else:
scripts/syntax_validator.py:300:12: except Exception as e:
scripts/monitoring/security_monitoring_gates.py:344:8: end_time = time.time()
scripts/index_repository.py:357:8: client.create_collection(
scripts/startup-validator.py:695:8: return info
scripts/performance_dev_automation.py:445:4: cli()
```
**Fix**: Complete incomplete statements and exception handling

## Immediate Action Plan

### Phase 1: Critical Infrastructure Fixes (Priority 1 - 2 hours)

1. **Backend Services** (Must fix first - breaks core functionality)
   ```bash
   # Fix in order:
   backend/orchestration/workflow_monitor.py
   backend/services/service_discovery.py  
   backend/rag/query.py
   backend/database/connection_pool.py
   ```

2. **MCP Server Core** (Essential for MCP functionality)
   ```bash
   # Fix in order:
   mcp_servers/artemis/swarm_orchestrator.py
   mcp_servers/artemis/agents/coder_agent.py
   mcp_servers/base/prometheus_monitoring.py
   mcp_servers/hub_gateway.py
   ```

### Phase 2: Agent System Fixes (Priority 2 - 1 hour)

3. **Artemis Agent Files**
   ```bash
   mcp_servers/artemis/agents/evolver_agent.py
   mcp_servers/artemis/agents/planner_agent.py
   mcp_servers/base/ai_service_manager.py
   mcp_servers/base/batch_processor.py
   ```

### Phase 3: Infrastructure & Utilities (Priority 3 - 1 hour)

4. **Infrastructure Files**
   ```bash
   infrastructure/pulumi/production/lambda_labs.py
   infrastructure/setup/qdrant_setup.py
   pipelines/neon_qdrant_analytics.py
   ```

5. **Service Files**
   ```bash
   services/neural-gateway/main.py
   services/neural-engine/main.py
   services/events-jobs/outbox.py
   services/performance-kit/single_flight.py
   services/performance-kit/multi_tier_cache.py
   ```

### Phase 4: Scripts & Monitoring (Priority 4 - 1 hour)

6. **Critical Scripts**
   ```bash
   clear_all_caches.py
   app/observability/metrics.py
   backend/services/enterprise_security_service.py
   ```

7. **Utility Scripts** (Can be done last)
   ```bash
   scripts/final_cleanup_optimization.py
   scripts/generate_security_summary.py
   scripts/check_security_reports.py
   scripts/update_claude_to_opus41.py
   scripts/validate_mcp_servers.py
   scripts/syntax_validator.py
   scripts/monitoring/security_monitoring_gates.py
   scripts/index_repository.py
   scripts/startup-validator.py
   scripts/performance_dev_automation.py
   ```

## Systematic Fix Strategy

### Step 1: Create Failed Files List
```bash
black --check . 2>&1 | grep "error: cannot format" | cut -d: -f1 | sed 's/error: cannot format //' > failed_files_current.txt
```

### Step 2: Fix Files by Category

For each file, follow this process:

1. **Examine the specific line** mentioned in Black error
2. **Identify the syntax issue** (incomplete block, missing colon, etc.)
3. **Apply minimal fix** to make it syntactically valid
4. **Test with**: `python -m py_compile <file>`
5. **Test with**: `black --check <file>`
6. **Commit individual fix** if successful

### Step 3: Common Fix Patterns

#### Incomplete Docstrings
```python
# BROKEN:
"""

# FIXED:
"""
Module/function description.
"""
```

#### Incomplete Function Definitions
```python
# BROKEN:
async def start_metrics_updater(

# FIXED:
async def start_metrics_updater(self):
    """Start the metrics updater."""
    pass
```

#### Incomplete Code Blocks
```python
# BROKEN:
if self.postgres_pool:

# FIXED:
if self.postgres_pool:
    self.postgres_pool.close()
```

#### Incomplete Exception Handling
```python
# BROKEN:
except Exception as e:

# FIXED:
except Exception as e:
    logger.error(f"Error: {e}")
```

## Implementation Commands

### Quick Fix Script
```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def fix_file(file_path):
    """Quick fix for common syntax errors"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix incomplete docstrings
        content = content.replace('"""\n\n', '"""\nModule docstring.\n"""\n\n')
        content = content.replace('"""\n', '"""\nDocstring.\n"""\n', 1) if content.count('"""') == 1 else content
        
        # Fix incomplete try-except
        content = content.replace('except ImportError:\n\n', 'except ImportError:\n    pass\n\n')
        content = content.replace('except Exception as e:\n\n', 'except Exception as e:\n    pass\n\n')
        
        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

# Read failed files and fix them
with open('failed_files_current.txt', 'r') as f:
    failed_files = [line.strip() for line in f if line.strip()]

for file_path in failed_files:
    if Path(file_path).exists():
        fix_file(file_path)
```

### Validation Pipeline
```bash
#!/bin/bash
echo "🔍 Validating syntax fixes..."

total_files=0
fixed_files=0

while read -r file; do
    if [[ -f "$file" ]]; then
        total_files=$((total_files + 1))
        echo "Checking: $file"
        
        # Test compilation
        if python3 -m py_compile "$file" 2>/dev/null; then
            # Test Black formatting  
            if black --check "$file" >/dev/null 2>&1; then
                echo "✅ $file - Fully fixed"
                fixed_files=$((fixed_files + 1))
            else
                echo "⚠️  $file - Compiles but Black issues remain"
            fi
        else
            echo "❌ $file - Still has syntax errors"
            python3 -c "import ast; ast.parse(open('$file').read())" 2>&1 | head -2
        fi
    fi
done < failed_files_current.txt

echo ""
echo "📊 SUMMARY:"
echo "   Total files checked: $total_files"
echo "   Fully fixed: $fixed_files"
echo "   Remaining issues: $((total_files - fixed_files))"
```

## Success Metrics

### Completion Criteria
- [ ] All 33 files pass `python -m py_compile`
- [ ] All 33 files pass `black --check`
- [ ] `black --check .` shows 0 files that cannot be formatted
- [ ] No syntax errors in the entire codebase
- [ ] All existing functionality still works

### Timeline
- **Phase 1** (Critical): 2 hours
- **Phase 2** (Agents): 1 hour  
- **Phase 3** (Infrastructure): 1 hour
- **Phase 4** (Scripts): 1 hour
- **Testing & Validation**: 30 minutes
- **Total Estimated Time**: 5.5 hours

### Rollback Strategy
```bash
# If fixes break functionality:
git stash  # Save current changes
git checkout HEAD~1 -- <problematic-file>  # Restore specific files
# OR
git reset --hard HEAD~1  # Full rollback if needed
```

## Next Immediate Steps

1. **Create failed files list**: `black --check . 2>&1 | grep "error: cannot format" | cut -d: -f1 | sed 's/error: cannot format //' > failed_files_current.txt`

2. **Start with highest priority file**: `backend/orchestration/workflow_monitor.py`

3. **Fix, test, commit each file individually**

4. **Track progress**: Update this document as files are fixed

5. **Final validation**: Run complete Black formatting on entire codebase

This updated plan provides a systematic approach to resolve all remaining syntax errors and complete the Black formatting process for the entire Sophia Intel AI codebase.
