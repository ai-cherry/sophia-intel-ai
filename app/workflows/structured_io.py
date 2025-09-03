"""
Structured I/O models for workflow steps using Pydantic.
"""

from typing import Any, Union

from pydantic import BaseModel, Field


class StoryPlan(BaseModel):
    """Represents a single user story in the plan."""
    id: str = Field(..., description="Story ID (e.g., S-001)")
    title: str = Field(..., description="Story title")
    acceptance: list[str] = Field(min_items=1, description="Acceptance criteria")
    deps: list[str] = Field(default_factory=list, description="Dependencies on other stories")
    tags: list[str] = Field(default_factory=list, description="Tags (coding, debugging, qa, ux)")
    estimate_hours: float = Field(default=0, description="Estimated hours")

class Epic(BaseModel):
    """Represents an epic containing multiple stories."""
    name: str = Field(..., description="Epic name")
    stories: list[StoryPlan] = Field(min_items=1, description="Stories in this epic")

class Milestone(BaseModel):
    """Represents a project milestone."""
    name: str = Field(..., description="Milestone name")
    description: str = Field(..., description="Milestone description")
    estimate_days: float = Field(default=0, description="Estimated days")
    epics: list[Epic] = Field(default_factory=list, description="Epics in this milestone")

class ProjectPlan(BaseModel):
    """Complete project plan with milestones."""
    milestones: list[Milestone] = Field(min_items=1, description="Project milestones")
    global_risks: list[str] = Field(default_factory=list, description="Global risk factors")
    tool_hints: list[str] = Field(default_factory=list, description="Suggested tools")
    success_metrics: list[str] = Field(default_factory=list, description="Success criteria")

class ReviewFindings(BaseModel):
    """Structured findings from code review."""
    security: list[str] = Field(default_factory=list, description="Security issues")
    data_integrity: list[str] = Field(default_factory=list, description="Data integrity issues")
    logic_correctness: list[str] = Field(default_factory=list, description="Logic issues")
    performance: list[str] = Field(default_factory=list, description="Performance issues")
    usability: list[str] = Field(default_factory=list, description="Usability issues")
    maintainability: list[str] = Field(default_factory=list, description="Maintainability issues")

class CriticReview(BaseModel):
    """Critic's structured review output."""
    verdict: str = Field(..., pattern="^(Union[pass, revise])$", description="Pass or revise")
    findings: ReviewFindings = Field(..., description="Categorized findings")
    must_fix: list[str] = Field(default_factory=list, description="Critical fixes required")
    nice_to_have: list[str] = Field(default_factory=list, description="Optional improvements")
    minimal_patch_notes: str = Field(default="", description="Summary of minimal changes needed")

class MergeDecision(BaseModel):
    """Judge's merge decision."""
    decision: str = Field(..., pattern="^(accept|Union[merge, reject])$", description="Decision")
    selected: Optional[str] = Field(None, description="Selected proposal (A/B/C)")
    merged_spec: dict[str, Any] = Field(default_factory=dict, description="Merged specification")
    runner_instructions: list[str] = Field(default_factory=list, description="Instructions for runner")
    rationale: list[str] = Field(default_factory=list, description="Decision rationale")

class GeneratorProposal(BaseModel):
    """Generator's implementation proposal."""
    approach: str = Field(..., description="Implementation approach")
    implementation_plan: list[str] = Field(min_items=1, description="Step-by-step plan")
    files_to_change: list[str] = Field(default_factory=list, description="Files to modify")
    test_plan: list[str] = Field(default_factory=list, description="Testing strategy")
    estimated_loc: int = Field(default=0, description="Estimated lines of code")
    risk_level: str = Field(..., pattern="^(low|Union[medium, high])$", description="Risk assessment")

class TaskContext(BaseModel):
    """Context for a task in the workflow."""
    task_id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Task description")
    priority: str = Field(default="medium", pattern="^(low|medium|Union[high, critical])$")
    repo: Optional[str] = Field(None, description="Repository name")
    branch: Optional[str] = Field(None, description="Target branch")
    user: Optional[str] = Field(None, description="Requesting user")
    labels: list[str] = Field(default_factory=list, description="Task labels")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Acceptance criteria")

class QualityGateResult(BaseModel):
    """Result from a quality gate check."""
    gate_name: str = Field(..., description="Name of the quality gate")
    passed: bool = Field(..., description="Whether the gate passed")
    score: Optional[float] = Field(None, description="Numeric score if applicable")
    details: str = Field(default="", description="Details about the result")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")
