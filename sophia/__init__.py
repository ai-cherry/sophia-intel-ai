"""
SOPHIA V4 - AI Orchestra Conductor Platform
Core package for the ultimate AI orchestrator.
"""

from .core.ultimate_model_router import UltimateModelRouter, ModelConfig, TaskType
from .core.api_manager import SOPHIAAPIManager, ServiceClient
from .core.sophia_base_agent import SOPHIABaseAgent

__version__ = "4.0.0"
__author__ = "SOPHIA AI Team"

__all__ = [
    "UltimateModelRouter",
    "ModelConfig", 
    "TaskType",
    "SOPHIAAPIManager",
    "ServiceClient",
    "SOPHIABaseAgent"
]

