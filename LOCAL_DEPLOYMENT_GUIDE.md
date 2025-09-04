# 🚀 Sophia Intelligence Platform - Local Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Sophia Intelligence Platform locally with all services running properly.

## 📋 Prerequisites

- Python 3.11+ installed
- Node.js 18+ (if using frontend components)
- Required environment variables configured
- All dependencies installed

## 🔧 Environment Setup

### 1. Environment Variables
Create or update your environment with the following:

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export PORTKEY_API_KEY="your-portkey-key"
export TOGETHER_API_KEY="your-together-key" 
export OPENAI_API_KEY="dummy"  # Can be dummy for local dev
export LOCAL_DEV_MODE="true"
export RBAC_ENABLED="true"
export DB_TYPE="sqlite"
export DB_PATH="sophia_rbac.db"
```

### 2. Database Initialization
Initialize the RBAC database (if not already done):

```bash
python3 migrations/001_rbac_foundation.py up
```

## 🚀 Deployment Steps

### Step 1: Start the Unified API Server (Port 8006)

```bash
OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
PORTKEY_API_KEY=$PORTKEY_API_KEY \
TOGETHER_API_KEY=$TOGETHER_API_KEY \
OPENAI_API_KEY=dummy \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=8006 \
python3 -m app.api.unified_server &
```

**Expected Output:**
- Server starts on http://localhost:8006
- Health endpoint available at `/health`
- API documentation at `/docs`

### Step 2: Start the MCP Server (Port 3333)

```bash
OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
PORTKEY_API_KEY=$PORTKEY_API_KEY \
TOGETHER_API_KEY=$TOGETHER_API_KEY \
OPENAI_API_KEY=dummy \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=3333 \
RBAC_ENABLED=true \
DB_TYPE=sqlite \
DB_PATH=sophia_rbac.db \
python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333 --reload &
```

**Expected Output:**
- MCP server starts on http://localhost:3333
- Static files mounted at `/static`
- Sophia Intelligence Hub available at `/static/sophia-intelligence-hub.html`
- Sales Intelligence Swarm initialized
- Persona integration endpoints registered

### Step 3: Start the Persona Server (Port 9000)

```bash
AGENT_API_PORT=9000 python3 persona_server_standalone.py &
```

**Expected Output:**
- Persona server starts on http://localhost:9000
- Agent Factory dashboard available at `/agents/factory-dashboard.html`
- Apollo and Athena personas active and responding

## 🔍 Health Check & Verification

### Automated Health Check
Run the comprehensive health check script:

```bash
./deployment_health_check.sh
```

### Manual Verification Commands

```bash
# Check all processes are running
ps aux | grep -E "(unified_server|mcp_server|persona_server)"

# Test health endpoints
curl http://localhost:8006/health
curl http://localhost:9000/health
curl http://localhost:3333/static/sophia-intelligence-hub.html | head -5

# Test persona functionality
curl -X POST http://localhost:9000/api/personas/chat/apollo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Apollo!"}'

curl -X POST http://localhost:9000/api/personas/chat/athena \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Athena!"}'
```

## 🌐 Available Services

Once deployed, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Sophia Intelligence Hub** | http://localhost:3333/static/sophia-intelligence-hub.html | Main dashboard with all systems |
| **Persona Dashboard** | http://localhost:9000/agents/factory-dashboard.html | AI personas interface |
| **Unified API** | http://localhost:8006/docs | Core API documentation |
| **MCP Server** | http://localhost:3333 | MCP unified server |
| **Persona API** | http://localhost:9000/docs | Persona server API docs |

## 🤖 Active AI Personas

- **Apollo 'The Strategist' Thanos** ⚡
  - Role: Sales Wisdom & Strategic Catalyst  
  - Endpoint: `/api/personas/chat/apollo`
  - Tagline: "With Sophia's guidance, every conversation becomes a path to victory!"

- **Athena 'The Protector' Sophia** 🦉
  - Role: Client Wisdom & Success Guardian
  - Endpoint: `/api/personas/chat/athena`
  - Tagline: "Through Sophia's insight, we transform challenges into lasting partnerships!"

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. Logger Error in MCP Server
**Error:** `NameError: name 'logger' is not defined`
**Solution:** Ensure logging is properly imported and configured in `dev_mcp_unified/core/mcp_server.py`

#### 2. Port Already in Use
**Error:** Port conflicts on 3333, 8006, or 9000
**Solution:** Kill existing processes:
```bash
pkill -f "unified_server"
pkill -f "mcp_server"  
pkill -f "persona_server"
```

#### 3. Redis Connection Issues
**Warning:** `Could not connect to Redis: module 'aioredis' has no attribute 'from_url'`
**Solution:** This is a known warning and doesn't affect functionality. Redis is optional for local development.

#### 4. API Authentication Errors (400)
**Warning:** Linear/Gong API errors during startup
**Solution:** These are expected in local development mode when external APIs aren't configured.

### Health Check Failures

If `./deployment_health_check.sh` reports failures:

1. **Check Process Status:**
   ```bash
   ps aux | grep -E "(unified_server|mcp_server|persona_server)"
   ```

2. **Review Logs:**
   - Check terminal output for each service
   - Look for specific error messages

3. **Restart Individual Services:**
   Follow the deployment steps above for any failed service

4. **Verify Environment Variables:**
   ```bash
   echo $OPENROUTER_API_KEY
   echo $PORTKEY_API_KEY
   ```

## 🔄 Quick Restart Process

For development, use this quick restart sequence:

```bash
# Kill all services
pkill -f "unified_server"; pkill -f "mcp_server"; pkill -f "persona_server"

# Wait a moment
sleep 2

# Restart all services (run each in separate terminals or background)
./quick_deploy.sh  # See next section for this script
```

## 📝 Development Notes

### File Structure
- **MCP Server:** `dev_mcp_unified/core/mcp_server.py`
- **Unified Server:** `app/api/unified_server.py` 
- **Persona Server:** `persona_server_standalone.py`
- **Health Check:** `deployment_health_check.sh`

### Key Configuration Files
- `dev_mcp_unified/core/mcp_server.py` - Main MCP server with all integrations
- `persona_server_standalone.py` - Standalone persona server
- `CLAUDE.md` - Project configuration and guidelines

### API Endpoints Summary

#### Unified Server (8006)
- `/health` - Health check
- `/docs` - API documentation
- Core business logic APIs

#### MCP Server (3333)
- `/static/*` - Static file serving
- `/api/personas/team` - Team members list
- `/api/swarms/status` - Swarm status
- Sales intelligence endpoints

#### Persona Server (9000)
- `/health` - Health check
- `/api/personas/team` - Apollo & Athena team
- `/api/personas/chat/{persona_id}` - Chat with personas
- `/agents/factory-dashboard.html` - UI dashboard

## ✅ Success Indicators

Your deployment is successful when:

1. ✅ All three servers start without errors
2. ✅ Health check script passes all tests
3. ✅ Both personas respond to chat messages
4. ✅ Dashboards load properly in browser
5. ✅ No critical errors in server logs

## 🎯 Next Steps

After successful deployment:
1. Access the Sophia Intelligence Hub to explore all features
2. Test persona interactions through the dashboard
3. Review API documentation for integration options
4. Monitor logs for any runtime issues
5. Use the health check script regularly during development

---

*For additional support, check the troubleshooting section or review server logs for specific error messages.*