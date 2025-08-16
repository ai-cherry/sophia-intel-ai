"""
MCP Memory Client for standardized memory and context operations.
Extends BaseMCPClient with memory-specific functionality.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger


class MCPMemoryClient:
    """
    MCP client specialized for memory and context operations.
    Provides caching, resilience, and standardized memory access.
    """

    def __init__(self, base_url: str = None):
        from config.config import settings

        self.base_url = base_url or settings.MCP_BASE_URL

        # Memory-specific configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        self.local_cache = {}
        self.session = None
        self.timeout = 30

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to MCP server"""
        url = f"{self.base_url.rstrip('/')}{path}"
        session = await self._get_session()

        try:
            async with session.request(method, url, params=params, json=json_data) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise

    async def store(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None, context_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Store content in memory service with metadata.

        Args:
            session_id: Session identifier
            content: Content to store
            metadata: Additional metadata
            context_type: Type of context (general, code, conversation, etc.)

        Returns:
            Storage result with ID and status
        """
        try:
            request_data = {
                "session_id": session_id,
                "content": content,
                "metadata": metadata or {},
                "context_type": context_type,
            }

            result = await self._make_request("POST", "/context/store", json_data=request_data)

            # Update local cache
            cache_key = f"{session_id}:{content[:50]}"
            self.local_cache[cache_key] = {
                "content": content,
                "metadata": metadata,
                "timestamp": asyncio.get_event_loop().time(),
            }

            # Cleanup cache if too large
            if len(self.local_cache) > self.max_cache_size:
                await self._cleanup_cache()

            return result

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def query(
        self, session_id: str, query: str, top_k: int = 5, threshold: float = 0.7, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query context from memory service with caching.

        Args:
            session_id: Session identifier
            query: Query string for context search
            top_k: Number of results to return
            threshold: Similarity threshold
            use_cache: Whether to use local cache

        Returns:
            List of matching context entries
        """
        try:
            # Check local cache first
            if use_cache:
                cached_result = await self._check_cache(session_id, query)
                if cached_result:
                    logger.debug(f"Cache hit for query: {query[:50]}")
                    return cached_result

            request_data = {"session_id": session_id, "query": query, "top_k": top_k, "threshold": threshold}

            result = await self._make_request("POST", "/context/query", json_data=request_data)

            results = result.get("results", [])

            # Cache the results
            if use_cache and results:
                cache_key = f"query:{session_id}:{query[:50]}"
                self.local_cache[cache_key] = {"results": results, "timestamp": asyncio.get_event_loop().time()}

            return results

        except Exception as e:
            logger.error(f"Failed to query memory: {e}")
            # Return empty list on failure for graceful degradation
            return []

    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """
        Clear all context for a session.

        Args:
            session_id: Session identifier to clear

        Returns:
            Deletion result with count
        """
        try:
            result = await self._make_request("DELETE", f"/context/session/{session_id}")

            # Clear related cache entries
            await self._clear_session_cache(session_id)

            return result

        except Exception as e:
            logger.error(f"Failed to clear session memory: {e}")
            raise

    async def search_multi_service(
        self, session_id: str, query: str, services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search across multiple services for comprehensive results.

        Args:
            session_id: Session identifier
            query: Search query
            services: List of services to search (optional)

        Returns:
            Fused search results from multiple services
        """
        try:
            request_data = {
                "session_id": session_id,
                "query": query,
                "services": services or ["memory", "rag", "vector"],
            }

            result = await self._make_request("GET", "/context/search_multi_service", params=request_data)

            return result

        except Exception as e:
            logger.error(f"Failed multi-service search: {e}")
            # Fallback to regular query
            return {"results": await self.query(session_id, query), "source": "fallback_memory_only"}

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session's memory usage.

        Args:
            session_id: Session identifier

        Returns:
            Session statistics
        """
        try:
            result = await self._make_request("GET", f"/context/session/{session_id}/stats")
            return result

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}

    async def _check_cache(self, session_id: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """Check local cache for query results."""
        cache_key = f"query:{session_id}:{query[:50]}"

        if cache_key in self.local_cache:
            cached_entry = self.local_cache[cache_key]
            current_time = asyncio.get_event_loop().time()

            # Check if cache entry is still valid
            if current_time - cached_entry["timestamp"] < self.cache_ttl:
                return cached_entry["results"]
            else:
                # Remove expired entry
                del self.local_cache[cache_key]

        return None

    async def _cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = asyncio.get_event_loop().time()
        expired_keys = []

        for key, entry in self.local_cache.items():
            if current_time - entry["timestamp"] > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.local_cache[key]

        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def _clear_session_cache(self, session_id: str):
        """Clear cache entries for a specific session."""
        keys_to_remove = []

        for key in self.local_cache.keys():
            if key.startswith(f"query:{session_id}:") or key.startswith(f"{session_id}:"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.local_cache[key]

        logger.debug(f"Cleared {len(keys_to_remove)} cache entries for session {session_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Check memory client health and connectivity."""
        try:
            # Test basic connectivity
            result = await self._make_request("GET", "/health")

            return {
                "status": "healthy",
                "cache_size": len(self.local_cache),
                "server_health": result,
                "client_version": "1.0.0",
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "cache_size": len(self.local_cache)}
