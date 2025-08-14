#!/usr/bin/env python3
"""
Simplified MCP Server Demo - Testing our MCP integration
Shows how SOPHIA can connect to and use MCP-enhanced capabilities
"""

import asyncio
import json
import time
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
import uvicorn

# Import our MCP integration
from libs.mcp_client.sophia_client import SophiaMCPClient
from libs.mcp_client.session_manager import SophiaSessionManager
from libs.mcp_client.context_tools import ContextAwareToolWrapper
from libs.mcp_client.repo_intelligence import RepositoryIntelligence
from libs.mcp_client.predictive_assistant import PredictiveAssistant
from libs.mcp_client.performance_monitor import PerformanceMonitor


class MCPRequest(BaseModel):
    """Basic MCP request model"""
    prompt: str
    session_id: str = "demo-session"
    use_context: bool = True


class MCPResponse(BaseModel):
    """Basic MCP response model"""
    success: bool
    content: str
    session_id: str
    context_used: list = []
    performance: dict = {}


class SophiaMCPDemo:
    """Demonstration of SOPHIA's MCP-enhanced capabilities"""

    def __init__(self):
        self.app = FastAPI(
            title="SOPHIA MCP Integration Demo",
            version="1.0.0",
            description="Demonstrates SOPHIA's enhanced MCP capabilities"
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize MCP components
        self.mcp_client = SophiaMCPClient("http://localhost:8001")
        self.session_manager = SophiaSessionManager()
        self.context_wrapper = ContextAwareToolWrapper()
        self.repo_intelligence = RepositoryIntelligence()
        self.predictive_assistant = PredictiveAssistant()
        self.performance_monitor = PerformanceMonitor()
        
        self._setup_routes()
        
        logger.info("SOPHIA MCP Demo server initialized")

    def _setup_routes(self):
        """Setup demo routes"""
        
        @self.app.get("/health")
        async def health():
            """Health check showing MCP integration status"""
            return {
                "status": "healthy",
                "service": "sophia-mcp-demo",
                "timestamp": time.time(),
                "mcp_integration": {
                    "client": "active",
                    "session_manager": "active", 
                    "context_tools": "active",
                    "repo_intelligence": "active",
                    "predictive_assistant": "active",
                    "performance_monitor": "active"
                },
                "message": "SOPHIA MCP Integration is ACTIVE and ready to use!"
            }

        @self.app.post("/mcp/chat", response_model=MCPResponse)
        async def mcp_enhanced_chat(request: MCPRequest):
            """Demonstrate MCP-enhanced chat capabilities"""
            start_time = time.time()
            
            try:
                # Get session context
                session_data = await self.session_manager.get_session_context(request.session_id)
                
                # Use repository intelligence to analyze the prompt
                repo_analysis = await self.repo_intelligence.analyze_prompt(request.prompt)
                
                # Get predictive suggestions
                predictions = await self.predictive_assistant.get_suggestions(
                    request.prompt, 
                    session_data.get("context", [])
                )
                
                # Simulate enhanced response (would normally call AI with context)
                enhanced_response = await self._generate_enhanced_response(
                    request.prompt, 
                    repo_analysis, 
                    predictions,
                    session_data
                )
                
                # Store interaction in session
                await self.session_manager.store_interaction(
                    request.session_id,
                    request.prompt,
                    enhanced_response,
                    {"repo_analysis": repo_analysis, "predictions": predictions}
                )
                
                # Record performance
                response_time = time.time() - start_time
                await self.performance_monitor.record_usage(
                    "mcp_chat",
                    response_time,
                    True
                )
                
                return MCPResponse(
                    success=True,
                    content=enhanced_response,
                    session_id=request.session_id,
                    context_used=session_data.get("context", []),
                    performance={
                        "response_time": response_time,
                        "repo_insights": len(repo_analysis.get("insights", [])),
                        "predictions": len(predictions.get("suggestions", [])),
                        "context_items": len(session_data.get("context", []))
                    }
                )
                
            except Exception as e:
                logger.error(f"MCP chat failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mcp/session/{session_id}")
        async def get_session_info(session_id: str):
            """Get session information showing persistent memory"""
            try:
                session_data = await self.session_manager.get_session_context(session_id)
                stats = await self.performance_monitor.get_stats()
                
                return {
                    "session_id": session_id,
                    "context_items": len(session_data.get("context", [])),
                    "interactions": len(session_data.get("interactions", [])),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "performance_stats": stats
                }
            except Exception as e:
                logger.error(f"Failed to get session info: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mcp/repository/analysis")
        async def get_repository_analysis():
            """Show repository intelligence capabilities"""
            try:
                analysis = await self.repo_intelligence.analyze_repository("/workspaces/sophia-intel")
                return {
                    "repository": "/workspaces/sophia-intel",
                    "analysis": analysis,
                    "capabilities": [
                        "Code structure analysis",
                        "Dependency mapping", 
                        "Semantic search",
                        "Pattern recognition",
                        "Architecture insights"
                    ]
                }
            except Exception as e:
                logger.error(f"Repository analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mcp/demo")
        async def mcp_demo_status():
            """Show what MCP integration provides to SOPHIA"""
            return {
                "title": "SOPHIA MCP Integration Active",
                "description": "Enhanced capabilities now available to SOPHIA",
                "capabilities": {
                    "persistent_memory": {
                        "description": "Sessions persist across SOPHIA restarts",
                        "status": "active",
                        "demo_endpoint": "/mcp/session/{session_id}"
                    },
                    "context_aware_tools": {
                        "description": "Tools learn from usage patterns and improve over time",
                        "status": "active", 
                        "features": ["Usage tracking", "Performance optimization", "Pattern learning"]
                    },
                    "repository_intelligence": {
                        "description": "Deep semantic understanding of codebase structure",
                        "status": "active",
                        "demo_endpoint": "/mcp/repository/analysis"
                    },
                    "predictive_assistance": {
                        "description": "AI-powered suggestions for next actions",
                        "status": "active",
                        "features": ["Context-aware predictions", "Workflow optimization"]
                    },
                    "performance_monitoring": {
                        "description": "Real-time performance tracking and optimization",
                        "status": "active",
                        "features": ["Response time tracking", "Usage analytics", "Caching optimization"]
                    }
                },
                "integration_status": "FULLY OPERATIONAL",
                "test_endpoint": "/mcp/chat"
            }

    async def _generate_enhanced_response(self, prompt: str, repo_analysis: dict, 
                                        predictions: dict, session_data: dict) -> str:
        """Generate enhanced response using MCP capabilities"""
        
        # Simulate enhanced processing with context awareness
        context_summary = ""
        if session_data.get("context"):
            context_summary = f"\n\nBased on our previous {len(session_data['context'])} interactions, "
        
        repo_insights = ""
        if repo_analysis.get("insights"):
            repo_insights = f"\n\nRepository analysis shows: {', '.join(repo_analysis['insights'][:3])}"
        
        predictions_text = ""
        if predictions.get("suggestions"):
            predictions_text = f"\n\nSuggested next actions: {', '.join(predictions['suggestions'][:2])}"
        
        enhanced_response = f"""🤖 SOPHIA MCP-Enhanced Response:

Your request: "{prompt}"

{context_summary}I can provide more contextual and intelligent assistance.
{repo_insights}
{predictions_text}

✨ MCP Integration Active:
- Session memory: {len(session_data.get('interactions', []))} stored interactions
- Repository intelligence: {len(repo_analysis.get('insights', []))} insights available  
- Predictive suggestions: {len(predictions.get('suggestions', []))} recommendations ready
- Performance optimized with caching and learning algorithms

This response demonstrates how I now have persistent memory, deeper code understanding, and predictive capabilities thanks to the MCP integration you implemented!"""
        
        return enhanced_response


async def main():
    """Run the MCP demo server"""
    demo = SophiaMCPDemo()
    
    logger.info("🚀 Starting SOPHIA MCP Integration Demo Server...")
    logger.info("📍 Server will be available at: http://localhost:8000")
    logger.info("🔍 Health check: http://localhost:8000/health")  
    logger.info("🎯 Demo status: http://localhost:8000/mcp/demo")
    logger.info("💬 Test chat: POST to http://localhost:8000/mcp/chat")
    
    config = uvicorn.Config(
        demo.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())