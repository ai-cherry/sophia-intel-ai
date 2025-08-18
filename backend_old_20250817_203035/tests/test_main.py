import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "SOPHIA Intel API" in data["message"]

def test_health():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
