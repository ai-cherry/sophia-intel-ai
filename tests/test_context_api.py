import os
import pytest
from fastapi.testclient import TestClient


def test_context_person_sets_request_id_and_metrics():
    # Import unified server app
    from sophia_unified_server import app
    client = TestClient(app)
    # Call person context
    r = client.get("/api/context/person", params={"email": "john@example.com"})
    assert r.status_code == 200
    assert r.json().get("type") == "person"
    # Check correlation header present
    assert "X-Request-ID" in r.headers
    # Metrics should contain at least the total counter after call
    m = client.get("/metrics")
    assert m.status_code == 200
    assert "sophia_context_requests_total" in m.text or "context_requests_total" in m.text

