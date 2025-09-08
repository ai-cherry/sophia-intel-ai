"""
Airtable Integration Data Models

Core models for federated Airtable architecture with domain-specific bases
and shared data synchronization.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class BaseType(str, Enum):
    """Types of Airtable bases in federated architecture"""

    SHARED_CORE = "shared_core"
    MARKETING_OPS = "marketing_ops"
    SALES_INTELLIGENCE = "sales_intelligence"
    CUSTOMER_SUCCESS = "customer_success"
    FINANCE_OPS = "finance_ops"
    BRAND_KIT = "brand_kit"
    SOPHIA_FOUNDATION = "sophia_foundation"


class SyncStatus(str, Enum):
    """Synchronization status for records and bases"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    PAUSED = "paused"


class RecordType(str, Enum):
    """Types of records in Airtable bases"""

    # Shared Core Types
    COMPANY_PROFILE = "company_profile"
    INDUSTRY_DATA = "industry_data"
    INTEGRATION_CREDENTIAL = "integration_credential"
    UNIVERSAL_METRIC = "universal_metric"

    # Marketing Types
    CAMPAIGN_TEMPLATE = "campaign_template"
    BRAND_ASSET = "brand_asset"
    LEAD_SCORING_MODEL = "lead_scoring_model"
    AB_TEST_RESULT = "ab_test_result"

    # Sales Types
    PROSPECT_PROFILE = "prospect_profile"
    PERSONALITY_ASSESSMENT = "personality_assessment"
    OUTREACH_SEQUENCE = "outreach_sequence"
    COMPETITIVE_INTEL = "competitive_intel"

    # Customer Success Types
    HEALTH_SCORE_MODEL = "health_score_model"
    SUCCESS_MILESTONE = "success_milestone"
    ONBOARDING_WORKFLOW = "onboarding_workflow"

    # Finance Types
    BUDGET_ALLOCATION = "budget_allocation"
    ROI_MODEL = "roi_model"
    VENDOR_CONTRACT = "vendor_contract"

    # Brand Kit Types
    BRAND_GUIDELINE = "brand_guideline"
    TEMPLATE_ASSET = "template_asset"
    COLOR_PALETTE = "color_palette"
    LOGO_VARIANT = "logo_variant"

    # Sophia Foundation Types
    FOUNDATIONAL_KNOWLEDGE = "foundational_knowledge"
    CONTEXT_MAPPING = "context_mapping"
    DECISION_FRAMEWORK = "decision_framework"


@dataclass
class AirtableBase:
    """Airtable base configuration and metadata"""

    base_id: str
    name: str
    base_type: BaseType
    workspace_id: str

    # Configuration
    api_key: str = ""
    access_permissions: dict[str, list[str]] = field(default_factory=dict)
    sync_enabled: bool = True
    auto_sync_interval: int = 300  # seconds

    # Tables and structure
    tables: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_version: str = "1.0"

    # Sync configuration
    sync_dependencies: list[str] = field(default_factory=list)  # Other base IDs
    sync_priority: int = 1  # 1=highest, 10=lowest
    conflict_resolution: str = "manual"  # manual, auto_merge, source_wins

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.PENDING

    def get_table_names(self) -> list[str]:
        """Get list of table names in base"""
        return list(self.tables.keys())

    def has_table(self, table_name: str) -> bool:
        """Check if base has specific table"""
        return table_name in self.tables

    def update_sync_status(self, status: SyncStatus, timestamp: datetime = None):
        """Update synchronization status"""
        self.sync_status = status
        self.last_sync = timestamp or datetime.now()
        self.updated_at = datetime.now()


@dataclass
class AirtableRecord:
    """Individual record in Airtable with sync metadata"""

    record_id: str
    table_name: str
    base_id: str
    record_type: RecordType

    # Data
    fields: dict[str, Any] = field(default_factory=dict)

    # Sync metadata
    sync_id: str = field(default_factory=lambda: str(uuid4()))
    source_base: str = ""  # Original base for federated records
    sync_status: SyncStatus = SyncStatus.PENDING
    last_synced: Optional[datetime] = None
    sync_conflicts: list[dict[str, Any]] = field(default_factory=list)

    # Versioning
    version: int = 1
    version_history: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    updated_by: str = "system"

    def update_field(self, field_name: str, value: Any, updated_by: str = "system"):
        """Update field value with versioning"""
        old_value = self.fields.get(field_name)

        # Store version history
        self.version_history.append(
            {
                "version": self.version,
                "field": field_name,
                "old_value": old_value,
                "new_value": value,
                "updated_by": updated_by,
                "timestamp": datetime.now(),
            }
        )

        # Update field and metadata
        self.fields[field_name] = value
        self.version += 1
        self.updated_at = datetime.now()
        self.updated_by = updated_by
        self.sync_status = SyncStatus.PENDING

    def add_sync_conflict(self, conflict_description: str, conflicting_value: Any):
        """Add synchronization conflict"""
        self.sync_conflicts.append(
            {
                "conflict_id": str(uuid4()),
                "description": conflict_description,
                "conflicting_value": conflicting_value,
                "timestamp": datetime.now(),
                "resolved": False,
            }
        )
        self.sync_status = SyncStatus.CONFLICT

    def resolve_sync_conflict(self, conflict_id: str, resolution: str):
        """Resolve specific sync conflict"""
        for conflict in self.sync_conflicts:
            if conflict["conflict_id"] == conflict_id:
                conflict["resolved"] = True
                conflict["resolution"] = resolution
                conflict["resolved_at"] = datetime.now()
                break

        # Check if all conflicts are resolved
        unresolved_conflicts = [
            c for c in self.sync_conflicts if not c.get("resolved", False)
        ]
        if not unresolved_conflicts:
            self.sync_status = SyncStatus.PENDING


@dataclass
class SyncConfiguration:
    """Configuration for federated synchronization"""

    sync_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""

    # Source and target configuration
    source_bases: list[str] = field(default_factory=list)
    target_bases: list[str] = field(default_factory=list)
    bi_directional: bool = True

    # Sync rules
    sync_tables: dict[str, list[str]] = field(
        default_factory=dict
    )  # base_id -> table_names
    field_mappings: dict[str, dict[str, str]] = field(
        default_factory=dict
    )  # table -> field mappings
    transformation_rules: dict[str, Any] = field(default_factory=dict)

    # Scheduling
    sync_schedule: str = "*/5 * * * *"  # Cron format, default every 5 minutes
    auto_sync_enabled: bool = True
    manual_approval_required: bool = False

    # Conflict resolution
    conflict_resolution_strategy: str = (
        "manual"  # manual, source_wins, target_wins, merge
    )
    notification_webhooks: list[str] = field(default_factory=list)

    # Performance
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 300

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    enabled: bool = True

    def add_table_sync(self, base_id: str, table_name: str):
        """Add table to sync configuration"""
        if base_id not in self.sync_tables:
            self.sync_tables[base_id] = []

        if table_name not in self.sync_tables[base_id]:
            self.sync_tables[base_id].append(table_name)
            self.updated_at = datetime.now()

    def add_field_mapping(self, table_name: str, source_field: str, target_field: str):
        """Add field mapping for table"""
        if table_name not in self.field_mappings:
            self.field_mappings[table_name] = {}

        self.field_mappings[table_name][source_field] = target_field
        self.updated_at = datetime.now()

    def is_table_synced(self, base_id: str, table_name: str) -> bool:
        """Check if table is configured for sync"""
        return base_id in self.sync_tables and table_name in self.sync_tables[base_id]


@dataclass
class BrandAsset:
    """Brand asset stored in Airtable brand kit base"""

    asset_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    asset_type: str = ""  # logo, color_palette, template, font, image
    category: str = ""  # primary, secondary, seasonal, specific_use

    # Asset details
    file_url: str = ""
    file_format: str = ""  # png, svg, pdf, jpg, etc.
    file_size: int = 0
    dimensions: dict[str, int] = field(default_factory=dict)  # width, height

    # Usage guidelines
    usage_contexts: list[str] = field(default_factory=list)  # email, social, print, web
    usage_restrictions: list[str] = field(default_factory=list)
    brand_compliance_score: float = 1.0

    # Color information (for color assets)
    color_hex: str = ""
    color_rgb: str = ""
    color_cmyk: str = ""
    color_pantone: str = ""

    # Template information (for template assets)
    template_type: str = ""  # powerpoint, email, social, document
    template_variables: list[str] = field(default_factory=list)
    customization_level: str = "medium"  # low, medium, high

    # Version management
    version: str = "1.0"
    version_notes: str = ""
    supersedes: Optional[str] = None  # Asset ID of previous version

    # Approval and governance
    approval_status: str = "approved"  # draft, pending, approved, deprecated
    approved_by: str = ""
    approval_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "brand_team"
    tags: list[str] = field(default_factory=list)

    def is_approved_for_use(self) -> bool:
        """Check if asset is approved for use"""
        return self.approval_status == "approved"

    def get_usage_guidelines(self) -> dict[str, Any]:
        """Get comprehensive usage guidelines"""
        return {
            "contexts": self.usage_contexts,
            "restrictions": self.usage_restrictions,
            "compliance_score": self.brand_compliance_score,
            "approval_status": self.approval_status,
        }

    def update_approval_status(self, status: str, approver: str, notes: str = ""):
        """Update approval status"""
        self.approval_status = status
        self.approved_by = approver
        self.approval_date = datetime.now()
        self.version_notes = notes
        self.updated_at = datetime.now()


@dataclass
class FoundationalKnowledge:
    """Foundational knowledge entry for Sophia"""

    knowledge_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    category: str = ""  # company, industry, competitive, operational, strategic
    knowledge_type: str = ""  # fact, process, decision_framework, context

    # Content
    content: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)

    # Context and usage
    business_domains: list[str] = field(
        default_factory=list
    )  # marketing, sales, finance
    use_cases: list[str] = field(default_factory=list)
    importance_level: str = "medium"  # critical, high, medium, low
    confidence_level: float = 0.9  # 0.0 to 1.0

    # Sources and validation
    data_sources: list[str] = field(default_factory=list)
    external_references: list[str] = field(default_factory=list)
    validation_status: str = "verified"  # verified, pending, outdated
    last_validated: Optional[datetime] = None

    # Usage tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    sophia_usage_contexts: list[dict[str, Any]] = field(default_factory=list)

    # Relationships
    parent_knowledge: Optional[str] = None  # Parent knowledge ID
    child_knowledge: list[str] = field(default_factory=list)  # Child knowledge IDs
    related_knowledge: list[str] = field(default_factory=list)  # Related knowledge IDs

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "knowledge_team"
    version: int = 1
    tags: list[str] = field(default_factory=list)

    def increment_access(self, context: dict[str, Any] = None):
        """Increment access count and log usage context"""
        self.access_count += 1
        self.last_accessed = datetime.now()

        if context:
            self.sophia_usage_contexts.append(
                {
                    "timestamp": datetime.now(),
                    "context": context,
                    "usage_type": context.get("type", "general"),
                }
            )

            # Keep only last 100 usage contexts
            if len(self.sophia_usage_contexts) > 100:
                self.sophia_usage_contexts = self.sophia_usage_contexts[-100:]

    def add_relationship(self, related_id: str, relationship_type: str):
        """Add relationship to other knowledge entry"""
        if relationship_type == "parent":
            self.parent_knowledge = related_id
        elif relationship_type == "child":
            if related_id not in self.child_knowledge:
                self.child_knowledge.append(related_id)
        elif (
            relationship_type == "related" and related_id not in self.related_knowledge
        ):
            self.related_knowledge.append(related_id)

        self.updated_at = datetime.now()

    def update_validation_status(self, status: str, validator: str = ""):
        """Update knowledge validation status"""
        self.validation_status = status
        self.last_validated = datetime.now()
        self.updated_at = datetime.now()

        if status == "outdated":
            self.confidence_level = max(0.0, self.confidence_level - 0.3)

    def is_current_and_valid(self) -> bool:
        """Check if knowledge is current and validated"""
        if self.validation_status != "verified":
            return False

        if self.confidence_level < 0.6:
            return False

        # Check if validated recently (within 90 days)
        if self.last_validated:
            days_since_validation = (datetime.now() - self.last_validated).days
            return days_since_validation <= 90

        return False


@dataclass
class SyncOperation:
    """Individual synchronization operation"""

    operation_id: str = field(default_factory=lambda: str(uuid4()))
    sync_config_id: str = ""

    # Operation details
    operation_type: str = ""  # create, update, delete, merge
    source_base: str = ""
    target_base: str = ""
    table_name: str = ""
    record_id: str = ""

    # Data
    source_data: dict[str, Any] = field(default_factory=dict)
    target_data: dict[str, Any] = field(default_factory=dict)
    transformed_data: dict[str, Any] = field(default_factory=dict)

    # Status and results
    status: SyncStatus = SyncStatus.PENDING
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3

    # Timing
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Conflict resolution
    conflicts_detected: list[dict[str, Any]] = field(default_factory=list)
    resolution_applied: Optional[str] = None
    manual_review_required: bool = False

    def start_operation(self):
        """Mark operation as started"""
        self.status = SyncStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete_operation(self, success: bool = True, error_message: str = ""):
        """Complete operation with status"""
        self.completed_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()

        if success:
            self.status = SyncStatus.COMPLETED
        else:
            self.status = SyncStatus.FAILED
            self.error_message = error_message

    def add_conflict(self, field_name: str, source_value: Any, target_value: Any):
        """Add data conflict to operation"""
        self.conflicts_detected.append(
            {
                "field": field_name,
                "source_value": source_value,
                "target_value": target_value,
                "detected_at": datetime.now(),
            }
        )
        self.status = SyncStatus.CONFLICT
        self.manual_review_required = True

    def can_retry(self) -> bool:
        """Check if operation can be retried"""
        return self.status == SyncStatus.FAILED and self.retry_count < self.max_retries

    def retry_operation(self):
        """Prepare operation for retry"""
        if self.can_retry():
            self.retry_count += 1
            self.status = SyncStatus.PENDING
            self.error_message = ""
            self.started_at = None
            self.completed_at = None
