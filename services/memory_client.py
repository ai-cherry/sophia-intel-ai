import qdrant_client
from qdrant_client.http import models
from typing import List, Dict, Any
import uuid

from services.embeddings import EmbeddingService

class MemoryClient:
    def __init__(self, qdrant_url: str, qdrant_api_key: str = None, collection_name: str = "repo_memory"):
        self.client = qdrant_client.QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService()
        
        # Create the collection if it doesn't exist
        try:
            self.client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )

    def upsert_documents(self, documents: List[str], metadata: List[Dict[str, Any]]):
        """
        Generates embeddings and upserts documents into the Qdrant collection.
        """
        embeddings = self.embedding_service.generate_embeddings(documents)
        
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=meta,
            )
            for embedding, meta in zip(embeddings, metadata)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a similarity search in the Qdrant collection.
        """
        query_vector = self.embedding_service.generate_embeddings([query_text])[0]
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        
        return [hit.payload for hit in search_result]

# Example usage
if __name__ == "__main__":
    import os
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url:
        memory_client = MemoryClient(qdrant_url, qdrant_api_key)
        
        # Example documents and metadata
        docs = ["This is a test document.", "This is another test document."]
        meta = [
            {"repo": "test-repo", "path": "test.py", "chunk": 0},
            {"repo": "test-repo", "path": "test.py", "chunk": 1},
        ]
        
        print("Upserting documents...")
        memory_client.upsert_documents(docs, meta)
        
        print("\nSearching for 'test'...")
        results = memory_client.search("test")
        print(results)
    else:
        print("QDRANT_URL not set. Skipping example.")