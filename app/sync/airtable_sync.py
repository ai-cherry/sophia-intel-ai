"""
Airtable synchronization service for foundational knowledge
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

try:
    from pyairtable import Api as AirtableApi

    AIRTABLE_AVAILABLE = True
except ImportError:
    AIRTABLE_AVAILABLE = False
    AirtableApi = None

from app.core.ai_logger import logger
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import (
    ConflictType,
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
    SyncConflict,
    SyncOperation,
)


class AirtableSync:
    """
    Synchronizes foundational knowledge with Airtable CEO Knowledge Base
    """

    def __init__(self):
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID", "appBOVJqGE166onrD")
        self.api = None
        self.manager = FoundationalKnowledgeManager()

        if AIRTABLE_AVAILABLE and self.api_key:
            self.api = AirtableApi(self.api_key)
            self.base = self.api.base(self.base_id)
            logger.info("Airtable sync service initialized")
        else:
            logger.warning("Airtable not available or API key not set")

    async def full_sync(self) -> SyncOperation:
        """
        Perform full synchronization from Airtable to local knowledge base
        """
        if not self.api:
            logger.error("Airtable API not initialized")
            return None

        operation = SyncOperation(
            operation_type="full_sync",
            source="airtable",
            status="in_progress",
        )

        try:
            # Create sync operation record
            await self.manager.storage.create_sync_operation(operation)

            records_processed = 0
            conflicts_detected = 0

            # Sync each table
            tables = {
                "Strategic Knowledge": KnowledgeClassification.FOUNDATIONAL,
                "Strategic Initiatives": KnowledgeClassification.STRATEGIC,
                "Executive Decisions": KnowledgeClassification.STRATEGIC,
            }

            for table_name, classification in tables.items():
                try:
                    table = self.base.table(table_name)
                    records = table.all()

                    for record in records:
                        entity = await self._airtable_to_entity(record, classification)
                        result = await self._sync_entity(entity)

                        records_processed += 1
                        if isinstance(result, SyncConflict):
                            conflicts_detected += 1

                    logger.info(f"Synced {len(records)} records from {table_name}")

                except Exception as e:
                    logger.error(f"Error syncing table {table_name}: {e}")

            # Mark operation complete
            operation.complete(records_processed, conflicts_detected)
            await self.manager.storage.update_sync_operation(operation)

            logger.info(
                f"Full sync completed: {records_processed} records, {conflicts_detected} conflicts"
            )

        except Exception as e:
            operation.fail(str(e))
            await self.manager.storage.update_sync_operation(operation)
            logger.error(f"Full sync failed: {e}")

        return operation

    async def incremental_sync(self, since: datetime | None = None) -> SyncOperation:
        """
        Perform incremental sync of changes since last sync
        """
        if not self.api:
            logger.error("Airtable API not initialized")
            return None

        operation = SyncOperation(
            operation_type="incremental_sync",
            source="airtable",
            status="in_progress",
        )

        try:
            await self.manager.storage.create_sync_operation(operation)

            records_processed = 0
            conflicts_detected = 0

            # Get last sync time if not provided
            if not since:
                # Get from last successful sync
                since = await self._get_last_sync_time()

            # Sync modified records
            tables = ["Strategic Knowledge", "Strategic Initiatives", "Executive Decisions"]

            for table_name in tables:
                table = self.base.table(table_name)

                # Airtable doesn't have built-in modified filtering,
                # so we need to check each record
                records = table.all()

                for record in records:
                    # Check if modified since last sync
                    modified_time = record["fields"].get("Last Modified")
                    if modified_time and since:
                        record_time = datetime.fromisoformat(modified_time.replace("Z", "+00:00"))
                        if record_time <= since:
                            continue

                    entity = await self._airtable_to_entity(
                        record, KnowledgeClassification.FOUNDATIONAL
                    )
                    result = await self._sync_entity(entity)

                    records_processed += 1
                    if isinstance(result, SyncConflict):
                        conflicts_detected += 1

            operation.complete(records_processed, conflicts_detected)
            await self.manager.storage.update_sync_operation(operation)

            logger.info(
                f"Incremental sync completed: {records_processed} records, {conflicts_detected} conflicts"
            )

        except Exception as e:
            operation.fail(str(e))
            await self.manager.storage.update_sync_operation(operation)
            logger.error(f"Incremental sync failed: {e}")

        return operation

    async def push_to_airtable(self, entity: KnowledgeEntity) -> bool:
        """
        Push knowledge entity to Airtable
        """
        if not self.api:
            logger.error("Airtable API not initialized")
            return False

        try:
            # Determine table based on classification
            table_name = self._get_table_for_classification(entity.classification)
            table = self.base.table(table_name)

            # Convert entity to Airtable format
            airtable_record = self._entity_to_airtable(entity)

            if entity.source_id:
                # Update existing record
                table.update(entity.source_id, airtable_record)
                logger.info(f"Updated Airtable record {entity.source_id}")
            else:
                # Create new record
                result = table.create(airtable_record)
                entity.source_id = result["id"]
                await self.manager.update(entity)
                logger.info(f"Created Airtable record {result['id']}")

            return True

        except Exception as e:
            logger.error(f"Failed to push to Airtable: {e}")
            return False

    async def _sync_entity(self, remote_entity: KnowledgeEntity) -> Any:
        """
        Sync a single entity, handling conflicts
        """
        # Check if entity exists locally
        local_entity = await self.manager.get(remote_entity.id)

        if not local_entity:
            # New entity - create it
            return await self.manager.create(remote_entity)

        # Check for conflicts
        if local_entity.updated_at > remote_entity.updated_at:
            # Local is newer - potential conflict
            conflict = SyncConflict(
                knowledge_id=remote_entity.id,
                sync_operation_id="current",
                local_version=local_entity.to_dict(),
                remote_version=remote_entity.to_dict(),
                conflict_type=ConflictType.CONTENT,
            )

            # Auto-resolve based on classification
            if local_entity.is_foundational:
                # Protect foundational knowledge - keep local
                resolved = conflict.auto_resolve("local_wins")
            else:
                # Accept remote changes for non-foundational
                resolved = conflict.auto_resolve("remote_wins")

            await self.manager.update(resolved)
            return conflict

        # Remote is newer - update local
        remote_entity.synced_at = datetime.utcnow()
        return await self.manager.update(remote_entity)

    async def _airtable_to_entity(
        self, record: dict[str, Any], classification: KnowledgeClassification
    ) -> KnowledgeEntity:
        """
        Convert Airtable record to KnowledgeEntity
        """
        fields = record["fields"]

        # Map Airtable fields to entity
        entity = KnowledgeEntity(
            id=record["id"],
            name=fields.get("Name", fields.get("Document Name", "Untitled")),
            category=fields.get("Category", "general"),
            classification=classification,
            priority=self._map_priority(fields.get("Priority", 3)),
            content={
                "summary": fields.get("Summary", ""),
                "key_insights": fields.get("Key Insights", ""),
                "strategic_implications": fields.get("Strategic Implications", ""),
                "ceo_notes": fields.get("CEO Notes", ""),
                "raw_data": fields,
            },
            metadata={
                "airtable_id": record["id"],
                "created_time": record.get("createdTime"),
                "last_modified": fields.get("Last Modified", fields.get("Last Reviewed")),
            },
            source="airtable",
            source_id=record["id"],
            is_active=True,
            synced_at=datetime.utcnow(),
        )

        return entity

    def _entity_to_airtable(self, entity: KnowledgeEntity) -> dict[str, Any]:
        """
        Convert KnowledgeEntity to Airtable record format
        """
        content = entity.content if isinstance(entity.content, dict) else {}

        return {
            "Name": entity.name,
            "Category": entity.category,
            "Classification": entity.classification.value,
            "Priority": entity.priority.value,
            "Summary": content.get("summary", ""),
            "Key Insights": content.get("key_insights", ""),
            "Strategic Implications": content.get("strategic_implications", ""),
            "AI Analysis": json.dumps(entity.metadata),
            "Confidence": 0.95 if entity.is_foundational else 0.75,
            "Last Updated": datetime.utcnow().isoformat(),
        }

    def _get_table_for_classification(self, classification: KnowledgeClassification) -> str:
        """
        Determine Airtable table based on classification
        """
        mapping = {
            KnowledgeClassification.FOUNDATIONAL: "Strategic Knowledge",
            KnowledgeClassification.STRATEGIC: "Strategic Initiatives",
            KnowledgeClassification.OPERATIONAL: "Metrics",
            KnowledgeClassification.REFERENCE: "Strategic Knowledge",
        }

        return mapping.get(classification, "Strategic Knowledge")

    def _map_priority(self, airtable_priority: Any) -> KnowledgePriority:
        """
        Map Airtable priority (1-5 rating) to KnowledgePriority
        """
        if isinstance(airtable_priority, (int, float)):
            if airtable_priority >= 5:
                return KnowledgePriority.CRITICAL
            elif airtable_priority >= 4:
                return KnowledgePriority.HIGH
            elif airtable_priority >= 3:
                return KnowledgePriority.MEDIUM
            elif airtable_priority >= 2:
                return KnowledgePriority.LOW
            else:
                return KnowledgePriority.ARCHIVE

        return KnowledgePriority.MEDIUM

    async def _get_last_sync_time(self) -> datetime | None:
        """
        Get timestamp of last successful sync
        """
        # Query sync operations for last successful sync
        # This is a simplified version - in production, query the database
        return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
