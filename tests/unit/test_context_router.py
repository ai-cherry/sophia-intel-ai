from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_app():
    app = FastAPI()
    from app.api.routers.context import router as context_router
    app.include_router(context_router)
    return app


def test_person_context_builds_sections(monkeypatch):
    # Enable a few integrations to populate sections
    monkeypatch.setenv("ASANA_PAT", "x")
    monkeypatch.setenv("LINEAR_API_KEY", "y")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "z")

    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/context/person", params={"email": "user@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "person"
    assert data["key"] == "user@example.com"
    assert isinstance(data.get("sections"), list)
    # At least one section should be present
    assert len(data["sections"]) >= 1

