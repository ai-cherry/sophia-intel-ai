# 🎯 Codex Implementation Request: Unified Artemis Enhancement

## Context
Codex, I've created a comprehensive plan for extending scout swarm capabilities across all Artemis swarms. Your local implementation approach (prefetch hook, scout overlays, readiness CLI) aligns perfectly with the broader vision. 

## Request for Review & Implementation

### 1. Please Review the Unified Plan
Review `/Users/lynnmusil/sophia-intel-ai/ARTEMIS_UNIFIED_ENHANCEMENT_PLAN.md` for:
- Architectural soundness
- Implementation sequencing 
- Potential issues or optimizations
- Integration with your current scout enhancements

### 2. Key Improvements to Consider

#### Immediate Scout Enhancements (Your Current Work)
- **Prefetch Hook**: Cap at 500KB total (10 files × 50KB max each)
- **Scout Overlays**: Use the SCOUT_OUTPUT_SCHEMA from the plan
- **Readiness CLI**: Include Weaviate, Redis, and MCP stdio checks
- **Smoke Test**: Add non-network validation path

#### Extended Implementation (After Scout)

**Phase 1: Enhanced Base Infrastructure**
```python
# Priority files to create:
app/swarms/artemis/enhanced_base.py  # Base class with all capabilities
app/swarms/artemis/mixins/
  ├── mcp_tool_mixin.py      # Tool integration
  ├── prefetch_mixin.py       # Context prefetching  
  ├── metrics_mixin.py        # Performance tracking
  └── schema_mixin.py         # Output validation
```

**Phase 2: Swarm Migration (Priority Order)**
1. **Coding Swarm** - Highest daily impact
2. **Planning Swarm** - Strategic value
3. **Security Swarm** - Risk mitigation
4. **Review Swarm** - Quality improvement

### 3. Implementation Checklist

#### Scout Swarm Enhancements (Immediate)
- [ ] Wire `prefetch_and_index()` into repository_scout with guards
- [ ] Add SCOUT_OUTPUT_SCHEMA to prompt assembly
- [ ] Create `scripts/scout_readiness_check.py`
- [ ] Add `--check` flag to scout command
- [ ] Implement basic smoke test (no network)

#### Base Infrastructure (Next)
- [ ] Create `EnhancedArtemisSwarmBase` class
- [ ] Implement MCP tool mixin with REQUEST_FS_READ pattern
- [ ] Add prefetch mixin with LRU cache (100MB limit)
- [ ] Create metrics collection system
- [ ] Add structured output validation

#### Swarm Upgrades (Following)
- [ ] Migrate CodingSwarm to EnhancedCodingSwarm
- [ ] Add backward compatibility adapter
- [ ] Create feature flags for gradual rollout
- [ ] Implement performance benchmarks

### 4. Configuration Recommendations

```yaml
# config/artemis_enhanced.yaml
scout_prefetch:
  enabled: true
  max_files: 10
  max_bytes_per_file: 50000
  total_cache_mb: 100
  
readiness_checks:
  required:
    - stdio_mcp
    - portkey_api_key
  optional:
    - weaviate
    - redis
    
performance:
  metrics_enabled: true
  trace_sampling: 0.1
  log_level: INFO
```

### 5. Testing Strategy

```python
# tests/artemis/test_enhanced_scout.py

def test_scout_readiness():
    """Test readiness check without network"""
    checks = check_scout_readiness()
    assert "stdio_mcp" in checks
    assert "llm_keys" in checks
    
def test_prefetch_with_limits():
    """Test prefetch respects size limits"""
    content = await prefetch_content(paths=large_file_list)
    assert total_size(content) <= 500_000  # 500KB limit
    
def test_schema_validation():
    """Test output conforms to schema"""
    output = await scout_swarm.execute(test_task)
    assert validate_schema(output, SCOUT_OUTPUT_SCHEMA)
```

### 6. Success Criteria

#### For Scout Implementation (Today)
- [ ] Readiness check passes for stdio MCP
- [ ] Scout runs with prefetched context (even without Weaviate)
- [ ] Output follows structured schema
- [ ] Smoke test passes without network

#### For Extended Implementation (This Week)
- [ ] Base classes created and tested
- [ ] At least 2 swarms migrated successfully
- [ ] Performance metrics show 30% improvement
- [ ] Backward compatibility maintained

### 7. Special Considerations

1. **Weaviate Fallback**: If Weaviate unavailable, use Redis L1 cache with JSON serialization
2. **Memory Management**: Implement aggressive LRU eviction at 100MB
3. **Tool Rate Limiting**: Max 2 tool calls per agent per iteration
4. **Error Recovery**: Graceful degradation if prefetch/tools fail

## Proposed Workflow

1. **Review this request and the unified plan**
2. **Make any critical improvements** to the architecture
3. **Implement scout enhancements** (your current work)
4. **Test locally** without pushing
5. **Report results** with any issues found
6. **Implement base infrastructure** (if scout successful)
7. **Migrate first swarm** (CodingSwarm) as proof of concept
8. **Create single batched commit** when ready

## Key Questions for Implementation

1. Should we use async Queue for prefetch or synchronous loading?
2. Should tool requests be in-band (in LLM response) or out-of-band (separate field)?
3. Should schemas be YAML or JSON for easier maintenance?
4. Should metrics go to Redis or local SQLite for simplicity?

## Final Notes

- **Don't push** until explicitly requested
- **Local testing only** for now
- **Fire-and-forget prefetch** to avoid blocking
- **Guards on all enhancements** for safety
- **Feature flags** for easy rollback

Codex, please review this entire plan, make improvements where you see opportunities, then proceed with implementation starting with the scout enhancements. Focus on making the system robust, performant, and maintainable.

The goal is a unified, enhanced Artemis ecosystem that leverages the innovations from scout swarm across all swarm types, creating a cohesive AI coordination platform.

---

*Ready for your review and implementation. Remember: local only, no push until requested.*