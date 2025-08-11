"""
Memory service with Qdrant vector database backend.
Provides semantic search and context storage for the Sophia platform.
"""
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, MatchValue
from typing import List, Dict, Optional, Any
from loguru import logger
from config.config import settings
import time
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.portkey_client import PortkeyClient

class MemoryService:
    def __init__(self):
        self.collection_name = settings.MEMORY_COLLECTION_NAME
        self.embedding_dim = settings.EMBEDDING_DIMENSION
        
        # Initialize Qdrant client
        client_kwargs = {"url": settings.QDRANT_URL}
        if settings.QDRANT_API_KEY:
            client_kwargs["api_key"] = settings.QDRANT_API_KEY
            
        self.client = QdrantClient(**client_kwargs)
        
        # Initialize Portkey client for embeddings
        self.portkey_client = PortkeyClient()
        
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the collection exists, create if not."""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} exists")
        except Exception as e:
            logger.info(f"Creating collection {self.collection_name}: {e}")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )

    async def _embed(self, text: str) -> List[float]:
        """
        Create embeddings for text content using OpenRouter text-embedding-3-small via Portkey.
        """
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            
            # Use OpenRouter's text-embedding-3-small model through Portkey
            response = await self.portkey_client.embeddings(
                input=text,
                model="openai/text-embedding-3-small"
            )
            
            # Extract the embedding vector
            embedding = response["data"][0]["embedding"]
            
            # Validate embedding dimension
            if len(embedding) != self.embedding_dim:
                logger.warning(f"Expected embedding dimension {self.embedding_dim}, got {len(embedding)}")
                
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding via OpenRouter: {e}")
            
            # Fallback to hash-based embedding to maintain system stability
            logger.warning("Falling back to hash-based embedding")
            return self._hash_embed_fallback(text)
    
    def _hash_embed_fallback(self, text: str) -> List[float]:
        """
        Fallback hash-based embedding for when OpenRouter is unavailable.
        This ensures the system remains functional even if the API is down.
        """
        import hashlib
        
        # Generate stable hash-based embedding
        h = hashlib.sha256(text.encode()).digest()
        vector = [b / 255.0 for b in h]
        
        # Pad or truncate to desired dimension
        if len(vector) < self.embedding_dim:
            # Repeat pattern to fill dimension
            while len(vector) < self.embedding_dim:
                vector.extend(vector[:self.embedding_dim - len(vector)])
        else:
            vector = vector[:self.embedding_dim]
            
        return vector

    async def _summarize_content(self, content: str) -> str:
        """
        Generate intelligent summary/title for stored content using LLM.
        """
        try:
            # Truncate content for summarization
            truncated_content = content[:500] if len(content) > 500 else content
            
            messages = [{
                "role": "user",
                "content": f"Create a concise, descriptive title (maximum 10 words) for this context:\n\n{truncated_content}"
            }]
            
            response = await self.portkey_client.chat(
                messages=messages,
                model="openrouter/auto",
                max_tokens=20,
                temperature=0.3
            )
            
            summary = response["choices"][0]["message"]["content"].strip()
            
            # Clean up the summary
            summary = summary.replace('"', '').replace("'", "")
            if summary.endswith('.'):
                summary = summary[:-1]
                
            return summary[:50]  # Ensure reasonable length
            
        except Exception as e:
            logger.warning(f"Failed to generate content summary: {e}")
            # Fallback to simple truncation
            words = content.split()[:8]
            return " ".join(words) + ("..." if len(content.split()) > 8 else "")

    async def health_check(self) -> Dict[str, Any]:
        """Check if the memory service is healthy."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            collection_info = await loop.run_in_executor(
                None, self.client.get_collection, self.collection_name
            )
            return {
                "status": "healthy",
                "collection": self.collection_name,
                "vector_count": collection_info.vectors_count
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def store_context(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store context with semantic embedding."""
        try:
            # Generate embedding
            vector = await self._embed(content)
            
            # Generate content summary
            summary = await self._summarize_content(content)
            
            # Generate unique ID
            point_id = int(time.time() * 1000000)  # Microsecond timestamp
            
            # Prepare payload
            payload = {
                "session_id": session_id,
                "content": content,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.upsert,
                self.collection_name,
                [PointStruct(id=point_id, vector=vector, payload=payload)]
            )
            
            logger.info(f"Stored context {point_id} for session {session_id} with summary: {summary}")
            return {"success": True, "id": point_id, "summary": summary}
            
        except Exception as e:
            logger.error(f"Failed to store context: {e}")
            raise

    async def query_context(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        global_search: bool = False,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Query context using semantic search."""
        try:
            # Generate query embedding
            query_vector = await self._embed(query)
            
            # Build filter
            query_filter = None
            if not global_search:
                query_filter = Filter(
                    must=[{"key": "session_id", "match": {"value": session_id}}]
                )
            
            # Search in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    score_threshold=threshold
                )
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "summary": result.payload.get("summary", ""),
                    "session_id": result.payload.get("session_id", ""),
                    "timestamp": result.payload.get("timestamp", ""),
                    "metadata": {k: v for k, v in result.payload.items()
                               if k not in ["content", "summary", "session_id", "timestamp"]}
                })
            
            logger.info(f"Found {len(formatted_results)} results for query in session {session_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query context: {e}")
            raise

    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear all context for a specific session."""
        try:
            # Delete points by session_id filter
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=Filter(
                        must=[{"key": "session_id", "match": {"value": session_id}}]
                    )
                )
            )
            
            logger.info(f"Cleared context for session {session_id}")
            return {"success": True, "deleted_count": getattr(result, 'deleted', 0)}
            
        except Exception as e:
            logger.error(f"Failed to clear session context: {e}")
            raise

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session."""
        try:
            # Count points for this session
            loop = asyncio.get_event_loop()
            
            # Use scroll to count points (Qdrant doesn't have a direct count API)
            result = await loop.run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        must=[{"key": "session_id", "match": {"value": session_id}}]
                    ),
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
            )
            
            # Get collection info for total context
            collection_info = await loop.run_in_executor(
                None, self.client.get_collection, self.collection_name
            )
            
            return {
                "session_id": session_id,
                "context_count": len(result[0]) if result[0] else 0,
                "total_contexts": collection_info.vectors_count,
                "collection": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            raise