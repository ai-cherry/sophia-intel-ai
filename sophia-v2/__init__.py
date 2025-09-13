"""
Sophia v2 - Business Operations Platform
=========================================
A specialized AI system for all business operations including project management,
customer support, analytics, and documentation.
Core Capabilities:
- Project management and planning
- Customer support and ticketing
- Business analytics and reporting
- Documentation and knowledge management
"""
__version__ = "2.0.0"
__author__ = "Sophia Development Team"
from .core import AnalyticsEngine, DocumentationHub, ProjectManager, SupportSystem
from .integrations import IntegrationManager
from .workflows import WorkflowEngine
__all__ = [
    "ProjectManager",
    "SupportSystem",
    "AnalyticsEngine",
    "DocumentationHub",
    "IntegrationManager",
    "WorkflowEngine",
]
