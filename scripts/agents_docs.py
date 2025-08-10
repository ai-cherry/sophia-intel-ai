# scripts/agents_docs.py
from fastapi import APIRouter
import subprocess, json, pathlib

router = APIRouter()

def run(c: str) -> str:
    p = subprocess.run(c, shell=True, capture_output=True, text=True)
    return p.stdout

@router.post("/agent/docs")
def docs():
    # Example: ensure README has a Runbook section
    readme = pathlib.Path("README.md")
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if "### Run in Codespaces" not in text:
        text += "\n\n### Run in Codespaces\n" \
                "- MCP: `uvicorn mcp_servers.unified_mcp_server:app --host 0.0.0.0 --port 8001 --reload`\n" \
                "- API: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`\n" \
                "- Agent: `uvicorn scripts.agno_api:app --host 0.0.0.0 --port 7777 --reload`\n"
        readme.write_text(text, encoding="utf-8")
    diff = run("git diff")
    return {"summary":"docs/runbook refreshed","patch":diff}