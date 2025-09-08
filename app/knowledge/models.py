"""
Data models for the Foundational Knowledge System
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class KnowledgeClassification(str, Enum):
    """Classification levels for knowledge entries"""

    FOUNDATIONAL = "foundational"  # Core business truths
    STRATEGIC = "strategic"  # Strategic decisions and plans
    OPERATIONAL = "operational"  # Day-to-day operational data
    REFERENCE = "reference"  # Reference materials


class KnowledgePriority(int, Enum):
    """Priority levels for knowledge entries"""

    CRITICAL = 5  # Mission-critical information
    HIGH = 4  # High importance
    MEDIUM = 3  # Standard importance
    LOW = 2  # Low importance
    ARCHIVE = 1  # Archived/historical


class ConflictType(str, Enum):
    """Types of sync conflicts"""

    CONTENT = "content"  # Content differs
    METADATA = "metadata"  # Metadata differs
    CLASSIFICATION = "classification"  # Classification differs
    DELETION = "deletion"  # One side deleted


class ResolutionStatus(str, Enum):
    """Status of conflict resolution"""

    PENDING = "pending"
    AUTO_RESOLVED = "auto_resolved"
    MANUAL_RESOLVED = "manual_resolved"
    IGNORED = "ignored"


class PayReadyContext(BaseModel):
    """Pay-Ready specific business context"""

    company: str = "Pay Ready"
    mission: str = (
        "AI-first resident engagement, payments, and recovery platform for U.S. multifamily housing"
    )
    industry: str = "PropTech / Real Estate Technology"
    stage: str = "High-growth, bootstrapped and profitable"
    metrics: dict[str, Any] = Field(
        default_factory=lambda: {
            "annual_rent_processed": "$20B+",
            "employee_count": 100,
            "customer_type": "Property Management Companies",
            "market": "U.S. Multifamily Housing",
        }
    )
    key_differentiators: list[str] = Field(
        default_factory=lambda: [
            "AI-first approach to resident engagement",
            "Comprehensive financial operating system",
            "Evolution from collections to full-service platform",
            "Bootstrapped and profitable growth model",
        ]
    )
    foundational_categories: list[str] = Field(
        default_factory=lambda: [
            "company_overview",
            "strategic_initiatives",
            "executive_decisions",
            "market_intelligence",
            "product_roadmap",
        ]
    )


class KnowledgeEntity(BaseModel):
    """Core knowledge entity model"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    category: str
    classification: KnowledgeClassification = KnowledgeClassification.OPERATIONAL
    priority: KnowledgePriority = KnowledgePriority.MEDIUM
    content: dict[str, Any]
    pay_ready_context: PayReadyContext | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"
    source_id: str | None = None
    is_active: bool = True
    is_foundational: bool = False  # Explicit foundational flag
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    synced_at: datetime | None = None

    @validator("is_foundational", always=True)
    def set_foundational_flag(cls, v, values):
        """Auto-set foundational flag based on classification"""
        if "classification" in values:
            return values["classification"] in [
                KnowledgeClassification.FOUNDATIONAL,
                KnowledgeClassification.STRATEGIC,
            ]
        return v

    @validator("priority", always=True)
    def validate_priority_for_foundational(cls, v, values):
        """Ensure foundational knowledge has appropriate priority"""
        if values.get("is_foundational") and v < KnowledgePriority.HIGH:
            return KnowledgePriority.HIGH
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "classification": self.classification.value,
            "priority": self.priority.value,
            "content": self.content,
            "pay_ready_context": self.pay_ready_context.dict() if self.pay_ready_context else None,
            "metadata": self.metadata,
            "source": self.source,
            "source_id": self.source_id,
            "is_active": self.is_active,
            "is_foundational": self.is_foundational,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }


class KnowledgeVersion(BaseModel):
    """Version tracking for knowledge entities"""

    version_id: str = Field(default_factory=lambda: str(uuid4()))
    knowledge_id: str
    version_number: int
    content: dict[str, Any]
    metadata: dict[str, Any] | None = None
    change_summary: str | None = None
    changed_by: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def generate_diff(self, previous: KnowledgeVersion | None) -> dict[str, Any]:
        """Generate diff from previous version"""
        if not previous:
            return {"type": "initial", "content": self.content}

        # Simple diff - in production, use deepdiff or similar
        diff = {
            "type": "update",
            "version_from": previous.version_number,
            "version_to": self.version_number,
            "changes": [],
        }

        # Compare content keys
        old_keys = set(previous.content.keys())
        new_keys = set(self.content.keys())

        for key in new_keys - old_keys:
            diff["changes"].append({"type": "added", "key": key, "value": self.content[key]})

        for key in old_keys - new_keys:
            diff["changes"].append({"type": "removed", "key": key})

        for key in old_keys & new_keys:
            if previous.content[key] != self.content[key]:
                diff["changes"].append(
                    {
                        "type": "modified",
                        "key": key,
                        "old": previous.content[key],
                        "new": self.content[key],
                    }
                )

        return diff


class SyncOperation(BaseModel):
    """Track sync operations"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    operation_type: str  # full_sync, incremental_sync, manual_sync
    source: str  # airtable, manual, api
    status: str  # pending, in_progress, completed, failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    records_processed: int = 0
    conflicts_detected: int = 0
    error_details: dict[str, Any] | None = None

    def complete(self, records: int = 0, conflicts: int = 0):
        """Mark operation as complete"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.records_processed = records
        self.conflicts_detected = conflicts

    def fail(self, error: str):
        """Mark operation as failed"""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_details = {"error": error}


class SyncConflict(BaseModel):
    """Track and resolve sync conflicts"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    knowledge_id: str
    sync_operation_id: str
    local_version: dict[str, Any]
    remote_version: dict[str, Any]
    conflict_type: ConflictType
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def auto_resolve(self, strategy: str = "remote_wins") -> KnowledgeEntity:
        """Attempt automatic conflict resolution"""
        if strategy == "remote_wins":
            resolved = KnowledgeEntity(**self.remote_version)
        elif strategy == "local_wins":
            resolved = KnowledgeEntity(**self.local_version)
        elif strategy == "merge":
            # Simple merge - combine both versions
            merged = {**self.local_version, **self.remote_version}
            merged["metadata"]["conflict_merged"] = True
            resolved = KnowledgeEntity(**merged)
        else:
            raise ValueError(f"Unknown resolution strategy: {strategy}")

        self.resolution_status = ResolutionStatus.AUTO_RESOLVED
        self.resolved_at = datetime.utcnow()
        return resolved

    def manual_resolve(self, resolved_version: KnowledgeEntity, resolver: str):
        """Manual conflict resolution"""
        self.resolution_status = ResolutionStatus.MANUAL_RESOLVED
        self.resolved_by = resolver
        self.resolved_at = datetime.utcnow()
        return resolved_version


class KnowledgeTag(BaseModel):
    """Extensible tagging system for knowledge"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    knowledge_id: str
    tag_name: str
    tag_value: str | None = None
    tag_type: str = "custom"  # custom, system, ai_generated
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("tag_name")
    def validate_tag_name(cls, v):
        """Ensure tag names are normalized"""
        return v.lower().replace(" ", "_")


class KnowledgeRelationship(BaseModel):
    """Relationships between knowledge entities"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relationship_type: str  # depends_on, related_to, supersedes, contradicts
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_strong(self) -> bool:
        """Check if relationship is strong"""
        return self.strength >= 0.7

    def is_weak(self) -> bool:
        """Check if relationship is weak"""
        return self.strength < 0.3
