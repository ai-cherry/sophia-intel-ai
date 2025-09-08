"""
Prospecting Intelligence Models

Data models for prospect analysis, personality profiling, and research insights.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class PersonalityType(str, Enum):
    """DISC personality types"""

    DOMINANT = "dominant"
    INFLUENTIAL = "influential"
    STEADY = "steady"
    CONSCIENTIOUS = "conscientious"
    # Combined types
    DOMINANCE_INFLUENCE = "dominance_influence"
    INFLUENCE_STEADINESS = "influence_steadiness"
    STEADINESS_CONSCIENTIOUSNESS = "steadiness_conscientiousness"
    CONSCIENTIOUSNESS_DOMINANCE = "conscientiousness_dominance"


class CommunicationStyle(str, Enum):
    """Communication style preferences"""

    DIRECT = "direct"
    COLLABORATIVE = "collaborative"
    SUPPORTIVE = "supportive"
    ANALYTICAL = "analytical"
    RELATIONSHIP_FOCUSED = "relationship_focused"
    RESULTS_FOCUSED = "results_focused"


class DecisionMakingStyle(str, Enum):
    """Decision making approach"""

    QUICK_DECISIVE = "quick_decisive"
    CONSENSUS_BUILDING = "consensus_building"
    DATA_DRIVEN = "data_driven"
    INTUITIVE = "intuitive"
    RISK_AVERSE = "risk_averse"
    RISK_TAKING = "risk_taking"


class EngagementLevel(str, Enum):
    """Engagement level with content"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    INACTIVE = "inactive"


class ResearchSource(str, Enum):
    """Sources of research data"""

    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    NEWS_ARTICLES = "news_articles"
    PRESS_RELEASES = "press_releases"
    SOCIAL_MEDIA = "social_media"
    PUBLIC_RECORDS = "public_records"
    INDUSTRY_REPORTS = "industry_reports"
    EMAIL_INTERACTIONS = "email_interactions"
    WEB_BEHAVIOR = "web_behavior"


@dataclass
class BehaviorPattern:
    """Behavioral pattern detected from digital activities"""

    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: str = ""  # engagement, communication, decision_timing
    pattern_name: str = ""
    description: str = ""

    # Pattern details
    frequency: str = ""  # daily, weekly, monthly
    timing_patterns: list[str] = field(default_factory=list)
    consistency_score: float = 0.0  # 0-1
    confidence_level: float = 0.0  # 0-1

    # Supporting data
    data_points: int = 0
    observation_period_days: int = 0
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)

    # Predictive insights
    predicts: list[str] = field(default_factory=list)  # What this pattern predicts
    correlation_strength: float = 0.0

    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    source: ResearchSource = ResearchSource.LINKEDIN

    def add_evidence(self, evidence: dict[str, Any]):
        """Add supporting evidence for pattern"""
        self.supporting_evidence.append({**evidence, "timestamp": datetime.now()})
        self.data_points += 1
        self.last_updated = datetime.now()

    def update_confidence(self, new_confidence: float):
        """Update confidence level based on new data"""
        # Weighted average with existing confidence
        weight = 0.7  # Weight for new evidence
        self.confidence_level = self.confidence_level * (1 - weight) + new_confidence * weight
        self.last_updated = datetime.now()


@dataclass
class PersonalityProfile:
    """Comprehensive personality profile for prospect"""

    prospect_id: str = ""
    profile_id: str = field(default_factory=lambda: str(uuid4()))

    # Basic personality indicators
    primary_disc_type: Optional[PersonalityType] = None
    secondary_disc_type: Optional[PersonalityType] = None
    disc_scores: dict[str, float] = field(default_factory=dict)  # D, I, S, C scores

    # Communication preferences
    communication_style: CommunicationStyle = CommunicationStyle.DIRECT
    preferred_contact_methods: list[str] = field(default_factory=list)
    response_timing_patterns: dict[str, Any] = field(default_factory=dict)

    # Decision making
    decision_making_style: DecisionMakingStyle = DecisionMakingStyle.DATA_DRIVEN
    decision_factors: list[str] = field(default_factory=list)
    influence_network: list[str] = field(default_factory=list)  # Key influencers

    # Behavioral patterns
    behavior_patterns: list[BehaviorPattern] = field(default_factory=list)
    engagement_patterns: dict[str, Any] = field(default_factory=dict)
    activity_patterns: dict[str, Any] = field(default_factory=dict)

    # Advanced psychological insights
    risk_tolerance: float = 0.5  # 0-1 scale
    innovation_adoption: str = "early_majority"  # innovator, early_adopter, etc.
    social_proof_sensitivity: float = 0.5
    authority_responsiveness: float = 0.5

    # Confidence and reliability
    profile_confidence: float = 0.0  # Overall confidence in profile
    data_quality_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    analysis_version: str = "1.0"

    # Data sources
    data_sources: list[ResearchSource] = field(default_factory=list)
    linkedin_data_points: int = 0
    email_data_points: int = 0
    web_behavior_data_points: int = 0

    def get_primary_disc_traits(self) -> list[str]:
        """Get primary DISC traits and characteristics"""
        trait_mapping = {
            PersonalityType.DOMINANT: [
                "Results-focused",
                "Direct communication",
                "Quick decisions",
                "Competitive",
                "Goal-oriented",
                "Challenges status quo",
            ],
            PersonalityType.INFLUENTIAL: [
                "People-focused",
                "Enthusiastic",
                "Optimistic",
                "Persuasive",
                "Collaborative",
                "Relationship builder",
            ],
            PersonalityType.STEADY: [
                "Team-oriented",
                "Patient",
                "Reliable",
                "Supportive",
                "Consistent",
                "Values harmony",
            ],
            PersonalityType.CONSCIENTIOUS: [
                "Detail-oriented",
                "Analytical",
                "Quality-focused",
                "Systematic",
                "Careful",
                "Standards-driven",
            ],
        }

        return trait_mapping.get(self.primary_disc_type, [])

    def get_optimal_outreach_approach(self) -> dict[str, Any]:
        """Get personalized outreach recommendations"""
        if not self.primary_disc_type:
            return {"approach": "generic", "confidence": 0.0}

        approach_mapping = {
            PersonalityType.DOMINANT: {
                "tone": "direct_results_focused",
                "message_length": "concise",
                "value_proposition": "ROI_and_efficiency",
                "call_to_action": "strong_direct",
                "timing": "business_hours",
                "channel_preference": ["email", "phone"],
            },
            PersonalityType.INFLUENTIAL: {
                "tone": "enthusiastic_collaborative",
                "message_length": "moderate",
                "value_proposition": "innovation_and_relationships",
                "call_to_action": "collaborative",
                "timing": "flexible",
                "channel_preference": ["linkedin", "email", "social"],
            },
            PersonalityType.STEADY: {
                "tone": "supportive_reliable",
                "message_length": "detailed",
                "value_proposition": "stability_and_support",
                "call_to_action": "gentle_supportive",
                "timing": "consistent",
                "channel_preference": ["email", "referral"],
            },
            PersonalityType.CONSCIENTIOUS: {
                "tone": "analytical_detailed",
                "message_length": "comprehensive",
                "value_proposition": "quality_and_accuracy",
                "call_to_action": "informational",
                "timing": "planned",
                "channel_preference": ["email", "documentation"],
            },
        }

        approach = approach_mapping.get(self.primary_disc_type, {})
        approach["confidence"] = self.profile_confidence
        return approach

    def update_profile_confidence(self):
        """Update overall profile confidence based on data quality"""
        confidence_factors = []

        # Data quantity
        total_data_points = (
            self.linkedin_data_points + self.email_data_points + self.web_behavior_data_points
        )

        if total_data_points >= 50:
            confidence_factors.append(0.9)
        elif total_data_points >= 20:
            confidence_factors.append(0.7)
        elif total_data_points >= 10:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)

        # Data source diversity
        source_diversity = len(self.data_sources) / len(ResearchSource)
        confidence_factors.append(source_diversity)

        # Pattern consistency
        if self.behavior_patterns:
            avg_pattern_confidence = sum(p.confidence_level for p in self.behavior_patterns) / len(
                self.behavior_patterns
            )
            confidence_factors.append(avg_pattern_confidence)

        # DISC score confidence
        if self.disc_scores:
            primary_score = max(self.disc_scores.values()) if self.disc_scores else 0.0
            score_confidence = min(primary_score / 0.7, 1.0)  # Normalize around 0.7
            confidence_factors.append(score_confidence)

        self.profile_confidence = sum(confidence_factors) / len(confidence_factors)
        self.data_quality_score = self.profile_confidence
        self.last_updated = datetime.now()


@dataclass
class ResearchInsight:
    """Research insight about a prospect or company"""

    insight_id: str = field(default_factory=lambda: str(uuid4()))
    prospect_id: str = ""
    company: str = ""

    # Insight details
    insight_type: str = ""  # financial, strategic, operational, competitive
    category: str = ""  # news, press_release, financial_report, social_activity
    title: str = ""
    summary: str = ""
    detailed_analysis: str = ""

    # Business relevance
    relevance_score: float = 0.0  # 0-1
    business_impact: str = "medium"  # high, medium, low
    actionability: str = "medium"  # high, medium, low
    urgency: str = "normal"  # urgent, high, normal, low

    # Context
    source: ResearchSource = ResearchSource.NEWS_ARTICLES
    source_url: str = ""
    publication_date: Optional[datetime] = None
    author: str = ""

    # Tags and categorization
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    entities_mentioned: list[str] = field(default_factory=list)

    # Analysis results
    sentiment: float = 0.0  # -1 to 1
    confidence: float = 0.0  # 0-1
    related_insights: list[str] = field(default_factory=list)  # Related insight IDs

    # Outreach recommendations
    outreach_angle: str = ""
    message_themes: list[str] = field(default_factory=list)
    talking_points: list[str] = field(default_factory=list)

    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_by: str = "research_agent"

    def is_current(self) -> bool:
        """Check if insight is still current and relevant"""
        if self.expiry_date and datetime.now() > self.expiry_date:
            return False

        # Consider insights older than 90 days as potentially stale
        if self.publication_date:
            age_days = (datetime.now() - self.publication_date).days
            if age_days > 90:
                return False

        return True

    def get_outreach_value(self) -> float:
        """Calculate outreach value score for this insight"""
        factors = [
            self.relevance_score * 0.3,
            ({"high": 1.0, "medium": 0.6, "low": 0.2}.get(self.business_impact, 0.5)) * 0.3,
            ({"high": 1.0, "medium": 0.6, "low": 0.2}.get(self.actionability, 0.5)) * 0.2,
            self.confidence * 0.2,
        ]

        return sum(factors)

    def generate_outreach_recommendations(self) -> dict[str, Any]:
        """Generate specific outreach recommendations based on insight"""
        recommendations = {
            "primary_angle": self.outreach_angle,
            "message_hooks": self.message_themes,
            "conversation_starters": self.talking_points,
            "timing_recommendation": "immediate" if self.urgency == "urgent" else "normal",
            "channel_recommendation": ["email", "linkedin"],
            "follow_up_strategy": [],
        }

        # Add follow-up strategy based on insight type
        if self.insight_type == "financial":
            recommendations["follow_up_strategy"].append("Share relevant ROI case studies")
        elif self.insight_type == "strategic":
            recommendations["follow_up_strategy"].append("Provide strategic partnership insights")
        elif self.insight_type == "operational":
            recommendations["follow_up_strategy"].append("Offer operational efficiency solutions")

        return recommendations


@dataclass
class ProspectIntelligence:
    """Comprehensive intelligence profile for a prospect"""

    prospect_id: str = field(default_factory=lambda: str(uuid4()))

    # Basic information
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""

    # Professional information
    current_company: str = ""
    current_title: str = ""
    department: str = ""
    seniority_level: str = ""
    industry: str = ""
    company_size: str = ""

    # Personality and behavior
    personality_profile: Optional[PersonalityProfile] = None
    behavior_patterns: list[BehaviorPattern] = field(default_factory=list)
    communication_preferences: dict[str, Any] = field(default_factory=dict)

    # Research insights
    research_insights: list[ResearchInsight] = field(default_factory=list)
    company_insights: list[ResearchInsight] = field(default_factory=list)
    industry_insights: list[ResearchInsight] = field(default_factory=list)

    # Engagement history
    engagement_score: float = 0.0  # 0-1
    last_engagement: Optional[datetime] = None
    engagement_history: list[dict[str, Any]] = field(default_factory=list)
    response_rate: float = 0.0
    preferred_engagement_channels: list[str] = field(default_factory=list)

    # Scoring and prioritization
    lead_score: int = 0
    fit_score: float = 0.0  # How well they fit our ICP
    intent_score: float = 0.0  # Buying intent indicators
    timing_score: float = 0.0  # How likely they are to buy now

    # Opportunity assessment
    estimated_deal_size: float = 0.0
    decision_timeline: str = ""  # 3-6 months, 6-12 months, etc.
    budget_authority: str = ""  # influencer, decision_maker, economic_buyer
    pain_points: list[str] = field(default_factory=list)

    # Competitive landscape
    current_solutions: list[str] = field(default_factory=list)
    competitive_threats: list[str] = field(default_factory=list)
    switching_barriers: list[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    last_researched: Optional[datetime] = None
    data_freshness_score: float = 0.0
    intelligence_confidence: float = 0.0

    def get_outreach_priority(self) -> float:
        """Calculate outreach priority score"""
        priority_factors = [
            self.fit_score * 0.3,
            self.intent_score * 0.3,
            self.timing_score * 0.2,
            (self.lead_score / 100) * 0.2,  # Normalize lead score
        ]

        return sum(priority_factors)

    def get_personalized_outreach_strategy(self) -> dict[str, Any]:
        """Get comprehensive personalized outreach strategy"""
        strategy = {
            "priority_score": self.get_outreach_priority(),
            "approach": "generic",
            "channels": ["email"],
            "timing": "business_hours",
            "message_themes": [],
            "value_propositions": [],
            "conversation_starters": [],
            "follow_up_cadence": "standard",
        }

        # Enhance with personality profile if available
        if self.personality_profile:
            personality_approach = self.personality_profile.get_optimal_outreach_approach()
            strategy.update(personality_approach)

        # Add insights-based recommendations
        high_value_insights = [
            insight for insight in self.research_insights if insight.get_outreach_value() > 0.7
        ]

        if high_value_insights:
            strategy["message_themes"] = []
            strategy["conversation_starters"] = []

            for insight in high_value_insights[:3]:  # Top 3 insights
                insight_recs = insight.generate_outreach_recommendations()
                strategy["message_themes"].extend(insight_recs["message_hooks"])
                strategy["conversation_starters"].extend(insight_recs["conversation_starters"])

        # Adjust based on engagement history
        if self.engagement_history:
            last_engagement = self.engagement_history[-1]
            if last_engagement.get("outcome") == "no_response":
                strategy["channels"] = ["linkedin", "phone"]  # Try different channels
                strategy["follow_up_cadence"] = "extended"

        return strategy

    def update_intelligence_confidence(self):
        """Update overall intelligence confidence score"""
        confidence_factors = []

        # Personality profile confidence
        if self.personality_profile:
            confidence_factors.append(self.personality_profile.profile_confidence)

        # Research insights quality
        if self.research_insights:
            avg_insight_confidence = sum(
                insight.confidence for insight in self.research_insights
            ) / len(self.research_insights)
            confidence_factors.append(avg_insight_confidence)

        # Data freshness
        if self.last_researched:
            days_since_research = (datetime.now() - self.last_researched).days
            freshness = max(0, 1 - (days_since_research / 30))  # 30-day decay
            confidence_factors.append(freshness)

        # Engagement data quality
        if self.engagement_history:
            engagement_data_quality = min(len(self.engagement_history) / 10, 1.0)
            confidence_factors.append(engagement_data_quality)

        if confidence_factors:
            self.intelligence_confidence = sum(confidence_factors) / len(confidence_factors)
            self.data_freshness_score = confidence_factors[-1] if confidence_factors else 0.0

        self.last_updated = datetime.now()

    def needs_research_refresh(self) -> bool:
        """Determine if prospect needs fresh research"""
        if not self.last_researched:
            return True

        days_since_research = (datetime.now() - self.last_researched).days

        # High-priority prospects need more frequent updates
        priority = self.get_outreach_priority()

        if priority > 0.8:
            return days_since_research > 7  # Weekly refresh for top prospects
        elif priority > 0.6:
            return days_since_research > 14  # Bi-weekly for high prospects
        else:
            return days_since_research > 30  # Monthly for others
