"""
Specialized Agent Classes

Domain-specific agents with optimized configurations for different use cases.
"""

from .coder_agent import CoderAgent
from .planner_agent import PlannerAgent
from .researcher_agent import ResearchAgent
from .security_agent import SecurityAgent

__all__ = [
    'PlannerAgent',
    'CoderAgent',
    'ResearchAgent',
    'SecurityAgent'
]
