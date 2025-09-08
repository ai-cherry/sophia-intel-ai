"""
Adaptive Hedged Requests Manager
Combines custom asyncio hedging with Tenacity retry fallback for maximum performance
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class HedgeConfig:
    initial_delay_ms: int = 200  # Aggressive initial delay
    max_hedges: int = 3  # Higher hedge count for better coverage
    timeout_ms: int = 2000  # Balanced timeout
    backoff_multiplier: float = 1.5
    provider_weights: Optional[Dict[str, float]] = None
    enable_adaptive_delays: bool = True
    ewma_alpha: float = 0.2  # For latency smoothing
    hedge_success_threshold: float = 0.3  # Hedge if >30% chance of improvement


@dataclass
class HedgeMetrics:
    total_requests: int = 0
    hedge_wins: int = 0
    hedge_losses: int = 0
    total_latency_saved_ms: float = 0
    provider_latencies: Dict[str, float] = None

    def __post_init__(self):
        if self.provider_latencies is None:
            self.provider_latencies = {}


class AdaptiveHedgedRequestManager:
    """
    Combines custom asyncio hedging with Tenacity retry fallback
    Features:
    - EWMA latency tracking for adaptive delays
    - Request deduplication with in-flight tracking
    - Circuit breaker integration
    - Comprehensive metrics collection
    """

    def __init__(self, config: HedgeConfig):
        self.config = config
        self._in_flight: Dict[str, asyncio.Future] = {}
        self._latency_ewma: Dict[str, float] = {}
        self._provider_success_rates: Dict[str, float] = {}
        self._metrics = HedgeMetrics()
        self._lock = asyncio.Lock()

        # Initialize provider weights if not provided
        if not config.provider_weights:
            self.config.provider_weights = {}

    async def execute_hedged(
        self,
        request_fn: Callable,
        providers: List[str],
        query_key: str,
        circuit_breaker_fn: Optional[Callable] = None,
        *args,
        **kwargs,
    ) -> Tuple[Any, str, Dict[str, Any]]:
        """
        Execute hedged request with adaptive delays and circuit breaker integration

        Args:
            request_fn: Async function to execute (session, provider, *args, **kwargs)
            providers: List of provider names to try
            query_key: Unique key for request deduplication
            circuit_breaker_fn: Optional circuit breaker check function

        Returns:
            Tuple of (result, winning_provider, metrics)
        """

        # Generate request hash for deduplication
        request_hash = self._hash_request(query_key, args, kwargs)

        # Check if request is already in flight
        async with self._lock:
            if request_hash in self._in_flight:
                logger.debug(f"Request {request_hash} already in flight, waiting...")
                return await self._in_flight[request_hash]

            # Create future for this request
            future = asyncio.get_event_loop().create_future()
            self._in_flight[request_hash] = future

        try:
            # Filter providers through circuit breaker if provided
            available_providers = providers
            if circuit_breaker_fn:
                available_providers = [
                    p for p in providers if await circuit_breaker_fn(p)
                ]

                if not available_providers:
                    raise Exception("All providers are circuit broken")

            # Sort providers by success rate and latency
            sorted_providers = self._sort_providers_by_performance(available_providers)

            # Calculate adaptive delays
            hedge_delays = self._calculate_adaptive_delays(sorted_providers)

            # Execute hedged requests
            result = await self._execute_hedged_internal(
                request_fn, sorted_providers, hedge_delays, args, kwargs
            )

            # Set future result
            future.set_result(result)
            return result

        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            # Clean up in-flight tracking
            async with self._lock:
                if request_hash in self._in_flight:
                    del self._in_flight[request_hash]

    async def _execute_hedged_internal(
        self,
        request_fn: Callable,
        providers: List[str],
        hedge_delays: List[float],
        args: tuple,
        kwargs: dict,
    ) -> Tuple[Any, str, Dict[str, Any]]:
        """Internal hedged execution with comprehensive metrics"""

        tasks = []
        start_times = []
        request_start = time.time()

        self._metrics.total_requests += 1

        try:
            # Launch requests with adaptive delays
            for i, provider in enumerate(providers[: self.config.max_hedges]):
                if i > 0:
                    # Wait for adaptive delay
                    await asyncio.sleep(hedge_delays[i - 1] / 1000)

                start_time = time.time()
                start_times.append(start_time)

                # Create resilient request with Tenacity retry
                task = asyncio.create_task(
                    self._create_resilient_request(request_fn, provider, args, kwargs)
                )
                tasks.append((task, provider, start_time))

                logger.debug(f"Launched hedged request {i+1} to {provider}")

            # Race for first successful response
            while tasks:
                done, pending = await asyncio.wait(
                    [t[0] for t in tasks],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=self.config.timeout_ms / 1000,
                )

                # Check for successful completion
                for task in done:
                    if not task.exception():
                        # Found winner
                        result = task.result()
                        winner_info = next((p, s) for t, p, s in tasks if t == task)
                        provider, start_time = winner_info

                        # Calculate metrics
                        latency = (time.time() - start_time) * 1000
                        total_latency = (time.time() - request_start) * 1000

                        # Update provider metrics
                        self._update_provider_metrics(provider, latency, True)

                        # Cancel remaining tasks
                        for t, _, _ in tasks:
                            if t in pending:
                                t.cancel()

                        # Track hedge effectiveness
                        hedge_activated = len(done) > 1 or len(tasks) > 1
                        if hedge_activated:
                            task_index = next(
                                i for i, (t, _, _) in enumerate(tasks) if t == task
                            )
                            if task_index > 0:
                                self._metrics.hedge_wins += 1
                                # Estimate latency saved
                                estimated_original_latency = self._latency_ewma.get(
                                    providers[0], latency
                                )
                                latency_saved = max(
                                    0, estimated_original_latency - latency
                                )
                                self._metrics.total_latency_saved_ms += latency_saved
                            else:
                                self._metrics.hedge_losses += 1

                        metrics = {
                            "latency_ms": latency,
                            "total_latency_ms": total_latency,
                            "hedge_activated": hedge_activated,
                            "providers_tried": len(done),
                            "winning_provider": provider,
                            "hedge_effectiveness": self._calculate_hedge_effectiveness(),
                        }

                        logger.info(
                            f"Hedged request completed: {provider} in {latency:.1f}ms"
                        )
                        return (result, provider, metrics)

                # Remove failed tasks and update metrics
                failed_tasks = [
                    (t, p, s) for t, p, s in tasks if t in done and t.exception()
                ]
                for task, provider, start_time in failed_tasks:
                    latency = (time.time() - start_time) * 1000
                    self._update_provider_metrics(provider, latency, False)
                    logger.warning(f"Provider {provider} failed: {task.exception()}")

                # Continue with remaining tasks
                tasks = [(t, p, s) for t, p, s in tasks if t not in done]

            raise Exception("All hedged requests failed or timed out")

        except Exception as e:
            logger.error(f"Hedged request failed completely: {e}")
            raise

    @retry(
        stop=stop_after_attempt(2), wait=wait_exponential(min=0.1, max=1), reraise=True
    )
    async def _create_resilient_request(
        self, request_fn: Callable, provider: str, args: tuple, kwargs: dict
    ) -> Any:
        """Create request with Tenacity retry wrapper"""

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_ms / 1000),
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            ),
        ) as session:
            return await request_fn(session, provider, *args, **kwargs)

    def _calculate_adaptive_delays(self, providers: List[str]) -> List[float]:
        """Calculate adaptive delays based on EWMA latencies"""

        if not self.config.enable_adaptive_delays:
            # Use fixed delays
            delays = []
            base_delay = self.config.initial_delay_ms
            for i in range(1, len(providers)):
                delays.append(base_delay)
                base_delay *= self.config.backoff_multiplier
            return delays

        delays = []
        base_delay = self.config.initial_delay_ms

        for i in range(1, len(providers)):
            # Use EWMA latency if available
            if providers[i - 1] in self._latency_ewma:
                # Hedge at percentage of typical latency based on success threshold
                adaptive_delay = (
                    self._latency_ewma[providers[i - 1]]
                    * self.config.hedge_success_threshold
                )
                delays.append(min(adaptive_delay, base_delay * 2))
            else:
                delays.append(base_delay)

            base_delay *= self.config.backoff_multiplier

        return delays

    def _sort_providers_by_performance(self, providers: List[str]) -> List[str]:
        """Sort providers by success rate and latency"""

        def provider_score(provider: str) -> float:
            # Combine success rate and latency (lower is better)
            success_rate = self._provider_success_rates.get(provider, 0.5)
            latency = self._latency_ewma.get(provider, 1000)  # Default 1s
            weight = self.config.provider_weights.get(provider, 1.0)

            # Score: higher success rate, lower latency, higher weight = better
            return (success_rate * weight) / (latency + 1)

        return sorted(providers, key=provider_score, reverse=True)

    def _update_provider_metrics(self, provider: str, latency: float, success: bool):
        """Update EWMA latency and success rate for provider"""

        alpha = self.config.ewma_alpha

        # Update latency EWMA
        if provider not in self._latency_ewma:
            self._latency_ewma[provider] = latency
        else:
            self._latency_ewma[provider] = (
                alpha * latency + (1 - alpha) * self._latency_ewma[provider]
            )

        # Update success rate EWMA
        success_value = 1.0 if success else 0.0
        if provider not in self._provider_success_rates:
            self._provider_success_rates[provider] = success_value
        else:
            self._provider_success_rates[provider] = (
                alpha * success_value
                + (1 - alpha) * self._provider_success_rates[provider]
            )

        # Update metrics
        self._metrics.provider_latencies[provider] = self._latency_ewma[provider]

    def _calculate_hedge_effectiveness(self) -> float:
        """Calculate overall hedge effectiveness ratio"""

        total_hedges = self._metrics.hedge_wins + self._metrics.hedge_losses
        if total_hedges == 0:
            return 0.0

        return self._metrics.hedge_wins / total_hedges

    def _hash_request(self, query_key: str, args: tuple, kwargs: dict) -> str:
        """Generate hash for request deduplication"""

        # Create deterministic hash from query key and parameters
        content = {
            "query_key": query_key,
            "args": str(args),
            "kwargs": json.dumps(kwargs, sort_keys=True, default=str),
        }

        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[
            :16
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive hedging metrics"""

        return {
            "total_requests": self._metrics.total_requests,
            "hedge_wins": self._metrics.hedge_wins,
            "hedge_losses": self._metrics.hedge_losses,
            "hedge_effectiveness": self._calculate_hedge_effectiveness(),
            "total_latency_saved_ms": self._metrics.total_latency_saved_ms,
            "avg_latency_saved_per_request": (
                self._metrics.total_latency_saved_ms
                / max(1, self._metrics.total_requests)
            ),
            "provider_latencies": dict(self._latency_ewma),
            "provider_success_rates": dict(self._provider_success_rates),
            "in_flight_requests": len(self._in_flight),
        }

    def reset_metrics(self):
        """Reset all metrics for fresh measurement"""
        self._metrics = HedgeMetrics()
        self._latency_ewma.clear()
        self._provider_success_rates.clear()


# Factory function for easy integration
def create_hedged_request_manager(
    initial_delay_ms: int = 200,
    max_hedges: int = 3,
    timeout_ms: int = 2000,
    provider_weights: Optional[Dict[str, float]] = None,
) -> AdaptiveHedgedRequestManager:
    """Factory function to create configured hedged request manager"""

    config = HedgeConfig(
        initial_delay_ms=initial_delay_ms,
        max_hedges=max_hedges,
        timeout_ms=timeout_ms,
        provider_weights=provider_weights or {},
    )

    return AdaptiveHedgedRequestManager(config)
