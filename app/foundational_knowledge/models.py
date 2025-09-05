"""
Pydantic models and database schemas for Foundational Knowledge System
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class DataClassification(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PROPRIETARY = "proprietary"
    RESTRICTED = "restricted"


class SensitivityLevel(str, Enum):
    """Data sensitivity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccessLevel(str, Enum):
    """Access control levels"""
    PUBLIC = "public"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    OWNER = "owner"


class ChangeType(str, Enum):
    """Types of changes for versioning"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"


class SyncStatus(str, Enum):
    """Sync operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RelationshipType(str, Enum):
    """Knowledge relationship types"""
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"
    CONTRADICTS = "contradicts"


# ==================== Base Models ====================

class FoundationalKnowledge(BaseModel):
    """Core foundational knowledge model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    source_id: str
    source_table: str
    source_platform: str = "airtable"
    
    # Content
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    
    # Classification
    data_classification: DataClassification = DataClassification.PROPRIETARY
    sensitivity_level: SensitivityLevel = SensitivityLevel.HIGH
    access_level: AccessLevel = AccessLevel.EXECUTIVE
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    
    # Tracking
    version: int = 1
    is_current: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
    
    # Computed fields
    @property
    def is_sensitive(self) -> bool:
        """Check if knowledge contains sensitive data"""
        return self.sensitivity_level in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
    
    @property
    def requires_auth(self) -> bool:
        """Check if knowledge requires authentication to access"""
        return self.access_level != AccessLevel.PUBLIC
    
    def can_access(self, user_level: AccessLevel) -> bool:
        """Check if user has access to this knowledge"""
        level_hierarchy = {
            AccessLevel.PUBLIC: 0,
            AccessLevel.EMPLOYEE: 1,
            AccessLevel.MANAGER: 2,
            AccessLevel.EXECUTIVE: 3,
            AccessLevel.OWNER: 4
        }
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(self.access_level, 0)


class KnowledgeVersion(BaseModel):
    """Version history for foundational knowledge"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    knowledge_id: UUID
    version_number: int
    
    # Snapshot of data
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Change tracking
    change_type: ChangeType
    change_summary: Optional[str] = None
    changed_fields: List[str] = Field(default_factory=list)
    previous_version_id: Optional[UUID] = None
    
    # Audit
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_source: str = "sync"  # 'sync', 'manual', 'api'


class KnowledgeRelationship(BaseModel):
    """Relationships between knowledge items"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    source_knowledge_id: UUID
    target_knowledge_id: UUID
    relationship_type: RelationshipType
    strength: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Sync Models ====================

class SyncOperation(BaseModel):
    """Sync operation tracking"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    sync_type: str  # 'full', 'incremental', 'manual'
    source_platform: str = "airtable"
    source_base: Optional[str] = None
    source_table: Optional[str] = None
    
    # Results
    status: SyncStatus = SyncStatus.PENDING
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Error tracking
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    triggered_by: Optional[str] = None
    sync_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def is_successful(self) -> bool:
        """Check if sync completed successfully"""
        return self.status == SyncStatus.COMPLETED and not self.error_message
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of sync"""
        if self.records_processed == 0:
            return 0.0
        return (self.records_processed - self.records_failed) / self.records_processed


# ==================== API Request/Response Models ====================

class CreateKnowledgeRequest(BaseModel):
    """Request model for creating knowledge"""
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    data_classification: Optional[DataClassification] = DataClassification.INTERNAL
    sensitivity_level: Optional[SensitivityLevel] = SensitivityLevel.MEDIUM
    access_level: Optional[AccessLevel] = AccessLevel.EMPLOYEE
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UpdateKnowledgeRequest(BaseModel):
    """Request model for updating knowledge"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    data_classification: Optional[DataClassification] = None
    sensitivity_level: Optional[SensitivityLevel] = None
    access_level: Optional[AccessLevel] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeSearchRequest(BaseModel):
    """Request model for searching knowledge"""
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    classification: Optional[DataClassification] = None
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)
    include_embeddings: bool = False


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge search"""
    results: List[FoundationalKnowledge]
    total_count: int
    query: str
    took_ms: int


class SyncTriggerRequest(BaseModel):
    """Request model for triggering sync"""
    sync_type: str = "incremental"  # 'full', 'incremental', 'manual'
    source_table: Optional[str] = None  # Specific table to sync
    force: bool = False  # Force sync even if recently synced


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    active_syncs: List[SyncOperation]
    last_successful_sync: Optional[SyncOperation]
    next_scheduled_sync: Optional[datetime]
    sync_health: str  # 'healthy', 'degraded', 'unhealthy'


# ==================== Cache Models ====================

class CacheMetadata(BaseModel):
    """Cache metadata for tracking"""
    cache_key: str
    knowledge_ids: List[UUID]
    query_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    hit_count: int = 0
    last_accessed_at: Optional[datetime] = None
    cache_size_bytes: int = 0


# ==================== Access Log Models ====================

class AccessLog(BaseModel):
    """Access log for audit trail"""
    id: UUID = Field(default_factory=uuid4)
    knowledge_id: Optional[UUID] = None
    accessed_by: str
    access_type: str  # 'read', 'update', 'delete', 'export'
    access_context: Optional[str] = None
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None