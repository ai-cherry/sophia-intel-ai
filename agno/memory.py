"""Real Memory and Knowledge Management for Agno v2
Integrates with RAG tools and vector databases
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import RAG tools
try:
    from builder_cli.lib.rag_tools import get_rag_manager, RAGManager, VectorStore
except ImportError:
    # Fallback if RAG tools not available
    RAGManager = None
    VectorStore = None
    def get_rag_manager():
        return None

import structlog

logger = structlog.get_logger(__name__)


class Knowledge:
    """Real Knowledge base with RAG capabilities"""
    
    def __init__(self, db=None, vector_store: str = "auto", **kwargs):
        self.db = db
        self.vector_store_type = vector_store
        
        # Initialize RAG manager
        self.rag_manager = None
        self._init_rag_manager()
        
        # Memory cache for frequent queries
        self._query_cache = {}
        self._cache_size = kwargs.get('cache_size', 100)
        
        logger.info(f"Knowledge base initialized with vector_store={vector_store}")
    
    def _init_rag_manager(self):
        """Initialize RAG manager with appropriate vector store"""
        if not RAGManager:
            logger.warning("RAG tools not available, Knowledge will have limited functionality")
            return
        
        try:
            if self.vector_store_type == "auto":
                # Auto-detect best available vector store
                self.rag_manager = get_rag_manager()
            else:
                # Use specific vector store
                store_map = {
                    "weaviate": VectorStore.WEAVIATE,
                    "milvus": VectorStore.MILVUS,
                    "unified": VectorStore.UNIFIED_MEMORY,
                    "local": VectorStore.LOCAL
                }
                
                store = store_map.get(self.vector_store_type, VectorStore.LOCAL)
                self.rag_manager = RAGManager(vector_store=store)
            
            logger.info(f"RAG manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG manager: {e}")
            self.rag_manager = None
    
    async def search(self, query: str, limit: int = 5, include_context: bool = False) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information
        
        Args:
            query: Search query
            limit: Maximum number of results
            include_context: Whether to include formatted context
            
        Returns:
            List of search results with content, scores, and metadata
        """
        # Check cache first
        cache_key = f"{query}:{limit}"
        if cache_key in self._query_cache:
            logger.debug(f"Returning cached result for query: {query[:50]}...")
            return self._query_cache[cache_key]
        
        results = []
        
        if self.rag_manager:
            try:
                rag_results = await self.rag_manager.search(query, limit)
                
                for rag_result in rag_results:
                    result = {
                        "content": rag_result.document.content,
                        "snippet": rag_result.context_snippet,
                        "source": rag_result.document.source,
                        "similarity_score": rag_result.similarity_score,
                        "metadata": rag_result.document.metadata,
                        "timestamp": rag_result.document.timestamp,
                        "reasoning": rag_result.reasoning
                    }
                    
                    if include_context:
                        # Add formatted context for LLM consumption
                        context, _ = await self.rag_manager.get_context(query)
                        result["formatted_context"] = context
                    
                    results.append(result)
                
                logger.info(f"Found {len(results)} results for query: {query[:50]}...")
                
            except Exception as e:
                logger.error(f"RAG search failed: {e}")
                # Fallback to simple text search if available
                results = await self._fallback_search(query, limit)
        else:
            # No RAG manager, use fallback
            results = await self._fallback_search(query, limit)
        
        # Cache results
        self._cache_result(cache_key, results)
        
        return results
    
    async def ingest(self, 
                    documents: List[str], 
                    sources: Optional[List[str]] = None,
                    metadata: Optional[List[Dict[str, Any]]] = None) -> int:
        """Ingest documents into the knowledge base
        
        Args:
            documents: List of document texts
            sources: Optional list of source identifiers
            metadata: Optional list of metadata dicts
            
        Returns:
            Number of documents successfully ingested
        """
        if not self.rag_manager:
            logger.error("Cannot ingest documents without RAG manager")
            return 0
        
        try:
            count = await self.rag_manager.ingest_documents(
                documents=documents,
                sources=sources,
                metadata=metadata
            )
            
            # Clear cache after ingestion
            self._clear_cache()
            
            logger.info(f"Successfully ingested {count} documents")
            return count
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return 0
    
    async def get_context_for_query(self, query: str, max_tokens: int = 3000) -> Tuple[str, List[Dict[str, Any]]]:
        """Get formatted context for a query suitable for LLM consumption
        
        Args:
            query: The query to get context for
            max_tokens: Maximum tokens in context
            
        Returns:
            Tuple of (formatted_context, source_documents)
        """
        if not self.rag_manager:
            return "No knowledge base available.", []
        
        try:
            context, rag_results = await self.rag_manager.get_context(query, max_tokens)
            
            # Convert RAG results to dict format
            source_docs = []
            for result in rag_results:
                source_docs.append({
                    "content": result.document.content,
                    "source": result.document.source,
                    "similarity_score": result.similarity_score,
                    "metadata": result.document.metadata
                })
            
            return context, source_docs
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return f"Error retrieving context: {e}", []
    
    async def add_memory(self, content: str, source: str = "user", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a single memory/document to the knowledge base
        
        Args:
            content: The content to remember
            source: Source identifier
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            count = await self.ingest(
                documents=[content],
                sources=[source],
                metadata=[metadata or {}]
            )
            return count > 0
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return False
    
    async def remember(self, query: str) -> Optional[str]:
        """Remember information related to a query
        
        Args:
            query: What to remember about
            
        Returns:
            Most relevant remembered content or None
        """
        results = await self.search(query, limit=1)
        if results:
            return results[0]["content"]
        return None
    
    async def forget(self, source: str) -> bool:
        """Forget/remove memories from a specific source
        
        Note: This is a placeholder - actual implementation would depend
        on vector store capabilities for deletion
        
        Args:
            source: Source to forget
            
        Returns:
            True if successful
        """
        logger.warning(f"Forget operation not implemented for source: {source}")
        # TODO: Implement deletion for each vector store type
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics
        
        Returns:
            Dictionary with stats about the knowledge base
        """
        stats = {
            "vector_store_type": self.vector_store_type,
            "rag_manager_available": self.rag_manager is not None,
            "cache_size": len(self._query_cache),
            "cache_limit": self._cache_size
        }
        
        # Add vector store specific stats if available
        if hasattr(self.rag_manager, 'vector_store'):
            if hasattr(self.rag_manager.vector_store, 'documents'):
                # Local vector store
                stats["document_count"] = len(self.rag_manager.vector_store.documents)
            else:
                stats["document_count"] = "unknown"
        
        return stats
    
    async def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback search when RAG is not available"""
        logger.warning("Using fallback search - functionality limited")
        
        # Simple text-based fallback
        # In a real implementation, this might search a simple database
        # or file system
        
        fallback_results = [
            {
                "content": f"Fallback result for query: {query}",
                "snippet": f"This is a fallback response since RAG is unavailable.",
                "source": "fallback",
                "similarity_score": 0.5,
                "metadata": {"type": "fallback"},
                "timestamp": datetime.now().timestamp(),
                "reasoning": "Fallback result due to RAG unavailability"
            }
        ]
        
        return fallback_results[:limit]
    
    def _cache_result(self, key: str, result: List[Dict[str, Any]]):
        """Cache a search result"""
        if len(self._query_cache) >= self._cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        
        self._query_cache[key] = result
    
    def _clear_cache(self):
        """Clear the query cache"""
        self._query_cache.clear()
        logger.debug("Query cache cleared")


# Convenience functions
async def quick_search(query: str, limit: int = 3) -> List[str]:
    """Quick search that returns just content snippets"""
    knowledge = Knowledge()
    results = await knowledge.search(query, limit)
    return [result["snippet"] for result in results]


async def get_context(query: str, max_tokens: int = 3000) -> str:
    """Get formatted context for LLM consumption"""
    knowledge = Knowledge()
    context, _ = await knowledge.get_context_for_query(query, max_tokens)
    return context


async def add_knowledge(content: str, source: str = "user") -> bool:
    """Add knowledge to the global knowledge base"""
    knowledge = Knowledge()
    return await knowledge.add_memory(content, source)