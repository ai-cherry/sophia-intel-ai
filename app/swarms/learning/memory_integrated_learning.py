#!/usr/bin/env python3
"""
Memory-Integrated Learning System for Sophia Intel AI Swarms
Seamless integration with UnifiedMemoryStore for persistent learning

Features:
- Vector embeddings for similarity-based learning retrieval
- Temporal knowledge graphs for causal learning relationships
- Working memory integration for session-specific context
- Episodic memory for experience replay and pattern recognition
- Semantic memory for concept and knowledge graphs
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from uuid import uuid4

import numpy as np
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from app.core.ai_logger import logger
from app.memory.unified_memory import UnifiedMemoryStore
from app.swarms.learning.adaptive_learning_system import (
    KnowledgeType,
    LearnedKnowledge,
    LearningExperience,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# =============================================================================
# MEMORY-INTEGRATED LEARNING COMPONENTS
# =============================================================================


@dataclass
class MemoryVector:
    """Vector representation for memory similarity search"""

    vector_id: str
    content_hash: str
    embedding: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def similarity(self, other: "MemoryVector") -> float:
        """Calculate cosine similarity with another vector"""
        if self.embedding.shape != other.embedding.shape:
            return 0.0

        norm_self = np.linalg.norm(self.embedding)
        norm_other = np.linalg.norm(other.embedding)

        if norm_self == 0 or norm_other == 0:
            return 0.0

        return np.dot(self.embedding, other.embedding) / (norm_self * norm_other)


@dataclass
class KnowledgeNode:
    """Node in the temporal knowledge graph"""

    node_id: str
    knowledge_id: str
    knowledge_type: KnowledgeType
    content: dict[str, Any]

    # Temporal relationships
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0

    # Graph relationships
    parent_nodes: list[str] = field(default_factory=list)
    child_nodes: list[str] = field(default_factory=list)
    related_nodes: list[str] = field(default_factory=list)

    # Performance metrics
    success_applications: int = 0
    total_applications: int = 0
    effectiveness_score: float = 0.0


@dataclass
class TemporalRelationship:
    """Relationship between knowledge nodes with temporal context"""

    relationship_id: str
    source_node: str
    target_node: str
    relationship_type: str  # 'causes', 'enables', 'improves', 'conflicts'

    strength: float = 0.5  # 0.0 to 1.0
    confidence: float = 0.5  # 0.0 to 1.0

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Evidence for the relationship
    supporting_experiences: list[str] = field(default_factory=list)
    contradicting_experiences: list[str] = field(default_factory=list)


class MemoryIntegratedLearningSystem:
    """
    Learning system that integrates deeply with UnifiedMemoryStore
    Provides vector similarity search, temporal knowledge graphs, and persistent learning
    """

    def __init__(
        self,
        memory_store: UnifiedMemoryStore,
        vector_dimension: int = 128,
        max_working_memory_size: int = 1000,
        knowledge_graph_max_nodes: int = 10000,
    ):
        self.memory_store = memory_store
        self.vector_dimension = vector_dimension
        self.max_working_memory_size = max_working_memory_size
        self.knowledge_graph_max_nodes = knowledge_graph_max_nodes

        # Memory components
        self.vector_index: dict[str, MemoryVector] = {}
        self.knowledge_graph: dict[str, KnowledgeNode] = {}
        self.temporal_relationships: dict[str, TemporalRelationship] = {}

        # Working memory for current session
        self.working_memory: list[dict[str, Any]] = []
        self.working_memory_vectors: list[MemoryVector] = []

        # Performance tracking
        self.memory_metrics = {
            "vectors_created": 0,
            "knowledge_nodes_created": 0,
            "relationships_formed": 0,
            "similarity_searches": 0,
            "knowledge_retrievals": 0,
            "last_cleanup": datetime.now(timezone.utc),
        }

        logger.info("🧠💾 MemoryIntegratedLearningSystem initialized")

    async def initialize(self):
        """Initialize the memory-integrated learning system"""
        # Load existing knowledge graph from memory store
        await self._load_knowledge_graph()

        # Load vector index
        await self._load_vector_index()

        logger.info(
            f"📊 Loaded {len(self.knowledge_graph)} knowledge nodes and {len(self.vector_index)} vectors"
        )

    # =============================================================================
    # VECTOR SIMILARITY OPERATIONS
    # =============================================================================

    async def create_learning_vector(
        self,
        content: Union[str, LearningExperience, LearnedKnowledge],
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryVector:
        """Create vector embedding for learning content"""
        with tracer.start_span("create_learning_vector", kind=SpanKind.INTERNAL) as span:
            # Generate content hash and embedding
            if isinstance(content, str):
                content_text = content
                content_hash = str(hash(content))
            elif isinstance(content, LearningExperience):
                content_text = (
                    f"{content.problem_type} {content.solution} {content.problem_context}"
                )
                content_hash = content.id
            elif isinstance(content, LearnedKnowledge):
                content_text = (
                    f"{content.knowledge_type.value} {content.pattern} {content.conditions}"
                )
                content_hash = content.id
            else:
                content_text = str(content)
                content_hash = str(hash(content_text))

            # Generate embedding (simplified - in production would use proper embeddings)
            embedding = self._generate_embedding(content_text)

            # Create vector
            vector = MemoryVector(
                vector_id=f"vec_{uuid4().hex[:8]}",
                content_hash=content_hash,
                embedding=embedding,
                metadata=metadata or {},
            )

            # Store in index
            self.vector_index[vector.vector_id] = vector
            self.memory_metrics["vectors_created"] += 1

            # Persist to memory store
            await self.memory_store.store_memory(
                content=f"Learning vector: {content_text[:100]}...",
                metadata={
                    "type": "learning_vector",
                    "vector_id": vector.vector_id,
                    "content_hash": content_hash,
                    "embedding_dimension": len(embedding),
                    "metadata": metadata or {},
                },
            )

            span.set_attribute("vector.id", vector.vector_id)
            span.set_attribute("embedding.dimension", len(embedding))

            logger.debug(f"📍 Created learning vector {vector.vector_id}")
            return vector

    async def find_similar_learning_vectors(
        self, query_vector: MemoryVector, limit: int = 10, similarity_threshold: float = 0.5
    ) -> list[tuple[MemoryVector, float]]:
        """Find similar learning vectors using cosine similarity"""
        with tracer.start_span("find_similar_vectors", kind=SpanKind.INTERNAL) as span:
            similarities = []

            for vector in self.vector_index.values():
                if vector.vector_id == query_vector.vector_id:
                    continue

                similarity_score = query_vector.similarity(vector)
                if similarity_score >= similarity_threshold:
                    similarities.append((vector, similarity_score))

            # Sort by similarity score
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Limit results
            results = similarities[:limit]

            self.memory_metrics["similarity_searches"] += 1
            span.set_attribute("results.count", len(results))
            span.set_attribute("similarity.threshold", similarity_threshold)

            logger.debug(
                f"🔍 Found {len(results)} similar vectors (threshold: {similarity_threshold})"
            )
            return results

    async def semantic_search(
        self, query_text: str, content_types: Optional[list[str]] = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Perform semantic search across learning content"""
        # Create query vector
        query_embedding = self._generate_embedding(query_text)
        query_vector = MemoryVector(
            vector_id="query_temp", content_hash="query", embedding=query_embedding
        )

        # Find similar vectors
        similar_vectors = await self.find_similar_learning_vectors(
            query_vector, limit=limit * 2, similarity_threshold=0.3
        )

        # Filter by content types if specified
        if content_types:
            filtered_vectors = [
                (vec, score)
                for vec, score in similar_vectors
                if vec.metadata.get("content_type") in content_types
            ]
        else:
            filtered_vectors = similar_vectors

        # Retrieve full content from memory store
        results = []
        for vector, similarity_score in filtered_vectors[:limit]:
            try:
                content_results = await self.memory_store.search_memory(
                    query="", filters={"content_hash": vector.content_hash}
                )

                if content_results:
                    result = content_results[0]
                    result["similarity_score"] = similarity_score
                    result["vector_id"] = vector.vector_id
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to retrieve content for vector {vector.vector_id}: {e}")

        logger.debug(f"🔎 Semantic search for '{query_text}' returned {len(results)} results")
        return results

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text (simplified implementation)"""
        # In production, this would use a proper embedding model like sentence-transformers
        # For now, using a simple hash-based approach for demonstration

        # Create features based on text characteristics
        features = []

        # Text length feature
        features.append(min(len(text) / 1000.0, 1.0))

        # Word count feature
        word_count = len(text.split())
        features.append(min(word_count / 100.0, 1.0))

        # Keyword presence features
        keywords = [
            "success",
            "failure",
            "quality",
            "performance",
            "agent",
            "swarm",
            "parallel",
            "sequential",
            "debate",
            "consensus",
            "hierarchical",
            "learning",
            "knowledge",
            "pattern",
            "strategy",
            "optimization",
        ]

        for keyword in keywords:
            features.append(1.0 if keyword.lower() in text.lower() else 0.0)

        # Hash-based features for uniqueness
        text_hash = hash(text.lower())
        for i in range(self.vector_dimension - len(features)):
            # Use different bit positions of hash for features
            bit_pos = i % 64
            features.append(1.0 if (text_hash >> bit_pos) & 1 else 0.0)

        # Normalize to unit vector
        embedding = np.array(features[: self.vector_dimension], dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    # =============================================================================
    # TEMPORAL KNOWLEDGE GRAPH OPERATIONS
    # =============================================================================

    async def create_knowledge_node(
        self, knowledge: LearnedKnowledge, parent_nodes: Optional[list[str]] = None
    ) -> KnowledgeNode:
        """Create a node in the temporal knowledge graph"""
        with tracer.start_span("create_knowledge_node", kind=SpanKind.INTERNAL) as span:
            node = KnowledgeNode(
                node_id=f"node_{uuid4().hex[:8]}",
                knowledge_id=knowledge.id,
                knowledge_type=knowledge.knowledge_type,
                content={
                    "pattern": knowledge.pattern,
                    "conditions": knowledge.conditions,
                    "expected_outcome": knowledge.expected_outcome,
                    "confidence": knowledge.confidence,
                },
                parent_nodes=parent_nodes or [],
            )

            # Add to knowledge graph
            self.knowledge_graph[node.node_id] = node
            self.memory_metrics["knowledge_nodes_created"] += 1

            # Update parent-child relationships
            for parent_id in node.parent_nodes:
                if parent_id in self.knowledge_graph:
                    self.knowledge_graph[parent_id].child_nodes.append(node.node_id)

            # Persist to memory store
            await self.memory_store.store_memory(
                content=f"Knowledge node: {knowledge.knowledge_type.value}",
                metadata={
                    "type": "knowledge_node",
                    "node_id": node.node_id,
                    "knowledge_id": knowledge.id,
                    "knowledge_type": knowledge.knowledge_type.value,
                    "parent_nodes": node.parent_nodes,
                },
            )

            span.set_attribute("node.id", node.node_id)
            span.set_attribute("knowledge.type", knowledge.knowledge_type.value)

            logger.debug(f"🧩 Created knowledge node {node.node_id}")
            return node

    async def create_temporal_relationship(
        self,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        strength: float = 0.5,
        supporting_experience: Optional[str] = None,
    ) -> TemporalRelationship:
        """Create temporal relationship between knowledge nodes"""
        with tracer.start_span("create_temporal_relationship", kind=SpanKind.INTERNAL) as span:
            relationship = TemporalRelationship(
                relationship_id=f"rel_{uuid4().hex[:8]}",
                source_node=source_node_id,
                target_node=target_node_id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=0.7,  # Initial confidence
                supporting_experiences=[supporting_experience] if supporting_experience else [],
            )

            # Add to relationships
            self.temporal_relationships[relationship.relationship_id] = relationship
            self.memory_metrics["relationships_formed"] += 1

            # Update node relationships
            if source_node_id in self.knowledge_graph:
                self.knowledge_graph[source_node_id].related_nodes.append(target_node_id)
            if target_node_id in self.knowledge_graph:
                self.knowledge_graph[target_node_id].related_nodes.append(source_node_id)

            # Persist to memory store
            await self.memory_store.store_memory(
                content=f"Temporal relationship: {relationship_type}",
                metadata={
                    "type": "temporal_relationship",
                    "relationship_id": relationship.relationship_id,
                    "source_node": source_node_id,
                    "target_node": target_node_id,
                    "relationship_type": relationship_type,
                    "strength": strength,
                },
            )

            span.set_attribute("relationship.id", relationship.relationship_id)
            span.set_attribute("relationship.type", relationship_type)
            span.set_attribute("relationship.strength", strength)

            logger.debug(f"🔗 Created temporal relationship {relationship.relationship_id}")
            return relationship

    async def find_knowledge_paths(
        self, source_node_id: str, target_node_id: str, max_depth: int = 3
    ) -> list[list[str]]:
        """Find paths between knowledge nodes in the temporal graph"""
        paths = []

        def dfs_paths(current_node: str, target: str, path: list[str], depth: int):
            if depth > max_depth:
                return

            if current_node == target and len(path) > 1:
                paths.append(path.copy())
                return

            if current_node in self.knowledge_graph:
                node = self.knowledge_graph[current_node]
                for related_node in node.related_nodes + node.child_nodes:
                    if related_node not in path:
                        path.append(related_node)
                        dfs_paths(related_node, target, path, depth + 1)
                        path.pop()

        dfs_paths(source_node_id, target_node_id, [source_node_id], 0)

        logger.debug(f"🛤️ Found {len(paths)} paths from {source_node_id} to {target_node_id}")
        return paths

    async def get_related_knowledge(
        self, node_id: str, relationship_types: Optional[list[str]] = None, max_depth: int = 2
    ) -> list[KnowledgeNode]:
        """Get related knowledge nodes within specified depth"""
        if node_id not in self.knowledge_graph:
            return []

        related_nodes = []
        visited = set()

        def collect_related(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)

            if current_id in self.knowledge_graph:
                node = self.knowledge_graph[current_id]

                # Add this node if it's not the starting node
                if current_id != node_id:
                    related_nodes.append(node)

                # Explore relationships
                for _rel_id, relationship in self.temporal_relationships.items():
                    include_relationship = True

                    if relationship_types:
                        include_relationship = relationship.relationship_type in relationship_types

                    if include_relationship:
                        if relationship.source_node == current_id:
                            collect_related(relationship.target_node, depth + 1)
                        elif relationship.target_node == current_id:
                            collect_related(relationship.source_node, depth + 1)

        collect_related(node_id, 0)

        logger.debug(f"🔍 Found {len(related_nodes)} related knowledge nodes for {node_id}")
        return related_nodes

    # =============================================================================
    # WORKING MEMORY OPERATIONS
    # =============================================================================

    async def add_to_working_memory(self, content: dict[str, Any], importance: float = 0.5):
        """Add content to working memory with importance weighting"""
        # Create working memory entry
        entry = {
            "id": f"wm_{uuid4().hex[:8]}",
            "content": content,
            "importance": importance,
            "added_at": datetime.now(timezone.utc),
            "access_count": 0,
            "last_accessed": datetime.now(timezone.utc),
        }

        # Add to working memory
        self.working_memory.append(entry)

        # Create vector for similarity search
        content_text = json.dumps(content, default=str)
        vector = await self.create_learning_vector(
            content_text, metadata={"type": "working_memory", "entry_id": entry["id"]}
        )
        self.working_memory_vectors.append(vector)

        # Maintain size limit
        if len(self.working_memory) > self.max_working_memory_size:
            # Remove least important and least recently accessed items
            self.working_memory.sort(
                key=lambda x: (x["importance"] + x["access_count"] * 0.1, x["last_accessed"])
            )

            # Remove oldest entries
            removed_count = len(self.working_memory) - self.max_working_memory_size
            for _ in range(removed_count):
                removed_entry = self.working_memory.pop(0)

                # Remove corresponding vector
                self.working_memory_vectors = [
                    v
                    for v in self.working_memory_vectors
                    if v.metadata.get("entry_id") != removed_entry["id"]
                ]

        logger.debug(f"📝 Added to working memory: {entry['id']} (importance: {importance})")

    async def search_working_memory(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search working memory using semantic similarity"""
        if not self.working_memory_vectors:
            return []

        # Create query vector
        query_embedding = self._generate_embedding(query)
        query_vector = MemoryVector(
            vector_id="query_temp", content_hash="query", embedding=query_embedding
        )

        # Find similar working memory vectors
        similarities = []
        for vector in self.working_memory_vectors:
            similarity_score = query_vector.similarity(vector)
            similarities.append((vector, similarity_score))

        # Sort and limit results
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Retrieve corresponding working memory entries
        results = []
        for vector, score in similarities[:limit]:
            entry_id = vector.metadata.get("entry_id")

            for entry in self.working_memory:
                if entry["id"] == entry_id:
                    entry_copy = entry.copy()
                    entry_copy["similarity_score"] = score

                    # Update access statistics
                    entry["access_count"] += 1
                    entry["last_accessed"] = datetime.now(timezone.utc)

                    results.append(entry_copy)
                    break

        logger.debug(f"💭 Working memory search for '{query}' returned {len(results)} results")
        return results

    # =============================================================================
    # EPISODIC MEMORY OPERATIONS
    # =============================================================================

    async def store_learning_episode(
        self, experience: LearningExperience, context: dict[str, Any], outcome: dict[str, Any]
    ) -> str:
        """Store a complete learning episode for later replay"""
        episode = {
            "episode_id": f"episode_{uuid4().hex[:8]}",
            "experience_id": experience.id,
            "timestamp": experience.timestamp,
            "context": context,
            "outcome": outcome,
            "success": experience.success,
            "quality_score": experience.quality_score,
            "execution_mode": experience.execution_mode.value,
            "problem_type": experience.problem_type,
        }

        # Create vector for episode
        episode_text = f"{experience.problem_type} {context} {outcome}"
        await self.create_learning_vector(
            episode_text,
            metadata={
                "type": "learning_episode",
                "episode_id": episode["episode_id"],
                "success": experience.success,
                "quality_score": experience.quality_score,
            },
        )

        # Store in memory
        await self.memory_store.store_memory(
            content=f"Learning episode: {experience.problem_type}",
            metadata={"type": "learning_episode", **episode},
        )

        logger.debug(f"📚 Stored learning episode {episode['episode_id']}")
        return episode["episode_id"]

    async def replay_similar_episodes(
        self, current_context: dict[str, Any], limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find and replay similar learning episodes"""
        # Search for similar episodes
        context_text = json.dumps(current_context, default=str)
        similar_episodes = await self.semantic_search(
            context_text, content_types=["learning_episode"], limit=limit
        )

        # Filter for successful episodes with high quality
        quality_episodes = [
            episode
            for episode in similar_episodes
            if episode["metadata"].get("success", False)
            and episode["metadata"].get("quality_score", 0.0) > 0.6
        ]

        logger.debug(f"🔄 Found {len(quality_episodes)} quality episodes for replay")
        return quality_episodes

    # =============================================================================
    # PERSISTENCE AND LOADING
    # =============================================================================

    async def _load_knowledge_graph(self):
        """Load knowledge graph from memory store"""
        try:
            # Load knowledge nodes
            node_results = await self.memory_store.search_memory(
                query="", filters={"type": "knowledge_node"}
            )

            for result in node_results:
                metadata = result.get("metadata", {})
                node_id = metadata.get("node_id")

                if node_id:
                    # Reconstruct knowledge node (simplified)
                    node = KnowledgeNode(
                        node_id=node_id,
                        knowledge_id=metadata.get("knowledge_id", ""),
                        knowledge_type=KnowledgeType(
                            metadata.get("knowledge_type", "execution_pattern")
                        ),
                        content={},
                        parent_nodes=metadata.get("parent_nodes", []),
                    )
                    self.knowledge_graph[node_id] = node

            # Load temporal relationships
            rel_results = await self.memory_store.search_memory(
                query="", filters={"type": "temporal_relationship"}
            )

            for result in rel_results:
                metadata = result.get("metadata", {})
                rel_id = metadata.get("relationship_id")

                if rel_id:
                    # Reconstruct temporal relationship (simplified)
                    relationship = TemporalRelationship(
                        relationship_id=rel_id,
                        source_node=metadata.get("source_node", ""),
                        target_node=metadata.get("target_node", ""),
                        relationship_type=metadata.get("relationship_type", "relates"),
                        strength=metadata.get("strength", 0.5),
                    )
                    self.temporal_relationships[rel_id] = relationship

            logger.info(
                f"📊 Loaded {len(self.knowledge_graph)} knowledge nodes and {len(self.temporal_relationships)} relationships"
            )

        except Exception as e:
            logger.warning(f"Failed to load knowledge graph: {e}")

    async def _load_vector_index(self):
        """Load vector index from memory store"""
        try:
            vector_results = await self.memory_store.search_memory(
                query="", filters={"type": "learning_vector"}
            )

            for result in vector_results:
                metadata = result.get("metadata", {})
                vector_id = metadata.get("vector_id")

                if vector_id:
                    # Note: In full implementation, would need to store/load actual embeddings
                    # For now, creating placeholder vectors
                    vector = MemoryVector(
                        vector_id=vector_id,
                        content_hash=metadata.get("content_hash", ""),
                        embedding=np.random.rand(self.vector_dimension).astype(np.float32),
                        metadata=metadata.get("metadata", {}),
                    )
                    self.vector_index[vector_id] = vector

            logger.info(f"📍 Loaded {len(self.vector_index)} learning vectors")

        except Exception as e:
            logger.warning(f"Failed to load vector index: {e}")

    # =============================================================================
    # MAINTENANCE AND OPTIMIZATION
    # =============================================================================

    async def cleanup_expired_knowledge(self, retention_days: int = 30):
        """Clean up expired knowledge nodes and relationships"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Find expired nodes
        expired_nodes = [
            node_id
            for node_id, node in self.knowledge_graph.items()
            if node.last_accessed < cutoff_date and node.access_count < 5
        ]

        # Remove expired nodes
        for node_id in expired_nodes:
            del self.knowledge_graph[node_id]

            # Remove related relationships
            expired_relationships = [
                rel_id
                for rel_id, rel in self.temporal_relationships.items()
                if rel.source_node == node_id or rel.target_node == node_id
            ]

            for rel_id in expired_relationships:
                del self.temporal_relationships[rel_id]

        self.memory_metrics["last_cleanup"] = datetime.now(timezone.utc)

        logger.info(f"🧹 Cleaned up {len(expired_nodes)} expired knowledge nodes")

    async def optimize_knowledge_graph(self):
        """Optimize knowledge graph structure and relationships"""
        # Strengthen frequently used relationships
        for relationship in self.temporal_relationships.values():
            if len(relationship.supporting_experiences) > 3:
                relationship.strength = min(relationship.strength + 0.1, 1.0)
                relationship.confidence = min(relationship.confidence + 0.05, 1.0)

        # Update node effectiveness scores
        for node in self.knowledge_graph.values():
            if node.total_applications > 0:
                node.effectiveness_score = node.success_applications / node.total_applications
            else:
                node.effectiveness_score = 0.5  # Neutral for unused nodes

        logger.info("🔧 Optimized knowledge graph structure")

    async def get_memory_insights(self) -> dict[str, Any]:
        """Get insights about memory system performance"""
        # Calculate knowledge graph metrics
        avg_node_effectiveness = (
            np.mean([node.effectiveness_score for node in self.knowledge_graph.values()])
            if self.knowledge_graph
            else 0.0
        )

        # Calculate relationship strength distribution
        relationship_strengths = [rel.strength for rel in self.temporal_relationships.values()]
        avg_relationship_strength = (
            np.mean(relationship_strengths) if relationship_strengths else 0.0
        )

        # Working memory utilization
        working_memory_utilization = len(self.working_memory) / self.max_working_memory_size

        return {
            "memory_metrics": self.memory_metrics,
            "knowledge_graph_size": len(self.knowledge_graph),
            "temporal_relationships_count": len(self.temporal_relationships),
            "vector_index_size": len(self.vector_index),
            "working_memory_utilization": working_memory_utilization,
            "avg_node_effectiveness": avg_node_effectiveness,
            "avg_relationship_strength": avg_relationship_strength,
            "working_memory_entries": len(self.working_memory),
        }

    async def cleanup(self):
        """Clean up memory-integrated learning system"""
        # Perform final optimization
        await self.optimize_knowledge_graph()

        # Save final insights
        insights = await self.get_memory_insights()
        await self.memory_store.store_memory(
            content="Memory-integrated learning system final state",
            metadata={"type": "memory_learning_final_state", "insights": insights},
        )

        logger.info("🧹💾 Memory-integrated learning system cleaned up")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


async def create_memory_integrated_learning(
    memory_store: UnifiedMemoryStore, config: Optional[dict[str, Any]] = None
) -> MemoryIntegratedLearningSystem:
    """Create and initialize a memory-integrated learning system"""
    system = MemoryIntegratedLearningSystem(
        memory_store=memory_store,
        vector_dimension=config.get("vector_dimension", 128) if config else 128,
        max_working_memory_size=config.get("max_working_memory_size", 1000) if config else 1000,
        knowledge_graph_max_nodes=config.get("knowledge_graph_max_nodes", 10000)
        if config
        else 10000,
    )

    await system.initialize()

    # Store creation event
    await memory_store.store_memory(
        content="Memory-integrated learning system created",
        metadata={"type": "memory_learning_creation", "config": config or {}},
    )

    return system


if __name__ == "__main__":
    # Example usage demonstration
    async def demo():
        from app.memory.unified_memory import get_memory_store
        from app.swarms.core.swarm_base import SwarmExecutionMode
        from app.swarms.learning.adaptive_learning_system import LearningExperience

        # Initialize components
        memory_store = get_memory_store()

        # Create memory-integrated learning system
        learning_system = await create_memory_integrated_learning(
            memory_store, config={"vector_dimension": 64, "max_working_memory_size": 100}
        )

        print("🧠💾 Memory-integrated learning system initialized")

        # Create sample learning experience
        experience = LearningExperience(
            swarm_id="demo-swarm",
            execution_mode=SwarmExecutionMode.PARALLEL,
            problem_type="coding",
            success=True,
            quality_score=0.85,
        )

        # Store learning episode
        episode_id = await learning_system.store_learning_episode(
            experience,
            context={"complexity": "medium", "agents": 5},
            outcome={"solution_quality": 0.85, "time_taken": 30.5},
        )

        print(f"📚 Stored learning episode: {episode_id}")

        # Add to working memory
        await learning_system.add_to_working_memory(
            {
                "current_task": "coding optimization",
                "progress": 0.7,
                "insights": "parallel execution works well for this problem type",
            },
            importance=0.8,
        )

        # Search working memory
        wm_results = await learning_system.search_working_memory("optimization insights", limit=3)
        print(f"💭 Working memory search results: {len(wm_results)}")

        # Perform semantic search
        search_results = await learning_system.semantic_search(
            "parallel execution coding problems", limit=5
        )
        print(f"🔎 Semantic search results: {len(search_results)}")

        # Get insights
        insights = await learning_system.get_memory_insights()
        print(f"📊 Memory insights: {insights}")

        # Cleanup
        await learning_system.cleanup()

        print("✅ Demo completed")

    asyncio.run(demo())
