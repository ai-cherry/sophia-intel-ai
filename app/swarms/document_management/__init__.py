#!/usr/bin/env python3
"""
Revolutionary Document Management Swarm

This package implements a revolutionary AI-powered document management system featuring:

- Neural Documentation Networks: Documents form intelligent connections
- Quantum Document States: Adaptive presentation based on agent type  
- Swarm Intelligence: Collective intelligence for document optimization
- AI-Friendliness Scoring: Comprehensive quality assessment for AI consumption
- Automated Cleanup: Safe, intelligent document lifecycle management
- Living Knowledge Evolution: Documents that improve themselves over time

Key Components:
- DocumentDiscoveryAgent: Finds and catalogs documents with neural pathfinding
- DocumentClassifierAgent: AI-powered classification and scoring
- DocumentCleanupAgent: Safe automated cleanup with comprehensive safety checks
- DocumentSwarmOrchestrator: Coordinates all swarm operations

Usage:
    from app.swarms.document_management import unleash_document_management_swarm
    
    results = await unleash_document_management_swarm(["/path/to/docs"])
"""

from .core.document_swarm_orchestrator import (
    DocumentSwarmOrchestrator,
    SwarmConfiguration,
    unleash_document_management_swarm
)

from .agents.document_discovery_agent import (
    DocumentDiscoveryAgent,
    discover_documents_with_neural_intelligence
)

from .agents.document_classifier_agent import (
    DocumentClassifierAgent,
    classify_documents_with_intelligence
)

from .agents.document_cleanup_agent import DocumentCleanupAgent

from .models.document import (
    DocumentType,
    DocumentStatus,
    DocumentMetadata,
    AIFriendlinessScore,
    DocumentClassification,
    CleanupPolicy
)

from .core.scoring_engine import (
    AIFriendlinessScorer,
    DocumentClassificationEngine
)

__version__ = "1.0.0"
__author__ = "Claude & Sophia Intelligence Platform"

__all__ = [
    # Main orchestration
    'DocumentSwarmOrchestrator',
    'SwarmConfiguration', 
    'unleash_document_management_swarm',
    
    # Specialized agents
    'DocumentDiscoveryAgent',
    'DocumentClassifierAgent', 
    'DocumentCleanupAgent',
    
    # Utility functions
    'discover_documents_with_neural_intelligence',
    'classify_documents_with_intelligence',
    
    # Data models
    'DocumentType',
    'DocumentStatus',
    'DocumentMetadata',
    'AIFriendlinessScore',
    'DocumentClassification',
    'CleanupPolicy',
    
    # Core engines
    'AIFriendlinessScorer',
    'DocumentClassificationEngine'
]