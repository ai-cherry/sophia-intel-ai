from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sentry_sdk
import os
import logging
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment="production"
)

# FastAPI app with CORS
app = FastAPI(title="SOPHIA Intel - AI Swarm Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ChatRequest(BaseModel):
    query: str
    use_case: str = "general"

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    result: str
    status: str
    agents_used: List[str]

# OpenRouter client
class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(self, query: str, model: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sophia-intel.pay-ready.com",
                        "X-Title": "SOPHIA Intel"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": query}]
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Token usage: {data.get('usage', {})}")
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenRouter API error: {str(e)}")
                sentry_sdk.capture_exception(e)
                raise

# Initialize client
openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)

# Model selection logic based on LATEST OpenRouter leaderboard
async def select_model(query: str, use_case: str) -> str:
    try:
        if "complex" in use_case.lower() or len(query.split()) > 50:
            return "anthropic/claude-sonnet-4"  # #1 on leaderboard
        elif "code" in use_case.lower():
            return "qwen/qwen3-coder"  # #6 on leaderboard
        elif "reasoning" in use_case.lower():
            return "deepseek/deepseek-v3-0324"  # #5 on leaderboard
        else:
            return "google/gemini-2.0-flash"  # #2 on leaderboard
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        return "google/gemini-2.5-flash"  # #3 fallback

# SOPHIA's LangGraph Agent State
class AgentState(BaseModel):
    messages: List[Any]
    current_agent: str
    task_complete: bool = False
    final_result: str = ""
    agents_used: List[str] = []

# Agent Definitions
class PlannerAgent:
    def __init__(self):
        self.name = "Planner"
        
    async def invoke(self, input_data: Dict) -> Dict:
        try:
            query = input_data.get("input", "")
            chat_history = input_data.get("chat_history", [])
            
            # Use OpenRouter for planning
            planning_prompt = f"As a task planner, break down this task into actionable steps: {query}"
            result = await openrouter_client.generate(planning_prompt, "anthropic/claude-sonnet-4")
            
            return {"output": result}
        except Exception as e:
            logger.error(f"Planner agent error: {str(e)}")
            return {"output": f"Planning failed: {str(e)}"}

class CoderAgent:
    def __init__(self):
        self.name = "Coder"
        
    async def invoke(self, input_data: Dict) -> Dict:
        try:
            query = input_data.get("input", "")
            chat_history = input_data.get("chat_history", [])
            
            # Extract plan from previous messages
            plan_context = ""
            for msg in chat_history:
                if hasattr(msg, 'content'):
                    plan_context += msg.content + "\n"
            
            coding_prompt = f"Based on this plan:\n{plan_context}\n\nImplement the solution with production-ready code."
            result = await openrouter_client.generate(coding_prompt, "qwen/qwen3-coder")
            
            return {"output": result}
        except Exception as e:
            logger.error(f"Coder agent error: {str(e)}")
            return {"output": f"Coding failed: {str(e)}"}

class ReviewerAgent:
    def __init__(self):
        self.name = "Reviewer"
        
    async def invoke(self, input_data: Dict) -> Dict:
        try:
            query = input_data.get("input", "")
            chat_history = input_data.get("chat_history", [])
            
            # Extract code from previous messages
            code_context = ""
            for msg in chat_history:
                if hasattr(msg, 'content'):
                    code_context += msg.content + "\n"
            
            review_prompt = f"Review this implementation for quality, security, and production readiness:\n{code_context}"
            result = await openrouter_client.generate(review_prompt, "anthropic/claude-sonnet-4")
            
            return {"output": result}
        except Exception as e:
            logger.error(f"Reviewer agent error: {str(e)}")
            return {"output": f"Review failed: {str(e)}"}

# Initialize agents
planner_agent = PlannerAgent()
coder_agent = CoderAgent()
reviewer_agent = ReviewerAgent()

# Create LangGraph workflow
def create_swarm_graph():
    workflow = StateGraph(AgentState)
    
    async def planner_node(state: AgentState):
        logger.info("Executing Planner Agent")
        system_msg = SystemMessage(content="You are a strategic task planner.")
        messages = [system_msg] + state.messages
        result = await planner_agent.invoke({"input": "", "chat_history": messages})
        
        new_agents_used = state.agents_used + ["Planner"]
        return AgentState(
            messages=state.messages + [AIMessage(content=result["output"])],
            current_agent="coder",
            agents_used=new_agents_used
        )

    async def coder_node(state: AgentState):
        logger.info("Executing Coder Agent")
        system_msg = SystemMessage(content="You are an expert software developer.")
        messages = [system_msg] + state.messages
        result = await coder_agent.invoke({"input": "", "chat_history": messages})
        
        new_agents_used = state.agents_used + ["Coder"]
        return AgentState(
            messages=state.messages + [AIMessage(content=result["output"])],
            current_agent="reviewer",
            agents_used=new_agents_used
        )

    async def reviewer_node(state: AgentState):
        logger.info("Executing Reviewer Agent")
        system_msg = SystemMessage(content="You are a code reviewer. Evaluate quality and approve for production.")
        messages = [system_msg] + state.messages
        result = await reviewer_agent.invoke({"input": "", "chat_history": messages})
        
        new_agents_used = state.agents_used + ["Reviewer"]
        return AgentState(
            messages=state.messages + [AIMessage(content=result["output"])],
            current_agent="end",
            task_complete=True,
            final_result=result["output"],
            agents_used=new_agents_used
        )

    # Add nodes to workflow
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # Define routing
    def route_agent(state: AgentState):
        if state.current_agent == "planner":
            return "planner"
        elif state.current_agent == "coder":
            return "coder"
        elif state.current_agent == "reviewer":
            return "reviewer"
        else:
            return END

    workflow.set_conditional_entry_point(route_agent)
    workflow.add_conditional_edges(
        "planner",
        lambda _: "coder"
    )
    workflow.add_conditional_edges(
        "coder",
        lambda _: "reviewer"
    )
    workflow.add_conditional_edges(
        "reviewer",
        lambda state: END if state.task_complete else "planner"
    )
    
    return workflow.compile()

# Initialize compiled workflow graph
swarm_graph = create_swarm_graph()

# API Endpoints
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "sentry": "connected" if os.getenv("SENTRY_DSN") else "disconnected",
        "llm_providers": ["openrouter"],
        "swarm_enabled": True,
        "deployment_timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug/routes")
async def debug_routes():
    return [str(route) for route in app.routes]

@app.post("/api/v1/chat/enhanced")
async def enhanced_chat(request: ChatRequest):
    try:
        model = await select_model(request.query, request.use_case)
        logger.info(f"Selected model: {model} for query: {request.query[:50]}...")
        response = await openrouter_client.generate(request.query, model)
        logger.info(f"Enhanced chat response: {response[:50]}...")
        return {"response": response, "model_used": model}
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/swarm/execute", response_model=TaskResponse)
async def execute_swarm_task(request: TaskRequest):
    """Execute task through LangGraph agent swarm"""
    try:
        logger.info(f"Executing swarm task: {request.task[:100]}...")
        
        initial_state = AgentState(
            messages=[HumanMessage(content=request.task)],
            current_agent="planner",
            agents_used=[]
        )
        
        # Execute workflow with timeout protection
        async def run_graph():
            # Convert to dict for LangGraph
            state_dict = {
                "messages": initial_state.messages,
                "current_agent": initial_state.current_agent,
                "task_complete": initial_state.task_complete,
                "final_result": initial_state.final_result,
                "agents_used": initial_state.agents_used
            }
            return await asyncio.get_event_loop().run_in_executor(
                None, swarm_graph.invoke, state_dict
            )
            
        # Create task with timeout
        task_result = await asyncio.wait_for(run_graph(), timeout=120.0)
        
        logger.info(f"Swarm task completed. Agents used: {task_result.get('agents_used', [])}")
        
        return TaskResponse(
            result=task_result.get("final_result", "Task completed"),
            status="completed",
            agents_used=task_result.get("agents_used", ["Planner", "Coder", "Reviewer"])
        )
            
    except asyncio.TimeoutError:
        logger.error("Swarm task timeout exceeded")
        raise HTTPException(status_code=408, detail="Task timeout exceeded")
    except Exception as e:
        logger.error(f"Swarm execution error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Swarm execution failed: {str(e)}")

@app.get("/api/v1/swarm/status")
async def swarm_status():
    """Get swarm system status"""
    return {
        "swarm_enabled": True,
        "agents": ["Planner", "Coder", "Reviewer"],
        "workflow_compiled": swarm_graph is not None,
        "openrouter_connected": OPENROUTER_API_KEY is not None
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

