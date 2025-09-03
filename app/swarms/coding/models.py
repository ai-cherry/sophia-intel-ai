"""
Typed models for Coding Swarm results and configurations.

This module defines Pydantic models for all swarm inputs and outputs,
ensuring type safety and validation throughout the system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class PoolType(str, Enum):
    """Available model pools for generator agents."""
    FAST = "fast"
    BALANCED = "balanced"
    HEAVY = "heavy"


class CriticVerdict(str, Enum):
    """Possible verdicts from the critic agent."""
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"


class JudgeDecision(str, Enum):
    """Possible decisions from the judge agent."""
    ACCEPT = "accept"
    MERGE = "merge"
    REJECT = "reject"


class RiskLevel(str, Enum):
    """Risk levels for generated code."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class CriticOutput(BaseModel):
    """Structured output from the Critic agent."""
    verdict: CriticVerdict
    findings: Dict[str, List[str]] = Field(default_factory=dict)
    must_fix: List[str] = Field(default_factory=list)
    nice_to_have: List[str] = Field(default_factory=list, alias="nice_to_haves")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = ConfigDict(populate_by_name=True)


class JudgeOutput(BaseModel):
    """Structured output from the Judge agent."""
    decision: JudgeDecision
    runner_instructions: List[str] = Field(default_factory=list)
    rationale: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_assessment: Optional[RiskLevel] = None


class GateDecision(BaseModel):
    """Runner gate decision based on critic and judge outputs."""
    allowed: bool
    reason: str
    accuracy_score: float = Field(ge=0.0, le=10.0)
    reliability_passed: bool
    risk_level: RiskLevel
    requires_approval: bool = False
    approval_actions: List[str] = Field(default_factory=list)


class GeneratorProposal(BaseModel):
    """Proposal from a generator agent."""
    agent_name: str
    approach: str
    code_changes: str
    test_code: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    tools_used: List[str] = Field(default_factory=list)


class DebateResult(BaseModel):
    """Complete result from a coding swarm debate."""
    task: str
    team_id: Optional[str] = None
    session_id: Optional[str] = None

    # Agent outputs
    proposals: List[GeneratorProposal] = Field(default_factory=list)
    critic: Optional[CriticOutput] = None
    judge: Optional[JudgeOutput] = None

    # Validation status
    critic_validated: bool = False
    judge_validated: bool = False

    # Gate decision
    gate_decision: Optional[GateDecision] = None
    runner_approved: bool = False

    # Metadata
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Memory integration
    memory_entries_created: List[str] = Field(default_factory=list)
    related_memories: List[str] = Field(default_factory=list)


class SwarmConfiguration(BaseModel):
    """Configuration for creating and running a coding swarm."""
    # Team composition
    pool: PoolType = PoolType.BALANCED
    concurrent_models: List[str] = Field(default_factory=list)
    include_default_pair: bool = True
    include_runner: bool = False
    max_generators: int = Field(default=4, ge=1, le=10)

    # Execution settings
    max_rounds: int = Field(default=3, ge=1, le=10)
    stream_responses: bool = False
    timeout_seconds: int = Field(default=300, ge=30, le=1800)

    # Evaluation gates
    accuracy_threshold: float = Field(default=7.0, ge=0.0, le=10.0)
    reliability_checks_enabled: bool = True
    auto_approve_low_risk: bool = False

    # Memory integration
    use_memory: bool = True
    memory_search_limit: int = Field(default=5, ge=0, le=20)
    store_results: bool = True

    # Tool access
    enable_file_write: bool = False
    enable_test_execution: bool = True
    enable_git_operations: bool = False

    model_config = ConfigDict(use_enum_values=True)


class SwarmRequest(BaseModel):
    """Request to execute a coding swarm."""
    task: str = Field(..., min_length=1, max_length=10000)
    configuration: SwarmConfiguration = Field(default_factory=SwarmConfiguration)
    context: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    team_id: Optional[str] = None
