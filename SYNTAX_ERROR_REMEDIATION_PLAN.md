# Sophia Intel AI - Syntax Error Remediation Plan
**Mission Critical: Fix 42 Python files with syntax errors to complete Black formatting**

## Overview
Black formatter successfully processed 879 Python files but failed on 42 files due to syntax errors. This plan provides a systematic approach to identify, fix, and prevent these issues.

## Phase 1: Error Analysis & Categorization (Priority: HIGH)

### 1.1 Create Error Inventory
```bash
# Generate detailed error report with line numbers
black --check --diff . 2>&1 | tee black_errors_detailed.log

# Extract just the failed files for focused analysis
black --check . 2>&1 | grep -E "error: cannot format" | cut -d: -f1 | sort | uniq > failed_files.txt
```

### 1.2 Categorize Error Types
Based on initial scan, errors fall into these categories:

**A. Malformed Regex Patterns**
- `code_sanitizer.py:37` - Multiple r' strings concatenated incorrectly
- Pattern: `r'\b            r'\b            r'\b`

**B. Incomplete/Corrupted Docstrings**
- `mcp_servers/artemis/*.py:9` - Malformed triple quotes
- `infrastructure/pulumi/production/lambda_labs.py:12`

**C. Missing/Incomplete Source Content**
- `dashboard.py:1226` - Missing line numbers in source
- Likely file corruption or incomplete merge

**D. Syntax Issues in String Literals**
- `tests/generators/business_data_generators.py:151` - Incomplete list/string
- Pattern: `["Backlog", "                ),` (missing closing)

**E. Incomplete Function/Class Definitions**
- Various files with incomplete async functions
- Missing colons, incomplete parameter lists

## Phase 2: Systematic Repair Strategy (Priority: HIGH)

### 2.1 Automated Detection Script
```python
# Create syntax_error_detector.py
import ast
import sys
from pathlib import Path

def check_syntax_errors(file_path):
    """Check if a Python file has syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return {
            'file': str(file_path),
            'line': e.lineno,
            'offset': e.offset,
            'message': e.msg,
            'text': e.text
        }
    except Exception as e:
        return {
            'file': str(file_path),
            'error': str(e),
            'type': 'other'
        }
```

### 2.2 Priority Repair Order

**PHASE 2A: Critical Infrastructure Files (Day 1)**
1. `dashboard.py` - Main dashboard functionality
2. `backend/core/di_container.py` - Dependency injection core
3. `backend/database/connection_pool.py` - Database connectivity
4. `app/observability/metrics.py` - System monitoring

**PHASE 2B: MCP Server Files (Day 2)**
1. `mcp_servers/artemis/__init__.py`
2. `mcp_servers/artemis/swarm_orchestrator.py`
3. `mcp_servers/artemis/agents/*.py`
4. `mcp_servers/base/*.py`

**PHASE 2C: Service & Infrastructure Files (Day 3)**
1. `services/neural-gateway/main.py`
2. `services/neural-engine/main.py`
3. `infrastructure/setup/qdrant_setup.py`
4. `backend/services/*.py`

**PHASE 2D: Scripts & Utilities (Day 4)**
1. `code_sanitizer.py` - Fix regex patterns
2. `scripts/*.py` - Various utility scripts
3. `clear_all_caches.py`
4. Test files with syntax errors

## Phase 3: Specific Fix Strategies

### 3.1 Regex Pattern Fixes
```python
# Example fix for code_sanitizer.py:37
# BROKEN:
r'\b            r'\b            r'\b            r'\b            r'\bNOTE\b(?!\s*:)'

# FIXED:
r'\bTODO\b|\bFIXME\b|\bHACK\b|\bXXX\b|\bNOTE\b(?!\s*:)'
```

### 3.2 Docstring Fixes
```python
# BROKEN:
"""

# FIXED:
"""
Module docstring describing functionality.
"""
```

### 3.3 String Literal Fixes
```python
# BROKEN:
["Backlog", "                ),

# FIXED:
["Backlog", "In Progress", "Done"]
```

### 3.4 Function Definition Fixes
```python
# BROKEN:
async def start_metrics_updater(

# FIXED:
async def start_metrics_updater(self):
    """Start the metrics updater task."""
    pass
```

## Phase 4: Automated Repair Tools

### 4.1 Custom Syntax Fixer Script
```python
# syntax_fixer.py
import re
from pathlib import Path

class SyntaxFixer:
    def __init__(self):
        self.fixes_applied = []
        
    def fix_regex_patterns(self, content, file_path):
        """Fix malformed regex patterns"""
        # Fix multiple r' concatenations
        pattern = r"r'\\b\s+r'\\b\s+r'\\b\s+r'\\b\s+r'\\b([^']+)'"
        fixed = re.sub(pattern, r"r'\b\1'", content)
        if fixed != content:
            self.fixes_applied.append(f"{file_path}: Fixed regex pattern")
        return fixed
    
    def fix_incomplete_strings(self, content, file_path):
        """Fix incomplete string literals"""
        # Fix incomplete list items
        content = re.sub(r'\["([^"]*)",\s*"\s*\),', r'["\1"]', content)
        return content
    
    def fix_docstrings(self, content, file_path):
        """Fix malformed docstrings"""
        # Fix incomplete triple quotes
        content = re.sub(r'^"""$', '"""\nModule docstring.\n"""', content, flags=re.MULTILINE)
        return content
```

### 4.2 Validation Pipeline
```bash
# Create validation script
#!/bin/bash
echo "🔍 Validating syntax fixes..."

for file in $(cat failed_files.txt); do
    echo "Checking: $file"
    python -m py_compile "$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $file - Fixed"
    else
        echo "❌ $file - Still broken"
        python -c "import ast; ast.parse(open('$file').read())" 2>&1 | head -3
    fi
done
```

## Phase 5: Implementation Steps

### 5.1 Immediate Actions
```bash
# 1. Create working branch
git checkout -b fix/syntax-errors-black-formatting

# 2. Backup current state
cp -r . ../sophia-backup-$(date +%Y%m%d)

# 3. Create error analysis
python -c "
import subprocess
import sys
from pathlib import Path

failed_files = []
result = subprocess.run(['black', '--check', '.'], 
                       capture_output=True, text=True)
for line in result.stderr.split('\n'):
    if 'cannot format' in line:
        file_path = line.split(':')[1].strip() if ':' in line else None
        if file_path:
            failed_files.append(file_path)

with open('failed_files.txt', 'w') as f:
    for file in sorted(set(failed_files)):
        f.write(file + '\n')

print(f'Found {len(set(failed_files))} files with syntax errors')
"
```

### 5.2 Systematic Fix Process
```bash
# For each file in failed_files.txt:
# 1. Manual inspection
# 2. Identify error type
# 3. Apply appropriate fix
# 4. Test with: python -m py_compile <file>
# 5. Test with: black --check <file>
# 6. Commit individual fixes

while IFS= read -r file; do
    echo "🔧 Fixing: $file"
    # Manual fix process here
    python -m py_compile "$file" && echo "✅ Syntax OK" || echo "❌ Still broken"
done < failed_files.txt
```

## Phase 6: Quality Assurance

### 6.1 Comprehensive Testing
```bash
# 1. Syntax validation
find . -name "*.py" -exec python -m py_compile {} \;

# 2. Black formatting test
black --check --diff .

# 3. Import testing
python -c "
import sys
import importlib.util
from pathlib import Path

for py_file in Path('.').rglob('*.py'):
    if 'test' in str(py_file) or '__pycache__' in str(py_file):
        continue
    
    try:
        spec = importlib.util.spec_from_file_location('temp_module', py_file)
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just validate structure
        print(f'✅ {py_file}')
    except Exception as e:
        print(f'❌ {py_file}: {e}')
"

# 4. Run existing tests
python -m pytest tests/ --tb=short
```

### 6.2 Black Formatting Validation
```bash
# Final formatting run
black .

# Verify success
if black --check . >/dev/null 2>&1; then
    echo "🎉 All files successfully formatted!"
else
    echo "❌ Some files still have issues"
    black --check .
fi
```

## Phase 7: Prevention Strategy

### 7.1 Pre-commit Hooks
```yaml
# Update .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: local
    hooks:
      - id: syntax-check
        name: Python Syntax Check
        entry: python -m py_compile
        language: system
        files: \.py$
```

### 7.2 CI/CD Integration
```yaml
# Add to GitHub Actions workflow
- name: Syntax Check
  run: |
    find . -name "*.py" -exec python -m py_compile {} \;
    
- name: Black Check
  run: |
    black --check --diff .
```

## Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2 hours | Error analysis and categorization |
| Phase 2A | 4 hours | Fix critical infrastructure files |
| Phase 2B | 4 hours | Fix MCP server files |
| Phase 2C | 3 hours | Fix service files |
| Phase 2D | 2 hours | Fix scripts and utilities |
| Phase 3-4 | 2 hours | Automated tools and validation |
| Phase 5-6 | 3 hours | Final testing and QA |
| **Total** | **20 hours** | Complete remediation |

## Success Criteria

✅ All 42 files pass `python -m py_compile`
✅ All files pass `black --check`
✅ No syntax errors in codebase
✅ All existing tests continue to pass
✅ Pre-commit hooks prevent future syntax errors

## Emergency Rollback Plan

If fixes break functionality:
```bash
# Restore from backup
rm -rf ./*
cp -r ../sophia-backup-$(date +%Y%m%d)/* .

# OR restore specific files
git checkout main -- <problematic-file>
```

This plan ensures systematic resolution of all syntax errors while maintaining code quality and preventing regressions.
