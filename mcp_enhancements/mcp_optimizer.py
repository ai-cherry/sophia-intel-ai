"""
SOPHIA Intel MCP Server Enhancements
Phase 7 of V4 Mega Upgrade - MCP Optimization

Enhanced MCP server with n8n vs Qdrant optimization and context persistence
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MCPOptimizer:
    """
    MCP (Model Context Protocol) optimization system for SOPHIA Intel.
    Provides intelligent routing between n8n MCP and Qdrant MCP based on context type.
    """
    
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.n8n_mcp_enabled = os.getenv("N8N_MCP_ENABLED", "true").lower() == "true"
        
        # MCP collections for different context types
        self.collections = {
            "workflow_context": "sophia_workflows",
            "code_context": "sophia_code",
            "conversation_context": "sophia_conversations",
            "system_context": "sophia_system"
        }
        
        logger.info("Initialized MCP Optimizer with Qdrant and Redis")
    
    async def optimize_context_storage(self, context_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently route context storage between n8n MCP and Qdrant MCP.
        
        Args:
            context_type: Type of context (workflow, code, conversation, system)
            content: Content to store
            metadata: Additional metadata
            
        Returns:
            Storage result with optimization details
        """
        try:
            # Determine optimal storage strategy
            storage_strategy = self._determine_storage_strategy(context_type, content, metadata)
            
            if storage_strategy == "qdrant_primary":
                result = await self._store_in_qdrant(context_type, content, metadata)
                # Cache in Redis for fast access
                await self._cache_in_redis(context_type, content, metadata, ttl=3600)
            
            elif storage_strategy == "n8n_primary":
                result = await self._store_in_n8n_mcp(context_type, content, metadata)
                # Backup in Qdrant for persistence
                await self._store_in_qdrant(context_type, content, metadata)
            
            else:  # hybrid_storage
                # Store in both systems with different priorities
                qdrant_result = await self._store_in_qdrant(context_type, content, metadata)
                n8n_result = await self._store_in_n8n_mcp(context_type, content, metadata)
                result = {
                    "strategy": "hybrid",
                    "qdrant": qdrant_result,
                    "n8n": n8n_result
                }
            
            # Log optimization decision
            await self._log_optimization_decision(context_type, storage_strategy, result)
            
            return {
                "status": "optimized",
                "strategy": storage_strategy,
                "context_type": context_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"MCP optimization error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "context_type": context_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def _determine_storage_strategy(self, context_type: str, content: str, metadata: Dict[str, Any]) -> str:
        """Determine optimal storage strategy based on context characteristics"""
        
        # Workflow contexts -> n8n MCP (better workflow integration)
        if context_type == "workflow_context" and self.n8n_mcp_enabled:
            return "n8n_primary"
        
        # Code contexts -> Qdrant (better semantic search)
        if context_type == "code_context":
            return "qdrant_primary"
        
        # Large content -> Qdrant (better vector storage)
        if len(content) > 10000:
            return "qdrant_primary"
        
        # Real-time contexts -> hybrid (fast access + persistence)
        if metadata.get("priority") == "real_time":
            return "hybrid_storage"
        
        # Default to Qdrant for semantic capabilities
        return "qdrant_primary"
    
    async def _store_in_qdrant(self, context_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store context in Qdrant vector database"""
        try:
            collection_name = self.collections.get(context_type, "sophia_general")
            
            # Ensure collection exists
            await self._ensure_qdrant_collection(collection_name)
            
            # Generate embedding (simplified - would use actual embedding model)
            embedding = await self._generate_embedding(content)
            
            # Create point
            point_id = hash(content + str(datetime.now().timestamp()))
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "content": content,
                    "context_type": context_type,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat(),
                    "source": "sophia_mcp_optimizer"
                }
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            return {
                "storage": "qdrant",
                "collection": collection_name,
                "point_id": point_id,
                "status": "stored"
            }
            
        except Exception as e:
            logger.error(f"Qdrant storage error: {e}")
            return {"storage": "qdrant", "status": "error", "error": str(e)}
    
    async def _store_in_n8n_mcp(self, context_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store context in n8n MCP system"""
        try:
            if not self.n8n_mcp_enabled:
                return {"storage": "n8n_mcp", "status": "disabled"}
            
            # Store in Redis with n8n MCP structure
            mcp_key = f"n8n_mcp:{context_type}:{hash(content)}"
            mcp_data = {
                "content": content,
                "context_type": context_type,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "mcp_version": "1.0"
            }
            
            await self.redis_client.setex(
                mcp_key,
                86400,  # 24 hours TTL
                json.dumps(mcp_data)
            )
            
            return {
                "storage": "n8n_mcp",
                "key": mcp_key,
                "status": "stored"
            }
            
        except Exception as e:
            logger.error(f"n8n MCP storage error: {e}")
            return {"storage": "n8n_mcp", "status": "error", "error": str(e)}
    
    async def _cache_in_redis(self, context_type: str, content: str, metadata: Dict[str, Any], ttl: int = 3600):
        """Cache context in Redis for fast access"""
        try:
            cache_key = f"mcp_cache:{context_type}:{hash(content)}"
            cache_data = {
                "content": content,
                "metadata": metadata,
                "cached_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    async def _ensure_qdrant_collection(self, collection_name: str):
        """Ensure Qdrant collection exists"""
        try:
            collections = self.qdrant_client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Qdrant collection setup error: {e}")
    
    async def _generate_embedding(self, content: str) -> List[float]:
        """Generate embedding for content (simplified implementation)"""
        # This would use an actual embedding model like sentence-transformers
        # For now, return a dummy embedding
        import hashlib
        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hex to normalized float vector
        embedding = []
        for i in range(0, len(hash_hex), 2):
            byte_val = int(hash_hex[i:i+2], 16)
            normalized_val = (byte_val - 127.5) / 127.5
            embedding.append(normalized_val)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.extend(embedding[:384-len(embedding)])
        
        return embedding[:384]
    
    async def _log_optimization_decision(self, context_type: str, strategy: str, result: Dict[str, Any]):
        """Log MCP optimization decisions for analysis"""
        try:
            log_data = {
                "context_type": context_type,
                "strategy": strategy,
                "result_status": result.get("status"),
                "timestamp": datetime.now().isoformat(),
                "optimizer": "sophia_mcp_v4"
            }
            
            await self.redis_client.lpush(
                "mcp_optimization_logs",
                json.dumps(log_data)
            )
            await self.redis_client.expire("mcp_optimization_logs", 604800)  # 7 days
            
        except Exception as e:
            logger.warning(f"Optimization logging error: {e}")
    
    async def retrieve_optimized_context(self, context_type: str, query: str, limit: int = 10) -> Dict[str, Any]:
        """Retrieve context using optimized strategy"""
        try:
            # Try cache first
            cache_results = await self._search_redis_cache(context_type, query, limit)
            
            if cache_results:
                return {
                    "status": "cache_hit",
                    "source": "redis_cache",
                    "results": cache_results
                }
            
            # Search Qdrant for semantic similarity
            qdrant_results = await self._search_qdrant(context_type, query, limit)
            
            # Search n8n MCP if enabled
            n8n_results = []
            if self.n8n_mcp_enabled:
                n8n_results = await self._search_n8n_mcp(context_type, query, limit)
            
            # Combine and rank results
            combined_results = self._combine_search_results(qdrant_results, n8n_results)
            
            return {
                "status": "retrieved",
                "sources": ["qdrant", "n8n_mcp"] if self.n8n_mcp_enabled else ["qdrant"],
                "results": combined_results[:limit],
                "total_found": len(combined_results)
            }
            
        except Exception as e:
            logger.error(f"Context retrieval error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _search_redis_cache(self, context_type: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Redis cache for matching contexts"""
        try:
            pattern = f"mcp_cache:{context_type}:*"
            keys = await self.redis_client.keys(pattern)
            
            results = []
            for key in keys[:limit]:
                data = await self.redis_client.get(key)
                if data:
                    cache_item = json.loads(data)
                    # Simple keyword matching (would use better search in production)
                    if query.lower() in cache_item["content"].lower():
                        results.append(cache_item)
            
            return results
            
        except Exception as e:
            logger.warning(f"Redis cache search error: {e}")
            return []
    
    async def _search_qdrant(self, context_type: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Qdrant for semantic similarity"""
        try:
            collection_name = self.collections.get(context_type, "sophia_general")
            query_embedding = await self._generate_embedding(query)
            
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "content": result.payload["content"],
                    "metadata": result.payload["metadata"],
                    "score": result.score,
                    "source": "qdrant"
                }
                for result in search_results
            ]
            
        except Exception as e:
            logger.warning(f"Qdrant search error: {e}")
            return []
    
    async def _search_n8n_mcp(self, context_type: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search n8n MCP system"""
        try:
            pattern = f"n8n_mcp:{context_type}:*"
            keys = await self.redis_client.keys(pattern)
            
            results = []
            for key in keys[:limit]:
                data = await self.redis_client.get(key)
                if data:
                    mcp_item = json.loads(data)
                    # Simple keyword matching
                    if query.lower() in mcp_item["content"].lower():
                        results.append({
                            "content": mcp_item["content"],
                            "metadata": mcp_item["metadata"],
                            "source": "n8n_mcp"
                        })
            
            return results
            
        except Exception as e:
            logger.warning(f"n8n MCP search error: {e}")
            return []
    
    def _combine_search_results(self, qdrant_results: List[Dict], n8n_results: List[Dict]) -> List[Dict[str, Any]]:
        """Combine and rank search results from different sources"""
        combined = []
        
        # Add Qdrant results with semantic scores
        for result in qdrant_results:
            result["combined_score"] = result.get("score", 0.5)
            combined.append(result)
        
        # Add n8n MCP results with default score
        for result in n8n_results:
            result["combined_score"] = 0.7  # Default score for exact matches
            combined.append(result)
        
        # Sort by combined score (descending)
        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return combined

# Global MCP optimizer instance
mcp_optimizer = MCPOptimizer()
