#!/usr/bin/env python3
"""
Minimal MCP Server for Integration Verification
Port: 8000 (as requested)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket
import uvicorn

# In-memory storage for demo purposes
memory_store = []
workspace_context = {
    "current_project": "sophia-intel-ai",
    "active_files": [],
    "recent_changes": []
}

async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "MCP Verification Server", 
        "port": 8000,
        "timestamp": datetime.now().isoformat(),
        "mcp_protocol": "1.0",
        "capabilities": [
            "memory_storage",
            "memory_search", 
            "workspace_sync",
            "cross_tool_context"
        ]
    })

async def store_memory(request):
    """Store memory endpoint"""
    try:
        data = await request.json()
        memory_entry = {
            "id": len(memory_store) + 1,
            "content": data.get("content", ""),
            "metadata": data.get("metadata", {}),
            "timestamp": datetime.now().isoformat(),
            "source": data.get("source", "unknown")
        }
        memory_store.append(memory_entry)
        
        return JSONResponse({
            "success": True,
            "memory_id": memory_entry["id"],
            "stored_at": memory_entry["timestamp"]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

async def search_memory(request):
    """Search memory endpoint"""
    try:
        query_params = dict(request.query_params)
        query = query_params.get("q", "")
        
        # Simple search implementation
        results = []
        for entry in memory_store:
            if query.lower() in entry["content"].lower():
                results.append(entry)
        
        return JSONResponse({
            "success": True,
            "query": query,
            "results": results[-10:],  # Return last 10 matches
            "total_found": len(results)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

async def get_workspace_context(request):
    """Get current workspace context"""
    return JSONResponse({
        "success": True,
        "context": workspace_context,
        "memory_entries": len(memory_store)
    })

async def mcp_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MCP communication"""
    await websocket.accept()
    
    # Send welcome message
    await websocket.send_json({
        "type": "connection_established",
        "server": "MCP Verification Server",
        "capabilities": ["memory", "workspace", "sync"],
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        while True:
            # Listen for messages from MCP clients
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")
            
            if message_type == "memory_store":
                # Store memory from client
                memory_entry = {
                    "id": len(memory_store) + 1,
                    "content": data.get("content", ""),
                    "metadata": data.get("metadata", {}),
                    "timestamp": datetime.now().isoformat(),
                    "source": data.get("source", "websocket")
                }
                memory_store.append(memory_entry)
                
                await websocket.send_json({
                    "type": "memory_stored",
                    "memory_id": memory_entry["id"],
                    "success": True
                })
                
            elif message_type == "memory_search":
                # Search memory for client
                query = data.get("query", "")
                results = [entry for entry in memory_store if query.lower() in entry["content"].lower()]
                
                await websocket.send_json({
                    "type": "memory_results",
                    "query": query,
                    "results": results[-5:],  # Last 5 matches
                    "total": len(results)
                })
                
            elif message_type == "workspace_sync":
                # Sync workspace context
                if "context" in data:
                    workspace_context.update(data["context"])
                
                await websocket.send_json({
                    "type": "workspace_synced",
                    "context": workspace_context
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Define routes
routes = [
    Route("/healthz", health_check, methods=["GET"]),
    Route("/health", health_check, methods=["GET"]),
    Route("/api/memory/store", store_memory, methods=["POST"]),
    Route("/api/memory/search", search_memory, methods=["GET"]),
    Route("/api/workspace/context", get_workspace_context, methods=["GET"]),
    WebSocketRoute("/ws/mcp", mcp_websocket_endpoint),
]

# Create Starlette app
app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    print("🚀 Starting MCP Verification Server on port 8000...")
    print("📡 MCP Protocol: 1.0")
    print("🔍 Endpoints:")
    print("   Health: http://localhost:8000/healthz")
    print("   Memory Store: http://localhost:8000/api/memory/store")
    print("   Memory Search: http://localhost:8000/api/memory/search")
    print("   WebSocket: ws://localhost:8000/ws/mcp")
    
    uvicorn.run(
        "mcp_verification_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )