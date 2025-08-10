from agno.playground import Playground
from fastapi import FastAPI
from agents.coding_agent import CodingAgent
from config.config import settings
from pydantic import BaseModel

coding_agent = CodingAgent()
playground = Playground(agents=[])  # Keep Agno chat UI optional
app = FastAPI()

class CodeReq(BaseModel):
    session_id: str
    code: str
    query: str

@app.post("/agent/coding")
async def agent_coding(req: CodeReq):
    return await coding_agent.execute("code-edit", req.dict())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)