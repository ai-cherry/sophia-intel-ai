"""Tests for memory embedding workflow and schema validation."""
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient
from mcp_memory import server
from mcp_memory.models import MemoryRecord
class DummyQdrant:
    """Minimal in-memory Qdrant replacement for tests."""
    def __init__(self) -> None:
        self.points: Dict[str, Dict[str, Any]] = {}
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        for p in points:
            self.points[p["id"]] = p
    def search(self, collection_name: str, query_vector: List[float], limit: int):
        # Return stored points with dummy score
        class Result:
            def __init__(self, pid: str) -> None:
                self.id = pid
                self.score = 1.0
        return [Result(pid) for pid in list(self.points.keys())[:limit]]
@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    dummy_qdrant = DummyQdrant()
    monkeypatch.setattr(server, "QDRANT_AVAILABLE", True)
    monkeypatch.setattr(server, "qdrant_client", dummy_qdrant)
    import fakeredis
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(server, "redis_client", redis_client)
    return dummy_qdrant, redis_client
def test_metadata_validation() -> None:
    """Missing required metadata keys should raise a validation error."""
    with pytest.raises(Exception):
        MemoryRecord(content="test", metadata={"domain": "x"}, agent_id="a")
def test_store_and_semantic_retrieve(patch_dependencies):
    dummy_qdrant, redis_client = patch_dependencies
    client = TestClient(server.app)
    payload = {
        "content": "hello world",
        "metadata": {
            "domain": "test",
            "origin": "unit",
            "sensitivity": "low",
            "ttl": 60,
        },
        "agent_id": "tester",
        "vector_embedding": [0.1, 0.2, 0.3],
    }
    res = client.post("/memory/store", json=payload)
    assert res.status_code == 200
    memory_id = res.json()["data"]["id"]
    assert memory_id in dummy_qdrant.points
    assert redis_client.hgetall(memory_id)["content"] == "hello world"
    query = {
        "semantic_search": True,
        "vector_embedding": [0.1, 0.2, 0.3],
        "limit": 5,
    }
    res = client.post("/memory/retrieve", json=query)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == memory_id
