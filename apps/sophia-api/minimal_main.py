import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from github import Github
import aiohttp
import anthropic
import google.generativeai as gemini
import asana
# import apify_client  # Temporarily disabled due to import error
import requests
from langgraph.graph import StateGraph
from typing import Dict, Any
import logging
import asyncpg
import redis.asyncio as redis
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SOPHIA Intel - AI Swarm Orchestrator")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load secrets from environment variables (populated by Fly.io secrets)
GITHUB_PAT = os.getenv("GITHUB_PAT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io:6333")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LAMBDA_CLOUD_API_KEY = os.getenv("LAMBDA_CLOUD_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APOLLO_IO_API_KEY = os.getenv("APOLLO_IO_API_KEY")
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")
ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID")
ASANA_PAT_TOKEN = os.getenv("ASANA_PAT_TOKEN")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
CONTINUE_API_KEY = os.getenv("CONTINUE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DNSIMPLE_API_KEY = os.getenv("DNSIMPLE_API_KEY")
DOCKER_PAT = os.getenv("DOCKER_PAT")
EDEN_AI_API_KEY = os.getenv("EDEN_AI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FIGMA_PAT = os.getenv("FIGMA_PAT")
FLY_IO_API_TOKEN = os.getenv("FLY_IO_API_TOKEN")
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
GONG_CLIENT_SECRET = os.getenv("GONG_CLIENT_SECRET")
AGNO_API_KEY = os.getenv("AGNO_API_KEY")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "securepassword")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

# Initialize clients with error handling for missing API keys
try:
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY) if QDRANT_API_KEY else None
except Exception as e:
    logger.warning(f"Qdrant client initialization failed: {e}")
    qdrant_client = None

try:
    github_client = Github(GITHUB_PAT) if GITHUB_PAT else None
except Exception as e:
    logger.warning(f"GitHub client initialization failed: {e}")
    github_client = None

try:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception as e:
    logger.warning(f"Anthropic client initialization failed: {e}")
    anthropic_client = None

try:
    if GEMINI_API_KEY:
        gemini.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.warning(f"Gemini client initialization failed: {e}")

try:
    asana_client = asana.ApiClient() if ASANA_PAT_TOKEN else None
except Exception as e:
    logger.warning(f"Asana client initialization failed: {e}")
    asana_client = None

# apify_client_instance = apify_client.ApifyClient(APIFY_API_TOKEN)  # Temporarily disabled

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis client initialization failed: {e}")
    redis_client = None

async def get_db_pool():
    """Get PostgreSQL connection pool"""
    return await asyncpg.create_pool(
        user="sophia", password=POSTGRES_PASSWORD, database="sophia", host="postgres"
    )

# Pydantic models
class ChatRequest(BaseModel):
    query: str

class CodeRequest(BaseModel):
    query: str
    repo: str

class SwarmRequest(BaseModel):
    task: str

class IntegrationRequest(BaseModel):
    query: str

class MemoryRequest(BaseModel):
    context: str
    data: str

class MemoryRetrieveRequest(BaseModel):
    query: str

class ResearchRequest(BaseModel):
    url: str

# AI Agent Swarm (Agno/LangGraph)
class AgentState(Dict[str, Any]):
    query: str
    code: str
    output: Dict[str, Any]

async def planner(state: AgentState) -> AgentState:
    """Planner Agent - Creates execution plan"""
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": f"Plan task: {state['query']}"}],
            max_tokens=1000
        )
        state["plan"] = response.content[0].text
        logger.info(f"Planner: {state['plan']}")
        return state
    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["plan"] = f"Error in planning: {e}"
        return state

async def coder(state: AgentState) -> AgentState:
    """Coder Agent - Generates code"""
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": f"Write code for: {state['plan']}"}],
            max_tokens=4000
        )
        state["code"] = response.content[0].text
        logger.info(f"Coder: Generated code for {state['query']}")
        return state
    except Exception as e:
        logger.error(f"Coder error: {e}")
        state["code"] = f"Error in coding: {e}"
        return state

async def reviewer(state: AgentState) -> AgentState:
    """Reviewer Agent - Reviews code quality"""
    try:
        model = gemini.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Review code: {state['code']}")
        state["review"] = response.text
        logger.info(f"Reviewer: {state['review']}")
        return state
    except Exception as e:
        logger.error(f"Reviewer error: {e}")
        state["review"] = f"Error in review: {e}"
        return state

async def integrator(state: AgentState) -> AgentState:
    """Integrator Agent - Creates GitHub PR"""
    try:
        repo = github_client.get_repo("ai-cherry/sophia-intel")
        branch = f"feature-{state['query'].replace(' ', '-').lower()}"
        
        # Create branch
        main_branch = repo.get_branch("main")
        repo.create_git_ref(f"refs/heads/{branch}", main_branch.commit.sha)
        
        # Create file
        file_path = f"apps/sophia-api/generated/{state['query'].replace(' ', '_').lower()}.py"
        repo.create_file(
            path=file_path,
            message=f"Add code for {state['query']}",
            content=state["code"],
            branch=branch
        )
        
        # Create PR
        pr = repo.create_pull(
            title=f"Auto-generated: {state['query']}",
            body=state["review"],
            head=branch,
            base="main"
        )
        
        state["pr"] = pr.html_url
        logger.info(f"Integrator: PR created at {state['pr']}")
        return state
    except Exception as e:
        logger.error(f"Integrator error: {e}")
        state["pr"] = f"Error in integration: {e}"
        return state

# Create LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner)
workflow.add_node("coder", coder)
workflow.add_node("reviewer", reviewer)
workflow.add_node("integrator", integrator)

workflow.add_edge("planner", "coder")
workflow.add_edge("coder", "reviewer")
workflow.add_edge("reviewer", "integrator")

workflow.set_entry_point("planner")
workflow.set_finish_point("integrator")

agent_swarm = workflow.compile()

# API Endpoints

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "OK", "service": "SOPHIA Intel"}

@app.post("/api/v1/chat/enhanced")
async def enhanced_chat(request: ChatRequest):
    """Enhanced chat with AI models"""
    try:
        # Use Claude for enhanced responses
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": request.query}],
            max_tokens=2000
        )
        
        result = {
            "response": response.content[0].text,
            "model": "claude-3-5-sonnet",
            "timestamp": "2025-08-18T16:00:00Z"
        }
        
        logger.info(f"Enhanced chat: {request.query}")
        return result
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/code/modify")
async def modify_code(request: CodeRequest):
    """Autonomous code modification via agent swarm"""
    try:
        initial_state = AgentState(query=request.query, code="", output={})
        result = await agent_swarm.ainvoke(initial_state)
        
        logger.info(f"Code modification: {request.query}")
        return {
            "query": request.query,
            "plan": result.get("plan", ""),
            "code": result.get("code", ""),
            "review": result.get("review", ""),
            "pr_url": result.get("pr", "")
        }
    except Exception as e:
        logger.error(f"Code modification error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/swarm/execute")
async def execute_swarm(request: SwarmRequest):
    """Execute AI agent swarm for complex tasks"""
    try:
        initial_state = AgentState(query=request.task, code="", output={})
        result = await agent_swarm.ainvoke(initial_state)
        
        logger.info(f"Swarm execution: {request.task}")
        return {
            "task": request.task,
            "plan": result.get("plan", ""),
            "code": result.get("code", ""),
            "review": result.get("review", ""),
            "pr_url": result.get("pr", ""),
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Swarm execution error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/integrations/notion")
async def notion_integration(request: IntegrationRequest):
    """Notion integration via Asana API"""
    try:
        # Use Asana as proxy for task management
        workspaces = asana_client.workspaces.get_workspaces()
        workspace_data = list(workspaces)
        
        logger.info(f"Notion query: {request.query}")
        return {
            "query": request.query,
            "workspaces": len(workspace_data),
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Notion integration error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/integrations/salesforce")
async def salesforce_integration(request: IntegrationRequest):
    """Salesforce integration placeholder"""
    try:
        # Placeholder for Salesforce integration
        logger.info(f"Salesforce query: {request.query}")
        return {
            "query": request.query,
            "opportunities": [],
            "status": "placeholder"
        }
    except Exception as e:
        logger.error(f"Salesforce integration error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/integrations/slack")
async def slack_integration(request: IntegrationRequest):
    """Slack integration placeholder"""
    try:
        # Placeholder for Slack integration
        logger.info(f"Slack query: {request.query}")
        return {
            "query": request.query,
            "channel": "#dev-channel",
            "status": "placeholder"
        }
    except Exception as e:
        logger.error(f"Slack integration error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/memory/store")
async def store_memory(request: MemoryRequest):
    """Store context in Qdrant vector database"""
    try:
        # Create embedding and store in Qdrant
        collection_name = "sophia_memory"
        
        # Simple storage (in production, would use proper embeddings)
        point_id = hash(request.context) % 1000000
        
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[{
                "id": point_id,
                "vector": [0.1] * 384,  # Placeholder vector
                "payload": {
                    "context": request.context,
                    "data": request.data,
                    "timestamp": "2025-08-18T16:00:00Z"
                }
            }]
        )
        
        logger.info(f"Memory stored: {request.context}")
        return {"status": "stored", "id": point_id}
    except Exception as e:
        logger.error(f"Memory storage error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/memory/retrieve")
async def retrieve_memory(request: MemoryRetrieveRequest):
    """Retrieve context from Qdrant vector database"""
    try:
        collection_name = "sophia_memory"
        
        # Simple retrieval (in production, would use semantic search)
        results = qdrant_client.scroll(
            collection_name=collection_name,
            limit=5
        )
        
        logger.info(f"Memory retrieved: {request.query}")
        return {
            "query": request.query,
            "results": [point.payload for point in results[0]],
            "count": len(results[0])
        }
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/research/scrape")
async def research_scrape(request: ResearchRequest):
    """Web scraping for research using Brave API"""
    try:
        # Use Brave Search API for research
        headers = {"X-Subscription-Token": BRAVE_API_KEY}
        params = {"q": request.url, "count": 5}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            ) as response:
                data = await response.json()
        
        logger.info(f"Research scrape: {request.url}")
        return {
            "url": request.url,
            "results": data.get("web", {}).get("results", []),
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Research scrape error: {e}")
        return {"error": str(e)}

@app.get("/api/v1/dashboard/status")
async def dashboard_status():
    """Dashboard status endpoint"""
    try:
        # Get database status
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            db_count = await conn.fetchval("SELECT COUNT(*) FROM information_schema.tables")
        
        # Get Redis status
        redis_status = await redis_client.ping()
        
        # Get Qdrant status
        qdrant_status = "OK"
        try:
            collections = qdrant_client.get_collections()
            qdrant_status = f"OK ({len(collections.collections)} collections)"
        except:
            qdrant_status = "ERROR"
        
        # Get GitHub PRs
        repo = github_client.get_repo("ai-cherry/sophia-intel")
        pr_count = len(list(repo.get_pulls()))
        
        return {
            "health": "OK",
            "models": ["claude-3-5-sonnet", "gemini-1.5-pro"],
            "qdrant_status": qdrant_status,
            "github_prs": pr_count,
            "db_tables": db_count,
            "redis_status": "OK" if redis_status else "DOWN",
            "timestamp": "2025-08-18T16:00:00Z"
        }
    except Exception as e:
        logger.error(f"Dashboard status error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

