#!/usr/bin/env python3
"""
Document Management Swarm - Specialized Agents
"""

from .document_discovery_agent import (
    DocumentDiscoveryAgent,
    discover_documents_with_neural_intelligence
)

from .document_classifier_agent import (
    DocumentClassifierAgent,
    classify_documents_with_intelligence
)

from .document_cleanup_agent import DocumentCleanupAgent

__all__ = [
    'DocumentDiscoveryAgent',
    'DocumentClassifierAgent', 
    'DocumentCleanupAgent',
    'discover_documents_with_neural_intelligence',
    'classify_documents_with_intelligence'
]