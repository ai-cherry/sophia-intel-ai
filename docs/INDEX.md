---
title: Documentation Index
type: index
status: active
version: 2.0.0
last_updated: 2025-09-08
ai_context: high
---

# 📚 SOPHIA Documentation Index

_Updated for Phase 3 Implementation - September 2025_

## 🚀 Quick Start

- [README](../README.md) - Project overview
- [Ports Reference](PORTS.md) - Standard local ports and flags
- [Environment Setup](SECURE_ENV_AND_TOOLS.md) - Configure API keys and tools
- [Phase 3 Agent Architecture](PHASE_3_AGENT_WIRING_PLAN.md) - Current implementation
- [SOPHIA Runbook](RUNBOOK_SOPHIA.md) - Operational guide

## 📐 Current Architecture (Phase 3)

### Core Systems
- [Phase 3 Agent Wiring Plan](PHASE_3_AGENT_WIRING_PLAN.md) - Agent implementation with router
- [Phase 2 Design](PHASE2_DESIGN.md) - Router, budget, circuit breaker
- [System Architecture](ARCHITECTURE.md) - Overall system design
- [Sidecar Architecture](sidecar-architecture.md) - MCP sidecar pattern

### Analysis & Planning
- [Documentation Audit](DOCUMENTATION_AUDIT.md) - Documentation reorganization plan
- [UI Unification Report](../sophia_analysis/UNIFICATION_REPORT.md) - Frontend consolidation
- [Implementation Roadmap](../sophia_analysis/IMPLEMENTATION_ROADMAP.md) - Development timeline
- [Unified Design Plan](../sophia_analysis/SOPHIA_UNIFIED_DESIGN_PLAN.md) - Comprehensive design

## 🤖 Agent System (Phase 3)

### Agents
- **Coder Agent** - Code generation, refactoring, test creation
- **Architect Agent** - System design, API design, scalability
- **Reviewer Agent** - Code review, security analysis, bug detection
- **Researcher Agent** - Web search, documentation lookup

### Infrastructure
- [Smart Router](PHASE2_DESIGN.md) - Model routing with fallbacks
- [Budget Manager](PHASE2_DESIGN.md) - Cost control and tracking
- [Circuit Breaker](PHASE2_DESIGN.md) - Failure protection
- [Telemetry System](../webui/telemetry_endpoint.py) - Monitoring

## 📊 API Reference

### REST Endpoints
- [API Documentation](API_REFERENCE.md) - Core API reference
- **Telemetry API** (Port 5003)
  - `GET /api/telemetry/snapshot` - Recent events
  - `GET /api/telemetry/budgets` - Budget status
  - `GET /api/telemetry/circuits` - Circuit breaker status
  - `GET /api/telemetry/metrics` - Routing metrics

### MCP Integration
- [MCP Integration Guide](SWARM_MCP_INTEGRATION.md) - Model Context Protocol
- [Agent Contracts](AGENTS_CONTRACT.md) - Agent interfaces
- [MCP Servers Info](guides/integrations/MCP_SERVERS_INFO.md) - Server details

## 🛠️ Development Guides

### Configuration
- [Environment Variables](SECURE_ENV_AND_TOOLS.md) - Required setup
- [Service Dependencies](../config/service-dependency-graph.md) - Service map
- [Docker Services](DOCKER_SERVICES_MATRIX.md) - Container config
- [ADR-006 Config Management](configuration/ADR-006-IMPLEMENTATION-GUIDE.md)

### Implementation Guides
- [AI Orchestrator Plan](guides/development/AI_ORCHESTRATOR_COMPREHENSIVE_PLAN.md)
- [Implementation Plan](guides/development/IMPLEMENTATION_PLAN.md)
- [Orchestration Plan](guides/development/COMPREHENSIVE_ORCHESTRATION_PLAN.md)
- [Phase 2 Implementation](guides/development/PHASE_2_IMPLEMENTATION_PLAN.md)
 - Deployment Prompts:
   - [Docker Deployment Specialist](../docs/prompts/DOCKER_DEPLOYMENT_SPECIALIST.md)
   - [Agno Multi‑Agent Specialist](../docs/prompts/AGNO_MULTI_AGENT_SPECIALIST.md)

### Integration Guides
- [Portkey Integration](guides/integrations/portkey.md) - LLM gateway
- [NL-Swarm Integration](guides/development/NL_SWARM_INTEGRATION_PLAN.md)

## 📚 Architecture Decisions

### Active ADRs
- [ADR-001: UI Consolidation](architecture/decisions/ADR-001.md)
- [ADR-002: Evolution Engine](architecture/decisions/ADR-002.md)
- [ADR-003: Consciousness Tracking](architecture/decisions/ADR-003.md)
- [ADR-004: MCP Security](architecture/decisions/ADR-004.md)
- [ADR-005: Memory System](architecture/decisions/ADR-005.md)
- [ADR-006: Configuration Management](architecture/decisions/ADR-006.md)
- [ADR-007: Testing Framework](architecture/decisions/ADR-007.md)
- [ADR-008: Deployment Architecture](architecture/decisions/ADR-008.md)

## 🧠 Knowledge Systems

- [Foundational Knowledge System](foundational_knowledge_system.md) - Core knowledge
- [Meta Tagging System](meta_tagging_system.md) - Content organization
- [Capability Graph](CAPABILITY_GRAPH.md) - System capabilities

## 🚨 Operations

### Runbooks
- [SOPHIA Runbook](RUNBOOK_SOPHIA.md) - Main operations
- [Troubleshooting Guide](guides/operations/troubleshooting.md) - Common issues
- [Production Ready Guide](guides/deployment/PRODUCTION_READY.md) - Deployment

### Monitoring
- Telemetry Dashboard: `http://localhost:5003`
- Agent Status: Via telemetry API
- Budget Tracking: Real-time via API

## 📦 Project Structure

```
sophia-intel-ai/
├── agno_core/              # Core agent framework
│   ├── adapters/           # Router, budget, circuit breaker
│   │   ├── router.py       # Smart routing with fallbacks
│   │   ├── budget.py       # Budget management
│   │   ├── circuit_breaker.py  # Failure protection
│   │   └── telemetry.py    # Event tracking
│   ├── agents/             # Agent implementations (Phase 3)
│   └── coordinator/        # Agent orchestration
├── agent-ui/               # React frontend
│   └── src/               
│       ├── components/     # UI components
│       ├── modules/        # Feature modules
│       └── store/          # Zustand state
├── mcp_servers/            # MCP server implementations
├── webui/                  # Backend services
│   └── telemetry_endpoint.py  # Telemetry service
├── config/                 # Configuration files
├── docs/                   # Documentation
└── sophia_analysis/        # Analysis reports
```

## 📊 Status Dashboard

### ✅ Phase 2 Complete
- Smart Router with model selection
- Budget Manager with soft/hard caps
- Circuit Breaker with cooldown
- Telemetry system with API
- Cost estimation logic

### 🚧 Phase 3 In Progress
- BaseAgent class implementation
- 4 specialized agents (Coder, Architect, Reviewer, Researcher)
- Agent Coordinator with strategies
- MCP server wrappers
- Integration testing

### 📅 Upcoming
- Production deployment
- Performance optimization
- Documentation site generation
- Monitoring dashboard UI

## 🔗 Resources

### Internal Docs
- [Tech Stack Analysis](TECH_STACK_ANALYSIS.md)
- [API Keys Guide](guides/development/API_KEYS_GUIDE.md)
- [Document Management Strategy](DOCUMENT_MANAGEMENT_STRATEGY.md)

### External Links
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Anthropic API](https://docs.anthropic.com)
- [OpenAI API](https://platform.openai.com/docs)
- [Portkey Documentation](https://portkey.ai/docs)

## 📝 Recent Updates

### September 2025
- ✅ Phase 3 Agent Architecture designed
- ✅ Telemetry endpoint implemented (port 5003)
- ✅ Documentation audit completed
- ✅ UI unification analysis complete
- 🚧 Agent implementation in progress

### Next Steps
1. Complete BaseAgent implementation
2. Deploy MCP servers for agents
3. Create agent UI components
4. Integration testing
5. Production deployment

---

*For the latest updates, check the [Documentation Audit](DOCUMENTATION_AUDIT.md) or the [Phase 3 Plan](PHASE_3_AGENT_WIRING_PLAN.md)*
