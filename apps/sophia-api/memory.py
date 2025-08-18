from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
import logging
from datetime import datetime
import hashlib
import os
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SophiaMemory:
    def __init__(self):
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"), 
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "sophia_memory"
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists"""
        try:
            collections = self.qdrant.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Collection setup failed: {e}")

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50):
        """Chunk text into smaller pieces with overlap"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    def store(self, context: str, data: dict, tags: list = None):
        """Store context with hierarchical meta-tagging"""
        try:
            # Prepare content for chunking
            content = json.dumps(data) if isinstance(data, dict) else str(data)
            chunks = self._chunk_text(content)
            
            # Generate hierarchical tags
            base_tags = [f"ctx:{context}"]
            if tags:
                base_tags.extend(tags)
            
            # Add automatic tags based on data structure
            if isinstance(data, dict):
                if "type" in data:
                    base_tags.append(f"type:{data['type']}")
                if "category" in data:
                    base_tags.append(f"cat:{data['category']}")
                if "source" in data:
                    base_tags.append(f"src:{data['source']}")
                if "priority" in data:
                    base_tags.append(f"pri:{data['priority']}")
            
            # Create points for each chunk
            points = []
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{context}_{i}_{chunk}".encode()).hexdigest()
                vector = self.model.encode(chunk).tolist()
                
                point = PointStruct(
                    id=chunk_id,
                    vector=vector,
                    payload={
                        "context": context,
                        "chunk": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "tags": base_tags,
                        "timestamp": datetime.now().isoformat(),
                        "source": data.get("source", "unknown") if isinstance(data, dict) else "unknown",
                        "metadata": data if isinstance(data, dict) else {"content": str(data)}
                    }
                )
                points.append(point)
            
            # Store in Qdrant
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Stored {len(chunks)} chunks for context: {context}")
            return {"status": "stored", "chunks": len(chunks), "tags": base_tags}
        
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            return {"status": "error", "error": str(e)}

    def retrieve(self, query: str, tags: list = None, limit: int = 10, score_threshold: float = 0.7):
        """Retrieve context with tag filtering and semantic search"""
        try:
            # Generate query vector
            query_vector = self.model.encode(query).tolist()
            
            # Build filter conditions
            filter_conditions = []
            if tags:
                for tag in tags:
                    filter_conditions.append({
                        "key": "tags",
                        "match": {"value": tag}
                    })
            
            search_filter = {"must": filter_conditions} if filter_conditions else None
            
            # Search in Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Process results
            processed_results = []
            for result in results:
                processed_results.append({
                    "content": result.payload["chunk"],
                    "context": result.payload["context"],
                    "score": result.score,
                    "tags": result.payload["tags"],
                    "timestamp": result.payload["timestamp"],
                    "source": result.payload["source"],
                    "metadata": result.payload.get("metadata", {})
                })
            
            logger.info(f"Retrieved {len(results)} items for query: {query}")
            return {
                "query": query,
                "results": processed_results,
                "count": len(results),
                "tags_used": tags or []
            }
        
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_tags(self, prefix: str = None):
        """Get all available tags, optionally filtered by prefix"""
        try:
            # This is a simplified implementation
            # In a real scenario, you'd want to maintain a separate tags index
            results = self.qdrant.scroll(
                collection_name=self.collection_name,
                limit=1000
            )
            
            all_tags = set()
            for point in results[0]:
                tags = point.payload.get("tags", [])
                for tag in tags:
                    if not prefix or tag.startswith(prefix):
                        all_tags.add(tag)
            
            return {"tags": sorted(list(all_tags))}
        
        except Exception as e:
            logger.error(f"Tag retrieval failed: {e}")
            return {"status": "error", "error": str(e)}

    def delete_by_context(self, context: str):
        """Delete all memories for a specific context"""
        try:
            # Search for all points with the given context
            results = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [{"key": "context", "match": {"value": context}}]
                },
                limit=10000
            )
            
            # Extract point IDs
            point_ids = [point.id for point in results[0]]
            
            if point_ids:
                self.qdrant.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.info(f"Deleted {len(point_ids)} points for context: {context}")
                return {"status": "deleted", "count": len(point_ids)}
            else:
                return {"status": "not_found", "count": 0}
        
        except Exception as e:
            logger.error(f"Memory deletion failed: {e}")
            return {"status": "error", "error": str(e)}

