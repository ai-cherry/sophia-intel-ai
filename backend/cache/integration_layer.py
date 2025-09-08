"""
Cache Integration Layer for ASIP Orchestrator
Seamless integration of 5-tier cache predator with Sophia AI components
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from .predator_system import CachePredatorSystem, create_cache_predator

logger = logging.getLogger(__name__)


class CacheIntegrationLayer:
    """Integration layer between cache predator and ASIP components"""

    def __init__(self):
        self.cache_system: Optional[CachePredatorSystem] = None
        self.integration_metrics = {
            "asip_cache_hits": 0,
            "embedding_cache_hits": 0,
            "rag_cache_hits": 0,
            "mcp_cache_hits": 0,
            "total_integrations": 0,
        }

    async def initialize(self, target_hit_rate: float = 0.97):
        """Initialize cache integration"""

        self.cache_system = await create_cache_predator(target_hit_rate)
        logger.info("Cache integration layer initialized")

    # ASIP Orchestrator Integration
    async def cache_asip_response(
        self, query_hash: str, response: Dict[str, Any], ttl: int = 3600
    ):
        """Cache ASIP orchestrator response"""

        cache_key = f"asip:response:{query_hash}"
        await self.cache_system.set(cache_key, response, ttl)
        logger.debug(f"Cached ASIP response for query hash {query_hash}")

    async def get_asip_response(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached ASIP response"""

        cache_key = f"asip:response:{query_hash}"
        response = await self.cache_system.get(cache_key)

        if response:
            self.integration_metrics["asip_cache_hits"] += 1
            logger.debug(f"ASIP cache hit for query hash {query_hash}")

        return response

    # Embedding Service Integration
    async def cache_embedding(
        self, text_hash: str, embedding: List[float], ttl: int = 86400
    ):
        """Cache embedding vector"""

        cache_key = f"embedding:vector:{text_hash}"
        await self.cache_system.set(cache_key, embedding, ttl)

    async def get_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embedding"""

        cache_key = f"embedding:vector:{text_hash}"
        embedding = await self.cache_system.get(cache_key)

        if embedding:
            self.integration_metrics["embedding_cache_hits"] += 1

        return embedding

    # RAG System Integration
    async def cache_rag_context(
        self, query_hash: str, context: Dict[str, Any], ttl: int = 1800
    ):
        """Cache RAG context and retrieved documents"""

        cache_key = f"rag:context:{query_hash}"
        await self.cache_system.set(cache_key, context, ttl)

    async def get_rag_context(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached RAG context"""

        cache_key = f"rag:context:{query_hash}"
        context = await self.cache_system.get(cache_key)

        if context:
            self.integration_metrics["rag_cache_hits"] += 1

        return context

    # MCP Integration
    async def cache_mcp_response(
        self, tool_call_hash: str, response: Any, ttl: int = 600
    ):
        """Cache MCP tool response"""

        cache_key = f"mcp:response:{tool_call_hash}"
        await self.cache_system.set(cache_key, response, ttl)

    async def get_mcp_response(self, tool_call_hash: str) -> Any:
        """Get cached MCP response"""

        cache_key = f"mcp:response:{tool_call_hash}"
        response = await self.cache_system.get(cache_key)

        if response:
            self.integration_metrics["mcp_cache_hits"] += 1

        return response

    # Business Intelligence Integration
    async def cache_bi_query(
        self, query_hash: str, result: Dict[str, Any], ttl: int = 900
    ):
        """Cache business intelligence query result"""

        cache_key = f"bi:query:{query_hash}"
        await self.cache_system.set(cache_key, result, ttl)

    async def get_bi_query(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached BI query result"""

        cache_key = f"bi:query:{query_hash}"
        result = await self.cache_system.get(cache_key)

        return result

    # User Session Integration
    async def cache_user_session(
        self, user_id: str, session_data: Dict[str, Any], ttl: int = 3600
    ):
        """Cache user session data"""

        cache_key = f"user:session:{user_id}"
        await self.cache_system.set(cache_key, session_data, ttl)

    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session"""

        cache_key = f"user:session:{user_id}"
        return await self.cache_system.get(cache_key)

    # Performance and Metrics
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Get cache integration performance metrics"""

        cache_metrics = await self.cache_system.get_performance_metrics()

        # Calculate integration-specific metrics
        total_integration_hits = sum(
            [
                self.integration_metrics["asip_cache_hits"],
                self.integration_metrics["embedding_cache_hits"],
                self.integration_metrics["rag_cache_hits"],
                self.integration_metrics["mcp_cache_hits"],
            ]
        )

        return {
            "cache_system_metrics": cache_metrics,
            "integration_metrics": self.integration_metrics,
            "total_integration_hits": total_integration_hits,
            "integration_efficiency": {
                "asip_hit_rate": self.integration_metrics["asip_cache_hits"]
                / max(1, self.integration_metrics["total_integrations"]),
                "embedding_hit_rate": self.integration_metrics["embedding_cache_hits"]
                / max(1, self.integration_metrics["total_integrations"]),
                "rag_hit_rate": self.integration_metrics["rag_cache_hits"]
                / max(1, self.integration_metrics["total_integrations"]),
                "mcp_hit_rate": self.integration_metrics["mcp_cache_hits"]
                / max(1, self.integration_metrics["total_integrations"]),
            },
        }

    async def warm_cache_for_user(self, user_id: str, common_queries: List[str]):
        """Warm cache with common user queries"""

        for query in common_queries:
            # Pre-generate embeddings for common queries
            query_hash = hash(query)

            # This would integrate with actual embedding service
            # For now, we'll just mark the cache keys as warmed
            cache_key = f"embedding:vector:{query_hash}"
            await self.cache_system.set(cache_key, f"warmed_for_{user_id}", ttl=3600)

        logger.info(
            f"Cache warmed for user {user_id} with {len(common_queries)} queries"
        )

    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user"""

        # This is a simplified implementation
        # In production, you'd want more sophisticated cache tagging
        user_keys = [
            f"user:session:{user_id}",
            f"bi:query:user_{user_id}*",
            f"asip:response:user_{user_id}*",
        ]

        for key_pattern in user_keys:
            # Clear matching keys (simplified)
            await self.cache_system.set(key_pattern, None, ttl=1)

        logger.info(f"Cache invalidated for user {user_id}")

    async def shutdown(self):
        """Shutdown cache integration"""

        if self.cache_system:
            await self.cache_system.shutdown()

        logger.info("Cache integration layer shutdown complete")


# Global cache integration instance
_cache_integration: Optional[CacheIntegrationLayer] = None


async def get_cache_integration() -> CacheIntegrationLayer:
    """Get global cache integration instance"""

    global _cache_integration

    if _cache_integration is None:
        _cache_integration = CacheIntegrationLayer()
        await _cache_integration.initialize()

    return _cache_integration


@asynccontextmanager
async def cache_context():
    """Context manager for cache integration"""

    integration = await get_cache_integration()
    try:
        yield integration
    finally:
        # Context cleanup if needed
        pass


# Decorator for automatic caching
def cache_result(cache_key_prefix: str, ttl: int = 3600):
    """Decorator for automatic result caching"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = (
                f"{cache_key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            )

            integration = await get_cache_integration()

            # Try to get from cache
            cached_result = await integration.cache_system.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await integration.cache_system.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
