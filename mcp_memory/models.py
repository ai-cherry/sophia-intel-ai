from __future__ import annotations

"""Pydantic models for the MCP memory server."""

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator


class MemoryRecord(BaseModel):
    """Canonical representation of a single memory entry.

    The schema is versioned so that agents and services can coordinate
    changes as the repository evolves.
    """

    schema_version: Literal["1.0"] = Field(default="1.0", description="Schema version")
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str = Field(default="default", description="Agent originating the memory")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    vector_embedding: Optional[List[float]] = Field(default=None, description="Embedding vector")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required metadata keys are present."""
        required_keys = {"domain", "origin", "sensitivity", "ttl"}
        missing = required_keys - set(value.keys())
        if missing:
            raise ValueError(f"Missing metadata keys: {', '.join(sorted(missing))}")
        return value


class MemoryQuery(BaseModel):
    """Query parameters for memory retrieval."""

    content: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    vector_embedding: Optional[List[float]] = Field(
        default=None, description="Embedding vector for semantic search"
    )
    limit: int = 10
    semantic_search: bool = False


class MemoryResponse(BaseModel):
    """Standard response model for memory operations."""

    success: bool
    message: str
    data: Optional[Any] = None
