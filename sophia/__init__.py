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

__version__ = "4.0.0"
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
    "SOPHIAMCPClient"
]

