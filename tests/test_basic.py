"""Test health endpoints"""


def test_health_endpoint(client):
    """Test /health returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "2.0.0"


def test_ready_endpoint(client):
    """Test /ready returns correct status"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert "timestamp" in data


def test_root_endpoint(client):
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sophia AI Platform API"
    assert "endpoints" in data


def test_docs_endpoint(client):
    """Test Swagger docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
