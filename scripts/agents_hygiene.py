# scripts/agents_hygiene.py
from fastapi import APIRouter
import subprocess

router = APIRouter()

def run(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.stdout + p.stderr

@router.post("/agent/hygiene")
def hygiene():
    # Format + organize imports
    run("ruff check --fix . || true")
    run("black . || true")

    # Only return diff of working tree
    diff = run("git diff")
    summary = "format/import cleanup via ruff + black"
    return {"summary": summary, "patch": diff}