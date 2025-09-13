"""
Contextual Bandit for Search Provider Selection
Uses MABWiser with Thompson Sampling for intelligent provider routing
"""
import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import redis.asyncio as redis
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
logger = logging.getLogger(__name__)
@dataclass
class ProviderContext:
    """Enhanced context for provider selection"""
    query_length: int
    query_type: str  # 'semantic', 'factual', 'news', 'code'
    time_of_day: float  # 0-23.99
    recent_latency_p95: float  # Recent P95 latency in ms
    recent_error_rate: float  # Recent error rate 0-1
    cost_per_request: float  # Cost in cents
    provider_load: float  # Current utilization 0-1
    query_embedding_cluster: int  # Query similarity cluster 0-9
    user_context: str = "general"  # User context type
    urgency_level: float = 0.5  # 0-1, higher = more urgent
    def to_feature_vector(self) -> np.ndarray:
        """Convert context to feature vector for ML models"""
        # Normalize categorical features
        query_type_map = {"semantic": 0, "factual": 1, "news": 2, "code": 3}
        user_context_map = {"general": 0, "technical": 1, "business": 2, "research": 3}
        return np.array(
            [
                self.query_length / 1000,  # Normalize to 0-1 range
                query_type_map.get(self.query_type, 0),
                self.time_of_day / 24,
                min(self.recent_latency_p95 / 5000, 1),  # Cap at 5s
                self.recent_error_rate,
                min(self.cost_per_request / 10, 1),  # Cap at 10 cents
                self.provider_load,
                self.query_embedding_cluster / 10,
                user_context_map.get(self.user_context, 0),
                self.urgency_level,
            ]
        )
@dataclass
class ProviderMetrics:
    """Metrics tracking for each provider"""
    total_requests: int = 0
    successful_requests: int = 0
    total_latency_ms: float = 0
    total_cost_cents: float = 0
    error_count: int = 0
    last_used: float = 0
    ewma_latency: float = 0
    ewma_success_rate: float = 1.0
    ewma_cost: float = 0
    def get_success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    def get_avg_latency(self) -> float:
        if self.successful_requests == 0:
            return 0
        return self.total_latency_ms / self.successful_requests
    def get_avg_cost(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.total_cost_cents / self.total_requests
@dataclass
class BanditConfig:
    """Configuration for contextual bandit"""
    exploration_decay_rate: float = 0.01
    min_exploration_rate: float = 0.05
    max_exploration_rate: float = 0.3
    context_similarity_threshold: float = 0.8
    reward_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "latency": -0.4,  # Lower latency is better
            "success": 0.5,  # Higher success rate is better
            "cost": -0.1,  # Lower cost is better
        }
    )
    ewma_alpha: float = 0.2
    enable_clustering: bool = True
    cluster_count: int = 10
class ProductionContextualBandit:
    """
    Production-ready contextual bandit with Thompson Sampling
    Features:
    - MABWiser integration with Thompson Sampling
    - Context clustering for similar query handling
    - EWMA metrics tracking
    - Redis persistence for state
    - Comprehensive reward engineering
    """
    def __init__(
        self,
        providers: List[str],
        redis_client: redis.Redis,
        config: Optional[BanditConfig] = None,
    ):
        self.providers = providers
        self.redis = redis_client
        self.config = config or BanditConfig()
        # Initialize MABWiser with Thompson Sampling
        self.bandit = MAB(
            arms=providers,
            learning_policy=LearningPolicy.ThompsonSampling(
                alpha=1.0, beta=1.0  # Prior success count  # Prior failure count
            ),
            neighborhood_policy=NeighborhoodPolicy.KNearest(k=5),
            seed=42,
        )
        # Metrics tracking
        self.provider_metrics: Dict[str, ProviderMetrics] = {
            p: ProviderMetrics() for p in providers
        }
        # Context clustering for similar queries
        self.context_scaler = StandardScaler()
        self.context_clusterer = KMeans(
            n_clusters=self.config.cluster_count, random_state=42
        )
        self._context_history: List[np.ndarray] = []
        self._clustering_fitted = False
        # Decision tracking
        self.decision_history: List[Dict[str, Any]] = []
        self.total_decisions = 0
        # Background tasks
        self._background_tasks: set = set()
        self._start_background_tasks()
    async def select_provider(
        self, context: ProviderContext, force_exploration: bool = False
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Select optimal provider using contextual bandit
        Args:
            context: Current request context
            force_exploration: Force exploration regardless of policy
        Returns:
            Tuple of (selected_provider, confidence_score, decision_metadata)
        """
        self.total_decisions += 1
        # Convert context to feature vector
        feature_vector = context.to_feature_vector()
        # Update context clustering
        await self._update_context_clustering(feature_vector)
        # Get cluster assignment for this context
        context.query_embedding_cluster = self._get_context_cluster(feature_vector)
        # Calculate exploration rate
        exploration_rate = self._calculate_exploration_rate()
        # Decide between exploration and exploitation
        should_explore = (
            force_exploration
            or np.random.random() < exploration_rate
            or self.total_decisions
            < len(self.providers) * 2  # Ensure all providers tried
        )
        if should_explore:
            # Exploration: Use bandit's exploration strategy
            selected_provider = self._explore_provider(context)
            confidence_score = 0.5  # Medium confidence during exploration
            decision_type = "exploration"
        else:
            # Exploitation: Use bandit's learned policy
            selected_provider = self._exploit_provider(context)
            confidence_score = self._calculate_confidence(selected_provider, context)
            decision_type = "exploitation"
        # Update provider metrics
        self.provider_metrics[selected_provider].last_used = time.time()
        # Create decision metadata
        decision_metadata = {
            "decision_type": decision_type,
            "exploration_rate": exploration_rate,
            "confidence_score": confidence_score,
            "context_cluster": context.query_embedding_cluster,
            "total_decisions": self.total_decisions,
            "provider_metrics": {
                p: {
                    "success_rate": m.get_success_rate(),
                    "avg_latency": m.get_avg_latency(),
                    "avg_cost": m.get_avg_cost(),
                }
                for p, m in self.provider_metrics.items()
            },
        }
        # Store decision for learning
        decision_record = {
            "timestamp": time.time(),
            "provider": selected_provider,
            "context": asdict(context),
            "decision_type": decision_type,
            "confidence": confidence_score,
        }
        self.decision_history.append(decision_record)
        # Persist state to Redis
        await self._persist_state()
        logger.debug(
            f"Selected provider {selected_provider} with confidence {confidence_score:.3f}"
        )
        return selected_provider, confidence_score, decision_metadata
    async def update_reward(
        self,
        provider: str,
        context: ProviderContext,
        latency_ms: float,
        success: bool,
        cost_cents: float = 0,
        quality_score: Optional[float] = None,
    ):
        """
        Update bandit with reward signal from request outcome
        Args:
            provider: Provider that was used
            context: Context that was used for selection
            latency_ms: Request latency in milliseconds
            success: Whether request was successful
            cost_cents: Cost of request in cents
            quality_score: Optional quality score 0-1
        """
        # Update provider metrics
        metrics = self.provider_metrics[provider]
        metrics.total_requests += 1
        metrics.total_cost_cents += cost_cents
        if success:
            metrics.successful_requests += 1
            metrics.total_latency_ms += latency_ms
        else:
            metrics.error_count += 1
        # Update EWMA metrics
        alpha = self.config.ewma_alpha
        if success:
            metrics.ewma_latency = (
                alpha * latency_ms + (1 - alpha) * metrics.ewma_latency
                if metrics.ewma_latency > 0
                else latency_ms
            )
        success_value = 1.0 if success else 0.0
        metrics.ewma_success_rate = (
            alpha * success_value + (1 - alpha) * metrics.ewma_success_rate
        )
        metrics.ewma_cost = (
            alpha * cost_cents + (1 - alpha) * metrics.ewma_cost
            if metrics.ewma_cost > 0
            else cost_cents
        )
        # Calculate composite reward
        reward = self._calculate_reward(latency_ms, success, cost_cents, quality_score)
        # Update bandit with context and reward
        feature_vector = context.to_feature_vector()
        try:
            # MABWiser expects context as list of features
            self.bandit.partial_fit(
                decisions=[provider],
                rewards=[reward],
                contexts=[feature_vector.tolist()],
            )
        except Exception as e:
            logger.warning(f"Failed to update bandit: {e}")
        # Update decision history with outcome
        if self.decision_history:
            last_decision = self.decision_history[-1]
            if last_decision.get("provider") == provider:
                last_decision.update(
                    {
                        "outcome": {
                            "latency_ms": latency_ms,
                            "success": success,
                            "cost_cents": cost_cents,
                            "quality_score": quality_score,
                            "reward": reward,
                        }
                    }
                )
        # Persist updated state
        await self._persist_state()
        logger.debug(
            f"Updated reward for {provider}: {reward:.3f} (latency={latency_ms:.1f}ms, success={success})"
        )
    def _explore_provider(self, context: ProviderContext) -> str:
        """Select provider for exploration"""
        # Use weighted random selection based on recent performance
        weights = []
        for provider in self.providers:
            metrics = self.provider_metrics[provider]
            # Base weight on inverse of recent usage and error rate
            recency_weight = max(
                0.1, 1.0 - (time.time() - metrics.last_used) / 3600
            )  # Decay over 1 hour
            error_weight = max(0.1, 1.0 - metrics.ewma_success_rate)
            weight = recency_weight * error_weight
            weights.append(weight)
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(self.providers)] * len(self.providers)
        # Select provider based on weights
        selected_idx = np.random.choice(len(self.providers), p=weights)
        return self.providers[selected_idx]
    def _exploit_provider(self, context: ProviderContext) -> str:
        """Select provider for exploitation using bandit policy"""
        feature_vector = context.to_feature_vector()
        try:
            # Use bandit to predict best provider
            prediction = self.bandit.predict([feature_vector.tolist()])
            return prediction[0]
        except Exception as e:
            logger.warning(
                f"Bandit prediction failed: {e}, falling back to best provider"
            )
            # Fallback: Select provider with best recent performance
            best_provider = self.providers[0]
            best_score = -float("inf")
            for provider in self.providers:
                metrics = self.provider_metrics[provider]
                # Composite score based on success rate, latency, and cost
                score = (
                    metrics.ewma_success_rate * 0.5
                    + (1.0 - min(metrics.ewma_latency / 5000, 1.0)) * 0.3
                    + (1.0 - min(metrics.ewma_cost / 10, 1.0)) * 0.2
                )
                if score > best_score:
                    best_score = score
                    best_provider = provider
            return best_provider
    def _calculate_exploration_rate(self) -> float:
        """Calculate dynamic exploration rate with decay"""
        # Exponential decay based on total decisions
        decayed_rate = self.config.max_exploration_rate * np.exp(
            -self.config.exploration_decay_rate * self.total_decisions
        )
        # Ensure within bounds
        return max(self.config.min_exploration_rate, decayed_rate)
    def _calculate_confidence(self, provider: str, context: ProviderContext) -> float:
        """Calculate confidence score for provider selection"""
        metrics = self.provider_metrics[provider]
        # Base confidence on number of samples and recent performance
        sample_confidence = min(
            1.0, metrics.total_requests / 100
        )  # Max confidence at 100 samples
        performance_confidence = metrics.ewma_success_rate
        # Adjust for context similarity
        context_confidence = self._get_context_similarity_confidence(context)
        # Composite confidence
        confidence = (
            sample_confidence * 0.4
            + performance_confidence * 0.4
            + context_confidence * 0.2
        )
        return confidence
    def _calculate_reward(
        self,
        latency_ms: float,
        success: bool,
        cost_cents: float,
        quality_score: Optional[float] = None,
    ) -> float:
        """Calculate composite reward signal"""
        if not success:
            return -1.0  # Heavy penalty for failures
        # Normalize metrics to 0-1 range
        latency_score = max(0, 1.0 - latency_ms / 5000)  # Normalize to 5s max
        cost_score = max(0, 1.0 - cost_cents / 10)  # Normalize to 10 cents max
        quality_score = quality_score or 0.8  # Default quality if not provided
        # Weighted composite reward
        reward = (
            self.config.reward_weights["latency"] * (1.0 - latency_score)
            + self.config.reward_weights["success"] * 1.0
            + self.config.reward_weights["cost"] * (1.0 - cost_score)
            + 0.2 * quality_score  # Quality bonus
        )
        return reward
    async def _update_context_clustering(self, feature_vector: np.ndarray):
        """Update context clustering with new feature vector"""
        if not self.config.enable_clustering:
            return
        self._context_history.append(feature_vector)
        # Retrain clustering periodically
        if (
            len(self._context_history) % 100 == 0
            and len(self._context_history) >= self.config.cluster_count
        ):
            try:
                # Fit scaler and clusterer
                context_matrix = np.array(
                    self._context_history[-1000:]
                )  # Use last 1000 samples
                scaled_contexts = self.context_scaler.fit_transform(context_matrix)
                self.context_clusterer.fit(scaled_contexts)
                self._clustering_fitted = True
                logger.debug("Updated context clustering with new data")
            except Exception as e:
                logger.warning(f"Context clustering update failed: {e}")
    def _get_context_cluster(self, feature_vector: np.ndarray) -> int:
        """Get cluster assignment for feature vector"""
        if not self.config.enable_clustering or not self._clustering_fitted:
            return 0
        try:
            scaled_vector = self.context_scaler.transform([feature_vector])
            cluster = self.context_clusterer.predict(scaled_vector)[0]
            return int(cluster)
        except Exception as e:
            logger.warning(f"Context clustering prediction failed: {e}")
            return 0
    def _get_context_similarity_confidence(self, context: ProviderContext) -> float:
        """Calculate confidence based on context similarity to historical data"""
        if len(self._context_history) < 10:
            return 0.5  # Medium confidence with limited data
        feature_vector = context.to_feature_vector()
        # Calculate similarity to recent contexts
        recent_contexts = np.array(self._context_history[-100:])  # Last 100 contexts
        try:
            # Use cosine similarity
            similarities = []
            for hist_context in recent_contexts:
                similarity = np.dot(feature_vector, hist_context) / (
                    np.linalg.norm(feature_vector) * np.linalg.norm(hist_context)
                )
                similarities.append(similarity)
            # Return average similarity as confidence
            return np.mean(similarities)
        except Exception as e:
            logger.warning(f"Context similarity calculation failed: {e}")
            return 0.5
    async def _persist_state(self):
        """Persist bandit state to Redis"""
        try:
            # Persist provider metrics
            metrics_data = {
                provider: asdict(metrics)
                for provider, metrics in self.provider_metrics.items()
            }
            await self.redis.set(
                "bandit:provider_metrics",
                json.dumps(metrics_data),
                ex=86400,  # 24 hour expiry
            )
            # Persist decision history (last 1000 decisions)
            recent_decisions = self.decision_history[-1000:]
            await self.redis.set(
                "bandit:decision_history", json.dumps(recent_decisions), ex=86400
            )
            # Persist bandit configuration
            await self.redis.set(
                "bandit:config", json.dumps(asdict(self.config)), ex=86400
            )
        except Exception as e:
            logger.warning(f"Failed to persist bandit state: {e}")
    async def _load_state(self):
        """Load bandit state from Redis"""
        try:
            # Load provider metrics
            metrics_data = await self.redis.get("bandit:provider_metrics")
            if metrics_data:
                metrics_dict = json.loads(metrics_data)
                for provider, metrics in metrics_dict.items():
                    if provider in self.provider_metrics:
                        self.provider_metrics[provider] = ProviderMetrics(**metrics)
            # Load decision history
            history_data = await self.redis.get("bandit:decision_history")
            if history_data:
                self.decision_history = json.loads(history_data)
            logger.info("Loaded bandit state from Redis")
        except Exception as e:
            logger.warning(f"Failed to load bandit state: {e}")
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        async def periodic_cleanup():
            """Periodic cleanup of old data"""
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    # Trim decision history
                    if len(self.decision_history) > 10000:
                        self.decision_history = self.decision_history[-5000:]
                    # Trim context history
                    if len(self._context_history) > 10000:
                        self._context_history = self._context_history[-5000:]
                    logger.debug("Completed periodic bandit cleanup")
                except Exception as e:
                    logger.error(f"Error in periodic cleanup: {e}")
        task = asyncio.create_task(periodic_cleanup())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive bandit metrics"""
        # Calculate aggregate statistics
        total_requests = sum(m.total_requests for m in self.provider_metrics.values())
        total_successes = sum(
            m.successful_requests for m in self.provider_metrics.values()
        )
        total_errors = sum(m.error_count for m in self.provider_metrics.values())
        provider_stats = {}
        for provider, metrics in self.provider_metrics.items():
            provider_stats[provider] = {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.get_success_rate(),
                "avg_latency_ms": metrics.get_avg_latency(),
                "avg_cost_cents": metrics.get_avg_cost(),
                "ewma_success_rate": metrics.ewma_success_rate,
                "ewma_latency": metrics.ewma_latency,
                "ewma_cost": metrics.ewma_cost,
                "last_used": metrics.last_used,
            }
        return {
            "total_decisions": self.total_decisions,
            "total_requests": total_requests,
            "overall_success_rate": total_successes / max(1, total_requests),
            "total_errors": total_errors,
            "exploration_rate": self._calculate_exploration_rate(),
            "provider_count": len(self.providers),
            "clustering_fitted": self._clustering_fitted,
            "context_history_size": len(self._context_history),
            "decision_history_size": len(self.decision_history),
            "provider_stats": provider_stats,
        }
    async def close(self):
        """Clean shutdown of bandit"""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        # Final state persistence
        await self._persist_state()
        logger.info("Contextual bandit closed")
# Factory function for easy integration
def create_contextual_bandit(
    providers: List[str],
    redis_client: redis.Redis,
    exploration_decay_rate: float = 0.01,
    reward_weights: Optional[Dict[str, float]] = None,
) -> ProductionContextualBandit:
    """Factory function to create configured contextual bandit"""
    config = BanditConfig(
        exploration_decay_rate=exploration_decay_rate,
        reward_weights=reward_weights or {},
    )
    return ProductionContextualBandit(providers, redis_client, config)
