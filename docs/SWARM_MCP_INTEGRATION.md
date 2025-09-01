# 🚀 Swarm + MCP Integration Architecture

## Overview

This document describes the integrated architecture connecting AI swarms with MCP (Model Context Protocol) bridges, enabling coordinated multi-assistant execution with unified optimization and monitoring.

## 🏗️ Architecture Components

### 1. **Unified Orchestrator Facade** (`app/orchestration/unified_facade.py`)
Central routing layer that:
- Routes requests to appropriate swarm implementations
- Manages MCP assistant coordination
- Handles memory context injection/extraction
- Provides consistent streaming interface
- Wraps calls with circuit breakers and monitoring

### 2. **Mode Normalizer** (`app/orchestration/mode_normalizer.py`)
Ensures consistent optimization modes across all swarms:
- Normalizes mode strings (fast/lite/speed → LITE)
- Provides unified configuration for each mode
- Calculates mode costs and selects optimal modes
- Handles graceful degradation strategies

### 3. **MCP Bridge System** (`mcp-bridge/`)
TypeScript adapters for AI assistants:
- **Claude Desktop**: General memory and context operations
- **Roo/Cursor**: Code intelligence and pattern analysis
- **Cline**: Autonomous task execution and project management

### 4. **Swarm Implementations**
- **Coding Swarm**: Debate pipeline with critic/judge/gates
- **Improved Swarm**: 8 improvement patterns with selective activation
- **Simple Agents**: Sequential agent execution
- **MCP Coordinated**: Multi-assistant coordination

## 🔄 Data Flow

```
User Request
    ↓
Unified API Gateway (/teams/run)
    ↓
Unified Orchestrator Facade
    ├─→ Mode Selection (based on complexity/urgency)
    ├─→ Memory Context Injection
    ├─→ Circuit Breaker Wrapping
    ↓
Swarm Router
    ├─→ Coding Swarm (code tasks)
    ├─→ Improved Swarm (complex problems)
    ├─→ Simple Agents (sequential tasks)
    └─→ MCP Coordination (multi-assistant)
         ├─→ Claude (analysis/synthesis)
         ├─→ Roo (code patterns)
         └─→ Cline (autonomous execution)
    ↓
Performance Monitoring & Metrics
    ↓
Memory Storage (results/learning)
    ↓
Response Stream (SSE/NDJSON)
```

## 🎯 Key Features

### Unified Optimization Modes

| Mode | Aliases | Timeout | Max Agents | Patterns | Use Case |
|------|---------|---------|------------|----------|----------|
| **LITE** | fast, speed, quick | 30s | 2 | Safety only | Urgent/simple tasks |
| **BALANCED** | normal, standard | 120s | 5 | Safety, Roles, Gates | Default operation |
| **QUALITY** | thorough, complete | 300s | 10 | All 8 patterns | Complex/critical tasks |

### Mode Selection Logic

```python
# Automatic mode selection based on:
- Task Complexity (0.0 - 1.0)
- Urgency (low/normal/high/critical)
- Resource Availability (system health)

High Complexity + Low Urgency + Good Resources → QUALITY
Low Complexity + High Urgency + Limited Resources → LITE
Default → BALANCED
```

### Circuit Breaker Protection

Components protected:
- Memory operations (search/store)
- LLM calls
- MCP assistant communications
- Vector database queries

Degradation strategies:
- Skip non-critical operations
- Reduce agent count
- Fallback to simpler mode
- Use cached results

### Performance Monitoring

Metrics collected:
- Execution time per pattern
- Success/failure rates
- Quality scores
- Resource utilization
- Circuit breaker states

## 🔧 Implementation Fixes Applied

### 1. **Mode Normalization Fix**
```python
# Before (in coding swarm):
def _is_fast_mode(self):
    return self.config.get("optimization") in ["speed", "fast"]

# After:
def _is_fast_mode(self):
    mode = self.config.get("optimization").lower()
    return mode in ["speed", "fast", "lite"]  # Now includes "lite"
```

### 2. **Optimizer Wiring**
```python
# Improved swarm now uses optimizer for dynamic mode selection:
mode_cfg = self.optimizer.get_optimal_swarm_config(problem)
self.optimization_mode = mode_cfg["mode"]
self.enabled_patterns = mode_cfg["patterns"]
```

### 3. **Circuit Breaker Integration**
```python
# All external calls now wrapped:
cb = self.optimizer.get_circuit_breaker("memory")
async with performance_monitoring(self.optimizer, "memory_search"):
    results = await cb.call(self.memory.search, query)
```

### 4. **Pattern Module Usage**
```python
# Replaced inline implementations with imports:
from app.swarms.patterns.adversarial_debate import AdversarialDebateSystem
from app.swarms.patterns.quality_gates import QualityGateSystem
# ... etc
```

## 📡 MCP Assistant Coordination

### Coordination Strategies

**Code-Heavy Tasks:**
1. Roo analyzes codebase patterns
2. Cline creates implementation plan
3. Claude synthesizes and reviews

**General Tasks:**
1. Claude performs initial analysis
2. Cline executes autonomously (if not lite mode)
3. Results synthesized

### Assistant Capabilities

| Assistant | Strengths | Best For |
|-----------|-----------|----------|
| **Claude** | General reasoning, synthesis | Analysis, review, documentation |
| **Roo/Cursor** | Code intelligence, patterns | Refactoring, code search, patterns |
| **Cline** | Autonomous execution | Implementation, testing, planning |

## 🚀 Usage Examples

### Basic Execution
```python
from app.orchestration.wire_integration import IntegratedSwarmSystem

system = IntegratedSwarmSystem()
await system.initialize()

# Auto mode selection
result = await system.execute_with_mode_selection(
    task="Implement user authentication",
    urgency="normal"
)
```

### MCP Coordinated Execution
```python
# Use specific assistants
result = await system.execute_mcp_coordinated(
    task="Refactor and optimize database queries",
    assistants=["roo", "cline"],
    mode="quality"
)
```

### Manual Mode Control
```python
from app.orchestration.unified_facade import SwarmRequest, SwarmType, OptimizationMode

request = SwarmRequest(
    swarm_type=SwarmType.CODING_DEBATE,
    task="Debug memory leak",
    mode=OptimizationMode.LITE,  # Force lite mode
    use_memory=True
)

async for event in facade.execute(request):
    print(f"{event.event_type}: {event.data}")
```

## 📊 Monitoring & Observability

### Prometheus Metrics
- `swarm_execution_seconds{swarm_type, mode}`
- `swarm_pattern_success_total{pattern}`
- `swarm_circuit_breaker_open{component}`
- `swarm_quality_score{swarm_type}`

### Grafana Dashboards
- Swarm execution times by mode
- Pattern effectiveness
- Circuit breaker states
- System health score
- Cost analysis by mode

### Logging
```python
# Structured logging at key points:
logger.info("Swarm execution", extra={
    "swarm_type": request.swarm_type.value,
    "mode": request.mode.value,
    "complexity": complexity,
    "duration": duration
})
```

## 🔐 Security

- JWT authentication for MCP operations
- Rate limiting per assistant
- Encrypted memory storage
- Audit logging for all operations
- RBAC with granular permissions

## 🧪 Testing Strategy

### Unit Tests
- Mode normalization correctness
- Circuit breaker state transitions
- Pattern selection logic
- Degradation strategies

### Integration Tests
- End-to-end swarm execution
- MCP assistant coordination
- Memory operations with failures
- Mode transitions under load

### Performance Tests
- Latency comparison: LITE vs QUALITY
- Throughput under various modes
- Resource utilization
- Degradation effectiveness

## 📈 Performance Optimizations

1. **Caching**: Redis cache for memory searches
2. **Connection Pooling**: Reused connections to MCP/LLM
3. **Async Execution**: Non-blocking I/O throughout
4. **Selective Patterns**: Only load needed patterns
5. **Circuit Breaking**: Fast fail on unhealthy components

## 🚦 Deployment Checklist

- [ ] Configure mode settings in `swarm_optimization_config.json`
- [ ] Set up Redis for caching and pub/sub
- [ ] Deploy MCP server v2
- [ ] Install and configure MCP bridge adapters
- [ ] Configure monitoring stack (Prometheus/Grafana)
- [ ] Set JWT secrets and API keys
- [ ] Mount persistent volumes for strategy archive
- [ ] Configure circuit breaker thresholds
- [ ] Set up log aggregation
- [ ] Test degradation strategies

## 🔄 Migration Path

### From Current State
1. Deploy Unified Orchestrator Facade
2. Apply mode normalization fixes
3. Wire optimizer and circuit breakers
4. Deploy MCP bridges
5. Update API endpoints to use facade
6. Monitor and tune

### Rollback Plan
1. Keep original endpoints active
2. Use feature flags for gradual rollout
3. Monitor error rates and latency
4. Quick switch back if issues

## 📚 Related Documentation

- [MCP Bridge README](../mcp-bridge/README.md)
- [Swarm Patterns Guide](./swarm_patterns.md)
- [API Documentation](./api_docs.md)
- [Security Framework](../app/security/README.md)

## 🎯 Success Metrics

- **Latency Reduction**: 40% faster in LITE mode vs current
- **Quality Improvement**: 25% higher success rate in QUALITY mode
- **Reliability**: 99.9% uptime with degradation
- **Cost Efficiency**: 30% reduction via mode optimization
- **Developer Experience**: Single unified interface

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## 📝 License

MIT License - See [LICENSE](../LICENSE) for details.