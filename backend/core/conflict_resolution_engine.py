"\nSophia AI Conflict Resolution Warlord\nMaster conflict resolver for Python errors, TypeScript conflicts, Pulumi mergers,\nn8n flows, Estuary retry logic, Qdrant upserts, Mem0 dedup, and Lambda Labs reconciliation.\nTargets 15% error reduction through intelligent conflict resolution.\n"

import asyncio
import logging
import time
import traceback
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts we handle"""

    PYTHON_EXCEPTION = "python_exception"
    TYPESCRIPT_TYPE_CONFLICT = "typescript_type_conflict"
    PULUMI_STACK_MERGE = "pulumi_stack_merge"
    N8N_WORKFLOW_ERROR = "n8n_workflow_error"
    ESTUARY_FLOW_RETRY = "estuary_flow_retry"
    QDRANT_UPSERT_CONFLICT = "qdrant_upsert_conflict"
    MEM0_DEDUPLICATION = "mem0_deduplication"
    LAMBDA_LABS_RESOURCE = "lambda_labs_resource"
    API_RATE_LIMIT = "api_rate_limit"
    DATABASE_DEADLOCK = "database_deadlock"
    NETWORK_TIMEOUT = "network_timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONCURRENT_MODIFICATION = "concurrent_modification"
    DATA_VALIDATION = "data_validation"
    AUTHENTICATION_FAILURE = "authentication_failure"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""

    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_VALUE = "fallback_value"
    QUEUE_FOR_LATER = "queue_for_later"
    AUTO_MERGE = "auto_merge"
    MANUAL_INTERVENTION = "manual_intervention"
    COMPENSATING_TRANSACTION = "compensating_transaction"
    CACHE_AND_CONTINUE = "cache_and_continue"
    THROTTLE_REQUESTS = "throttle_requests"
    ALTERNATIVE_PATH = "alternative_path"
    ROLLBACK = "rollback"
    IGNORE_AND_LOG = "ignore_and_log"


@dataclass
class ConflictContext:
    """Context for conflict resolution"""

    error_type: ConflictType
    error_message: str
    error_code: str | None = None
    stack_trace: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)
    resolution_history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ResolutionResult:
    """Result of conflict resolution"""

    success: bool
    strategy_used: ResolutionStrategy
    resolved_value: Any = None
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    should_retry: bool = False


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                    self.half_open_calls = 0
                else:
                    raise Exception("Circuit breaker is OPEN. Service unavailable.")
            if (
                self.state == "HALF_OPEN"
                and self.half_open_calls >= self.half_open_max_calls
            ):
                if self.failure_count > 0:
                    self.state = "OPEN"
                    raise Exception("Circuit breaker is OPEN after half-open test.")
                else:
                    self.state = "CLOSED"
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0
            if self.state == "HALF_OPEN":
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.state = "CLOSED"

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if (
                self.state == "HALF_OPEN"
                or self.failure_count >= self.failure_threshold
            ):
                self.state = "OPEN"

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            self.last_failure_time
            and time.time() - self.last_failure_time >= self.timeout
        )


class ExponentialBackoff:
    """Exponential backoff for retry logic"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def get_delay(self, retry_count: int) -> float:
        """Calculate delay for given retry count"""
        delay = min(self.base_delay * self.multiplier**retry_count, self.max_delay)
        if self.jitter:
            import random

            delay = delay * (0.5 + random.random() * 0.5)
        return delay


class DeadLetterQueue:
    """Dead letter queue for unrecoverable errors"""

    def __init__(self, max_size: int = 10000):
        self.queue = deque(maxlen=max_size)
        self.stats = defaultdict(int)

    async def add(self, context: ConflictContext, error: Exception):
        """Add failed operation to dead letter queue"""
        entry = {
            "context": context,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
        }
        self.queue.append(entry)
        self.stats[context.error_type.value] += 1
        logger.error(
            f"Added to dead letter queue: {context.error_type.value} - {error}"
        )

    async def process_batch(self, batch_size: int = 100) -> list[dict[str, Any]]:
        """Process a batch from dead letter queue"""
        batch = []
        for _ in range(min(batch_size, len(self.queue))):
            if self.queue:
                batch.append(self.queue.popleft())
        return batch

    def get_stats(self) -> dict[str, int]:
        """Get dead letter queue statistics"""
        return dict(self.stats)


class ConflictResolutionEngine:
    """Master conflict resolution engine"""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.backoff = ExponentialBackoff()
        self.dead_letter_queue = DeadLetterQueue()
        self.resolution_stats = defaultdict(lambda: {"success": 0, "failure": 0})
        self.handlers: dict[ConflictType, Callable] = {}
        self._register_default_handlers()
        self.error_patterns = {
            "rate limit": ConflictType.API_RATE_LIMIT,
            "timeout|timed out": ConflictType.NETWORK_TIMEOUT,
            "deadlock": ConflictType.DATABASE_DEADLOCK,
            "resource exhausted|out of memory": ConflictType.RESOURCE_EXHAUSTION,
            "concurrent modification|version conflict": ConflictType.CONCURRENT_MODIFICATION,
            "validation error|invalid data": ConflictType.DATA_VALIDATION,
            "unauthorized|authentication failed": ConflictType.AUTHENTICATION_FAILURE,
            "upsert conflict|duplicate key": ConflictType.QDRANT_UPSERT_CONFLICT,
        }

    def _register_default_handlers(self):
        """Register default conflict handlers"""
        self.handlers[ConflictType.PYTHON_EXCEPTION] = self._handle_python_exception
        self.handlers[ConflictType.API_RATE_LIMIT] = self._handle_rate_limit
        self.handlers[ConflictType.NETWORK_TIMEOUT] = self._handle_timeout
        self.handlers[ConflictType.DATABASE_DEADLOCK] = self._handle_deadlock
        self.handlers[ConflictType.QDRANT_UPSERT_CONFLICT] = (
            self._handle_qdrant_conflict
        )
        self.handlers[ConflictType.PULUMI_STACK_MERGE] = self._handle_pulumi_merge
        self.handlers[ConflictType.LAMBDA_LABS_RESOURCE] = self._handle_lambda_resource

    async def resolve_conflict(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Main conflict resolution entry point"""
        start_time = time.time()
        try:
            if context.error_type == ConflictType.PYTHON_EXCEPTION:
                context.error_type = self._detect_conflict_type(context.error_message)
            handler = self.handlers.get(context.error_type, self._default_handler)
            result = await handler(context, operation)
            self.resolution_stats[context.error_type.value]["success"] += 1
            context.resolution_history.append(
                {
                    "strategy": result.strategy_used.value,
                    "success": result.success,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            await self.dead_letter_queue.add(context, e)
            self.resolution_stats[context.error_type.value]["failure"] += 1
            return ResolutionResult(
                success=False,
                strategy_used=ResolutionStrategy.MANUAL_INTERVENTION,
                error=e,
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _detect_conflict_type(self, error_message: str) -> ConflictType:
        """Detect conflict type from error message"""
        import re

        error_lower = error_message.lower()
        for pattern, conflict_type in self.error_patterns.items():
            if re.search(pattern, error_lower):
                return conflict_type
        return ConflictType.PYTHON_EXCEPTION

    async def _handle_python_exception(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle generic Python exceptions with retry logic"""
        if context.retry_count < context.max_retries:
            delay = self.backoff.get_delay(context.retry_count)
            await asyncio.sleep(delay)
            try:
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.RETRY_WITH_BACKOFF,
                    resolved_value=result,
                )
            except Exception as e:
                context.retry_count += 1
                context.error_message = str(e)
                return await self.resolve_conflict(context, operation)
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.QUEUE_FOR_LATER,
            should_retry=True,
        )

    async def _handle_rate_limit(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle API rate limit errors"""
        retry_after = context.metadata.get("retry_after", 60)
        logger.warning(f"Rate limit hit. Waiting {retry_after} seconds.")
        await asyncio.sleep(retry_after)
        try:
            result = await operation()
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.THROTTLE_REQUESTS,
                resolved_value=result,
            )
        except Exception as e:
            return ResolutionResult(
                success=False, strategy_used=ResolutionStrategy.CIRCUIT_BREAKER, error=e
            )

    async def _handle_timeout(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle network timeout errors"""
        timeout_multiplier = 1.5
        current_timeout = context.metadata.get("timeout", 30)
        for i in range(context.max_retries):
            new_timeout = current_timeout * timeout_multiplier**i
            try:
                result = await asyncio.wait_for(operation(), timeout=new_timeout)
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.RETRY_WITH_BACKOFF,
                    resolved_value=result,
                )
            except TimeoutError:
                logger.warning(f"Timeout retry {i + 1}/{context.max_retries}")
                continue
            except Exception as e:
                return ResolutionResult(
                    success=False,
                    strategy_used=ResolutionStrategy.ALTERNATIVE_PATH,
                    error=e,
                )
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.FALLBACK_VALUE,
            resolved_value=context.metadata.get("default_value"),
        )

    async def _handle_deadlock(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle database deadlock with exponential backoff"""
        max_deadlock_retries = 5
        for i in range(max_deadlock_retries):
            delay = self.backoff.get_delay(i)
            await asyncio.sleep(delay)
            try:
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.RETRY_WITH_BACKOFF,
                    resolved_value=result,
                )
            except Exception as e:
                if "deadlock" not in str(e).lower() or i == max_deadlock_retries - 1:
                    return ResolutionResult(
                        success=False,
                        strategy_used=ResolutionStrategy.COMPENSATING_TRANSACTION,
                        error=e,
                    )
        return ResolutionResult(
            success=False, strategy_used=ResolutionStrategy.MANUAL_INTERVENTION
        )

    async def _handle_qdrant_conflict(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle Qdrant upsert conflicts"""
        if "vector_id" in context.metadata:
            original_id = context.metadata["vector_id"]
            new_id = f"{original_id}_{int(time.time() * 1000)}"
            context.metadata["vector_id"] = new_id
            try:
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.AUTO_MERGE,
                    resolved_value=result,
                    metadata={"new_id": new_id},
                )
            except Exception:
                return await self._deduplicate_and_merge(context, operation)
        return ResolutionResult(
            success=False, strategy_used=ResolutionStrategy.MANUAL_INTERVENTION
        )

    async def _handle_pulumi_merge(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle Pulumi stack merge conflicts"""
        if all(k in context.metadata for k in ["base", "ours", "theirs"]):
            try:
                merged = await self._three_way_merge(
                    context.metadata["base"],
                    context.metadata["ours"],
                    context.metadata["theirs"],
                )
                context.metadata["merged_config"] = merged
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.AUTO_MERGE,
                    resolved_value=result,
                    metadata={"merged_config": merged},
                )
            except Exception as e:
                logger.error(f"Three-way merge failed: {e}")
        return await self._timestamp_based_resolution(context, operation)

    async def _handle_lambda_resource(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Handle Lambda Labs resource conflicts"""
        resource_type = context.metadata.get("resource_type", "gpu")
        alternatives = {
            "gpu": ["rtx_6000", "a100_40gb", "a100_80gb"],
            "instance": ["gpu_1x_a100", "gpu_2x_a100", "gpu_4x_a100"],
        }
        for alternative in alternatives.get(resource_type, []):
            try:
                context.metadata["resource_id"] = alternative
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.ALTERNATIVE_PATH,
                    resolved_value=result,
                    metadata={"selected_resource": alternative},
                )
            except Exception:
                continue
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.QUEUE_FOR_LATER,
            should_retry=True,
        )

    async def _default_handler(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Default handler for unknown conflict types"""
        logger.warning(f"Unknown conflict type: {context.error_type.value}")
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.MANUAL_INTERVENTION,
            metadata={"requires_review": True},
        )

    async def _deduplicate_and_merge(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Deduplicate and merge conflicting entries"""
        existing_data = context.metadata.get("existing_data")
        new_data = context.metadata.get("new_data")
        if existing_data and new_data:
            merged_data = self._merge_data(existing_data, new_data)
            context.metadata["merged_data"] = merged_data
            try:
                result = await operation()
                return ResolutionResult(
                    success=True,
                    strategy_used=ResolutionStrategy.AUTO_MERGE,
                    resolved_value=result,
                )
            except Exception as e:
                logger.error(f"Merge failed: {e}")
        return ResolutionResult(
            success=False, strategy_used=ResolutionStrategy.MANUAL_INTERVENTION
        )

    async def _three_way_merge(self, base: dict, ours: dict, theirs: dict) -> dict:
        """Perform three-way merge for configurations"""
        merged = base.copy()
        for key, value in ours.items():
            if key not in base or base[key] != value:
                merged[key] = value
        conflicts = []
        for key, value in theirs.items():
            if key not in base or base[key] != value:
                if key in merged and merged[key] != value:
                    conflicts.append({"key": key, "ours": merged[key], "theirs": value})
                else:
                    merged[key] = value
        for conflict in conflicts:
            merged[conflict["key"]] = conflict["theirs"]
        return merged

    async def _timestamp_based_resolution(
        self, context: ConflictContext, operation: Callable
    ) -> ResolutionResult:
        """Resolve conflicts based on timestamp"""
        timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        if "name" in context.metadata:
            context.metadata["name"] = f"{context.metadata['name']}_{timestamp_suffix}"
        try:
            result = await operation()
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.AUTO_MERGE,
                resolved_value=result,
                metadata={"timestamp_suffix": timestamp_suffix},
            )
        except Exception as e:
            return ResolutionResult(
                success=False, strategy_used=ResolutionStrategy.ROLLBACK, error=e
            )

    def _merge_data(self, existing: Any, new: Any) -> Any:
        """Merge two data structures intelligently"""
        if isinstance(existing, dict) and isinstance(new, dict):
            merged = existing.copy()
            for key, value in new.items():
                if key in merged:
                    merged[key] = self._merge_data(merged[key], value)
                else:
                    merged[key] = value
            return merged
        elif isinstance(existing, list) and isinstance(new, list):
            return list(set(existing + new))
        else:
            return new

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def get_resolution_stats(self) -> dict[str, Any]:
        """Get conflict resolution statistics"""
        total_success = sum(s["success"] for s in self.resolution_stats.values())
        total_failure = sum(s["failure"] for s in self.resolution_stats.values())
        total_attempts = total_success + total_failure
        error_reduction = 0
        if total_attempts > 0:
            error_reduction = total_success / total_attempts * 100
        return {
            "total_conflicts_resolved": total_success,
            "total_conflicts_failed": total_failure,
            "error_reduction_percentage": error_reduction,
            "conflict_type_breakdown": dict(self.resolution_stats),
            "dead_letter_queue_stats": self.dead_letter_queue.get_stats(),
            "circuit_breaker_states": {
                name: cb.state for name, cb in self.circuit_breakers.items()
            },
            "target_error_reduction": 15,
            "current_vs_target": f"{error_reduction:.1f}% / 15%",
        }


conflict_resolver = ConflictResolutionEngine()
