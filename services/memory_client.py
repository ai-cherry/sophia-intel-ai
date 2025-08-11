from qdrant_client import QdrantClient, models
from typing import List, Dict, Any, Optional

class MemoryClient:
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the memory client with a connection to Qdrant.
        """
        qdrant_config = config.get("qdrant", {})
        self.client = QdrantClient(
            url=qdrant_config.get("url"),
            api_key=qdrant_config.get("api_key"),
        )
        print("MemoryClient initialized.")

    def upsert(self, collection_name: str, points: List[models.PointStruct]):
        """
        Upserts points into a Qdrant collection.
        """
        print(f"Upserting {len(points)} points to collection '{collection_name}'...")
        self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )
        print("Upsert complete.")

    def search(self, collection_name: str, query_vector: List[float], limit: int = 10) -> List[models.ScoredPoint]:
        """
        Searches for similar vectors in a Qdrant collection.
        """
        print(f"Searching collection '{collection_name}'...")
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            search_params=models.SearchParams(
                hnsw_ef=128,
                exact=False
            )
        )
        print(f"Found {len(search_result)} results.")
        return search_result

    def create_collection(self, collection_name: str, vector_size: int):
        """
        Creates a new collection if it doesn't already exist.
        """
        try:
            self.client.get_collection(collection_name=collection_name)
            print(f"Collection '{collection_name}' already exists.")
        except Exception:
            print(f"Creating collection '{collection_name}'...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            print("Collection created.")

if __name__ == "__main__":
    # Example usage (requires a running Qdrant instance)
    # To run this example, you might need to start Qdrant with Docker:
    # docker run -p 6333:6333 qdrant/qdrant

    mock_config = {
        "qdrant": {
            "url": "http://localhost:6333",
            "api_key": None
        }
    }
    memory_client = MemoryClient(mock_config)

    COLLECTION_NAME = "test_collection"
    VECTOR_SIZE = 4 # Using a small vector size for the example

    # Create a collection
    memory_client.create_collection(COLLECTION_NAME, VECTOR_SIZE)

    # Upsert some points
    points_to_upsert = [
        models.PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"color": "red"}),
        models.PointStruct(id=2, vector=[0.9, 0.8, 0.7, 0.6], payload={"color": "blue"}),
    ]
    memory_client.upsert(COLLECTION_NAME, points_to_upsert)

    # Search for a similar point
    query_vector = [0.11, 0.22, 0.33, 0.44]
    search_results = memory_client.search(COLLECTION_NAME, query_vector)
    print("Search results:")
    for result in search_results:
        print(f"- ID: {result.id}, Score: {result.score}, Payload: {result.payload}")