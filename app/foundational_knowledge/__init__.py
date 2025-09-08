"""
Foundational Knowledge System
CEO-curated knowledge base with versioning and intelligent classification
"""

from .manager import FoundationalKnowledgeManager
from .models import (
    DataClassification,
    FoundationalKnowledge,
    KnowledgeVersion,
    SyncOperation,
)

__all__ = [
    "FoundationalKnowledgeManager",
    "FoundationalKnowledge",
    "KnowledgeVersion",
    "SyncOperation",
    "DataClassification",
]
