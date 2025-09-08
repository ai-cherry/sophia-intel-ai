"""
Versioning engine for knowledge entities
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.ai_logger import logger
from app.knowledge.models import KnowledgeEntity, KnowledgeVersion
from app.knowledge.storage_adapter import StorageAdapter


class VersioningEngine:
    """
    Manages versioning for knowledge entities with:
    - Automatic version creation on changes
    - Diff generation and comparison
    - Rollback capabilities
    - Audit trail maintenance
    """

    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def create_version(
        self,
        entity: KnowledgeEntity,
        changed_by: str = "system",
        change_summary: str | None = None,
    ) -> KnowledgeVersion:
        """Create a new version for a knowledge entity"""
        # Get current versions to determine version number
        existing_versions = await self.storage.get_versions(entity.id)
        version_number = len(existing_versions) + 1

        # Auto-generate change summary if not provided
        if not change_summary and existing_versions:
            last_version = existing_versions[0]
            change_summary = self._generate_change_summary(last_version, entity)
        elif not change_summary:
            change_summary = "Initial version"

        version = KnowledgeVersion(
            knowledge_id=entity.id,
            version_number=version_number,
            content=entity.content,
            metadata={
                "name": entity.name,
                "category": entity.category,
                "classification": entity.classification.value,
                "priority": entity.priority.value,
                "is_foundational": entity.is_foundational,
            },
            change_summary=change_summary,
            changed_by=changed_by,
        )

        await self.storage.create_version(version)
        logger.info(f"Created version {version_number} for knowledge {entity.id}")

        return version

    async def get_history(self, knowledge_id: str) -> list[KnowledgeVersion]:
        """Get complete version history for a knowledge entity"""
        versions = await self.storage.get_versions(knowledge_id)
        return versions

    async def get_version(self, knowledge_id: str, version_number: int) -> KnowledgeVersion | None:
        """Get specific version of knowledge"""
        return await self.storage.get_version(knowledge_id, version_number)

    async def rollback(self, knowledge_id: str, version_number: int) -> KnowledgeEntity:
        """Rollback knowledge to a specific version"""
        # Get the target version
        target_version = await self.get_version(knowledge_id, version_number)
        if not target_version:
            raise ValueError(f"Version {version_number} not found for knowledge {knowledge_id}")

        # Get current entity
        current_entity = await self.storage.get_knowledge(knowledge_id)
        if not current_entity:
            raise ValueError(f"Knowledge entity {knowledge_id} not found")

        # Create new entity from version
        rollback_entity = KnowledgeEntity(
            id=knowledge_id,
            name=target_version.metadata.get("name", current_entity.name),
            category=target_version.metadata.get("category", current_entity.category),
            classification=target_version.metadata.get(
                "classification", current_entity.classification
            ),
            priority=target_version.metadata.get("priority", current_entity.priority),
            content=target_version.content,
            metadata={
                **current_entity.metadata,
                "rolled_back_from": current_entity.version,
                "rolled_back_to": version_number,
                "rollback_timestamp": datetime.utcnow().isoformat(),
            },
            source=current_entity.source,
            source_id=current_entity.source_id,
            is_active=current_entity.is_active,
            version=current_entity.version + 1,
        )

        # Update the entity
        updated = await self.storage.update_knowledge(rollback_entity)

        # Create a new version documenting the rollback
        await self.create_version(
            updated,
            changed_by="system",
            change_summary=f"Rolled back from version {current_entity.version} to version {version_number}",
        )

        logger.info(f"Rolled back knowledge {knowledge_id} to version {version_number}")
        return updated

    async def compare(self, knowledge_id: str, v1: int, v2: int) -> dict[str, Any]:
        """Compare two versions of knowledge"""
        version1 = await self.get_version(knowledge_id, v1)
        version2 = await self.get_version(knowledge_id, v2)

        if not version1 or not version2:
            raise ValueError(f"One or both versions not found: v{v1}, v{v2}")

        comparison = {
            "knowledge_id": knowledge_id,
            "version_1": v1,
            "version_2": v2,
            "timestamp_1": version1.created_at.isoformat(),
            "timestamp_2": version2.created_at.isoformat(),
            "diff": version2.generate_diff(version1),
            "metadata_changes": self._compare_metadata(version1.metadata, version2.metadata),
        }

        return comparison

    async def get_latest_changes(self, knowledge_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get the latest changes for a knowledge entity"""
        versions = await self.get_history(knowledge_id)
        changes = []

        for i in range(min(limit, len(versions) - 1)):
            current = versions[i]
            previous = versions[i + 1] if i + 1 < len(versions) else None

            change = {
                "version": current.version_number,
                "timestamp": current.created_at.isoformat(),
                "changed_by": current.changed_by,
                "summary": current.change_summary,
            }

            if previous:
                change["diff"] = current.generate_diff(previous)

            changes.append(change)

        return changes

    def _generate_change_summary(
        self, old_version: KnowledgeVersion, new_entity: KnowledgeEntity
    ) -> str:
        """Generate automatic change summary"""
        changes = []

        # Check content changes
        old_content_keys = set(old_version.content.keys())
        new_content_keys = set(new_entity.content.keys())

        added = new_content_keys - old_content_keys
        removed = old_content_keys - new_content_keys

        if added:
            changes.append(f"Added {len(added)} field(s)")
        if removed:
            changes.append(f"Removed {len(removed)} field(s)")

        # Check for modified fields
        common = old_content_keys & new_content_keys
        modified_count = sum(1 for k in common if old_version.content[k] != new_entity.content[k])
        if modified_count:
            changes.append(f"Modified {modified_count} field(s)")

        # Check metadata changes
        if old_version.metadata:
            old_class = old_version.metadata.get("classification")
            new_class = new_entity.classification.value
            if old_class != new_class:
                changes.append(f"Classification: {old_class} → {new_class}")

            old_priority = old_version.metadata.get("priority")
            new_priority = new_entity.priority.value
            if old_priority != new_priority:
                changes.append(f"Priority: {old_priority} → {new_priority}")

        return "; ".join(changes) if changes else "Content updated"

    def _compare_metadata(self, meta1: dict | None, meta2: dict | None) -> dict[str, Any]:
        """Compare metadata between versions"""
        if not meta1:
            meta1 = {}
        if not meta2:
            meta2 = {}

        comparison = {
            "added": {},
            "removed": {},
            "modified": {},
        }

        keys1 = set(meta1.keys())
        keys2 = set(meta2.keys())

        # Added keys
        for key in keys2 - keys1:
            comparison["added"][key] = meta2[key]

        # Removed keys
        for key in keys1 - keys2:
            comparison["removed"][key] = meta1[key]

        # Modified values
        for key in keys1 & keys2:
            if meta1[key] != meta2[key]:
                comparison["modified"][key] = {
                    "old": meta1[key],
                    "new": meta2[key],
                }

        return comparison
