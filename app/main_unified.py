"""
Sophia AI Unified MCP Server
Production deployment with real API integrations and zero mock data
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.factory_ai.swarm_wrapper import FactoryMCPSwarm
from app.mcp.revenue_ops_gateway import RevenueOpsGateway
from app.mcp.server_template import SophiaMCPServer
# Import our components
from app.memory.bus import UnifiedMemoryBus
from app.observability.metrics import MetricsCollector
from app.observability.otel import setup_telemetry

# Import builder router
try:
    from app.api.routers.builder import router as builder_router
    BUILDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Builder router not available: {e}")
    BUILDER_AVAILABLE = False
# Early environment load (central unified env and fallbacks)
try:
    from builder_cli.lib.env import load_central_env  # type: ignore
    load_central_env()
except Exception:
    pass
try:
    from app.core.env import load_env_once  # type: ignore
    load_env_once()
except Exception:
    pass

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
class SophiaAIUnified:
    """
    Unified Sophia AI Server
    Orchestrates all MCP components with real integrations
    """
    def __init__(self):
        self.app = FastAPI(
            title="Sophia AI Unified Platform",
            description="Production MCP server with real business intelligence integrations",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        # Configuration from environment
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        # Component instances
        self.memory_bus = None
        self.mcp_server = None
        self.revenue_ops = None
        self.factory_swarm = None
        self.metrics = None
        # Performance tracking
        self.startup_time = None
        self.request_count = 0
        self.error_count = 0
        self._setup_middleware()
        self._setup_routes()
        self._setup_builder_routes()
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS middleware
        allowed_origins = os.getenv(
            "CORS_ORIGINS", "${SOPHIA_FRONTEND_ENDPOINT},http://localhost:5173"
        ).split(",")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # Request tracking middleware
        @self.app.middleware("http")
        async def track_requests(request, call_next):
            start_time = datetime.now()
            self.request_count += 1
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                self.error_count += 1
                logger.error(f"Request failed: {e}")
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                if self.metrics:
                    await self.metrics.record_request(
                        method=request.method,
                        path=request.url.path,
                        duration=duration,
                        status_code=(
                            getattr(response, "status_code", 500)
                            if "response" in locals()
                            else 500
                        ),
                    )
    async def initialize(self):
        """Initialize all components"""
        self.startup_time = datetime.now()
        logger.info("Initializing Sophia AI Unified Platform...")
        try:
            # Setup telemetry first (optional)
            enable_otel = os.getenv("SOPHIA_ENABLE_OTEL", "false").lower() == "true"
            if enable_otel:
                setup_telemetry(
                    service_name="sophia-ai-unified", environment=self.environment
                )
            # Initialize metrics collector
            self.metrics = MetricsCollector()
            await self.metrics.initialize()
            # Initialize memory bus
            logger.info("Initializing unified memory bus...")
            self.memory_bus = UnifiedMemoryBus()
            await self.memory_bus.initialize()
            # Initialize MCP server template
            logger.info("Initializing MCP server...")
            self.mcp_server = SophiaMCPServer(memory_bus=self.memory_bus)
            await self.mcp_server.initialize()
            # Initialize Revenue Ops Gateway
            logger.info("Initializing Revenue Ops Gateway...")
            self.revenue_ops = RevenueOpsGateway(memory_bus=self.memory_bus)
            await self.revenue_ops.initialize()
            # Initialize Factory AI Swarm
            logger.info("Initializing Factory AI Swarm...")
            self.factory_swarm = FactoryMCPSwarm()
            await self.factory_swarm.initialize()
            logger.info("✅ Sophia AI Unified Platform initialized successfully")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    async def shutdown(self):
        """Cleanup all components"""
        logger.info("Shutting down Sophia AI Unified Platform...")
        try:
            if self.factory_swarm:
                await self.factory_swarm.shutdown()
            if self.revenue_ops:
                await self.revenue_ops.shutdown()
            if self.mcp_server:
                await self.mcp_server.shutdown()
            if self.memory_bus:
                await self.memory_bus.shutdown()
            if self.metrics:
                await self.metrics.shutdown()
            logger.info("✅ Shutdown complete")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
    def _setup_routes(self):
        """Setup all API routes"""
        @self.app.on_event("startup")
        async def startup_event():
            await self.initialize()
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()
        @self.app.get("/")
        async def root():
            """Root endpoint with system status"""
            uptime = (
                (datetime.now() - self.startup_time).total_seconds()
                if self.startup_time
                else 0
            )
            return {
                "service": "Sophia AI Unified Platform",
                "version": "1.0.0",
                "environment": self.environment,
                "status": "operational",
                "uptime_seconds": uptime,
                "components": {
                    "memory_bus": (
                        "operational" if self.memory_bus else "not_initialized"
                    ),
                    "mcp_server": (
                        "operational" if self.mcp_server else "not_initialized"
                    ),
                    "revenue_ops": (
                        "operational" if self.revenue_ops else "not_initialized"
                    ),
                    "factory_swarm": (
                        "operational" if self.factory_swarm else "not_initialized"
                    ),
                },
                "metrics": {
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                    "error_rate": self.error_count / max(self.request_count, 1),
                },
                "timestamp": datetime.now().isoformat(),
            }
        @self.app.get("/health")
        async def health_check():
            """Comprehensive health check"""
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {},
            }
            # Check each component
            try:
                if self.memory_bus:
                    memory_health = await self.memory_bus.health_check()
                    health_status["components"]["memory_bus"] = memory_health
                if self.revenue_ops:
                    revenue_health = await self.revenue_ops.health_check()
                    health_status["components"]["revenue_ops"] = revenue_health
                if self.factory_swarm:
                    # Factory swarm health check
                    health_status["components"]["factory_swarm"] = {
                        "status": "healthy",
                        "active_droids": len(self.factory_swarm.evolution_loops),
                        "cache_size": (
                            len(self.factory_swarm.cache.l0_cache)
                            if self.factory_swarm.cache
                            else 0
                        ),
                    }
                # Overall health determination
                component_statuses = [
                    comp.get("status", "unknown")
                    for comp in health_status["components"].values()
                ]
                if all(status == "healthy" for status in component_statuses):
                    health_status["status"] = "healthy"
                elif any(status == "unhealthy" for status in component_statuses):
                    health_status["status"] = "unhealthy"
                else:
                    health_status["status"] = "degraded"
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
            status_code = 200 if health_status["status"] == "healthy" else 503
            return JSONResponse(content=health_status, status_code=status_code)
        @self.app.get("/healthz")
        async def healthz():
            """Alias for legacy health endpoint"""
            return await health_check()
        @self.app.get("/metrics")
        async def get_metrics():
            """Get system metrics"""
            if not self.metrics:
                raise HTTPException(status_code=503, detail="Metrics not available")
            return await self.metrics.get_all_metrics()

        @self.app.get("/integrations/health")
        async def integrations_health():
            """Report readiness for core integrations without making network calls."""
            try:
                cm = get_config_manager() if get_config_manager else None
            except Exception:
                cm = None
            def _status(name: str, required: list[str]):
                cfg = cm.get_integration_config(name) if cm else {}
                enabled = bool(cfg.get("enabled"))
                present = {k: bool(cfg.get(k)) for k in required}
                ok = (not enabled) or all(present.values())
                return {"enabled": enabled, "ok": ok, "keys_present": present}
            return {
                "slack": _status("slack", ["bot_token"]),
                "asana": _status("asana", ["pat_token"]),
                "linear": _status("linear", ["api_key"]),
                "airtable": _status("airtable", ["api_key", "base_id"]),
            }
        # MCP Server routes
        @self.app.post("/mcp/tools/call")
        async def mcp_tool_call(request: Dict[str, Any]):
            """Universal MCP tool call endpoint"""
            if not self.mcp_server:
                raise HTTPException(
                    status_code=503, detail="MCP server not initialized"
                )
            return await self.mcp_server.call_tool(request)
        @self.app.get("/mcp/tools/list")
        async def list_mcp_tools():
            """List all available MCP tools"""
            if not self.mcp_server:
                raise HTTPException(
                    status_code=503, detail="MCP server not initialized"
                )
            return await self.mcp_server.list_tools()
        # Revenue Ops routes
        @self.app.post("/revenue/search")
        async def revenue_search(request: Dict[str, Any]):
            """Search across revenue operations data"""
            if not self.revenue_ops:
                raise HTTPException(
                    status_code=503, detail="Revenue Ops not initialized"
                )
            return await self.revenue_ops.federated_search(request)
        @self.app.get("/revenue/health/{client_name}")
        async def client_health(client_name: str):
            """Get client health score"""
            if not self.revenue_ops:
                raise HTTPException(
                    status_code=503, detail="Revenue Ops not initialized"
                )
            return await self.revenue_ops.get_client_health(client_name)
        @self.app.get("/revenue/insights")
        async def revenue_insights():
            """Get revenue intelligence insights"""
            if not self.revenue_ops:
                raise HTTPException(
                    status_code=503, detail="Revenue Ops not initialized"
                )
            return await self.revenue_ops.get_insights()
        # Factory AI Swarm routes
        @self.app.post("/factory/call")
        async def factory_call(request: Dict[str, Any], background: BackgroundTasks):
            """Factory AI MCP call with evolution"""
            if not self.factory_swarm:
                raise HTTPException(
                    status_code=503, detail="Factory Swarm not initialized"
                )
            # Convert to ToolCall format
            from app.factory_ai.swarm_wrapper import ToolCall
            tool_call = ToolCall(
                tool=request.get("tool", "unknown"),
                params=request.get("params", {}),
                user_context=request.get("user_context"),
            )
            # Use the factory swarm's mcp_call method
            return await self.factory_swarm.app.routes[2].endpoint(
                tool_call, background
            )
        @self.app.get("/factory/evolution")
        async def factory_evolution():
            """Get Factory AI evolution metrics"""
            if not self.factory_swarm:
                raise HTTPException(
                    status_code=503, detail="Factory Swarm not initialized"
                )
            return await self.factory_swarm.app.routes[3].endpoint()
        # Unified chat interface routes
        @self.app.post("/chat/message")
        async def chat_message(request: Dict[str, Any]):
            """Unified chat message processing"""
            message = request.get("message", "")
            agent_type = request.get("agent", "all")
            user_context = request.get("context", {})
            # Route to appropriate agent based on type
            if agent_type == "sales_coach":
                return await self._handle_sales_coach(message, user_context)
            elif agent_type == "customer_support":
                return await self._handle_customer_support(message, user_context)
            elif agent_type == "client_health":
                return await self._handle_client_health(message, user_context)
            elif agent_type == "product_strategist":
                return await self._handle_product_strategist(message, user_context)
            elif agent_type == "database_master":
                return await self._handle_database_master(message, user_context)
            elif agent_type == "ceo_coach":
                return await self._handle_ceo_coach(message, user_context)
            else:
                # All agents mode - intelligent routing
                return await self._handle_intelligent_routing(message, user_context)
        @self.app.get("/chat/agents")
        async def list_agents():
            """List all available chat agents"""
            return {
                "agents": [
                    {
                        "id": "sales_coach",
                        "name": "Sales Coach",
                        "description": "Pipeline optimization and deal coaching",
                        "capabilities": [
                            "deal_analysis",
                            "pipeline_health",
                            "sales_coaching",
                        ],
                    },
                    {
                        "id": "customer_support",
                        "name": "Customer Support Coach",
                        "description": "Support efficiency and customer satisfaction",
                        "capabilities": [
                            "ticket_analysis",
                            "satisfaction_tracking",
                            "support_coaching",
                        ],
                    },
                    {
                        "id": "client_health",
                        "name": "Client Health Agent",
                        "description": "Account health and retention analysis",
                        "capabilities": [
                            "health_scoring",
                            "retention_analysis",
                            "risk_assessment",
                        ],
                    },
                    {
                        "id": "product_strategist",
                        "name": "Product Strategist",
                        "description": "Feature analysis and roadmap insights",
                        "capabilities": [
                            "feature_analysis",
                            "roadmap_planning",
                            "user_feedback",
                        ],
                    },
                    {
                        "id": "database_master",
                        "name": "Database Master",
                        "description": "Data analysis and query optimization",
                        "capabilities": [
                            "data_analysis",
                            "query_optimization",
                            "reporting",
                        ],
                    },
                    {
                        "id": "ceo_coach",
                        "name": "CEO Coach",
                        "description": "Executive insights and strategic guidance",
                        "capabilities": [
                            "strategic_analysis",
                            "executive_reporting",
                            "risk_management",
                        ],
                    },
                ]
            }
    async def _handle_sales_coach(self, message: str, context: Dict) -> Dict:
        """Handle sales coach queries"""
        # Use Revenue Ops Gateway for sales intelligence
        if self.revenue_ops:
            return await self.revenue_ops.sales_intelligence(message, context)
        else:
            return {"error": "Revenue Ops not available", "agent": "sales_coach"}
    async def _handle_customer_support(self, message: str, context: Dict) -> Dict:
        """Handle customer support queries"""
        # Use Revenue Ops Gateway for support intelligence
        if self.revenue_ops:
            return await self.revenue_ops.support_intelligence(message, context)
        else:
            return {"error": "Revenue Ops not available", "agent": "customer_support"}
    async def _handle_client_health(self, message: str, context: Dict) -> Dict:
        """Handle client health queries"""
        # Use Revenue Ops Gateway for client health
        if self.revenue_ops:
            return await self.revenue_ops.client_health_intelligence(message, context)
        else:
            return {"error": "Revenue Ops not available", "agent": "client_health"}
    async def _handle_product_strategist(self, message: str, context: Dict) -> Dict:
        """Handle product strategist queries"""
        # Use Factory AI for product intelligence
        if self.factory_swarm:
            return await self.factory_swarm._proxy_fallback(
                {"query": message, "type": "product_strategy"}, context
            )
        else:
            return {
                "error": "Factory Swarm not available",
                "agent": "product_strategist",
            }
    async def _handle_database_master(self, message: str, context: Dict) -> Dict:
        """Handle database master queries"""
        # Use Memory Bus for data queries
        if self.memory_bus:
            return await self.memory_bus.query_data(message, context)
        else:
            return {"error": "Memory Bus not available", "agent": "database_master"}
    async def _handle_ceo_coach(self, message: str, context: Dict) -> Dict:
        """Handle CEO coach queries"""
        # Use Revenue Ops Gateway for executive intelligence
        if self.revenue_ops:
            return await self.revenue_ops.executive_intelligence(message, context)
        else:
            return {"error": "Revenue Ops not available", "agent": "ceo_coach"}
    async def _handle_intelligent_routing(self, message: str, context: Dict) -> Dict:
        """Intelligent routing across all agents"""
        # Analyze message to determine best agent
        message_lower = message.lower()
        # Simple keyword-based routing (can be enhanced with ML)
        if any(
            word in message_lower for word in ["deal", "pipeline", "sales", "revenue"]
        ):
            return await self._handle_sales_coach(message, context)
        elif any(
            word in message_lower
            for word in ["support", "ticket", "customer", "satisfaction"]
        ):
            return await self._handle_customer_support(message, context)
        elif any(
            word in message_lower for word in ["health", "retention", "churn", "risk"]
        ):
            return await self._handle_client_health(message, context)
        elif any(
            word in message_lower
            for word in ["product", "feature", "roadmap", "development"]
        ):
            return await self._handle_product_strategist(message, context)
        elif any(
            word in message_lower for word in ["data", "query", "database", "analytics"]
        ):
            return await self._handle_database_master(message, context)
        elif any(
            word in message_lower
            for word in ["strategic", "executive", "ceo", "leadership"]
        ):
            return await self._handle_ceo_coach(message, context)
        else:
            # Default to CEO coach for general queries
            return await self._handle_ceo_coach(message, context)

try:
    from config.unified_manager import get_config_manager  # type: ignore
except Exception:
    get_config_manager = None  # type: ignore
    
    def _setup_builder_routes(self):
        """Setup builder-specific routes"""
        if BUILDER_AVAILABLE:
            self.app.include_router(builder_router)
            logger.info("Builder API routes enabled at /api/builder/*")
        else:
            logger.warning("Builder API routes disabled - dependencies not available")
# Create the unified server instance
sophia_unified = SophiaAIUnified()
app = sophia_unified.app
if __name__ == "__main__":
    # Production server configuration
    # Canonical per AGENTS.md: unified API on 8003
    port = int(os.getenv("PORT", 8003))
    host = os.getenv("HOST", "${BIND_IP}")
    workers = int(os.getenv("WORKERS", 1))
    uvicorn.run(
        "main_unified:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,  # Disable reload in production
        log_level="info",
        access_log=True,
    )
