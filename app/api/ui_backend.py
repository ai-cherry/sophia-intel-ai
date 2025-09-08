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
    allow_origins=["http://localhost:8085", "http://localhost:8086", "http://localhost:3000"],
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
    return {"service": "Sophia UI Backend", "version": "1.0.0", "status": "operational"}

@app.get("/api/agents")
async def get_agents():
    """List all available agents"""
    return {"agents": list(agents.values()), "count": len(agents)}

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
    # Simulate initialization
    agents[agent_id]["status"] = "ready"
    return agents[agent_id]

@app.get("/api/swarms")
async def get_swarms():
    """List all swarms"""
    return {"swarms": list(swarms.values()), "count": len(swarms)}

@app.post("/api/swarms/{swarm_id}/execute")
async def execute_swarm(swarm_id: str, task: Dict[str, Any]):
    """Execute a swarm task"""
    if swarm_id not in swarms:
        raise HTTPException(404, f"Swarm {swarm_id} not found")
    
    import time
    return {
        "task_id": f"task_{int(time.time())}",
        "swarm_id": swarm_id,
        "status": "executing",
        "task": task,
        "agents_assigned": swarms[swarm_id]["agents"]
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
                "swarms": list(swarms.values()),
                "timestamp": int(asyncio.get_event_loop().time())
            })
    except:
        pass

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "agents_count": len(agents), 
        "swarms_count": len(swarms),
        "services": {
            "agent_factory": "operational",
            "swarm_orchestrator": "operational",
            "websocket": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Sophia UI Backend on http://localhost:8090")
    print("Health check: http://localhost:8090/health")
    print("API docs: http://localhost:8090/docs")
    uvicorn.run(app, host="0.0.0.0", port=8090)