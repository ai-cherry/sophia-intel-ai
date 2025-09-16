import hashlib
import hmac
import time
import urllib.parse as urlparse

import os
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _sign(secret: str, timestamp: str, body: str) -> str:
    basestring = f"v0:{timestamp}:{body}".encode()
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_slack_webhook_signature_e2e():
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret:
        pytest.skip("SLACK_SIGNING_SECRET not set")

    from app.api.main import app

    client = TestClient(app)
    # Simulate Slack URL verification event
    payload = {"type": "url_verification", "challenge": "test_challenge"}
    body = urlparse.urlencode(payload)
    ts = str(int(time.time()))
    sig = _sign(secret, ts, body)

    r = client.post(
        "/api/slack/webhook",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Slack-Request-Timestamp": ts,
            "X-Slack-Signature": sig,
        },
    )
    assert r.status_code == 200
    assert r.json().get("challenge") == "test_challenge"

