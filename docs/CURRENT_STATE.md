---
title: Current System State
type: reference
status: active
version: 1.0.0
last_updated: 2024-09-01
ai_context: high
auto_update: true
---

# 🔄 Current System State

## Active Services

### API Endpoints
- **Unified API**: http://localhost:8000
  - Health: `/health`
  - Swarms: `/teams/run`
  - NL Interface: `/api/nl/process`
  - Memory: `/memory/search`, `/memory/add`

- **MCP Server v2**: http://localhost:8004
  - Health: `/health`
  - Metrics: `/metrics`

### UI Applications
- **Agent UI**: http://localhost:3000
- **Streamlit Chat**: http://localhost:8501

### Infrastructure
- **Redis**: redis://localhost:6379
- **Weaviate**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Configuration
- **Environment**: development
- **Optimization Modes**: lite, balanced, quality
- **Active Swarms**: coding-debate, improved-solve, simple-agents, mcp-coordinated

## Recent Deployments
- Last deployment: 2024-09-01
- Version: 2.0.0
- Status: Healthy

## Active Features
- ✅ Unified Orchestrator Facade
- ✅ MCP Bridge System
- ✅ WebSocket Real-time Updates
- ✅ Memory Context Integration
- ✅ Mode Normalization
- ✅ Circuit Breakers
- ✅ Performance Monitoring

## Known Issues
- None currently

## Next Maintenance
- Scheduled: 2024-09-08
- Type: Documentation review
