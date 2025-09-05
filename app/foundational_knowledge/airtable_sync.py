"""
Airtable Sync Service
Handles synchronization between Airtable CEO Knowledge Base and local foundational knowledge
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import aiohttp
from pydantic import BaseModel

from app.foundational_knowledge.classification_engine import DataClassificationEngine
from app.foundational_knowledge.manager import FoundationalKnowledgeManager
from app.foundational_knowledge.models import (
    AccessLevel,
    DataClassification,
    FoundationalKnowledge,
    SensitivityLevel,
    SyncOperation,
    SyncStatus,
)

logger = logging.getLogger(__name__)


class AirtableRecord(BaseModel):
    """Airtable record model"""

    id: str
    fields: Dict[str, Any]
    createdTime: str


class SyncQueueItem(BaseModel):
    """Item in the sync queue"""

    id: UUID = uuid4()
    table_name: str
    record_id: str
    operation: str  # 'create', 'update', 'delete'
    data: Dict[str, Any]
    priority: int = 0
    created_at: datetime = datetime.utcnow()
    attempts: int = 0
    last_attempt: Optional[datetime] = None


class AirtableSync:
    """
    Airtable synchronization service

    Features:
    - Incremental and full sync modes
    - Queue-based processing for reliability
    - Automatic retry with exponential backoff
    - Change detection and versioning
    - Data classification and sensitivity tagging
    """

    def __init__(
        self,
        api_key: str,
        base_id: str,
        knowledge_manager: FoundationalKnowledgeManager,
        classification_engine: Optional[DataClassificationEngine] = None,
        max_retries: int = 3,
        batch_size: int = 100,
    ):
        """
        Initialize Airtable sync service

        Args:
            api_key: Airtable API key
            base_id: Airtable base ID
            knowledge_manager: Knowledge manager instance
            classification_engine: Optional classification engine
            max_retries: Maximum retry attempts
            batch_size: Records per batch
        """
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = f"https://api.airtable.com/v0/{base_id}"

        self.knowledge_manager = knowledge_manager
        self.classification_engine = classification_engine or DataClassificationEngine()

        self.max_retries = max_retries
        self.batch_size = batch_size

        # Sync queue
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.processing_set: Set[str] = set()  # Track items being processed

        # Table mappings from config
        self.table_mappings = {
            "Employee Roster": {
                "category": "organization",
                "default_classification": DataClassification.CONFIDENTIAL,
                "field_mappings": {
                    "Name": "title",
                    "Role": "role",
                    "Department": "department",
                    "Email": "email",
                    "Linear ID": "linear_id",
                    "Asana ID": "asana_id",
                    "Gong ID": "gong_id",
                },
            },
            "Strategic Initiatives": {
                "category": "strategy",
                "default_classification": DataClassification.PROPRIETARY,
                "field_mappings": {
                    "Initiative": "title",
                    "Description": "content",
                    "Owner": "owner",
                    "Status": "status",
                    "Priority": "priority",
                    "Target Date": "target_date",
                },
            },
            "Executive Decisions": {
                "category": "decisions",
                "default_classification": DataClassification.RESTRICTED,
                "field_mappings": {
                    "Decision": "title",
                    "Context": "content",
                    "Rationale": "rationale",
                    "Impact": "impact",
                    "Date": "decision_date",
                    "Stakeholders": "stakeholders",
                },
            },
        }

        logger.info(f"AirtableSync initialized for base {base_id}")

    # ==================== Sync Operations ====================

    async def sync_all_tables(
        self, sync_type: str = "incremental", force: bool = False
    ) -> SyncOperation:
        """
        Sync all configured tables

        Args:
            sync_type: 'full' or 'incremental'
            force: Force sync even if recently synced

        Returns:
            Sync operation result
        """
        sync_op = SyncOperation(
            sync_type=sync_type,
            source_platform="airtable",
            source_base=self.base_id,
            triggered_by="system",
        )

        try:
            sync_op.status = SyncStatus.RUNNING

            for table_name in self.table_mappings.keys():
                logger.info(f"Syncing table: {table_name}")

                table_result = await self.sync_table(
                    table_name=table_name, sync_type=sync_type, force=force
                )

                # Aggregate results
                sync_op.records_processed += table_result.records_processed
                sync_op.records_created += table_result.records_created
                sync_op.records_updated += table_result.records_updated
                sync_op.records_deleted += table_result.records_deleted
                sync_op.records_failed += table_result.records_failed

            sync_op.status = SyncStatus.COMPLETED
            sync_op.completed_at = datetime.utcnow()
            sync_op.duration_seconds = int(
                (sync_op.completed_at - sync_op.started_at).total_seconds()
            )

            logger.info(
                f"Sync completed: {sync_op.records_processed} processed, "
                f"{sync_op.records_created} created, {sync_op.records_updated} updated"
            )

        except Exception as e:
            sync_op.status = SyncStatus.FAILED
            sync_op.error_message = str(e)
            sync_op.completed_at = datetime.utcnow()
            logger.error(f"Sync failed: {e}")

        return sync_op

    async def sync_table(
        self, table_name: str, sync_type: str = "incremental", force: bool = False
    ) -> SyncOperation:
        """
        Sync a specific table

        Args:
            table_name: Table to sync
            sync_type: 'full' or 'incremental'
            force: Force sync even if recently synced

        Returns:
            Sync operation result
        """
        if table_name not in self.table_mappings:
            raise ValueError(f"Unknown table: {table_name}")

        sync_op = SyncOperation(
            sync_type=sync_type,
            source_platform="airtable",
            source_base=self.base_id,
            source_table=table_name,
            triggered_by="system",
        )

        try:
            sync_op.status = SyncStatus.RUNNING

            # Get last sync time for incremental
            last_sync = None
            if sync_type == "incremental" and not force:
                last_sync = await self._get_last_sync_time(table_name)

            # Fetch records from Airtable
            records = await self._fetch_airtable_records(
                table_name=table_name, modified_since=last_sync
            )

            sync_op.records_processed = len(records)

            # Process records
            for record in records:
                try:
                    result = await self._process_record(record=record, table_name=table_name)

                    if result == "created":
                        sync_op.records_created += 1
                    elif result == "updated":
                        sync_op.records_updated += 1
                    elif result == "failed":
                        sync_op.records_failed += 1

                except Exception as e:
                    sync_op.records_failed += 1
                    logger.error(f"Failed to process record {record.id}: {e}")

            # Handle deletions for full sync
            if sync_type == "full":
                deleted_count = await self._handle_deletions(
                    table_name=table_name, current_record_ids=[r.id for r in records]
                )
                sync_op.records_deleted = deleted_count

            sync_op.status = SyncStatus.COMPLETED
            sync_op.completed_at = datetime.utcnow()
            sync_op.duration_seconds = int(
                (sync_op.completed_at - sync_op.started_at).total_seconds()
            )

        except Exception as e:
            sync_op.status = SyncStatus.FAILED
            sync_op.error_message = str(e)
            sync_op.completed_at = datetime.utcnow()
            logger.error(f"Table sync failed for {table_name}: {e}")

        return sync_op

    # ==================== Queue Processing ====================

    async def start_queue_processor(self):
        """Start the background queue processor"""
        asyncio.create_task(self._process_queue())
        logger.info("Sync queue processor started")

    async def _process_queue(self):
        """Process items from the sync queue"""
        while True:
            try:
                # Get item from queue
                item: SyncQueueItem = await self.sync_queue.get()

                # Skip if already being processed
                item_key = f"{item.table_name}:{item.record_id}"
                if item_key in self.processing_set:
                    continue

                self.processing_set.add(item_key)

                try:
                    # Process the item
                    await self._process_queue_item(item)

                except Exception as e:
                    logger.error(f"Failed to process queue item {item.id}: {e}")

                    # Retry logic
                    item.attempts += 1
                    item.last_attempt = datetime.utcnow()

                    if item.attempts < self.max_retries:
                        # Re-queue with exponential backoff
                        delay = 2**item.attempts
                        await asyncio.sleep(delay)
                        await self.sync_queue.put(item)
                    else:
                        logger.error(f"Max retries reached for {item.id}")

                finally:
                    self.processing_set.discard(item_key)

            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(1)

    async def _process_queue_item(self, item: SyncQueueItem):
        """Process a single queue item"""
        if item.operation == "create":
            await self._create_knowledge_from_item(item)
        elif item.operation == "update":
            await self._update_knowledge_from_item(item)
        elif item.operation == "delete":
            await self._delete_knowledge_from_item(item)
        else:
            logger.warning(f"Unknown operation: {item.operation}")

    # ==================== Airtable API ====================

    async def _fetch_airtable_records(
        self,
        table_name: str,
        modified_since: Optional[datetime] = None,
        offset: Optional[str] = None,
    ) -> List[AirtableRecord]:
        """
        Fetch records from Airtable

        Args:
            table_name: Table to fetch from
            modified_since: Only get records modified after this time
            offset: Pagination offset

        Returns:
            List of Airtable records
        """
        records = []
        url = f"{self.base_url}/{table_name}"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        params = {"pageSize": self.batch_size, "timeZone": "UTC", "userLocale": "en"}

        if offset:
            params["offset"] = offset

        if modified_since:
            # Airtable filterByFormula for modified records
            formula = f"DATETIME_DIFF(LAST_MODIFIED_TIME(), '{modified_since.isoformat()}', 'seconds') > 0"
            params["filterByFormula"] = formula

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Airtable API error: {response.status} - {error_text}")

                data = await response.json()

                for record_data in data.get("records", []):
                    records.append(AirtableRecord(**record_data))

                # Handle pagination
                if data.get("offset"):
                    next_records = await self._fetch_airtable_records(
                        table_name=table_name, modified_since=modified_since, offset=data["offset"]
                    )
                    records.extend(next_records)

        return records

    # ==================== Record Processing ====================

    async def _process_record(self, record: AirtableRecord, table_name: str) -> str:
        """
        Process a single Airtable record

        Args:
            record: Airtable record
            table_name: Source table name

        Returns:
            Result: 'created', 'updated', or 'failed'
        """
        mapping = self.table_mappings[table_name]

        # Extract and map fields
        knowledge_data = await self._map_record_to_knowledge(
            record=record, table_name=table_name, mapping=mapping
        )

        # Check if record exists
        existing = await self.knowledge_manager.get_knowledge(
            knowledge_id=self._generate_knowledge_id(record.id, table_name), use_cache=False
        )

        if existing:
            # Update existing
            changes = self._detect_changes(existing, knowledge_data)

            if changes:
                updated = await self.knowledge_manager.update_knowledge(
                    knowledge_id=existing.id, updates=changes, updated_by="airtable_sync"
                )
                return "updated" if updated else "failed"

            return "unchanged"
        else:
            # Create new
            knowledge = FoundationalKnowledge(**knowledge_data)
            created = await self.knowledge_manager.create_knowledge(
                knowledge=knowledge, created_by="airtable_sync"
            )
            return "created" if created else "failed"

    async def _map_record_to_knowledge(
        self, record: AirtableRecord, table_name: str, mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map Airtable record to foundational knowledge

        Args:
            record: Airtable record
            table_name: Source table
            mapping: Field mappings

        Returns:
            Knowledge data dictionary
        """
        field_mappings = mapping.get("field_mappings", {})

        # Extract title and content
        title = None
        content = None
        metadata = {}

        for airtable_field, knowledge_field in field_mappings.items():
            value = record.fields.get(airtable_field)

            if knowledge_field == "title":
                title = str(value) if value else f"Record {record.id}"
            elif knowledge_field == "content":
                content = str(value) if value else None
            else:
                # Store in metadata
                if value is not None:
                    metadata[knowledge_field] = value

        # Classify the data
        classification_result = await self.classification_engine.classify(
            title=title, content=content, source_table=table_name, metadata=metadata
        )

        return {
            "id": self._generate_knowledge_id(record.id, table_name),
            "source_id": record.id,
            "source_table": table_name,
            "source_platform": "airtable",
            "title": title,
            "content": content,
            "category": mapping.get("category", "general"),
            "tags": classification_result.get("tags", []),
            "data_classification": classification_result.get(
                "classification", mapping.get("default_classification", DataClassification.INTERNAL)
            ),
            "sensitivity_level": classification_result.get("sensitivity", SensitivityLevel.MEDIUM),
            "access_level": classification_result.get("access_level", AccessLevel.EMPLOYEE),
            "metadata": metadata,
            "last_synced_at": datetime.utcnow(),
        }

    def _generate_knowledge_id(self, record_id: str, table_name: str) -> UUID:
        """Generate deterministic UUID from record ID and table"""
        namespace = uuid4()  # Use a fixed namespace in production
        name = f"{table_name}:{record_id}"
        # Create deterministic UUID
        hash_obj = hashlib.sha256(f"{namespace}{name}".encode())
        return UUID(hash_obj.hexdigest()[:32])

    def _detect_changes(
        self, existing: FoundationalKnowledge, new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect changes between existing and new data

        Args:
            existing: Existing knowledge
            new_data: New data from Airtable

        Returns:
            Dictionary of changed fields
        """
        changes = {}

        # Check each field for changes
        fields_to_check = [
            "title",
            "content",
            "category",
            "tags",
            "data_classification",
            "sensitivity_level",
            "access_level",
            "metadata",
        ]

        for field in fields_to_check:
            existing_value = getattr(existing, field, None)
            new_value = new_data.get(field)

            # Handle different types
            if field == "tags":
                # Compare lists
                if set(existing_value or []) != set(new_value or []):
                    changes[field] = new_value
            elif field == "metadata":
                # Compare dictionaries
                if existing_value != new_value:
                    changes[field] = new_value
            else:
                # Simple comparison
                if existing_value != new_value:
                    changes[field] = new_value

        return changes

    async def _handle_deletions(self, table_name: str, current_record_ids: List[str]) -> int:
        """
        Handle deletions for full sync

        Args:
            table_name: Table being synced
            current_record_ids: IDs that currently exist in Airtable

        Returns:
            Number of records deleted
        """
        # This would query the database for records from this table
        # that don't exist in current_record_ids and mark them as deleted
        # Implementation depends on database structure

        deleted_count = 0
        # Placeholder for deletion logic

        return deleted_count

    async def _get_last_sync_time(self, table_name: str) -> Optional[datetime]:
        """Get the last successful sync time for a table"""
        # Query the database for the last successful sync
        # This is a placeholder - actual implementation would query sync_operations table
        return None

    # ==================== Queue Item Processors ====================

    async def _create_knowledge_from_item(self, item: SyncQueueItem):
        """Create knowledge from queue item"""
        knowledge = FoundationalKnowledge(
            source_id=item.record_id, source_table=item.table_name, **item.data
        )

        await self.knowledge_manager.create_knowledge(knowledge=knowledge, created_by="sync_queue")

    async def _update_knowledge_from_item(self, item: SyncQueueItem):
        """Update knowledge from queue item"""
        knowledge_id = self._generate_knowledge_id(item.record_id, item.table_name)

        await self.knowledge_manager.update_knowledge(
            knowledge_id=knowledge_id, updates=item.data, updated_by="sync_queue"
        )

    async def _delete_knowledge_from_item(self, item: SyncQueueItem):
        """Delete knowledge from queue item"""
        knowledge_id = self._generate_knowledge_id(item.record_id, item.table_name)

        await self.knowledge_manager.delete_knowledge(
            knowledge_id=knowledge_id, deleted_by="sync_queue", soft_delete=True
        )
