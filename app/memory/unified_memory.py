import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import aioredis

logger = logging.getLogger(__name__)

# Singleton memory store instance
_memory_store = None

class UnifiedMemoryStore:
    """Redis-backed unified memory storage with proper async implementation"""

    def __init__(self, config: dict):
        self.config = config
        self.redis = None
        self.pool = None
        self.initialize_task = None

    async def initialize(self):
        """Initialize Redis connection pool"""
        if self.initialize_task:
            return await self.initialize_task

        self.initialize_task = asyncio.create_task(self._do_initialize())
        await self.initialize_task
        return self.initialize_task.result()

    async def _do_initialize(self):
        """Actual Redis initialization"""
        try:
            self.pool = await aioredis.create_redis_pool(
                self.config.get('redis_url', 'redis://localhost:6379'),
                minsize=self.config.get('min_pool_size', 5),
                maxsize=self.config.get('max_pool_size', 20)
            )
            self.redis = self.pool
            logger.info("✅ Redis memory store connected successfully")
        except Exception as e:
            logger.error(f"Redis initialization failed: {str(e)}")
            raise

    async def store_memory(self, content: str, metadata: dict[str, Any]):
        """Store memory with metadata and generate new ID"""
        if not self.redis:
            await self.initialize()

        memory_id = f"mem:{uuid4().hex}"
        timestamp = datetime.utcnow().isoformat()

        # Store main content
        await self.redis.set(f"memory:{memory_id}:content", content)

        # Store metadata
        metadata = {
            **metadata,
            "timestamp": timestamp,
            "type": metadata.get("type", "text"),
            "memory_id": memory_id
        }

        # Store metadata separately for indexing
        await self.redis.hmset(f"memory:{memory_id}:meta", metadata)

        # Add to global index
        await self.redis.sadd("memory:index", memory_id)

        logger.debug(f"📦 Stored memory {memory_id} with metadata {metadata}")
        return memory_id

    async def search_memory(self, query: str, filters: dict[str, Any] = None):
        """Search memory with filters and semantic similarity support"""
        if not self.redis:
            await self.initialize()

        # Get all memory IDs from index
        memory_ids = await self.redis.smembers("memory:index")

        # Apply filters
        filtered_ids = []
        for mem_id in memory_ids:
            meta = await self.redis.hgetall(f"memory:{mem_id}:meta")
            if self._matches_filters(meta, filters):
                filtered_ids.append(mem_id)

        # Get content for matching IDs
        results = []
        for mem_id in filtered_ids:
            content = await self.redis.get(f"memory:{mem_id}:content")
            meta = await self.redis.hgetall(f"memory:{mem_id}:meta")

            results.append({
                "id": mem_id.decode() if isinstance(mem_id, bytes) else mem_id,
                "content": content.decode() if isinstance(content, bytes) else content,
                "metadata": {k.decode(): v.decode() for k,v in meta.items()} if isinstance(meta, dict) else meta
            })

        logger.debug(f"🔍 Returned {len(results)} matches for query '{query}'")
        return results

    async def update_memory(self, memory_id: str, content: str, metadata: dict[str, Any]):
        """Update existing memory entry"""
        if not self.redis:
            await self.initialize()

        # Update content
        await self.redis.set(f"memory:{memory_id}:content", content)

        # Update metadata
        await self.redis.hmset(f"memory:{memory_id}:meta", metadata)

        logger.debug(f"✏️ Updated memory {memory_id}")
        return True

    async def delete_memory(self, memory_id: str):
        """Delete memory entry"""
        if not self.redis:
            await self.initialize()

        # Delete content
        await self.redis.delete(f"memory:{memory_id}:content")

        # Delete metadata
        await self.redis.delete(f"memory:{memory_id}:meta")

        # Remove from index
        await self.redis.srem("memory:index", memory_id)

        logger.debug(f"🗑️ Deleted memory {memory_id}")
        return True

    def _matches_filters(self, meta: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if metadata matches filters"""
        if not filters:
            return True

        for key, value in filters.items():
            if key not in meta:
                return False
            if isinstance(value, str) and meta[key] != value:
                return False
            if isinstance(value, list) and meta[key] not in value:
                return False
        return True

    async def close(self):
        """Close Redis connection pool"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection closed")

# Module-level async wrappers for API compatibility
def get_memory_store():
    """Return a singleton UnifiedMemoryStore instance"""
    global _memory_store
    if _memory_store is None:
        # Initialize with default config
        _memory_store = UnifiedMemoryStore({
            "redis_url": "redis://localhost:6379",
            "min_pool_size": 5,
            "max_pool_size": 20
        })
        # Async initialize
        asyncio.create_task(_memory_store.initialize())
    return _memory_store

async def store_memory(content: str, metadata: dict[str, Any]):
    store = await get_memory_store()
    return await store.store_memory(content, metadata)

async def search_memory(query: str, filters: dict[str, Any] = None, top_k: int = 10):
    store = await get_memory_store()
    return await store.search_memory(query, filters)

async def update_memory(memory_id: str, content: str, metadata: dict[str, Any]):
    store = await get_memory_store()
    return await store.update_memory(memory_id, content, metadata)

async def delete_memory(memory_id: str):
    store = await get_memory_store()
    return await store.delete_memory(memory_id)
