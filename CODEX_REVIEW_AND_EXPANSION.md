# 🎯 Codex: Review & Expansion Request

## Implementation Quality Assessment

### ✅ Excellent Work Done

Your scout implementation is solid with smart architectural choices:

1. **Fire-and-forget prefetch** - Non-blocking design prevents scout delays
2. **Graceful fallbacks** - MCP memory when Weaviate unavailable  
3. **Clean integration** - Minimal changes to existing code
4. **Safe overlay injection** - Try/except ensures prompts never break

### 🔧 Improvements Needed

#### 1. **Prefetch Module Issues**

**Current**: `app/swarms/scout/prefetch.py` has synchronous `client.repo_index()` and `client.fs_read()`
**Problem**: These should be async for true non-blocking behavior
**Fix**:
```python
# Make these async
listing = await client.repo_index(...)  
content = await client.fs_read(...)
```

#### 2. **Readiness Check Enhancement**

**Current**: Basic dictionary print
**Improvement**: Structured output with actionable feedback
```python
# scripts/scout_readiness_check.py
import json
import sys

def check_readiness():
    # ... existing checks ...
    
    # Add LLM checks
    status["llm_analyst"] = bool(os.getenv("LLM_ANALYST_PROVIDER"))
    status["llm_strategist"] = bool(os.getenv("LLM_STRATEGIST_PROVIDER"))
    status["llm_validator"] = bool(os.getenv("LLM_VALIDATOR_PROVIDER"))
    
    # Structured output
    ready = all([
        status["mcp_stdio"],
        status["portkey"],
        any([status["weaviate"], status["redis"]])  # Either vector store
    ])
    
    result = {
        "ready": ready,
        "checks": status,
        "missing": [k for k, v in status.items() if not v],
        "warnings": []
    }
    
    if not status["weaviate"]:
        result["warnings"].append("Weaviate unavailable - using fallback memory")
    
    print(json.dumps(result, indent=2))
    return 0 if ready else 1

if __name__ == "__main__":
    sys.exit(check_readiness())
```

#### 3. **Schema Validation Missing**

**Current**: Schema defined but not validated
**Add**: Validation after scout execution
```python
# app/swarms/core/swarm_integration.py
async def _post_execution_integration(self, swarm_result, context):
    if "scout" in context.integration_context.get("swarm_type", "").lower():
        from app.swarms.scout.validation import validate_scout_output
        
        is_valid, errors = validate_scout_output(swarm_result.final_output)
        if not is_valid:
            logger.warning(f"Scout output validation failed: {errors}")
            swarm_result.metadata["schema_valid"] = False
```

## 📋 Expansion Plan: All Artemis Swarms

### Phase 1: Enhanced Base Infrastructure (Immediate)

Create these files to enable all swarms to inherit scout capabilities:

#### 1. **Enhanced Base Class**
```python
# app/swarms/artemis/enhanced_base.py

from typing import Optional, Dict, Any
import asyncio
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SwarmEnhancements:
    """Configuration for swarm enhancements"""
    prefetch_enabled: bool = True
    max_prefetch_files: int = 10
    max_bytes_per_file: int = 50_000
    schema_validation: bool = True
    metrics_enabled: bool = True
    tool_use_enabled: bool = False  # Phase 2

class EnhancedArtemisSwarmBase:
    """Base class providing scout-level capabilities to all swarms"""
    
    def __init__(self, config: Any, enhancements: Optional[SwarmEnhancements] = None):
        self.config = config
        self.enhancements = enhancements or SwarmEnhancements()
        self.prefetch_task: Optional[asyncio.Task] = None
        self.metrics = {}
        self.output_schema = None
        
    async def initialize(self):
        """Initialize enhanced capabilities"""
        if self.enhancements.prefetch_enabled:
            await self._start_prefetch()
            
    async def _start_prefetch(self):
        """Start prefetch in background"""
        from app.swarms.scout.prefetch import prefetch_and_index
        
        self.prefetch_task = asyncio.create_task(
            prefetch_and_index(
                max_files=self.enhancements.max_prefetch_files,
                max_bytes_per_file=self.enhancements.max_bytes_per_file
            )
        )
        
    def register_output_schema(self, schema: dict):
        """Register output schema for validation"""
        self.output_schema = schema
        
    async def validate_output(self, output: Any) -> tuple[bool, list[str]]:
        """Validate output against schema"""
        if not self.enhancements.schema_validation or not self.output_schema:
            return True, []
            
        # Implement JSON schema validation
        import jsonschema
        try:
            jsonschema.validate(output, self.output_schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]
```

#### 2. **Swarm-Specific Schemas**
```python
# app/swarms/artemis/schemas/__init__.py

CODING_SCHEMA = {
    "type": "object",
    "required": ["implementation", "tests", "documentation"],
    "properties": {
        "implementation": {
            "type": "object",
            "properties": {
                "files_modified": {"type": "array"},
                "lines_added": {"type": "integer"},
                "complexity": {"type": "number"}
            }
        },
        "tests": {
            "type": "object",
            "properties": {
                "coverage": {"type": "number"},
                "test_cases": {"type": "array"}
            }
        }
    }
}

PLANNING_SCHEMA = {
    "type": "object",
    "required": ["phases", "timeline", "risks"],
    "properties": {
        "phases": {"type": "array"},
        "timeline": {"type": "object"},
        "risks": {"type": "array"}
    }
}

SECURITY_SCHEMA = {
    "type": "object",
    "required": ["vulnerabilities", "recommendations", "severity"],
    "properties": {
        "vulnerabilities": {"type": "array"},
        "severity": {"enum": ["critical", "high", "medium", "low"]},
        "recommendations": {"type": "array"}
    }
}
```

### Phase 2: Migrate Priority Swarms (Next 2 Days)

#### 1. **Enhanced Coding Swarm**
```python
# app/swarms/artemis/enhanced_coding.py

from app.swarms.artemis.enhanced_base import EnhancedArtemisSwarmBase, SwarmEnhancements
from app.swarms.artemis.schemas import CODING_SCHEMA

class EnhancedCodingSwarm(EnhancedArtemisSwarmBase):
    """Coding swarm with scout-level capabilities"""
    
    def __init__(self, config):
        enhancements = SwarmEnhancements(
            prefetch_enabled=True,
            max_prefetch_files=20,  # More files for coding
            schema_validation=True,
            metrics_enabled=True
        )
        super().__init__(config, enhancements)
        self.register_output_schema(CODING_SCHEMA)
        
    async def execute(self, task: str, context: dict = None):
        """Execute with enhancements"""
        start_time = datetime.now()
        
        # Wait briefly for prefetch to populate some context
        if self.prefetch_task and not self.prefetch_task.done():
            await asyncio.sleep(0.5)  # Give prefetch a head start
            
        # Execute normally
        result = await self._execute_swarm(task, context)
        
        # Validate output
        if self.enhancements.schema_validation:
            valid, errors = await self.validate_output(result)
            result["schema_valid"] = valid
            if errors:
                result["validation_errors"] = errors
                
        # Record metrics
        if self.enhancements.metrics_enabled:
            self.metrics["execution_time"] = (datetime.now() - start_time).total_seconds()
            self.metrics["tokens_used"] = result.get("tokens", 0)
            
        return result
```

#### 2. **Migration Helper**
```python
# app/swarms/artemis/migrate.py

def migrate_to_enhanced(swarm_type: str):
    """Migrate swarm to enhanced version"""
    
    migrations = {
        "coding": ("app.swarms.coding.teams", "app.swarms.artemis.enhanced_coding"),
        "planning": ("app.swarms.planning.planner", "app.swarms.artemis.enhanced_planning"),
        "security": ("app.swarms.security.auditor", "app.swarms.artemis.enhanced_security"),
    }
    
    if swarm_type not in migrations:
        return False
        
    old_module, new_module = migrations[swarm_type]
    
    # Feature flag check
    if os.getenv(f"ENABLE_ENHANCED_{swarm_type.upper()}", "false") == "true":
        # Dynamically import and replace
        import importlib
        new = importlib.import_module(new_module)
        # Register enhanced version
        return True
        
    return False
```

### Phase 3: Add Runtime Controls (Day 3)

#### 1. **Feature Flags**
```bash
# .env.artemis.local additions
ENABLE_ENHANCED_SCOUT=true
ENABLE_ENHANCED_CODING=false  # Gradual rollout
ENABLE_ENHANCED_PLANNING=false
ENABLE_ENHANCED_SECURITY=false

# Prefetch tuning
PREFETCH_MAX_FILES=10
PREFETCH_MAX_BYTES=50000
PREFETCH_TIMEOUT_MS=500
```

#### 2. **CLI Enhancements**
```python
# Add to artemis_runner.py
sp.add_argument("--no-prefetch", action="store_true", help="Disable prefetch")
sp.add_argument("--validate-schema", action="store_true", help="Enforce schema validation")
sp.add_argument("--metrics", action="store_true", help="Show execution metrics")
```

### Phase 4: Testing Suite (Day 4)

#### 1. **Unit Tests**
```python
# tests/artemis/test_enhanced_swarms.py

import pytest
from app.swarms.artemis.enhanced_base import EnhancedArtemisSwarmBase

@pytest.mark.asyncio
async def test_prefetch_respects_limits():
    """Test prefetch stays within configured limits"""
    swarm = EnhancedArtemisSwarmBase(config={})
    swarm.enhancements.max_prefetch_files = 5
    swarm.enhancements.max_bytes_per_file = 1000
    
    await swarm._start_prefetch()
    await swarm.prefetch_task
    
    # Verify limits respected
    assert swarm.metrics.get("prefetch_files", 0) <= 5
    assert swarm.metrics.get("prefetch_bytes", 0) <= 5000

@pytest.mark.asyncio  
async def test_schema_validation():
    """Test output validation against schema"""
    swarm = EnhancedArtemisSwarmBase(config={})
    swarm.register_output_schema({"type": "object", "required": ["test"]})
    
    valid, errors = await swarm.validate_output({"test": "value"})
    assert valid
    
    valid, errors = await swarm.validate_output({"wrong": "key"})
    assert not valid
    assert len(errors) > 0
```

#### 2. **Integration Tests**
```python
# tests/artemis/test_scout_integration.py

@pytest.mark.integration
async def test_scout_with_prefetch():
    """Test scout runs with prefetched context"""
    # Start services if needed
    # Run scout
    # Verify context was used
    pass
```

## 🎯 Recommended Implementation Order

### Today (Immediate)
1. ✅ Fix async issues in prefetch.py
2. ✅ Enhance readiness check output
3. ✅ Add schema validation to scout
4. ✅ Create enhanced_base.py

### Tomorrow (Day 2)
1. Create enhanced_coding.py
2. Create enhanced_planning.py  
3. Add migration helper
4. Test with feature flags

### Day 3
1. Add runtime controls
2. Create enhanced_security.py
3. Create enhanced_review.py
4. Update CLI with new flags

### Day 4
1. Complete test suite
2. Run integration tests
3. Performance benchmarks
4. Documentation update

## 📊 Success Metrics

Track these metrics to validate improvements:

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Scout execution time | 30s | 20s | With prefetch |
| Output validation | 0% | 100% | Schema compliance |
| Context relevance | 40% | 80% | Files used/prefetched |
| Error rate | 15% | 5% | Failed executions |
| Token usage | 10K | 6K | Per execution |

## 🚨 Critical Notes

1. **Don't break existing swarms** - All enhancements must be optional
2. **Feature flag everything** - Allow instant rollback
3. **Test prefetch limits** - Prevent memory bloat
4. **Monitor performance** - Track metrics from day 1
5. **Document changes** - Update swarm documentation

## Final Request

Codex, please:

1. **Fix the async issues** in prefetch.py
2. **Enhance readiness check** as shown above
3. **Create enhanced_base.py** with the pattern provided
4. **Migrate coding swarm** as proof of concept
5. **Add feature flags** for safe rollout
6. **Test locally** without pushing
7. **Report results** with metrics

Remember: 
- Local changes only (no push)
- Backwards compatible
- Feature flagged
- Well tested

The goal is to have all Artemis swarms inherit scout's capabilities (prefetch, schemas, metrics) while maintaining stability and allowing gradual rollout.

---
*Ready for your implementation. Focus on making the enhancement framework reusable so all swarms benefit from scout innovations.*