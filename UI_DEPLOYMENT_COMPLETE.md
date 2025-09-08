# Complete UI Deployment & Integration Guide

## ✅ Current Architecture (Properly Structured)

Based on ChatGPT's analysis, we have the **correct UI architecture**:

```yaml
webui/
├── backend/
│   └── main.py         # FastAPI backend (Port 8000)
├── frontend/
│   ├── index.html      # Main UI
│   └── tactical-command.html  # Advanced interface
└── Dockerfile.webui    # Container definition
```

## 🚀 Complete Local Deployment

### Step 1: Start Infrastructure & MCP
```bash
# One command to start everything
cd ~/sophia-intel-ai
bash scripts/dev.sh all

# Verify infrastructure
make health-infra
```

### Step 2: Start WebUI Backend
```bash
# Option A: Direct Python (recommended for dev)
cd webui/backend
python3 main.py &

# Option B: Via Docker (if Dockerfile.webui is fixed)
docker compose -f docker-compose.dev.yml up -d webui
```

### Step 3: Access UI Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| WebUI Backend | http://localhost:8000 | API & Static serving |
| Health Check | http://localhost:8000/health | Backend status |
| API Docs | http://localhost:8000/docs | FastAPI documentation |
| Frontend | http://localhost:8000/static | Static UI files |
| WebSocket | ws://localhost:8000/ws | Real-time updates |

### Step 4: MCP Integration URLs

The webui backend connects to MCP servers:
```yaml
MCP_FILESYSTEM_SOPHIA_URL: http://localhost:8082
MCP_FILESYSTEM_ARTEMIS_URL: http://localhost:8083  # When ARTEMIS_PATH set
MCP_GIT_URL: http://localhost:8084
MCP_MEMORY_URL: http://localhost:8081
```

## 🧪 End-to-End Validation Tests

### Test 1: Health Checks
```bash
# WebUI Backend
curl -s http://localhost:8000/health | jq

# MCP Services
make mcp-test

# Expected: All services "ok" or "healthy"
```

### Test 2: Create Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent": "coder", "repo_scope": "sophia"}' | jq
```

### Test 3: Tool Invocation (Filesystem)
```bash
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "fs",
    "scope": "sophia",
    "action": "list",
    "params": {"path": "."}
  }' | jq
```

### Test 4: WebSocket Connection
```javascript
// In browser console or Node.js
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.send(JSON.stringify({type: 'ping'}));
```

### Test 5: Agent Completion
```bash
curl -X POST http://localhost:8000/agents/complete \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "agent": "coder"
  }' | jq
```

## 🔧 Optional: Artemis Integration

### Enable Artemis Sidecar
```bash
# Set Artemis path
export ARTEMIS_PATH=~/artemis-cli

# Start Artemis profile
docker compose -f docker-compose.dev.yml --profile artemis up -d

# Test Artemis filesystem
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "fs",
    "scope": "artemis",
    "action": "list",
    "params": {"path": "."}
  }'
```

## 📊 Complete System Status

### Currently Running Services
```yaml
Infrastructure:
  Redis: ✅ Port 6379
  PostgreSQL: ✅ Port 5432
  Weaviate: ✅ Port 8080

MCP Servers:
  Memory: ✅ Port 8081
  Filesystem: ✅ Port 8082
  Git: ✅ Port 8084

UI Services:
  WebUI Backend: ✅ Port 8000
  Agent Factory API: ✅ Port 8090
  Static UI Server: ✅ Port 8085

WebSocket: ✅ ws://localhost:8000/ws
```

## 🎯 UI Consolidation Actions

Based on ChatGPT's recommendations:

1. **✅ Keep `webui/` as canonical UI** - This is the proper structure
2. **✅ Remove scattered UI files** - Already cleaned up
3. **✅ MCP URLs from environment** - Configured in backend
4. **✅ Single backend for all UI** - `webui/backend/main.py`
5. **⏳ Artemis UI in artemis-cli** - Keep separate (sidecar pattern)

## 🚦 Makefile Targets for UI

Add these to Makefile:
```makefile
ui-up: ## Start WebUI backend
	cd webui/backend && python3 main.py &

ui-health: ## Check UI health
	@curl -sf http://localhost:8000/health && echo "✅ WebUI healthy"

ui-smoke: ## Run UI smoke tests
	@curl -sf http://localhost:8000/health
	@curl -sf -X POST http://localhost:8000/tools/invoke \
		-H "Content-Type: application/json" \
		-d '{"capability":"fs","scope":"sophia","action":"list","params":{"path":"."}}' \
		| jq -e '.result' > /dev/null && echo "✅ UI smoke test passed"

ui-down: ## Stop UI services
	@pkill -f "python.*webui/backend/main.py" || true
```

## 🔒 Production Considerations

### 1. Reverse Proxy (nginx/traefik)
```nginx
server {
    listen 443 ssl http2;
    server_name sophia.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Authentication
- Add JWT middleware to FastAPI
- Integrate with your auth provider
- Protect all `/api` and `/tools` endpoints

### 3. CORS Configuration
```python
# In webui/backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sophia.yourdomain.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Monitoring
- Add OpenTelemetry instrumentation
- Export metrics to Prometheus
- Log aggregation with Loki

## ✅ Validation Checklist

- [x] Infrastructure running (Redis, Postgres, Weaviate)
- [x] MCP servers healthy (Memory, FS, Git)
- [x] WebUI backend running (Port 8000)
- [x] Health endpoint responding
- [x] Tool invocation working
- [x] WebSocket connection active
- [x] Agent API functional
- [x] Frontend served correctly
- [ ] Artemis integration (optional)
- [ ] Production reverse proxy (later)

## 🎉 Summary

The UI architecture is **correctly structured** with:
- Single canonical webui directory
- FastAPI backend with MCP proxy
- Static frontend files
- WebSocket support
- Proper separation from Artemis

**Everything is running and validated!** The system is ready for development and can be easily deployed to production with the additions noted above.