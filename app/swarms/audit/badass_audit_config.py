"""
Badass Audit Swarm Configuration
Leveraging premium models for comprehensive codebase analysis
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModelTier(Enum):
    """Model performance tiers"""

    ULTRA = "ultra"  # 500B+ tokens - For critical analysis
    PREMIUM = "premium"  # 100B+ tokens - For complex reasoning
    BALANCED = "balanced"  # 50B+ tokens - For standard analysis
    FAST = "fast"  # For quick iterations


# Premium model roster with specialized assignments
BADASS_MODEL_ASSIGNMENTS = {
    # Ultra-tier models for critical analysis
    "chief_architect": "x-ai/grok-code-fast-1",  # 693B - Ultimate code analysis
    "security_commander": "anthropic/claude-sonnet-4",  # 539B - Security expertise
    "performance_guru": "google/gemini-2.5-flash",  # 471B - Performance analysis
    "quality_overlord": "google/gemini-2.0-flash",  # 206B - Quality assessment
    "integration_master": "google/gemini-2.5-pro",  # 180B - Integration testing
    # Premium tier for specialized analysis
    "deepcode_analyzer": "deepseek/deepseek-chat-v3-0324",  # 150B - Deep code analysis
    "strategic_planner": "qwen/qwen3-30b-a3b",  # 136B - Strategic planning
    "vulnerability_hunter": "deepseek/deepseek-chat-v3.1",  # 104B - Security vulnerabilities
    "code_architect": "qwen/qwen3-coder-480b-a35b",  # 87.4B - Code architecture
    "system_critic": "anthropic/claude-3.7-sonnet",  # 82.3B - Critical analysis
    "infrastructure_expert": "openai/gpt-5",  # 74.2B - Infrastructure review
    # Balanced tier for collaborative work
    "consensus_builder": "google/gemini-2.5-flash-lite",  # 67.7B - Consensus building
    "debate_moderator": "deepseek/r1-0528:free",  # 63.7B - Debate moderation
    "compliance_officer": "openai/gpt-4.1-mini",  # 55.1B - Compliance review
    "deployment_specialist": "mistralai/mistral-nemo",  # 53.6B - Deployment analysis
    "test_commander": "deepseek/deepseek-chat-v3-0324:free",  # 52.9B - Testing strategy
    # Fast tier for rapid iterations
    "rapid_scanner": "openai/gpt-4o-mini",  # 50.2B - Quick scans
    "pattern_detector": "openai/gpt-oss-120b",  # 45.9B - Pattern detection
    "code_reviewer": "z-ai/glm-4.5",  # 41.2B - Code review
    "final_validator": "openai/gpt-4.1",  # 40.4B - Final validation
    # Strategic Planning Specialists (New)
    "strategic_commander": "openai/gpt-5",  # Strategic oversight
    "environmental_scanner": "anthropic/claude-sonnet-4",  # Environmental analysis
    "scenario_modeler": "google/gemini-2.5-pro",  # Scenario forecasting
    "trend_analyst": "deepseek/deepseek-chat-v3.1",  # Trend analysis
    "predictive_planner": "x-ai/grok-code-fast-1",  # Predictive modeling
    "adaptation_agent": "qwen/qwen3-30b-a3b",  # Dynamic adaptation
}


@dataclass
class AgentSpec:
    """Specification for a specialized audit agent"""

    name: str
    role: str
    model: str
    specialization: list[str]
    confidence_threshold: float
    collaboration_style: str  # "leader", "collaborator", "specialist", "critic"
    debate_tendency: float  # 0.0-1.0 how likely to initiate debates
    consensus_weight: float  # Weight in consensus decisions


# Badass agent specifications
BADASS_AGENTS = {
    # Leadership tier - Strategic oversight
    "chief_architect": AgentSpec(
        name="Chief Technical Architect",
        role="strategic_oversight",
        model=BADASS_MODEL_ASSIGNMENTS["chief_architect"],
        specialization=[
            "system_architecture",
            "technical_strategy",
            "scalability",
            "design_patterns",
        ],
        confidence_threshold=0.95,
        collaboration_style="leader",
        debate_tendency=0.8,
        consensus_weight=1.5,
    ),
    "security_commander": AgentSpec(
        name="Security Operations Commander",
        role="security_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["security_commander"],
        specialization=[
            "threat_modeling",
            "vulnerability_assessment",
            "compliance",
            "cryptography",
        ],
        confidence_threshold=0.98,
        collaboration_style="specialist",
        debate_tendency=0.9,
        consensus_weight=2.0,  # Security findings have higher weight
    ),
    # Analysis specialists
    "performance_guru": AgentSpec(
        name="Performance Engineering Guru",
        role="performance_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["performance_guru"],
        specialization=[
            "performance_profiling",
            "optimization",
            "scalability",
            "resource_management",
        ],
        confidence_threshold=0.90,
        collaboration_style="specialist",
        debate_tendency=0.7,
        consensus_weight=1.3,
    ),
    "quality_overlord": AgentSpec(
        name="Code Quality Overlord",
        role="quality_assessment",
        model=BADASS_MODEL_ASSIGNMENTS["quality_overlord"],
        specialization=[
            "code_quality",
            "best_practices",
            "maintainability",
            "technical_debt",
        ],
        confidence_threshold=0.88,
        collaboration_style="critic",
        debate_tendency=0.85,
        consensus_weight=1.2,
    ),
    "deepcode_analyzer": AgentSpec(
        name="Deep Code Analysis Engine",
        role="deep_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["deepcode_analyzer"],
        specialization=[
            "static_analysis",
            "code_complexity",
            "dependency_analysis",
            "refactoring",
        ],
        confidence_threshold=0.92,
        collaboration_style="specialist",
        debate_tendency=0.6,
        consensus_weight=1.4,
    ),
    "vulnerability_hunter": AgentSpec(
        name="Vulnerability Hunter",
        role="security_scanning",
        model=BADASS_MODEL_ASSIGNMENTS["vulnerability_hunter"],
        specialization=[
            "cve_analysis",
            "dependency_scanning",
            "code_injection",
            "data_leaks",
        ],
        confidence_threshold=0.94,
        collaboration_style="specialist",
        debate_tendency=0.75,
        consensus_weight=1.8,
    ),
    # Integration and testing specialists
    "integration_master": AgentSpec(
        name="Integration Testing Master",
        role="integration_testing",
        model=BADASS_MODEL_ASSIGNMENTS["integration_master"],
        specialization=[
            "api_testing",
            "contract_testing",
            "e2e_testing",
            "data_validation",
        ],
        confidence_threshold=0.87,
        collaboration_style="collaborator",
        debate_tendency=0.5,
        consensus_weight=1.1,
    ),
    "test_commander": AgentSpec(
        name="Test Strategy Commander",
        role="test_strategy",
        model=BADASS_MODEL_ASSIGNMENTS["test_commander"],
        specialization=[
            "test_coverage",
            "test_automation",
            "qa_processes",
            "regression_testing",
        ],
        confidence_threshold=0.85,
        collaboration_style="collaborator",
        debate_tendency=0.4,
        consensus_weight=1.0,
    ),
    # Infrastructure and deployment
    "infrastructure_expert": AgentSpec(
        name="Infrastructure Engineering Expert",
        role="infrastructure_review",
        model=BADASS_MODEL_ASSIGNMENTS["infrastructure_expert"],
        specialization=[
            "cloud_architecture",
            "containerization",
            "ci_cd",
            "monitoring",
        ],
        confidence_threshold=0.89,
        collaboration_style="specialist",
        debate_tendency=0.6,
        consensus_weight=1.3,
    ),
    "deployment_specialist": AgentSpec(
        name="Deployment Operations Specialist",
        role="deployment_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["deployment_specialist"],
        specialization=[
            "deployment_pipelines",
            "rollback_strategies",
            "blue_green",
            "canary_deployments",
        ],
        confidence_threshold=0.84,
        collaboration_style="collaborator",
        debate_tendency=0.3,
        consensus_weight=1.0,
    ),
    # Collaboration and synthesis agents
    "consensus_builder": AgentSpec(
        name="Consensus Building Engine",
        role="consensus_coordination",
        model=BADASS_MODEL_ASSIGNMENTS["consensus_builder"],
        specialization=[
            "conflict_resolution",
            "decision_synthesis",
            "stakeholder_alignment",
        ],
        confidence_threshold=0.80,
        collaboration_style="collaborator",
        debate_tendency=0.2,
        consensus_weight=0.8,  # Facilitator, not decision maker
    ),
    "debate_moderator": AgentSpec(
        name="Technical Debate Moderator",
        role="debate_facilitation",
        model=BADASS_MODEL_ASSIGNMENTS["debate_moderator"],
        specialization=[
            "argumentation_analysis",
            "evidence_evaluation",
            "bias_detection",
        ],
        confidence_threshold=0.85,
        collaboration_style="collaborator",
        debate_tendency=0.1,  # Moderates, doesn't initiate
        consensus_weight=0.5,
    ),
    # Rapid response agents
    "rapid_scanner": AgentSpec(
        name="Rapid Issue Scanner",
        role="quick_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["rapid_scanner"],
        specialization=[
            "issue_detection",
            "quick_scans",
            "triage",
            "priority_assessment",
        ],
        confidence_threshold=0.75,
        collaboration_style="collaborator",
        debate_tendency=0.3,
        consensus_weight=0.8,
    ),
    "pattern_detector": AgentSpec(
        name="Anti-Pattern Detection Engine",
        role="pattern_analysis",
        model=BADASS_MODEL_ASSIGNMENTS["pattern_detector"],
        specialization=[
            "anti_patterns",
            "code_smells",
            "architectural_patterns",
            "design_violations",
        ],
        confidence_threshold=0.82,
        collaboration_style="specialist",
        debate_tendency=0.65,
        consensus_weight=1.1,
    ),
    "compliance_officer": AgentSpec(
        name="Compliance Assessment Officer",
        role="compliance_review",
        model=BADASS_MODEL_ASSIGNMENTS["compliance_officer"],
        specialization=[
            "regulatory_compliance",
            "standards_adherence",
            "audit_trails",
            "documentation",
        ],
        confidence_threshold=0.90,
        collaboration_style="specialist",
        debate_tendency=0.4,
        consensus_weight=1.2,
    ),
    "final_validator": AgentSpec(
        name="Final Report Validator",
        role="report_validation",
        model=BADASS_MODEL_ASSIGNMENTS["final_validator"],
        specialization=[
            "report_synthesis",
            "executive_summary",
            "recommendation_prioritization",
        ],
        confidence_threshold=0.88,
        collaboration_style="leader",
        debate_tendency=0.2,
        consensus_weight=1.4,
    ),
}

# Swarm formation configurations
AUDIT_FORMATIONS = {
    "full_spectrum": {
        "description": "Complete codebase audit with all specialists",
        "agents": list(BADASS_AGENTS.keys()),
        "phases": ["discovery", "analysis", "debate", "consensus", "validation"],
        "parallel_teams": 4,
        "expected_duration": "45-60 minutes",
    },
    "strategic_planning_enhanced": {
        "description": "Strategic planning enhanced comprehensive audit with OODA loop methodology",
        "agents": [
            "strategic_commander",
            "environmental_scanner",
            "scenario_modeler",
            "trend_analyst",
            "predictive_planner",
            "adaptation_agent",
            "chief_architect",
            "security_commander",
            "performance_guru",
            "quality_overlord",
            "consensus_builder",
            "final_validator",
        ],
        "phases": [
            "strategic_observe",
            "strategic_orient",
            "strategic_decide",
            "strategic_act",
            "discovery",
            "analysis",
            "adaptation",
            "consensus",
            "validation",
        ],
        "parallel_teams": 5,
        "expected_duration": "60-90 minutes",
        "strategic_planning": True,
        "ooda_enabled": True,
    },
    "security_focused": {
        "description": "Security-focused audit with vulnerability hunting",
        "agents": [
            "security_commander",
            "vulnerability_hunter",
            "compliance_officer",
            "infrastructure_expert",
            "deployment_specialist",
            "consensus_builder",
        ],
        "phases": [
            "security_discovery",
            "threat_analysis",
            "vulnerability_assessment",
            "compliance_check",
        ],
        "parallel_teams": 2,
        "expected_duration": "20-30 minutes",
    },
    "architecture_deep_dive": {
        "description": "Deep architectural analysis and refactoring recommendations",
        "agents": [
            "chief_architect",
            "deepcode_analyzer",
            "performance_guru",
            "pattern_detector",
            "quality_overlord",
            "debate_moderator",
        ],
        "phases": [
            "architecture_analysis",
            "design_review",
            "performance_assessment",
            "refactoring_plan",
        ],
        "parallel_teams": 3,
        "expected_duration": "30-45 minutes",
    },
    "performance_optimization": {
        "description": "Performance-focused audit with optimization recommendations",
        "agents": [
            "performance_guru",
            "deepcode_analyzer",
            "infrastructure_expert",
            "pattern_detector",
            "test_commander",
            "consensus_builder",
        ],
        "phases": [
            "performance_profiling",
            "bottleneck_analysis",
            "optimization_opportunities",
        ],
        "parallel_teams": 2,
        "expected_duration": "25-35 minutes",
    },
    "rapid_assessment": {
        "description": "Quick comprehensive assessment for time-sensitive audits",
        "agents": [
            "rapid_scanner",
            "pattern_detector",
            "vulnerability_hunter",
            "quality_overlord",
            "final_validator",
        ],
        "phases": ["rapid_scan", "issue_triage", "priority_assessment"],
        "parallel_teams": 2,
        "expected_duration": "10-15 minutes",
    },
}

# Collaboration patterns
COLLABORATION_PATTERNS = {
    "debate_intensive": {
        "description": "High debate activity for controversial findings",
        "min_participants": 3,
        "max_rounds": 5,
        "consensus_threshold": 0.8,
        "suitable_for": [
            "architecture_decisions",
            "security_assessments",
            "major_refactoring",
        ],
    },
    "consensus_building": {
        "description": "Collaborative consensus for balanced decisions",
        "min_participants": 4,
        "max_rounds": 3,
        "consensus_threshold": 0.75,
        "suitable_for": [
            "priority_ranking",
            "recommendation_synthesis",
            "final_reports",
        ],
    },
    "expert_review": {
        "description": "Specialist-led review with peer validation",
        "min_participants": 2,
        "max_rounds": 2,
        "consensus_threshold": 0.85,
        "suitable_for": [
            "technical_deep_dives",
            "specialized_analysis",
            "compliance_review",
        ],
    },
    "rapid_validation": {
        "description": "Quick validation for time-critical decisions",
        "min_participants": 2,
        "max_rounds": 1,
        "consensus_threshold": 0.7,
        "suitable_for": ["issue_triage", "quick_assessments", "emergency_reviews"],
    },
}

# Quality gates and thresholds
QUALITY_GATES = {
    "architecture_score_minimum": 75,
    "security_score_minimum": 85,
    "performance_score_minimum": 70,
    "quality_score_minimum": 80,
    "test_coverage_minimum": 80,
    "critical_findings_maximum": 3,
    "high_findings_maximum": 10,
    "consensus_agreement_minimum": 0.75,
    "agent_confidence_minimum": 0.80,
}


def get_formation_config(formation_name: str) -> dict[str, Any]:
    """Get configuration for specific audit formation"""
    return AUDIT_FORMATIONS.get(formation_name, AUDIT_FORMATIONS["full_spectrum"])


def get_agents_for_formation(formation_name: str) -> list[AgentSpec]:
    """Get agent specifications for a formation"""
    formation = get_formation_config(formation_name)
    return [BADASS_AGENTS[agent_name] for agent_name in formation["agents"]]


def get_model_distribution() -> dict[str, int]:
    """Get distribution of models across tiers"""
    distribution = {"ultra": 0, "premium": 0, "balanced": 0, "fast": 0}

    for model in BADASS_MODEL_ASSIGNMENTS.values():
        if "grok-code-fast-1" in model or "claude-sonnet-4" in model:
            distribution["ultra"] += 1
        elif "gemini-2.5" in model or "deepseek-chat-v3" in model or "gpt-5" in model:
            distribution["premium"] += 1
        elif "flash-lite" in model or "r1-0528" in model or "mistral-nemo" in model:
            distribution["balanced"] += 1
        else:
            distribution["fast"] += 1

    return distribution
