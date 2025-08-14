"""
Enhanced RAG Pipeline with Swarm-Integrated MCP Suite
Provides multi-service context retrieval with intelligent routing and fallbacks
"""
import os
import json
import asyncio
import time
from functools import lru_cache
from typing import Dict, Any, List, Optional, Union
from loguru import logger

# Import both legacy and new MCP tools for backward compatibility
from integrations.mcp_tools import mcp_semantic_search as legacy_mcp_search
try:
    from libs.mcp_client.base_client import get_client_manager, SearchResult
except ImportError:
    logger.warning(
        "New MCP client library not available, falling back to legacy only")
    get_client_manager = None
    SearchResult = None


class EnhancedRAGPipeline:
    """
    Enhanced RAG Pipeline with multi-service support and intelligent routing

    Features:
    - Multi-service semantic search across all MCP services
    - Intelligent routing based on query context and Swarm stage
    - Fallback chains: New MCP → Legacy MCP → Qdrant → Mock
    - Context fusion from multiple sources
    - Performance monitoring and caching
    - Swarm-aware context prioritization
    """

    def __init__(self):
        self.client_manager = None
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.performance_metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "service_response_times": {},
            "fallback_usage": {
                "new_mcp": 0,
                "legacy_mcp": 0,
                "qdrant": 0,
                "mock": 0
            }
        }

    async def _get_client_manager(self):
        """Lazy initialization of client manager"""
        if self.client_manager is None and get_client_manager:
            self.client_manager = await get_client_manager()
        return self.client_manager

    async def search_multi_service(
        self,
        query: str,
        k: int = 8,
        swarm_stage: Optional[str] = None,
        services: Optional[List[str]] = None,
        enable_fusion: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search across multiple MCP services with intelligent routing

        Args:
            query: Search query
            k: Number of results to return
            swarm_stage: Current Swarm stage for context-aware routing
            services: Specific services to search (None = auto-detect)
            enable_fusion: Whether to fuse results from multiple services

        Returns:
            List of search results with unified format
        """
        start_time = time.time()
        self.performance_metrics["total_queries"] += 1

        # Check cache first
        cache_key = f"{query}_{k}_{swarm_stage}_{services}"
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.performance_metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cache_entry["results"]

        try:
            # Try new MCP architecture first
            results = await self._search_new_mcp(query, k, swarm_stage, services)
            if results:
                self.performance_metrics["fallback_usage"]["new_mcp"] += 1
                logger.info(f"New MCP returned {len(results)} results")
                return self._cache_and_return(cache_key, results, start_time)
        except Exception as e:
            logger.warning(f"New MCP search failed: {e}")

        # Fall back to legacy MCP
        try:
            results = await self._search_legacy_mcp(query, k, swarm_stage)
            if results:
                self.performance_metrics["fallback_usage"]["legacy_mcp"] += 1
                logger.info(f"Legacy MCP returned {len(results)} results")
                return self._cache_and_return(cache_key, results, start_time)
        except Exception as e:
            logger.warning(f"Legacy MCP search failed: {e}")

        # Fall back to Qdrant
        try:
            results = await self._search_qdrant_fallback(query, k)
            if results:
                self.performance_metrics["fallback_usage"]["qdrant"] += 1
                logger.info(f"Qdrant fallback returned {len(results)} results")
                return self._cache_and_return(cache_key, results, start_time)
        except Exception as e:
            logger.warning(f"Qdrant search failed: {e}")

        # Final fallback to mock data
        self.performance_metrics["fallback_usage"]["mock"] += 1
        results = self._get_mock_results(query, k)
        logger.info(f"Using mock results for query: {query[:50]}...")
        return self._cache_and_return(cache_key, results, start_time)

    async def _search_new_mcp(
        self,
        query: str,
        k: int,
        swarm_stage: Optional[str],
        services: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Search using new standardized MCP architecture"""
        client_manager = await self._get_client_manager()
        if not client_manager:
            return []

        if services:
            # Search specific services
            all_results = []
            for service_name in services:
                client = await client_manager.get_client(service_name)
                if client:
                    service_start = time.time()
                    try:
                        results = await client.semantic_search(query, k, swarm_stage)
                        all_results.extend(
                            self._convert_search_results(results))

                        # Record performance
                        response_time = time.time() - service_start
                        if service_name not in self.performance_metrics["service_response_times"]:
                            self.performance_metrics["service_response_times"][service_name] = [
                            ]
                        self.performance_metrics["service_response_times"][service_name].append(
                            response_time)

                    except Exception as e:
                        logger.error(f"Search failed for {service_name}: {e}")

            # Sort by score and return top k
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return all_results[:k]
        else:
            # Search all available services
            results = await client_manager.search_all(query, k, swarm_stage)
            return self._convert_search_results(results)

    async def _search_legacy_mcp(
        self,
        query: str,
        k: int,
        swarm_stage: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search using legacy MCP tools for backward compatibility"""
        results = legacy_mcp_search(query, k=k)
        if results:
            # Convert to standard format
            standardized = []
            for result in results:
                standardized.append({
                    "id": result.get("id", "legacy_" + str(hash(result.get("content", "")))),
                    "content": result.get("content", ""),
                    "path": result.get("path", ""),
                    "score": result.get("score", 0.5),
                    "source": "legacy_mcp",
                    "metadata": result.get("metadata", {}),
                    "timestamp": time.time()
                })
            return standardized
        return []

    async def _search_qdrant_fallback(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Fallback Qdrant search without Haystack dependencies"""
        try:
            import qdrant_client
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            client = qdrant_client.QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY")
            )

            collection = os.getenv("QDRANT_COLLECTION", "repo_docs")

            # Simple text search without embeddings
            results = client.scroll(
                collection_name=collection,
                limit=k,
                with_payload=True,
                with_vectors=False
            )

            docs = []
            for point in results[0]:
                payload = point.payload or {}
                docs.append({
                    "id": f"qdrant_{point.id}",
                    "path": payload.get("path", ""),
                    "content": payload.get("content", "")[:800],
                    "score": 0.5,  # Default score since we can't do semantic search
                    "source": "qdrant_fallback",
                    "metadata": payload,
                    "timestamp": time.time()
                })

            return docs[:k]
        except Exception as e:
            logger.error(f"Qdrant fallback failed: {e}")
            return []

    def _get_mock_results(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Generate mock results for development/testing"""
        return [{
            "id": f"mock_{i}",
            "path": "mock/development.py",
            "content": f"# Mock search result {i+1} for query: {query}\n# This is returned when no search backend is available\n# Context: Development fallback data",
            "score": 0.1 - (i * 0.01),  # Decreasing scores
            "source": "mock",
            "metadata": {
                "query": query,
                "result_index": i,
                "fallback_reason": "no_services_available"
            },
            "timestamp": time.time()
        } for i in range(min(k, 3))]  # Return up to 3 mock results

    def _convert_search_results(self, results: List) -> List[Dict[str, Any]]:
        """Convert SearchResult objects to dictionary format"""
        if not results:
            return []

        converted = []
        for result in results:
            if SearchResult and isinstance(result, SearchResult):
                # New format
                converted.append({
                    "id": result.id,
                    "content": result.content,
                    "path": result.metadata.get("path", ""),
                    "score": result.score,
                    "source": result.service,
                    "metadata": result.metadata,
                    "timestamp": result.timestamp
                })
            else:
                # Legacy format or dict
                converted.append({
                    "id": result.get("id", f"result_{hash(str(result))}"),
                    "content": result.get("content", ""),
                    "path": result.get("path", ""),
                    "score": result.get("score", 0.5),
                    "source": result.get("source", "unknown"),
                    "metadata": result.get("metadata", {}),
                    "timestamp": result.get("timestamp", time.time())
                })
        return converted

    def _cache_and_return(
        self,
        cache_key: str,
        results: List[Dict[str, Any]],
        start_time: float
    ) -> List[Dict[str, Any]]:
        """Cache results and return them"""
        # Cache the results
        self.search_cache[cache_key] = {
            "results": results,
            "timestamp": time.time()
        }

        # Clean old cache entries
        self._cleanup_cache()

        # Log performance
        response_time = time.time() - start_time
        logger.debug(
            f"Search completed in {response_time:.3f}s with {len(results)} results")

        return results

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.search_cache.items()
            if current_time - value["timestamp"] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.search_cache[key]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        metrics = self.performance_metrics.copy()

        # Calculate average response times
        avg_response_times = {}
        for service, times in metrics["service_response_times"].items():
            if times:
                avg_response_times[service] = sum(times) / len(times)
        metrics["avg_service_response_times"] = avg_response_times

        # Calculate cache hit rate
        total_queries = metrics["total_queries"]
        if total_queries > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / total_queries
        else:
            metrics["cache_hit_rate"] = 0.0

        return metrics

    async def intelligent_routing(
        self,
        query: str,
        swarm_stage: Optional[str] = None
    ) -> List[str]:
        """
        Intelligently route query to most appropriate services based on content and context

        Args:
            query: Search query
            swarm_stage: Current Swarm stage

        Returns:
            List of service names to search, ordered by priority
        """
        services = []
        query_lower = query.lower()

        # Stage-based routing
        if swarm_stage == "architect":
            # Architects need documentation, requirements, and design context
            services.extend(["notion", "slack"])
        elif swarm_stage == "builder":
            # Builders need code examples, APIs, and technical documentation
            services.extend(["slack", "notion"])
        elif swarm_stage == "tester":
            # Testers need test cases, bug reports, and quality metrics
            services.extend(["notion", "slack"])
        elif swarm_stage == "operator":
            # Operators need deployment guides, infrastructure, and monitoring
            services.extend(["notion", "slack"])

        # Content-based routing
        if any(word in query_lower for word in ["customer", "sales", "lead", "opportunity", "crm"]):
            services.insert(0, "salesforce")

        if any(word in query_lower for word in ["message", "chat", "conversation", "channel"]):
            services.insert(0, "slack")

        if any(word in query_lower for word in ["document", "note", "page", "wiki"]):
            services.insert(0, "notion")

        if any(word in query_lower for word in ["support", "ticket", "help", "issue"]):
            services.insert(0, "intercom")

        # Remove duplicates while preserving order
        seen = set()
        unique_services = []
        for service in services:
            if service not in seen:
                unique_services.append(service)
                seen.add(service)

        return unique_services or ["slack", "notion"]  # Default services


# Global pipeline instance
_rag_pipeline = None


async def get_rag_pipeline() -> EnhancedRAGPipeline:
    """Get global RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = EnhancedRAGPipeline()
    return _rag_pipeline

# Backward compatibility functions for existing Swarm system


def _qdrant_search_fallback(query: str, k: int = 8):
    """Fallback Qdrant search without Haystack dependencies - legacy function"""
    try:
        import qdrant_client
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = qdrant_client.QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        collection = os.getenv("QDRANT_COLLECTION", "repo_docs")

        # Simple text search without embeddings - basic implementation
        results = client.scroll(
            collection_name=collection,
            limit=k,
            with_payload=True,
            with_vectors=False
        )

        docs = []
        for point in results[0]:
            payload = point.payload or {}
            docs.append({
                "path": payload.get("path", ""),
                "content": payload.get("content", "")[:800],
                "score": 0.5,  # Default score since we can't do semantic search
                "source": "qdrant_fallback"
            })

        return docs[:k]
    except Exception as e:
        print(f"Qdrant fallback failed: {e}")
        return []


def repo_search(query: str, k: int = 8, swarm_stage: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Backward compatible repo search function
    Maintains existing interface while using enhanced pipeline when possible
    """
    try:
        # Try enhanced pipeline first if async context is available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this carefully
                # For now, fall back to legacy approach to avoid issues
                pass
            else:
                # We can run async directly
                pipeline = loop.run_until_complete(get_rag_pipeline())
                results = loop.run_until_complete(
                    pipeline.search_multi_service(query, k, swarm_stage)
                )
                return results
        except Exception:
            # Fall through to legacy approach
            pass

        # Get configured source priority
        sources_priority = os.getenv(
            "RAG_SOURCES_PRIORITY", "legacy_mcp,qdrant,mock").split(",")

        # Try each source in priority order
        for source in sources_priority:
            if source == "legacy_mcp":
                hits = legacy_mcp_search(query, k=k)
                if hits:
                    for hit in hits:
                        hit["source"] = hit.get("source", "legacy_mcp")
                    return hits

            elif source == "mock" and os.getenv("USE_MOCK_DATA", "0") == "1":
                # Generate mock results with higher priority
                mock_hits = [{
                    "path": f"mock/{query.replace(' ', '_')[:10]}.py",
                    "content": f"# Mock search result for query: {query}\n# This is returned based on your preference for mock data",
                    "score": 0.85,  # Higher score than fallback
                    "source": "mock_preferred"
                }]
                return mock_hits

            elif source == "qdrant":
                fallback_hits = _qdrant_search_fallback(query, k=k)
                if fallback_hits:
                    for hit in fallback_hits:
                        hit["source"] = hit.get("source", "qdrant")
                    return fallback_hits

        # Last resort mock data
        return [{
            "path": "mock/development.py",
            "content": f"# Last resort mock result for: {query}\n# All configured sources failed",
            "score": 0.1,
            "source": "mock_fallback"
        }]

    except Exception as e:
        logger.error(f"Repo search failed: {e}")
        return [{
            "path": "error/search.py",
            "content": f"# Search error: {str(e)}\n# Query: {query}",
            "score": 0.01,
            "source": "error"
        }]


def rag_tool(query: str, swarm_stage: Optional[str] = None) -> str:
    """
    Enhanced RAG tool with multi-service support
    Maintains backward compatibility with existing Swarm system
    """
    try:
        k = int(os.getenv("RAG_TOPK", "8"))
        results = repo_search(query, k=k, swarm_stage=swarm_stage)

        # Enhanced formatting with service attribution
        formatted_results = {
            "query": query,
            "swarm_stage": swarm_stage,
            "result_count": len(results),
            "services_used": list(set(r.get("source", "unknown") for r in results)),
            "results": results[:k],
            "enhanced": True,  # Flag to indicate enhanced pipeline
            "timestamp": time.time()
        }

        output = json.dumps(formatted_results, indent=2)
        max_chars = int(os.getenv("MAX_RAG_CHARS", "8000"))

        return output[:max_chars]

    except Exception as e:
        logger.error(f"RAG tool failed: {e}")
        return json.dumps({
            "error": f"RAG tool failed: {str(e)}",
            "query": query,
            "fallback": True,
            "timestamp": time.time()
        })

# New enhanced functions for advanced use cases


async def multi_service_search(
    query: str,
    k: int = 8,
    swarm_stage: Optional[str] = None,
    services: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Advanced multi-service search with intelligent routing

    Args:
        query: Search query
        k: Number of results to return
        swarm_stage: Current Swarm stage for context-aware routing
        services: Specific services to search (None = auto-route)

    Returns:
        List of search results from multiple services
    """
    pipeline = await get_rag_pipeline()

    if services is None:
        services = await pipeline.intelligent_routing(query, swarm_stage)

    return await pipeline.search_multi_service(query, k, swarm_stage, services)


async def get_rag_metrics() -> Dict[str, Any]:
    """Get RAG pipeline performance metrics"""
    pipeline = await get_rag_pipeline()
    return pipeline.get_performance_metrics()
