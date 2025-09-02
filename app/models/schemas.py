"""
Pydantic Schemas for Sophia Intel AI
Centralized type definitions for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, conint, constr, validator

# ============================================
# Base Models
# ============================================

class TimestampedModel(BaseModel):
    """Base model with timestamp."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class StatusModel(BaseModel):
    """Base model for status responses."""
    status: Literal["success", "error", "pending", "processing"] = Field(..., description="Operation status")
    message: str | None = Field(None, description="Status message")

# ============================================
# Error Models (Standardized)
# ============================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: str | None = Field(None, description="Field that caused error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")

class ErrorResponse(TimestampedModel):
    """Standardized error response."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error detail")
    status_code: int = Field(..., ge=400, le=599, description="HTTP status code")
    path: str | None = Field(None, description="Request path")
    errors: list[ErrorDetail] | None = Field(None, description="Detailed errors")
    trace_id: str | None = Field(None, description="Trace ID for debugging")

# ============================================
# Team Models
# ============================================

class TeamMember(BaseModel):
    """Team member information."""
    name: str = Field(..., description="Member name")
    role: str = Field(..., description="Member role")
    model: str | None = Field(None, description="Model used")

class TeamInfo(BaseModel):
    """Team/Swarm information."""
    id: constr(min_length=1, max_length=100) = Field(..., description="Team identifier")
    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team description")
    members: list[str | TeamMember] = Field(..., description="Team members")
    model_pool: str = Field(..., description="Model pool (premium/balanced/fast)")
    active: bool = Field(default=True, description="Team active status")
    capabilities: list[str] | None = Field(None, description="Team capabilities")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

class RunRequest(BaseModel):
    """Request for team/workflow execution."""
    team_id: str | None = Field(None, description="Team identifier")
    workflow_id: str | None = Field(None, description="Workflow identifier")
    message: constr(min_length=1, max_length=10000) = Field(..., description="Task message")
    stream: bool = Field(default=True, description="Enable streaming")
    use_memory: bool = Field(default=True, description="Use memory context")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    parameters: dict[str, Any] | None = Field(None, description="Execution parameters")
    timeout: conint(ge=1, le=3600) = Field(default=300, description="Timeout in seconds")

class RunResponse(TimestampedModel):
    """Response from team/workflow execution."""
    task_id: str = Field(..., description="Execution task ID")
    status: str = Field(..., description="Execution status")
    result: dict[str, Any] | None = Field(None, description="Execution result")
    metrics: dict[str, Any] | None = Field(None, description="Execution metrics")

# ============================================
# Memory Models
# ============================================

class MemoryType(str, Enum):
    """Types of memory entries."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"

class MemoryEntry(TimestampedModel):
    """Memory entry model."""
    hash_id: str | None = Field(None, description="Unique hash ID")
    topic: str = Field(..., min_length=1, max_length=500, description="Memory topic")
    content: str = Field(..., min_length=1, description="Memory content")
    source: str = Field(default="user", description="Memory source")
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC, description="Memory type")
    tags: list[str] = Field(default_factory=list, description="Memory tags")
    embedding: list[float] | None = Field(None, description="Vector embedding")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    access_count: int = Field(default=0, ge=0, description="Access count")

    @validator('tags')
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        return [tag.lower().strip() for tag in v if tag.strip()]

class MemorySearchResult(MemoryEntry):
    """Memory search result with score."""
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    highlights: list[str] | None = Field(None, description="Text highlights")

# ============================================
# Workflow Models
# ============================================

class WorkflowStep(BaseModel):
    """Workflow step definition."""
    id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    description: str | None = Field(None, description="Step description")
    agent: str | None = Field(None, description="Agent to execute")
    inputs: dict[str, Any] | None = Field(None, description="Step inputs")
    outputs: dict[str, Any] | None = Field(None, description="Step outputs")
    conditions: dict[str, Any] | None = Field(None, description="Execution conditions")

class WorkflowInfo(BaseModel):
    """Workflow information."""
    id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: list[WorkflowStep] = Field(..., description="Workflow steps")
    inputs: dict[str, Any] | None = Field(None, description="Required inputs")
    outputs: dict[str, Any] | None = Field(None, description="Expected outputs")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

# ============================================
# Search Models
# ============================================

class SearchMode(str, Enum):
    """Search modes."""
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"
    GRAPHRAG = "graphrag"

class SearchRequest(BaseModel):
    """Search request model."""
    query: constr(min_length=1, max_length=1000) = Field(..., description="Search query")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    limit: conint(ge=1, le=100) = Field(default=10, description="Result limit")
    offset: conint(ge=0) = Field(default=0, description="Result offset")
    filters: dict[str, Any] | None = Field(None, description="Search filters")
    rerank: bool = Field(default=False, description="Apply reranking")
    include_metadata: bool = Field(default=True, description="Include metadata")
    stream: bool = Field(default=False, description="Stream results")

class SearchResult(TimestampedModel):
    """Search result model."""
    id: str = Field(..., description="Result identifier")
    content: str = Field(..., description="Result content")
    score: float = Field(..., ge=0.0, description="Relevance score")
    source: str | None = Field(None, description="Result source")
    metadata: dict[str, Any] | None = Field(None, description="Result metadata")
    highlights: list[str] | None = Field(None, description="Text highlights")

class SearchResponse(TimestampedModel):
    """Search response model."""
    results: list[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., ge=0, description="Total results")
    mode: SearchMode = Field(..., description="Search mode used")
    query: str = Field(..., description="Original query")
    took_ms: int | None = Field(None, ge=0, description="Search duration in ms")

# ============================================
# Indexing Models
# ============================================

class IndexingStatus(str, Enum):
    """Indexing task status."""
    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IndexingRequest(BaseModel):
    """Indexing request model."""
    path: str = Field(..., description="Path to index")
    recursive: bool = Field(default=True, description="Index recursively")
    force: bool = Field(default=False, description="Force reindexing")
    file_patterns: list[str] | None = Field(None, description="File patterns to include")
    exclude_patterns: list[str] | None = Field(None, description="Patterns to exclude")
    batch_size: conint(ge=1, le=1000) = Field(default=100, description="Batch size")

class IndexingTask(TimestampedModel):
    """Indexing task model."""
    task_id: str = Field(..., description="Task identifier")
    status: IndexingStatus = Field(..., description="Task status")
    path: str = Field(..., description="Path being indexed")
    progress: conint(ge=0, le=100) = Field(default=0, description="Progress percentage")
    total_files: int = Field(default=0, ge=0, description="Total files to index")
    indexed_files: int = Field(default=0, ge=0, description="Files indexed")
    failed_files: int = Field(default=0, ge=0, description="Failed files")
    error_message: str | None = Field(None, description="Error message if failed")
    start_time: datetime | None = Field(None, description="Start time")
    end_time: datetime | None = Field(None, description="End time")

# ============================================
# Health Check Models
# ============================================

class ComponentHealth(BaseModel):
    """Component health status."""
    name: str = Field(..., description="Component name")
    healthy: bool = Field(..., description="Health status")
    latency_ms: int | None = Field(None, ge=0, description="Response latency")
    details: dict[str, Any] | None = Field(None, description="Health details")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last check time")

class SystemHealth(TimestampedModel):
    """System health status."""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall status")
    components: list[ComponentHealth] = Field(..., description="Component statuses")
    uptime_seconds: int = Field(..., ge=0, description="System uptime")
    version: str = Field(..., description="System version")
    environment: str = Field(..., description="Environment (dev/staging/prod)")

# ============================================
# Configuration Models
# ============================================

class ConfigUpdate(BaseModel):
    """Configuration update request."""
    section: str = Field(..., description="Configuration section")
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="New value")
    validate: bool = Field(default=True, description="Validate before applying")

class ConfigResponse(TimestampedModel):
    """Configuration response."""
    config: dict[str, Any] = Field(..., description="Current configuration")
    editable: list[str] = Field(..., description="Editable keys")
    readonly: list[str] = Field(..., description="Read-only keys")

# ============================================
# Metrics Models
# ============================================

class MetricPoint(BaseModel):
    """Single metric point."""
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str | None = Field(None, description="Metric unit")
    tags: dict[str, str] | None = Field(None, description="Metric tags")

class MetricsSnapshot(TimestampedModel):
    """Metrics snapshot."""
    metrics: list[MetricPoint] = Field(..., description="Metric points")
    period_seconds: int = Field(..., ge=0, description="Collection period")
    aggregation: str | None = Field(None, description="Aggregation method")

# ============================================
# Export All Models
# ============================================

__all__ = [
    # Base
    "TimestampedModel",
    "StatusModel",
    # Errors
    "ErrorDetail",
    "ErrorResponse",
    # Teams
    "TeamMember",
    "TeamInfo",
    "RunRequest",
    "RunResponse",
    # Memory
    "MemoryType",
    "MemoryEntry",
    "MemorySearchResult",
    # Workflows
    "WorkflowStep",
    "WorkflowInfo",
    # Search
    "SearchMode",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    # Indexing
    "IndexingStatus",
    "IndexingRequest",
    "IndexingTask",
    # Health
    "ComponentHealth",
    "SystemHealth",
    # Config
    "ConfigUpdate",
    "ConfigResponse",
    # Metrics
    "MetricPoint",
    "MetricsSnapshot"
]
