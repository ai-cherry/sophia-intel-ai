"""
Cross-Encoder Reranking for Search Quality Enhancement
Uses sentence-transformers cross-encoder models for semantic reranking
"""
import asyncio
import hashlib
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import redis.asyncio as redis
import torch
from sentence_transformers import CrossEncoder
logger = logging.getLogger(__name__)
@dataclass
class RerankingResult:
    """Result with reranking score"""
    id: str
    title: str
    content: str
    url: str
    original_score: float
    rerank_score: float
    final_rank: int
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
@dataclass
class RerankingConfig:
    """Configuration for cross-encoder reranking"""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    max_length: int = 512  # Maximum sequence length
    batch_size: int = 32  # Batch size for inference
    device: str = "auto"  # Device for inference (auto, cpu, cuda)
    cache_ttl: int = 3600  # Cache TTL in seconds
    enable_caching: bool = True
    rerank_top_k: int = 100  # Only rerank top K results
    score_combination_weight: float = 0.7  # Weight for rerank score vs original
    min_content_length: int = 20  # Minimum content length for reranking
    enable_async_inference: bool = True
    max_concurrent_batches: int = 4
@dataclass
class RerankingMetrics:
    """Metrics for reranking process"""
    total_results: int = 0
    reranked_results: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    inference_time_ms: float = 0
    total_time_ms: float = 0
    batch_count: int = 0
    avg_score_change: float = 0
    top_10_changes: int = 0  # How many top-10 positions changed
class OptimizedCrossEncoderReranker:
    """
    Production-ready cross-encoder reranking system
    Features:
    - Async inference with batching
    - Redis caching for performance
    - Multiple model support
    - Comprehensive metrics
    - Memory-efficient processing
    - Score combination strategies
    """
    def __init__(
        self, redis_client: redis.Redis, config: Optional[RerankingConfig] = None
    ):
        self.redis = redis_client
        self.config = config or RerankingConfig()
        # Model and device setup
        self.model: Optional[CrossEncoder] = None
        self.device = self._determine_device()
        self._model_lock = threading.Lock()
        # Thread pool for async inference
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_batches,
            thread_name_prefix="reranker",
        )
        # Metrics tracking
        self._metrics = RerankingMetrics()
        # Initialize model
        asyncio.create_task(self._initialize_model())
    async def rerank_results(
        self, query: str, results: List[Dict[str, Any]], preserve_top_k: int = 10
    ) -> Tuple[List[RerankingResult], Dict[str, Any]]:
        """
        Rerank search results using cross-encoder
        Args:
            query: Search query
            results: List of search results to rerank
            preserve_top_k: Number of top results to preserve order
        Returns:
            Tuple of (reranked_results, reranking_metadata)
        """
        start_time = time.time()
        # Reset metrics
        self._metrics = RerankingMetrics()
        self._metrics.total_results = len(results)
        if not results:
            return [], {"error": "No results to rerank"}
        if not self.model:
            await self._initialize_model()
            if not self.model:
                return self._fallback_ranking(results), {"error": "Model not available"}
        # Prepare results for reranking
        prepared_results = self._prepare_results(results)
        # Filter results for reranking
        rerank_candidates = self._filter_rerank_candidates(prepared_results)
        self._metrics.reranked_results = len(rerank_candidates)
        if not rerank_candidates:
            return self._fallback_ranking(prepared_results), {
                "warning": "No candidates for reranking"
            }
        # Perform reranking
        reranked_candidates = await self._perform_reranking(query, rerank_candidates)
        # Combine with non-reranked results
        final_results = self._combine_results(
            reranked_candidates,
            [r for r in prepared_results if r not in rerank_candidates],
            preserve_top_k,
        )
        self._metrics.total_time_ms = (time.time() - start_time) * 1000
        # Generate metadata
        metadata = self._generate_reranking_metadata(query, results, final_results)
        logger.debug(
            f"Reranking completed: {len(final_results)} results in {self._metrics.total_time_ms:.1f}ms"
        )
        return final_results, metadata
    async def _perform_reranking(
        self, query: str, candidates: List[RerankingResult]
    ) -> List[RerankingResult]:
        """Perform the actual reranking with caching and batching"""
        inference_start = time.time()
        # Check cache for existing scores
        cached_results, uncached_results = await self._check_cache(query, candidates)
        # Perform inference for uncached results
        if uncached_results:
            inference_results = await self._run_inference(query, uncached_results)
            # Cache new results
            await self._cache_results(query, inference_results)
            # Combine cached and inference results
            all_results = cached_results + inference_results
        else:
            all_results = cached_results
        self._metrics.inference_time_ms = (time.time() - inference_start) * 1000
        # Sort by rerank score
        all_results.sort(key=lambda x: x.rerank_score, reverse=True)
        # Update final ranks
        for i, result in enumerate(all_results):
            result.final_rank = i + 1
        return all_results
    async def _run_inference(
        self, query: str, results: List[RerankingResult]
    ) -> List[RerankingResult]:
        """Run cross-encoder inference on results"""
        if not results:
            return []
        # Prepare query-document pairs
        pairs = []
        for result in results:
            # Combine title and content for better context
            document = f"{result.title} {result.content}"
            # Truncate if too long
            if len(document) > self.config.max_length * 4:  # Rough character estimate
                document = document[: self.config.max_length * 4]
            pairs.append([query, document])
        # Run inference in batches
        all_scores = []
        batch_size = self.config.batch_size
        for i in range(0, len(pairs), batch_size):
            batch_pairs = pairs[i : i + batch_size]
            # Run inference in thread pool
            if self.config.enable_async_inference:
                batch_scores = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._inference_batch, batch_pairs
                )
            else:
                batch_scores = self._inference_batch(batch_pairs)
            all_scores.extend(batch_scores)
            self._metrics.batch_count += 1
        # Update results with rerank scores
        for result, score in zip(results, all_scores):
            result.rerank_score = float(score)
            # Combine with original score
            combined_score = (
                self.config.score_combination_weight * result.rerank_score
                + (1 - self.config.score_combination_weight) * result.original_score
            )
            result.metadata["combined_score"] = combined_score
            result.metadata["rerank_score_raw"] = result.rerank_score
        return results
    def _inference_batch(self, pairs: List[List[str]]) -> List[float]:
        """Run inference on a batch of query-document pairs"""
        with self._model_lock:
            try:
                scores = self.model.predict(pairs)
                return scores.tolist() if hasattr(scores, "tolist") else list(scores)
            except Exception as e:
                logger.error(f"Inference batch failed: {e}")
                # Return neutral scores as fallback
                return [0.5] * len(pairs)
    async def _check_cache(
        self, query: str, candidates: List[RerankingResult]
    ) -> Tuple[List[RerankingResult], List[RerankingResult]]:
        """Check cache for existing rerank scores"""
        if not self.config.enable_caching:
            return [], candidates
        cached_results = []
        uncached_results = []
        for candidate in candidates:
            cache_key = self._generate_cache_key(query, candidate)
            try:
                cached_score = await self.redis.get(cache_key)
                if cached_score is not None:
                    candidate.rerank_score = float(cached_score)
                    candidate.metadata["cache_hit"] = True
                    cached_results.append(candidate)
                    self._metrics.cache_hits += 1
                else:
                    uncached_results.append(candidate)
                    self._metrics.cache_misses += 1
            except Exception as e:
                logger.warning(f"Cache check failed for {cache_key}: {e}")
                uncached_results.append(candidate)
                self._metrics.cache_misses += 1
        return cached_results, uncached_results
    async def _cache_results(self, query: str, results: List[RerankingResult]):
        """Cache rerank scores for future use"""
        if not self.config.enable_caching:
            return
        try:
            # Batch cache operations
            pipe = self.redis.pipeline()
            for result in results:
                cache_key = self._generate_cache_key(query, result)
                pipe.set(cache_key, str(result.rerank_score), ex=self.config.cache_ttl)
            await pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to cache rerank results: {e}")
    def _generate_cache_key(self, query: str, result: RerankingResult) -> str:
        """Generate cache key for query-document pair"""
        # Create deterministic key from query and document content
        content_hash = hashlib.md5(
            f"{result.title} {result.content}".encode()
        ).hexdigest()
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"rerank:{self.config.model_name}:{query_hash}:{content_hash}"
    def _prepare_results(self, results: List[Dict[str, Any]]) -> List[RerankingResult]:
        """Convert input results to RerankingResult objects"""
        prepared = []
        for i, result in enumerate(results):
            # Extract required fields with defaults
            rerank_result = RerankingResult(
                id=result.get("id", f"result_{i}"),
                title=result.get("title", ""),
                content=result.get("content", result.get("snippet", "")),
                url=result.get("url", ""),
                original_score=result.get("score", 0.0),
                rerank_score=0.0,  # Will be set during reranking
                final_rank=i + 1,
                provider=result.get("provider", "unknown"),
                metadata=result.get("metadata", {}),
            )
            # Copy additional metadata
            rerank_result.metadata.update(
                {"original_rank": i + 1, "original_score": rerank_result.original_score}
            )
            prepared.append(rerank_result)
        return prepared
    def _filter_rerank_candidates(
        self, results: List[RerankingResult]
    ) -> List[RerankingResult]:
        """Filter results that should be reranked"""
        candidates = []
        for result in results[: self.config.rerank_top_k]:
            # Skip results with insufficient content
            if len(result.content) < self.config.min_content_length:
                continue
            # Skip results without meaningful text
            if not result.title.strip() and not result.content.strip():
                continue
            candidates.append(result)
        return candidates
    def _combine_results(
        self,
        reranked: List[RerankingResult],
        non_reranked: List[RerankingResult],
        preserve_top_k: int,
    ) -> List[RerankingResult]:
        """Combine reranked and non-reranked results"""
        # Sort reranked results by combined score
        reranked.sort(
            key=lambda x: x.metadata.get("combined_score", x.rerank_score), reverse=True
        )
        # Preserve top K from original ranking if requested
        if preserve_top_k > 0:
            preserved = reranked[:preserve_top_k]
            remaining_reranked = reranked[preserve_top_k:]
        else:
            preserved = []
            remaining_reranked = reranked
        # Combine all results
        final_results = preserved + remaining_reranked + non_reranked
        # Update final ranks
        for i, result in enumerate(final_results):
            result.final_rank = i + 1
            result.metadata["reranked"] = result in reranked
        return final_results
    def _fallback_ranking(
        self, results: List[RerankingResult]
    ) -> List[RerankingResult]:
        """Fallback ranking when reranking is not available"""
        # Sort by original score
        results.sort(key=lambda x: x.original_score, reverse=True)
        # Update ranks
        for i, result in enumerate(results):
            result.final_rank = i + 1
            result.rerank_score = result.original_score
            result.metadata["fallback_ranking"] = True
        return results
    def _determine_device(self) -> str:
        """Determine the best device for inference"""
        if self.config.device != "auto":
            return self.config.device
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    async def _initialize_model(self):
        """Initialize the cross-encoder model"""
        try:
            logger.info(f"Loading cross-encoder model: {self.config.model_name}")
            # Load model in thread pool to avoid blocking
            self.model = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_model
            )
            logger.info(f"Model loaded successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model {self.config.model_name}: {e}")
            self.model = None
    def _load_model(self) -> CrossEncoder:
        """Load the cross-encoder model (runs in thread pool)"""
        model = CrossEncoder(
            self.config.model_name,
            max_length=self.config.max_length,
            device=self.device,
        )
        # Set to evaluation mode
        model.model.eval()
        return model
    def _generate_reranking_metadata(
        self,
        query: str,
        original_results: List[Dict[str, Any]],
        final_results: List[RerankingResult],
    ) -> Dict[str, Any]:
        """Generate comprehensive reranking metadata"""
        # Calculate ranking changes
        original_top_10 = [
            r.get("id", f"result_{i}") for i, r in enumerate(original_results[:10])
        ]
        final_top_10 = [r.id for r in final_results[:10]]
        top_10_changes = len(set(original_top_10) ^ set(final_top_10))
        self._metrics.top_10_changes = top_10_changes
        # Calculate average score change
        score_changes = []
        for result in final_results:
            if "rerank_score_raw" in result.metadata:
                score_change = (
                    result.metadata["rerank_score_raw"] - result.original_score
                )
                score_changes.append(score_change)
        self._metrics.avg_score_change = np.mean(score_changes) if score_changes else 0
        return {
            "reranking_config": {
                "model_name": self.config.model_name,
                "max_length": self.config.max_length,
                "batch_size": self.config.batch_size,
                "device": self.device,
                "rerank_top_k": self.config.rerank_top_k,
                "score_combination_weight": self.config.score_combination_weight,
            },
            "reranking_metrics": {
                "total_results": self._metrics.total_results,
                "reranked_results": self._metrics.reranked_results,
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "cache_hit_rate": (
                    self._metrics.cache_hits
                    / max(1, self._metrics.cache_hits + self._metrics.cache_misses)
                ),
                "inference_time_ms": self._metrics.inference_time_ms,
                "total_time_ms": self._metrics.total_time_ms,
                "batch_count": self._metrics.batch_count,
                "avg_score_change": self._metrics.avg_score_change,
                "top_10_changes": self._metrics.top_10_changes,
            },
            "performance_metrics": {
                "results_per_second": (
                    self._metrics.reranked_results
                    / max(0.001, self._metrics.total_time_ms / 1000)
                ),
                "inference_efficiency": (
                    (
                        self._metrics.reranked_results
                        / max(0.001, self._metrics.inference_time_ms / 1000)
                    )
                    if self._metrics.inference_time_ms > 0
                    else 0
                ),
            },
        }
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive reranking metrics"""
        return {
            "model_info": {
                "model_name": self.config.model_name,
                "device": self.device,
                "model_loaded": self.model is not None,
            },
            "processing_metrics": {
                "total_results": self._metrics.total_results,
                "reranked_results": self._metrics.reranked_results,
                "rerank_rate": (
                    self._metrics.reranked_results / max(1, self._metrics.total_results)
                ),
                "total_time_ms": self._metrics.total_time_ms,
                "inference_time_ms": self._metrics.inference_time_ms,
                "batch_count": self._metrics.batch_count,
            },
            "cache_metrics": {
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "cache_hit_rate": (
                    self._metrics.cache_hits
                    / max(1, self._metrics.cache_hits + self._metrics.cache_misses)
                ),
                "cache_enabled": self.config.enable_caching,
            },
            "quality_metrics": {
                "avg_score_change": self._metrics.avg_score_change,
                "top_10_changes": self._metrics.top_10_changes,
            },
        }
    async def warm_up_model(
        self, sample_queries: List[str], sample_documents: List[str]
    ):
        """Warm up the model with sample queries"""
        if not self.model or not sample_queries or not sample_documents:
            return
        logger.info("Warming up reranking model...")
        try:
            # Create sample pairs
            pairs = []
            for query in sample_queries[:5]:  # Limit to 5 queries
                for doc in sample_documents[:10]:  # Limit to 10 docs per query
                    pairs.append([query, doc])
            # Run warm-up inference
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._inference_batch, pairs[:20]  # Limit total pairs
            )
            logger.info("Model warm-up completed")
        except Exception as e:
            logger.warning(f"Model warm-up failed: {e}")
    async def close(self):
        """Clean shutdown of reranker"""
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        # Clear model from memory
        if self.model:
            del self.model
            self.model = None
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Cross-encoder reranker closed")
# Factory function for easy integration
def create_cross_encoder_reranker(
    redis_client: redis.Redis,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    batch_size: int = 32,
    enable_caching: bool = True,
    rerank_top_k: int = 100,
) -> OptimizedCrossEncoderReranker:
    """Factory function to create configured cross-encoder reranker"""
    config = RerankingConfig(
        model_name=model_name,
        batch_size=batch_size,
        enable_caching=enable_caching,
        rerank_top_k=rerank_top_k,
    )
    return OptimizedCrossEncoderReranker(redis_client, config)
