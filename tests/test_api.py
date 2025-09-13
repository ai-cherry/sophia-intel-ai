"""Test API endpoints"""
from fastapi.testclient import TestClient
def test_chat_endpoint(client: TestClient):
    """Test chat message endpoint"""
    response = client.post("/api/chat", json={"text": "Hello, Sophia!"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "status" in data
def test_orchestration_endpoint(client: TestClient):
    """Test orchestration endpoint"""
    response = client.post(
        "/api/orchestration",
        json={"task": "test_task", "agents": ["agent1", "agent2"], "parameters": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "status" in data
def test_memory_store_endpoint(client: TestClient):
    """Test memory storage endpoint"""
    response = client.post(
        "/api/memory/store",
        json={"key": "test_key", "value": {"data": "test_value"}, "metadata": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "test_key"
    assert "timestamp" in data
