"""
Reciprocal Rank Fusion (RRF) for Search Result Merging
Combines results from multiple search providers with optimized ranking
"""

import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result with metadata"""

    id: str  # Unique identifier for deduplication
    title: str
    content: str
    url: str
    score: float  # Original provider score
    provider: str
    rank: int  # Original rank from provider (1-based)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Generate ID from URL if not provided
        if not self.id:
            self.id = hashlib.md5(self.url.encode()).hexdigest()


@dataclass
class ProviderResults:
    """Results from a single search provider"""

    provider: str
    results: List[SearchResult]
    total_results: int
    latency_ms: float
    cost_cents: float = 0
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RRFConfig:
    """Configuration for Reciprocal Rank Fusion"""

    k_value: float = 60.0  # RRF constant, higher = less emphasis on rank
    max_results: int = 50  # Maximum results to return
    deduplication_threshold: float = 0.85  # Similarity threshold for dedup
    provider_weights: Dict[str, float] = field(default_factory=dict)
    quality_boost_factor: float = 0.2  # Boost for high-quality providers
    recency_boost_factor: float = 0.1  # Boost for recent results
    enable_content_deduplication: bool = True
    enable_url_normalization: bool = True
    min_content_length: int = 50  # Minimum content length to include


@dataclass
class FusionMetrics:
    """Metrics for RRF fusion process"""

    total_input_results: int = 0
    deduplicated_results: int = 0
    final_result_count: int = 0
    fusion_time_ms: float = 0
    provider_contributions: Dict[str, int] = field(default_factory=dict)
    quality_adjustments: int = 0
    recency_adjustments: int = 0


class OptimizedReciprocalRankFusion:
    """
    Production-ready Reciprocal Rank Fusion implementation

    Features:
    - Weighted RRF with provider-specific weights
    - Content-based deduplication
    - Quality and recency boosting
    - URL normalization
    - Comprehensive metrics
    - Performance optimization
    """

    def __init__(self, config: Optional[RRFConfig] = None):
        self.config = config or RRFConfig()
        self._metrics = FusionMetrics()

        # Precompiled patterns for URL normalization
        self._url_patterns = self._compile_url_patterns()

        # Content similarity cache for deduplication
        self._similarity_cache: Dict[str, float] = {}
        self._cache_max_size = 10000

    def fuse_results(
        self,
        provider_results: List[ProviderResults],
        query: str = "",
        boost_recent: bool = True,
        boost_quality: bool = True,
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Fuse search results from multiple providers using RRF

        Args:
            provider_results: Results from each provider
            query: Original search query for relevance boosting
            boost_recent: Whether to boost recent results
            boost_quality: Whether to boost high-quality provider results

        Returns:
            Tuple of (fused_results, fusion_metadata)
        """
        start_time = time.time()

        # Reset metrics
        self._metrics = FusionMetrics()

        # Validate inputs
        if not provider_results:
            return [], {"error": "No provider results provided"}

        # Collect all results with normalization
        all_results = self._collect_and_normalize_results(provider_results)
        self._metrics.total_input_results = len(all_results)

        if not all_results:
            return [], {"error": "No valid results after normalization"}

        # Deduplicate results
        deduplicated_results = self._deduplicate_results(all_results)
        self._metrics.deduplicated_results = len(all_results) - len(deduplicated_results)

        # Calculate RRF scores
        scored_results = self._calculate_rrf_scores(deduplicated_results, provider_results)

        # Apply quality and recency boosts
        if boost_quality:
            scored_results = self._apply_quality_boost(scored_results, provider_results)

        if boost_recent:
            scored_results = self._apply_recency_boost(scored_results)

        # Sort by final score and limit results
        final_results = sorted(scored_results, key=lambda x: x[1], reverse=True)
        final_results = final_results[: self.config.max_results]

        # Extract results and update ranks
        fused_results = []
        for i, (result, score) in enumerate(final_results):
            result.rank = i + 1
            result.metadata["rrf_score"] = score
            fused_results.append(result)

        self._metrics.final_result_count = len(fused_results)
        self._metrics.fusion_time_ms = (time.time() - start_time) * 1000

        # Generate fusion metadata
        fusion_metadata = self._generate_fusion_metadata(provider_results, fused_results)

        logger.debug(
            f"RRF fusion completed: {len(fused_results)} results in {self._metrics.fusion_time_ms:.1f}ms"
        )

        return fused_results, fusion_metadata

    def _collect_and_normalize_results(
        self, provider_results: List[ProviderResults]
    ) -> List[SearchResult]:
        """Collect and normalize results from all providers"""

        all_results = []

        for provider_result in provider_results:
            for result in provider_result.results:
                # Skip results that are too short
                if len(result.content) < self.config.min_content_length:
                    continue

                # Normalize URL if enabled
                if self.config.enable_url_normalization:
                    result.url = self._normalize_url(result.url)

                # Ensure result has required fields
                if not result.id:
                    result.id = hashlib.md5(result.url.encode()).hexdigest()

                # Add provider metadata
                result.metadata.update(
                    {
                        "original_rank": result.rank,
                        "original_score": result.score,
                        "provider_latency": provider_result.latency_ms,
                        "provider_quality": provider_result.quality_score,
                    }
                )

                all_results.append(result)

        return all_results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL and content similarity"""

        if not self.config.enable_content_deduplication:
            # Simple URL-based deduplication
            seen_urls = set()
            deduplicated = []

            for result in results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    deduplicated.append(result)

            return deduplicated

        # Content-based deduplication
        deduplicated = []
        seen_content_hashes = set()

        for result in results:
            # Create content hash for exact duplicates
            content_hash = hashlib.md5((result.title + result.content).lower().encode()).hexdigest()

            if content_hash in seen_content_hashes:
                continue

            # Check for similar content
            is_duplicate = False
            for existing_result in deduplicated:
                similarity = self._calculate_content_similarity(result, existing_result)

                if similarity > self.config.deduplication_threshold:
                    # Keep the result with higher original score
                    if result.score > existing_result.score:
                        # Replace existing result
                        deduplicated.remove(existing_result)
                        deduplicated.append(result)

                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_content_hashes.add(content_hash)
                deduplicated.append(result)

        return deduplicated

    def _calculate_rrf_scores(
        self, results: List[SearchResult], provider_results: List[ProviderResults]
    ) -> List[Tuple[SearchResult, float]]:
        """Calculate RRF scores for all results"""

        # Group results by provider for RRF calculation
        provider_rankings: Dict[str, List[SearchResult]] = defaultdict(list)

        for result in results:
            provider_rankings[result.provider].append(result)

        # Sort each provider's results by original rank
        for provider in provider_rankings:
            provider_rankings[provider].sort(key=lambda x: x.rank)

        # Calculate RRF scores
        rrf_scores: Dict[str, float] = defaultdict(float)

        for provider, provider_results_list in provider_rankings.items():
            # Get provider weight
            provider_weight = self.config.provider_weights.get(provider, 1.0)

            # Calculate RRF contribution for each result
            for rank, result in enumerate(provider_results_list, 1):
                rrf_contribution = provider_weight / (self.config.k_value + rank)
                rrf_scores[result.id] += rrf_contribution

                # Track provider contributions
                if provider not in self._metrics.provider_contributions:
                    self._metrics.provider_contributions[provider] = 0
                self._metrics.provider_contributions[provider] += 1

        # Create scored results list
        scored_results = []
        for result in results:
            score = rrf_scores[result.id]
            scored_results.append((result, score))

        return scored_results

    def _apply_quality_boost(
        self,
        scored_results: List[Tuple[SearchResult, float]],
        provider_results: List[ProviderResults],
    ) -> List[Tuple[SearchResult, float]]:
        """Apply quality boost based on provider quality scores"""

        # Create provider quality map
        provider_quality = {pr.provider: pr.quality_score for pr in provider_results}

        boosted_results = []

        for result, score in scored_results:
            quality_score = provider_quality.get(result.provider, 1.0)

            # Apply quality boost if above average
            if quality_score > 1.0:
                quality_boost = (quality_score - 1.0) * self.config.quality_boost_factor
                boosted_score = score * (1.0 + quality_boost)
                self._metrics.quality_adjustments += 1
            else:
                boosted_score = score

            result.metadata["quality_boost"] = quality_score
            boosted_results.append((result, boosted_score))

        return boosted_results

    def _apply_recency_boost(
        self, scored_results: List[Tuple[SearchResult, float]]
    ) -> List[Tuple[SearchResult, float]]:
        """Apply recency boost for recent content"""

        current_time = time.time()
        boosted_results = []

        for result, score in scored_results:
            # Extract publish date from metadata if available
            publish_date = result.metadata.get("publish_date")

            if publish_date:
                try:
                    # Calculate age in days
                    if isinstance(publish_date, (int, float)):
                        age_days = (current_time - publish_date) / 86400
                    else:
                        # Assume ISO format string
                        import datetime

                        dt = datetime.datetime.fromisoformat(publish_date.replace("Z", "+00:00"))
                        age_days = (current_time - dt.timestamp()) / 86400

                    # Apply recency boost (stronger for newer content)
                    if age_days < 7:  # Boost content less than a week old
                        recency_boost = self.config.recency_boost_factor * (1.0 - age_days / 7)
                        boosted_score = score * (1.0 + recency_boost)
                        self._metrics.recency_adjustments += 1
                    else:
                        boosted_score = score

                    result.metadata["age_days"] = age_days
                    result.metadata["recency_boost"] = age_days < 7

                except Exception as e:
                    logger.warning(f"Failed to parse publish date {publish_date}: {e}")
                    boosted_score = score
            else:
                boosted_score = score

            boosted_results.append((result, boosted_score))

        return boosted_results

    def _calculate_content_similarity(self, result1: SearchResult, result2: SearchResult) -> float:
        """Calculate content similarity between two results"""

        # Create cache key
        cache_key = f"{result1.id}:{result2.id}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        # Simple Jaccard similarity on word sets
        text1 = (result1.title + " " + result1.content).lower()
        text2 = (result2.title + " " + result2.content).lower()

        # Extract words (simple tokenization)
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        similarity = intersection / union if union > 0 else 0.0

        # Cache result (with size limit)
        if len(self._similarity_cache) < self._cache_max_size:
            self._similarity_cache[cache_key] = similarity

        return similarity

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for better deduplication"""

        # Remove common tracking parameters
        tracking_params = [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
            "source",
            "campaign",
        ]

        # Simple URL normalization
        normalized = url.lower()

        # Remove www prefix
        normalized = normalized.replace("://www.", "://")

        # Remove trailing slash
        if normalized.endswith("/"):
            normalized = normalized[:-1]

        # Remove fragment
        if "#" in normalized:
            normalized = normalized.split("#")[0]

        # Remove tracking parameters (simple approach)
        if "?" in normalized:
            base_url, params = normalized.split("?", 1)
            param_pairs = params.split("&")

            filtered_params = []
            for param in param_pairs:
                if "=" in param:
                    key = param.split("=")[0]
                    if key not in tracking_params:
                        filtered_params.append(param)

            if filtered_params:
                normalized = base_url + "?" + "&".join(filtered_params)
            else:
                normalized = base_url

        return normalized

    def _compile_url_patterns(self) -> Dict[str, Any]:
        """Compile regex patterns for URL processing"""
        import re

        return {
            "tracking_params": re.compile(
                r"[?&](utm_[^&]*|fbclid|gclid|ref|source|campaign)=[^&]*", re.IGNORECASE
            ),
            "www_prefix": re.compile(r"://www\.", re.IGNORECASE),
            "trailing_slash": re.compile(r"/$"),
            "fragment": re.compile(r"#.*$"),
        }

    def _generate_fusion_metadata(
        self, provider_results: List[ProviderResults], fused_results: List[SearchResult]
    ) -> Dict[str, Any]:
        """Generate comprehensive fusion metadata"""

        # Provider statistics
        provider_stats = {}
        for pr in provider_results:
            provider_stats[pr.provider] = {
                "input_results": len(pr.results),
                "latency_ms": pr.latency_ms,
                "cost_cents": pr.cost_cents,
                "quality_score": pr.quality_score,
                "contribution_count": self._metrics.provider_contributions.get(pr.provider, 0),
            }

        # Result distribution analysis
        provider_distribution = defaultdict(int)
        for result in fused_results:
            provider_distribution[result.provider] += 1

        # Quality metrics
        avg_rrf_score = np.mean([r.metadata.get("rrf_score", 0) for r in fused_results])
        score_std = np.std([r.metadata.get("rrf_score", 0) for r in fused_results])

        return {
            "fusion_config": {
                "k_value": self.config.k_value,
                "max_results": self.config.max_results,
                "deduplication_threshold": self.config.deduplication_threshold,
                "provider_weights": dict(self.config.provider_weights),
            },
            "fusion_metrics": {
                "total_input_results": self._metrics.total_input_results,
                "deduplicated_results": self._metrics.deduplicated_results,
                "final_result_count": self._metrics.final_result_count,
                "fusion_time_ms": self._metrics.fusion_time_ms,
                "quality_adjustments": self._metrics.quality_adjustments,
                "recency_adjustments": self._metrics.recency_adjustments,
            },
            "provider_stats": provider_stats,
            "result_distribution": dict(provider_distribution),
            "quality_metrics": {
                "avg_rrf_score": avg_rrf_score,
                "score_std": score_std,
                "score_range": [
                    (
                        min(r.metadata.get("rrf_score", 0) for r in fused_results)
                        if fused_results
                        else 0
                    ),
                    (
                        max(r.metadata.get("rrf_score", 0) for r in fused_results)
                        if fused_results
                        else 0
                    ),
                ],
            },
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive RRF metrics"""

        return {
            "total_input_results": self._metrics.total_input_results,
            "deduplicated_results": self._metrics.deduplicated_results,
            "deduplication_rate": (
                self._metrics.deduplicated_results / max(1, self._metrics.total_input_results)
            ),
            "final_result_count": self._metrics.final_result_count,
            "fusion_time_ms": self._metrics.fusion_time_ms,
            "provider_contributions": dict(self._metrics.provider_contributions),
            "quality_adjustments": self._metrics.quality_adjustments,
            "recency_adjustments": self._metrics.recency_adjustments,
            "similarity_cache_size": len(self._similarity_cache),
            "config": {
                "k_value": self.config.k_value,
                "max_results": self.config.max_results,
                "deduplication_threshold": self.config.deduplication_threshold,
                "enable_content_deduplication": self.config.enable_content_deduplication,
            },
        }

    def update_provider_weights(self, weights: Dict[str, float]):
        """Update provider weights for future fusions"""
        self.config.provider_weights.update(weights)
        logger.info(f"Updated provider weights: {weights}")

    def clear_similarity_cache(self):
        """Clear the content similarity cache"""
        self._similarity_cache.clear()
        logger.debug("Cleared similarity cache")


# Factory function for easy integration
def create_rrf_fusion(
    k_value: float = 60.0,
    max_results: int = 50,
    provider_weights: Optional[Dict[str, float]] = None,
    enable_content_deduplication: bool = True,
) -> OptimizedReciprocalRankFusion:
    """Factory function to create configured RRF fusion"""

    config = RRFConfig(
        k_value=k_value,
        max_results=max_results,
        provider_weights=provider_weights or {},
        enable_content_deduplication=enable_content_deduplication,
    )

    return OptimizedReciprocalRankFusion(config)
