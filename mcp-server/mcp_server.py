"""
SOPHIA Intel MCP Server with Lambda Labs GH200 integration
"""
from fastapi import FastAPI
import uvicorn
import os
from lambda_client import LambdaLabsClient, SERVERS

app = FastAPI(
    title="SOPHIA Intel MCP Server",
    description="Model Control Plane for Lambda Labs GH200 servers",
    version="1.0.0"
)

lambda_client = LambdaLabsClient()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SOPHIA Intel MCP Server",
        "lambda_servers": len(SERVERS),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/servers")
async def list_servers():
    """List all configured Lambda Labs servers"""
    try:
        instances = lambda_client.get_instances()
        server_info = []
        
        for server_key, server_config in SERVERS.items():
            # Find matching instance from Lambda API
            for instance in instances.get("data", []):
                if instance["id"] == server_config["id"]:
                    server_info.append({
                        "key": server_key,
                        "name": server_config["name"],
                        "ip": server_config["ip"],
                        "role": server_config["role"],
                        "status": instance["status"],
                        "instance_type": instance.get("instance_type", {}).get("name", "unknown")
                    })
                    break
        
        return {"servers": server_info}
    except Exception as e:
        return {"error": str(e), "servers": []}

@app.post("/servers/rename")
async def rename_servers():
    """Rename Lambda Labs servers with proper naming convention"""
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
                "new_name": server_config["name"]
            })
        except Exception as e:
            results.append({
                "server": server_key,
                "status": "error",
                "error": str(e)
            })
    
    return {"rename_results": results}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
