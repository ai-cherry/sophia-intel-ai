"""
Storage adapter for database-agnostic operations
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

from app.core.ai_logger import logger
from app.knowledge.models import (
    KnowledgeEntity,
    KnowledgeRelationship,
    KnowledgeTag,
    KnowledgeVersion,
    SyncConflict,
    SyncOperation,
)


class StorageAdapter:
    """Adapter for SQLite and PostgreSQL storage"""

    def __init__(self):
        self.db_type = os.getenv("DB_TYPE", "sqlite")
        self.connection = None
        self._connection_lock = threading.Lock()  # Thread safety lock
        self._connect()

    def _connect(self):
        """Establish database connection"""
        if self.db_type == "sqlite":
            db_path = os.getenv("DB_PATH", "sophia.db")
            # Use check_same_thread=False but with proper locking for thread safety
            # This allows the connection to be used across threads while preventing race conditions
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        elif self.db_type == "postgresql":
            if psycopg2 is None:
                raise ImportError(
                    "psycopg2 required for PostgreSQL. Install with: pip install psycopg2-binary"
                )

            self.connection = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "sophia"),
                user=os.getenv("DB_USER", "sophia"),
                password=os.getenv("DB_PASSWORD", ""),
                cursor_factory=RealDictCursor,
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _execute(self, query: str, params: tuple = ()) -> Any:
        """Execute query with proper parameter handling and thread safety"""
        with self._connection_lock:  # Ensure thread-safe database access
            if self.db_type == "postgresql":
                # Convert ? to %s for PostgreSQL
                query = query.replace("?", "%s")

            cursor = self.connection.cursor()
            cursor.execute(query, params)

            if self.db_type == "postgresql" or self.db_type == "sqlite":
                self.connection.commit()

            return cursor

    def _fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row (thread safety handled in _execute)"""
        cursor = self._execute(query, params)
        row = cursor.fetchone()
        if row:
            if self.db_type == "sqlite":
                return dict(row)
            else:
                return dict(row)
        return None

    def _fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows (thread safety handled in _execute)"""
        cursor = self._execute(query, params)
        rows = cursor.fetchall()
        if self.db_type == "sqlite":
            return [dict(row) for row in rows]
        else:
            return [dict(row) for row in rows]

    # ========== Knowledge Entity Operations ==========

    async def create_knowledge(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Create new knowledge entity"""
        query = """
            INSERT INTO foundational_knowledge
            (id, name, category, classification, priority, content,
             pay_ready_context, metadata, source, source_id, is_active,
             created_at, updated_at, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            entity.id,
            entity.name,
            entity.category,
            entity.classification.value,
            entity.priority.value,
            json.dumps(entity.content),
            json.dumps(entity.pay_ready_context.dict()) if entity.pay_ready_context else None,
            json.dumps(entity.metadata),
            entity.source,
            entity.source_id,
            entity.is_active,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat(),
            entity.synced_at.isoformat() if entity.synced_at else None,
        )

        self._execute(query, params)
        logger.info(f"Created knowledge entity: {entity.id}")
        return entity

    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeEntity]:
        """Get knowledge entity by ID"""
        query = "SELECT * FROM foundational_knowledge WHERE id = ?"
        row = self._fetchone(query, (knowledge_id,))

        if row:
            return self._row_to_entity(row)
        return None

    async def update_knowledge(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Update existing knowledge entity"""
        entity.updated_at = datetime.utcnow()

        query = """
            UPDATE foundational_knowledge
            SET name = ?, category = ?, classification = ?, priority = ?,
                content = ?, pay_ready_context = ?, metadata = ?,
                is_active = ?, updated_at = ?, synced_at = ?
            WHERE id = ?
        """

        params = (
            entity.name,
            entity.category,
            entity.classification.value,
            entity.priority.value,
            json.dumps(entity.content),
            json.dumps(entity.pay_ready_context.dict()) if entity.pay_ready_context else None,
            json.dumps(entity.metadata),
            entity.is_active,
            entity.updated_at.isoformat(),
            entity.synced_at.isoformat() if entity.synced_at else None,
            entity.id,
        )

        self._execute(query, params)
        logger.info(f"Updated knowledge entity: {entity.id}")
        return entity

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete knowledge entity"""
        query = "DELETE FROM foundational_knowledge WHERE id = ?"
        self._execute(query, (knowledge_id,))
        logger.info(f"Deleted knowledge entity: {knowledge_id}")
        return True

    async def list_knowledge(
        self,
        classification: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeEntity]:
        """List knowledge entities with filters"""
        query = "SELECT * FROM foundational_knowledge WHERE 1=1"
        params = []

        if classification:
            query += " AND classification = ?"
            params.append(classification)

        if category:
            query += " AND category = ?"
            params.append(category)

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        query += " ORDER BY priority DESC, updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._fetchall(query, tuple(params))
        return [self._row_to_entity(row) for row in rows]

    async def search_knowledge(self, query_text: str) -> List[KnowledgeEntity]:
        """Search knowledge entities"""
        # Simple text search - in production, use full-text search
        query = """
            SELECT * FROM foundational_knowledge
            WHERE name LIKE ? OR content LIKE ?
            AND is_active = 1
            ORDER BY priority DESC
            LIMIT 20
        """
        search_term = f"%{query_text}%"
        rows = self._fetchall(query, (search_term, search_term))
        return [self._row_to_entity(row) for row in rows]

    # ========== Version Operations ==========

    async def create_version(self, version: KnowledgeVersion) -> KnowledgeVersion:
        """Create knowledge version"""
        query = """
            INSERT INTO knowledge_versions
            (version_id, knowledge_id, version_number, content, metadata,
             change_summary, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            version.version_id,
            version.knowledge_id,
            version.version_number,
            json.dumps(version.content),
            json.dumps(version.metadata) if version.metadata else None,
            version.change_summary,
            version.changed_by,
            version.created_at.isoformat(),
        )

        self._execute(query, params)
        logger.info(
            f"Created version {version.version_number} for knowledge {version.knowledge_id}"
        )
        return version

    async def get_versions(self, knowledge_id: str) -> List[KnowledgeVersion]:
        """Get all versions for a knowledge entity"""
        query = """
            SELECT * FROM knowledge_versions
            WHERE knowledge_id = ?
            ORDER BY version_number DESC
        """
        rows = self._fetchall(query, (knowledge_id,))

        versions = []
        for row in rows:
            versions.append(
                KnowledgeVersion(
                    version_id=row["version_id"],
                    knowledge_id=row["knowledge_id"],
                    version_number=row["version_number"],
                    content=json.loads(row["content"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    change_summary=row["change_summary"],
                    changed_by=row["changed_by"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )

        return versions

    async def get_version(
        self, knowledge_id: str, version_number: int
    ) -> Optional[KnowledgeVersion]:
        """Get specific version"""
        query = """
            SELECT * FROM knowledge_versions
            WHERE knowledge_id = ? AND version_number = ?
        """
        row = self._fetchone(query, (knowledge_id, version_number))

        if row:
            return KnowledgeVersion(
                version_id=row["version_id"],
                knowledge_id=row["knowledge_id"],
                version_number=row["version_number"],
                content=json.loads(row["content"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                change_summary=row["change_summary"],
                changed_by=row["changed_by"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        return None

    # ========== Sync Operations ==========

    async def create_sync_operation(self, operation: SyncOperation) -> SyncOperation:
        """Create sync operation record"""
        query = """
            INSERT INTO sync_operations
            (id, operation_type, source, status, started_at, completed_at,
             records_processed, conflicts_detected, error_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            operation.id,
            operation.operation_type,
            operation.source,
            operation.status,
            operation.started_at.isoformat(),
            operation.completed_at.isoformat() if operation.completed_at else None,
            operation.records_processed,
            operation.conflicts_detected,
            json.dumps(operation.error_details) if operation.error_details else None,
        )

        self._execute(query, params)
        return operation

    async def update_sync_operation(self, operation: SyncOperation) -> SyncOperation:
        """Update sync operation"""
        query = """
            UPDATE sync_operations
            SET status = ?, completed_at = ?, records_processed = ?,
                conflicts_detected = ?, error_details = ?
            WHERE id = ?
        """

        params = (
            operation.status,
            operation.completed_at.isoformat() if operation.completed_at else None,
            operation.records_processed,
            operation.conflicts_detected,
            json.dumps(operation.error_details) if operation.error_details else None,
            operation.id,
        )

        self._execute(query, params)
        return operation

    # ========== Helper Methods ==========

    def _row_to_entity(self, row: Dict[str, Any]) -> KnowledgeEntity:
        """Convert database row to KnowledgeEntity"""
        from app.knowledge.models import KnowledgeClassification, KnowledgePriority, PayReadyContext

        pay_ready_context = None
        if row.get("pay_ready_context"):
            context_data = json.loads(row["pay_ready_context"])
            pay_ready_context = PayReadyContext(**context_data)

        return KnowledgeEntity(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            classification=KnowledgeClassification(row["classification"]),
            priority=KnowledgePriority(row["priority"]),
            content=json.loads(row["content"]),
            pay_ready_context=pay_ready_context,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            source=row["source"],
            source_id=row["source_id"],
            is_active=row["is_active"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            synced_at=datetime.fromisoformat(row["synced_at"]) if row["synced_at"] else None,
        )

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
