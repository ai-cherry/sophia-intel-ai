"""
Base Memory Interfaces
Defines abstract base classes for AI agent memory systems including
episodic, semantic, and working memory components.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, TypeVar
from uuid import uuid4
from pydantic import BaseModel, Field, validator
logger = logging.getLogger(__name__)
T = TypeVar("T")
class MemoryType(str, Enum):
    """Types of memory systems."""
    EPISODIC = "episodic"  # Specific experiences and events
    SEMANTIC = "semantic"  # General knowledge and facts
    WORKING = "working"  # Temporary, active information
    PROCEDURAL = "procedural"  # Skills and procedures
    META = "meta"  # Memory about memory
class MemorySearchStrategy(str, Enum):
    """Memory search strategies."""
    SIMILARITY = "similarity"  # Vector similarity search
    KEYWORD = "keyword"  # Keyword/text search
    TEMPORAL = "temporal"  # Time-based search
    CONTEXTUAL = "contextual"  # Context-aware search
    HYBRID = "hybrid"  # Combined strategies
class MemoryEntry(BaseModel):
    """
    Represents a single memory entry.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    memory_type: MemoryType
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Temporal information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None
    access_count: int = 0
    # Relevance and importance
    importance_score: float = Field(0.5, ge=0.0, le=1.0)
    relevance_decay: float = Field(0.95, ge=0.0, le=1.0)
    # Relationships
    related_entries: List[str] = Field(default_factory=list)  # Entry IDs
    tags: Set[str] = Field(default_factory=set)
    # Context information
    context_window: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    @validator("tags", pre=True)
    def convert_tags_to_set(cls, v):
        if isinstance(v, list):
            return set(v)
        return v
    def update_access(self) -> None:
        """Update access statistics."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1
    def calculate_current_relevance(
        self, decay_factor: Optional[float] = None
    ) -> float:
        """
        Calculate current relevance based on time decay.
        Args:
            decay_factor: Optional custom decay factor
        Returns:
            float: Current relevance score
        """
        if not self.accessed_at:
            age = (datetime.utcnow() - self.created_at).total_seconds() / 3600  # hours
        else:
            age = (datetime.utcnow() - self.accessed_at).total_seconds() / 3600
        decay = decay_factor or self.relevance_decay
        return self.importance_score * (decay**age)
    def add_relationship(self, entry_id: str) -> None:
        """Add relationship to another entry."""
        if entry_id not in self.related_entries:
            self.related_entries.append(entry_id)
    def add_tag(self, tag: str) -> None:
        """Add a tag to the entry."""
        self.tags.add(tag.lower().strip())
    class Config:
        validate_assignment = True
        json_encoders = {datetime: lambda v: v.isoformat(), set: lambda v: list(v)}
class MemoryQuery(BaseModel):
    """
    Query for retrieving memories.
    """
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[Set[str]] = None
    # Search parameters
    strategy: MemorySearchStrategy = MemorySearchStrategy.SIMILARITY
    limit: int = Field(10, gt=0, le=100)
    min_similarity: float = Field(0.0, ge=0.0, le=1.0)
    min_relevance: float = Field(0.0, ge=0.0, le=1.0)
    # Temporal filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    accessed_after: Optional[datetime] = None
    # Context filters
    context_filter: Optional[Dict[str, Any]] = None
    source_filter: Optional[str] = None
    @validator("tags", pre=True)
    def convert_tags_to_set(cls, v):
        if isinstance(v, list):
            return set(v)
        return v
    def has_content_query(self) -> bool:
        """Check if query has content-based search criteria."""
        return self.query_text is not None or self.query_embedding is not None
class MemoryResult(BaseModel):
    """
    Result from memory query.
    """
    entry: MemoryEntry
    similarity_score: float = 0.0
    relevance_score: float = 0.0
    combined_score: float = 0.0
    match_reason: str = ""
    @validator("combined_score", always=True)
    def calculate_combined_score(cls, v, values):
        """Calculate combined score if not provided."""
        if v == 0.0:
            similarity = values.get("similarity_score", 0.0)
            relevance = values.get("relevance_score", 0.0)
            return (similarity * 0.7) + (relevance * 0.3)
        return v
class MemoryStats(BaseModel):
    """
    Memory system statistics.
    """
    total_entries: int = 0
    entries_by_type: Dict[str, int] = Field(default_factory=dict)
    memory_usage_bytes: int = 0
    # Access statistics
    total_queries: int = 0
    cache_hit_rate: float = 0.0
    average_query_time: float = 0.0
    # Performance metrics
    index_size: int = 0
    last_cleanup: Optional[datetime] = None
    fragmentation_ratio: float = 0.0
class BaseMemory(ABC):
    """
    Abstract base class for memory systems.
    """
    def __init__(
        self,
        memory_type: MemoryType,
        max_entries: Optional[int] = None,
        embedding_dim: int = 384,
        **kwargs,
    ):
        """
        Initialize memory system.
        Args:
            memory_type: Type of memory system
            max_entries: Maximum number of entries (None for unlimited)
            embedding_dim: Dimension of embeddings
            **kwargs: Additional configuration
        """
        self.memory_type = memory_type
        self.max_entries = max_entries
        self.embedding_dim = embedding_dim
        self._entries: Dict[str, MemoryEntry] = {}
        self._stats = MemoryStats()
        self._config = kwargs
        logger.info(
            f"Initialized {memory_type.value} memory with max_entries={max_entries}"
        )
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry.
        Args:
            entry: Memory entry to store
        Returns:
            bool: True if stored successfully
        """
        pass
    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> List[MemoryResult]:
        """
        Retrieve memory entries based on query.
        Args:
            query: Memory query
        Returns:
            List[MemoryResult]: Retrieved memory results
        """
        pass
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        Delete a memory entry.
        Args:
            entry_id: ID of entry to delete
        Returns:
            bool: True if deleted successfully
        """
        pass
    async def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """
        Get entry by ID.
        Args:
            entry_id: Entry ID
        Returns:
            Optional[MemoryEntry]: Entry if found
        """
        entry = self._entries.get(entry_id)
        if entry:
            entry.update_access()
        return entry
    async def update(self, entry: MemoryEntry) -> bool:
        """
        Update an existing memory entry.
        Args:
            entry: Updated memory entry
        Returns:
            bool: True if updated successfully
        """
        if entry.id in self._entries:
            self._entries[entry.id] = entry
            await self._update_index(entry)
            return True
        return False
    async def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()
        await self._rebuild_index()
        self._stats = MemoryStats()
        logger.info(f"Cleared all entries from {self.memory_type.value} memory")
    async def cleanup_old_entries(self, max_age: timedelta) -> int:
        """
        Clean up entries older than max_age.
        Args:
            max_age: Maximum age for entries
        Returns:
            int: Number of entries removed
        """
        cutoff_time = datetime.utcnow() - max_age
        to_remove = []
        for entry_id, entry in self._entries.items():
            if entry.created_at < cutoff_time and entry.access_count == 0:
                to_remove.append(entry_id)
        removed_count = 0
        for entry_id in to_remove:
            if await self.delete(entry_id):
                removed_count += 1
        if removed_count > 0:
            self._stats.last_cleanup = datetime.utcnow()
            logger.info(f"Cleaned up {removed_count} old entries")
        return removed_count
    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        self._stats.total_entries = len(self._entries)
        self._stats.entries_by_type = {self.memory_type.value: len(self._entries)}
        return self._stats
    async def _update_index(self, entry: MemoryEntry) -> None:
        """Update search index for entry (to be overridden)."""
        pass
    async def _rebuild_index(self) -> None:
        """Rebuild search index (to be overridden)."""
        pass
    def _enforce_capacity_limit(self) -> None:
        """Remove old entries if over capacity."""
        if self.max_entries and len(self._entries) > self.max_entries:
            # Remove least recently used entries
            entries_by_access = sorted(
                self._entries.values(), key=lambda e: e.accessed_at or e.created_at
            )
            excess_count = len(self._entries) - self.max_entries
            for i in range(excess_count):
                entry_to_remove = entries_by_access[i]
                del self._entries[entry_to_remove.id]
                logger.debug(
                    f"Removed entry {entry_to_remove.id} due to capacity limit"
                )
class EpisodicMemory(BaseMemory):
    """
    Memory for specific experiences and events.
    Focuses on temporal ordering and contextual relationships.
    """
    def __init__(self, **kwargs):
        super().__init__(MemoryType.EPISODIC, **kwargs)
        self._temporal_index: List[str] = []  # Entry IDs sorted by time
    async def store(self, entry: MemoryEntry) -> bool:
        """Store episodic memory entry."""
        if entry.memory_type != MemoryType.EPISODIC:
            entry.memory_type = MemoryType.EPISODIC
        self._entries[entry.id] = entry
        self._insert_in_temporal_index(entry.id)
        self._enforce_capacity_limit()
        logger.debug(f"Stored episodic memory entry: {entry.id}")
        return True
    async def retrieve(self, query: MemoryQuery) -> List[MemoryResult]:
        """Retrieve episodic memories."""
        if query.strategy == MemorySearchStrategy.TEMPORAL:
            return await self._temporal_search(query)
        else:
            return await self._general_search(query)
    async def delete(self, entry_id: str) -> bool:
        """Delete episodic memory entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            if entry_id in self._temporal_index:
                self._temporal_index.remove(entry_id)
            return True
        return False
    def _insert_in_temporal_index(self, entry_id: str) -> None:
        """Insert entry ID in temporal index maintaining chronological order."""
        entry = self._entries[entry_id]
        entry_time = entry.created_at
        # Binary search for insertion point
        left, right = 0, len(self._temporal_index)
        while left < right:
            mid = (left + right) // 2
            mid_entry = self._entries[self._temporal_index[mid]]
            if mid_entry.created_at < entry_time:
                left = mid + 1
            else:
                right = mid
        self._temporal_index.insert(left, entry_id)
    async def _temporal_search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search based on temporal ordering."""
        results = []
        for entry_id in reversed(self._temporal_index):  # Most recent first
            if len(results) >= query.limit:
                break
            entry = self._entries[entry_id]
            # Apply temporal filters
            if query.created_after and entry.created_at < query.created_after:
                continue
            if query.created_before and entry.created_at > query.created_before:
                continue
            # Calculate relevance score
            relevance = entry.calculate_current_relevance()
            if relevance < query.min_relevance:
                continue
            results.append(
                MemoryResult(
                    entry=entry,
                    relevance_score=relevance,
                    match_reason="temporal_order",
                )
            )
        return results
    async def _general_search(self, query: MemoryQuery) -> List[MemoryResult]:
        """General search across all entries."""
        results = []
        for entry in self._entries.values():
            # Apply filters
            if query.tags and not query.tags.intersection(entry.tags):
                continue
            relevance = entry.calculate_current_relevance()
            if relevance < query.min_relevance:
                continue
            # Simple text matching if query text provided
            similarity = 0.0
            if query.query_text:
                similarity = self._calculate_text_similarity(
                    query.query_text, entry.content
                )
                if similarity < query.min_similarity:
                    continue
            results.append(
                MemoryResult(
                    entry=entry,
                    similarity_score=similarity,
                    relevance_score=relevance,
                    match_reason="content_match" if similarity > 0 else "tag_match",
                )
            )
        # Sort by combined score
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[: query.limit]
    def _calculate_text_similarity(self, query_text: str, content: str) -> float:
        """Simple text similarity calculation (to be enhanced with embeddings)."""
        query_words = set(query_text.lower().split())
        content_words = set(content.lower().split())
        if not query_words:
            return 0.0
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
class SemanticMemory(BaseMemory):
    """
    Memory for general knowledge and facts.
    Focuses on conceptual relationships and semantic similarity.
    """
    def __init__(self, **kwargs):
        super().__init__(MemoryType.SEMANTIC, **kwargs)
        self._concept_graph: Dict[str, Set[str]] = {}  # Concept -> related entry IDs
    async def store(self, entry: MemoryEntry) -> bool:
        """Store semantic memory entry."""
        if entry.memory_type != MemoryType.SEMANTIC:
            entry.memory_type = MemoryType.SEMANTIC
        self._entries[entry.id] = entry
        self._update_concept_graph(entry)
        self._enforce_capacity_limit()
        logger.debug(f"Stored semantic memory entry: {entry.id}")
        return True
    async def retrieve(self, query: MemoryQuery) -> List[MemoryResult]:
        """Retrieve semantic memories."""
        if query.strategy == MemorySearchStrategy.CONTEXTUAL:
            return await self._contextual_search(query)
        else:
            return await self._semantic_search(query)
    async def delete(self, entry_id: str) -> bool:
        """Delete semantic memory entry."""
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            # Remove from concept graph
            for concept in entry.tags:
                if concept in self._concept_graph:
                    self._concept_graph[concept].discard(entry_id)
                    if not self._concept_graph[concept]:
                        del self._concept_graph[concept]
            del self._entries[entry_id]
            return True
        return False
    def _update_concept_graph(self, entry: MemoryEntry) -> None:
        """Update concept graph with new entry."""
        for tag in entry.tags:
            if tag not in self._concept_graph:
                self._concept_graph[tag] = set()
            self._concept_graph[tag].add(entry.id)
    async def _semantic_search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search based on semantic similarity."""
        results = []
        candidate_entries = set()
        # Collect candidates based on concept overlap
        if query.tags:
            for tag in query.tags:
                if tag in self._concept_graph:
                    candidate_entries.update(self._concept_graph[tag])
        else:
            candidate_entries = set(self._entries.keys())
        for entry_id in candidate_entries:
            if len(results) >= query.limit:
                break
            entry = self._entries[entry_id]
            # Calculate semantic similarity
            tag_overlap = len(query.tags.intersection(entry.tags)) if query.tags else 0
            semantic_score = (
                tag_overlap / max(len(query.tags), 1) if query.tags else 0.0
            )
            # Text similarity if query provided
            text_similarity = 0.0
            if query.query_text:
                text_similarity = self._calculate_text_similarity(
                    query.query_text, entry.content
                )
            combined_similarity = max(semantic_score, text_similarity)
            if combined_similarity < query.min_similarity:
                continue
            relevance = entry.calculate_current_relevance()
            if relevance < query.min_relevance:
                continue
            results.append(
                MemoryResult(
                    entry=entry,
                    similarity_score=combined_similarity,
                    relevance_score=relevance,
                    match_reason="semantic_similarity",
                )
            )
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[: query.limit]
    async def _contextual_search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search based on contextual relationships."""
        # Similar to semantic search but considers entry relationships
        results = await self._semantic_search(query)
        # Expand results with related entries
        related_entry_ids = set()
        for result in results[
            : query.limit // 2
        ]:  # Use half the limit for initial results
            related_entry_ids.update(result.entry.related_entries)
        # Add related entries
        for entry_id in related_entry_ids:
            if entry_id in self._entries and len(results) < query.limit:
                entry = self._entries[entry_id]
                results.append(
                    MemoryResult(
                        entry=entry,
                        similarity_score=0.5,  # Lower similarity for related entries
                        relevance_score=entry.calculate_current_relevance(),
                        match_reason="contextual_relation",
                    )
                )
        return results[: query.limit]
    def _calculate_text_similarity(self, query_text: str, content: str) -> float:
        """Enhanced text similarity for semantic content."""
        # Simple implementation - would use embeddings in practice
        query_words = set(query_text.lower().split())
        content_words = set(content.lower().split())
        if not query_words or not content_words:
            return 0.0
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        return len(intersection) / len(union) if union else 0.0
class WorkingMemory(BaseMemory):
    """
    Memory for temporary, active information.
    Focuses on recent context and immediate relevance.
    """
    def __init__(self, max_entries: int = 50, **kwargs):
        super().__init__(MemoryType.WORKING, max_entries=max_entries, **kwargs)
        self._activation_levels: Dict[str, float] = {}
        self._decay_rate = kwargs.get("decay_rate", 0.1)
    async def store(self, entry: MemoryEntry) -> bool:
        """Store working memory entry."""
        if entry.memory_type != MemoryType.WORKING:
            entry.memory_type = MemoryType.WORKING
        self._entries[entry.id] = entry
        self._activation_levels[entry.id] = 1.0  # Full activation
        self._enforce_capacity_limit()
        logger.debug(f"Stored working memory entry: {entry.id}")
        return True
    async def retrieve(self, query: MemoryQuery) -> List[MemoryResult]:
        """Retrieve working memory entries."""
        await self._decay_activations()
        results = []
        for entry_id, entry in self._entries.items():
            activation = self._activation_levels.get(entry_id, 0.0)
            # Skip entries with very low activation
            if activation < 0.1:
                continue
            # Apply filters
            if query.tags and not query.tags.intersection(entry.tags):
                continue
            # Calculate similarity if query provided
            similarity = 0.0
            if query.query_text:
                similarity = self._calculate_text_similarity(
                    query.query_text, entry.content
                )
                if similarity < query.min_similarity:
                    continue
            # Working memory prioritizes activation level
            combined_score = (similarity * 0.3) + (activation * 0.7)
            results.append(
                MemoryResult(
                    entry=entry,
                    similarity_score=similarity,
                    relevance_score=activation,
                    combined_score=combined_score,
                    match_reason="working_memory_activation",
                )
            )
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[: query.limit]
    async def delete(self, entry_id: str) -> bool:
        """Delete working memory entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._activation_levels.pop(entry_id, None)
            return True
        return False
    async def activate(self, entry_id: str, boost: float = 0.2) -> None:
        """Boost activation level of an entry."""
        if entry_id in self._activation_levels:
            self._activation_levels[entry_id] = min(
                1.0, self._activation_levels[entry_id] + boost
            )
            logger.debug(f"Boosted activation for entry {entry_id}")
    async def _decay_activations(self) -> None:
        """Decay activation levels over time."""
        to_remove = []
        for entry_id in self._activation_levels:
            self._activation_levels[entry_id] *= 1 - self._decay_rate
            # Mark for removal if activation is too low
            if self._activation_levels[entry_id] < 0.01:
                to_remove.append(entry_id)
        # Remove entries with very low activation
        for entry_id in to_remove:
            await self.delete(entry_id)
    def _calculate_text_similarity(self, query_text: str, content: str) -> float:
        """Simple text similarity for working memory."""
        query_words = set(query_text.lower().split())
        content_words = set(content.lower().split())
        if not query_words:
            return 0.0
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
class MemoryManager:
    """
    Manages multiple memory systems and provides unified interface.
    """
    def __init__(self):
        self.memories: Dict[MemoryType, BaseMemory] = {}
        logger.info("Initialized memory manager")
    def register_memory(self, memory: BaseMemory) -> None:
        """
        Register a memory system.
        Args:
            memory: Memory system to register
        """
        self.memories[memory.memory_type] = memory
        logger.info(f"Registered {memory.memory_type.value} memory system")
    async def store_across_memories(
        self, content: str, memory_types: List[MemoryType], **metadata
    ) -> List[str]:
        """
        Store entry across multiple memory systems.
        Args:
            content: Content to store
            memory_types: Types of memory to store in
            **metadata: Additional metadata
        Returns:
            List[str]: Entry IDs created
        """
        entry_ids = []
        for memory_type in memory_types:
            if memory_type in self.memories:
                entry = MemoryEntry(
                    content=content, memory_type=memory_type, metadata=metadata
                )
                if await self.memories[memory_type].store(entry):
                    entry_ids.append(entry.id)
                    logger.debug(
                        f"Stored entry {entry.id} in {memory_type.value} memory"
                    )
        return entry_ids
    async def unified_retrieve(
        self, query: MemoryQuery, memory_types: Optional[List[MemoryType]] = None
    ) -> List[MemoryResult]:
        """
        Retrieve from multiple memory systems and combine results.
        Args:
            query: Memory query
            memory_types: Memory types to search (all if None)
        Returns:
            List[MemoryResult]: Combined results
        """
        if memory_types is None:
            memory_types = list(self.memories.keys())
        all_results = []
        for memory_type in memory_types:
            if memory_type in self.memories:
                try:
                    results = await self.memories[memory_type].retrieve(query)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(
                        f"Error retrieving from {memory_type.value} memory: {e}"
                    )
        # Remove duplicates and sort by combined score
        unique_results = {}
        for result in all_results:
            if result.entry.id not in unique_results:
                unique_results[result.entry.id] = result
            else:
                # Keep result with higher score
                if (
                    result.combined_score
                    > unique_results[result.entry.id].combined_score
                ):
                    unique_results[result.entry.id] = result
        final_results = list(unique_results.values())
        final_results.sort(key=lambda r: r.combined_score, reverse=True)
        return final_results[: query.limit]
    async def cleanup_all_memories(self, max_age: timedelta) -> Dict[str, int]:
        """
        Clean up old entries from all memory systems.
        Args:
            max_age: Maximum age for entries
        Returns:
            Dict[str, int]: Cleanup statistics by memory type
        """
        cleanup_stats = {}
        for memory_type, memory in self.memories.items():
            try:
                removed_count = await memory.cleanup_old_entries(max_age)
                cleanup_stats[memory_type.value] = removed_count
            except Exception as e:
                logger.error(f"Error cleaning up {memory_type.value} memory: {e}")
                cleanup_stats[memory_type.value] = 0
        return cleanup_stats
    def get_all_stats(self) -> Dict[str, MemoryStats]:
        """Get statistics from all memory systems."""
        return {
            memory_type.value: memory.get_stats()
            for memory_type, memory in self.memories.items()
        }
