"""
Shim server to add missing endpoints for the UI.
This wraps the Agno Playground with additional endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import httpx

app = FastAPI(title="Agno UI Shim")

# CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PLAYGROUND_URL = "http://localhost:7777"

class TeamInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    members: Optional[List[str]] = None

class WorkflowInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None

class RunRequest(BaseModel):
    team_id: Optional[str] = None
    workflow_id: Optional[str] = None
    message: str
    additional_data: Optional[Dict[str, Any]] = None

@app.get("/healthz")
async def health():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PLAYGROUND_URL}/health", timeout=5.0)
            if response.status_code == 200:
                return {"status": "ok"}
    except:
        pass
    return {"status": "ok"}  # Return ok even if playground is down

@app.get("/agents", response_model=List[TeamInfo])
async def get_agents():
    """Get available teams/agents."""
    # Static list for now, can be made dynamic
    return [
        TeamInfo(
            id="coding_team",
            name="Coding Team",
            description="Original 5-agent team (Lead, Coder-A/B, Critic, Judge)",
            members=["Lead", "Coder-A", "Coder-B", "Critic", "Judge"]
        ),
        TeamInfo(
            id="coding_swarm",
            name="Coding Swarm",
            description="Advanced team with 3+ concurrent generators",
            members=["Lead", "Coder-A", "Coder-B", "Coder-C", "Critic", "Judge"]
        ),
        TeamInfo(
            id="coding_swarm_fast",
            name="Coding Swarm (fast)",
            description="Low-latency pool for quick iterations",
            members=["Lead", "Fast-Coder", "Critic", "Judge"]
        ),
        TeamInfo(
            id="coding_swarm_heavy",
            name="Coding Swarm (heavy)",
            description="Deep reasoning pool for complex tasks",
            members=["Lead", "Heavy-Coder", "Critic", "Judge"]
        ),
    ]

@app.get("/workflows", response_model=List[WorkflowInfo])
async def get_workflows():
    """Get available workflows."""
    return [
        WorkflowInfo(
            id="pr_lifecycle",
            name="PR Lifecycle",
            description="End-to-end PR workflow with quality gates",
            inputs={
                "priority": "Task priority (low/medium/high/critical)",
                "repo": "Repository name",
                "branch": "Target branch"
            }
        ),
        WorkflowInfo(
            id="code_review",
            name="Code Review",
            description="Comprehensive code review with critic and judge",
            inputs={
                "files": "List of files to review",
                "context": "Review context"
            }
        ),
    ]

async def stream_tokens(text: str):
    """Simulate streaming tokens."""
    words = text.split()
    for word in words:
        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        await asyncio.sleep(0.05)
    yield "data: [DONE]\n\n"

@app.post("/run/team")
async def run_team(request: RunRequest):
    """Run a team with streaming response."""
    # For now, return a simulated stream
    # In production, this would call the actual playground
    
    async def generate():
        # Simulate processing
        yield f"data: {json.dumps({'token': 'Processing with team: '})}\n\n"
        yield f"data: {json.dumps({'token': request.team_id or 'default'})}\n\n"
        yield f"data: {json.dumps({'token': '\\n\\nTask: '})}\n\n"
        yield f"data: {json.dumps({'token': request.message})}\n\n"
        
        # Simulate some work
        await asyncio.sleep(1)
        
        # Return structured response
        final_response = {
            "critic": {
                "verdict": "pass",
                "findings": {},
                "must_fix": [],
                "nice_to_have": ["Consider adding more tests"]
            },
            "judge": {
                "decision": "accept",
                "runner_instructions": [
                    "Implement the requested feature",
                    "Add comprehensive tests",
                    "Update documentation"
                ],
                "rationale": ["Code meets quality standards"]
            },
            "tool_calls": [
                {"name": "code_search", "args": {"query": "authentication"}},
                {"name": "file_read", "args": {"path": "app/main.py"}}
            ]
        }
        
        yield f"data: {json.dumps({'final': final_response})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/run/workflow")
async def run_workflow(request: RunRequest):
    """Run a workflow with streaming response."""
    
    async def generate():
        # Simulate workflow steps
        steps = [
            "Initializing workflow...",
            "Running preflight checks...",
            "Executing coding debate...",
            "Running quality gates...",
            "Finalizing results..."
        ]
        
        for step in steps:
            yield f"data: {json.dumps({'token': step + '\\n'})}\n\n"
            await asyncio.sleep(0.5)
        
        # Return structured response with gates
        final_response = {
            "workflow_result": "completed",
            "gates": {
                "accuracy": {"passed": True, "score": 8.5},
                "reliability": {"passed": True}
            },
            "judge": {
                "decision": "merge",
                "runner_instructions": [
                    "Merge the PR",
                    "Deploy to staging"
                ]
            }
        }
        
        yield f"data: {json.dumps({'final': final_response})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting UI Shim Server on http://localhost:8888")
    print("📍 Point your UI to this endpoint instead of :7777")
    uvicorn.run(app, host="0.0.0.0", port=8888)