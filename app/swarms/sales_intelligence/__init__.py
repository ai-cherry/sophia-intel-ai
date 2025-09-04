"""
Sales Intelligence Swarm

A comprehensive real-time sales intelligence system that provides:
- Live Gong call monitoring and analysis
- Immediate feedback and coaching
- Advanced sentiment and competitive intelligence
- Risk assessment and deal probability scoring
- Real-time dashboard with live metrics
- Natural language integration with Universal Sophia
"""

from .agents import (
    TranscriptionAgent,
    SentimentAgent,
    CompetitiveAgent,
    RiskAssessmentAgent,
    CoachingAgent,
    SummaryAgent,
    SalesAgentOrchestrator,
    create_sales_intelligence_swarm
)

from .gong_realtime import (
    GongRealtimeConnector,
    GongWebSocketHandler,
    RealtimeCallData,
    CallMetadata,
    TranscriptSegment,
    CallParticipant,
    CallEvent,
    create_gong_connector
)

from .feedback_engine import (
    ImmediateFeedbackEngine,
    SalesFeedbackSystem,
    FeedbackMessage,
    FeedbackType,
    DeliveryChannel,
    CoachingPrompt,
    LiveDashboardUpdater,
    NotificationSystem
)

from .dashboard import (
    SalesIntelligenceDashboard,
    MetricsCalculator,
    WebSocketManager,
    DashboardMetric,
    CallSummaryCard,
    MetricType,
    create_dashboard_app,
    get_dashboard_html
)

from .sophia_integration import (
    SalesIntelligenceOrchestrator,
    NaturalLanguageProcessor,
    SalesQuery,
    SalesCommandType,
    create_sales_intelligence_commands
)

__version__ = "1.0.0"
__author__ = "Sophia Intelligence Team"

__all__ = [
    # Agents
    "TranscriptionAgent",
    "SentimentAgent", 
    "CompetitiveAgent",
    "RiskAssessmentAgent",
    "CoachingAgent",
    "SummaryAgent",
    "SalesAgentOrchestrator",
    "create_sales_intelligence_swarm",
    
    # Gong Integration
    "GongRealtimeConnector",
    "GongWebSocketHandler",
    "RealtimeCallData",
    "CallMetadata",
    "TranscriptSegment",
    "CallParticipant",
    "CallEvent",
    "create_gong_connector",
    
    # Feedback Engine
    "ImmediateFeedbackEngine",
    "SalesFeedbackSystem",
    "FeedbackMessage",
    "FeedbackType",
    "DeliveryChannel",
    "CoachingPrompt",
    "LiveDashboardUpdater",
    "NotificationSystem",
    
    # Dashboard
    "SalesIntelligenceDashboard",
    "MetricsCalculator",
    "WebSocketManager",
    "DashboardMetric",
    "CallSummaryCard",
    "MetricType",
    "create_dashboard_app",
    "get_dashboard_html",
    
    # Sophia Integration
    "SalesIntelligenceOrchestrator",
    "NaturalLanguageProcessor",
    "SalesQuery",
    "SalesCommandType",
    "create_sales_intelligence_commands"
]