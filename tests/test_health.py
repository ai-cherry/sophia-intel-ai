"""Basic health check tests for the Sophia platform."""

from fastapi.testclient import TestClient
from backend.main import app
from mcp_servers.unified_mcp_server import app as mcp_app


def test_backend_health():
    """Test backend health endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "env" in data


def test_backend_metrics():
    """Test backend metrics endpoint."""
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_mcp_server_docs():
    """Test MCP server documentation endpoint."""
    client = TestClient(mcp_app)
    response = client.get("/docs")
    assert response.status_code == 200


# TODO: Add more comprehensive tests
# - Test agent execution
# - Test memory storage/retrieval
# - Test configuration loading
# - Test service integrations
