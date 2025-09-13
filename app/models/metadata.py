from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field
class MemoryMetadata(BaseModel):
    """
    Canonical metadata model used across memory entries, graph nodes, and index records.
    Keep this model stable and evolve with additive fields to avoid breaking downstream consumers.
    """
    type: Literal["code", "sql", "doc", "summary", "entity", "relation"] = Field(
        description="Primary content type"
    )
    topic: str | None = Field(default=None, description="High-level topic/category")
    source: str = Field(description="Origin of the record e.g., file path, URL, system")
    author: str | None = Field(default=None, description="Author or committer")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation or ingestion timestamp (UTC)",
    )
    version: str | None = Field(default=None, description="Version or commit hash")
    tags: list[str] = Field(
        default_factory=list, description="Normalized tags/keywords"
    )
    project: str | None = Field(default=None, description="Project or subsystem")
    security_level: Literal["public", "internal", "restricted"] = Field(
        default="public", description="Access classification"
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata for source-specific fields (non-indexed by default)",
    )
class EntityNode(BaseModel):
    """
    Graph entity node representation for Weaviate/graph store.
    """
    id: str | None = None
    name: str
    kind: Literal["func", "class", "module", "file", "table", "column", "fk", "entity"]
    summary: str | None = None
    path: str | None = None
    signature: str | None = None
    schema: str | None = None
    metadata: MemoryMetadata
class RelationEdge(BaseModel):
    """
    Graph relation edge representation for Weaviate/graph store.
    """
    id: str | None = None
    rel_type: str  # e.g., references, imports, belongs_to, has_many
    description: str | None = None
    from_id: str
    to_id: str
    metadata: MemoryMetadata
class DocumentChunk(BaseModel):
    """
    A single chunk of text with embedding and metadata.
    """
    id: str | None = None
    text: str
    embedding: list[float] | None = None
    chunk_index: int
    total_chunks: int
    metadata: MemoryMetadata
