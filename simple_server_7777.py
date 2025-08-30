from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import time

app = FastAPI()

# Enable CORS for the UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TeamRequest(BaseModel):
    message: str
    team_id: str = None
    additional_data: dict = None

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.get("/teams")
async def get_teams():
    return [
        {"id": "coding-team", "name": "Coding Team", "description": "5 agents for coding tasks"},
        {"id": "coding-swarm", "name": "Coding Swarm", "description": "Advanced swarm intelligence"},
        {"id": "coding-swarm-fast", "name": "Coding Swarm (fast)", "description": "Fast coding swarm"},
        {"id": "coding-swarm-heavy", "name": "Coding Swarm (heavy)", "description": "Heavy-duty coding swarm"}
    ]

@app.get("/workflows")
async def get_workflows():
    return [
        {"id": "pr-lifecycle", "name": "PR Lifecycle", "description": "Complete PR workflow"},
        {"id": "code-review", "name": "Code Review", "description": "Automated code review"}
    ]

def generate_response(request: TeamRequest):
    # Simulate streaming response
    yield f"data: {json.dumps({'token': 'Starting task with team: '})}\n\n"
    yield f"data: {json.dumps({'token': request.team_id or 'default'})}\n\n"
    
    task_prefix = "\n\nTask: "
    yield f"data: {json.dumps({'token': task_prefix})}\n\n"
    yield f"data: {json.dumps({'token': request.message})}\n\n"
    
    yield f"data: {json.dumps({'token': '\n\n🔄 Processing...'})}\n\n"
    time.sleep(1)
    
    yield f"data: {json.dumps({'token': '\n✅ Critic Review: PASS'})}\n\n"
    time.sleep(0.5)
    
    yield f"data: {json.dumps({'token': '\n⚖️ Judge Decision: ACCEPT'})}\n\n"
    time.sleep(0.5)
    
    yield f"data: {json.dumps({'token': '\n🚪 Runner Gate: ALLOWED'})}\n\n"
    time.sleep(0.5)
    
    yield f"data: {json.dumps({'token': '\n\n📊 Task completed successfully!'})}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/teams/run")
async def run_team(request: TeamRequest):
    return StreamingResponse(
        generate_response(request),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/workflows/run")
async def run_workflow(request: TeamRequest):
    return StreamingResponse(
        generate_response(request),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)
