"""
Memory system type definitions.
Shared types for memory entries and operations.
"""
from typing import Optional

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Types of memory entries."""
    EPISODIC = "episodic"      # Per-task notes, recent decisions
    SEMANTIC = "semantic"      # Patterns, conventions, architectural idioms
    PROCEDURAL = "procedural"  # Step checklists, fix recipes


@dataclass
class MemoryEntry:
    """Structured memory entry with deduplication."""
    topic: str
    content: str
    source: str
    tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: MemoryType = MemoryType.SEMANTIC
    embedding_vector: Optional[list[float]] = None
    hash_id: Optional[str] = None

    def __post_init__(self):
        """Generate hash ID for deduplication."""
        if not self.hash_id:
            import hashlib
            content_hash = hashlib.sha256(
                f"{self.topic}:{self.content}:{self.source}".encode()
            ).hexdigest()[:16]
            self.hash_id = content_hash
