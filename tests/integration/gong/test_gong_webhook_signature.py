import hmac
import hashlib
import os
import pytest

pytestmark = pytest.mark.integration


def test_gong_webhook_signature_valid(monkeypatch):
    from app.api.routers.gong_webhook import GongWebhookHandler

    secret = "test-secret"
    monkeypatch.setenv("GONG_WEBHOOK_SECRET", secret)
    handler = GongWebhookHandler()

    payload = b'{"hello": "world"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert handler.verify_signature(payload, f"sha256={sig}") is True


def test_gong_webhook_signature_invalid(monkeypatch):
    from app.api.routers.gong_webhook import GongWebhookHandler

    monkeypatch.setenv("GONG_WEBHOOK_SECRET", "test-secret")
    handler = GongWebhookHandler()

    payload = b"{}"
    assert handler.verify_signature(payload, "sha256=deadbeef") is False

