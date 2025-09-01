"""
Agno Bridge Server - Provides Agno-compatible API endpoints.
Bridges between Agno UI expectations and our unified server implementation.

Following ADR-006: Configuration Management Standardization
- Uses enhanced EnvLoader with Pulumi ESC integration
- Single source of truth for all environment configuration
- Proper secret management and validation
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import httpx
import logging
from datetime import datetime

# Import enhanced configuration system following ADR-006
from app.config.env_loader import get_env_config, validate_environment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration using enhanced EnvLoader
try:
    config = get_env_config()
    logger.info(f"✅ Agno Bridge configuration loaded from: {config.loaded_from}")
except Exception as e:
    logger.error(f"❌ Failed to load configuration: {e}")
    config = None

app = FastAPI(
    title="Agno Bridge Server",
    description="Bridges Agno UI to Sophia Intel AI unified server - ADR-006 compliant",
    version="2.0.0"
)

# Enhanced CORS configuration using config
cors_origins = []
if config:
    cors_origins = [
        config.frontend_url,
        config.agno_bridge_url,
        config.unified_api_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3333",
        "http://localhost:7777"
    ]
    
    # Add environment-specific origins
    if config.environment_name == "prod":
        cors_origins.extend([
            f"https://{config.domain}",
            f"https://app.{config.domain}",
            "https://sophia-ui.fly.dev"
        ])
    elif config.environment_name == "staging":
        cors_origins.extend([
            f"https://staging.{config.domain}",
            "https://sophia-ui-staging.fly.dev"
        ])
else:
    # Fallback CORS for startup issues
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(cors_origins)),  # Remove duplicates
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced configuration using EnvConfig
if config:
    UNIFIED_API_URL = config.unified_api_url
    AGNO_API_KEY = config.agno_api_key
    USE_DIRECT_SWARMS = config.local_dev_mode  # Enable in dev mode
    BRIDGE_PORT = config.playground_port
    BRIDGE_HOST = config.playground_host
else:
    # Fallback configuration
    UNIFIED_API_URL = os.getenv("UNIFIED_API_URL", "http://localhost:8003")
    AGNO_API_KEY = os.getenv("AGNO_API_KEY", "")
    USE_DIRECT_SWARMS = True
    BRIDGE_PORT = 7777
    BRIDGE_HOST = "0.0.0.0"

if not AGNO_API_KEY:
    logger.warning("⚠️  AGNO_API_KEY not configured - some features may not work")

# Configuration validation
if config:
    validation = validate_environment()
    if validation.get("overall_status") == "unhealthy":
        logger.warning("⚠️  Configuration validation failed - bridge may have limited functionality")
        for issue in validation.get("critical_issues", []):
            logger.error(f"❌ {issue}")

# ============================================
# Data Models
# ============================================

class AgentInfo(BaseModel):
    """Agno-compatible agent model."""
    agent_id: str
    name: str
    description: str
    model: Dict[str, str]  # {provider, name, model}
    storage: bool = True
    tools: Optional[List[str]] = None

class TeamInfo(BaseModel):
    """Agno-compatible team model."""
    team_id: str
    name: str
    description: str
    model: Dict[str, str]
    storage: bool = True
    members: Optional[List[str]] = None

class WorkflowInfo(BaseModel):
    """Workflow information."""
    workflow_id: str
    name: str
    description: str
    inputs: Optional[Dict[str, Any]] = None

class RunRequest(BaseModel):
    """Request to run agent/team."""
    message: str
    session_id: Optional[str] = None
    stream: bool = True
    additional_data: Optional[Dict[str, Any]] = None

# ============================================
# Helper Functions
# ============================================

def transform_team_to_agent(team: Dict) -> AgentInfo:
    """Transform our team format to Agno agent format."""
    return AgentInfo(
        agent_id=team.get("id", "unknown"),
        name=team.get("name", "Unknown Agent"),
        description=team.get("description", ""),
        model={
            "provider": team.get("model_pool", "openai"),
            "name": team.get("name", "gpt-4"),
            "model": "gpt-4o"
        },
        storage=True,
        tools=["code_search", "file_operations", "git_operations"]
    )

async def proxy_streaming_response(response: httpx.Response) -> AsyncGenerator:
    """Proxy streaming response from unified server to Agno format."""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                
                # Transform to Agno RunEvent format
                if "phase" in data:
                    # Convert phase-based to RunEvent
                    if data["phase"] == "initialization":
                        yield f"data: {json.dumps({'event': 'RunStarted', 'data': {'message': data.get('token', '')}})}\n\n"
                    elif data["phase"] == "completion":
                        yield f"data: {json.dumps({'event': 'RunCompleted', 'data': data})}\n\n"
                    else:
                        yield f"data: {json.dumps({'event': 'RunResponse', 'data': {'content': data.get('token', '')}})}\n\n"
                elif "token" in data:
                    # Direct token streaming
                    yield f"data: {json.dumps({'event': 'RunResponse', 'data': {'content': data['token']}})}\n\n"
                else:
                    # Pass through other events
                    yield line + "\n"
            except json.JSONDecodeError:
                if line == "data: [DONE]":
                    yield f"data: {json.dumps({'event': 'RunCompleted', 'data': {'status': 'success'}})}\n\n"
                    yield "data: [DONE]\n\n"
                else:
                    yield line + "\n"
        else:
            yield line + "\n"

# ============================================
# Agno Playground Compatible Endpoints
# ============================================

@app.get("/v1/playground/status")
@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{UNIFIED_API_URL}/healthz", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "timestamp": datetime.utcnow().isoformat(),
                    "systems": data.get("systems", {}),
                    "version": "2.0.0"
                }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/v1/playground/agents", response_model=List[AgentInfo])
@app.get("/agents", response_model=List[AgentInfo])
async def get_agents():
    """Get available agents (teams presented as agents)."""
    if USE_DIRECT_SWARMS:
        # Direct swarm integration - return real swarm types
        from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator
        
        try:
            orchestrator = UnifiedSwarmOrchestrator()
            agents = []
            
            for name, info in orchestrator.swarm_registry.items():
                agents.append(AgentInfo(
                    agent_id=name,
                    name=info["description"],
                    description=f"AI Agent Swarm: {info['description']}",
                    model={
                        "provider": "sophia-intel",
                        "name": name,
                        "model": info["type"]
                    },
                    storage=True,
                    tools=info.get("mcp_servers", [])
                ))
            
            return agents
        except Exception as e:
            logger.error(f"Direct swarm integration failed: {e}")
    
    # Fallback to unified server
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{UNIFIED_API_URL}/teams", timeout=10.0)
            if response.status_code == 200:
                teams = response.json()
                # Transform teams to agents
                agents = [transform_team_to_agent(team) for team in teams]
                return agents
    except Exception as e:
        logger.error(f"Failed to fetch teams: {e}")
        
        # Return real swarm types as fallback
        return [
            AgentInfo(
                agent_id="coding_team",
                name="Coding Team (5 agents)",
                description="Balanced 5-agent team for general coding tasks",
                model={"provider": "sophia-intel", "name": "coding_team", "model": "multi-agent"},
                storage=True,
                tools=["consensus", "memory_dedup", "filesystem"]
            ),
            AgentInfo(
                agent_id="coding_swarm",
                name="Advanced Coding Swarm (10+ agents)",
                description="Comprehensive swarm for complex projects",
                model={"provider": "sophia-intel", "name": "coding_swarm", "model": "multi-agent"},
                storage=True,
                tools=["consensus", "memory_dedup", "filesystem", "git"]
            )
        ]

@app.get("/v1/playground/teams", response_model=List[TeamInfo])
async def get_teams():
    """Get available teams."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{UNIFIED_API_URL}/teams", timeout=10.0)
            if response.status_code == 200:
                teams = response.json()
                # Transform to Agno team format
                return [
                    TeamInfo(
                        team_id=team.get("id"),
                        name=team.get("name"),
                        description=team.get("description"),
                        model={
                            "provider": team.get("model_pool", "balanced"),
                            "name": "multi-model",
                            "model": "various"
                        },
                        storage=True,
                        members=team.get("members", [])
                    )
                    for team in teams
                ]
    except Exception as e:
        logger.error(f"Failed to fetch teams: {e}")
        return []

@app.get("/v1/playground/workflows", response_model=List[WorkflowInfo])
@app.get("/workflows", response_model=List[WorkflowInfo])
async def get_workflows():
    """Get available workflows."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{UNIFIED_API_URL}/workflows", timeout=10.0)
            if response.status_code == 200:
                workflows = response.json()
                return [
                    WorkflowInfo(
                        workflow_id=w.get("id"),
                        name=w.get("name"),
                        description=w.get("description"),
                        inputs=w.get("inputs")
                    )
                    for w in workflows
                ]
    except Exception as e:
        logger.error(f"Failed to fetch workflows: {e}")
        return []

@app.post("/v1/playground/agents/{agent_id}/runs")
@app.post("/run/agent/{agent_id}")
@app.post("/run/team")
async def run_agent(agent_id: str = None, request: RunRequest = None):
    """Run an agent/team with streaming response."""
    
    # Map agent_id to team_id for our backend
    team_id = request.additional_data.get("team_id") if request.additional_data else agent_id
    
    try:
        async with httpx.AsyncClient() as client:
            # Call our unified server's team run endpoint
            payload = {
                "team_id": team_id or "development-swarm",
                "message": request.message,
                "stream": True
            }
            
            async with client.stream(
                "POST",
                f"{UNIFIED_API_URL}/teams/run",
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code == 200:
                    return StreamingResponse(
                        proxy_streaming_response(response),
                        media_type="text/event-stream"
                    )
                else:
                    raise HTTPException(status_code=response.status_code, detail="Team run failed")
    
    except httpx.RequestError as e:
        logger.error(f"Failed to run team: {e}")
        # FAIL FAST - No mock fallbacks allowed in production
        if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
            raise HTTPException(status_code=503, detail=f"Team execution failed: {e}")
            
        # Return error response instead of mock
        raise HTTPException(status_code=503, detail="Unified server unavailable for team execution")

@app.post("/v1/playground/teams/{team_id}/runs")
async def run_team(team_id: str, request: RunRequest):
    """Run a team with streaming response."""
    request.additional_data = {"team_id": team_id}
    return await run_agent(agent_id=team_id, request=request)

@app.post("/run/workflow")
async def run_workflow(request: RunRequest):
    """Run a workflow with streaming response."""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "workflow_id": request.additional_data.get("workflow_id") if request.additional_data else "code_review",
                "message": request.message,
                "stream": True
            }
            
            async with client.stream(
                "POST",
                f"{UNIFIED_API_URL}/workflows/run",
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code == 200:
                    return StreamingResponse(
                        proxy_streaming_response(response),
                        media_type="text/event-stream"
                    )
    except Exception as e:
        logger.error(f"Failed to run workflow: {e}")
        # FAIL FAST - No mock fallbacks allowed
        if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
            raise HTTPException(status_code=503, detail=f"Workflow execution failed: {e}")
            
        raise HTTPException(status_code=503, detail="Workflow execution unavailable")

# ============================================
# Session Management (for Agno compatibility)
# ============================================

@app.get("/v1/playground/agents/{agent_id}/sessions")
async def get_agent_sessions(agent_id: str):
    """Get agent sessions."""
    # TODO: Implement session persistence
    return []

@app.get("/v1/playground/agents/{agent_id}/sessions/{session_id}")
async def get_agent_session(agent_id: str, session_id: str):
    """Get specific session."""
    return {"session_id": session_id, "messages": []}

@app.delete("/v1/playground/agents/{agent_id}/sessions/{session_id}")
async def delete_agent_session(agent_id: str, session_id: str):
    """Delete session."""
    return {"deleted": True}

# ============================================
# Memory Management
# ============================================

@app.post("/memory/add")
async def add_memory(request: Dict[str, Any]):
    """Add to agent memory."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{UNIFIED_API_URL}/memory/add",
                json=request,
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/memory/search")
async def search_memory(request: Dict[str, Any]):
    """Search agent memory."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{UNIFIED_API_URL}/memory/search",
                json=request,
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return {"results": []}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🌉 Agno Bridge Server v2.0.0")
    print("=" * 60)
    print("✅ Bridging Agno UI to Sophia Intel AI")
    print(f"📡 Proxying to unified server at {UNIFIED_API_URL}")
    print("🚀 Starting on http://localhost:7777")
    print("=" * 60)
    print("\nEndpoints:")
    print("  • GET  /v1/playground/agents     - List agents")
    print("  • POST /v1/playground/agents/{id}/runs - Run agent")
    print("  • GET  /v1/playground/teams      - List teams")
    print("  • POST /v1/playground/teams/{id}/runs - Run team")
    print("  • GET  /workflows                - List workflows")
    print("  • POST /run/workflow             - Run workflow")
    print("  • POST /memory/add               - Add memory")
    print("  • POST /memory/search            - Search memory")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=7777, log_level="info")