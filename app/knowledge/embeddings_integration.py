"""
Foundational Knowledge Embeddings Integration

Provides integration between the foundational knowledge system
and the multi-modal embedding generation system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import numpy as np

from app.embeddings.multi_modal_system import (
    EmbeddingMetadata,
    EmbeddingType,
    HierarchyLevel,
    MultiModalEmbeddings,
)
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import KnowledgeClassification, KnowledgeEntity
from app.scaffolding.meta_tagging import (
    MetaTag,
    SemanticRole,
    get_global_registry,
)

logger = logging.getLogger(__name__)


class FoundationalKnowledgeEmbeddings:
    """
    Integrates foundational knowledge with embeddings and meta-tagging.

    Features:
    - Automatic embedding generation for foundational knowledge
    - Semantic search across foundational knowledge base
    - Meta-tag integration for enhanced classification
    - Hierarchical embedding structure for complex knowledge
    """

    def __init__(
        self,
        cache_dir: str = "data/knowledge_embeddings_cache",
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-large",
    ):
        """
        Initialize the foundational knowledge embeddings integration.

        Args:
            cache_dir: Directory for caching embeddings
            embedding_provider: Embedding provider to use
            embedding_model: Specific embedding model
        """
        self.knowledge_manager = FoundationalKnowledgeManager()
        self.embeddings = MultiModalEmbeddings(
            cache_dir=cache_dir,
            default_provider=embedding_provider,
        )
        self.embedding_model = embedding_model
        self.meta_registry = get_global_registry()

        # Track embedded knowledge entities
        self._embedded_entities: dict[str, datetime] = {}

    async def embed_knowledge_entity(
        self,
        entity: KnowledgeEntity,
        force_regenerate: bool = False,
    ) -> tuple[np.ndarray, EmbeddingMetadata]:
        """
        Generate embeddings for a knowledge entity.

        Args:
            entity: Knowledge entity to embed
            force_regenerate: Force regeneration even if cached

        Returns:
            Tuple of (embedding_vector, metadata)
        """
        # Determine embedding type based on classification
        embedding_type = self._get_embedding_type(entity.classification)

        # Serialize entity content for embedding
        content = self._serialize_entity_content(entity)

        # Create metadata for the embedding
        metadata = EmbeddingMetadata(
            content_hash="",  # Will be set by embedding system
            embedding_type=embedding_type,
            hierarchy_level=HierarchyLevel.FILE if entity.is_foundational else HierarchyLevel.BLOCK,
            file_path=f"knowledge/{entity.category}/{entity.name}",
            language="json",
            extra_metadata={
                "entity_id": entity.id,
                "classification": entity.classification.value,
                "priority": entity.priority.value,
                "is_foundational": entity.is_foundational,
                "version": entity.version,
            },
        )

        # Generate embedding
        vector, metadata = await self.embeddings.generate_embedding(
            content=content,
            embedding_type=embedding_type,
            metadata=metadata,
            provider=self.embeddings.default_provider,
            model=self.embedding_model,
            use_cache=not force_regenerate,
        )

        # Track embedded entity
        self._embedded_entities[entity.id] = datetime.now()

        logger.info(f"Generated embedding for {entity.name} ({entity.classification.value})")
        return vector, metadata

    async def embed_all_foundational(
        self,
        batch_size: int = 10,
        force_regenerate: bool = False,
    ) -> dict[str, tuple[np.ndarray, EmbeddingMetadata]]:
        """
        Generate embeddings for all foundational knowledge.

        Args:
            batch_size: Batch size for processing
            force_regenerate: Force regeneration of all embeddings

        Returns:
            Dictionary mapping entity IDs to embeddings
        """
        # Get all foundational entities
        entities = await self.knowledge_manager.list_foundational()

        results = {}
        total = len(entities)

        logger.info(f"Generating embeddings for {total} foundational entities")

        # Process in batches
        for i in range(0, total, batch_size):
            batch = entities[i : i + batch_size]

            # Process batch concurrently
            batch_tasks = [
                self.embed_knowledge_entity(entity, force_regenerate) for entity in batch
            ]

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Store results
            for entity, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to embed {entity.name}: {result}")
                else:
                    results[entity.id] = result

            logger.info(f"Processed {min(i + batch_size, total)}/{total} entities")

        return results

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        classification_filter: Optional[KnowledgeClassification] = None,
        include_operational: bool = False,
    ) -> list[tuple[KnowledgeEntity, float]]:
        """
        Search foundational knowledge using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            classification_filter: Optional classification filter
            include_operational: Whether to include operational knowledge

        Returns:
            List of (entity, similarity_score) tuples
        """
        # Generate query embedding
        query_vector, _ = await self.embeddings.generate_embedding(
            content=query,
            embedding_type=EmbeddingType.SEMANTIC,
            use_cache=True,
        )

        # Get all entities to search
        if include_operational:
            entities = await self.knowledge_manager.storage.list_knowledge()
        else:
            entities = await self.knowledge_manager.list_foundational()

        # Filter by classification if specified
        if classification_filter:
            entities = [e for e in entities if e.classification == classification_filter]

        # Calculate similarities
        similarities = []
        for entity in entities:
            try:
                # Get entity embedding
                entity_vector, _ = await self.embed_knowledge_entity(entity)

                # Calculate cosine similarity
                similarity = np.dot(query_vector, entity_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(entity_vector)
                )

                similarities.append((entity, float(similarity)))

            except Exception as e:
                logger.warning(f"Failed to calculate similarity for {entity.name}: {e}")

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    async def integrate_with_meta_tags(
        self,
        entity: KnowledgeEntity,
    ) -> Optional[MetaTag]:
        """
        Integrate knowledge entity with meta-tagging system.

        Args:
            entity: Knowledge entity to integrate

        Returns:
            MetaTag if found or created
        """
        # Map knowledge classification to semantic role
        semantic_role = self._map_to_semantic_role(entity.classification)

        # Check if entity already has meta tag
        existing_tag = self.meta_registry.get_by_component(entity.name)

        if existing_tag:
            # Update existing tag with knowledge info
            existing_tag.extra_metadata["knowledge_entity_id"] = entity.id
            existing_tag.extra_metadata["is_foundational"] = entity.is_foundational
            existing_tag.extra_metadata["knowledge_classification"] = entity.classification.value

            logger.info(f"Updated meta tag for {entity.name}")
            return existing_tag

        # Create new meta tag for knowledge entity
        from app.scaffolding.meta_tagging import ModificationRisk, Priority

        meta_tag = MetaTag(
            component_name=entity.name,
            file_path=f"knowledge/{entity.category}/{entity.name}",
            line_range=(0, 0),  # Not applicable for knowledge entities
            semantic_role=semantic_role,
            complexity=self._map_to_complexity(entity),
            priority=Priority(min(entity.priority.value, 4)),  # Map to Priority enum
            modification_risk=(
                ModificationRisk.CRITICAL if entity.is_foundational else ModificationRisk.MODERATE
            ),
            capabilities=self._extract_capabilities(entity),
            dependencies=set(),
            external_integrations=self._extract_integrations(entity),
            optimization_opportunities=[],
            refactoring_suggestions=[],
            test_requirements=[],
            security_considerations=[],
            cyclomatic_complexity=0,
            lines_of_code=0,
            documentation_score=1.0 if entity.description else 0.5,
            type_safety_score=1.0,  # Knowledge entities are type-safe by design
            performance_impact="minimal",
            maintainability_score=0.9 if entity.is_foundational else 0.7,
            last_modified=entity.updated_at,
            tags={"knowledge", entity.category, entity.classification.value},
            extra_metadata={
                "knowledge_entity_id": entity.id,
                "is_foundational": entity.is_foundational,
                "knowledge_classification": entity.classification.value,
                "version": entity.version,
            },
        )

        # Add to registry
        self.meta_registry.add_tag(meta_tag)
        logger.info(f"Created meta tag for {entity.name}")

        return meta_tag

    def _get_embedding_type(self, classification: KnowledgeClassification) -> EmbeddingType:
        """Map knowledge classification to embedding type."""
        mapping = {
            KnowledgeClassification.COMPANY_INFO: EmbeddingType.DOCUMENTATION,
            KnowledgeClassification.BUSINESS_METRICS: EmbeddingType.SEMANTIC,
            KnowledgeClassification.PAYMENT_PROCESSING: EmbeddingType.SEMANTIC,
            KnowledgeClassification.INTEGRATION_CONFIG: EmbeddingType.CODE,
            KnowledgeClassification.OPERATIONAL: EmbeddingType.USAGE,
            KnowledgeClassification.SYSTEM_CONFIG: EmbeddingType.CODE,
        }
        return mapping.get(classification, EmbeddingType.SEMANTIC)

    def _serialize_entity_content(self, entity: KnowledgeEntity) -> str:
        """Serialize entity content for embedding."""
        import json

        content_parts = [
            f"Name: {entity.name}",
            f"Category: {entity.category}",
            f"Classification: {entity.classification.value}",
            f"Priority: {entity.priority.value}",
        ]

        if entity.description:
            content_parts.append(f"Description: {entity.description}")

        # Add structured content
        content_parts.append(f"Content: {json.dumps(entity.content, indent=2)}")

        # Add Pay-Ready context if available
        if entity.pay_ready_context:
            content_parts.append(f"Business Context: {entity.pay_ready_context.business_impact}")
            content_parts.append(
                f"Integration Requirements: {', '.join(entity.pay_ready_context.integration_requirements)}"
            )

        return "\n".join(content_parts)

    def _map_to_semantic_role(self, classification: KnowledgeClassification) -> SemanticRole:
        """Map knowledge classification to semantic role."""
        mapping = {
            KnowledgeClassification.COMPANY_INFO: SemanticRole.DOCUMENTATION,
            KnowledgeClassification.BUSINESS_METRICS: SemanticRole.ANALYZER,
            KnowledgeClassification.PAYMENT_PROCESSING: SemanticRole.SERVICE,
            KnowledgeClassification.INTEGRATION_CONFIG: SemanticRole.CONFIG,
            KnowledgeClassification.OPERATIONAL: SemanticRole.SERVICE,
            KnowledgeClassification.SYSTEM_CONFIG: SemanticRole.CONFIG,
        }
        return mapping.get(classification, SemanticRole.UNKNOWN)

    def _map_to_complexity(self, entity: KnowledgeEntity) -> "Complexity":
        """Map knowledge entity to complexity level."""
        from app.scaffolding.meta_tagging import Complexity

        # Foundational knowledge is generally more complex
        if entity.is_foundational:
            if entity.priority.value >= 4:
                return Complexity.CRITICAL
            else:
                return Complexity.HIGH
        else:
            if entity.priority.value >= 3:
                return Complexity.MODERATE
            else:
                return Complexity.LOW

    def _extract_capabilities(self, entity: KnowledgeEntity) -> set:
        """Extract capabilities from knowledge entity."""
        capabilities = set()

        # Add based on classification
        if entity.classification == KnowledgeClassification.PAYMENT_PROCESSING:
            capabilities.add("payment_processing")
        elif entity.classification == KnowledgeClassification.INTEGRATION_CONFIG:
            capabilities.add("external_integration")
        elif entity.classification == KnowledgeClassification.BUSINESS_METRICS:
            capabilities.add("analytics")

        # Add based on content
        if "api" in str(entity.content).lower():
            capabilities.add("api")
        if "database" in str(entity.content).lower():
            capabilities.add("database")

        return capabilities

    def _extract_integrations(self, entity: KnowledgeEntity) -> set:
        """Extract external integrations from knowledge entity."""
        integrations = set()

        # Check Pay-Ready context
        if entity.pay_ready_context:
            for req in entity.pay_ready_context.integration_requirements:
                if "API" in req or "integration" in req.lower():
                    integrations.add(req)

        # Check content for known integrations
        content_str = str(entity.content).lower()
        if "airtable" in content_str:
            integrations.add("airtable")
        if "stripe" in content_str:
            integrations.add("stripe")
        if "plaid" in content_str:
            integrations.add("plaid")

        return integrations

    async def get_statistics(self) -> dict[str, any]:
        """Get integration statistics."""
        knowledge_stats = await self.knowledge_manager.get_statistics()
        embedding_stats = self.embeddings.get_stats()

        return {
            "knowledge": knowledge_stats,
            "embeddings": embedding_stats,
            "embedded_entities": len(self._embedded_entities),
            "last_embedding_time": (
                max(self._embedded_entities.values()).isoformat()
                if self._embedded_entities
                else None
            ),
        }


# Global instance for convenience
_global_integration = None


def get_knowledge_embeddings() -> FoundationalKnowledgeEmbeddings:
    """Get or create global knowledge embeddings integration."""
    global _global_integration
    if _global_integration is None:
        _global_integration = FoundationalKnowledgeEmbeddings()
    return _global_integration
