import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
app = FastAPI()
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
        {
            "id": "coding-team",
            "name": "Coding Team",
            "description": "5 agents for coding tasks",
        },
        {
            "id": "coding-swarm",
            "name": "Coding Swarm",
            "description": "Advanced swarm intelligence",
        },
        {
            "id": "coding-swarm-fast",
            "name": "Coding Swarm (fast)",
            "description": "Fast coding swarm",
        },
        {
            "id": "coding-swarm-heavy",
            "name": "Coding Swarm (heavy)",
            "description": "Heavy-duty coding swarm",
        },
    ]
@app.get("/workflows")
async def get_workflows():
    return [
        {
            "id": "pr-lifecycle",
            "name": "PR Lifecycle",
            "description": "Complete PR workflow",
        },
        {
            "id": "code-review",
            "name": "Code Review",
            "description": "Automated code review",
        },
    ]
@app.post("/teams/run")
async def run_team_ultra_debug(request: Request):
    print(f"\n{'='*60}")
    print("ULTRA DEBUG: INCOMING REQUEST")
    print(f"{'='*60}")
    # Headers
    print("Headers:")
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    # Raw body
    raw_body = await request.body()
    print(f"\nRaw Body ({len(raw_body)} bytes):")
    print(f"  {raw_body!r}")
    try:
        # Parse JSON
        json_data = json.loads(raw_body)
        print("\nParsed JSON:")
        print(f"  {json.dumps(json_data, indent=2)}")
        # Check each field
        print("\nField Analysis:")
        print(
            f"  message: {json_data.get('message')!r} (type: {type(json_data.get('message'))})"
        )
        print(
            f"  team_id: {json_data.get('team_id')!r} (type: {type(json_data.get('team_id'))})"
        )
        print(
            f"  additional_data: {json_data.get('additional_data')!r} (type: {type(json_data.get('additional_data'))})"
        )
        # Try Pydantic validation
        print("\nPydantic Validation:")
        try:
            validated = TeamRequest(**json_data)
            print(f"  SUCCESS: {validated}")
            # Generate successful response
            def generate_response():
                yield f"data: {json.dumps({'token': f'✅ SUCCESS! Team: {validated.team_id}, Message: {validated.message}'})}\n\n"
                yield f"data: {json.dumps({'token': '\n🎉 Validation passed!'})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(
                generate_response(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        except ValidationError as ve:
            print(f"  VALIDATION ERROR: {ve}")
            print("  Error details:")
            for error in ve.errors():
                print(f"    - {error}")
            raise HTTPException(status_code=422, detail=str(ve))
    except json.JSONDecodeError as je:
        print(f"\nJSON DECODE ERROR: {je}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {je}")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/workflows/run")
async def run_workflow(request: TeamRequest):
    def generate_response():
        yield f"data: {json.dumps({'token': 'Workflow started!'})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate_response(), media_type="text/event-stream")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)
