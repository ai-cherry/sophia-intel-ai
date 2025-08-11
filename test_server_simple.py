#!/usr/bin/env python3
"""
Simplified Test Server - Runs enhanced MCP server with minimal dependencies
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import test services
from config.test_config import settings
from mcp_servers.test_memory_service import TestMemoryService
from mcp_servers.ai_router import AIRouter, TaskRequest, TaskType

# Create simplified FastAPI app
app = FastAPI(
    title="Sophia Intel Enhanced MCP Server - Test Mode",
    version="2.0.0-test",
    description="Simplified test version of Enhanced MCP Server",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
memory_service = TestMemoryService()
ai_router = AIRouter()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "service": "enhanced-mcp-server-test",
        "version": "2.0.0-test",
        "components": {
            "memory_service": await memory_service.health_check(),
            "ai_router": await ai_router.health_check()
        }
    }

@app.get("/models")
async def get_models():
    """Get available AI models"""
    return await ai_router.get_model_stats()

@app.post("/context/store")
async def store_context(request: dict):
    """Store context"""
    return await memory_service.store_context(
        session_id=request["session_id"],
        content=request["content"],
        metadata=request.get("metadata", {})
    )

@app.post("/context/query")
async def query_context(request: dict):
    """Query context"""
    results = await memory_service.query_context(
        session_id=request["session_id"],
        query=request["query"],
        top_k=request.get("top_k", 5),
        threshold=request.get("threshold", 0.7)
    )
    return {
        "success": True,
        "results": results,
        "query": request["query"],
        "total_found": len(results)
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "memory_service": await memory_service.get_stats(),
        "ai_router": await ai_router.get_model_stats()
    }

@app.post("/ai/route")
async def test_ai_routing(request: dict):
    """Test AI routing functionality"""
    task_request = TaskRequest(
        prompt=request["prompt"],
        task_type=TaskType(request.get("task_type", "general_chat")),
        max_tokens=request.get("max_tokens"),
        temperature=request.get("temperature", 0.7),
        priority=request.get("priority", "normal"),
        cost_preference=request.get("cost_preference", "balanced"),
        latency_requirement=request.get("latency_requirement", "normal"),
        quality_requirement=request.get("quality_requirement", "high")
    )
    
    routing_decision = await ai_router.route_request(task_request)
    
    return {
        "success": True,
        "routing_decision": {
            "selected_provider": routing_decision.selected_provider.value,
            "selected_model": routing_decision.selected_model,
            "confidence_score": routing_decision.confidence_score,
            "reasoning": routing_decision.reasoning,
            "estimated_cost": routing_decision.estimated_cost,
            "estimated_latency": routing_decision.estimated_latency,
            "fallback_options": routing_decision.fallback_options
        }
    }

def run_test_server():
    """Run the test server"""
    print("🚀 Starting Simplified Enhanced MCP Server")
    print(f"📍 Server running on http://localhost:{settings.MCP_PORT}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print("-" * 50)
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.MCP_PORT,
        log_level="info"
    )

if __name__ == "__main__":
    try:
        run_test_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

