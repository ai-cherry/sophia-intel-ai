"""
SOPHIA V4 - AI Orchestra Conductor Platform
Core package for the ultimate AI orchestrator.
"""

from .core.ultimate_model_router import UltimateModelRouter, ModelConfig, TaskType
from .core.api_manager import SOPHIAAPIManager, ServiceClient
from .core.sophia_base_agent import SOPHIABaseAgent
from .core.github_master import SOPHIAGitHubMaster, GitHubRepoInfo, GitHubCommitInfo, GitHubPRInfo
from .core.fly_master import SOPHIAFlyMaster, FlyAppInfo, FlyReleaseInfo, FlyMachineInfo
from .core.research_master import SOPHIAResearchMaster
from .core.business_master import SOPHIABusinessMaster
from .core.memory_master import SOPHIAMemoryMaster
from .core.mcp_client import SOPHIAMCPClient
from .core.feedback_master import SOPHIAFeedbackMaster, FeedbackRecord, FeedbackSummary
from .core.performance_monitor import SOPHIAPerformanceMonitor, PerformanceMetric, ServiceStats
from .core.lambda_master import SOPHIALambdaMaster, LambdaInstance, LambdaInstanceType, LambdaJob
from .core.chatops_router import SOPHIAChatOpsRouter, ChatMode, ExecutionPlan, ParsedIntent

# NEW: Action Engine Framework (v4.2)
from .core.action_engine import ActionEngine, ActionResult, ActionStatus, ResearchResult

# Import integrations
from .integrations.asana_client import AsanaClient, AsanaProject, AsanaTask
from .integrations.linear_client import LinearClient, LinearTeam, LinearIssue
from .integrations.notion_client import NotionClient, NotionDatabase, NotionPage
from .integrations.gong_client import GongClient, GongCall, GongCallSummary

__version__ = "4.2.0"
__author__ = "SOPHIA AI Team"

__all__ = [
    "UltimateModelRouter",
    "ModelConfig", 
    "TaskType",
    "SOPHIAAPIManager",
    "ServiceClient",
    "SOPHIABaseAgent",
    "SOPHIAGitHubMaster",
    "GitHubRepoInfo",
    "GitHubCommitInfo", 
    "GitHubPRInfo",
    "SOPHIAFlyMaster",
    "FlyAppInfo",
    "FlyReleaseInfo",
    "FlyMachineInfo",
    "SOPHIAResearchMaster",
    "SOPHIABusinessMaster",
    "SOPHIAMemoryMaster",
    "SOPHIAMCPClient",
    "SOPHIAFeedbackMaster",
    "FeedbackRecord",
    "FeedbackSummary",
    "SOPHIAPerformanceMonitor",
    "PerformanceMetric",
    "ServiceStats",
    "SOPHIALambdaMaster",
    "LambdaInstance",
    "LambdaInstanceType",
    "LambdaJob",
    "SOPHIAChatOpsRouter",
    "ChatMode",
    "ExecutionPlan",
    "ParsedIntent",
    # NEW: Action Engine Framework
    "ActionEngine",
    "ActionResult", 
    "ActionStatus",
    "ResearchResult",
    # Integrations
    "AsanaClient",
    "AsanaProject",
    "AsanaTask",
    "LinearClient",
    "LinearTeam",
    "LinearIssue",
    "NotionClient",
    "NotionDatabase",
    "NotionPage",
    "GongClient",
    "GongCall",
    "GongCallSummary"
]

