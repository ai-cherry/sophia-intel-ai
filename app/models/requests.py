"""
Unified Request/Response Models - Consolidates duplicate classes
found across the codebase (TeamRequest, RunRequest, GlobalState)
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


# =============================================================================
# CORE REQUEST MODELS - Consolidating duplicates found in multiple files
# =============================================================================

class TeamRequest(BaseModel):
    """Unified team execution request - replaces duplicates in debug_server, fixed_server, ultra_server"""
    message: str = Field(..., description="Natural language task description")
    team_id: Optional[str] = Field(None, description="Specific team ID to use")
    session_id: Optional[str] = Field(None, description="User session identifier")
    mode: Optional[str] = Field("balanced", description="Execution mode: lite/balanced/quality")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional execution metadata")


class RunRequest(BaseModel):
    """Unified execution request - consolidates agno_bridge, models/schemas, unified_server, orphan classes"""
    team_id: Optional[str] = Field(None, description="Team identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    workflow_id: Optional[str] = Field(None, description="Workflow identifier")
    task: Optional[str] = Field(None, description="Task description")
    message: Optional[str] = Field(None, description="Natural language message")
    session_id: Optional[str] = Field(None, description="Session tracking ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution metadata")
    timeout: Optional[int] = Field(300, description="Execution timeout in seconds")


class MetadataEntry(BaseModel):
    """Metadata entry for memory and execution tracking"""
    key: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    """Unified memory entry - consolidates different memory models"""
    content: str
    topic: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    memory_type: str = Field("general", description="Memory classification")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Unified search request - consolidates NLP and memory search"""
    query: str
    limit: int = Field(10, ge=1, le=100, description="Max results to return")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    include_metadata: bool = Field(False, description="Include metadata in results")


class WorkflowStatus(BaseModel):
    """Workflow execution status"""
    execution_id: str
    status: str = Field(..., description="Execution status")
    progress: float = Field(0.0, description="Progress percentage")
    result: Optional[Any] = None
    errors: List[str] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps_completed: int = 0
    total_steps: int = 0


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class StandardResponse(BaseModel):
    """Base response structure for consistency"""
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class NLProcessResponse(StandardResponse):
    """Natural language processing response"""
    intent: str
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions: List[str] = Field(default_factory=list)


class ExecutionResponse(StandardResponse):
    """Execution response with result"""
    execution_id: str
    status: str
    result: Optional[Any] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: Optional[float] = None


class SwarmResponse(StandardResponse):
    """Swarm execution response"""
    swarm_id: str
    swarm_type: str
    pattern_used: str
    consensus_score: Optional[float] = None
    debateresult: Optional[Dict[str, Any]] = None


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================

class SystemStatus(BaseModel):
    """Comprehensive system status"""
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = Field("healthy", description="Overall system status")
    version: str = ""
    uptime_seconds: Optional[float] = None
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ComponentHealth(BaseModel):
    """Individual component health status"""
    name: str
    status: str = Field("unknown", description="healthy|degraded|unhealthy")
    last_check: datetime = Field(default_factory=datetime.now)
    response_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# VALIDATION
# =============================================================================

def validate_request_models():
    """Runtime validation of unified request models"""
    try:
        # Test TeamRequest
        team_req = TeamRequest(message="Test request")
        assert team_req.mode == "balanced"

        # Test RunRequest
        run_req = RunRequest(task="Test task")
        assert run_req.timeout == 300

        # Test MemoryEntry
        memory = MemoryEntry(content="test", topic="test", source="test")
        assert memory.memory_type == "general"

        return {"status": "success", "validated_models": ["TeamRequest", "RunRequest", "MemoryEntry"]}

    except Exception as e:
        return {"status": "error", "message": f"Validation failed: {e}"}


if __name__ == "__main__":
    print("Validating unified request models...")
    result = validate_request_models()
    print(f"Validation result: {result}")
