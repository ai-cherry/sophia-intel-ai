# Sophia UI Integration & Testing Guide

## 🎯 UI Components Status

### ✅ Available UI Components

1. **Agent Factory Dashboard** 
   - Location: `app/agents/ui/agent_factory_dashboard.html`
   - Purpose: Manage AI agents and teams
   - Status: Static HTML (needs backend connection)

2. **Factory UI Dashboard**
   - Location: `app/factory/ui/agent_factory_dashboard.html`
   - Purpose: Agent creation and configuration
   - Status: Static HTML

3. **Agno Teams Integration**
   - Location: `app/swarms/agno_teams.py`
   - Purpose: Agno-based agent swarms
   - Status: Python module (needs API wrapper)

## 🔧 Complete Integration Setup

### Step 1: Create Unified API Server

```python
# Save as: app/api/ui_backend.py
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

app = FastAPI(title="Sophia UI Backend")

# CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8085", "http://localhost:8086"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent Registry
agents = {
    "scout": {"id": "scout", "name": "Scout Agent", "status": "ready", "type": "reconnaissance"},
    "analyst": {"id": "analyst", "name": "Data Analyst", "status": "ready", "type": "analysis"},
    "coordinator": {"id": "coordinator", "name": "Team Coordinator", "status": "ready", "type": "orchestration"},
    "coder": {"id": "coder", "name": "Code Generator", "status": "ready", "type": "development"},
}

# Swarm configurations
swarms = {
    "agno": {
        "id": "agno",
        "name": "Agno Swarm",
        "agents": ["scout", "analyst", "coordinator"],
        "status": "ready"
    },
    "dev": {
        "id": "dev",
        "name": "Development Swarm",
        "agents": ["coder", "analyst"],
        "status": "ready"
    }
}

@app.get("/")
async def root():
    return {"service": "Sophia UI Backend", "version": "1.0.0"}

@app.get("/api/agents")
async def get_agents():
    """List all available agents"""
    return {"agents": list(agents.values())}

@app.post("/api/agents")
async def create_agent(agent: Dict[str, Any]):
    """Create a new agent"""
    agent_id = agent.get("id", f"agent_{len(agents)}")
    agents[agent_id] = {
        "id": agent_id,
        "name": agent.get("name", "New Agent"),
        "status": "initializing",
        "type": agent.get("type", "generic")
    }
    return agents[agent_id]

@app.get("/api/swarms")
async def get_swarms():
    """List all swarms"""
    return {"swarms": list(swarms.values())}

@app.post("/api/swarms/{swarm_id}/execute")
async def execute_swarm(swarm_id: str, task: Dict[str, Any]):
    """Execute a swarm task"""
    if swarm_id not in swarms:
        raise HTTPException(404, f"Swarm {swarm_id} not found")
    
    return {
        "task_id": f"task_{asyncio.get_event_loop().time()}",
        "swarm_id": swarm_id,
        "status": "executing",
        "task": task
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send periodic status updates
            await asyncio.sleep(5)
            await websocket.send_json({
                "type": "status",
                "agents": list(agents.values()),
                "timestamp": asyncio.get_event_loop().time()
            })
    except:
        pass

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents_count": len(agents), "swarms_count": len(swarms)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

### Step 2: Create Enhanced UI with Backend Connection

```html
<!-- Save as: app/ui/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sophia AI Command Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f1f5f9;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #334155;
        }
        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status { 
            position: absolute; 
            top: 20px; 
            right: 20px;
            padding: 10px 20px;
            background: #22c55e;
            border-radius: 20px;
            font-weight: 600;
        }
        .status.offline { background: #ef4444; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .agent-name { font-size: 1.2em; font-weight: 600; margin-bottom: 10px; }
        .agent-type { color: #94a3b8; font-size: 0.9em; }
        .agent-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-top: 10px;
            background: #22c55e;
        }
        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 20px;
        }
        button:hover { background: #1d4ed8; }
    </style>
</head>
<body>
    <div class="status" id="connection-status">Offline</div>
    <div class="container">
        <div class="header">
            <h1>Sophia AI Command Center</h1>
            <p>Agent Factory & Swarm Orchestration</p>
        </div>
        
        <div class="controls">
            <button onclick="fetchAgents()">Refresh Agents</button>
            <button onclick="createAgent()">Create Agent</button>
            <button onclick="executeSwarm()">Execute Swarm</button>
        </div>

        <div class="grid" id="agents-grid">
            <!-- Agents will be loaded here -->
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8090';
        let ws = null;

        async function fetchAgents() {
            try {
                const response = await fetch(`${API_BASE}/api/agents`);
                const data = await response.json();
                displayAgents(data.agents);
                updateStatus('Online');
            } catch (error) {
                console.error('Failed to fetch agents:', error);
                updateStatus('Offline');
            }
        }

        function displayAgents(agents) {
            const grid = document.getElementById('agents-grid');
            grid.innerHTML = agents.map(agent => `
                <div class="card">
                    <div class="agent-name">${agent.name}</div>
                    <div class="agent-type">Type: ${agent.type}</div>
                    <div class="agent-status">${agent.status}</div>
                </div>
            `).join('');
        }

        async function createAgent() {
            const name = prompt('Agent name:');
            if (!name) return;
            
            try {
                const response = await fetch(`${API_BASE}/api/agents`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, type: 'custom'})
                });
                const agent = await response.json();
                console.log('Created agent:', agent);
                fetchAgents();
            } catch (error) {
                console.error('Failed to create agent:', error);
            }
        }

        async function executeSwarm() {
            try {
                const response = await fetch(`${API_BASE}/api/swarms/agno/execute`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task: 'analyze', data: 'test'})
                });
                const result = await response.json();
                alert(`Swarm executing: ${result.task_id}`);
            } catch (error) {
                console.error('Failed to execute swarm:', error);
            }
        }

        function updateStatus(status) {
            const elem = document.getElementById('connection-status');
            elem.textContent = status;
            elem.className = status === 'Online' ? 'status' : 'status offline';
        }

        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8090/ws');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'status') {
                    displayAgents(data.agents);
                }
            };
            ws.onopen = () => updateStatus('Online');
            ws.onclose = () => {
                updateStatus('Offline');
                setTimeout(connectWebSocket, 5000);
            };
        }

        // Initialize
        fetchAgents();
        connectWebSocket();
    </script>
</body>
</html>
```

### Step 3: Start Everything

```bash
# Terminal 1: Start backend API
cd ~/sophia-intel-ai
python3 app/api/ui_backend.py

# Terminal 2: Start UI server
cd ~/sophia-intel-ai/app/ui
python3 -m http.server 8085

# Access UI at: http://localhost:8085
```

## 🧪 Integration Tests

### Test 1: API Connectivity
```bash
# Test agents endpoint
curl http://localhost:8090/api/agents

# Test health check
curl http://localhost:8090/health

# Expected: JSON responses with agent data
```

### Test 2: WebSocket Connection
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8090/ws');
ws.onmessage = (e) => console.log('Received:', e.data);
```

### Test 3: Create Agent via API
```bash
curl -X POST http://localhost:8090/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "type": "test"}'
```

### Test 4: Execute Swarm
```bash
curl -X POST http://localhost:8090/api/swarms/agno/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "analyze", "target": "test data"}'
```

## ✅ Feature Checklist

- [x] Agent listing and status display
- [x] Agent creation interface
- [x] Swarm execution triggers
- [x] Real-time WebSocket updates
- [x] Health monitoring
- [x] CORS configuration for UI access
- [ ] Authentication (needs JWT integration)
- [ ] Persistent storage (needs database)
- [ ] Task history and logs
- [ ] Advanced swarm configuration

## 🔌 Required Services

For full functionality, ensure these are running:

```bash
# Check infrastructure
docker ps | grep sophia

# Should see:
# - sophia-redis (6379)
# - sophia-postgres (5432)
# - sophia-weaviate (8080)

# Check MCP servers (if needed)
make mcp-test
```

## 🚀 Quick Test Command

```bash
# One command to test everything
curl -s http://localhost:8090/health && \
curl -s http://localhost:8090/api/agents | jq '.agents | length' && \
echo "✅ UI Backend is working!"
```

## 📝 Notes

- The current UI is functional but needs database persistence
- WebSocket provides real-time updates every 5 seconds
- CORS is configured for localhost development
- Production deployment needs authentication added