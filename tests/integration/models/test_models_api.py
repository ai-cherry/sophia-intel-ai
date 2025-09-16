from fastapi.testclient import TestClient
from app.api.main import app


def test_models_endpoint_lists_models():
    client = TestClient(app)
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]

