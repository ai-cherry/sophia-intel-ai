"""
🔥 Industry-Specific Research Automation Templates
================================================
Badass Implementation Swarm Enhanced Research System
Premium AI agent templates for deep industry analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class IndustryDomain(str, Enum):
    """Supported industry research domains"""

    PROPTECH = "proptech"
    AI_TECHNOLOGY = "ai_technology"
    APARTMENT_RENTAL = "apartment_rental"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    REAL_ESTATE = "real_estate"
    FINTECH = "fintech"
    SAAS = "saas"
    HEALTHTECH = "healthtech"


class ResearchDepth(str, Enum):
    """Research depth levels"""

    QUICK_SCAN = "quick_scan"  # 15-30 minutes
    STANDARD = "standard"  # 1-2 hours
    COMPREHENSIVE = "comprehensive"  # 3-6 hours
    DEEP_DIVE = "deep_dive"  # 6-12 hours


class ResearchFrequency(str, Enum):
    """Research scheduling frequencies"""

    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class ResearchSource:
    """Research source specification"""

    name: str
    type: str  # "web", "api", "database", "expert_network"
    url: str | None = None
    api_key: str | None = None
    priority: int = 1  # 1=highest, 5=lowest
    cost_per_query: float = 0.0
    rate_limit: dict[str, int] | None = None


@dataclass
class ResearchTemplate:
    """Complete research automation template"""

    template_id: str
    name: str
    industry: IndustryDomain
    description: str

    # Research parameters
    default_depth: ResearchDepth
    estimated_duration: str
    agent_count: int
    premium_models_required: bool

    # Research focus areas
    key_questions: list[str]
    data_sources: list[ResearchSource]
    analysis_frameworks: list[str]
    output_formats: list[str]

    # Automation settings
    scheduling_enabled: bool = True
    alert_thresholds: dict[str, Any] = None
    stakeholder_notifications: list[str] = None


# PREMIUM RESEARCH TEMPLATES

PROPTECH_COMPREHENSIVE = ResearchTemplate(
    template_id="proptech_comprehensive_2025",
    name="PropTech Industry Comprehensive Analysis",
    industry=IndustryDomain.PROPTECH,
    description="Deep analysis of property technology trends, market dynamics, and competitive landscape",
    default_depth=ResearchDepth.COMPREHENSIVE,
    estimated_duration="4-6 hours",
    agent_count=8,
    premium_models_required=True,
    key_questions=[
        "What are the top 10 emerging proptech trends for 2025?",
        "Which proptech startups raised the most funding in the last 6 months?",
        "What new technologies are disrupting traditional real estate processes?",
        "How is AI being integrated into property management platforms?",
        "What are the key pain points property managers face today?",
        "Which markets are seeing the fastest proptech adoption?",
        "What regulatory changes are affecting proptech companies?",
        "How are large real estate companies responding to proptech disruption?",
    ],
    data_sources=[
        ResearchSource("Crunchbase API", "api", "https://api.crunchbase.com", priority=1),
        ResearchSource("CB Insights", "web", "https://cbinsights.com", priority=1),
        ResearchSource("PitchBook", "api", priority=1, cost_per_query=0.50),
        ResearchSource("PropTech News", "web", "https://proptechnews.com", priority=2),
        ResearchSource("Real Estate Tech News", "web", priority=2),
        ResearchSource("Venture Capital Databases", "api", priority=1),
        ResearchSource("Patent Databases", "api", priority=3),
        ResearchSource("LinkedIn Executive Network", "api", priority=2),
    ],
    analysis_frameworks=[
        "Porter's Five Forces Analysis",
        "Technology Adoption Lifecycle",
        "Competitive Landscape Mapping",
        "Market Size & Growth Analysis",
        "Investment Flow Analysis",
        "Regulatory Impact Assessment",
        "Customer Journey Analysis",
        "Technology Stack Analysis",
    ],
    output_formats=[
        "Executive Summary (2-page)",
        "Detailed Research Report (15-25 pages)",
        "Market Map Visualization",
        "Investment Trend Dashboard",
        "Competitive Analysis Matrix",
        "Technology Roadmap",
        "Strategic Recommendations",
        "Presentation Deck (20-30 slides)",
    ],
    scheduling_enabled=True,
    alert_thresholds={
        "new_funding_rounds": ">$10M",
        "new_market_entrants": ">3 per month",
        "regulatory_changes": "any",
        "major_acquisitions": ">$50M",
    },
    stakeholder_notifications=["research@sophia.ai", "executives@sophia.ai"],
)

APARTMENT_RENTAL_DEEP_DIVE = ResearchTemplate(
    template_id="apartment_rental_deep_dive_2025",
    name="Apartment Rental Market Deep Dive",
    industry=IndustryDomain.APARTMENT_RENTAL,
    description="Comprehensive analysis of apartment rental markets, pricing trends, and resident experience innovations",
    default_depth=ResearchDepth.DEEP_DIVE,
    estimated_duration="8-12 hours",
    agent_count=12,
    premium_models_required=True,
    key_questions=[
        "What are current apartment rental pricing trends by metro area?",
        "How is remote work affecting rental demand patterns?",
        "Which resident experience technologies are gaining traction?",
        "What are the key factors driving rent increases in major markets?",
        "How are property management companies adapting to post-pandemic expectations?",
        "What amenities are most important to renters in 2025?",
        "How is AI being used to optimize rental pricing and operations?",
        "What are the fastest-growing apartment rental platforms and services?",
    ],
    data_sources=[
        ResearchSource("RentSpree API", "api", priority=1),
        ResearchSource("Apartment List API", "api", priority=1),
        ResearchSource("RentData", "api", priority=1, cost_per_query=1.00),
        ResearchSource("CoStar Data", "api", priority=1, cost_per_query=2.00),
        ResearchSource("Census Bureau Housing Data", "api", priority=2),
        ResearchSource("Local MLS Feeds", "api", priority=2),
        ResearchSource("Social Media Sentiment", "api", priority=3),
        ResearchSource("Property Management Forums", "web", priority=3),
    ],
    analysis_frameworks=[
        "Supply & Demand Analysis",
        "Price Elasticity Modeling",
        "Geographic Market Segmentation",
        "Demographic Trend Analysis",
        "Technology Adoption Patterns",
        "Customer Satisfaction Analysis",
        "Operational Efficiency Analysis",
        "Investment ROI Modeling",
    ],
    output_formats=[
        "Market Analysis Dashboard",
        "Pricing Strategy Report",
        "Resident Experience Study",
        "Technology Implementation Guide",
        "Investment Opportunity Brief",
        "Competitive Landscape Analysis",
        "Regulatory Compliance Overview",
        "Strategic Action Plan",
    ],
)

AI_TECHNOLOGY_TRENDS = ResearchTemplate(
    template_id="ai_technology_trends_2025",
    name="AI Technology Trends & Business Applications",
    industry=IndustryDomain.AI_TECHNOLOGY,
    description="Latest AI/ML developments, business applications, and implementation strategies",
    default_depth=ResearchDepth.COMPREHENSIVE,
    estimated_duration="5-7 hours",
    agent_count=10,
    premium_models_required=True,
    key_questions=[
        "What are the breakthrough AI developments in the last 6 months?",
        "Which AI business applications show the highest ROI?",
        "How are enterprises implementing AI governance frameworks?",
        "What are the latest developments in AI agent frameworks?",
        "Which AI startups are disrupting traditional business processes?",
        "How is AI regulation evolving across different markets?",
        "What are the emerging AI use cases in business intelligence?",
        "Which AI tools and platforms are gaining enterprise adoption?",
    ],
    data_sources=[
        ResearchSource("arXiv AI Papers", "api", "https://arxiv.org/list/cs.AI/recent", priority=1),
        ResearchSource("Google AI Blog", "web", priority=1),
        ResearchSource("OpenAI Research", "web", priority=1),
        ResearchSource("AI Investment Database", "api", priority=1),
        ResearchSource("Hugging Face Models", "api", priority=2),
        ResearchSource("AI Conference Proceedings", "web", priority=2),
        ResearchSource("Enterprise AI Surveys", "api", priority=2),
        ResearchSource("AI Patent Database", "api", priority=3),
    ],
    analysis_frameworks=[
        "Technology Maturity Assessment",
        "Business Value Analysis",
        "Implementation Complexity Matrix",
        "ROI Modeling",
        "Risk Assessment Framework",
        "Competitive Analysis",
        "Regulatory Impact Analysis",
        "Adoption Timeline Projections",
    ],
    output_formats=[
        "AI Trends Executive Brief",
        "Technology Implementation Roadmap",
        "Business Case Analysis",
        "Vendor Evaluation Matrix",
        "Risk & Compliance Guide",
        "Investment Opportunity Assessment",
        "Strategic Planning Deck",
        "Technical Architecture Guide",
    ],
)

BUSINESS_INTELLIGENCE_LANDSCAPE = ResearchTemplate(
    template_id="bi_landscape_2025",
    name="Business Intelligence Platform Landscape",
    industry=IndustryDomain.BUSINESS_INTELLIGENCE,
    description="Comprehensive analysis of BI tools, platforms, and emerging analytics trends",
    default_depth=ResearchDepth.STANDARD,
    estimated_duration="2-4 hours",
    agent_count=6,
    premium_models_required=False,
    key_questions=[
        "Which BI platforms are gaining market share in 2025?",
        "How is AI integration changing traditional BI workflows?",
        "What are the key features enterprises prioritize in BI tools?",
        "Which self-service analytics platforms show the best user adoption?",
        "How are cloud-native BI solutions competing with legacy systems?",
        "What are the emerging trends in real-time analytics?",
        "Which data visualization techniques are most effective?",
        "How are organizations measuring BI ROI and success?",
    ],
    data_sources=[
        ResearchSource("Gartner Magic Quadrant", "web", priority=1),
        ResearchSource("Forrester Research", "api", priority=1),
        ResearchSource("G2 Reviews", "api", priority=2),
        ResearchSource("Software Advice", "web", priority=2),
        ResearchSource("BI User Communities", "web", priority=2),
        ResearchSource("Vendor Documentation", "web", priority=3),
        ResearchSource("Enterprise Surveys", "api", priority=2),
        ResearchSource("LinkedIn Professional Networks", "api", priority=3),
    ],
    analysis_frameworks=[
        "Feature Comparison Matrix",
        "Total Cost of Ownership Analysis",
        "User Experience Assessment",
        "Technical Architecture Review",
        "Integration Capability Analysis",
        "Scalability Assessment",
        "Security & Compliance Review",
        "Market Position Analysis",
    ],
    output_formats=[
        "Platform Comparison Report",
        "Vendor Selection Guide",
        "Implementation Best Practices",
        "Cost-Benefit Analysis",
        "Technical Requirements Checklist",
        "User Training Curriculum",
        "Migration Strategy Guide",
        "Performance Benchmarks",
    ],
)

# TEMPLATE REGISTRY
RESEARCH_TEMPLATES: dict[str, ResearchTemplate] = {
    "proptech_comprehensive": PROPTECH_COMPREHENSIVE,
    "apartment_rental_deep_dive": APARTMENT_RENTAL_DEEP_DIVE,
    "ai_technology_trends": AI_TECHNOLOGY_TRENDS,
    "business_intelligence_landscape": BUSINESS_INTELLIGENCE_LANDSCAPE,
}

# QUICK ACCESS BY INDUSTRY
TEMPLATES_BY_INDUSTRY: dict[IndustryDomain, list[str]] = {
    IndustryDomain.PROPTECH: ["proptech_comprehensive"],
    IndustryDomain.APARTMENT_RENTAL: ["apartment_rental_deep_dive"],
    IndustryDomain.AI_TECHNOLOGY: ["ai_technology_trends"],
    IndustryDomain.BUSINESS_INTELLIGENCE: ["business_intelligence_landscape"],
}


def get_template_by_id(template_id: str) -> ResearchTemplate | None:
    """Get research template by ID"""
    return RESEARCH_TEMPLATES.get(template_id)


def get_templates_for_industry(industry: IndustryDomain) -> list[ResearchTemplate]:
    """Get all templates for specific industry"""
    template_ids = TEMPLATES_BY_INDUSTRY.get(industry, [])
    return [RESEARCH_TEMPLATES[tid] for tid in template_ids if tid in RESEARCH_TEMPLATES]


def get_recommended_template(industry: str, depth: str = "standard") -> ResearchTemplate | None:
    """Get recommended template for industry and depth"""
    try:
        industry_enum = IndustryDomain(industry.lower())
        templates = get_templates_for_industry(industry_enum)

        if not templates:
            return None

        # Filter by depth preference
        depth_enum = ResearchDepth(depth.lower())
        matching = [t for t in templates if t.default_depth == depth_enum]

        return matching[0] if matching else templates[0]

    except (ValueError, KeyError):
        return None


def estimate_research_cost(template: ResearchTemplate, depth: ResearchDepth) -> dict[str, float]:
    """Estimate research execution cost"""

    # Base costs by depth level
    base_costs = {
        ResearchDepth.QUICK_SCAN: 25.0,
        ResearchDepth.STANDARD: 75.0,
        ResearchDepth.COMPREHENSIVE: 200.0,
        ResearchDepth.DEEP_DIVE: 500.0,
    }

    # Premium model multiplier
    premium_multiplier = 2.5 if template.premium_models_required else 1.0

    # Agent count multiplier
    agent_multiplier = min(template.agent_count / 4, 3.0)  # Cap at 3x

    # Data source costs
    data_costs = sum(source.cost_per_query for source in template.data_sources)

    base_cost = base_costs.get(depth, 100.0)
    total_cost = (base_cost * premium_multiplier * agent_multiplier) + data_costs

    return {
        "base_cost": base_cost,
        "premium_multiplier": premium_multiplier,
        "agent_multiplier": agent_multiplier,
        "data_source_costs": data_costs,
        "estimated_total": round(total_cost, 2),
    }


# SWARM INTELLIGENCE: ADVANCED TEMPLATE CAPABILITIES


class TemplateOrchestrator:
    """
    🔥 Badass Implementation Swarm Template Orchestrator
    Manages template selection, customization, and execution
    """

    def __init__(self):
        self.active_research = {}
        self.template_cache = RESEARCH_TEMPLATES.copy()

    def create_custom_template(
        self, base_template_id: str, customizations: dict[str, Any]
    ) -> ResearchTemplate:
        """Create customized research template"""
        base = self.get_template(base_template_id)
        if not base:
            raise ValueError(f"Base template not found: {base_template_id}")

        # Apply customizations
        custom_template = ResearchTemplate(
            template_id=f"{base_template_id}_custom_{int(datetime.utcnow().timestamp())}",
            name=customizations.get("name", f"{base.name} (Custom)"),
            industry=base.industry,
            description=customizations.get("description", base.description),
            default_depth=ResearchDepth(customizations.get("depth", base.default_depth.value)),
            estimated_duration=customizations.get("duration", base.estimated_duration),
            agent_count=customizations.get("agent_count", base.agent_count),
            premium_models_required=customizations.get(
                "premium_models", base.premium_models_required
            ),
            key_questions=customizations.get("questions", base.key_questions),
            data_sources=customizations.get("sources", base.data_sources),
            analysis_frameworks=customizations.get("frameworks", base.analysis_frameworks),
            output_formats=customizations.get("outputs", base.output_formats),
            scheduling_enabled=customizations.get("scheduling", base.scheduling_enabled),
            alert_thresholds=customizations.get("alerts", base.alert_thresholds),
            stakeholder_notifications=customizations.get(
                "notifications", base.stakeholder_notifications
            ),
        )

        return custom_template

    def get_template(self, template_id: str) -> ResearchTemplate | None:
        """Get template by ID from cache"""
        return self.template_cache.get(template_id)

    def validate_template(self, template: ResearchTemplate) -> dict[str, Any]:
        """Validate template configuration"""
        issues = []
        warnings = []

        # Validate required fields
        if not template.key_questions:
            issues.append("Template must have at least one key question")

        if not template.data_sources:
            issues.append("Template must have at least one data source")

        if template.agent_count < 1:
            issues.append("Agent count must be at least 1")

        # Validate cost implications
        cost_estimate = estimate_research_cost(template, template.default_depth)
        if cost_estimate["estimated_total"] > 1000:
            warnings.append(f"High cost estimate: ${cost_estimate['estimated_total']:.2f}")

        # Validate duration
        if template.premium_models_required and template.agent_count > 10:
            warnings.append("High agent count with premium models may cause rate limiting")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "cost_estimate": cost_estimate,
        }


# GLOBAL TEMPLATE ORCHESTRATOR INSTANCE
template_orchestrator = TemplateOrchestrator()
