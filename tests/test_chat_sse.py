from fastapi.testclient import TestClient
from bridge.api import app


def test_sophia_chat_sse_start_and_stream():
    client = TestClient(app)
    # Start stream
    r = client.post("/api/sophia/chat/start", json={"message": "Hello", "context": {"path": "/test"}})
    assert r.status_code == 200
    data = r.json()
    assert "stream_id" in data and "stream_url" in data

    # Connect to SSE
    with client.stream("GET", data["stream_url"]) as resp:
        assert resp.status_code == 200
        # Read a few lines to ensure stream yields start/content/complete eventually
        # Note: we only check that at least one line arrives
        read_any = False
        for chunk in resp.iter_lines():
            if chunk:
                read_any = True
                break
        assert read_any, "No SSE data received"

