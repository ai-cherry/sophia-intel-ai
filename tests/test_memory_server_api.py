from fastapi.testclient import TestClient

from mcp.memory_server import app


def test_memory_session_crud():
    client = TestClient(app)
    # health
    h = client.get("/health")
    assert h.status_code == 200

    # create session id manually (memory_server expects PUT via store to create)
    session_id = "test-session"
    # ensure empty read creates meta
    r = client.get(f"/sessions/{session_id}/memory")
    assert r.status_code == 200
    # store a message
    s = client.post(
        f"/sessions/{session_id}/memory",
        json={"content": "hello", "role": "user"},
    )
    assert s.status_code == 200
    # read back
    r2 = client.get(f"/sessions/{session_id}/memory")
    assert r2.status_code == 200
    data = r2.json()
    assert data.get("session_id") == session_id
    assert len(data.get("entries", [])) >= 1

