"""
Search Quality Pipeline - Advanced search optimization for Sophia AI
This package provides sophisticated search quality components:
- Contextual bandit for provider selection
- Reciprocal Rank Fusion for result merging
- Cross-encoder reranking for semantic quality
"""
from .contextual_bandit import (
    BanditConfig,
    ProductionContextualBandit,
    ProviderContext,
    ProviderMetrics,
    create_contextual_bandit,
)
from .cross_encoder_reranking import (
    OptimizedCrossEncoderReranker,
    RerankingConfig,
    RerankingMetrics,
    RerankingResult,
    create_cross_encoder_reranker,
)
from .reciprocal_rank_fusion import (
    FusionMetrics,
    OptimizedReciprocalRankFusion,
    ProviderResults,
    RRFConfig,
    SearchResult,
    create_rrf_fusion,
)
__version__ = "1.0.0"
__all__ = [
    # Contextual Bandit
    "ProductionContextualBandit",
    "ProviderContext",
    "ProviderMetrics",
    "BanditConfig",
    "create_contextual_bandit",
    # Reciprocal Rank Fusion
    "OptimizedReciprocalRankFusion",
    "SearchResult",
    "ProviderResults",
    "RRFConfig",
    "FusionMetrics",
    "create_rrf_fusion",
    # Cross-Encoder Reranking
    "OptimizedCrossEncoderReranker",
    "RerankingResult",
    "RerankingConfig",
    "RerankingMetrics",
    "create_cross_encoder_reranker",
]
