import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mount only the MCP routers to avoid unrelated import issues
from app.api.mcp.unified_mcp_router import router as unified_mcp_router
from app.api.mcp.status import router as mcp_status_router


def build_minimal_app() -> TestClient:
    app = FastAPI()
    app.include_router(unified_mcp_router)
    app.include_router(mcp_status_router)
    return TestClient(app)


def test_mcp_health_endpoint():
    client = build_minimal_app()
    resp = client.get("/api/mcp/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"healthy", "optimizing", "error"}
    assert "capabilities" in data


def test_filesystem_read_via_orchestrator():
    client = build_minimal_app()
    # Read a small repo file that should exist
    path = "README_SOPHIA.md"
    assert os.path.exists(path), f"Expected {path} to exist in repo"
    payload = {
        "method": "read_file",
        "params": {"path": path},
        "client_id": "test",
    }
    resp = client.post("/api/mcp/filesystem", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert "result" in data and "content" in data["result"]


def test_git_status_via_orchestrator():
    client = build_minimal_app()
    payload = {
        "method": "git_status",
        "params": {},
        "client_id": "test",
    }
    resp = client.post("/api/mcp/git", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert "result" in data and "clean" in data["result"]


def test_mcp_status_summary_endpoints():
    client = build_minimal_app()
    # Domain status for core (empty string) is exposed at /api/mcp/status
    resp = client.get("/api/mcp/status")
    assert resp.status_code == 200
    overall = resp.json()
    assert "domains" in overall and "sophia" in overall["domains"]

