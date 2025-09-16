import json
from fastapi.testclient import TestClient
from app.api.main import app


def test_chat_stream_endpoint_smoke(monkeypatch):
    client = TestClient(app)

    # Monkeypatch chat service to return a deterministic response
    from app.api.routers import chat as chat_router

    async def fake_process(query, context):
        return {
            "response": "This is a streamed response.",
            "trace_id": "test-trace",
            "sources": [],
            "confidence": 0.9,
            "citations": [],
        }

    chat_router.chat_service.process_query = fake_process  # type: ignore

    r = client.post("/api/chat/stream", json={"query": "hello", "context": {}})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/event-stream")

    # Validate that at least start and end events present
    body = r.text
    assert "event: start" in body
    assert "event: end" in body

