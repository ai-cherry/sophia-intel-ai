#!/usr/bin/env python3
"""
Document models for the Document Management Swarm
Comprehensive data structures for AI-optimized document handling
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum
import hashlib
import json


class DocumentType(str, Enum):
    """Document type classification"""
    ARCHITECTURE = "architecture"
    API_DOCUMENTATION = "api_documentation"  
    GUIDE = "guide"
    PROMPT = "prompt"
    REPORT = "report"
    README = "readme"
    CONFIGURATION = "configuration"
    AUDIT = "audit"
    DEPLOYMENT = "deployment"
    INTEGRATION = "integration"
    TROUBLESHOOTING = "troubleshooting"
    ONE_TIME = "one_time"
    DEPRECATED = "deprecated"


class DocumentStatus(str, Enum):
    """Document processing status"""
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    CLASSIFIED = "classified" 
    SCORED = "scored"
    INDEXED = "indexed"
    OPTIMIZED = "optimized"
    ARCHIVED = "archived"
    MARKED_FOR_DELETION = "marked_for_deletion"
    FAILED = "failed"


class AIFriendlinessScore(BaseModel):
    """Detailed AI-friendliness scoring breakdown"""
    overall_score: float = Field(0.0, ge=0.0, le=100.0)
    
    # Structure & Clarity (0-25 points)
    structure_score: float = Field(0.0, ge=0.0, le=25.0)
    headings_present: bool = False
    consistent_formatting: bool = False
    clear_sections: bool = False
    
    # Semantic Richness (0-25 points)  
    semantic_score: float = Field(0.0, ge=0.0, le=25.0)
    context_provided: bool = False
    examples_included: bool = False
    cross_references: bool = False
    
    # Technical Accuracy (0-25 points)
    technical_score: float = Field(0.0, ge=0.0, le=25.0)
    code_blocks_formatted: bool = False
    accurate_terminology: bool = False
    up_to_date_content: bool = False
    
    # AI Processing Efficiency (0-25 points)
    processing_score: float = Field(0.0, ge=0.0, le=25.0)
    parseable_structure: bool = False
    consistent_patterns: bool = False
    minimal_ambiguity: bool = False
    
    # Additional metrics
    readability_score: float = 0.0
    completeness_score: float = 0.0
    actionability_score: float = 0.0


class DocumentClassification(BaseModel):
    """Document classification with confidence scores"""
    primary_type: DocumentType
    secondary_types: List[DocumentType] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    
    # Content analysis
    keywords: List[str] = []
    entities: List[str] = []  # Technical entities extracted
    topics: List[str] = []
    
    # Relationship indicators
    dependencies: List[str] = []  # Files this doc depends on
    references: List[str] = []    # Files this doc references
    reverse_refs: List[str] = []  # Files that reference this doc


class DocumentMetadata(BaseModel):
    """Comprehensive document metadata"""
    # Core identification
    id: str = Field(..., description="Unique document identifier")
    source_path: str
    relative_path: str
    filename: str
    file_extension: str
    
    # File system metadata
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    last_accessed_at: Optional[datetime] = None
    content_hash: str
    
    # Processing metadata
    processing_status: DocumentStatus = DocumentStatus.DISCOVERED
    classification: Optional[DocumentClassification] = None
    ai_score: Optional[AIFriendlinessScore] = None
    
    # Content analysis
    line_count: int = 0
    word_count: int = 0
    character_count: int = 0
    language: Optional[str] = None
    
    # AI optimization flags
    needs_restructuring: bool = False
    needs_examples: bool = False
    needs_context: bool = False
    has_code_blocks: bool = False
    has_diagrams: bool = False
    
    # Neural document network connections
    connection_strength: Dict[str, float] = {}
    access_patterns: List[Dict[str, Any]] = []
    
    # Custom metadata
    custom_fields: Dict[str, Any] = {}

    @validator('content_hash', pre=True, always=True)
    def calculate_hash(cls, v, values):
        if not v and 'source_path' in values:
            # Will be calculated during processing
            return ""
        return v


class CleanupPolicy(BaseModel):
    """Automated cleanup policy configuration"""
    id: str
    name: str
    description: str
    
    # Policy conditions (all must be true)
    conditions: Dict[str, Any] = {}  # e.g., {"age_days": {"$gt": 30}, "ai_score": {"$lt": 50}}
    
    # Policy actions
    action: str  # "archive", "delete", "compress", "consolidate"
    backup_before_action: bool = True
    require_confirmation: bool = True
    
    # Safety checks
    safety_checks: List[str] = ["recent_access", "dependency_check", "git_history"]
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_applied: Optional[datetime] = None
    application_count: int = 0


class DocumentProcessingResult(BaseModel):
    """Result of document processing operations"""
    document_id: str
    operation: str
    success: bool
    
    # Processing details
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Results
    changes_made: List[str] = []
    errors: List[str] = []
    warnings: List[str] = []
    
    # Metrics
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    improvement_score: Optional[float] = None
    
    # Additional data
    metadata: Dict[str, Any] = {}


class DocumentBatch(BaseModel):
    """Batch of documents for processing"""
    batch_id: str
    documents: List[str]  # Document IDs
    operation: str
    
    # Batch configuration
    parallel_workers: int = 5
    timeout_seconds: int = 300
    
    # Status tracking
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    successful_docs: List[str] = []
    failed_docs: List[str] = []
    results: List[DocumentProcessingResult] = []


class DocumentNetwork(BaseModel):
    """Neural document network representation"""
    network_id: str
    documents: Set[str]  # Document IDs in this network
    
    # Network properties
    connection_matrix: Dict[str, Dict[str, float]] = {}  # doc_id -> {doc_id: strength}
    activation_patterns: List[Dict[str, Any]] = []
    learning_rate: float = 0.1
    
    # Network health
    coherence_score: float = 0.0
    stability_score: float = 0.0
    performance_metrics: Dict[str, float] = {}
    
    # Evolution tracking
    generation: int = 1
    mutation_rate: float = 0.05
    fitness_score: float = 0.0


class DocumentSwarmState(BaseModel):
    """Current state of the document swarm"""
    swarm_id: str = "document_management_swarm"
    
    # Swarm composition
    active_agents: List[str] = []
    agent_specializations: Dict[str, List[str]] = {}
    
    # Processing queues
    discovery_queue: List[str] = []
    classification_queue: List[str] = []
    optimization_queue: List[str] = []
    cleanup_queue: List[str] = []
    
    # Swarm intelligence
    collective_knowledge: Dict[str, Any] = {}
    pheromone_trails: Dict[str, float] = {}  # path -> strength
    emergent_patterns: List[Dict[str, Any]] = []
    
    # Performance metrics
    docs_processed_per_hour: float = 0.0
    average_quality_improvement: float = 0.0
    error_rate: float = 0.0
    
    # Status
    last_updated: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


# Utility functions
def calculate_document_hash(content: str) -> str:
    """Calculate SHA-256 hash of document content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_metadata_from_path(file_path: str) -> Dict[str, Any]:
    """Extract metadata from file path patterns"""
    import os
    from pathlib import Path
    
    path = Path(file_path)
    metadata = {
        'filename': path.name,
        'file_extension': path.suffix.lower(),
        'relative_path': str(path.relative_to(Path.cwd())) if path.is_absolute() else str(path),
        'directory_depth': len(path.parts) - 1,
        'parent_directory': path.parent.name,
    }
    
    # Infer type from path patterns
    if 'README' in path.name.upper():
        metadata['inferred_type'] = DocumentType.README
    elif path.name.lower().endswith('_prompt.md'):
        metadata['inferred_type'] = DocumentType.PROMPT
    elif 'audit' in path.name.lower():
        metadata['inferred_type'] = DocumentType.AUDIT
    elif 'deployment' in path.name.lower():
        metadata['inferred_type'] = DocumentType.DEPLOYMENT
    elif 'architecture' in path.name.lower():
        metadata['inferred_type'] = DocumentType.ARCHITECTURE
    elif 'report' in path.name.lower():
        metadata['inferred_type'] = DocumentType.REPORT
    
    return metadata


def is_likely_one_time_document(filename: str, content: str = "") -> bool:
    """Heuristics to identify one-time documents"""
    one_time_indicators = [
        'status_report', 'deployment_status', 'audit_report', 
        '_report_', 'test_results', 'migration_report',
        'cleanup_report', 'summary_report', 'handoff',
        'current', 'latest', 'final_'
    ]
    
    filename_lower = filename.lower()
    return any(indicator in filename_lower for indicator in one_time_indicators)


def calculate_document_importance(metadata: DocumentMetadata) -> float:
    """Calculate document importance score (0-1)"""
    importance = 0.0
    
    # File type importance
    type_weights = {
        DocumentType.ARCHITECTURE: 0.9,
        DocumentType.API_DOCUMENTATION: 0.8,
        DocumentType.README: 0.7,
        DocumentType.GUIDE: 0.7,
        DocumentType.CONFIGURATION: 0.6,
        DocumentType.INTEGRATION: 0.6,
        DocumentType.TROUBLESHOOTING: 0.5,
        DocumentType.REPORT: 0.3,
        DocumentType.AUDIT: 0.2,
        DocumentType.ONE_TIME: 0.1,
        DocumentType.DEPRECATED: 0.05,
    }
    
    if metadata.classification:
        importance += type_weights.get(metadata.classification.primary_type, 0.3)
    
    # AI-friendliness score influence
    if metadata.ai_score:
        importance += (metadata.ai_score.overall_score / 100) * 0.3
    
    # Recency influence (decay over time)
    days_old = (datetime.now() - metadata.modified_at).days
    recency_factor = max(0.1, 1.0 - (days_old / 365))  # Decay over a year
    importance *= recency_factor
    
    # Access patterns influence
    if metadata.access_patterns:
        recent_access = any(
            (datetime.now() - datetime.fromisoformat(pattern.get('timestamp', '2020-01-01T00:00:00')))
            .days < 30 
            for pattern in metadata.access_patterns
        )
        if recent_access:
            importance *= 1.2
    
    return min(1.0, importance)