"""
Knowledge Store - Structured knowledge and facts memory
Stores factual information, entities, relationships, and structured knowledge
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.unified_memory import (
    MemoryContext,
    MemoryEntry,
    MemoryMetadata,
    MemoryPriority,
    unified_memory,
)

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge stored"""

    ENTITY = "entity"  # People, organizations, products
    RELATIONSHIP = "relationship"  # Connections between entities
    FACT = "fact"  # Verified facts and data points
    CONCEPT = "concept"  # Abstract concepts and definitions
    PROCEDURE = "procedure"  # Step-by-step procedures
    RULE = "rule"  # Business rules and policies
    DOMAIN_KNOWLEDGE = "domain_knowledge"  # Specialized domain expertise
    REFERENCE = "reference"  # Reference materials and docs


class VerificationStatus(Enum):
    """Knowledge verification status"""

    VERIFIED = "verified"  # Confirmed accurate
    UNVERIFIED = "unverified"  # Not yet verified
    DISPUTED = "disputed"  # Conflicting information exists
    OUTDATED = "outdated"  # No longer current
    SUSPICIOUS = "suspicious"  # Questionable accuracy


@dataclass
class EntityRelationship:
    """Relationship between knowledge entities"""

    relationship_type: str  # "is_a", "part_of", "works_for", etc.
    source_entity: str
    target_entity: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEntity:
    """Structured knowledge entity"""

    entity_id: str
    name: str
    entity_type: str  # "person", "company", "product", etc.
    description: str

    # Attributes and properties
    properties: Dict[str, Any] = field(default_factory=dict)
    aliases: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)

    # Relationships
    relationships: List[EntityRelationship] = field(default_factory=list)

    # Verification and quality
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence_score: float = 1.0
    sources: List[str] = field(default_factory=list)

    # Temporal aspects
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    domains: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)


@dataclass
class FactualKnowledge:
    """Factual knowledge entry"""

    fact_id: str
    statement: str  # The factual statement
    knowledge_type: KnowledgeType

    # Evidence and verification
    evidence: List[str] = field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence_score: float = 1.0

    # Context and scope
    subject_entities: Set[str] = field(default_factory=set)
    applicable_domains: Set[str] = field(default_factory=set)
    temporal_scope: Optional[str] = None  # "current", "historical", "future"

    # Sources and attribution
    sources: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    verified_by: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Set[str] = field(default_factory=set)


class KnowledgeStore:
    """
    Specialized memory store for structured knowledge and facts
    Optimized for entity relationships, fact verification, and knowledge graphs
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.namespace = "knowledge"

    async def store_entity(self, entity: KnowledgeEntity, domain: Optional[str] = None) -> str:
        """Store a knowledge entity"""

        # Create comprehensive content for storage
        content = self._format_entity_content(entity)

        # Create metadata with entity-specific attributes
        metadata = MemoryMetadata(
            memory_id=entity.entity_id,
            context=MemoryContext.KNOWLEDGE,
            priority=self._determine_entity_priority(entity),
            tags=entity.tags.union(
                {
                    KnowledgeType.ENTITY.value,
                    entity.entity_type,
                    entity.verification_status.value,
                    f"confidence_{self._categorize_confidence(entity.confidence_score)}",
                }.union(entity.categories)
            ),
            domain=domain,
            source="knowledge_store",
            confidence_score=entity.confidence_score,
        )

        # Store in unified memory
        memory_id = await self.memory_interface.store(content, metadata)

        # Store structured entity data
        await self._store_structured_entity(memory_id, entity)

        # Index entity relationships
        await self._index_entity_relationships(entity)

        logger.debug(f"Stored knowledge entity: {entity.name} ({memory_id})")
        return memory_id

    async def store_fact(self, fact: FactualKnowledge, domain: Optional[str] = None) -> str:
        """Store factual knowledge"""

        # Create comprehensive content for storage
        content = self._format_fact_content(fact)

        # Create metadata with fact-specific attributes
        metadata = MemoryMetadata(
            memory_id=fact.fact_id,
            context=MemoryContext.KNOWLEDGE,
            priority=self._determine_fact_priority(fact),
            tags=fact.tags.union(
                {
                    fact.knowledge_type.value,
                    fact.verification_status.value,
                    f"confidence_{self._categorize_confidence(fact.confidence_score)}",
                    fact.temporal_scope or "current",
                }.union(fact.applicable_domains)
            ),
            domain=domain,
            source="knowledge_store",
            confidence_score=fact.confidence_score,
        )

        # Store in unified memory
        memory_id = await self.memory_interface.store(content, metadata)

        # Store structured fact data
        await self._store_structured_fact(memory_id, fact)

        logger.debug(f"Stored factual knowledge: {fact.statement[:50]}... ({memory_id})")
        return memory_id

    async def search_entities(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        verification_status: Optional[List[VerificationStatus]] = None,
        min_confidence: float = 0.0,
        max_results: int = 15,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search knowledge entities"""

        # Build search tags
        search_tags = {KnowledgeType.ENTITY.value}
        if entity_types:
            search_tags.update(entity_types)
        if verification_status:
            search_tags.update([vs.value for vs in verification_status])

        # Search unified memory
        from app.core.unified_memory import MemoryContext, MemorySearchRequest

        search_request = MemorySearchRequest(
            query=query,
            context_filter=[MemoryContext.KNOWLEDGE],
            tag_filter=search_tags,
            domain_filter=domain,
            max_results=max_results,
            similarity_threshold=min_confidence,
        )

        results = await self.memory_interface.search(search_request)

        # Enhance results with structured data
        enhanced_results = []
        for result in results:
            structured_data = await self._retrieve_structured_entity(result.memory_id)
            if structured_data:
                enhanced_results.append(
                    {
                        "memory_id": result.memory_id,
                        "content": result.content,
                        "metadata": result.metadata,
                        "relevance_score": result.relevance_score,
                        "entity_data": structured_data,
                    }
                )

        return enhanced_results

    async def search_facts(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        verification_status: Optional[List[VerificationStatus]] = None,
        subject_entities: Optional[Set[str]] = None,
        min_confidence: float = 0.0,
        max_results: int = 20,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search factual knowledge"""

        # Build search tags
        search_tags = set()
        if knowledge_types:
            search_tags.update([kt.value for kt in knowledge_types])
        if verification_status:
            search_tags.update([vs.value for vs in verification_status])

        # Search unified memory
        from app.core.unified_memory import MemoryContext, MemorySearchRequest

        search_request = MemorySearchRequest(
            query=query,
            context_filter=[MemoryContext.KNOWLEDGE],
            tag_filter=search_tags if search_tags else None,
            domain_filter=domain,
            max_results=max_results,
            similarity_threshold=min_confidence,
        )

        results = await self.memory_interface.search(search_request)

        # Enhance results with structured data and apply entity filter
        enhanced_results = []
        for result in results:
            structured_data = await self._retrieve_structured_fact(result.memory_id)
            if structured_data:
                # Apply subject entity filter
                if subject_entities:
                    fact_entities = set(structured_data.get("subject_entities", []))
                    if not subject_entities.intersection(fact_entities):
                        continue

                enhanced_results.append(
                    {
                        "memory_id": result.memory_id,
                        "content": result.content,
                        "metadata": result.metadata,
                        "relevance_score": result.relevance_score,
                        "fact_data": structured_data,
                    }
                )

        return enhanced_results

    async def get_entity_relationships(
        self, entity_id: str, relationship_types: Optional[List[str]] = None, max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get entity relationships as a graph"""

        entity_data = await self._retrieve_structured_entity(entity_id)
        if not entity_data:
            return {"error": "Entity not found"}

        # Build relationship graph
        graph = {
            "root_entity": {
                "entity_id": entity_id,
                "name": entity_data.get("name"),
                "entity_type": entity_data.get("entity_type"),
            },
            "relationships": [],
            "connected_entities": {},
            "max_depth": max_depth,
        }

        # Get direct relationships
        relationships = entity_data.get("relationships", [])
        for rel in relationships:
            if not relationship_types or rel.get("relationship_type") in relationship_types:
                graph["relationships"].append(rel)

                # Add connected entity info if we have it
                target_id = rel.get("target_entity")
                if target_id and target_id not in graph["connected_entities"]:
                    target_data = await self._retrieve_structured_entity(target_id)
                    if target_data:
                        graph["connected_entities"][target_id] = {
                            "name": target_data.get("name"),
                            "entity_type": target_data.get("entity_type"),
                        }

        return graph

    async def get_knowledge_summary(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of knowledge store contents"""

        # This would be implemented with more efficient aggregation queries
        summary = {
            "total_entities": 0,
            "total_facts": 0,
            "by_entity_type": {},
            "by_knowledge_type": {},
            "by_verification_status": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "domain": domain,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return summary

    async def verify_fact(
        self,
        fact_id: str,
        verification_status: VerificationStatus,
        verified_by: Optional[str] = None,
        verification_notes: Optional[str] = None,
    ) -> bool:
        """Update fact verification status"""

        structured_data = await self._retrieve_structured_fact(fact_id)
        if not structured_data:
            return False

        # Update verification info
        structured_data["verification_status"] = verification_status.value
        structured_data["verified_by"] = verified_by
        structured_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        if verification_notes:
            if "verification_notes" not in structured_data:
                structured_data["verification_notes"] = []
            structured_data["verification_notes"].append(
                {
                    "note": verification_notes,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "verified_by": verified_by,
                }
            )

        # Store updated data
        await self._store_structured_fact(fact_id, None, structured_data)

        logger.info(f"Updated fact verification: {fact_id} -> {verification_status.value}")
        return True

    # Private helper methods

    def _format_entity_content(self, entity: KnowledgeEntity) -> str:
        """Format entity into comprehensive text content"""

        content_parts = [
            f"KNOWLEDGE ENTITY: {entity.name}",
            f"ID: {entity.entity_id}",
            f"TYPE: {entity.entity_type}",
            f"VERIFICATION: {entity.verification_status.value}",
            f"CONFIDENCE: {entity.confidence_score:.2f}",
            "",
            "DESCRIPTION:",
            entity.description,
            "",
        ]

        if entity.properties:
            content_parts.extend(
                ["PROPERTIES:", *[f"• {k}: {v}" for k, v in entity.properties.items()], ""]
            )

        if entity.aliases:
            content_parts.extend([f"ALIASES: {', '.join(entity.aliases)}", ""])

        if entity.relationships:
            content_parts.extend(
                [
                    "RELATIONSHIPS:",
                    *[
                        f"• {rel.relationship_type}: {rel.target_entity}"
                        for rel in entity.relationships
                    ],
                    "",
                ]
            )

        if entity.sources:
            content_parts.extend(["SOURCES:", *[f"• {source}" for source in entity.sources], ""])

        return "\n".join(content_parts)

    def _format_fact_content(self, fact: FactualKnowledge) -> str:
        """Format fact into comprehensive text content"""

        content_parts = [
            f"FACTUAL KNOWLEDGE: {fact.knowledge_type.value}",
            f"ID: {fact.fact_id}",
            f"VERIFICATION: {fact.verification_status.value}",
            f"CONFIDENCE: {fact.confidence_score:.2f}",
            "",
            "STATEMENT:",
            fact.statement,
            "",
        ]

        if fact.subject_entities:
            content_parts.extend([f"SUBJECT ENTITIES: {', '.join(fact.subject_entities)}", ""])

        if fact.evidence:
            content_parts.extend(
                ["EVIDENCE:", *[f"• {evidence}" for evidence in fact.evidence], ""]
            )

        if fact.sources:
            content_parts.extend(["SOURCES:", *[f"• {source}" for source in fact.sources], ""])

        content_parts.extend(
            [f"CREATED: {fact.created_at.isoformat()}", f"UPDATED: {fact.updated_at.isoformat()}"]
        )

        return "\n".join(content_parts)

    def _determine_entity_priority(self, entity: KnowledgeEntity) -> MemoryPriority:
        """Determine memory priority for entities"""
        if (
            entity.verification_status == VerificationStatus.VERIFIED
            and entity.confidence_score >= 0.9
        ):
            return MemoryPriority.HIGH
        elif entity.confidence_score >= 0.7:
            return MemoryPriority.STANDARD
        else:
            return MemoryPriority.LOW

    def _determine_fact_priority(self, fact: FactualKnowledge) -> MemoryPriority:
        """Determine memory priority for facts"""
        if fact.verification_status == VerificationStatus.VERIFIED and fact.confidence_score >= 0.9:
            return MemoryPriority.HIGH
        elif fact.confidence_score >= 0.7:
            return MemoryPriority.STANDARD
        else:
            return MemoryPriority.LOW

    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence score for tagging"""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.3:
            return "low"
        else:
            return "very_low"

    async def _store_structured_entity(
        self,
        memory_id: str,
        entity: Optional[KnowledgeEntity],
        entity_dict: Optional[Dict[str, Any]] = None,
    ):
        """Store structured entity data"""

        if not self.memory_interface.redis_manager:
            return

        if entity:
            structured_data = {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "description": entity.description,
                "properties": entity.properties,
                "aliases": list(entity.aliases),
                "categories": list(entity.categories),
                "relationships": [
                    {
                        "relationship_type": rel.relationship_type,
                        "source_entity": rel.source_entity,
                        "target_entity": rel.target_entity,
                        "confidence": rel.confidence,
                        "metadata": rel.metadata,
                    }
                    for rel in entity.relationships
                ],
                "verification_status": entity.verification_status.value,
                "confidence_score": entity.confidence_score,
                "sources": entity.sources,
                "valid_from": entity.valid_from.isoformat() if entity.valid_from else None,
                "valid_until": entity.valid_until.isoformat() if entity.valid_until else None,
                "last_updated": entity.last_updated.isoformat(),
                "domains": list(entity.domains),
                "tags": list(entity.tags),
            }
        else:
            structured_data = entity_dict

        key = f"entity_structured:{memory_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, structured_data, ttl=86400 * 30, namespace="knowledge"  # 30 days
        )

    async def _store_structured_fact(
        self,
        memory_id: str,
        fact: Optional[FactualKnowledge],
        fact_dict: Optional[Dict[str, Any]] = None,
    ):
        """Store structured fact data"""

        if not self.memory_interface.redis_manager:
            return

        if fact:
            structured_data = {
                "fact_id": fact.fact_id,
                "statement": fact.statement,
                "knowledge_type": fact.knowledge_type.value,
                "evidence": fact.evidence,
                "verification_status": fact.verification_status.value,
                "confidence_score": fact.confidence_score,
                "subject_entities": list(fact.subject_entities),
                "applicable_domains": list(fact.applicable_domains),
                "temporal_scope": fact.temporal_scope,
                "sources": fact.sources,
                "created_by": fact.created_by,
                "verified_by": fact.verified_by,
                "created_at": fact.created_at.isoformat(),
                "updated_at": fact.updated_at.isoformat(),
                "tags": list(fact.tags),
            }
        else:
            structured_data = fact_dict

        key = f"fact_structured:{memory_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, structured_data, ttl=86400 * 30, namespace="knowledge"  # 30 days
        )

    async def _retrieve_structured_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve structured entity data"""

        if not self.memory_interface.redis_manager:
            return None

        try:
            key = f"entity_structured:{entity_id}"
            data = await self.memory_interface.redis_manager.get(key, namespace="knowledge")

            if data:
                import json

                return json.loads(data.decode() if isinstance(data, bytes) else data)

        except Exception as e:
            logger.warning(f"Failed to retrieve structured entity {entity_id}: {e}")

        return None

    async def _retrieve_structured_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve structured fact data"""

        if not self.memory_interface.redis_manager:
            return None

        try:
            key = f"fact_structured:{fact_id}"
            data = await self.memory_interface.redis_manager.get(key, namespace="knowledge")

            if data:
                import json

                return json.loads(data.decode() if isinstance(data, bytes) else data)

        except Exception as e:
            logger.warning(f"Failed to retrieve structured fact {fact_id}: {e}")

        return None

    async def _index_entity_relationships(self, entity: KnowledgeEntity):
        """Index entity relationships for graph queries"""

        if not self.memory_interface.redis_manager:
            return

        # Store bidirectional relationship index
        for rel in entity.relationships:
            # Forward relationship: source -> target
            forward_key = f"relationships:{entity.entity_id}:{rel.relationship_type}"
            await self.memory_interface.redis_manager.redis.sadd(forward_key, rel.target_entity)

            # Reverse relationship index: target <- source
            reverse_key = f"reverse_relationships:{rel.target_entity}:{rel.relationship_type}"
            await self.memory_interface.redis_manager.redis.sadd(reverse_key, entity.entity_id)


# Global knowledge store instance
knowledge_store = KnowledgeStore()
