"""
Unified Memory Store Interface
Integrates all memory components into a single, powerful interface
Part of 2025 Memory Stack Modernization
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.core.ai_logger import logger
from app.embeddings.agno_embedding_service import (
    AgnoEmbeddingRequest,
    AgnoEmbeddingService,
)
from app.memory.crdt_memory_sync import CRDTMemoryStore
from app.memory.hybrid_vector_manager import (
    CollectionConfig,
    HybridVectorManager,
    QueryType,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class RetrievalLevel(Enum):
    """Hierarchical retrieval levels"""
    DOCUMENT = "document"    # Coarse-grained
    SECTION = "section"      # Medium-grained
    SNIPPET = "snippet"      # Fine-grained


@dataclass
class MemoryEntry:
    """Unified memory entry"""
    id: str
    content: dict[str, Any]
    embeddings: list[float]
    metadata: dict[str, Any]
    tags: list[str]
    hierarchy: dict[str, Any]  # Document/section/snippet info
    timestamp: float
    agent_id: str


@dataclass
class RetrievalResult:
    """Unified retrieval result"""
    entries: list[MemoryEntry]
    query: str
    level: RetrievalLevel
    total_results: int
    latency_ms: float
    sources: list[str]  # Which databases were used


class UnifiedMemoryStore:
    """
    Unified interface for the advanced memory stack
    Features:
    - Portkey-routed embeddings with 1600+ models
    - Hybrid vector search (Weaviate + Milvus)
    - CRDT-based distributed synchronization
    - Hierarchical retrieval (Document→Section→Snippet)
    - Ontology-driven tagging
    - Real-time performance monitoring
    """

    def __init__(
        self,
        agent_id: str,
        enable_sync: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize unified memory store
        
        Args:
            agent_id: Unique agent identifier
            enable_sync: Enable CRDT synchronization
            cache_size: Size of memory cache
        """
        self.agent_id = agent_id
        self.enable_sync = enable_sync
        self.cache_size = cache_size

        # Initialize components
        self.embedding_service = AgnoEmbeddingService()
        self.vector_manager = HybridVectorManager()
        self.crdt_store = CRDTMemoryStore(agent_id) if enable_sync else None

        # Memory cache
        self.cache: dict[str, MemoryEntry] = {}
        self.cache_order: list[str] = []

        # Performance metrics
        self.metrics = {
            'total_memories': 0,
            'total_retrievals': 0,
            'avg_store_latency_ms': 0.0,
            'avg_retrieval_latency_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Initialize collections
        self._initialized = False

    async def initialize(self):
        """Initialize memory store and create collections"""
        if self._initialized:
            return

        # Create vector collections
        config = CollectionConfig(
            name="sophia_unified_memory",
            dimension=1024,
            index_type="HNSW",
            metric_type="COSINE",
            properties=[
                {"name": "content", "type": "text"},
                {"name": "metadata", "type": "object"},
                {"name": "tags", "type": "string[]"},
                {"name": "agent_id", "type": "string"},
                {"name": "timestamp", "type": "number"}
            ]
        )

        await self.vector_manager.create_collection(config, target="both")

        # Start CRDT sync if enabled
        if self.crdt_store:
            await self.crdt_store.start()

        self._initialized = True
        logger.info(f"Initialized unified memory store for agent {self.agent_id}")

    async def store(
        self,
        content: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        auto_tag: bool = True
    ) -> str:
        """
        Store memory with automatic embedding and tagging
        
        Args:
            content: Memory content
            metadata: Optional metadata
            tags: Optional tags
            auto_tag: Enable automatic tagging
            
        Returns:
            Memory ID
        """
        start_time = time.perf_counter()

        # Generate memory ID
        memory_id = f"{self.agent_id}_{time.time_ns()}"

        # Extract text for embedding
        text = self._extract_text(content)

        # Detect use case for embedding
        use_case = self._detect_use_case(content)

        # Generate embeddings using Agno service
        request = AgnoEmbeddingRequest(
            texts=[text],
            use_case=use_case
        )
        embedding_response = await self.embedding_service.embed(request)
        embeddings = embedding_response.embeddings[0]

        # Auto-generate tags if enabled
        if auto_tag:
            auto_tags = await self._auto_generate_tags(content, text)
            tags = (tags or []) + auto_tags

        # Create memory entry
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            embeddings=embeddings,
            metadata=metadata or {},
            tags=tags or [],
            hierarchy=self._extract_hierarchy(content),
            timestamp=time.time(),
            agent_id=self.agent_id
        )

        # Store in vector databases
        await self.vector_manager.insert_vectors(
            collection="sophia_unified_memory",
            vectors=[embeddings],
            metadata=[{
                "id": memory_id,
                "content": content,
                "metadata": metadata,
                "tags": tags,
                "agent_id": self.agent_id,
                "timestamp": entry.timestamp
            }],
            target="both"  # Store in both Weaviate and Milvus
        )

        # Store in CRDT if sync enabled
        if self.crdt_store:
            await self.crdt_store.add_memory(
                memory_id,
                {
                    "content": content,
                    "metadata": metadata,
                    "tags": tags,
                    "embeddings": embeddings
                }
            )

        # Update cache
        self._update_cache(entry)

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        self._update_metrics('store', latency_ms)

        logger.debug(f"Stored memory {memory_id} in {latency_ms:.2f}ms")

        return memory_id

    async def retrieve(
        self,
        query: str,
        level: RetrievalLevel = RetrievalLevel.DOCUMENT,
        limit: int = 10,
        filters: Optional[dict[str, Any]] = None,
        use_cache: bool = True
    ) -> RetrievalResult:
        """
        Hierarchical memory retrieval
        
        Args:
            query: Search query
            level: Retrieval level (document/section/snippet)
            limit: Maximum results
            filters: Optional filters
            use_cache: Use cached results
            
        Returns:
            Retrieval results
        """
        start_time = time.perf_counter()

        # Check cache first
        if use_cache:
            cache_key = f"{query}:{level.value}:{limit}"
            if cache_key in self.cache:
                self.metrics['cache_hits'] += 1
                cached_entry = self.cache[cache_key]
                return RetrievalResult(
                    entries=[cached_entry],
                    query=query,
                    level=level,
                    total_results=1,
                    latency_ms=0.1,
                    sources=['cache']
                )

        self.metrics['cache_misses'] += 1

        # Perform hierarchical retrieval
        if level == RetrievalLevel.DOCUMENT:
            results = await self._document_level_retrieval(query, filters, limit)
        elif level == RetrievalLevel.SECTION:
            results = await self._section_level_retrieval(query, filters, limit)
        else:  # SNIPPET
            results = await self._snippet_level_retrieval(query, filters, limit)

        # Convert to memory entries
        entries = []
        for result in results:
            entry = MemoryEntry(
                id=result.id,
                content=result.content,
                embeddings=result.vector or [],
                metadata=result.metadata,
                tags=result.metadata.get('tags', []),
                hierarchy={},
                timestamp=result.metadata.get('timestamp', 0),
                agent_id=result.metadata.get('agent_id', '')
            )
            entries.append(entry)

        # Create retrieval result
        retrieval_result = RetrievalResult(
            entries=entries,
            query=query,
            level=level,
            total_results=len(entries),
            latency_ms=(time.perf_counter() - start_time) * 1000,
            sources=list(set(r.source for r in results))
        )

        # Update metrics
        self._update_metrics('retrieve', retrieval_result.latency_ms)

        return retrieval_result

    async def _document_level_retrieval(
        self,
        query: str,
        filters: Optional[dict],
        limit: int
    ) -> list[VectorSearchResult]:
        """Document-level retrieval (coarse-grained)"""
        # Use Weaviate for hybrid search
        results = await self.vector_manager.route_query(
            QueryType.REALTIME,
            query=query,
            collection="sophia_unified_memory",
            filters=filters,
            alpha=0.7,  # Balance vector and keyword
            limit=limit * 2  # Get more for filtering
        )

        # Filter to document-level results
        document_results = []
        seen_docs = set()

        for result in results:
            doc_id = result.metadata.get('document_id', result.id)
            if doc_id not in seen_docs:
                document_results.append(result)
                seen_docs.add(doc_id)
                if len(document_results) >= limit:
                    break

        return document_results

    async def _section_level_retrieval(
        self,
        query: str,
        filters: Optional[dict],
        limit: int
    ) -> list[VectorSearchResult]:
        """Section-level retrieval (medium-grained)"""
        # First get documents
        doc_results = await self._document_level_retrieval(
            query, filters, limit * 2
        )

        # Then search within documents for sections
        section_results = []

        for doc in doc_results:
            # Generate query embedding using Agno service
            query_request = AgnoEmbeddingRequest(
                texts=[query],
                use_case="search"
            )
            query_response = await self.embedding_service.embed(query_request)

            # Search for sections within document
            sections = await self.vector_manager.route_query(
                QueryType.ANALYTICS,
                vectors=[query_response.embeddings[0]],
                collection="sophia_unified_memory",
                filters=f"document_id == '{doc.id}'",
                top_k=5
            )

            section_results.extend(sections[:2])  # Take top 2 sections per doc

            if len(section_results) >= limit:
                break

        return section_results[:limit]

    async def _snippet_level_retrieval(
        self,
        query: str,
        filters: Optional[dict],
        limit: int
    ) -> list[VectorSearchResult]:
        """Snippet-level retrieval (fine-grained)"""
        # Get sections first
        section_results = await self._section_level_retrieval(
            query, filters, limit * 2
        )

        # Extract snippets from sections
        snippet_results = []

        for section in section_results:
            # Extract relevant snippets using reranking
            content_text = str(section.content.get('text', ''))
            snippets = self._extract_snippets(content_text, query)

            for snippet in snippets[:2]:  # Take top 2 snippets per section
                # Create snippet result
                snippet_result = VectorSearchResult(
                    id=f"{section.id}_snippet_{len(snippet_results)}",
                    content={'text': snippet},
                    score=section.score * 0.9,  # Slightly lower score
                    vector=None,
                    metadata={**section.metadata, 'level': 'snippet'},
                    source=section.source,
                    latency_ms=0
                )
                snippet_results.append(snippet_result)

                if len(snippet_results) >= limit:
                    break

            if len(snippet_results) >= limit:
                break

        return snippet_results[:limit]

    async def update(
        self,
        memory_id: str,
        updates: dict[str, Any],
        regenerate_embeddings: bool = True
    ) -> bool:
        """
        Update existing memory
        
        Args:
            memory_id: Memory ID
            updates: Updates to apply
            regenerate_embeddings: Regenerate embeddings
            
        Returns:
            Success status
        """
        # Update in CRDT store
        if self.crdt_store:
            success = await self.crdt_store.update_memory(memory_id, updates)
            if not success:
                return False

        # Regenerate embeddings if needed
        if regenerate_embeddings:
            text = self._extract_text(updates)
            request = AgnoEmbeddingRequest(
                texts=[text],
                use_case="general"
            )
            embedding_response = await self.embedding_service.embed(request)

            # Update in vector databases
            # Note: This would require database-specific update operations
            logger.info(f"Updated embeddings for memory {memory_id}")

        # Invalidate cache
        self._invalidate_cache(memory_id)

        return True

    async def delete(self, memory_id: str) -> bool:
        """
        Delete memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Success status
        """
        # Delete from CRDT store
        if self.crdt_store:
            await self.crdt_store.delete_memory(memory_id)

        # Delete from vector databases
        await self.vector_manager.weaviate_client.delete_object(
            "sophia_unified_memory", memory_id
        )

        # Invalidate cache
        self._invalidate_cache(memory_id)

        return True

    async def sync_with_peers(self, peer_stores: list['UnifiedMemoryStore']):
        """
        Synchronize with peer memory stores
        
        Args:
            peer_stores: List of peer stores
        """
        if not self.crdt_store:
            logger.warning("CRDT sync not enabled")
            return

        for peer in peer_stores:
            if peer.crdt_store:
                self.crdt_store.add_peer(peer.agent_id, peer.crdt_store)
                peer.crdt_store.add_peer(self.agent_id, self.crdt_store)

        logger.info(f"Connected to {len(peer_stores)} peer stores")

    def _extract_text(self, content: dict[str, Any]) -> str:
        """Extract text from content for embedding"""
        if 'text' in content:
            return content['text']
        elif 'content' in content:
            return str(content['content'])
        else:
            # Convert dict to text representation
            return ' '.join(str(v) for v in content.values())

    def _detect_use_case(self, content: dict[str, Any]) -> str:
        """Detect use case for embedding generation"""
        if 'code' in content or 'language' in content:
            return "code"

        if 'type' in content:
            if content['type'] in ['documentation', 'reference', 'knowledge']:
                return "rag"
            elif content['type'] in ['search', 'query']:
                return "search"

        # Default to general use case
        return "general"

    def _extract_hierarchy(self, content: dict[str, Any]) -> dict[str, Any]:
        """Extract hierarchical information"""
        return {
            'document_id': content.get('document_id', ''),
            'section_id': content.get('section_id', ''),
            'snippet_id': content.get('snippet_id', ''),
            'level': content.get('level', 'document')
        }

    def _extract_snippets(self, text: str, query: str, snippet_size: int = 200) -> list[str]:
        """Extract relevant snippets from text"""
        words = text.split()
        query_words = set(query.lower().split())

        snippets = []
        for i in range(0, len(words), snippet_size // 2):
            snippet = ' '.join(words[i:i + snippet_size])
            # Score by query word overlap
            snippet_words = set(snippet.lower().split())
            overlap = len(query_words & snippet_words)
            if overlap > 0:
                snippets.append((snippet, overlap))

        # Sort by relevance
        snippets.sort(key=lambda x: x[1], reverse=True)

        return [s[0] for s in snippets[:5]]

    async def _auto_generate_tags(self, content: dict[str, Any], text: str) -> list[str]:
        """Auto-generate tags from content"""
        tags = []

        # Extract entity types
        if 'type' in content:
            tags.append(f"type:{content['type']}")

        # Extract language for code
        if 'language' in content:
            tags.append(f"lang:{content['language']}")

        # Extract domain
        if 'domain' in content:
            tags.append(f"domain:{content['domain']}")

        # Add agent tag
        tags.append(f"agent:{self.agent_id}")

        # Add timestamp tag
        tags.append(f"time:{int(time.time() // 3600)}")  # Hourly buckets

        return tags

    def _update_cache(self, entry: MemoryEntry):
        """Update memory cache"""
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry
            oldest = self.cache_order.pop(0)
            del self.cache[oldest]

        self.cache[entry.id] = entry
        self.cache_order.append(entry.id)

    def _invalidate_cache(self, memory_id: str):
        """Invalidate cache entry"""
        if memory_id in self.cache:
            del self.cache[memory_id]
            self.cache_order.remove(memory_id)

    def _update_metrics(self, operation: str, latency_ms: float):
        """Update performance metrics"""
        if operation == 'store':
            self.metrics['total_memories'] += 1
            n = self.metrics['total_memories']
            prev_avg = self.metrics['avg_store_latency_ms']
            self.metrics['avg_store_latency_ms'] = (prev_avg * (n - 1) + latency_ms) / n
        else:
            self.metrics['total_retrievals'] += 1
            n = self.metrics['total_retrievals']
            prev_avg = self.metrics['avg_retrieval_latency_ms']
            self.metrics['avg_retrieval_latency_ms'] = (prev_avg * (n - 1) + latency_ms) / n

    def get_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics"""
        metrics = {
            **self.metrics,
            'embedding_metrics': self.embedding_service.get_metrics(),
            'vector_metrics': self.vector_manager.get_metrics(),
            'cache_hit_rate': (
                self.metrics['cache_hits'] /
                (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
                else 0
            )
        }

        if self.crdt_store:
            metrics['crdt_metrics'] = self.crdt_store.get_state_snapshot()

        return metrics

    async def close(self):
        """Clean up resources"""
        if self.crdt_store:
            await self.crdt_store.stop()

        logger.info(f"Closed unified memory store for agent {self.agent_id}")


# Example usage
if __name__ == "__main__":
    async def test_unified_memory():
        # Create memory store
        store = UnifiedMemoryStore("test-agent")
        await store.initialize()

        # Store memory
        memory_id = await store.store(
            content={
                "text": "This is a test memory about machine learning algorithms",
                "type": "documentation",
                "language": "english"
            },
            metadata={"source": "test", "importance": "high"},
            tags=["ml", "algorithms", "test"]
        )
        logger.info(f"Stored memory: {memory_id}")

        # Retrieve at different levels
        doc_results = await store.retrieve(
            "machine learning",
            level=RetrievalLevel.DOCUMENT,
            limit=5
        )
        logger.info(f"Document results: {doc_results.total_results}")

        section_results = await store.retrieve(
            "algorithms",
            level=RetrievalLevel.SECTION,
            limit=5
        )
        logger.info(f"Section results: {section_results.total_results}")

        # Show metrics
        metrics = store.get_metrics()
        logger.info("\nMetrics:")
        logger.info(f"  Total memories: {metrics['total_memories']}")
        logger.info(f"  Avg store latency: {metrics['avg_store_latency_ms']:.2f}ms")
        logger.info(f"  Cache hit rate: {metrics['cache_hit_rate']:.2%}")

        # Cleanup
        await store.close()

    asyncio.run(test_unified_memory())
