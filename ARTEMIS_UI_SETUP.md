# Artemis UI Setup Guide

## 🎯 Overview

The Artemis Command Center UI is a React-based interface for managing AI agents and swarms. It's currently located in the Sophia repository but should eventually move to the artemis-cli sidecar.

## 📍 Current Location

```
sophia-intel-ai/
└── app/swarms/artemis/
    ├── command_center_ui.tsx    # Main UI component
    ├── components/               # UI components
    ├── military_orchestrator.py  # Backend orchestrator
    └── portkey_swarm_orchestrator.py
```

## 🚀 Quick Start

### Option 1: Run Artemis UI from Sophia (Current Setup)

#### Step 1: Install Frontend Dependencies
```bash
cd ~/sophia-intel-ai

# Install Node.js dependencies if not present
npm install react react-dom @radix-ui/react-* lucide-react
```

#### Step 2: Build the UI
```bash
# Create a simple HTML wrapper
cat > app/swarms/artemis/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artemis Command Center</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        body { margin: 0; font-family: system-ui, -apple-system, sans-serif; }
        #root { min-height: 100vh; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel" src="command_center_ui.tsx"></script>
</body>
</html>
EOF
```

#### Step 3: Start a Simple Server
```bash
# Using Python's built-in server
cd app/swarms/artemis
python3 -m http.server 8085

# UI will be available at: http://localhost:8085
```

### Option 2: Run with FastAPI Backend

#### Step 1: Create API Server
```bash
cat > app/swarms/artemis/ui_server.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

app = FastAPI(title="Artemis Command Center")

# Mount static files
static_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def get_ui():
    """Serve the main UI"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    raise HTTPException(404, "UI not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "artemis-ui"}

@app.get("/api/agents")
async def get_agents():
    """Get available agents"""
    return {
        "agents": [
            {"id": "scout", "name": "Scout Agent", "status": "ready"},
            {"id": "analyst", "name": "Analyst Agent", "status": "ready"},
            {"id": "coordinator", "name": "Coordinator", "status": "ready"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085)
EOF
```

#### Step 2: Run the Server
```bash
cd ~/sophia-intel-ai
python3 app/swarms/artemis/ui_server.py

# Access at: http://localhost:8085
```

### Option 3: Docker Container for UI

#### Step 1: Create Dockerfile
```bash
cat > app/swarms/artemis/Dockerfile.ui << 'EOF'
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8085
CMD ["nginx", "-g", "daemon off;"]
EOF
```

#### Step 2: Build and Run
```bash
cd app/swarms/artemis
docker build -f Dockerfile.ui -t artemis-ui .
docker run -d -p 8085:8085 --name artemis-ui artemis-ui
```

## 🔧 Connecting to Backend Services

The Artemis UI needs to connect to:

1. **Portkey Orchestrator** (Port 8090)
```python
# Already in portkey_swarm_orchestrator.py
python3 app/swarms/artemis/portkey_swarm_orchestrator.py
```

2. **MCP Servers** (Memory, Filesystem, Git)
```bash
# These should be running via docker-compose
make mcp-test  # Verify they're up
```

3. **Agent Factory** (Port 8091)
```python
# Start the agent factory
python3 app/swarms/artemis/agent_factory.py
```

## 🎨 UI Features

The Artemis Command Center includes:

- **Agent Management**: Create, configure, and monitor agents
- **Swarm Orchestration**: Coordinate multi-agent swarms
- **Task Routing**: Route tasks to appropriate agents
- **Real-time Monitoring**: Live status updates via WebSocket
- **Memory Interface**: Access shared memory system
- **Code Generation**: AI-powered code creation tools

## 🔌 API Endpoints

The UI expects these endpoints:

```javascript
// Agent endpoints
GET  /api/agents          // List all agents
POST /api/agents          // Create new agent
GET  /api/agents/{id}     // Get agent details
PUT  /api/agents/{id}     // Update agent
DELETE /api/agents/{id}   // Remove agent

// Swarm endpoints  
GET  /api/swarms          // List swarms
POST /api/swarms          // Create swarm
POST /api/swarms/{id}/execute  // Execute swarm task

// Task endpoints
POST /api/tasks           // Submit new task
GET  /api/tasks/{id}      // Get task status
GET  /api/tasks/{id}/logs // Get task logs
```

## 🐛 Troubleshooting

### UI Not Loading
```bash
# Check if server is running
curl http://localhost:8085/health

# Check browser console for errors
# Open Chrome DevTools: Cmd+Option+I (Mac)
```

### Cannot Connect to Backend
```bash
# Verify backend services
docker ps | grep sophia
make mcp-test

# Check CORS settings in backend
# May need to add localhost:8085 to allowed origins
```

### Missing Dependencies
```bash
# Install React and UI libraries
npm install react react-dom lucide-react @radix-ui/react-select

# Or use CDN versions in index.html
```

## 🚧 Future Migration Plan

The Artemis UI should eventually move to the `artemis-cli` repository:

```bash
# Future structure
artemis-cli/
├── ui/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── orchestrator.py
│   └── agent_factory.py
└── docker-compose.yml
```

## 🎯 Quick Test

```bash
# 1. Start backend services
cd ~/sophia-intel-ai
bash scripts/dev.sh all

# 2. Start UI server
python3 app/swarms/artemis/ui_server.py &

# 3. Open browser
open http://localhost:8085

# You should see the Artemis Command Center interface
```

---

**Note**: The UI is currently a work in progress. Some features may not be fully connected to the backend yet.