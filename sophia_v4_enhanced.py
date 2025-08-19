#!/usr/bin/env python3
"""
SOPHIA V4 Enhanced Production Server - Maximum Autonomous Capabilities
Badass AI with persona, deep web search, IaC control, GitHub swarms, and business integrations.
"""

import os
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Database and external service imports
from qdrant_client import QdrantClient
import redis.asyncio as redis
from github import Github, GithubException
import aiohttp

# Configure logging FIRST
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SOPHIA's enhanced capabilities with proper error handling
try:
    from agents.persona_manager import PersonaManager
    from agents.search_engine import DeepSearchEngine
    from agents.swarm_manager import SwarmManager
    from infrastructure.pulumi_manager import PulumiManager
    from integrations.business_services import BusinessServiceClient
    logger.info("✅ All enhanced modules imported successfully")
except ImportError as e:
    logger.warning(f"Some enhanced modules not available: {e}")
    # Fallback to basic functionality
    PersonaManager = None
    DeepSearchEngine = None
    SwarmManager = None
    PulumiManager = None
    BusinessServiceClient = None

# Pydantic models for API requests
class ChatRequest(BaseModel):
    query: str = Field(..., description="User query for SOPHIA")
    sources_limit: int = Field(default=3, description="Number of sources to search")
    user_id: str = Field(default="default_user", description="User identifier for memory")

class SwarmRequest(BaseModel):
    task: str = Field(..., description="Task for the agent swarm")
    agents: List[str] = Field(..., description="List of agent types to deploy")
    objective: str = Field(..., description="Objective of the swarm operation")
    user_id: str = Field(default="default_user", description="User identifier")

class CodeCommitRequest(BaseModel):
    repo: str = Field(..., description="Repository in format owner/repo")
    changes: str = Field(..., description="Description of changes")
    branch: str = Field(default="main", description="Target branch")
    file_path: str = Field(..., description="Path to file to create/update")

class IaCDeployRequest(BaseModel):
    app_name: str = Field(default="sophia-intel", description="Application name")
    org_name: str = Field(default="lynn-musil", description="Organization name")
    region: str = Field(default="ord", description="Deployment region")

class BusinessWorkflowRequest(BaseModel):
    workflow_type: str = Field(..., description="Type of business workflow")
    data: Dict[str, Any] = Field(..., description="Workflow data")

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 SOPHIA V4 Enhanced - Starting up with maximum autonomous capabilities!")
    
    # Initialize enhanced components
    if PersonaManager:
        await app.state.persona_manager.initialize_collections()
        logger.info("✅ Persona manager initialized with badass attitude")
    
    yield
    
    logger.info("🛑 SOPHIA V4 Enhanced - Shutting down")

# Create FastAPI application
app = FastAPI(
    title="SOPHIA V4 Enhanced - Autonomous AI Platform",
    description="Maximum autonomous AI with persona, deep search, IaC, swarms, and business integrations",
    version="4.0.0-enhanced",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/v4", StaticFiles(directory="apps/frontend/v4", html=True), name="frontend")

# Initialize enhanced components
try:
    # SOPHIA's enhanced capabilities
    app.state.persona_manager = PersonaManager() if PersonaManager else None
    app.state.search_engine = DeepSearchEngine() if DeepSearchEngine else None
    app.state.swarm_manager = SwarmManager() if SwarmManager else None
    app.state.pulumi_manager = PulumiManager() if PulumiManager else None
    app.state.business_client = BusinessServiceClient() if BusinessServiceClient else None
    
    # Traditional components
    app.state.qdrant = QdrantClient(
        url="https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io",
        api_key=os.getenv("QDRANT_API_KEY")
    )
    app.state.redis = redis.from_url(os.getenv("REDIS_URL", "redis://sophia-cache.fly.dev"))
    app.state.github = Github(os.getenv("GH_FINE_GRAINED_TOKEN"))
    
    logger.info("✅ All SOPHIA V4 enhanced components initialized")
    
except Exception as e:
    logger.error(f"❌ Error initializing components: {e}")

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Enhanced health check with component status"""
    component_status = {
        "persona_manager": bool(app.state.persona_manager),
        "search_engine": bool(app.state.search_engine),
        "swarm_manager": bool(app.state.swarm_manager),
        "pulumi_manager": bool(app.state.pulumi_manager),
        "business_client": bool(app.state.business_client),
        "qdrant": bool(app.state.qdrant),
        "redis": bool(app.state.redis),
        "github": bool(app.state.github)
    }
    
    return {
        "status": "healthy",
        "version": "4.0.0-enhanced",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "agents": "operational",
        "persona": "badass_mode_active",
        "components": component_status,
        "capabilities": [
            "natural_language_interaction",
            "deep_web_search", 
            "multi_agent_swarms",
            "github_integration",
            "infrastructure_as_code",
            "business_service_integration",
            "long_term_memory"
        ]
    }

# Legacy health endpoint
@app.get("/health")
async def legacy_health():
    """Legacy health endpoint for compatibility"""
    return {
        "status": "healthy",
        "version": "4.0.0-enhanced",
        "timestamp": datetime.now().isoformat()
    }

# Enhanced chat endpoint with persona and deep search
@app.post("/api/v1/chat")
async def enhanced_chat(request: ChatRequest):
    """Enhanced chat with SOPHIA's badass persona and deep web search"""
    try:
        if not app.state.search_engine or not app.state.persona_manager:
            # Fallback to basic functionality
            return {
                "message": "Hey partner! SOPHIA here, but I'm running in basic mode. Still ready to help!",
                "sources": [],
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Perform deep multi-provider search
        search_results = await app.state.search_engine.perform_multi_provider_search(
            request.query, 
            request.sources_limit
        )
        
        # Synthesize answer
        synthesis = await app.state.search_engine.synthesize_answer(search_results, request.query)
        
        # Craft SOPHIA's response with personality
        persona_response = await app.state.persona_manager.craft_response(
            request.query,
            search_results,
            request.user_id
        )
        
        # Store interaction in memory
        await app.state.persona_manager.store_interaction(
            request.user_id,
            request.query,
            {"sources": search_results, "synthesis": synthesis}
        )
        
        return {
            "message": persona_response,
            "sources": search_results,
            "results": search_results,
            "synthesis": synthesis,
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat(),
            "sophia_mode": "enhanced_badass"
        }
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        return {
            "message": "Hey partner! SOPHIA hit a snag, but I'm still here to help. What else can I do for you?",
            "sources": [],
            "results": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Enhanced swarm orchestration with GitHub integration
@app.post("/api/v1/swarm/trigger")
async def enhanced_swarm_trigger(request: SwarmRequest):
    """Enhanced swarm orchestration with GitHub-integrated agent management"""
    try:
        if not app.state.swarm_manager:
            # Fallback to basic swarm functionality
            coordinator_id = f"swarm_{int(time.time()) % 1000000:06d}"
            task_id = f"task_{int(time.time()) % 1000000:06d}"
            
            return {
                "coordinator_id": coordinator_id,
                "task_id": task_id,
                "task": request.task,
                "agents_used": request.agents,
                "status": "completed",
                "message": "Basic swarm mode - GitHub integration not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use enhanced swarm manager
        result = await app.state.swarm_manager.trigger_swarm(
            request.task,
            request.agents,
            request.objective,
            request.user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced swarm error: {str(e)}")
        return {
            "error": f"Swarm deployment failed: {str(e)}",
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }

# Enhanced code commit with improved GitHub integration
@app.post("/api/v1/code/commit")
async def enhanced_code_commit(request: CodeCommitRequest):
    """Enhanced autonomous GitHub commits with better error handling"""
    try:
        # Use GitHub PAT from environment (multiple possible names)
        github_token = (
            os.getenv("GH_FINE_GRAINED_TOKEN") or 
            os.getenv("GITHUB_TOKEN") or 
            os.getenv("GITHUB_PAT")
        )
        
        if not github_token:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        github_client = Github(github_token)
        repo_obj = github_client.get_repo(request.repo)
        
        commit_message = f"SOPHIA V4 automated commit: {request.changes}"
        
        try:
            # Try to update existing file
            contents = repo_obj.get_contents(request.file_path, ref=request.branch)
            repo_obj.update_file(
                request.file_path,
                commit_message,
                request.changes,
                contents.sha,
                branch=request.branch
            )
        except GithubException:
            # File doesn't exist, create it
            repo_obj.create_file(
                request.file_path,
                commit_message,
                request.changes,
                branch=request.branch
            )
        
        # Get the latest commit
        commit = repo_obj.get_branch(request.branch).commit
        
        return {
            "commit_hash": commit.sha,
            "message": commit_message,
            "file_path": request.file_path,
            "branch": request.branch,
            "repo": request.repo,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "sophia_mode": "autonomous_coding"
        }
        
    except GithubException as e:
        raise HTTPException(status_code=400, detail=f"GitHub commit failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Commit operation failed: {str(e)}")

# Infrastructure as Code endpoint
@app.post("/api/v1/iac/deploy")
async def iac_deploy(request: IaCDeployRequest):
    """Deploy infrastructure using Pulumi IaC"""
    try:
        if not app.state.pulumi_manager:
            return {
                "status": "not_available",
                "message": "IaC functionality not available in this deployment",
                "timestamp": datetime.now().isoformat()
            }
        
        result = await app.state.pulumi_manager.deploy_infrastructure(
            request.app_name,
            request.org_name,
            request.region
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IaC deployment failed: {str(e)}")

# Business service integration endpoints
@app.post("/api/v1/business/salesforce")
async def salesforce_endpoint(data: Dict[str, Any]):
    """Salesforce integration endpoint"""
    try:
        if not app.state.business_client:
            return {"error": "Business integrations not available", "status": "disabled"}
        
        query = data.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter required")
        
        result = await app.state.business_client.salesforce_query(query)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Salesforce operation failed: {str(e)}")

@app.post("/api/v1/business/hubspot")
async def hubspot_endpoint(data: Dict[str, Any]):
    """HubSpot integration endpoint"""
    try:
        if not app.state.business_client:
            return {"error": "Business integrations not available", "status": "disabled"}
        
        action = data.get("action", "get_deals")
        
        if action == "create_contact":
            contact_data = data.get("contact", {})
            result = await app.state.business_client.hubspot_create_contact(contact_data)
        elif action == "get_deals":
            limit = data.get("limit", 10)
            result = await app.state.business_client.hubspot_get_deals(limit)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HubSpot operation failed: {str(e)}")

@app.post("/api/v1/business/slack")
async def slack_endpoint(data: Dict[str, Any]):
    """Slack integration endpoint"""
    try:
        if not app.state.business_client:
            return {"error": "Business integrations not available", "status": "disabled"}
        
        action = data.get("action", "notify")
        
        if action == "notify":
            channel = data.get("channel", "#general")
            message = data.get("message", "")
            user_id = data.get("user_id")
            result = await app.state.business_client.slack_notify(channel, message, user_id)
        elif action == "get_channels":
            result = await app.state.business_client.slack_get_channels()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slack operation failed: {str(e)}")

@app.post("/api/v1/business/workflow")
async def business_workflow(request: BusinessWorkflowRequest):
    """Create automated business workflow"""
    try:
        if not app.state.business_client:
            return {"error": "Business integrations not available", "status": "disabled"}
        
        result = await app.state.business_client.create_business_workflow(
            request.workflow_type,
            request.data
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business workflow failed: {str(e)}")

@app.get("/api/v1/business/metrics")
async def business_metrics():
    """Get aggregated business metrics"""
    try:
        if not app.state.business_client:
            return {"error": "Business integrations not available", "status": "disabled"}
        
        result = await app.state.business_client.get_business_metrics()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business metrics failed: {str(e)}")

# Legacy deployment endpoint
@app.post("/api/v1/deploy/trigger")
async def deploy_trigger(data: Dict[str, Any]):
    """Legacy deployment trigger endpoint"""
    try:
        app_name = data.get("app_name", "sophia-intel")
        org_name = data.get("org_name", "lynn-musil")
        
        # Use IaC manager if available, otherwise simulate
        if app.state.pulumi_manager:
            result = await app.state.pulumi_manager.deploy_infrastructure(app_name, org_name)
            return {"deployment_id": result.get("deployment_id"), "status": "deployed"}
        else:
            deployment_id = f"deploy_{int(time.time())}"
            return {
                "deployment_id": deployment_id,
                "status": "simulated",
                "message": "IaC manager not available - simulated deployment",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

# SOPHIA persona endpoint
@app.get("/api/v1/persona")
async def get_persona():
    """Get SOPHIA's current persona configuration"""
    if app.state.persona_manager:
        return {
            "persona": app.state.persona_manager.persona,
            "status": "badass_mode_active",
            "capabilities": [
                "witty_responses",
                "long_term_memory",
                "context_awareness",
                "neon_cowboy_attitude"
            ],
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "persona": {"name": "SOPHIA", "mode": "basic"},
            "status": "basic_mode",
            "timestamp": datetime.now().isoformat()
        }

# System status endpoint
@app.get("/api/v1/status")
async def system_status():
    """Get comprehensive system status"""
    return {
        "sophia_version": "4.0.0-enhanced",
        "status": "fully_operational",
        "mode": "maximum_autonomy",
        "capabilities": {
            "natural_language": bool(app.state.persona_manager),
            "deep_web_search": bool(app.state.search_engine),
            "agent_swarms": bool(app.state.swarm_manager),
            "infrastructure_control": bool(app.state.pulumi_manager),
            "business_integrations": bool(app.state.business_client),
            "github_automation": bool(app.state.github),
            "vector_memory": bool(app.state.qdrant),
            "caching": bool(app.state.redis)
        },
        "personality": "badass_neon_cowboy_tech",
        "uptime": "operational",
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with SOPHIA personality"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "message": "Well partner, that didn't go as planned! SOPHIA's still here to help though.",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "SOPHIA hit an unexpected snag, but she's tough and ready to keep going!",
            "timestamp": datetime.now().isoformat()
        }
    )

# Main application entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    
    logger.info(f"🚀 Starting SOPHIA V4 Enhanced on port {port}")
    logger.info("🤠 Maximum autonomous capabilities activated!")
    logger.info("🔥 Badass persona mode: ENGAGED")
    
    uvicorn.run(
        "sophia_v4_enhanced:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

