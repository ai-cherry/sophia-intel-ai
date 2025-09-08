"""
MCP Hub Gateway - Routes requests to appropriate servers
No mocks, real routing only
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="MCP Hub Gateway")

# Load configuration
with open("hub_config.json") as f:
    config = json.load(f)

class Query(BaseModel):
    text: str
    capability: Optional[str] = None
    context: dict = {}

class ServerStatus(BaseModel):
    name: str
    status: str
    port: int
    last_check: str

# Track server health
server_health = {}

async def check_server_health(server: dict) -> bool:
    """Check if a server is healthy"""
    try:
        url = f"http://{server['host']}:{server['port']}{server['health_endpoint']}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 200:
                    server_health[server['name']] = {
                        'status': 'healthy',
                        'last_check': datetime.utcnow().isoformat()
                    }
                    return True
    except:

    server_health[server['name']] = {
        'status': 'unhealthy',
        'last_check': datetime.utcnow().isoformat()
    }
    return False

async def periodic_health_check():
    """Periodically check all servers"""
    while True:
        for server in config['servers']:
            await check_server_health(server)
        await asyncio.sleep(config['monitoring']['health_check_interval'])

@app.on_event("startup")
async def startup():
    """Start health monitoring"""
    asyncio.create_task(periodic_health_check())

@app.get("/health")
async def health():
    """Hub health check"""
    return {
        "status": "healthy",
        "hub": "mcp_hub_gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "actual_mode": False
    }

@app.get("/servers/status")
async def get_servers_status():
    """Get status of all MCP servers"""
    statuses = []
    for server in config['servers']:
        status = server_health.get(server['name'], {'status': 'unknown', 'last_check': 'never'})
        statuses.append({
            'name': server['name'],
            'port': server['port'],
            'status': status['status'],
            'last_check': status['last_check'],
            'requires_api_key': server.get('requires_api_key', False)
        })
    return {"servers": statuses, "timestamp": datetime.utcnow().isoformat()}

@app.post("/route")
async def route_query(query: Query):
    """Route query to appropriate server based on capability"""

    # Find servers with matching capability
    matching_servers = []
    for server in config['servers']:
        if query.capability in server.get('capabilities', []):
            if server_health.get(server['name'], {}).get('status') == 'healthy':
                matching_servers.append(server)

    if not matching_servers:
        return {
            "error": f"No healthy servers for capability: {query.capability}",
            "available_capabilities": list(set(
                cap for s in config['servers'] 
                for cap in s.get('capabilities', [])
            ))
        }

    # Route to first matching server (can implement load balancing later)
    server = matching_servers[0]

    try:
        url = f"http://{server['host']}:{server['port']}/query"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=query.dict(), timeout=aiohttp.ClientTimeout(total=server['timeout'])) as response:
                result = await response.json()
                result['routed_to'] = server['name']
                return result
    except Exception as e:
        return {
            "error": f"Failed to route to {server['name']}: {str(e)}",
            "mock": False
        }

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Hub Gateway on port 8000")
    uvicorn.run(app, host="${BIND_IP}", port=8000)
