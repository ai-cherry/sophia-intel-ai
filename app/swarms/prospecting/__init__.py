"""
Prospecting Intelligence Microswarm

Advanced prospecting agents for sales intelligence including:
- Progressive personality analysis (basic -> DISC -> predictive -> psychological)
- Deep executive research and profiling
- LinkedIn activity and behavior analysis
- Email pattern recognition and communication style analysis
- Predictive outreach optimization and timing
"""

from .behavioral_analysis import (
    DecisionMakingAnalyzer,
    EmailPatternAnalyzer,
    EngagementBehaviorAnalyzer,
    LinkedInActivityAnalyzer,
)
from .models import (
    BehaviorPattern,
    PersonalityProfile,
    ProspectIntelligence,
    ResearchInsight,
)
from .personality_analysis import (
    AdvancedPsychProfileAgent,
    BasicPersonalityAgent,
    DISCProfileAnalyzer,
    PredictivePersonalityEngine,
)
from .prospecting_orchestrator import (
    ProspectEnrichmentPipeline,
    ProspectingSwarmOrchestrator,
)
from .research_agents import (
    CompanyIntelligenceAgent,
    CompetitiveResearchAgent,
    ExecutiveResearchAgent,
    IndustryAnalysisAgent,
)

__all__ = [
    "BasicPersonalityAgent",
    "DISCProfileAnalyzer",
    "PredictivePersonalityEngine",
    "AdvancedPsychProfileAgent",
    "ExecutiveResearchAgent",
    "CompanyIntelligenceAgent",
    "IndustryAnalysisAgent",
    "CompetitiveResearchAgent",
    "LinkedInActivityAnalyzer",
    "EmailPatternAnalyzer",
    "EngagementBehaviorAnalyzer",
    "DecisionMakingAnalyzer",
    "ProspectingSwarmOrchestrator",
    "ProspectEnrichmentPipeline",
    "PersonalityProfile",
    "ProspectIntelligence",
    "BehaviorPattern",
    "ResearchInsight",
]
