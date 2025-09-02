from fastapi.testclient import TestClient

from app.api.embedding_endpoints import router

client = TestClient(router)

def test_create_embedding():
    response = client.post("/embeddings/create", json={
        "text": "Hello, world!",
        "model": "text-embedding-ada-002"
    })
    assert response.status_code == 200
    assert "embedding" in response.json()
    assert "model" in response.json()

def test_batch_embeddings():
    response = client.post("/embeddings/batch", json={
        "texts": ["Hello", "world"],
        "model": "text-embedding-ada-002"
    })
    assert response.status_code == 200
    assert "embeddings" in response.json()
    assert len(response.json()["embeddings"]) == 2

def test_search_embeddings():
    response = client.get("/embeddings/search?query=hello&top_k=5")
    assert response.status_code == 200
    assert "results" in response.json()
    assert len(response.json()["results"]) > 0
