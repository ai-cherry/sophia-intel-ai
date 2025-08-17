"""
SOPHIA Intel Domain-Driven Architecture
Organized by business capabilities for maintainability and scalability
"""

# Domain modules
from . import chat
from . import research
from . import orchestration
from . import mcp
from . import persona
from . import monitoring

__all__ = [
    "chat",
    "research", 
    "orchestration",
    "mcp",
    "persona",
    "monitoring"
]

