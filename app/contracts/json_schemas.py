"""
JSON Contract Schemas for Planner, Critic, and Judge.
Strict validation with Pydantic V2 for type safety.
"""
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
# ============================================
# Planner Schemas
# ============================================
class Dependency(BaseModel):
    """Task dependency specification."""
    task_id: str = Field(..., description="ID of the dependent task")
    type: Literal["blocks", "informs", "optional"] = Field(
        "blocks", description="Dependency type"
    )
class Story(BaseModel):
    """User story in the plan."""
    id: str = Field(..., pattern=r"^S-\d{3}$", description="Story ID (e.g., S-001)")
    title: str = Field(..., min_length=5, max_length=200)
    acceptance_criteria: list[str] = Field(
        ..., min_length=1, max_length=10, description="Clear pass/fail criteria"
    )
    dependencies: list[Dependency] = Field(default_factory=list)
    tags: list[str] = Field(
        default_factory=list,
        description="Tags: coding, debugging, qa, ux, infrastructure",
    )
    estimate_hours: float = Field(0.5, ge=0.5, le=40)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
class Epic(BaseModel):
    """Epic containing multiple stories."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)
    stories: list[Story] = Field(..., min_length=1)
    @field_validator("stories")
    @classmethod
    def unique_story_ids(cls, v: list[Story]) -> list[Story]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate story IDs found")
        return v
class Milestone(BaseModel):
    """Project milestone."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)
    estimate_days: float = Field(1.0, ge=0.5, le=90)
    epics: list[Epic] = Field(default_factory=list)
    success_criteria: list[str] = Field(
        ..., min_length=1, description="Measurable success criteria"
    )
class PlannerOutput(BaseModel):
    """Complete planner output with validation."""
    milestones: list[Milestone] = Field(..., min_length=1)
    global_risks: list[str] = Field(
        default_factory=list, max_length=10, description="Major risk factors"
    )
    tool_hints: list[str] = Field(
        default_factory=list, description="Suggested tools and libraries"
    )
    success_metrics: list[str] = Field(
        ..., min_length=1, description="Overall success criteria"
    )
    total_estimate_days: float = Field(..., ge=0.5)
    @model_validator(mode="after")
    def calculate_total_estimate(self) -> "PlannerOutput":
        if not self.total_estimate_days:
            self.total_estimate_days = sum(m.estimate_days for m in self.milestones)
        return self
# ============================================
# Critic Schemas
# ============================================
class FindingCategory(str, Enum):
    """Categories of findings."""
    SECURITY = "security"
    DATA_INTEGRITY = "data_integrity"
    LOGIC_CORRECTNESS = "logic_correctness"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
class Findings(BaseModel):
    """Categorized findings from critic review."""
    security: list[str] = Field(default_factory=list, max_length=10)
    data_integrity: list[str] = Field(default_factory=list, max_length=10)
    logic_correctness: list[str] = Field(default_factory=list, max_length=10)
    performance: list[str] = Field(default_factory=list, max_length=10)
    usability: list[str] = Field(default_factory=list, max_length=10)
    maintainability: list[str] = Field(default_factory=list, max_length=10)
    @field_validator("*")
    @classmethod
    def validate_finding_length(cls, v: list[str]) -> list[str]:
        for finding in v:
            if len(finding) < 10:
                raise ValueError(f"Finding too short: {finding}")
            if len(finding) > 500:
                raise ValueError(f"Finding too long: {finding}")
        return v
class CriticOutput(BaseModel):
    """Critic's structured review output with strict validation."""
    verdict: Literal["pass", "revise"] = Field(..., description="Overall verdict")
    findings: Findings = Field(..., description="Categorized findings")
    must_fix: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Critical issues that must be fixed",
    )
    nice_to_have: list[str] = Field(
        default_factory=list, max_length=10, description="Optional improvements"
    )
    minimal_patch_notes: str = Field(
        "", max_length=1000, description="Summary of minimal changes needed"
    )
    confidence_score: float = Field(
        0.8, ge=0.0, le=1.0, description="Confidence in the review (0-1)"
    )
    @model_validator(mode="after")
    def validate_verdict_consistency(self) -> "CriticOutput":
        # If there are must_fix items, verdict should be "revise"
        if self.must_fix and self.verdict == "pass":
            raise ValueError("Verdict cannot be 'pass' with must_fix items")
        # If verdict is "revise", there should be findings or must_fix
        if self.verdict == "revise":
            has_findings = any(
                [
                    self.findings.security,
                    self.findings.data_integrity,
                    self.findings.logic_correctness,
                    self.findings.performance,
                    self.findings.usability,
                    self.findings.maintainability,
                ]
            )
            if not has_findings and not self.must_fix:
                raise ValueError("Verdict 'revise' requires findings or must_fix items")
        return self
# ============================================
# Judge Schemas
# ============================================
class MergeStrategy(str, Enum):
    """Strategy for merging proposals."""
    TAKE_A = "take_a"
    TAKE_B = "take_b"
    TAKE_C = "take_c"
    MERGE_ALL = "merge_all"
    CHERRY_PICK = "cherry_pick"
    CUSTOM = "custom"
class JudgeOutput(BaseModel):
    """Judge's decision output with strict validation."""
    decision: Literal["accept", "merge", "reject"] = Field(
        ..., description="Final decision"
    )
    selected: Optional[str] = Field(
        None, pattern=r"^[A-C]$", description="Selected proposal (A/B/C) if applicable"
    )
    merge_strategy: Optional[MergeStrategy] = Field(
        None, description="How to merge proposals if decision is 'merge'"
    )
    merged_spec: dict[str, Any] = Field(
        default_factory=dict, description="Merged specification if applicable"
    )
    runner_instructions: list[str] = Field(
        default_factory=list,
        min_length=0,
        max_length=20,
        description="Step-by-step instructions for the runner",
    )
    rationale: list[str] = Field(
        ..., min_length=1, max_length=10, description="Reasoning for the decision"
    )
    confidence_score: float = Field(
        0.9, ge=0.0, le=1.0, description="Confidence in the decision (0-1)"
    )
    quality_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Quality score of the proposal (0-10)"
    )
    @model_validator(mode="after")
    def validate_decision_consistency(self) -> "JudgeOutput":
        # Accept/Merge requires runner_instructions
        if self.decision in ["accept", "merge"]:
            if not self.runner_instructions:
                raise ValueError(
                    f"Decision '{self.decision}' requires runner_instructions"
                )
            if len(self.runner_instructions) < 3:
                raise ValueError("Runner instructions should have at least 3 steps")
        # Reject should not have runner_instructions
        if self.decision == "reject" and self.runner_instructions:
            raise ValueError("Decision 'reject' should not have runner_instructions")
        # Merge requires merge_strategy
        if self.decision == "merge" and not self.merge_strategy:
            raise ValueError("Decision 'merge' requires merge_strategy")
        # Selected proposal required for certain strategies
        if self.merge_strategy in [
            MergeStrategy.TAKE_A,
            MergeStrategy.TAKE_B,
            MergeStrategy.TAKE_C,
        ]:
            expected = self.merge_strategy.value[-1].upper()
            if self.selected != expected:
                raise ValueError(
                    f"Strategy {self.merge_strategy} requires selected='{expected}'"
                )
        return self
# ============================================
# Generator Schemas
# ============================================
class GeneratorProposal(BaseModel):
    """Generator's implementation proposal."""
    approach: str = Field(..., min_length=20, max_length=500)
    implementation_plan: list[str] = Field(
        ..., min_length=3, max_length=20, description="Step-by-step implementation plan"
    )
    files_to_change: list[str] = Field(
        default_factory=list, description="List of files that will be modified"
    )
    test_plan: list[str] = Field(..., min_length=1, description="Testing strategy")
    estimated_loc: int = Field(0, ge=0, le=10000)
    risk_level: Literal["low", "medium", "high"] = Field(
        ..., description="Risk assessment"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="External dependencies required"
    )
    rollback_plan: Optional[str] = Field(
        None, max_length=500, description="How to rollback if needed"
    )
# ============================================
# Validation Functions
# ============================================
def validate_planner_output(data: dict[str, Any]) -> PlannerOutput:
    """Validate and parse planner output."""
    try:
        return PlannerOutput.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid planner output: {e}")
def validate_critic_output(data: dict[str, Any]) -> CriticOutput:
    """Validate and parse critic output."""
    try:
        return CriticOutput.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid critic output: {e}")
def validate_judge_output(data: dict[str, Any]) -> JudgeOutput:
    """Validate and parse judge output."""
    try:
        return JudgeOutput.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid judge output: {e}")
def validate_generator_proposal(data: dict[str, Any]) -> GeneratorProposal:
    """Validate and parse generator proposal."""
    try:
        return GeneratorProposal.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid generator proposal: {e}")
# ============================================
# Runner Gate Decision
# ============================================
def runner_gate_decision(
    critic: CriticOutput,
    judge: JudgeOutput,
    accuracy_score: float = 0.0,
    reliability_passed: bool = False,
) -> dict[str, Any]:
    """
    Determine if Runner is allowed to proceed.
    Args:
        critic: Validated critic output
        judge: Validated judge output
        accuracy_score: Score from AccuracyEval (0-10)
        reliability_passed: Whether ReliabilityEval passed
    Returns:
        Gate decision with reasoning
    """
    reasons = []
    allowed = True
    # Check critic verdict
    if critic.verdict == "revise":
        reasons.append("Critic requires revision")
        allowed = False
    # Check judge decision
    if judge.decision == "reject":
        reasons.append("Judge rejected the proposal")
        allowed = False
    elif judge.decision in ["accept", "merge"] and not judge.runner_instructions:
        reasons.append("Judge approved but no runner instructions provided")
        allowed = False
    # Check quality gates
    if accuracy_score < 7.0:
        reasons.append(f"Accuracy score {accuracy_score:.1f} below threshold (7.0)")
        allowed = False
    if not reliability_passed:
        reasons.append("Reliability evaluation failed")
        allowed = False
    # Check confidence scores
    if critic.confidence_score < 0.7:
        reasons.append(f"Critic confidence {critic.confidence_score:.1f} too low")
        allowed = False
    if judge.confidence_score < 0.8:
        reasons.append(f"Judge confidence {judge.confidence_score:.1f} too low")
        allowed = False
    # If all checks pass
    if allowed:
        reasons.append("All quality gates passed")
    return {
        "allowed": allowed,
        "status": "ALLOWED" if allowed else "BLOCKED",
        "reasons": reasons,
        "scores": {
            "accuracy": accuracy_score,
            "reliability": reliability_passed,
            "critic_confidence": critic.confidence_score,
            "judge_confidence": judge.confidence_score,
        },
        "instructions": judge.runner_instructions if allowed else [],
    }
