from fastapi.testclient import TestClient

from bridge.api import app


def test_projects_overview_defensive():
    client = TestClient(app)
    r = client.get("/api/projects/overview")
    assert r.status_code == 200
    data = r.json()
    # Defensive contract: always returns structured payload
    assert "generated_at" in data
    assert isinstance(data.get("notes"), list)
    assert isinstance(data.get("major_projects"), list)
    assert isinstance(data.get("sources"), dict)


def test_gong_calls_defensive():
    client = TestClient(app)
    r = client.get("/api/gong/calls")
    assert r.status_code == 200
    data = r.json()
    assert "configured" in data
    assert isinstance(data.get("calls", []), list)


def test_brain_ingest_dedup_contract():
    client = TestClient(app)
    payload = {
        "documents": [
            {"text": "Hello world", "metadata": {"source": "test"}},
            {"text": "Hello world", "metadata": {"source": "test-dup"}},
        ],
        "domain": "SOPHIA",
        "deduplicate": True,
    }
    r = client.post("/api/brain/ingest", json=payload)
    # If memory store is available, should return counts; if not, clear 500 with message
    if r.status_code == 200:
        data = r.json()
        assert set(data.keys()) >= {"stored", "duplicates", "total"}
        assert data["total"] == 2
    else:
        # Defensive failure path: explicit error message
        assert r.status_code in (400, 500)
        err = r.json()
        assert "detail" in err

