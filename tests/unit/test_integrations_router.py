from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_app():
    app = FastAPI()
    from app.api.routers.integrations import router as integrations_router
    app.include_router(integrations_router)
    return app


def test_catalog_reflects_env(monkeypatch):
    # Enable only Asana
    monkeypatch.setenv("ASANA_PAT", "x")
    for k in [
        "LINEAR_API_KEY",
        "SLACK_BOT_TOKEN",
        "AIRTABLE_PAT",
        "HUBSPOT_PRIVATE_APP_TOKEN",
        "INTERCOM_ACCESS_TOKEN",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "SALESFORCE_REFRESH_TOKEN",
        "LATTICE_API_TOKEN",
        "GONG_ACCESS_KEY",
        "GONG_CLIENT_SECRET",
    ]:
        monkeypatch.delenv(k, raising=False)

    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/integrations/catalog")
    assert resp.status_code == 200
    data = resp.json()
    names = {i["name"]: i for i in data["integrations"]}
    assert names["asana"]["enabled"] is True
    assert names["linear"]["enabled"] is False

