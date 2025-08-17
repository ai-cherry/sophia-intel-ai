"""
Intelligence Domain Models - AI-powered development and architecture models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CodeGenerationType(str, Enum):
    """Code generation type enumeration"""
    ENDPOINT = "endpoint"
    SERVICE = "service"
    MODEL = "model"
    TEST = "test"
    DOCUMENTATION = "documentation"
    MIGRATION = "migration"
    COMPONENT = "component"


class ArchitectureDecision(str, Enum):
    """Architecture decision enumeration"""
    USE_ORCHESTRATOR = "use_orchestrator"
    USE_SWARM = "use_swarm"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    IMPROVE_RELIABILITY = "improve_reliability"


class ImprovementType(str, Enum):
    """Improvement type enumeration"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    CODE_QUALITY = "code_quality"


class CodeGenerationRequest(BaseModel):
    """Request for AI code generation"""
    generation_type: CodeGenerationType = Field(..., description="Type of code to generate")
    description: str = Field(..., description="Description of what to generate")
    
    # Context
    existing_code: Optional[str] = Field(None, description="Existing code for reference")
    schema: Optional[Dict[str, Any]] = Field(None, description="Schema or structure definition")
    requirements: List[str] = Field(default_factory=list, description="Specific requirements")
    
    # Generation options
    include_tests: bool = Field(True, description="Generate tests alongside code")
    include_documentation: bool = Field(True, description="Generate documentation")
    follow_patterns: bool = Field(True, description="Follow existing code patterns")
    
    # Target configuration
    target_file: Optional[str] = Field(None, description="Target file path")
    target_directory: Optional[str] = Field(None, description="Target directory")
    programming_language: str = Field("python", description="Programming language")
    framework: Optional[str] = Field(None, description="Framework to use")
    
    # Quality settings
    complexity_level: str = Field("standard", description="Complexity: simple, standard, advanced")
    performance_focus: bool = Field(False, description="Focus on performance optimization")
    security_focus: bool = Field(True, description="Focus on security best practices")


class CodeGenerationResponse(BaseModel):
    """Response from AI code generation"""
    success: bool = Field(..., description="Generation success status")
    generated_code: Optional[str] = Field(None, description="Generated code")
    generated_tests: Optional[str] = Field(None, description="Generated test code")
    generated_docs: Optional[str] = Field(None, description="Generated documentation")
    
    # File information
    files_created: List[str] = Field(default_factory=list, description="Created file paths")
    files_modified: List[str] = Field(default_factory=list, description="Modified file paths")
    
    # Generation metadata
    generation_time: float = Field(..., description="Generation time in seconds")
    model_used: str = Field(..., description="AI model used for generation")
    tokens_used: int = Field(..., description="Tokens consumed")
    
    # Quality metrics
    complexity_score: float = Field(..., description="Code complexity score")
    quality_score: float = Field(..., description="Code quality score")
    security_score: float = Field(..., description="Security score")
    
    # Suggestions
    improvements: List[str] = Field(default_factory=list, description="Improvement suggestions")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ArchitectureAnalysis(BaseModel):
    """Architecture analysis and recommendations"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Current state
    current_load: float = Field(..., description="Current system load (0-1)")
    response_times: Dict[str, float] = Field(..., description="Response times by service")
    error_rates: Dict[str, float] = Field(..., description="Error rates by service")
    resource_usage: Dict[str, float] = Field(..., description="Resource usage metrics")
    
    # Performance analysis
    bottlenecks: List[str] = Field(default_factory=list, description="Identified bottlenecks")
    optimization_opportunities: List[str] = Field(default_factory=list, description="Optimization opportunities")
    
    # Recommendations
    recommended_decision: ArchitectureDecision = Field(..., description="Recommended architecture decision")
    confidence_score: float = Field(..., description="Recommendation confidence (0-1)")
    reasoning: str = Field(..., description="Reasoning for recommendation")
    
    # Alternative options
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative decisions")
    
    # Impact assessment
    expected_improvement: float = Field(..., description="Expected performance improvement")
    implementation_effort: str = Field(..., description="Implementation effort: low, medium, high")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    
    # Historical context
    previous_decisions: List[str] = Field(default_factory=list, description="Previous architecture decisions")
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict, description="Performance trends")


class ImprovementSuggestion(BaseModel):
    """Continuous improvement suggestion"""
    suggestion_id: str = Field(..., description="Unique suggestion identifier")
    improvement_type: ImprovementType = Field(..., description="Type of improvement")
    
    # Problem identification
    issue_description: str = Field(..., description="Description of the issue")
    affected_components: List[str] = Field(..., description="Affected system components")
    severity: str = Field(..., description="Severity: low, medium, high, critical")
    
    # Solution
    suggested_solution: str = Field(..., description="Suggested solution")
    implementation_steps: List[str] = Field(..., description="Implementation steps")
    code_changes: Optional[str] = Field(None, description="Suggested code changes")
    
    # Impact assessment
    expected_benefit: str = Field(..., description="Expected benefit")
    implementation_effort: str = Field(..., description="Implementation effort")
    risk_assessment: str = Field(..., description="Risk assessment")
    
    # Metrics
    priority_score: float = Field(..., description="Priority score (0-1)")
    confidence_score: float = Field(..., description="Confidence in suggestion (0-1)")
    
    # Context
    detected_at: datetime = Field(default_factory=datetime.now)
    detection_method: str = Field(..., description="How the issue was detected")
    related_metrics: Dict[str, Any] = Field(default_factory=dict, description="Related performance metrics")
    
    # Status tracking
    status: str = Field("pending", description="Status: pending, approved, implemented, rejected")
    implemented_at: Optional[datetime] = Field(None, description="Implementation timestamp")
    implementation_result: Optional[str] = Field(None, description="Implementation result")


class IntelligencePipelineConfig(BaseModel):
    """Configuration for intelligence pipeline"""
    # Code generation settings
    auto_generate_tests: bool = Field(True, description="Automatically generate tests")
    auto_generate_docs: bool = Field(True, description="Automatically generate documentation")
    code_quality_threshold: float = Field(0.8, description="Minimum code quality score")
    
    # Architecture adaptation settings
    analysis_interval: int = Field(300, description="Analysis interval in seconds")
    adaptation_threshold: float = Field(0.7, description="Threshold for automatic adaptation")
    require_approval: bool = Field(True, description="Require approval for architecture changes")
    
    # Improvement settings
    improvement_scan_interval: int = Field(3600, description="Improvement scan interval in seconds")
    auto_implement_low_risk: bool = Field(False, description="Auto-implement low-risk improvements")
    priority_threshold: float = Field(0.6, description="Minimum priority for suggestions")
    
    # AI model settings
    code_generation_model: str = Field("claude-3-5-sonnet-20241022", description="Model for code generation")
    analysis_model: str = Field("gpt-4", description="Model for architecture analysis")
    improvement_model: str = Field("claude-3-5-sonnet-20241022", description="Model for improvement suggestions")
    
    # Performance settings
    max_concurrent_operations: int = Field(5, description="Maximum concurrent operations")
    operation_timeout: int = Field(300, description="Operation timeout in seconds")
    cache_results: bool = Field(True, description="Cache analysis results")
    cache_ttl: int = Field(1800, description="Cache TTL in seconds")


class IntelligenceMetrics(BaseModel):
    """Intelligence pipeline metrics"""
    # Code generation metrics
    total_code_generations: int = Field(0, description="Total code generations")
    successful_generations: int = Field(0, description="Successful generations")
    average_generation_time: float = Field(0.0, description="Average generation time")
    average_quality_score: float = Field(0.0, description="Average quality score")
    
    # Architecture adaptation metrics
    total_analyses: int = Field(0, description="Total architecture analyses")
    adaptations_recommended: int = Field(0, description="Adaptations recommended")
    adaptations_implemented: int = Field(0, description="Adaptations implemented")
    average_improvement: float = Field(0.0, description="Average performance improvement")
    
    # Improvement metrics
    total_suggestions: int = Field(0, description="Total improvement suggestions")
    suggestions_implemented: int = Field(0, description="Suggestions implemented")
    average_priority_score: float = Field(0.0, description="Average priority score")
    
    # Performance metrics
    pipeline_uptime: float = Field(0.0, description="Pipeline uptime percentage")
    average_response_time: float = Field(0.0, description="Average response time")
    error_rate: float = Field(0.0, description="Error rate percentage")
    
    # Resource usage
    cpu_usage: float = Field(0.0, description="CPU usage percentage")
    memory_usage: float = Field(0.0, description="Memory usage percentage")
    tokens_consumed: int = Field(0, description="Total tokens consumed")
    
    # Timestamp
    last_updated: datetime = Field(default_factory=datetime.now)


class ContextAwareRequest(BaseModel):
    """Context-aware development request"""
    request_id: str = Field(..., description="Unique request identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    # Request details
    request_type: str = Field(..., description="Type of request")
    description: str = Field(..., description="Request description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Request context")
    
    # Project context
    project_files: List[str] = Field(default_factory=list, description="Relevant project files")
    current_architecture: Optional[str] = Field(None, description="Current architecture description")
    recent_changes: List[str] = Field(default_factory=list, description="Recent changes")
    
    # User preferences
    coding_style: Optional[str] = Field(None, description="Preferred coding style")
    frameworks: List[str] = Field(default_factory=list, description="Preferred frameworks")
    patterns: List[str] = Field(default_factory=list, description="Preferred patterns")
    
    # Requirements
    performance_requirements: Optional[str] = Field(None, description="Performance requirements")
    security_requirements: Optional[str] = Field(None, description="Security requirements")
    scalability_requirements: Optional[str] = Field(None, description="Scalability requirements")


class MultiModalInput(BaseModel):
    """Multi-modal input for development requests"""
    # Text input
    text_description: Optional[str] = Field(None, description="Text description")
    
    # Voice input
    voice_audio_url: Optional[str] = Field(None, description="Voice audio URL")
    voice_transcript: Optional[str] = Field(None, description="Voice transcript")
    
    # Visual input
    diagram_image_url: Optional[str] = Field(None, description="Diagram image URL")
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")
    visual_description: Optional[str] = Field(None, description="Visual description")
    
    # Code input
    existing_code: Optional[str] = Field(None, description="Existing code")
    code_files: List[str] = Field(default_factory=list, description="Code file paths")
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.now)
    processing_model: Optional[str] = Field(None, description="Model used for processing")
    confidence_score: Optional[float] = Field(None, description="Processing confidence")

