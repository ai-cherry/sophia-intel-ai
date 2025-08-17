"""
SOPHIA Intel MCP Server with Lambda Labs GH200 integration
Production-ready with authentication, lifecycle management, and monitoring
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from typing import Optional, Dict, Any
from lambda_client import LambdaLabsClient, SERVERS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOPHIA Intel MCP Server",
    description="Model Control Plane for Lambda Labs GH200 servers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
security = HTTPBearer()

def verify_token(x_mcp_token: Optional[str] = Header(None)):
    """Verify MCP authentication token"""
    if not MCP_AUTH_TOKEN:
        # Skip authentication if no token is configured (development mode)
        return True
    
    if not x_mcp_token or x_mcp_token != MCP_AUTH_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-MCP-Token header"
        )
    return True

# Initialize Lambda client with error handling
try:
    lambda_client = LambdaLabsClient()
    logger.info("Lambda Labs client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Lambda Labs client: {e}")
    lambda_client = None

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SOPHIA Intel MCP Server",
        "lambda_servers": len(SERVERS),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "lambda_client_ready": lambda_client is not None,
        "auth_enabled": MCP_AUTH_TOKEN is not None
    }

@app.get("/servers")
async def list_servers(authenticated: bool = Depends(verify_token)):
    """List all configured Lambda Labs servers"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    try:
        instances = lambda_client.get_instances()
        server_info = []
        
        for server_key, server_config in SERVERS.items():
            # Find matching instance from Lambda API
            instance_found = False
            for instance in instances.get("data", []):
                if instance["id"] == server_config["id"]:
                    server_info.append({
                        "key": server_key,
                        "id": server_config["id"],
                        "name": server_config["name"],
                        "ip": server_config["ip"],
                        "role": server_config["role"],
                        "inference_url": server_config.get("inference_url", f"http://{server_config['ip']}:8000"),
                        "status": instance["status"],
                        "instance_type": instance.get("instance_type", {}).get("name", "unknown"),
                        "region": instance.get("region", {}).get("name", "unknown")
                    })
                    instance_found = True
                    break
            
            if not instance_found:
                server_info.append({
                    "key": server_key,
                    "id": server_config["id"],
                    "name": server_config["name"],
                    "ip": server_config["ip"],
                    "role": server_config["role"],
                    "inference_url": server_config.get("inference_url", f"http://{server_config['ip']}:8000"),
                    "status": "not_found",
                    "error": "Instance not found in Lambda Labs API"
                })
        
        return {"servers": server_info, "total": len(server_info)}
    
    except Exception as e:
        logger.error(f"Failed to list servers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")

@app.post("/servers/{server_key}/start")
async def start_server(server_key: str, authenticated: bool = Depends(verify_token)):
    """Start a Lambda Labs server"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    if server_key not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Server '{server_key}' not found")
    
    try:
        server_config = SERVERS[server_key]
        result = lambda_client.start_instance(server_config["id"])
        
        logger.info(f"Started server {server_key} ({server_config['id']})")
        return {
            "server": server_key,
            "action": "start",
            "status": "success",
            "instance_id": server_config["id"],
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Failed to start server {server_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")

@app.post("/servers/{server_key}/stop")
async def stop_server(server_key: str, authenticated: bool = Depends(verify_token)):
    """Stop a Lambda Labs server"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    if server_key not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Server '{server_key}' not found")
    
    try:
        server_config = SERVERS[server_key]
        result = lambda_client.stop_instance(server_config["id"])
        
        logger.info(f"Stopped server {server_key} ({server_config['id']})")
        return {
            "server": server_key,
            "action": "stop",
            "status": "success",
            "instance_id": server_config["id"],
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Failed to stop server {server_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")

@app.post("/servers/{server_key}/restart")
async def restart_server(server_key: str, authenticated: bool = Depends(verify_token)):
    """Restart a Lambda Labs server"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    if server_key not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Server '{server_key}' not found")
    
    try:
        server_config = SERVERS[server_key]
        result = lambda_client.restart_instance(server_config["id"])
        
        logger.info(f"Restarted server {server_key} ({server_config['id']})")
        return {
            "server": server_key,
            "action": "restart",
            "status": "success",
            "instance_id": server_config["id"],
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Failed to restart server {server_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {str(e)}")

@app.get("/servers/{server_key}/stats")
async def get_server_stats(server_key: str, authenticated: bool = Depends(verify_token)):
    """Get server statistics including GPU utilization"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    if server_key not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Server '{server_key}' not found")
    
    try:
        server_config = SERVERS[server_key]
        stats = lambda_client.get_instance_stats(server_config["id"])
        
        return {
            "server": server_key,
            "stats": stats,
            "config": server_config
        }
    
    except Exception as e:
        logger.error(f"Failed to get stats for server {server_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get server stats: {str(e)}")

@app.post("/servers/rename")
async def rename_servers(authenticated: bool = Depends(verify_token)):
    """Rename Lambda Labs servers with proper naming convention"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    results = []
    
    for server_key, server_config in SERVERS.items():
        try:
            result = lambda_client.rename_instance(
                server_config["id"], 
                server_config["name"]
            )
            results.append({
                "server": server_key,
                "status": "success",
                "new_name": server_config["name"],
                "instance_id": server_config["id"]
            })
            logger.info(f"Renamed server {server_key} to {server_config['name']}")
        except Exception as e:
            logger.error(f"Failed to rename server {server_key}: {e}")
            results.append({
                "server": server_key,
                "status": "error",
                "error": str(e),
                "instance_id": server_config["id"]
            })
    
    return {"rename_results": results, "total": len(results)}

@app.get("/servers/{server_key}")
async def get_server_details(server_key: str, authenticated: bool = Depends(verify_token)):
    """Get detailed information about a specific server"""
    if not lambda_client:
        raise HTTPException(status_code=503, detail="Lambda Labs client not available")
    
    if server_key not in SERVERS:
        raise HTTPException(status_code=404, detail=f"Server '{server_key}' not found")
    
    try:
        server_config = SERVERS[server_key]
        instance = lambda_client.get_instance(server_config["id"])
        stats = lambda_client.get_instance_stats(server_config["id"])
        
        return {
            "server": server_key,
            "config": server_config,
            "instance": instance,
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"Failed to get details for server {server_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get server details: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=log_level,
        access_log=True
    )
