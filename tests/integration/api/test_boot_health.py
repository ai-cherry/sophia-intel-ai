import os
import pytest

pytestmark = pytest.mark.integration


def test_boot_health_import_only():
    # Ensure app imports without crashing (no import-time settings errors)
    from app.api.main import app  # noqa: F401


def test_health_route_via_testclient():
    from fastapi.testclient import TestClient
    from app.api.main import app

    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "healthy"

