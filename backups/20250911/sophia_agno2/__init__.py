"""Sophia BI-domain Agno 2.0 scaffolding (separate from Builder).

Provides a minimal factory for BI consultant-style agents that operate
only over business data/integrations (no repo/git tools). Uses Agno v2
when available, degrades to stubs otherwise.
"""

from .factory import SophiaAgentFactory, BIConsultantSpec

__all__ = ["SophiaAgentFactory", "BIConsultantSpec"]

