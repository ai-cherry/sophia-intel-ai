"""
Sophia AI Production RAG Pipeline
Phase 1: LangChain Integration - Replace Mock Implementations
This module provides production-ready RAG capabilities including:
- Hybrid semantic + structured search
- Multi-source data ingestion (Gong, HubSpot, Salesforce, Slack)
- Real-time embedding generation
- Caching and performance optimization
"""
from embeddings import EmbeddingService
from ingestion import ProductionIngestionPipeline
from pipeline import RAGPipeline
from query import HybridRAGRetriever
__all__ = [
    "RAGPipeline",
    "ProductionIngestionPipeline",
    "HybridRAGRetriever",
    "EmbeddingService",
]
__version__ = "1.0.0"
