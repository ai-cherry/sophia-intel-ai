"""
Marketing Intelligence Microswarm

Comprehensive marketing automation and intelligence agents for:
- Brand consistency management
- Market intelligence and competitive analysis
- Campaign automation and optimization
- Creative outreach orchestration
- Performance analytics and insights
"""

from .agents import (
    BrandConsistencyAgent,
    CampaignAutomationAgent,
    CreativeOutreachAgent,
    MarketIntelligenceAgent,
    PerformanceAnalyticsAgent,
)
from .models import BrandGuidelines, CampaignData, CreativeCampaign, MarketingContext, MarketInsight
from .orchestrator import MarketingSwarmOrchestrator

__all__ = [
    "BrandConsistencyAgent",
    "MarketIntelligenceAgent",
    "CampaignAutomationAgent",
    "CreativeOutreachAgent",
    "PerformanceAnalyticsAgent",
    "MarketingSwarmOrchestrator",
    "MarketingContext",
    "CampaignData",
    "BrandGuidelines",
    "MarketInsight",
    "CreativeCampaign",
]
