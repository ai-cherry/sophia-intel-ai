"""
SOPHIA Intel Enhanced Agent System
Fixed import structure to prevent startup crashes
"""

# Enhanced agents (fallback imports with error handling)
try:
    from .persona_manager import PersonaManager
except ImportError:
    PersonaManager = None

try:
    from .search_engine import DeepSearchEngine  
except ImportError:
    DeepSearchEngine = None

try:
    from .swarm_manager import SwarmManager
except ImportError:
    SwarmManager = None

# Legacy agents (commented out to prevent phi import errors)
# from .swarm_coordinator import SwarmCoordinator
# from .research_agent import ResearchAgent
# from .coding_agent import CodingAgent
# from .deployment_agent import DeploymentAgent
# from .monitoring_agent import MonitoringAgent

__all__ = [
    'PersonaManager',
    'DeepSearchEngine', 
    'SwarmManager'
]
