"""
Modular Swarm Patterns for Advanced Agent Coordination.

This package provides reusable patterns for sophisticated multi-agent systems.
Each pattern implements a specific coordination strategy that can be composed
together to create complex swarm behaviors.

Patterns:
- adversarial_debate: Structured debate for solution improvement
- quality_gates: Quality thresholds with automatic retry
- strategy_archive: Historical strategy tracking and reuse
- safety_boundaries: Risk assessment and mitigation
- dynamic_roles: Adaptive agent specialization
- consensus_mechanisms: Sophisticated tie-breaking and voting
- adaptive_parameters: Self-tuning system behavior
- knowledge_transfer: Cross-swarm learning
"""

from .adaptive_parameters import AdaptiveParametersPattern
from .adversarial_debate import AdversarialDebatePattern
from .base import PatternConfig, PatternResult, SwarmPattern
from .composer import SwarmComposer
from .consensus import ConsensusPattern
from .dynamic_roles import DynamicRolesPattern
from .knowledge_transfer import KnowledgeTransferPattern
from .quality_gates import QualityGatesPattern
from .safety_boundaries import SafetyBoundariesPattern
from .strategy_archive import StrategyArchivePattern

__all__ = [
    'SwarmPattern',
    'PatternConfig',
    'PatternResult',
    'AdversarialDebatePattern',
    'QualityGatesPattern',
    'StrategyArchivePattern',
    'SafetyBoundariesPattern',
    'DynamicRolesPattern',
    'ConsensusPattern',
    'AdaptiveParametersPattern',
    'KnowledgeTransferPattern',
    'SwarmComposer'
]
