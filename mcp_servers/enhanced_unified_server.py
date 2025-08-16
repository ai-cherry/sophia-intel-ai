"""
Enhanced Unified MCP Server
Integrates AI Router, memory services, and comprehensive AI development capabilities
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger
import aiohttp
import uvicorn

from config.config import settings
from mcp_servers.memory_service import MemoryService
from mcp_servers.ai_router import AIRouter, TaskRequest, TaskType, RoutingDecision
from agents.base_agent import BaseAgent
from services.lambda_client import LambdaClient


# Request/Response Models
class AIRequest(BaseModel):
    """Enhanced AI request with routing capabilities"""
    prompt: str = Field(..., description="The prompt to send to the AI")
    task_type: TaskType = Field(
        default=TaskType.GENERAL_CHAT, description="Type of task")
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    stream: bool = Field(
        default=False, description="Whether to stream the response")
    priority: str = Field(default="normal", description="Request priority")
    cost_preference: str = Field(
        default="balanced", description="Cost optimization preference")
    latency_requirement: str = Field(
        default="normal", description="Latency requirement")
    quality_requirement: str = Field(
        default="high", description="Quality requirement")
    session_id: Optional[str] = Field(
        default=None, description="Session ID for context")
    use_context: bool = Field(
        default=True, description="Whether to use session context")
    context_query: Optional[str] = Field(
        default=None, description="Specific context query")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata")


class AIResponse(BaseModel):
    """Enhanced AI response with routing information"""
    success: bool
    content: str
    provider: str
    model: str
    routing_decision: Dict[str, Any]
    usage: Dict[str, Any]
    performance: Dict[str, Any]
    session_id: Optional[str] = None
    context_used: List[Dict[str, Any]] = []


class ContextRequest(BaseModel):
    """Context management request"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Content to store")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata")
    context_type: Optional[str] = Field(
        default="general", description="Type of context")


class ContextQueryRequest(BaseModel):
    """Context query request"""
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Query string for context search")
    top_k: int = Field(default=5, ge=1, le=20,
                       description="Number of results to return")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0,
                             description="Similarity threshold")


class AgentTaskRequest(BaseModel):
    """Agent task execution request"""
    agent_type: str = Field(..., description="Type of agent to use")
    task_data: Dict[str, Any] = Field(..., description="Task data")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    priority: str = Field(default="normal", description="Task priority")


# Enhanced Unified MCP Server
class EnhancedUnifiedMCPServer:
    """
    Enhanced MCP server that provides comprehensive AI development capabilities
    including intelligent model routing, context management, and agent orchestration.
    """

    def __init__(self):
        self.app = FastAPI(
            title="Sophia Intel Enhanced MCP Server",
            version="2.0.0",
            description="Enhanced Model Context Protocol server with AI Router and comprehensive capabilities",
        )

        # Initialize services
        self.memory_service = MemoryService()
        self.ai_router = AIRouter()
        self.lambda_client = LambdaClient()
        self.agents = {}
        self.active_sessions = {}
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "total_cost": 0.0
        }

        # Setup middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()

        # Initialize AI provider clients (will be initialized on startup)
        self.ai_clients = {}
        self.session = None
        self._initialized = False

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.get("/health")
        async def health():
            """Comprehensive health check"""
            try:
                # Check memory service
                memory_health = await self.memory_service.health_check()

                # Check AI router
                router_health = await self.ai_router.health_check()

                # Check AI providers
                provider_health = await self._check_provider_health()

                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "service": "enhanced-mcp-server",
                    "version": "2.0.0",
                    "components": {
                        "memory_service": memory_health,
                        "ai_router": router_health,
                        "providers": provider_health
                    },
                    "metrics": self.performance_metrics
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(
                    status_code=503, detail="Service unhealthy")

        @self.app.post("/ai/chat", response_model=AIResponse)
        async def ai_chat(request: AIRequest, background_tasks: BackgroundTasks):
            """Enhanced AI chat with intelligent routing"""
            start_time = time.time()

            try:
                # Update metrics
                self.performance_metrics["total_requests"] += 1

                # Get session context if requested
                context_content = ""
                context_used = []

                if request.use_context and request.session_id:
                    context_query = request.context_query or request.prompt[:100]
                    context_results = await self.memory_service.query_context(
                        session_id=request.session_id,
                        query=context_query,
                        top_k=5,
                        threshold=0.7
                    )

                    if context_results:
                        context_content = "\n".join(
                            [r.get("content", "") for r in context_results])
                        context_used = context_results

                # Prepare enhanced prompt with context
                enhanced_prompt = request.prompt
                if context_content:
                    enhanced_prompt = f"Context:\n{context_content}\n\nUser: {request.prompt}"

                # Create task request for AI router
                task_request = TaskRequest(
                    prompt=enhanced_prompt,
                    task_type=request.task_type,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    priority=request.priority,
                    cost_preference=request.cost_preference,
                    latency_requirement=request.latency_requirement,
                    quality_requirement=request.quality_requirement,
                    context=context_content,
                    metadata=request.metadata
                )

                # Get routing decision
                routing_decision = await self.ai_router.route_request(task_request)

                # Execute AI request
                ai_response = await self._execute_ai_request(
                    routing_decision,
                    enhanced_prompt,
                    request
                )

                # Store interaction in context if session provided
                if request.session_id:
                    background_tasks.add_task(
                        self._store_interaction,
                        request.session_id,
                        request.prompt,
                        ai_response["content"],
                        routing_decision
                    )

                # Record performance
                response_time = time.time() - start_time
                background_tasks.add_task(
                    self.ai_router.record_performance,
                    routing_decision.selected_provider,
                    routing_decision.selected_model,
                    True,
                    response_time,
                    routing_decision.estimated_cost
                )

                # Update metrics
                self.performance_metrics["successful_requests"] += 1
                self.performance_metrics["avg_response_time"] = (
                    (self.performance_metrics["avg_response_time"] *
                     (self.performance_metrics["successful_requests"] - 1) + response_time) /
                    self.performance_metrics["successful_requests"]
                )
                self.performance_metrics["total_cost"] += routing_decision.estimated_cost

                return AIResponse(
                    success=True,
                    content=ai_response["content"],
                    provider=routing_decision.selected_provider.value,
                    model=routing_decision.selected_model,
                    routing_decision=routing_decision.__dict__,
                    usage=ai_response.get("usage", {}),
                    performance={
                        "response_time": response_time,
                        "estimated_cost": routing_decision.estimated_cost
                    },
                    session_id=request.session_id,
                    context_used=context_used
                )

            except Exception as e:
                logger.error(f"AI chat request failed: {e}")
                self.performance_metrics["failed_requests"] += 1

                # Record failure
                if 'routing_decision' in locals():
                    await self.ai_router.record_failure(
                        routing_decision.selected_provider,
                        routing_decision.selected_model
                    )

                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/ai/stream")
        async def ai_stream(request: AIRequest):
            """Streaming AI response"""
            if not request.stream:
                raise HTTPException(
                    status_code=400, detail="Stream must be enabled for this endpoint")

            # Get routing decision
            task_request = TaskRequest(
                prompt=request.prompt,
                task_type=request.task_type,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                priority=request.priority,
                cost_preference=request.cost_preference,
                latency_requirement=request.latency_requirement,
                quality_requirement=request.quality_requirement,
                metadata=request.metadata
            )

            routing_decision = await self.ai_router.route_request(task_request)

            # Stream response
            return StreamingResponse(
                self._stream_ai_response(routing_decision, request),
                media_type="text/plain"
            )

        @self.app.post("/context/store")
        async def store_context(request: ContextRequest):
            """Store context in memory service"""
            try:
                result = await self.memory_service.store_context(
                    session_id=request.session_id,
                    content=request.content,
                    metadata={**request.metadata,
                              "context_type": request.context_type}
                )

                return {
                    "success": True,
                    "id": str(result["id"]),
                    "message": "Context stored successfully"
                }
            except Exception as e:
                logger.error(f"Failed to store context: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/context/query")
        async def query_context(request: ContextQueryRequest):
            """Query context from memory service"""
            try:
                results = await self.memory_service.query_context(
                    session_id=request.session_id,
                    query=request.query,
                    top_k=request.top_k,
                    threshold=request.threshold
                )

                return {
                    "success": True,
                    "results": results,
                    "query": request.query,
                    "total_found": len(results)
                }
            except Exception as e:
                logger.error(f"Failed to query context: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/context/session/{session_id}")
        async def clear_session_context(session_id: str):
            """Clear all context for a session"""
            try:
                result = await self.memory_service.clear_session(session_id)
                return {
                    "success": True,
                    "deleted_count": result.get("deleted_count", 0)
                }
            except Exception as e:
                logger.error(f"Failed to clear session context: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/context/search_multi_service")
        async def search_multi_service(
            session_id: str,
            query: str,
            services: Optional[str] = "memory,rag,vector",
            top_k: int = 10
        ):
            """Search across multiple services for comprehensive results"""
            try:
                service_list = services.split(",") if services else ["memory", "rag", "vector"]
                results = {}
                
                # Search memory service
                if "memory" in service_list:
                    memory_results = await self.memory_service.query_context(
                        session_id=session_id,
                        query=query,
                        top_k=top_k // len(service_list),
                        threshold=0.6
                    )
                    results["memory"] = memory_results
                
                # Search RAG pipeline (if available)
                if "rag" in service_list:
                    try:
                        # TODO: Integrate with RAG pipeline when available
                        results["rag"] = []
                    except Exception as e:
                        logger.warning(f"RAG search failed: {e}")
                        results["rag"] = []
                
                # Search vector database directly (if available)
                if "vector" in service_list:
                    try:
                        # TODO: Direct vector search when available
                        results["vector"] = []
                    except Exception as e:
                        logger.warning(f"Vector search failed: {e}")
                        results["vector"] = []
                
                # Fuse results (simple concatenation for now)
                fused_results = []
                for service, service_results in results.items():
                    for result in service_results:
                        result["source_service"] = service
                        fused_results.append(result)
                
                # Sort by relevance score if available
                fused_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                
                return {
                    "success": True,
                    "query": query,
                    "services_searched": service_list,
                    "results": fused_results[:top_k],
                    "total_found": len(fused_results),
                    "service_breakdown": {
                        service: len(service_results) 
                        for service, service_results in results.items()
                    }
                }
                
            except Exception as e:
                logger.error(f"Multi-service search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/agents/execute")
        async def execute_agent_task(request: AgentTaskRequest):
            """Execute task using specialized agent"""
            try:
                agent = self._get_agent(request.agent_type)
                task_id = f"{request.agent_type}_{int(time.time())}"

                result = await agent.execute(task_id, request.task_data)

                # Store result in context if session provided
                if request.session_id:
                    await self.memory_service.store_context(
                        session_id=request.session_id,
                        content=json.dumps(result),
                        metadata={
                            "type": "agent_result",
                            "agent_type": request.agent_type,
                            "task_id": task_id
                        }
                    )

                return result

            except Exception as e:
                logger.error(f"Agent task execution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Alias for /agent/task endpoint
        @self.app.post("/agent/task")
        async def agent_task_alias(request: AgentTaskRequest):
            """Execute task using specialized agent (alias for /agents/execute)"""
            return await execute_agent_task(request)

        # Web Research Endpoints
        @self.app.post("/research/search")
        async def web_search(request: dict):
            """
            Perform web search using integrated web access service
            """
            try:
                from backend.web_access_service import WebAccessService
                web_service = WebAccessService()
                
                query = request.get("query", "")
                max_results = request.get("max_results", 10)
                strategy = request.get("strategy", "auto")
                
                if not query:
                    raise HTTPException(status_code=400, detail="Query is required")
                
                results = await web_service.search(
                    query=query,
                    max_results=max_results,
                    strategy=strategy
                )
                
                return {
                    "query": query,
                    "strategy": strategy,
                    "results": results,
                    "total_found": len(results),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/research/scrape")
        async def web_scrape(request: dict):
            """
            Scrape content from a URL using integrated web access service
            """
            try:
                from backend.web_access_service import WebAccessService
                web_service = WebAccessService()
                
                url = request.get("url", "")
                strategy = request.get("strategy", "auto")
                extract_text = request.get("extract_text", True)
                extract_links = request.get("extract_links", False)
                extract_images = request.get("extract_images", False)
                
                if not url:
                    raise HTTPException(status_code=400, detail="URL is required")
                
                result = await web_service.scrape(
                    url=url,
                    strategy=strategy,
                    extract_text=extract_text,
                    extract_links=extract_links,
                    extract_images=extract_images
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Web scraping failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/research/comprehensive")
        async def comprehensive_research(request: dict):
            """
            Perform comprehensive research combining search and scraping
            """
            try:
                from backend.web_access_service import WebAccessService
                web_service = WebAccessService()
                
                query = request.get("query", "")
                max_results = request.get("max_results", 5)
                scrape_top = request.get("scrape_top", 3)
                
                if not query:
                    raise HTTPException(status_code=400, detail="Query is required")
                
                # First, perform web search
                search_results = await web_service.search(
                    query=query,
                    max_results=max_results,
                    strategy="auto"
                )
                
                # Then scrape top results for detailed content
                detailed_results = []
                for i, result in enumerate(search_results[:scrape_top]):
                    try:
                        scraped = await web_service.scrape(
                            url=result["url"],
                            strategy="auto",
                            extract_text=True
                        )
                        
                        result["scraped_content"] = scraped.get("content", "")[:2000]  # Limit content
                        result["scraped_title"] = scraped.get("title", "")
                        result["scrape_success"] = scraped.get("success", False)
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {result['url']}: {e}")
                        result["scraped_content"] = ""
                        result["scraped_title"] = ""
                        result["scrape_success"] = False
                        result["scrape_error"] = str(e)
                    
                    detailed_results.append(result)
                
                return {
                    "query": query,
                    "strategy": "comprehensive",
                    "search_results": len(search_results),
                    "scraped_results": len([r for r in detailed_results if r.get("scrape_success")]),
                    "results": detailed_results,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Comprehensive research failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/stats")
        async def get_stats():
            """Get comprehensive system statistics"""
            try:
                # Get AI router stats
                router_stats = await self.ai_router.get_model_stats()

                # Get memory service stats
                memory_stats = await self.memory_service.get_stats()

                # Get agent stats
                agent_stats = {
                    name: agent.get_stats()
                    for name, agent in self.agents.items()
                }

                return {
                    "system": self.performance_metrics,
                    "ai_router": router_stats,
                    "memory_service": memory_stats,
                    "agents": agent_stats,
                    "active_sessions": len(self.active_sessions)
                }
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/models")
        async def get_available_models():
            """Get available AI models and their capabilities"""
            try:
                return await self.ai_router.get_model_stats()
            except Exception as e:
                logger.error(f"Failed to get models: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # GPU Management Endpoints
        @self.app.get("/gpu/quota")
        async def gpu_quota():
            """Get GPU quota and usage information"""
            try:
                return await self.lambda_client.quota()
            except Exception as e:
                logger.error(f"Failed to get GPU quota: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/gpu/instances")
        async def list_gpu_instances():
            """List all GPU instances"""
            try:
                return await self.lambda_client.list_instances()
            except Exception as e:
                logger.error(f"Failed to list GPU instances: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/gpu/instances/{instance_id}")
        async def get_gpu_instance(instance_id: str):
            """Get details for a specific GPU instance"""
            try:
                return await self.lambda_client.get_instance(instance_id)
            except Exception as e:
                logger.error(f"Failed to get GPU instance {instance_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/gpu/launch")
        async def launch_gpu_instance(config: Dict[str, Any]):
            """Launch a new GPU instance"""
            try:
                return await self.lambda_client.launch_instance(config)
            except Exception as e:
                logger.error(f"Failed to launch GPU instance: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/gpu/instances/{instance_id}")
        async def terminate_gpu_instance(instance_id: str):
            """Terminate a GPU instance"""
            try:
                return await self.lambda_client.terminate_instance(instance_id)
            except Exception as e:
                logger.error(f"Failed to terminate GPU instance {instance_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/gpu/instances/{instance_id}/restart")
        async def restart_gpu_instance(instance_id: str):
            """Restart a GPU instance"""
            try:
                return await self.lambda_client.restart_instance(instance_id)
            except Exception as e:
                logger.error(f"Failed to restart GPU instance {instance_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/gpu/instance-types")
        async def list_gpu_instance_types():
            """List available GPU instance types"""
            try:
                return await self.lambda_client.list_instance_types()
            except Exception as e:
                logger.error(f"Failed to list GPU instance types: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _initialize_ai_clients(self):
        """Initialize AI provider clients"""
        try:
            # Initialize HTTP session
            self.session = aiohttp.ClientSession()

            # Initialize provider-specific clients
            self.ai_clients = {
                "openai": self._create_openai_client(),
                "anthropic": self._create_anthropic_client(),
                "google": self._create_google_client(),
                "groq": self._create_groq_client(),
                "deepseek": self._create_deepseek_client(),
                "grok": self._create_grok_client()
            }

            logger.info("AI clients initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AI clients: {e}")

    def _create_openai_client(self):
        """Create OpenAI client configuration"""
        return {
            "base_url": "https://api.openai.com/v1",
            "headers": {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
        }

    def _create_anthropic_client(self):
        """Create Anthropic client configuration"""
        return {
            "base_url": "https://api.anthropic.com/v1",
            "headers": {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        }

    def _create_google_client(self):
        """Create Google AI client configuration"""
        return {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "headers": {
                "Content-Type": "application/json"
            },
            "api_key": settings.GEMINI_API_KEY
        }

    def _create_groq_client(self):
        """Create Groq client configuration"""
        return {
            "base_url": "https://api.groq.com/openai/v1",
            "headers": {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
        }

    def _create_deepseek_client(self):
        """Create DeepSeek client configuration"""
        return {
            "base_url": "https://api.deepseek.com/v1",
            "headers": {
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
        }

    def _create_grok_client(self):
        """Create Grok client configuration"""
        return {
            "base_url": "https://api.x.ai/v1",
            "headers": {
                "Authorization": f"Bearer {settings.GROK_API_KEY}",
                "Content-Type": "application/json"
            }
        }

    async def _execute_ai_request(self, routing_decision: RoutingDecision,
                                  prompt: str, request: AIRequest) -> Dict[str, Any]:
        """Execute AI request using the selected provider"""
        provider = routing_decision.selected_provider.value
        model = routing_decision.selected_model

        if provider not in self.ai_clients:
            raise HTTPException(
                status_code=500, detail=f"Provider {provider} not available")

        client_config = self.ai_clients[provider]

        # Prepare request payload based on provider
        if provider in ["openai", "groq", "deepseek"]:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            endpoint = f"{client_config['base_url']}/chat/completions"

        elif provider == "anthropic":
            payload = {
                "model": model,
                "max_tokens": request.max_tokens or 4096,
                "temperature": request.temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            endpoint = f"{client_config['base_url']}/messages"

        elif provider == "google":
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": request.max_tokens or 4096,
                    "temperature": request.temperature
                }
            }
            endpoint = f"{client_config['base_url']}/models/{model}:generateContent?key={client_config['api_key']}"

        elif provider == "grok":
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            endpoint = f"{client_config['base_url']}/chat/completions"

        # Make API request
        async with self.session.post(
            endpoint,
            headers=client_config["headers"],
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Provider API error: {error_text}"
                )

            result = await response.json()

            # Extract content based on provider response format
            if provider in ["openai", "groq", "deepseek", "grok"]:
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
            elif provider == "anthropic":
                content = result["content"][0]["text"]
                usage = result.get("usage", {})
            elif provider == "google":
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                usage = result.get("usageMetadata", {})

            return {
                "content": content,
                "usage": usage,
                "raw_response": result
            }

    async def _stream_ai_response(self, routing_decision: RoutingDecision, request: AIRequest):
        """Stream AI response"""
        # Implementation for streaming responses
        # This would be provider-specific streaming logic
        yield f"data: Streaming from {routing_decision.selected_provider.value}:{routing_decision.selected_model}\n\n"
        yield f"data: {request.prompt}\n\n"
        yield "data: [DONE]\n\n"

    async def _store_interaction(self, session_id: str, user_prompt: str,
                                 ai_response: str, routing_decision: RoutingDecision):
        """Store interaction in context memory"""
        try:
            interaction = {
                "user_prompt": user_prompt,
                "ai_response": ai_response,
                "provider": routing_decision.selected_provider.value,
                "model": routing_decision.selected_model,
                "timestamp": datetime.now().isoformat()
            }

            await self.memory_service.store_context(
                session_id=session_id,
                content=json.dumps(interaction),
                metadata={
                    "type": "interaction",
                    "provider": routing_decision.selected_provider.value,
                    "model": routing_decision.selected_model
                }
            )
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")

    def _get_agent(self, agent_type: str) -> BaseAgent:
        """Get or create agent instance"""
        if agent_type not in self.agents:
            # Import and create agent based on type
            if agent_type == "coding":
                from agents.coding_agent import CodingAgent
                self.agents[agent_type] = CodingAgent()
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown agent type: {agent_type}")

        return self.agents[agent_type]

    async def _check_provider_health(self) -> Dict[str, Any]:
        """Check health of AI providers"""
        health_status = {}

        for provider, client_config in self.ai_clients.items():
            try:
                # Simple health check - attempt to make a minimal request
                if provider == "openai":
                    endpoint = f"{client_config['base_url']}/models"
                    async with self.session.get(endpoint, headers=client_config["headers"]) as response:
                        health_status[provider] = "healthy" if response.status == 200 else "unhealthy"
                else:
                    # For other providers, assume healthy if client is configured
                    health_status[provider] = "healthy"
            except Exception as e:
                health_status[provider] = f"unhealthy: {str(e)}"

        return health_status

    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


# Create global server instance
enhanced_server = EnhancedUnifiedMCPServer()
app = enhanced_server.app


if __name__ == "__main__":
    uvicorn.run(
        "enhanced_unified_server:app",
        host="0.0.0.0",
        port=settings.MCP_PORT,
        reload=True
    )
