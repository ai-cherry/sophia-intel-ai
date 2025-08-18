from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import requests
import os
import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
import hashlib

app = FastAPI(title="SOPHIA MCP Server")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key"""
    expected_key = os.getenv("MCP_API_KEY", "sophia-mcp-secret")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/mcp/{tool}")
@limiter.limit("100/minute")
async def mcp_proxy(
    request: Request,
    tool: str, 
    data: dict, 
    api_key: str = Depends(verify_api_key)
):
    """MCP proxy with rate limiting, auth, and caching"""
    try:
        # Tool configurations
        tools = {
            "notion": {
                "url": "https://api.notion.com/v1",
                "key": os.getenv("NOTION_API_KEY"),
                "headers": {
                    "Authorization": f"Bearer {os.getenv('NOTION_API_KEY')}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                }
            },
            "salesforce": {
                "url": "https://api.salesforce.com/services/data/v60.0",
                "key": os.getenv("SALESFORCE_ACCESS_TOKEN"),
                "headers": {
                    "Authorization": f"Bearer {os.getenv('SALESFORCE_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                }
            },
            "slack": {
                "url": "https://slack.com/api",
                "key": os.getenv("SLACK_API_TOKEN"),
                "headers": {
                    "Authorization": f"Bearer {os.getenv('SLACK_API_TOKEN')}",
                    "Content-Type": "application/json"
                }
            }
        }
        
        if tool not in tools:
            raise HTTPException(status_code=400, detail="Unsupported tool")
        
        tool_config = tools[tool]
        if not tool_config["key"]:
            raise HTTPException(status_code=503, detail=f"{tool} API key not configured")
        
        # Generate cache key
        cache_key = f"mcp:{tool}:{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()}"
        
        # Check cache
        try:
            redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info(f"MCP cache hit: {tool}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
        
        # Make API request
        endpoint = data.get("endpoint", "")
        payload = data.get("payload", {})
        method = data.get("method", "POST").upper()
        
        url = f"{tool_config['url']}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=tool_config["headers"], params=payload)
        elif method == "POST":
            response = requests.post(url, headers=tool_config["headers"], json=payload)
        elif method == "PUT":
            response = requests.put(url, headers=tool_config["headers"], json=payload)
        elif method == "DELETE":
            response = requests.delete(url, headers=tool_config["headers"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported HTTP method")
        
        response.raise_for_status()
        response_data = response.json()
        
        # Cache successful responses
        try:
            await redis_client.setex(cache_key, 3600, json.dumps(response_data))
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")
        
        logger.info(f"MCP request to {tool}: {endpoint}")
        return response_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"MCP request failed: {e}")
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")
    except Exception as e:
        logger.error(f"MCP proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/health")
async def mcp_health():
    """Health check for MCP server"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "supported_tools": ["notion", "salesforce", "slack"]
    }

@app.get("/mcp/stats")
async def mcp_stats(api_key: str = Depends(verify_api_key)):
    """Get MCP usage statistics"""
    try:
        redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
        
        # Get cache statistics
        cache_keys = await redis_client.keys("mcp:*")
        cache_stats = {
            "total_cached_requests": len(cache_keys),
            "cache_keys_by_tool": {}
        }
        
        for key in cache_keys:
            tool = key.split(":")[1]
            if tool not in cache_stats["cache_keys_by_tool"]:
                cache_stats["cache_keys_by_tool"][tool] = 0
            cache_stats["cache_keys_by_tool"][tool] += 1
        
        return {
            "status": "ok",
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

