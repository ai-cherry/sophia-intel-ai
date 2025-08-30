"""
Structured I/O models for workflow steps using Pydantic.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StoryPlan(BaseModel):
    """Represents a single user story in the plan."""
    id: str = Field(..., description="Story ID (e.g., S-001)")
    title: str = Field(..., description="Story title")
    acceptance: List[str] = Field(min_items=1, description="Acceptance criteria")
    deps: List[str] = Field(default_factory=list, description="Dependencies on other stories")
    tags: List[str] = Field(default_factory=list, description="Tags (coding, debugging, qa, ux)")
    estimate_hours: float = Field(default=0, description="Estimated hours")

class Epic(BaseModel):
    """Represents an epic containing multiple stories."""
    name: str = Field(..., description="Epic name")
    stories: List[StoryPlan] = Field(min_items=1, description="Stories in this epic")

class Milestone(BaseModel):
    """Represents a project milestone."""
    name: str = Field(..., description="Milestone name")
    description: str = Field(..., description="Milestone description")
    estimate_days: float = Field(default=0, description="Estimated days")
    epics: List[Epic] = Field(default_factory=list, description="Epics in this milestone")

class ProjectPlan(BaseModel):
    """Complete project plan with milestones."""
    milestones: List[Milestone] = Field(min_items=1, description="Project milestones")
    global_risks: List[str] = Field(default_factory=list, description="Global risk factors")
    tool_hints: List[str] = Field(default_factory=list, description="Suggested tools")
    success_metrics: List[str] = Field(default_factory=list, description="Success criteria")

class ReviewFindings(BaseModel):
    """Structured findings from code review."""
    security: List[str] = Field(default_factory=list, description="Security issues")
    data_integrity: List[str] = Field(default_factory=list, description="Data integrity issues")
    logic_correctness: List[str] = Field(default_factory=list, description="Logic issues")
    performance: List[str] = Field(default_factory=list, description="Performance issues")
    usability: List[str] = Field(default_factory=list, description="Usability issues")
    maintainability: List[str] = Field(default_factory=list, description="Maintainability issues")

class CriticReview(BaseModel):
    """Critic's structured review output."""
    verdict: str = Field(..., pattern="^(pass|revise)$", description="Pass or revise")
    findings: ReviewFindings = Field(..., description="Categorized findings")
    must_fix: List[str] = Field(default_factory=list, description="Critical fixes required")
    nice_to_have: List[str] = Field(default_factory=list, description="Optional improvements")
    minimal_patch_notes: str = Field(default="", description="Summary of minimal changes needed")

class MergeDecision(BaseModel):
    """Judge's merge decision."""
    decision: str = Field(..., pattern="^(accept|merge|reject)$", description="Decision")
    selected: Optional[str] = Field(None, description="Selected proposal (A/B/C)")
    merged_spec: Dict[str, Any] = Field(default_factory=dict, description="Merged specification")
    runner_instructions: List[str] = Field(default_factory=list, description="Instructions for runner")
    rationale: List[str] = Field(default_factory=list, description="Decision rationale")

class GeneratorProposal(BaseModel):
    """Generator's implementation proposal."""
    approach: str = Field(..., description="Implementation approach")
    implementation_plan: List[str] = Field(min_items=1, description="Step-by-step plan")
    files_to_change: List[str] = Field(default_factory=list, description="Files to modify")
    test_plan: List[str] = Field(default_factory=list, description="Testing strategy")
    estimated_loc: int = Field(default=0, description="Estimated lines of code")
    risk_level: str = Field(..., pattern="^(low|medium|high)$", description="Risk assessment")

class TaskContext(BaseModel):
    """Context for a task in the workflow."""
    task_id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Task description")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    repo: Optional[str] = Field(None, description="Repository name")
    branch: Optional[str] = Field(None, description="Target branch")
    user: Optional[str] = Field(None, description="Requesting user")
    labels: List[str] = Field(default_factory=list, description="Task labels")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria")

class QualityGateResult(BaseModel):
    """Result from a quality gate check."""
    gate_name: str = Field(..., description="Name of the quality gate")
    passed: bool = Field(..., description="Whether the gate passed")
    score: Optional[float] = Field(None, description="Numeric score if applicable")
    details: str = Field(default="", description="Details about the result")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")