from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os, time

app = FastAPI(title="sophia-research-mcp", version="4.2.0")

@app.get("/healthz")
def healthz():
    # NO provider calls here; never crash
    return {"status": "ok", "service": "sophia-research-mcp", "version": "4.2.0"}

def _provider_key():
    return os.getenv("TAVILY_API_KEY") or os.getenv("SERPER_API_KEY")

@app.post("/search")
async def search(body: dict):
    # Lazy init so missing secrets don't crash startup
    key = _provider_key()
    if not key:
        return {"status":"failure","errors":[{"provider":"research","code":"missing-secret"}]}
    q = (body or {}).get("query") or ""
    # TODO: real provider call; return normalized body
    return {
        "status": "success",
        "results": [{"title":"placeholder", "url":"https://example.com", "snippet": f"query={q}"}],
        "summary": {"text": f"Searched for {q}", "confidence": 0.3, "model": "n/a", "sources":[]}
    }

