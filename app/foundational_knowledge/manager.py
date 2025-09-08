"""
Foundational Knowledge Manager
Core service for managing CEO-curated knowledge with versioning and caching
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.foundational_knowledge.cache_manager import CacheManager
from app.foundational_knowledge.models import (
    AccessLevel,
    AccessLog,
    ChangeType,
    DataClassification,
    FoundationalKnowledge,
    KnowledgeRelationship,
    KnowledgeVersion,
    RelationshipType,
    SyncOperation,
)
from app.foundational_knowledge.versioning_engine import VersioningEngine

logger = logging.getLogger(__name__)


class FoundationalKnowledgeManager:
    """
    Central manager for foundational knowledge operations

    Handles:
    - CRUD operations with automatic versioning
    - Search and retrieval with caching
    - Access control and audit logging
    - Relationship management
    - Sync coordination
    """

    def __init__(
        self,
        db_url: str,
        cache_manager: Optional[CacheManager] = None,
        versioning_engine: Optional[VersioningEngine] = None,
        enable_audit: bool = True,
    ):
        """
        Initialize the knowledge manager

        Args:
            db_url: Database connection URL
            cache_manager: Optional cache manager instance
            versioning_engine: Optional versioning engine instance
            enable_audit: Whether to enable audit logging
        """
        self.db_url = db_url
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self.cache_manager = cache_manager or CacheManager()
        self.versioning_engine = versioning_engine or VersioningEngine()
        self.enable_audit = enable_audit

        logger.info("FoundationalKnowledgeManager initialized")

    # ==================== CRUD Operations ====================

    async def create_knowledge(
        self, knowledge: FoundationalKnowledge, created_by: str = "system"
    ) -> FoundationalKnowledge:
        """
        Create new foundational knowledge with versioning

        Args:
            knowledge: Knowledge to create
            created_by: User/system creating the knowledge

        Returns:
            Created knowledge with ID
        """
        async with self.async_session() as session:
            try:
                # Create initial version
                await self.versioning_engine.create_version(
                    knowledge=knowledge,
                    change_type=ChangeType.CREATE,
                    changed_by=created_by,
                    session=session,
                )

                # Save knowledge
                session.add(knowledge)
                await session.commit()

                # Log access
                if self.enable_audit:
                    await self._log_access(
                        knowledge_id=knowledge.id,
                        accessed_by=created_by,
                        access_type="create",
                        session=session,
                    )

                # Invalidate relevant caches
                await self.cache_manager.invalidate_pattern("knowledge:*")

                logger.info(f"Created knowledge {knowledge.id}: {knowledge.title}")
                return knowledge

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create knowledge: {e}")
                raise

    async def get_knowledge(
        self,
        knowledge_id: UUID,
        user_level: AccessLevel = AccessLevel.EMPLOYEE,
        use_cache: bool = True,
    ) -> Optional[FoundationalKnowledge]:
        """
        Get foundational knowledge by ID

        Args:
            knowledge_id: Knowledge ID
            user_level: User's access level
            use_cache: Whether to use cache

        Returns:
            Knowledge if found and accessible, None otherwise
        """
        # Check cache first
        if use_cache:
            cached = await self.cache_manager.get(f"knowledge:{knowledge_id}")
            if cached:
                knowledge = FoundationalKnowledge.parse_obj(cached)
                if knowledge.can_access(user_level):
                    return knowledge
                return None

        async with self.async_session() as session:
            result = await session.execute(
                select(FoundationalKnowledge).where(
                    and_(
                        FoundationalKnowledge.id == knowledge_id,
                        FoundationalKnowledge.is_current,
                    )
                )
            )
            knowledge = result.scalar_one_or_none()

            if knowledge and knowledge.can_access(user_level):
                # Cache the result
                if use_cache:
                    await self.cache_manager.set(
                        f"knowledge:{knowledge_id}", knowledge.dict(), ttl=3600
                    )

                # Log access
                if self.enable_audit:
                    await self._log_access(
                        knowledge_id=knowledge_id,
                        accessed_by=str(user_level),
                        access_type="read",
                        session=session,
                    )

                return knowledge

            return None

    async def update_knowledge(
        self, knowledge_id: UUID, updates: dict[str, Any], updated_by: str = "system"
    ) -> Optional[FoundationalKnowledge]:
        """
        Update foundational knowledge with versioning

        Args:
            knowledge_id: Knowledge ID to update
            updates: Dictionary of updates
            updated_by: User/system updating the knowledge

        Returns:
            Updated knowledge if successful, None otherwise
        """
        async with self.async_session() as session:
            try:
                # Get current knowledge
                result = await session.execute(
                    select(FoundationalKnowledge).where(
                        and_(
                            FoundationalKnowledge.id == knowledge_id,
                            FoundationalKnowledge.is_current,
                        )
                    )
                )
                knowledge = result.scalar_one_or_none()

                if not knowledge:
                    return None

                # Create version before updating
                await self.versioning_engine.create_version(
                    knowledge=knowledge,
                    change_type=ChangeType.UPDATE,
                    changed_by=updated_by,
                    changed_fields=list(updates.keys()),
                    session=session,
                )

                # Apply updates
                for key, value in updates.items():
                    if hasattr(knowledge, key):
                        setattr(knowledge, key, value)

                knowledge.version += 1
                knowledge.updated_at = datetime.utcnow()

                await session.commit()

                # Log access
                if self.enable_audit:
                    await self._log_access(
                        knowledge_id=knowledge_id,
                        accessed_by=updated_by,
                        access_type="update",
                        access_context=json.dumps(updates),
                        session=session,
                    )

                # Invalidate cache
                await self.cache_manager.delete(f"knowledge:{knowledge_id}")
                await self.cache_manager.invalidate_pattern("search:*")

                logger.info(f"Updated knowledge {knowledge_id} (v{knowledge.version})")
                return knowledge

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update knowledge {knowledge_id}: {e}")
                raise

    async def delete_knowledge(
        self, knowledge_id: UUID, deleted_by: str = "system", soft_delete: bool = True
    ) -> bool:
        """
        Delete foundational knowledge

        Args:
            knowledge_id: Knowledge ID to delete
            deleted_by: User/system deleting the knowledge
            soft_delete: If True, mark as not current; if False, hard delete

        Returns:
            True if successful, False otherwise
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(FoundationalKnowledge).where(
                        FoundationalKnowledge.id == knowledge_id
                    )
                )
                knowledge = result.scalar_one_or_none()

                if not knowledge:
                    return False

                if soft_delete:
                    # Create deletion version
                    await self.versioning_engine.create_version(
                        knowledge=knowledge,
                        change_type=ChangeType.DELETE,
                        changed_by=deleted_by,
                        session=session,
                    )

                    # Mark as not current
                    knowledge.is_current = False
                    knowledge.updated_at = datetime.utcnow()
                else:
                    # Hard delete
                    await session.delete(knowledge)

                await session.commit()

                # Log access
                if self.enable_audit:
                    await self._log_access(
                        knowledge_id=knowledge_id,
                        accessed_by=deleted_by,
                        access_type="delete",
                        session=session,
                    )

                # Invalidate cache
                await self.cache_manager.delete(f"knowledge:{knowledge_id}")
                await self.cache_manager.invalidate_pattern("search:*")

                logger.info(
                    f"{'Soft' if soft_delete else 'Hard'} deleted knowledge {knowledge_id}"
                )
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete knowledge {knowledge_id}: {e}")
                return False

    # ==================== Search Operations ====================

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        classification: Optional[DataClassification] = None,
        user_level: AccessLevel = AccessLevel.EMPLOYEE,
        limit: int = 20,
        offset: int = 0,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Search foundational knowledge

        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            classification: Filter by classification
            user_level: User's access level
            limit: Maximum results
            offset: Results offset
            use_cache: Whether to use cache

        Returns:
            Dictionary with results and metadata
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            "search", query, category, tags, classification, limit, offset
        )

        # Check cache
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        start_time = datetime.utcnow()

        async with self.async_session() as session:
            # Build query
            stmt = select(FoundationalKnowledge).where(FoundationalKnowledge.is_current)

            # Add filters
            filters = []

            if query:
                # Full-text search on title and content
                filters.append(
                    or_(
                        FoundationalKnowledge.title.ilike(f"%{query}%"),
                        FoundationalKnowledge.content.ilike(f"%{query}%"),
                    )
                )

            if category:
                filters.append(FoundationalKnowledge.category == category)

            if tags:
                # Check if any of the provided tags are in the knowledge tags
                for tag in tags:
                    filters.append(FoundationalKnowledge.tags.contains([tag]))

            if classification:
                filters.append(
                    FoundationalKnowledge.data_classification == classification
                )

            # Apply access control
            access_hierarchy = {
                AccessLevel.PUBLIC: [AccessLevel.PUBLIC],
                AccessLevel.EMPLOYEE: [AccessLevel.PUBLIC, AccessLevel.EMPLOYEE],
                AccessLevel.MANAGER: [
                    AccessLevel.PUBLIC,
                    AccessLevel.EMPLOYEE,
                    AccessLevel.MANAGER,
                ],
                AccessLevel.EXECUTIVE: [
                    AccessLevel.PUBLIC,
                    AccessLevel.EMPLOYEE,
                    AccessLevel.MANAGER,
                    AccessLevel.EXECUTIVE,
                ],
                AccessLevel.OWNER: [
                    AccessLevel.PUBLIC,
                    AccessLevel.EMPLOYEE,
                    AccessLevel.MANAGER,
                    AccessLevel.EXECUTIVE,
                    AccessLevel.OWNER,
                ],
            }
            allowed_levels = access_hierarchy.get(user_level, [AccessLevel.PUBLIC])
            filters.append(FoundationalKnowledge.access_level.in_(allowed_levels))

            if filters:
                stmt = stmt.where(and_(*filters))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = await session.scalar(count_stmt)

            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)

            # Execute query
            result = await session.execute(stmt)
            results = result.scalars().all()

            # Calculate search time
            took_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            response = {
                "results": [r.dict() for r in results],
                "total_count": total_count,
                "query": query,
                "filters": {
                    "category": category,
                    "tags": tags,
                    "classification": classification,
                },
                "pagination": {"limit": limit, "offset": offset},
                "took_ms": took_ms,
            }

            # Cache results
            if use_cache:
                await self.cache_manager.set(
                    cache_key, response, ttl=300
                )  # 5 min cache

            # Log search
            if self.enable_audit:
                await self._log_access(
                    accessed_by=str(user_level),
                    access_type="search",
                    access_context=json.dumps(
                        {"query": query, "results": len(results)}
                    ),
                    session=session,
                )

            return response

    # ==================== Relationship Management ====================

    async def add_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> KnowledgeRelationship:
        """
        Add a relationship between knowledge items

        Args:
            source_id: Source knowledge ID
            target_id: Target knowledge ID
            relationship_type: Type of relationship
            strength: Relationship strength (0.0-1.0)
            metadata: Optional metadata

        Returns:
            Created relationship
        """
        async with self.async_session() as session:
            relationship = KnowledgeRelationship(
                source_knowledge_id=source_id,
                target_knowledge_id=target_id,
                relationship_type=relationship_type,
                strength=strength,
                metadata=metadata or {},
            )

            session.add(relationship)
            await session.commit()

            logger.info(
                f"Added {relationship_type} relationship: {source_id} -> {target_id}"
            )
            return relationship

    async def get_related_knowledge(
        self,
        knowledge_id: UUID,
        relationship_types: Optional[list[RelationshipType]] = None,
        min_strength: float = 0.0,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get related knowledge items

        Args:
            knowledge_id: Source knowledge ID
            relationship_types: Filter by relationship types
            min_strength: Minimum relationship strength
            limit: Maximum results

        Returns:
            List of related knowledge with relationship metadata
        """
        async with self.async_session() as session:
            stmt = (
                select(KnowledgeRelationship, FoundationalKnowledge)
                .join(
                    FoundationalKnowledge,
                    KnowledgeRelationship.target_knowledge_id
                    == FoundationalKnowledge.id,
                )
                .where(
                    and_(
                        KnowledgeRelationship.source_knowledge_id == knowledge_id,
                        KnowledgeRelationship.strength >= min_strength,
                        FoundationalKnowledge.is_current,
                    )
                )
            )

            if relationship_types:
                stmt = stmt.where(
                    KnowledgeRelationship.relationship_type.in_(relationship_types)
                )

            stmt = stmt.order_by(KnowledgeRelationship.strength.desc()).limit(limit)

            result = await session.execute(stmt)
            related = []

            for rel, knowledge in result:
                related.append(
                    {
                        "knowledge": knowledge.dict(),
                        "relationship": {
                            "type": rel.relationship_type,
                            "strength": rel.strength,
                            "metadata": rel.metadata,
                        },
                    }
                )

            return related

    # ==================== Version Management ====================

    async def get_version_history(
        self, knowledge_id: UUID, limit: int = 10
    ) -> list[KnowledgeVersion]:
        """
        Get version history for knowledge

        Args:
            knowledge_id: Knowledge ID
            limit: Maximum versions to return

        Returns:
            List of versions in descending order
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(KnowledgeVersion)
                .where(KnowledgeVersion.knowledge_id == knowledge_id)
                .order_by(KnowledgeVersion.version_number.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def restore_version(
        self, knowledge_id: UUID, version_number: int, restored_by: str = "system"
    ) -> Optional[FoundationalKnowledge]:
        """
        Restore a specific version of knowledge

        Args:
            knowledge_id: Knowledge ID
            version_number: Version to restore
            restored_by: User/system restoring the version

        Returns:
            Restored knowledge if successful
        """
        async with self.async_session() as session:
            # Get the version to restore
            result = await session.execute(
                select(KnowledgeVersion).where(
                    and_(
                        KnowledgeVersion.knowledge_id == knowledge_id,
                        KnowledgeVersion.version_number == version_number,
                    )
                )
            )
            version = result.scalar_one_or_none()

            if not version:
                return None

            # Get current knowledge
            result = await session.execute(
                select(FoundationalKnowledge).where(
                    FoundationalKnowledge.id == knowledge_id
                )
            )
            knowledge = result.scalar_one_or_none()

            if not knowledge:
                return None

            # Create restore version
            await self.versioning_engine.create_version(
                knowledge=knowledge,
                change_type=ChangeType.RESTORE,
                changed_by=restored_by,
                change_summary=f"Restored to version {version_number}",
                session=session,
            )

            # Restore fields from version
            knowledge.title = version.title
            knowledge.content = version.content
            knowledge.category = version.category
            knowledge.tags = version.tags
            knowledge.metadata = version.metadata
            knowledge.version += 1
            knowledge.is_current = True
            knowledge.updated_at = datetime.utcnow()

            await session.commit()

            # Invalidate cache
            await self.cache_manager.delete(f"knowledge:{knowledge_id}")

            logger.info(
                f"Restored knowledge {knowledge_id} to version {version_number}"
            )
            return knowledge

    # ==================== Utility Methods ====================

    async def _log_access(
        self,
        accessed_by: str,
        access_type: str,
        knowledge_id: Optional[UUID] = None,
        access_context: Optional[str] = None,
        session: AsyncSession = None,
    ):
        """Log access for audit trail"""
        if not self.enable_audit:
            return

        access_log = AccessLog(
            knowledge_id=knowledge_id,
            accessed_by=accessed_by,
            access_type=access_type,
            access_context=access_context,
        )

        if session:
            session.add(access_log)
        else:
            async with self.async_session() as new_session:
                new_session.add(access_log)
                await new_session.commit()

    def _generate_cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_parts = [str(arg) for arg in args if arg is not None]
        key_string = ":".join(key_parts)
        return f"knowledge:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics"""
        async with self.async_session() as session:
            # Total knowledge count
            total_count = await session.scalar(
                select(func.count())
                .select_from(FoundationalKnowledge)
                .where(FoundationalKnowledge.is_current)
            )

            # Count by category
            category_counts = await session.execute(
                select(FoundationalKnowledge.category, func.count().label("count"))
                .where(FoundationalKnowledge.is_current)
                .group_by(FoundationalKnowledge.category)
            )

            # Count by classification
            classification_counts = await session.execute(
                select(
                    FoundationalKnowledge.data_classification,
                    func.count().label("count"),
                )
                .where(FoundationalKnowledge.is_current)
                .group_by(FoundationalKnowledge.data_classification)
            )

            # Version statistics
            total_versions = await session.scalar(
                select(func.count()).select_from(KnowledgeVersion)
            )

            # Recent sync info
            result = await session.execute(
                select(SyncOperation)
                .where(SyncOperation.status == "completed")
                .order_by(SyncOperation.completed_at.desc())
                .limit(1)
            )
            last_sync = result.scalar_one_or_none()

            return {
                "total_knowledge": total_count,
                "by_category": {row[0]: row[1] for row in category_counts},
                "by_classification": {row[0]: row[1] for row in classification_counts},
                "total_versions": total_versions,
                "last_sync": last_sync.dict() if last_sync else None,
                "cache_stats": (
                    await self.cache_manager.get_stats() if self.cache_manager else None
                ),
            }
