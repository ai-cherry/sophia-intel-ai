import os
from typing import Dict


def test_registry_enabled_env_driven(monkeypatch):
    # Import lazily after setting env
    monkeypatch.setenv("ASANA_PAT", "x")
    monkeypatch.setenv("LINEAR_API_KEY", "y")
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)

    from app.integrations.registry import registry

    enabled: Dict[str, object] = registry.enabled()
    assert "asana" in enabled and enabled["asana"].enabled is True
    assert "linear" in enabled and enabled["linear"].enabled is True
    # Slack should be disabled without token
    assert "slack" in enabled and enabled["slack"].enabled is False

