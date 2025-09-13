# SOPHIA INTEL APP - Technical Architecture

## Overview
Sophia Intel App is a unified business intelligence platform for PayReady, integrating 21+ business services with AI-powered insights.

## Core Components

### 1. Main Application UI
- **Folder**: `sophia-intel-app/` (Next.js)
- **Port**: 3000
- **Description**: Consolidated Sophia dashboards with real-time integrations

### 2. Business Logic & API (`/app`)
- **Orchestrator**: `app/sophia/sophia_orchestrator.py`
- **Unified API**: `app/main_unified.py` (FastAPI on port 8003)
- **Integrations**: `app/integrations/` (21 services)
- **AI Personas**: `app/agents/personas/`

### 3. MCP Servers
- Memory Server (Port 8081)
- Git Server (Port 8084)
- Sophia Intel MCP (Port 8085)

### 4. Bridge API
- **File**: `bridge/api.py`
- **Port**: 8004
- **Purpose**: WebSocket and SSE streaming for real-time updates

## Service Ports
| Service | Port | Status |
|---------|------|--------|
| Agent UI (Sophia Dashboard) | 3000 | Primary |
| Sophia API | 8003 | Active |
| Bridge API (Builder) | 8004 | Active |
| Memory MCP | 8081 | Active |
| Filesystem MCP | 8082 | Active |
| Git MCP | 8084 | Active |

## Quick Start
```bash
# Start everything
./start_sophia_complete.sh

# Stop everything
./stop_sophia_complete.sh

# Check status
curl http://localhost:8003/healthz
```

## Important Notes
- Do NOT create separate dashboard apps – use `sophia-intel-app/`
- Use existing integrations in `app/integrations/`
- Agent UI is canonical; backend is `app/main_unified.py`
- Follow AGENTS.md and docs/AGENTS_CONTRACT.md
