"""Test health and status endpoints"""
import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient):
    """Test /health returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data
    assert "environment" in data

def test_ready_endpoint(client: TestClient):
    """Test /ready endpoint"""
    response = client.get("/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert "timestamp" in data
    
    # Should have database and redis checks
    assert "database" in data["checks"]
    assert "redis" in data["checks"]

def test_root_endpoint(client: TestClient):
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Sophia AI Platform API"
    assert data["version"] == "2.0.0"
    assert data["status"] == "running"
    assert "endpoints" in data
    
    # Check nested endpoints
    assert "health" in data["endpoints"]
    assert "api" in data["endpoints"]

def test_docs_accessible(client: TestClient):
    """Test Swagger docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Check for Prometheus format
    content = response.text
    assert "http_" in content or "python_" in content or "process_" in content

def test_request_id_header(client: TestClient):
    """Test that X-Request-ID header is added to responses"""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers

