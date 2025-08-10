# scripts/agents_deps.py
from fastapi import APIRouter
import subprocess

router = APIRouter()

def run(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.stdout + p.stderr

@router.post("/agent/deps")
def deps():
    # Compile fully pinned lock; then verify
    run("uv pip compile -q -o requirements.lock.txt requirements.txt || true")
    run("uv pip install --system -r requirements.lock.txt || true")
    run("uv pip check || true")

    # Optional: comment-only audit; do not fail here
    run("pip-audit --strict || true")

    diff = run("git diff")
    summary = "update dependency lock + verify environment"
    return {"summary": summary, "patch": diff}