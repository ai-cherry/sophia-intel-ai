"""
Marketing Microswarm Data Models

Core data structures for marketing intelligence and automation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class CampaignType(str, Enum):
    """Types of marketing campaigns"""

    EMAIL_NURTURE = "email_nurture"
    SMS_OUTREACH = "sms_outreach"
    LINKEDIN_SOCIAL = "linkedin_social"
    MULTI_TOUCH = "multi_touch"
    VIDEO_PERSONALIZED = "video_personalized"
    GIFT_CAMPAIGN = "gift_campaign"
    CONTENT_MARKETING = "content_marketing"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status"""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class BrandComplianceLevel(str, Enum):
    """Brand compliance scoring levels"""

    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"  # 75-89%
    FAIR = "fair"  # 60-74%
    POOR = "poor"  # Below 60%


class MarketSegment(str, Enum):
    """Market segments for targeting"""

    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "small_business"
    STARTUP = "startup"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"


@dataclass
class BrandGuidelines:
    """Brand guidelines and compliance rules"""

    # Visual Identity
    primary_colors: list[str] = field(default_factory=lambda: ["#1A73E8", "#34A853"])
    secondary_colors: list[str] = field(default_factory=lambda: ["#EA4335", "#FBBC04"])
    font_family: str = "Inter, Arial, sans-serif"
    logo_variants: dict[str, str] = field(default_factory=dict)

    # Voice and Tone
    voice_attributes: list[str] = field(
        default_factory=lambda: ["professional", "approachable", "confident"]
    )
    tone_guidelines: dict[str, str] = field(default_factory=dict)
    approved_terminology: list[str] = field(default_factory=list)
    avoided_terminology: list[str] = field(default_factory=list)

    # Messaging Framework
    value_proposition: str = ""
    key_differentiators: list[str] = field(default_factory=list)
    proof_points: list[str] = field(default_factory=list)
    elevator_pitch_templates: dict[str, str] = field(default_factory=dict)

    # Compliance Rules
    legal_disclaimers: list[str] = field(default_factory=list)
    required_elements: list[str] = field(default_factory=list)
    channel_specific_rules: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Asset Management
    template_library: dict[str, str] = field(default_factory=dict)
    image_library: dict[str, str] = field(default_factory=dict)
    video_assets: dict[str, str] = field(default_factory=dict)

    def validate_content(self, content: str, channel: str) -> dict[str, Any]:
        """Validate content against brand guidelines"""
        compliance_score = 0.0
        violations = []
        suggestions = []

        # Check voice and tone
        for attribute in self.voice_attributes:
            if self._check_voice_attribute(content, attribute):
                compliance_score += 0.2
            else:
                violations.append(f"Content doesn't reflect {attribute} voice")

        # Check terminology
        for term in self.avoided_terminology:
            if term.lower() in content.lower():
                violations.append(f"Avoid using term: {term}")
                compliance_score -= 0.1

        # Channel-specific rules
        if channel in self.channel_specific_rules:
            channel_score = self._validate_channel_rules(content, channel)
            compliance_score += channel_score * 0.3

        compliance_score = max(0.0, min(1.0, compliance_score))

        return {
            "compliance_score": compliance_score,
            "compliance_level": self._score_to_level(compliance_score),
            "violations": violations,
            "suggestions": suggestions,
        }

    def _check_voice_attribute(self, content: str, attribute: str) -> bool:
        """Check if content reflects voice attribute"""
        # Simplified implementation - would use NLP in production
        attribute_keywords = {
            "professional": ["expertise", "proven", "industry-leading", "enterprise"],
            "approachable": ["easy", "simple", "friendly", "support"],
            "confident": ["guaranteed", "proven", "leading", "best-in-class"],
        }

        keywords = attribute_keywords.get(attribute, [])
        return any(keyword in content.lower() for keyword in keywords)

    def _validate_channel_rules(self, content: str, channel: str) -> float:
        """Validate channel-specific rules"""
        rules = self.channel_specific_rules.get(channel, {})
        score = 1.0

        # Example: SMS character limits
        if channel == "sms" and "max_length" in rules:
            if len(content) > rules["max_length"]:
                score -= 0.5

        return score

    def _score_to_level(self, score: float) -> BrandComplianceLevel:
        """Convert compliance score to level"""
        if score >= 0.9:
            return BrandComplianceLevel.EXCELLENT
        elif score >= 0.75:
            return BrandComplianceLevel.GOOD
        elif score >= 0.6:
            return BrandComplianceLevel.FAIR
        else:
            return BrandComplianceLevel.POOR


@dataclass
class MarketInsight:
    """Market intelligence and competitive insights"""

    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    category: str = ""  # competitive, industry, customer, opportunity
    confidence_level: float = 0.0  # 0.0 to 1.0
    impact_level: str = "medium"  # high, medium, low

    # Content
    summary: str = ""
    detailed_analysis: str = ""
    key_findings: list[str] = field(default_factory=list)
    supporting_data: list[dict[str, Any]] = field(default_factory=list)

    # Context
    industry: str = ""
    market_segment: MarketSegment = MarketSegment.MID_MARKET
    geographic_scope: str = "US"
    time_period: str = "current"

    # Sources and Attribution
    data_sources: list[str] = field(default_factory=list)
    external_references: list[str] = field(default_factory=list)
    internal_research: list[str] = field(default_factory=list)

    # Actionability
    recommended_actions: list[str] = field(default_factory=list)
    business_implications: list[str] = field(default_factory=list)
    urgency_level: str = "normal"  # urgent, high, normal, low

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "market_intelligence_agent"
    tags: list[str] = field(default_factory=list)

    def is_actionable(self) -> bool:
        """Check if insight has actionable recommendations"""
        return len(self.recommended_actions) > 0 and self.confidence_level > 0.6

    def get_priority_score(self) -> float:
        """Calculate priority score for insight ranking"""
        impact_weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        urgency_weights = {"urgent": 1.0, "high": 0.8, "normal": 0.5, "low": 0.2}

        impact_score = impact_weights.get(self.impact_level, 0.5)
        urgency_score = urgency_weights.get(self.urgency_level, 0.5)

        return (self.confidence_level * 0.4) + (impact_score * 0.4) + (urgency_score * 0.2)


@dataclass
class CampaignPerformance:
    """Campaign performance metrics and analytics"""

    campaign_id: str
    campaign_type: CampaignType
    measurement_period: str

    # Core Metrics
    impressions: int = 0
    opens: int = 0
    clicks: int = 0
    responses: int = 0
    conversions: int = 0

    # Rates
    open_rate: float = 0.0
    click_rate: float = 0.0
    response_rate: float = 0.0
    conversion_rate: float = 0.0

    # Financial Metrics
    cost_total: float = 0.0
    cost_per_impression: float = 0.0
    cost_per_click: float = 0.0
    cost_per_conversion: float = 0.0
    revenue_attributed: float = 0.0
    roi: float = 0.0

    # Engagement Quality
    average_engagement_time: float = 0.0  # seconds
    engagement_score: float = 0.0  # 0-100
    sentiment_score: float = 0.0  # -1 to 1

    # Audience Insights
    audience_segments: dict[str, int] = field(default_factory=dict)
    demographic_breakdown: dict[str, int] = field(default_factory=dict)
    geographic_performance: dict[str, float] = field(default_factory=dict)

    # A/B Testing Results
    variant_performance: dict[str, dict[str, float]] = field(default_factory=dict)
    statistical_significance: float = 0.0
    winning_variant: Optional[str] = None

    # Metadata
    measured_at: datetime = field(default_factory=datetime.now)
    data_sources: list[str] = field(default_factory=list)

    def calculate_effectiveness_score(self) -> float:
        """Calculate overall campaign effectiveness score"""
        # Weighted combination of key metrics
        effectiveness = (
            (self.conversion_rate * 0.4)
            + (self.engagement_score / 100 * 0.3)
            + (min(self.roi / 3.0, 1.0) * 0.2)  # Cap ROI contribution
            + (max(self.sentiment_score, 0) * 0.1)  # Only positive sentiment counts
        )
        return min(effectiveness, 1.0)

    def identify_optimization_opportunities(self) -> list[str]:
        """Identify areas for campaign optimization"""
        opportunities = []

        if self.open_rate < 0.25:
            opportunities.append("Optimize subject lines and sender reputation")

        if self.click_rate < 0.05:
            opportunities.append("Improve email content and call-to-action")

        if self.conversion_rate < 0.02:
            opportunities.append("Review landing page experience and offer")

        if self.roi < 2.0:
            opportunities.append("Reassess audience targeting and campaign costs")

        if self.engagement_score < 60:
            opportunities.append("Enhance content relevance and personalization")

        return opportunities


@dataclass
class CreativeCampaign:
    """Creative campaign structure and content"""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    campaign_type: CampaignType = CampaignType.EMAIL_NURTURE
    status: CampaignStatus = CampaignStatus.DRAFT

    # Target Audience
    target_segments: list[MarketSegment] = field(default_factory=list)
    prospect_criteria: dict[str, Any] = field(default_factory=dict)
    personalization_level: str = "basic"  # basic, advanced, hyper_personalized

    # Creative Elements
    subject_lines: list[str] = field(default_factory=list)
    message_variants: list[str] = field(default_factory=list)
    visual_assets: list[str] = field(default_factory=list)
    call_to_actions: list[str] = field(default_factory=list)

    # Multi-Channel Components
    email_template: Optional[str] = None
    sms_template: Optional[str] = None
    linkedin_template: Optional[str] = None
    video_script: Optional[str] = None
    gift_strategy: Optional[dict[str, Any]] = None

    # Testing and Optimization
    ab_test_variants: list[dict[str, Any]] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    optimization_goals: list[str] = field(default_factory=list)

    # Approval Workflow
    approval_required: bool = True
    approvers: list[str] = field(default_factory=list)
    approval_history: list[dict[str, Any]] = field(default_factory=list)
    brand_compliance_score: float = 0.0

    # Execution
    launch_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    execution_schedule: dict[str, Any] = field(default_factory=dict)

    # Performance Tracking
    performance_metrics: Optional[CampaignPerformance] = None
    learning_insights: list[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "creative_outreach_agent"
    tags: list[str] = field(default_factory=list)

    def submit_for_approval(self, approver: str) -> bool:
        """Submit campaign for approval"""
        if self.status != CampaignStatus.DRAFT:
            return False

        self.status = CampaignStatus.PENDING_APPROVAL
        self.approval_history.append(
            {
                "action": "submitted",
                "approver": approver,
                "timestamp": datetime.now(),
                "status": "pending",
            }
        )
        return True

    def approve(self, approver: str, notes: str = "") -> bool:
        """Approve the campaign"""
        if self.status != CampaignStatus.PENDING_APPROVAL:
            return False

        self.status = CampaignStatus.APPROVED
        self.approval_history.append(
            {
                "action": "approved",
                "approver": approver,
                "timestamp": datetime.now(),
                "notes": notes,
            }
        )
        return True

    def reject(self, approver: str, reason: str) -> bool:
        """Reject the campaign with feedback"""
        if self.status != CampaignStatus.PENDING_APPROVAL:
            return False

        self.status = CampaignStatus.DRAFT
        self.approval_history.append(
            {
                "action": "rejected",
                "approver": approver,
                "timestamp": datetime.now(),
                "reason": reason,
            }
        )
        return True


@dataclass
class MarketingContext:
    """Context for marketing operations and decision-making"""

    # Business Context
    company_info: dict[str, Any] = field(default_factory=dict)
    industry: str = ""
    target_markets: list[MarketSegment] = field(default_factory=list)
    competitive_landscape: list[str] = field(default_factory=list)

    # Brand Guidelines
    brand_guidelines: Optional[BrandGuidelines] = None

    # Campaign Context
    active_campaigns: list[str] = field(default_factory=list)
    campaign_history: list[dict[str, Any]] = field(default_factory=list)
    budget_constraints: dict[str, float] = field(default_factory=dict)

    # Audience Intelligence
    prospect_database: dict[str, Any] = field(default_factory=dict)
    segment_performance: dict[str, float] = field(default_factory=dict)
    personality_insights: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Market Intelligence
    recent_insights: list[MarketInsight] = field(default_factory=list)
    competitive_intelligence: dict[str, Any] = field(default_factory=dict)
    industry_trends: list[dict[str, Any]] = field(default_factory=list)

    # Performance Data
    channel_performance: dict[str, CampaignPerformance] = field(default_factory=dict)
    roi_by_segment: dict[str, float] = field(default_factory=dict)
    attribution_data: dict[str, Any] = field(default_factory=dict)

    # Integration Context
    connected_platforms: list[str] = field(default_factory=list)
    data_sources: list[str] = field(default_factory=list)
    sync_status: dict[str, datetime] = field(default_factory=dict)

    def get_high_priority_insights(self) -> list[MarketInsight]:
        """Get high-priority actionable insights"""
        return [
            insight
            for insight in self.recent_insights
            if insight.get_priority_score() > 0.7 and insight.is_actionable()
        ]

    def get_best_performing_segments(self, limit: int = 3) -> list[str]:
        """Get top performing market segments"""
        sorted_segments = sorted(self.segment_performance.items(), key=lambda x: x[1], reverse=True)
        return [segment for segment, _ in sorted_segments[:limit]]

    def update_sync_status(self, platform: str):
        """Update sync status for integrated platform"""
        self.sync_status[platform] = datetime.now()


@dataclass
class CampaignData:
    """Campaign execution data and results"""

    campaign: CreativeCampaign
    context: MarketingContext
    execution_log: list[dict[str, Any]] = field(default_factory=list)
    real_time_metrics: dict[str, Any] = field(default_factory=dict)

    def log_execution_event(self, event_type: str, details: dict[str, Any]):
        """Log campaign execution event"""
        self.execution_log.append(
            {"timestamp": datetime.now(), "event_type": event_type, "details": details}
        )

    def update_real_time_metric(self, metric: str, value: Any):
        """Update real-time campaign metric"""
        self.real_time_metrics[metric] = {"value": value, "timestamp": datetime.now()}
