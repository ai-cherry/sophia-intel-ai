"""
Swarm Template Definitions - Multi-topology Swarm Templates for Code Generation
Leverages existing unified factory patterns for both Sophia and Artemis domains
Includes Pay Ready business templates and Artemis technical templates
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.artemis.unified_factory import (
    ArtemisUnifiedFactory,
    MilitaryUnitType,
    TechnicalAgentRole,
)
from app.artemis.unified_factory import SwarmType as ArtemisSwarmType
from app.sophia.unified_factory import (
    BusinessAgentRole,
    MythologyArchetype,
    SophiaUnifiedFactory,
)
from app.sophia.unified_factory import SwarmType as SophiaSwarmType

# ==============================================================================
# TEMPLATE ENUMS AND TYPES
# ==============================================================================


class SwarmTopology(str, Enum):
    """Swarm topology patterns"""

    SEQUENTIAL = "sequential"  # 3-stage pipeline
    STAR = "star"  # coordinator + workers
    COMMITTEE = "committee"  # voting system with arbiter
    HIERARCHICAL = "hierarchical"  # multi-level coordination


class TemplateDomain(str, Enum):
    """Template domain classification"""

    SOPHIA_BUSINESS = "sophia_business"
    ARTEMIS_TECHNICAL = "artemis_technical"
    PAY_READY = "pay_ready"
    CROSS_DOMAIN = "cross_domain"


class TemplateCategory(str, Enum):
    """Template categories for organization"""

    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    CODE_REVIEW = "code_review"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    MARKET_RESEARCH = "market_research"


# ==============================================================================
# TEMPLATE DATA MODELS
# ==============================================================================


@dataclass
class AgentTemplateConfig:
    """Configuration for an agent within a swarm template"""

    template_name: str
    role: str
    factory_type: str  # 'sophia' or 'artemis'
    custom_config: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # influence weight in decision making
    required: bool = True


@dataclass
class SwarmTemplate:
    """Complete swarm template definition"""

    id: str
    name: str
    description: str
    topology: SwarmTopology
    domain: TemplateDomain
    category: TemplateCategory
    agents: List[AgentTemplateConfig]
    coordination_config: Dict[str, Any]
    resource_limits: Dict[str, Any]
    success_criteria: Dict[str, Any]
    example_use_cases: List[str]
    estimated_duration: str
    complexity_level: int  # 1-5
    pay_ready_optimized: bool = False


@dataclass
class CoordinationConfig:
    """Coordination configuration for different topologies"""

    strategy: str
    timeout_minutes: int = 30
    consensus_threshold: float = 0.7
    retry_attempts: int = 3
    parallel_execution: bool = True
    arbiter_required: bool = False
    quality_gates: List[str] = field(default_factory=list)


# ==============================================================================
# SWARM TEMPLATE CATALOG
# ==============================================================================


class SwarmTemplateCatalog:
    """Catalog of all available swarm templates"""

    def __init__(self):
        self.templates: Dict[str, SwarmTemplate] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize all swarm templates"""
        self._create_sophia_templates()
        self._create_artemis_templates()
        self._create_pay_ready_templates()
        self._create_cross_domain_templates()

    def _create_sophia_templates(self):
        """Create Sophia business intelligence templates"""

        # Sequential Pipeline: Market Research Analysis
        self.templates["sophia_market_research_pipeline"] = SwarmTemplate(
            id="sophia_market_research_pipeline",
            name="Market Research Analysis Pipeline",
            description="3-stage sequential pipeline for comprehensive market research",
            topology=SwarmTopology.SEQUENTIAL,
            domain=TemplateDomain.SOPHIA_BUSINESS,
            category=TemplateCategory.MARKET_RESEARCH,
            agents=[
                AgentTemplateConfig(
                    template_name="market_research_specialist",
                    role="data_collector",
                    factory_type="sophia",
                    custom_config={"temperature": 0.2, "focus": "data_gathering"},
                ),
                AgentTemplateConfig(
                    template_name="competitive_intelligence",
                    role="analyst",
                    factory_type="sophia",
                    custom_config={"temperature": 0.4, "focus": "competitive_analysis"},
                ),
                AgentTemplateConfig(
                    template_name="revenue_forecaster",
                    role="strategist",
                    factory_type="sophia",
                    custom_config={"temperature": 0.3, "focus": "strategic_recommendations"},
                ),
            ],
            coordination_config={
                "strategy": "sequential_handoff",
                "quality_gates": ["data_validation", "analysis_review", "recommendation_check"],
                "stage_timeouts": [10, 15, 10],  # minutes per stage
                "handoff_validation": True,
            },
            resource_limits={
                "max_concurrent_tasks": 3,  # respects 8-task limit
                "memory_usage_mb": 500,
                "api_calls_per_minute": 60,
            },
            success_criteria={
                "data_completeness": 0.9,
                "insight_quality": 0.8,
                "actionable_recommendations": 3,
            },
            example_use_cases=[
                "Quarterly market analysis",
                "Competitive landscape assessment",
                "New market entry evaluation",
            ],
            estimated_duration="35-45 minutes",
            complexity_level=3,
        )

        # Star Topology: Business Intelligence Hub
        self.templates["sophia_bi_star"] = SwarmTemplate(
            id="sophia_bi_star",
            name="Business Intelligence Star Network",
            description="Central coordinator with specialized analyst workers",
            topology=SwarmTopology.STAR,
            domain=TemplateDomain.SOPHIA_BUSINESS,
            category=TemplateCategory.BUSINESS_INTELLIGENCE,
            agents=[
                AgentTemplateConfig(
                    template_name="athena",  # mythology agent as coordinator
                    role="coordinator",
                    factory_type="sophia",
                    custom_config={"wisdom_mode": "strategic_coordination"},
                    weight=2.0,
                ),
                AgentTemplateConfig(
                    template_name="sales_pipeline_analyst",
                    role="sales_worker",
                    factory_type="sophia",
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="client_success_manager",
                    role="client_worker",
                    factory_type="sophia",
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="revenue_forecaster",
                    role="finance_worker",
                    factory_type="sophia",
                    weight=1.0,
                ),
            ],
            coordination_config={
                "strategy": "star_coordination",
                "coordinator_timeout": 5,  # minutes for coordination decisions
                "worker_parallel": True,
                "result_aggregation": "weighted_synthesis",
                "feedback_loops": True,
            },
            resource_limits={
                "max_concurrent_tasks": 4,
                "memory_usage_mb": 800,
                "api_calls_per_minute": 100,
            },
            success_criteria={
                "coordinator_consensus": 0.8,
                "worker_completion_rate": 0.95,
                "synthesis_quality": 0.85,
            },
            example_use_cases=[
                "Executive dashboard updates",
                "Multi-departmental KPI analysis",
                "Strategic decision support",
            ],
            estimated_duration="25-35 minutes",
            complexity_level=4,
        )

        # Committee + Arbiter: Strategic Decision Making
        self.templates["sophia_strategic_committee"] = SwarmTemplate(
            id="sophia_strategic_committee",
            name="Strategic Decision Committee",
            description="Mythology council with voting and divine arbitration",
            topology=SwarmTopology.COMMITTEE,
            domain=TemplateDomain.SOPHIA_BUSINESS,
            category=TemplateCategory.ANALYSIS,
            agents=[
                AgentTemplateConfig(
                    template_name="athena",
                    role="committee_member",
                    factory_type="sophia",
                    weight=1.5,
                ),
                AgentTemplateConfig(
                    template_name="odin", role="committee_member", factory_type="sophia", weight=1.5
                ),
                AgentTemplateConfig(
                    template_name="minerva",
                    role="committee_member",
                    factory_type="sophia",
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="hermes",
                    role="arbiter",
                    factory_type="sophia",
                    custom_config={"arbitration_mode": True},
                    weight=2.0,
                ),
            ],
            coordination_config={
                "strategy": "committee_voting",
                "voting_rounds": 2,
                "consensus_threshold": 0.75,
                "arbiter_intervention_threshold": 0.6,
                "debate_enabled": True,
                "wisdom_synthesis": True,
            },
            resource_limits={
                "max_concurrent_tasks": 4,
                "memory_usage_mb": 600,
                "api_calls_per_minute": 80,
            },
            success_criteria={
                "committee_consensus": 0.75,
                "wisdom_integration": 0.9,
                "decision_confidence": 0.85,
            },
            example_use_cases=[
                "Strategic planning decisions",
                "Major investment evaluations",
                "Crisis response strategies",
            ],
            estimated_duration="40-60 minutes",
            complexity_level=5,
        )

    def _create_artemis_templates(self):
        """Create Artemis technical templates"""

        # Sequential: Code Review Pipeline
        self.templates["artemis_code_review_pipeline"] = SwarmTemplate(
            id="artemis_code_review_pipeline",
            name="Technical Code Review Pipeline",
            description="3-stage code review with security and performance analysis",
            topology=SwarmTopology.SEQUENTIAL,
            domain=TemplateDomain.ARTEMIS_TECHNICAL,
            category=TemplateCategory.CODE_REVIEW,
            agents=[
                AgentTemplateConfig(
                    template_name="code_reviewer",
                    role="initial_reviewer",
                    factory_type="artemis",
                    custom_config={"review_depth": "comprehensive"},
                ),
                AgentTemplateConfig(
                    template_name="security_auditor",
                    role="security_analyst",
                    factory_type="artemis",
                    custom_config={"paranoia_level": "maximum"},
                ),
                AgentTemplateConfig(
                    template_name="performance_optimizer",
                    role="performance_analyst",
                    factory_type="artemis",
                    custom_config={"optimization_focus": "critical_path"},
                ),
            ],
            coordination_config={
                "strategy": "sequential_review",
                "stage_gates": ["code_quality_check", "security_clearance", "performance_approval"],
                "rollback_on_failure": True,
                "escalation_enabled": True,
            },
            resource_limits={
                "max_concurrent_tasks": 3,
                "memory_usage_mb": 400,
                "api_calls_per_minute": 50,
            },
            success_criteria={
                "code_quality_score": 0.9,
                "security_clearance": True,
                "performance_rating": 0.85,
            },
            example_use_cases=[
                "Pull request reviews",
                "Pre-deployment audits",
                "Legacy code assessments",
            ],
            estimated_duration="20-30 minutes",
            complexity_level=3,
        )

        # Star: Security Assessment Hub
        self.templates["artemis_security_star"] = SwarmTemplate(
            id="artemis_security_star",
            name="Security Assessment Command Center",
            description="Central security coordinator with specialized scanner workers",
            topology=SwarmTopology.STAR,
            domain=TemplateDomain.ARTEMIS_TECHNICAL,
            category=TemplateCategory.SECURITY,
            agents=[
                AgentTemplateConfig(
                    template_name="security_auditor",
                    role="security_commander",
                    factory_type="artemis",
                    custom_config={"command_mode": True},
                    weight=2.0,
                ),
                AgentTemplateConfig(
                    template_name="code_reviewer",
                    role="code_scanner",
                    factory_type="artemis",
                    custom_config={"security_focus": True},
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="performance_optimizer",
                    role="resource_scanner",
                    factory_type="artemis",
                    custom_config={"security_metrics": True},
                    weight=1.0,
                ),
            ],
            coordination_config={
                "strategy": "security_command",
                "threat_escalation": True,
                "parallel_scanning": True,
                "real_time_monitoring": True,
            },
            resource_limits={
                "max_concurrent_tasks": 3,
                "memory_usage_mb": 600,
                "api_calls_per_minute": 70,
            },
            success_criteria={
                "vulnerability_detection": 0.95,
                "false_positive_rate": 0.05,
                "threat_classification": 0.9,
            },
            example_use_cases=[
                "Security audits",
                "Vulnerability assessments",
                "Compliance reviews",
            ],
            estimated_duration="30-45 minutes",
            complexity_level=4,
        )

        # Hierarchical: Military Operations
        self.templates["artemis_military_hierarchy"] = SwarmTemplate(
            id="artemis_military_hierarchy",
            name="Military Operations Hierarchy",
            description="Multi-level military command structure for complex operations",
            topology=SwarmTopology.HIERARCHICAL,
            domain=TemplateDomain.ARTEMIS_TECHNICAL,
            category=TemplateCategory.PERFORMANCE,
            agents=[
                AgentTemplateConfig(
                    template_name="recon_battalion",
                    role="reconnaissance_commander",
                    factory_type="artemis",
                    custom_config={"command_level": "strategic"},
                    weight=2.0,
                ),
                AgentTemplateConfig(
                    template_name="strike_force",
                    role="tactical_commander",
                    factory_type="artemis",
                    custom_config={"command_level": "tactical"},
                    weight=1.5,
                ),
                AgentTemplateConfig(
                    template_name="qc_division",
                    role="support_commander",
                    factory_type="artemis",
                    custom_config={"command_level": "operational"},
                    weight=1.0,
                ),
            ],
            coordination_config={
                "strategy": "military_hierarchy",
                "chain_of_command": ["strategic", "tactical", "operational"],
                "mission_phases": ["recon", "strike", "validation"],
                "real_time_comms": True,
            },
            resource_limits={
                "max_concurrent_tasks": 6,  # military operations need more resources
                "memory_usage_mb": 1000,
                "api_calls_per_minute": 120,
            },
            success_criteria={
                "mission_success_rate": 0.95,
                "coordination_efficiency": 0.9,
                "tactical_precision": 0.85,
            },
            example_use_cases=[
                "Large-scale refactoring",
                "System-wide optimizations",
                "Critical incident response",
            ],
            estimated_duration="45-75 minutes",
            complexity_level=5,
        )

    def _create_pay_ready_templates(self):
        """Create Pay Ready business optimization templates"""

        # Data Collection Pipeline
        self.templates["pay_ready_data_pipeline"] = SwarmTemplate(
            id="pay_ready_data_pipeline",
            name="Pay Ready Data Collection Pipeline",
            description="Optimized pipeline for business data collection and initial analysis",
            topology=SwarmTopology.SEQUENTIAL,
            domain=TemplateDomain.PAY_READY,
            category=TemplateCategory.DATA_COLLECTION,
            agents=[
                AgentTemplateConfig(
                    template_name="hermes",  # swift data gathering
                    role="data_collector",
                    factory_type="sophia",
                    custom_config={"collection_speed": "maximum", "data_sources": "all"},
                ),
                AgentTemplateConfig(
                    template_name="sales_pipeline_analyst",
                    role="data_processor",
                    factory_type="sophia",
                    custom_config={"processing_focus": "revenue_metrics"},
                ),
                AgentTemplateConfig(
                    template_name="asclepius",  # business health diagnostics
                    role="data_validator",
                    factory_type="sophia",
                    custom_config={"validation_mode": "business_health"},
                ),
            ],
            coordination_config={
                "strategy": "pay_ready_pipeline",
                "sla_targets": {"data_freshness": "< 5 minutes", "accuracy": "> 95%"},
                "automated_alerts": True,
                "business_hour_priority": True,
            },
            resource_limits={
                "max_concurrent_tasks": 3,
                "memory_usage_mb": 300,
                "api_calls_per_minute": 40,
            },
            success_criteria={
                "data_completeness": 0.95,
                "processing_speed": 0.9,
                "business_relevance": 0.85,
            },
            example_use_cases=[
                "Daily revenue reports",
                "Real-time KPI dashboards",
                "Customer health monitoring",
            ],
            estimated_duration="15-25 minutes",
            complexity_level=2,
            pay_ready_optimized=True,
        )

        # Business Intelligence Star
        self.templates["pay_ready_bi_hub"] = SwarmTemplate(
            id="pay_ready_bi_hub",
            name="Pay Ready Business Intelligence Hub",
            description="Fast business intelligence for revenue optimization",
            topology=SwarmTopology.STAR,
            domain=TemplateDomain.PAY_READY,
            category=TemplateCategory.BUSINESS_INTELLIGENCE,
            agents=[
                AgentTemplateConfig(
                    template_name="revenue_forecaster",
                    role="bi_coordinator",
                    factory_type="sophia",
                    custom_config={"forecasting_urgency": "high"},
                    weight=2.0,
                ),
                AgentTemplateConfig(
                    template_name="sales_pipeline_analyst",
                    role="sales_analyzer",
                    factory_type="sophia",
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="client_success_manager",
                    role="retention_analyzer",
                    factory_type="sophia",
                    weight=1.0,
                ),
                AgentTemplateConfig(
                    template_name="competitive_intelligence",
                    role="market_analyzer",
                    factory_type="sophia",
                    weight=0.8,
                ),
            ],
            coordination_config={
                "strategy": "revenue_optimization",
                "priority_metrics": ["revenue", "pipeline", "retention"],
                "real_time_updates": True,
                "business_hour_boost": True,
            },
            resource_limits={
                "max_concurrent_tasks": 4,
                "memory_usage_mb": 400,
                "api_calls_per_minute": 60,
            },
            success_criteria={
                "revenue_insight_accuracy": 0.9,
                "actionable_recommendations": 5,
                "competitive_awareness": 0.8,
            },
            example_use_cases=["Executive briefings", "Revenue optimization", "Market positioning"],
            estimated_duration="20-30 minutes",
            complexity_level=3,
            pay_ready_optimized=True,
        )

    def _create_cross_domain_templates(self):
        """Create cross-domain templates using both Sophia and Artemis"""

        # Full Stack Analysis
        self.templates["cross_domain_full_stack"] = SwarmTemplate(
            id="cross_domain_full_stack",
            name="Full Stack Business-Technical Analysis",
            description="Combined business and technical analysis for comprehensive insights",
            topology=SwarmTopology.HIERARCHICAL,
            domain=TemplateDomain.CROSS_DOMAIN,
            category=TemplateCategory.ANALYSIS,
            agents=[
                # Business layer (Sophia)
                AgentTemplateConfig(
                    template_name="athena",
                    role="business_strategist",
                    factory_type="sophia",
                    custom_config={"domain": "business_strategy"},
                    weight=1.5,
                ),
                AgentTemplateConfig(
                    template_name="revenue_forecaster",
                    role="business_analyst",
                    factory_type="sophia",
                    weight=1.0,
                ),
                # Technical layer (Artemis)
                AgentTemplateConfig(
                    template_name="security_auditor",
                    role="technical_lead",
                    factory_type="artemis",
                    custom_config={"business_context": True},
                    weight=1.5,
                ),
                AgentTemplateConfig(
                    template_name="performance_optimizer",
                    role="technical_analyst",
                    factory_type="artemis",
                    weight=1.0,
                ),
            ],
            coordination_config={
                "strategy": "cross_domain_synthesis",
                "business_technical_handoff": True,
                "unified_reporting": True,
                "stakeholder_alignment": True,
            },
            resource_limits={
                "max_concurrent_tasks": 4,
                "memory_usage_mb": 700,
                "api_calls_per_minute": 80,
            },
            success_criteria={
                "business_technical_alignment": 0.85,
                "comprehensive_coverage": 0.9,
                "stakeholder_satisfaction": 0.8,
            },
            example_use_cases=[
                "Product launch analysis",
                "System architecture business impact",
                "Technology ROI assessments",
            ],
            estimated_duration="50-70 minutes",
            complexity_level=5,
        )

    # ==============================================================================
    # TEMPLATE ACCESS METHODS
    # ==============================================================================

    def get_template(self, template_id: str) -> Optional[SwarmTemplate]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)

    def list_templates(
        self,
        domain: Optional[TemplateDomain] = None,
        category: Optional[TemplateCategory] = None,
        topology: Optional[SwarmTopology] = None,
        pay_ready_only: bool = False,
    ) -> List[SwarmTemplate]:
        """List templates with optional filtering"""
        templates = list(self.templates.values())

        if domain:
            templates = [t for t in templates if t.domain == domain]
        if category:
            templates = [t for t in templates if t.category == category]
        if topology:
            templates = [t for t in templates if t.topology == topology]
        if pay_ready_only:
            templates = [t for t in templates if t.pay_ready_optimized]

        return templates

    def get_templates_by_complexity(self, max_complexity: int = 3) -> List[SwarmTemplate]:
        """Get templates within complexity limit"""
        return [t for t in self.templates.values() if t.complexity_level <= max_complexity]

    def get_template_summary(self) -> Dict[str, Any]:
        """Get summary of all templates"""
        summary = {
            "total_templates": len(self.templates),
            "by_domain": {},
            "by_topology": {},
            "by_category": {},
            "by_complexity": {},
            "pay_ready_count": 0,
        }

        for template in self.templates.values():
            # Domain distribution
            domain_key = template.domain.value
            summary["by_domain"][domain_key] = summary["by_domain"].get(domain_key, 0) + 1

            # Topology distribution
            topology_key = template.topology.value
            summary["by_topology"][topology_key] = summary["by_topology"].get(topology_key, 0) + 1

            # Category distribution
            category_key = template.category.value
            summary["by_category"][category_key] = summary["by_category"].get(category_key, 0) + 1

            # Complexity distribution
            complexity_key = f"level_{template.complexity_level}"
            summary["by_complexity"][complexity_key] = (
                summary["by_complexity"].get(complexity_key, 0) + 1
            )

            # Pay Ready count
            if template.pay_ready_optimized:
                summary["pay_ready_count"] += 1

        return summary

    def validate_template(self, template: SwarmTemplate) -> Tuple[bool, List[str]]:
        """Validate template configuration"""
        errors = []

        # Check required fields
        if not template.id:
            errors.append("Template ID is required")
        if not template.name:
            errors.append("Template name is required")
        if not template.agents:
            errors.append("Template must have at least one agent")

        # Validate agent count for 8-task limit
        total_agents = len(template.agents)
        if total_agents > 8:
            errors.append(f"Template has {total_agents} agents, exceeds 8-task limit")

        # Validate topology-specific requirements
        if template.topology == SwarmTopology.STAR:
            coordinator_count = len([a for a in template.agents if a.role == "coordinator"])
            if coordinator_count != 1:
                errors.append("Star topology requires exactly one coordinator")

        elif template.topology == SwarmTopology.COMMITTEE:
            arbiter_count = len([a for a in template.agents if a.role == "arbiter"])
            if template.coordination_config.get("arbiter_required") and arbiter_count == 0:
                errors.append("Committee topology with arbiter_required needs an arbiter agent")

        # Validate resource limits
        max_tasks = template.resource_limits.get("max_concurrent_tasks", 0)
        if max_tasks > 8:
            errors.append(f"max_concurrent_tasks ({max_tasks}) exceeds system limit of 8")

        return len(errors) == 0, errors


# ==============================================================================
# GLOBAL CATALOG INSTANCE
# ==============================================================================

# Global template catalog instance
swarm_template_catalog = SwarmTemplateCatalog()
