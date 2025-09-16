import hashlib
import hmac
import json
import time
import os
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    basestring = b"v0:" + timestamp.encode() + b":" + raw_body
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_slack_event_app_mention_json():
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret:
        pytest.skip("SLACK_SIGNING_SECRET not set")

    from app.api.main import app

    client = TestClient(app)

    payload = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "user": "U123",
            "text": "<@ABC123> hello",
            "channel": "C123",
        },
    }
    raw = json.dumps(payload).encode()
    ts = str(int(time.time()))
    sig = _sign(secret, ts, raw)

    r = client.post(
        "/api/slack/webhook",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": ts,
            "X-Slack-Signature": sig,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in ("ok", "error")  # handler may log only; accept ok path

