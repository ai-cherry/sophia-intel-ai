"""
Foundational Knowledge Manager - Core service for managing Pay-Ready foundational knowledge
"""
from __future__ import annotations
import json
import os
from typing import Any
from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker
from app.knowledge.classification_engine import ClassificationEngine
from app.knowledge.models import (
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
    KnowledgeVersion,
    PayReadyContext,
    SyncConflict,
)
from app.knowledge.storage_adapter import StorageAdapter
from app.knowledge.versioning_engine import VersioningEngine
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
class FoundationalKnowledgeManager:
    """
    Manages foundational knowledge for Sophia with:
    - CRUD operations with versioning
    - Classification and tagging
    - Caching for performance
    - Pay-Ready context integration
    """
    def __init__(self):
        self.storage = StorageAdapter()
        self.versioning = VersioningEngine(self.storage)
        self.classifier = ClassificationEngine()
        self.cache = self._init_cache()
        self.pay_ready_context = self._init_pay_ready_context()
        logger.info("FoundationalKnowledgeManager initialized")
    def _init_cache(self):
        """Initialize Redis cache if available"""
        if REDIS_AVAILABLE:
            try:
                cache = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=int(os.getenv("REDIS_DB", "0")),
                    decode_responses=True,
                )
                cache.ping()
                logger.info("Redis cache initialized")
                return cache
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")
                return {}
        else:
            logger.info("Using in-memory cache (Redis not installed)")
            return {}
    def _init_pay_ready_context(self) -> PayReadyContext:
        """Initialize Pay-Ready business context"""
        return PayReadyContext()
    # ========== CRUD Operations ==========
    @with_circuit_breaker("database")
    async def create(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """
        Create new foundational knowledge entry with automatic classification
        """
        # Auto-classify if not explicitly set
        if (
            not entity.classification
            or entity.classification == KnowledgeClassification.OPERATIONAL
        ):
            entity.classification = await self.classifier.classify(entity)
        # Set foundational flag based on classification
        entity.is_foundational = entity.classification in [
            KnowledgeClassification.FOUNDATIONAL,
            KnowledgeClassification.STRATEGIC,
        ]
        # Ensure foundational knowledge has appropriate priority
        if entity.is_foundational and entity.priority < KnowledgePriority.HIGH:
            entity.priority = KnowledgePriority.HIGH
        # Add Pay-Ready context if foundational
        if entity.is_foundational and not entity.pay_ready_context:
            entity.pay_ready_context = self.pay_ready_context
        # Create in storage
        created = await self.storage.create_knowledge(entity)
        # Create initial version
        await self.versioning.create_version(created)
        # Cache if foundational
        if created.is_foundational:
            await self._cache_entity(created)
        logger.info(
            f"Created foundational knowledge: {created.id} ({created.classification.value})"
        )
        return created
    @with_circuit_breaker("database")
    async def get(self, knowledge_id: str) -> KnowledgeEntity | None:
        """Get knowledge entity by ID, with cache check"""
        # Check cache first
        cached = await self._get_cached(knowledge_id)
        if cached:
            return cached
        # Get from storage
        entity = await self.storage.get_knowledge(knowledge_id)
        # Cache if foundational
        if entity and entity.is_foundational:
            await self._cache_entity(entity)
        return entity
    @with_circuit_breaker("database")
    async def update(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Update knowledge with version tracking"""
        # Get current version for comparison
        current = await self.storage.get_knowledge(entity.id)
        if not current:
            raise ValueError(f"Knowledge entity {entity.id} not found")
        # Check if content actually changed
        if current.content != entity.content:
            # Create version before update
            entity.version = current.version + 1
            await self.versioning.create_version(entity, changed_by="system")
        # Update in storage
        updated = await self.storage.update_knowledge(entity)
        # Update cache if foundational
        if updated.is_foundational:
            await self._cache_entity(updated)
        else:
            await self._invalidate_cache(updated.id)
        logger.info(f"Updated knowledge: {updated.id} (version {updated.version})")
        return updated
    @with_circuit_breaker("database")
    async def delete(self, knowledge_id: str) -> bool:
        """Delete knowledge entity"""
        # Invalidate cache
        await self._invalidate_cache(knowledge_id)
        # Delete from storage
        result = await self.storage.delete_knowledge(knowledge_id)
        logger.info(f"Deleted knowledge: {knowledge_id}")
        return result
    # ========== Search and Retrieval ==========
    async def list_foundational(self, limit: int = 100) -> list[KnowledgeEntity]:
        """List all foundational knowledge entries"""
        return await self.storage.list_knowledge(
            classification=KnowledgeClassification.FOUNDATIONAL.value,
            is_active=True,
            limit=limit,
        )
    async def search(
        self, query: str, include_operational: bool = False
    ) -> list[KnowledgeEntity]:
        """Search knowledge with optional operational data inclusion"""
        results = await self.storage.search_knowledge(query)
        if not include_operational:
            # Filter to only foundational/strategic
            results = [
                r
                for r in results
                if r.classification
                in [
                    KnowledgeClassification.FOUNDATIONAL,
                    KnowledgeClassification.STRATEGIC,
                ]
            ]
        return results
    async def get_by_category(self, category: str) -> list[KnowledgeEntity]:
        """Get all knowledge in a category"""
        return await self.storage.list_knowledge(category=category)
    async def get_pay_ready_context(self) -> dict[str, Any]:
        """
        Get comprehensive Pay-Ready context including all foundational knowledge
        """
        foundational = await self.list_foundational()
        context = {
            "company": self.pay_ready_context.company,
            "mission": self.pay_ready_context.mission,
            "metrics": self.pay_ready_context.metrics,
            "foundational_knowledge": {},
        }
        # Organize by category
        for entity in foundational:
            if entity.category not in context["foundational_knowledge"]:
                context["foundational_knowledge"][entity.category] = []
            context["foundational_knowledge"][entity.category].append(
                {
                    "name": entity.name,
                    "priority": entity.priority.value,
                    "content": entity.content,
                    "last_updated": entity.updated_at.isoformat(),
                }
            )
        return context
    # ========== Version Management ==========
    async def get_version_history(self, knowledge_id: str) -> list[KnowledgeVersion]:
        """Get version history for knowledge entity"""
        return await self.versioning.get_history(knowledge_id)
    async def rollback_to_version(
        self, knowledge_id: str, version_number: int
    ) -> KnowledgeEntity:
        """Rollback knowledge to specific version"""
        entity = await self.versioning.rollback(knowledge_id, version_number)
        # Update cache
        if entity.is_foundational:
            await self._cache_entity(entity)
        logger.info(f"Rolled back {knowledge_id} to version {version_number}")
        return entity
    async def compare_versions(
        self, knowledge_id: str, v1: int, v2: int
    ) -> dict[str, Any]:
        """Compare two versions of knowledge"""
        return await self.versioning.compare(knowledge_id, v1, v2)
    # ========== Sync Operations ==========
    async def handle_sync_conflict(
        self, conflict: SyncConflict, strategy: str = "remote_wins"
    ) -> KnowledgeEntity:
        """Handle sync conflict with specified strategy"""
        if strategy == "auto":
            # Use classification to determine strategy
            local = KnowledgeEntity(**conflict.local_version)
            remote = KnowledgeEntity(**conflict.remote_version)
            if local.is_foundational and not remote.is_foundational:
                strategy = "local_wins"  # Protect foundational knowledge
            elif remote.is_foundational and not local.is_foundational:
                strategy = "remote_wins"  # Accept foundational updates
            else:
                strategy = "merge"  # Merge when both are same type
        resolved = conflict.auto_resolve(strategy)
        await self.update(resolved)
        logger.info(f"Resolved conflict for {conflict.knowledge_id} using {strategy}")
        return resolved
    # ========== Cache Management ==========
    async def _cache_entity(self, entity: KnowledgeEntity):
        """Cache knowledge entity"""
        if isinstance(self.cache, dict):
            # In-memory cache
            self.cache[f"fk:{entity.id}"] = entity.dict()
        elif REDIS_AVAILABLE and self.cache:
            # Redis cache
            key = f"fk:{entity.id}"
            value = json.dumps(entity.dict())
            self.cache.setex(key, 3600, value)  # 1 hour TTL
    async def _get_cached(self, knowledge_id: str) -> KnowledgeEntity | None:
        """Get entity from cache"""
        if isinstance(self.cache, dict):
            # In-memory cache
            data = self.cache.get(f"fk:{knowledge_id}")
            if data:
                return KnowledgeEntity(**data)
        elif REDIS_AVAILABLE and self.cache:
            # Redis cache
            key = f"fk:{knowledge_id}"
            value = self.cache.get(key)
            if value:
                data = json.loads(value)
                return KnowledgeEntity(**data)
        return None
    async def _invalidate_cache(self, knowledge_id: str):
        """Invalidate cache entry"""
        if isinstance(self.cache, dict):
            # In-memory cache
            self.cache.pop(f"fk:{knowledge_id}", None)
        elif REDIS_AVAILABLE and self.cache:
            # Redis cache
            self.cache.delete(f"fk:{knowledge_id}")
    async def refresh_cache(self):
        """Refresh all foundational knowledge in cache"""
        foundational = await self.list_foundational()
        for entity in foundational:
            await self._cache_entity(entity)
        logger.info(f"Refreshed cache with {len(foundational)} foundational entries")
    # ========== Statistics ==========
    async def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics"""
        all_knowledge = await self.storage.list_knowledge(limit=1000)
        stats = {
            "total_entries": len(all_knowledge),
            "foundational_count": sum(1 for k in all_knowledge if k.is_foundational),
            "operational_count": sum(1 for k in all_knowledge if not k.is_foundational),
            "by_classification": {},
            "by_priority": {},
            "by_category": {},
            "cache_size": len(self.cache) if isinstance(self.cache, dict) else 0,
        }
        for entity in all_knowledge:
            # By classification
            cls = entity.classification.value
            stats["by_classification"][cls] = stats["by_classification"].get(cls, 0) + 1
            # By priority
            pri = entity.priority.value
            stats["by_priority"][pri] = stats["by_priority"].get(pri, 0) + 1
            # By category
            cat = entity.category
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        return stats
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, "storage"):
            self.storage.close()
