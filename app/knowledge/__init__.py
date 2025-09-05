"""
Foundational Knowledge System for Sophia Intelligence
"""

from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import (
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
    KnowledgeRelationship,
    KnowledgeTag,
    KnowledgeVersion,
    PayReadyContext,
    SyncConflict,
    SyncOperation,
)
from app.knowledge.storage_adapter import StorageAdapter

__all__ = [
    "KnowledgeEntity",
    "KnowledgeVersion",
    "PayReadyContext",
    "SyncOperation",
    "SyncConflict",
    "KnowledgeTag",
    "KnowledgeRelationship",
    "KnowledgeClassification",
    "KnowledgePriority",
    "FoundationalKnowledgeManager",
    "StorageAdapter",
]
