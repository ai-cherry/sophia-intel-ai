"""
Sophia AI Main Application with WebSocket Support
Real-time chat interface with MCP backend integration
NO MOCK DATA - Production WebSocket server
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.factory_ai.swarm_wrapper import FactoryMCPSwarm
from app.mcp.revenue_ops_gateway import RevenueOpsGateway
from app.mcp.server_template import SophiaMCPServer
from app.memory.bus import UnifiedMemoryBus
from app.observability.metrics import MetricsCollector
from app.observability.otel import setup_telemetry
from app.websocket.chat_handler import SophiaChatHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global components
memory_bus: UnifiedMemoryBus = None
mcp_server: SophiaMCPServer = None
revenue_ops: RevenueOpsGateway = None
factory_swarm: FactoryMCPSwarm = None
chat_handler: SophiaChatHandler = None
metrics_collector: MetricsCollector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global memory_bus, mcp_server, revenue_ops, factory_swarm, chat_handler, metrics_collector

    logger.info("🔥 Starting Sophia AI WebSocket Server...")

    try:
        # Initialize observability
        setup_telemetry()

        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        await metrics_collector.initialize()

        # Initialize unified memory bus
        logger.info("Initializing Unified Memory Bus...")
        memory_bus = UnifiedMemoryBus()
        await memory_bus.initialize()

        # Initialize MCP server
        logger.info("Initializing MCP Server...")
        mcp_server = SophiaMCPServer(memory_bus=memory_bus)
        await mcp_server.initialize()

        # Initialize Revenue Ops Gateway
        logger.info("Initializing Revenue Ops Gateway...")
        revenue_ops = RevenueOpsGateway(memory_bus=memory_bus)
        await revenue_ops.initialize()

        # Initialize Factory AI Swarm
        logger.info("Initializing Factory AI Swarm...")
        factory_swarm = FactoryMCPSwarm()
        await factory_swarm.initialize()

        # Initialize chat handler
        logger.info("Initializing Chat Handler...")
        chat_handler = SophiaChatHandler(
            memory_bus=memory_bus,
            mcp_server=mcp_server,
            revenue_ops=revenue_ops,
            factory_swarm=factory_swarm,
        )

        logger.info("✅ Sophia AI WebSocket Server initialized successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to initialize Sophia AI: {e}")
        raise

    finally:
        # Cleanup
        logger.info("🔄 Shutting down Sophia AI...")

        try:
            if factory_swarm:
                await factory_swarm.shutdown()

            if revenue_ops:
                await revenue_ops.shutdown()

            if mcp_server:
                await mcp_server.shutdown()

            if memory_bus:
                await memory_bus.shutdown()

            if metrics_collector:
                await metrics_collector.shutdown()

            logger.info("✅ Sophia AI shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Sophia AI WebSocket Server",
    description="Real-time business intelligence chat interface with MCP backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


# Dependency to get chat handler
def get_chat_handler() -> SophiaChatHandler:
    if chat_handler is None:
        raise HTTPException(status_code=503, detail="Chat handler not initialized")
    return chat_handler


# Dependency to get memory bus
def get_memory_bus() -> UnifiedMemoryBus:
    if memory_bus is None:
        raise HTTPException(status_code=503, detail="Memory bus not initialized")
    return memory_bus


# Dependency to get MCP server
def get_mcp_server() -> SophiaMCPServer:
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    return mcp_server


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    """WebSocket endpoint for real-time chat"""
    if chat_handler is None:
        await websocket.close(code=1011, reason="Server not ready")
        return

    session_id = None

    try:
        # Connect WebSocket
        session_id = await chat_handler.connect(websocket, user_id)

        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle message
                await chat_handler.handle_message(session_id, message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from WebSocket: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": f"Message handling error: {str(e)}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        # Disconnect
        if session_id:
            await chat_handler.disconnect(session_id)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check component health
        components = {}

        if memory_bus:
            components["memory_bus"] = "operational"
        else:
            components["memory_bus"] = "not_initialized"

        if mcp_server:
            components["mcp_server"] = "operational"
        else:
            components["mcp_server"] = "not_initialized"

        if revenue_ops:
            components["revenue_ops"] = "operational"
        else:
            components["revenue_ops"] = "not_initialized"

        if factory_swarm:
            components["factory_swarm"] = "operational"
        else:
            components["factory_swarm"] = "not_initialized"

        if chat_handler:
            components["chat_handler"] = "operational"
            session_stats = chat_handler.get_session_stats()
        else:
            components["chat_handler"] = "not_initialized"
            session_stats = {}

        # Determine overall status
        if all(status == "operational" for status in components.values()):
            overall_status = "healthy"
        elif any(status == "operational" for status in components.values()):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "session_stats": session_stats,
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        metrics = {}

        if memory_bus:
            memory_metrics = await memory_bus.get_metrics()
            metrics.update(memory_metrics)

        if mcp_server:
            mcp_metrics = await mcp_server.get_metrics()
            metrics.update(mcp_metrics)

        if chat_handler:
            session_stats = chat_handler.get_session_stats()
            metrics.update(session_stats)

        return {"metrics": metrics, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return JSONResponse(
            status_code=500, content={"error": str(e), "timestamp": datetime.now().isoformat()}
        )


# Chat agents endpoint
@app.get("/chat/agents")
async def get_chat_agents():
    """Get available chat agents"""
    agents = [
        {
            "id": "all",
            "name": "All Agents",
            "description": "Comprehensive business intelligence across all domains",
            "capabilities": ["analysis", "insights", "recommendations"],
        },
        {
            "id": "sales_coach",
            "name": "Sales Coach",
            "description": "Pipeline optimization, deal coaching, revenue insights",
            "capabilities": ["pipeline_analysis", "deal_coaching", "revenue_forecasting"],
        },
        {
            "id": "customer_support_coach",
            "name": "Support Coach",
            "description": "Support efficiency, customer satisfaction, team coaching",
            "capabilities": ["support_optimization", "satisfaction_analysis", "team_coaching"],
        },
        {
            "id": "client_health",
            "name": "Client Health",
            "description": "Account health monitoring, retention analysis, risk alerts",
            "capabilities": ["health_scoring", "retention_analysis", "risk_detection"],
        },
        {
            "id": "product_strategist",
            "name": "Product Strategist",
            "description": "Feature analysis, roadmap insights, user feedback synthesis",
            "capabilities": ["feature_analysis", "roadmap_planning", "feedback_synthesis"],
        },
        {
            "id": "database_master",
            "name": "Database Master",
            "description": "Data analysis, query optimization, federated search",
            "capabilities": ["data_analysis", "query_optimization", "federated_search"],
        },
        {
            "id": "ceo_coach",
            "name": "CEO Coach",
            "description": "Executive insights, strategic analysis, Pay Ready intelligence",
            "capabilities": ["executive_insights", "strategic_analysis", "business_intelligence"],
        },
    ]

    return {"agents": agents, "total_count": len(agents), "timestamp": datetime.now().isoformat()}


# HTTP chat endpoint (fallback)
@app.post("/chat/message")
async def send_chat_message(message: Dict, handler: SophiaChatHandler = Depends(get_chat_handler)):
    """HTTP endpoint for chat messages (fallback when WebSocket unavailable)"""
    try:
        user_message = message.get("message", "").strip()
        agent = message.get("agent", "all")
        context = message.get("context", {})

        if not user_message:
            raise HTTPException(status_code=400, detail="Empty message")

        # Route to appropriate agent handler
        if agent in handler.agent_handlers:
            response = await handler.agent_handlers[agent](user_message, context)
        else:
            response = await handler._handle_all_agents(user_message, context)

        return {
            "success": True,
            "agent": agent,
            "response": response["content"],
            "metadata": response.get("metadata", {}),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"HTTP chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP tools endpoint
@app.get("/mcp/tools/list")
async def list_mcp_tools(server: SophiaMCPServer = Depends(get_mcp_server)):
    """List available MCP tools"""
    try:
        tools = await server.list_tools()
        return tools
    except Exception as e:
        logger.error(f"MCP tools list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP tool call endpoint
@app.post("/mcp/tools/call")
async def call_mcp_tool(request: Dict, server: SophiaMCPServer = Depends(get_mcp_server)):
    """Call MCP tool"""
    try:
        result = await server.call_tool(request)
        return result
    except Exception as e:
        logger.error(f"MCP tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sophia AI WebSocket Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "websocket": "/ws",
            "health": "/health",
            "metrics": "/metrics",
            "chat_agents": "/chat/agents",
            "chat_message": "/chat/message",
            "mcp_tools": "/mcp/tools/list",
            "mcp_call": "/mcp/tools/call",
        },
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "${BIND_IP}")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"🚀 Starting Sophia AI WebSocket Server on {host}:{port}")

    uvicorn.run(
        "app.main_websocket:app",
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        log_level="info",
    )
