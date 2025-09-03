import asyncio
import logging
from typing import Any, Optional, Union

import neo4j

from app.memory.embedding_coordinator import EmbeddingCoordinator
from app.memory.unified_embedder import UnifiedEmbedder
from app.memory.unified_memory import delete_memory, search_memory, store_memory

logger = logging.getLogger(__name__)

class WorkingMemory:
    """Session-scoped working memory stored in Redis"""

    def __init__(self, session_id: str, memory_store=None):
        self.session_id = session_id
        self.memory_store = memory_store or self._get_memory_store()

    async def store(self, key: str, content: str, metadata: dict[str, Any] = None):
        """Store in working memory with session-specific key"""
        namespace = f"wm:{self.session_id}:{key}"
        metadata = metadata or {}
        metadata.update({
            "namespace": namespace,
            "type": "working"
        })
        return await store_memory(content, metadata)

    async def get(self, key: str) -> Optional[dict]:
        """Get from working memory (by key namespace)"""
        namespace = f"wm:{self.session_id}:{key}"
        results = await search_memory("", {"namespace": namespace})
        return results[0] if results else None

    async def delete(self, key: str):
        """Delete from working memory"""
        namespace = f"wm:{self.session_id}:{key}"
        results = await search_memory("", {"namespace": namespace})
        if results:
            await delete_memory(results[0]["id"])
        return True

    async def list(self, prefix: str = "", limit: int = 100) -> list[dict]:
        """List working memory items with optional prefix"""
        namespace = f"wm:{self.session_id}:{prefix}%"
        results = await search_memory("", {"namespace": namespace})
        return results[:limit]

    def _get_memory_store(self):
        """Helper to get memory store instance"""
        return None  # Implementation uses global instance via unified_memory

class EpisodicMemory:
    """Persistent episodic memory stored via vector DB (Weaviate)"""

    def __init__(self, embedding_coordinator: EmbeddingCoordinator, unified_embedder: UnifiedEmbedder):
        self.embedding_coordinator = embedding_coordinator
        self.unified_embedder = unified_embedder
        self.vector_db = self._initialize_vector_db()

    def _initialize_vector_db(self):
        """Initialize vector store connection (Weaviate)"""
        # In production, this would connect to Weaviate
        logger.info("Initializing vector DB for episodic memory")
        return None  # Placeholder for actual connection

    async def store_event(self, task_id: str, thread_id: str, content: str, metadata: dict[str, Any] = None) -> str:
        """Store an event in episodic memory"""
        embedding = await self.unified_embedder.get_embedding(content)
        metadata = metadata or {}
        metadata.update({
            "task_id": task_id,
            "thread_id": thread_id,
            "type": "episodic"
        })

        # Store in vector DB via embedding coordinator
        event_id = await self.embedding_coordinator.store_vector(
            vector=embedding,
            metadata=metadata,
            content=content
        )

        logger.debug(f"Stored episodic event {event_id} for task {task_id}")
        return event_id

    async def search(self, query: str, filters: dict[str, Any] = None, top_k: int = 5) -> list[dict]:
        """Search episodic memory by semantic similarity"""
        embedding = await self.unified_embedder.get_embedding(query)
        results = await self.embedding_coordinator.vector_search(
            vector=embedding,
            filters=filters,
            top_k=top_k
        )
        return results

class SemanticMemory:
    """Knowledge graph storage using Neo4j for semantic relationships"""

    def __init__(self, neo4j_url: str, username: str, password: str):
        self.driver = neo4j.GraphDatabase.driver(
            neo4j_url,
            auth=(username, password)
        )

    async def add_fact(self, subject: str, predicate: str, object: str, confidence: float):
        """Add a fact to the knowledge graph"""
        async with self.driver.session() as session:
            query = """
            MERGE (s:Entity {name: $subject})
            MERGE (o:Entity {name: $object})
            MERGE (s)-[r:RELATES {predicate: $predicate, confidence: $confidence}]->(o)
            """
            await session.run(query, subject=subject, predicate=predicate, object=object, confidence=confidence)

    async def query_relations(self, entity: str, max_depth: int = 3) -> list[dict]:
        """Query relationships with depth limit"""
        async with self.driver.session() as session:
            query = """
            MATCH path = (e:Entity {name: $entity})-[:RELATES*1..$max_depth]-(n)
            RETURN e.name AS source, n.name AS target, 
                   rel.predicate AS predicate, 
                   rel.confidence AS confidence
            """
            result = await session.run(query, entity=entity, max_depth=max_depth)
            return [record.data() async for record in result]

    async def find_connections(self, entity1: str, entity2: str) -> list[dict]:
        """Find paths between two entities"""
        async with self.driver.session() as session:
            query = """
            MATCH path = (e1:Entity {name: $entity1})-[:RELATES*1..5]-(e2:Entity {name: $entity2})
            RETURN path
            """
            result = await session.run(query, entity1=entity1, entity2=entity2)
            return [record.data() async for record in result]

    async def update_confidence(self, fact_id: str, new_confidence: float):
        """Update confidence in a fact (by ID in graph)"""
        # Implementation would require precise fact ID tracking from the graph
        pass

class ProceduralMemory:
    """Memory for successful patterns and strategies"""

    def __init__(self, memory_store):
        self.memory_store = memory_store

    async def record_pattern(self, pattern_id: str, task_type: str, composition: list[str], outcome: str, timestamp: str = None):
        """Record a pattern in procedural memory"""
        timestamp = timestamp or asyncio.get_event_loop().time()
        metadata = {
            "type": "pattern",
            "task_type": task_type,
            "composition": composition,
            "outcome": outcome,
            "timestamp": timestamp
        }
        await store_memory(f"Pattern: {pattern_id}", metadata)

    async def get_top_patterns(self, domain: str, limit: int = 5) -> list[dict]:
        """Get top-rated patterns for a domain"""
        results = await search_memory("", {"type": "pattern", "domain": domain})
        return results[:limit]

class SwarmMemorySystem:
    """Unified memory system for all memory types"""

    def __init__(self, session_id: str, config: dict[str, Any]):
        self.session_id = session_id
        self.config = config

        # Initialize components
        self.working_memory = WorkingMemory(session_id)
        self.embedding_coordinator = EmbeddingCoordinator(config)
        self.unified_embedder = UnifiedEmbedder(config)
        self.episodic_memory = EpisodicMemory(
            self.embedding_coordinator,
            self.unified_embedder
        )
        self.knowledge_graph = SemanticMemory(
            config.get('neo4j_url', 'bolt://localhost:7687'),
            config.get('neo4j_user', 'neo4j'),
            config.get('neo4j_password', 'password')
        )
        self.procedural_memory = ProceduralMemory(self.working_memory)

    async def consolidate_session(self, session_id: str):
        """Move working memory to episodic memory for a session"""
        working = WorkingMemory(session_id)
        episodic = self.episodic_memory

        # Get all working memory items
        all_items = await working.list(prefix="", limit=100)

        # Move to episodic memory
        for item in all_items:
            await episodic.store_event(
                task_id=session_id,
                thread_id=item.get("metadata", {}).get("thread_id", "unknown"),
                content=item["content"],
                metadata=item.get("metadata", {})
            )

        # Delete working memory entries after consolidation
        for item in all_items:
            await working.delete(item["id"])

        logger.info(f"Consolidated session {session_id} from working to episodic memory")

    async def attach_relations(self, task_id: str, thread_id: str):
        """Attach semantic relations to episodic events"""
        # This would connect entities to knowledge graph
        pass

    async def get_context(self, task: dict[str, Any], max_tokens: int = 4000) -> dict:
        """Get context for task with token budgeting"""
        context = {}

        # 1. Working memory (recent, recency-weighted)
        working = WorkingMemory(self.session_id)
        recent_items = await working.list(prefix="", limit=10)
        context["working"] = recent_items

        # 2. Episodic memory (semantic similarity)
        episodic = self.episodic_memory
        episodic_results = await episodic.search(
            task.get("description", ""),
            {"task_id": task.get("id", "")},
            top_k=5
        )
        context["episodic"] = episodic_results

        # 3. Semantic memory (knowledge graph)
        graph_results = await self.knowledge_graph.query_relations(
            task.get("domain", "general"),
            max_depth=2
        )
        context["semantic"] = graph_results

        # 4. Procedural memory (past pattern success)
        patterns = await self.procedural_memory.get_top_patterns(
            task.get("domain", "general"),
            limit=3
        )
        context["procedural"] = patterns

        return context
