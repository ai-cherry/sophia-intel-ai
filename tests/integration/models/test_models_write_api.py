import os
from pathlib import Path

from fastapi.testclient import TestClient
from app.api.main import app


def test_models_write_endpoints(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "models.yaml"
    cfg.write_text(
        """
models:
  openai/gpt-4o-mini:
    enabled: true
    priority: 2
    provider: openai
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("MODELS_CONFIG_PATH", str(cfg))

    client = TestClient(app)

    # Disable model
    r = client.post("/api/models/openai/gpt-4o-mini/disable")
    assert r.status_code == 200
    models = {m["id"]: m for m in r.json()}
    assert models["openai/gpt-4o-mini"]["enabled"] is False

    # Set priority
    r = client.post("/api/models/openai/gpt-4o-mini/priority", json={"priority": 1})
    assert r.status_code == 200
    models = {m["id"]: m for m in r.json()}
    assert models["openai/gpt-4o-mini"]["priority"] == 1

    # Enable again
    r = client.post("/api/models/openai/gpt-4o-mini/enable")
    assert r.status_code == 200
    models = {m["id"]: m for m in r.json()}
    assert models["openai/gpt-4o-mini"]["enabled"] is True

