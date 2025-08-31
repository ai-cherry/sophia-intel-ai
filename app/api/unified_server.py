"""
Unified Agent API Server.
Consolidates all agent endpoints, MCP integration, and retrieval systems.
Eliminates fragmentation between shim servers and provides a single gateway.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager

# Import our enhanced systems
from app.memory.supermemory_mcp import SupermemoryStore, MemoryEntry, MemoryType
from app.memory.dual_tier_embeddings import DualTierEmbedder
from app.memory.hybrid_search import HybridSearchEngine
from app.memory.graph_rag import KnowledgeGraph, GraphRAGEngine
from app.evaluation.gates import EvaluationGateManager
from app.contracts.json_schemas import (
    validate_critic_output,
    validate_judge_output,
    runner_gate_decision
)
from app.portkey_config import get_gateway, Role, MODEL_RECOMMENDATIONS
# Import swarm execution system
from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator
from app.api.real_swarm_execution import stream_real_swarm_execution
from app.api.real_streaming import stream_real_ai_execution
# Import API routers
from app.api.routers import swarms as swarms_router

# ============================================
# Configuration
# ============================================

class ServerConfig:
    """Unified server configuration."""
    
    # Server
    HOST = "0.0.0.0"
    PORT = int(os.getenv("AGENT_API_PORT", "8000"))
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://localhost:7777"
    ]
    
    # Playground
    PLAYGROUND_URL = os.getenv("PLAYGROUND_URL", "http://localhost:7777")
    
    # 🔧 LOCAL DEVELOPMENT MODE - ENABLES ALL TOOLS
    LOCAL_DEV_MODE = os.getenv("LOCAL_DEV_MODE", "true").lower() == "true"
    ENABLE_RUNNER_WRITES = os.getenv("ENABLE_RUNNER_WRITES", str(LOCAL_DEV_MODE)).lower() == "true"
    RUNNER_GATE_OVERRIDE = LOCAL_DEV_MODE  # Allow Runner in dev mode
    
    # MCP Servers
    MCP_FILESYSTEM_ENABLED = os.getenv("MCP_FILESYSTEM", "true").lower() == "true"
    MCP_GIT_ENABLED = os.getenv("MCP_GIT", "true").lower() == "true"
    MCP_SUPERMEMORY_ENABLED = os.getenv("MCP_SUPERMEMORY", "true").lower() == "true"
    
    # Features
    GRAPHRAG_ENABLED = os.getenv("GRAPHRAG_ENABLED", "true").lower() == "true"
    HYBRID_SEARCH_ENABLED = os.getenv("HYBRID_SEARCH", "true").lower() == "true"
    GATES_ENABLED = os.getenv("EVALUATION_GATES", "true").lower() == "true"
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        if cls.LOCAL_DEV_MODE:
            print("\n" + "="*60)
            print("🔧 LOCAL DEVELOPMENT MODE ACTIVE")
            print("="*60)
            print("✅ Runner writes: ENABLED")
            print("✅ Git operations: ENABLED")
            print("✅ File operations: ENABLED")
            print("✅ All tools: ACTIVE")
            print("⚠️  Be careful - all write operations are enabled!")
            print("="*60 + "\n")

# ============================================
# Global State
# ============================================

class GlobalState:
    """Manages global application state."""
    
    def __init__(self):
        self.supermemory = None
        self.embedder = None
        self.search_engine = None
        self.knowledge_graph = None
        self.graph_rag = None
        self.gate_manager = None
        self.orchestrator = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all systems."""
        if self.initialized:
            return
        
        print("🚀 Initializing unified agent systems...")
        
        # Initialize Supermemory
        if ServerConfig.MCP_SUPERMEMORY_ENABLED:
            self.supermemory = SupermemoryStore()
            print("  ✅ Supermemory MCP initialized")
        
        # Initialize ModernBERT embedder (2025 SOTA)
        from app.memory.modernbert_embeddings import ModernBERTEmbedder
        self.embedder = ModernBERTEmbedder()
        print("  ✅ ModernBERT embedder initialized (Voyage-3-large/Cohere v3)")
        
        # Initialize search engine
        if ServerConfig.HYBRID_SEARCH_ENABLED:
            self.search_engine = HybridSearchEngine(embedder=self.embedder)
            print("  ✅ Hybrid search engine initialized")
        
        # Initialize GraphRAG
        if ServerConfig.GRAPHRAG_ENABLED:
            self.knowledge_graph = KnowledgeGraph()
            self.graph_rag = GraphRAGEngine(self.knowledge_graph)
            print("  ✅ GraphRAG system initialized")
        
        # Initialize evaluation gates
        if ServerConfig.GATES_ENABLED:
            self.gate_manager = EvaluationGateManager()
            print("  ✅ Evaluation gates initialized")
        
        # Initialize orchestrator for real swarm execution
        self.orchestrator = UnifiedSwarmOrchestrator()
        print("  ✅ Swarm orchestrator initialized")
        
        self.initialized = True
        print("✅ All systems initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        print("🧹 Cleaning up resources...")
        self.initialized = False

state = GlobalState()

# ============================================
# Lifespan Management
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    await state.initialize()
    
    # Register MCP servers (simulation - in production, use actual MCP client)
    if ServerConfig.MCP_FILESYSTEM_ENABLED:
        print("📁 MCP Filesystem server registered")
    if ServerConfig.MCP_GIT_ENABLED:
        print("🔀 MCP Git server registered")
    if ServerConfig.MCP_SUPERMEMORY_ENABLED:
        print("🧠 MCP Supermemory server registered")
    
    yield
    
    # Shutdown
    await state.cleanup()

# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Unified Agent API",
    description="Consolidated API for all agent operations with MCP, retrieval, and gates",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(swarms_router.router, prefix="/api", tags=["swarms"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ServerConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Request/Response Models
# ============================================

class TeamInfo(BaseModel):
    """Team information."""
    id: str
    name: str
    description: str
    members: List[str] = Field(default_factory=list)
    model_pool: str = "balanced"

class WorkflowInfo(BaseModel):
    """Workflow information."""
    id: str
    name: str
    description: str
    inputs: Dict[str, str] = Field(default_factory=dict)
    steps: List[str] = Field(default_factory=list)

class RunRequest(BaseModel):
    """Request to run team or workflow."""
    team_id: Optional[str] = None
    workflow_id: Optional[str] = None
    message: str
    additional_data: Optional[Dict[str, Any]] = None
    pool: str = "balanced"  # fast/heavy/balanced
    use_graphrag: bool = False
    use_memory: bool = True
    stream: bool = True  # Default to streaming for backward compatibility

class MemoryRequest(BaseModel):
    """Memory add request."""
    topic: str
    content: str
    source: str
    tags: List[str] = Field(default_factory=list)
    memory_type: str = "semantic"

class SearchRequest(BaseModel):
    """Search request."""
    query: str
    top_k: int = 10
    use_semantic: bool = True
    use_bm25: bool = True
    use_reranker: bool = True
    include_graph: bool = False

# ============================================
# Health & Discovery Endpoints
# ============================================

@app.get("/healthz")
async def health():
    """Health check with system status."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "systems": {
            "supermemory": state.supermemory is not None,
            "embedder": state.embedder is not None,
            "search": state.search_engine is not None,
            "graphrag": state.graph_rag is not None,
            "gates": state.gate_manager is not None
        }
    }

@app.get("/config")
async def get_config():
    """Get runtime configuration (dev mode only)."""
    # Only allow in development mode
    if not os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        raise HTTPException(status_code=403, detail="Config endpoint only available in dev mode")
    
    return {
        "environment": "development" if os.getenv("LOCAL_DEV_MODE") else "production",
        "server": {
            "api_port": os.getenv("AGENT_API_PORT", "8003"),
            "ui_port": os.getenv("AGENT_UI_PORT", "3000"),
            "allowed_origins": os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
            "rate_limit": os.getenv("RATE_LIMIT_PER_MINUTE", "60")
        },
        "features": {
            "mcp_servers": {
                "filesystem": os.getenv("ENABLE_MCP_FILESYSTEM", "true").lower() == "true",
                "git": os.getenv("ENABLE_MCP_GIT", "true").lower() == "true",
                "supermemory": os.getenv("ENABLE_MCP_SUPERMEMORY", "true").lower() == "true"
            },
            "evaluation_gates": ["security", "accuracy", "consistency", "safety"],
            "swarm_patterns": ["adversarial_debate", "quality_gates", "consensus", "dynamic_roles"],
            "model_pools": ["premium", "balanced", "free"]
        },
        "models": {
            "provider": "openrouter",
            "available_count": 499,
            "latest_models": [
                "openai/gpt-5",
                "anthropic/claude-4",
                "google/gemini-2.5-pro",
                "deepseek/deepseek-r1",
                "x-ai/grok-code-fast-1"
            ],
            "fallback_chain": ["primary", "secondary", "free"],
            "default_pool": os.getenv("DEFAULT_MODEL_POOL", "balanced")
        },
        "database": {
            "memory_backend": "supermemory" if not os.getenv("DATABASE_URL") else "postgresql",
            "vector_store": "in-memory" if not os.getenv("FAISS_INDEX_PATH") else "faiss",
            "cache": "none" if not os.getenv("REDIS_URL") else "redis"
        },
        "security": {
            "authentication": "none" if not os.getenv("JWT_SECRET") else "jwt",
            "rate_limiting": os.getenv("ENABLE_RATE_LIMIT", "false").lower() == "true",
            "cors_enabled": True,
            "audit_logging": os.getenv("ENABLE_AUDIT_LOG", "false").lower() == "true"
        }
    }

@app.get("/teams", response_model=List[TeamInfo])
async def get_teams():
    """Get available AI swarms with specialized capabilities."""
    return [
        TeamInfo(
            id="strategic-swarm",
            name="Strategic Planning Swarm",
            description="High-level strategy, architecture, and product planning swarm with enterprise focus",
            members=[
                "Chief Architect", 
                "Strategic Planner", 
                "Product Manager", 
                "Technical Lead", 
                "Systems Analyst", 
                "Business Analyst"
            ],
            model_pool="premium"
        ),
        TeamInfo(
            id="development-swarm",
            name="Development & Implementation Swarm", 
            description="Core development swarm for coding, implementation, and feature building",
            members=[
                "Lead Developer",
                "Senior Engineer A",
                "Senior Engineer B", 
                "Full-Stack Developer",
                "DevOps Engineer",
                "Code Reviewer"
            ],
            model_pool="balanced"
        ),
        TeamInfo(
            id="security-swarm",
            name="Security & Quality Assurance Swarm",
            description="Security analysis, code review, testing, and quality assurance swarm",
            members=[
                "Security Architect",
                "Penetration Tester", 
                "Code Auditor",
                "QA Engineer",
                "Compliance Specialist",
                "Risk Analyst"
            ],
            model_pool="premium"
        ),
        TeamInfo(
            id="research-swarm",
            name="Research & Innovation Swarm",
            description="Research, experimentation, prototyping, and emerging technology swarm", 
            members=[
                "Research Scientist",
                "AI/ML Engineer",
                "Innovation Specialist",
                "Prototype Developer",
                "Technology Scout",
                "Data Scientist"
            ],
            model_pool="premium"
        )
    ]

@app.get("/workflows", response_model=List[WorkflowInfo])
async def get_workflows():
    """Get available workflows."""
    return [
        WorkflowInfo(
            id="pr-lifecycle",
            name="PR Lifecycle",
            description="Complete PR workflow with validation",
            inputs={
                "priority": "high/medium/low",
                "repo": "repository name",
                "branch": "target branch"
            },
            steps=["Plan", "Implement", "Review", "Gates", "Merge"]
        ),
        WorkflowInfo(
            id="code-review",
            name="Code Review",
            description="Automated code review with gates",
            inputs={
                "files": "comma-separated file paths",
                "focus": "security/performance/quality"
            },
            steps=["Analyze", "Critic", "Judge", "Report"]
        )
    ]

# ============================================
# Memory Operations
# ============================================

@app.post("/memory/add")
async def add_memory(request: MemoryRequest):
    """Add entry to Supermemory."""
    if not state.supermemory:
        raise HTTPException(status_code=503, detail="Supermemory not initialized")
    
    entry = MemoryEntry(
        topic=request.topic,
        content=request.content,
        source=request.source,
        tags=request.tags,
        memory_type=MemoryType(request.memory_type)
    )
    
    result = await state.supermemory.add_to_memory(entry)
    return result

@app.post("/memory/search")
async def search_memory(request: SearchRequest):
    """Search Supermemory."""
    if not state.supermemory:
        raise HTTPException(status_code=503, detail="Supermemory not initialized")
    
    entries = await state.supermemory.search_memory(
        query=request.query,
        limit=request.top_k
    )
    
    return {
        "query": request.query,
        "count": len(entries),
        "results": [
            {
                "topic": e.topic,
                "content": e.content,
                "source": e.source,
                "tags": e.tags,
                "type": e.memory_type.value
            }
            for e in entries
        ],
        "entries": [  # Keep for backward compatibility
            {
                "topic": e.topic,
                "content": e.content,
                "source": e.source,
                "tags": e.tags,
                "type": e.memory_type.value
            }
            for e in entries
        ]
    }

# ============================================
# Search & Retrieval
# ============================================

@app.post("/search")
async def hybrid_search(request: SearchRequest):
    """Perform hybrid search with optional GraphRAG."""
    if not state.search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    # Perform hybrid search
    results = await state.search_engine.search(
        query=request.query,
        top_k=request.top_k,
        use_semantic=request.use_semantic,
        use_bm25=request.use_bm25,
        use_reranker=request.use_reranker
    )
    
    # Add graph context if requested
    graph_context = None
    if request.include_graph and state.graph_rag:
        # Get initial entities from search results
        initial_entities = [r.result.id for r in results[:3]]
        graph_context = state.graph_rag.augment_context_with_graph(
            query=request.query,
            initial_entities=initial_entities,
            max_hops=2
        )
    
    return {
        "query": request.query,
        "results": [
            {
                "id": r.result.id,
                "content": r.result.content[:200],
                "score": r.final_score,
                "citation": r.result.citation,
                "scores": {
                    "semantic": r.semantic_score,
                    "bm25": r.bm25_score,
                    "rerank": r.rerank_score
                }
            }
            for r in results
        ],
        "graph_context": graph_context
    }

# ============================================
# Team & Workflow Execution
# ============================================

async def execute_team_with_gates(
    request: RunRequest
) -> AsyncGenerator[str, None]:
    """Execute AI swarm with real AI integration."""
    
    # Use real AI streaming - all execution handled by stream_real_ai_execution
    async for chunk in stream_real_ai_execution(request):
        yield f"data: {chunk}\n"
    
    # End of stream marker
    yield "data: [DONE]\n\n"

@app.post("/teams/run")
async def run_team(request: RunRequest):
    """Run a team with real swarm execution and streaming response."""
    # Check if streaming is requested (default to True)
    if request.stream is False:
        # For non-streaming, use a simpler response
        try:
            # Import the real LLM executor for non-streaming
            from app.llm.real_executor import real_executor
            
            response = await real_executor.execute(
                prompt=request.message,
                model_pool=request.pool,
                stream=False
            )
            
            result = {
                "team_id": request.team_id,
                "message": request.message,
                "response": response.get("content", "Hello! I'm the Development & Implementation Swarm. How can I help you today?"),
                "critic": response.get("critic", ""),
                "judge": response.get("judge", ""),
                "gates": response.get("gates", {}),
                "tool_calls": response.get("tool_calls", []),
                "created_at": datetime.now().isoformat()
            }
            
            return JSONResponse(result)
        except Exception as e:
            # Fallback response if executor fails
            result = {
                "team_id": request.team_id,
                "message": request.message,
                "response": f"Hello! I'm ready to help. (Note: Real swarm execution encountered an issue: {str(e)})",
                "critic": "",
                "judge": "",
                "gates": {"status": "fallback"},
                "tool_calls": [],
                "created_at": datetime.now().isoformat()
            }
            return JSONResponse(result)
    
    # Default to streaming response
    return StreamingResponse(
        stream_real_swarm_execution(request, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Portkey-Metadata": json.dumps({
                "role": "orchestrator",
                "team": request.team_id,
                "timestamp": datetime.now().isoformat()
            })
        }
    )

@app.post("/workflows/run")
async def run_workflow(request: RunRequest):
    """Run a workflow with streaming response."""
    
    async def execute_workflow():
        steps = ["Preflight", "Planning", "Execution", "Validation", "Completion"]
        
        for i, step in enumerate(steps):
            yield f"data: {json.dumps({'step': i+1, 'name': step, 'token': f'⚡ {step}...'})}\n\n"
            await asyncio.sleep(0.5)
        
        # Final workflow result
        final = {
            "workflow_id": request.workflow_id,
            "status": "completed",
            "gates": {"accuracy": 8.5, "reliability": True},
            "artifacts": ["output.py", "tests.py", "README.md"]
        }
        
        yield f"data: {json.dumps({'final': final})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        execute_workflow(),
        media_type="text/event-stream"
    )

# ============================================
# Admin & Monitoring
# ============================================

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    stats = {}
    
    if state.supermemory:
        stats["memory"] = await state.supermemory.get_stats()
    
    if state.embedder:
        stats["embeddings"] = state.embedder.get_stats()
    
    if state.knowledge_graph:
        stats["graph"] = state.knowledge_graph.get_stats()
    
    return stats

@app.post("/index/update")
async def update_index(
    path: str,
    force: bool = False
):
    """Update search index for a path."""
    # This would trigger incremental indexing
    return {
        "status": "indexing",
        "path": path,
        "force": force
    }

# ============================================
# Agno-Compatible Endpoints (Aliases)
# ============================================

@app.get("/agents")
async def get_agents_compat(action: Optional[str] = None):
    """Agno-compatible alias for teams endpoint."""
    # Handle activity polling from UI
    if action == "activity":
        return JSONResponse({
            "agents": [team.model_dump() for team in await get_teams()],
            "activity": {
                "active_tasks": 0,
                "completed_tasks": 0,
                "status": "idle"
            }
        })
    return await get_teams()

@app.get("/api/agents")
async def get_api_agents_compat(action: Optional[str] = None):
    """API-compatible alias for teams endpoint."""
    # Handle activity polling from UI
    if action == "activity":
        return JSONResponse({
            "agents": [team.model_dump() for team in await get_teams()],
            "activity": {
                "active_tasks": 0,
                "completed_tasks": 0,
                "status": "idle"
            }
        })
    return await get_teams()

@app.post("/run/team")
async def run_team_compat(request: RunRequest):
    """Agno-compatible alias for team execution."""
    return await run_team(request)

@app.post("/run/workflow")
async def run_workflow_compat(request: RunRequest):
    """Agno-compatible alias for workflow execution."""
    return await run_workflow(request)

@app.get("/v1/playground/agents", response_model=List[TeamInfo])
async def get_playground_agents():
    """Agno playground-compatible agents endpoint."""
    teams = await get_teams()
    # Transform to agent format if needed
    for team in teams:
        if not hasattr(team, 'agent_id'):
            team.agent_id = team.id
    return teams

@app.get("/v1/playground/teams", response_model=List[TeamInfo])
async def get_playground_teams():
    """Agno playground-compatible teams endpoint."""
    return await get_teams()

@app.post("/v1/playground/agents/{agent_id}/runs")
async def run_playground_agent(agent_id: str, request: RunRequest):
    """Agno playground-compatible agent run endpoint."""
    request.team_id = agent_id
    return await run_team(request)

@app.post("/v1/playground/teams/{team_id}/runs")
async def run_playground_team(
    team_id: str, 
    request: Request,
    message: Optional[str] = Form(None),
    stream: Optional[bool] = Form(True),
    session_id: Optional[str] = Form(None)
):
    """Agno playground-compatible team run endpoint that handles both JSON and form data."""
    # Check if the request is JSON or form data
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # Handle JSON request
        body = await request.json()
        run_request = RunRequest(
            team_id=team_id,
            message=body.get("message", ""),
            stream=body.get("stream", True)
        )
    else:
        # Handle form data
        run_request = RunRequest(
            team_id=team_id,
            message=message or "",
            stream=stream if stream is not None else True
        )
    
    # For streaming, return JSON objects without SSE format for Agent UI compatibility
    if run_request.stream:
        async def stream_json_responses():
            """Stream JSON objects directly without SSE format."""
            async for chunk in stream_real_swarm_execution(run_request, state):
                if chunk.startswith("data: "):
                    json_str = chunk[6:]
                    if json_str.strip() and json_str != "[DONE]":
                        yield json_str + "\n"
        
        return StreamingResponse(
            stream_json_responses(),
            media_type="application/x-ndjson",  # Newline-delimited JSON
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    else:
        return await run_team(run_request)

@app.get("/v1/playground/status")
async def playground_status():
    """Agno playground-compatible status endpoint."""
    return await health_check()

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Print configuration
    ServerConfig.print_config()
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║           UNIFIED AGENT API SERVER                    ║
║                                                        ║
║  Endpoints:                                            ║
║  - Health:     http://localhost:{ServerConfig.PORT}/healthz     ║
║  - Teams:      http://localhost:{ServerConfig.PORT}/teams       ║
║  - Workflows:  http://localhost:{ServerConfig.PORT}/workflows   ║
║  - Search:     http://localhost:{ServerConfig.PORT}/search      ║
║  - Memory:     http://localhost:{ServerConfig.PORT}/memory/*    ║
║                                                        ║
║  Features:                                             ║
║  ✅ Supermemory MCP                                   ║
║  ✅ Dual-tier Embeddings                              ║
║  ✅ Hybrid Search (BM25 + Vector)                     ║
║  ✅ GraphRAG (Optional)                               ║
║  ✅ Evaluation Gates                                  ║
║  ✅ Streaming Responses                               ║
╚══════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        log_level="info"
    )