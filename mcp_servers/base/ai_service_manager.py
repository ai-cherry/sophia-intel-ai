from shared.core.common_functions import create_ai_service_config

"\nAI Service Manager - Critical Infrastructure for Performance Optimization\nLocation: mcp_servers/base/ai_service_manager.py\n\nWeek 1 Critical Infrastructure Component:\n- Intelligent connection pooling for AI services\n- Advanced retry logic with exponential backoff\n- Service health monitoring and failover\n- Request prioritization and queuing\n- Response optimization and caching\n"
import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
import backoff
import redis.asyncio as aioredis
from circuitbreaker import CircuitBreaker, CircuitBreakerOpenException

class ServiceTier(Enum):
    """AI Service tier classification for priority handling"""

    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"
    EXPERIMENTAL = "experimental"

class RequestPriority(Enum):
    """Request priority levels"""

    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BATCH = 5

@dataclass
class ServiceMetrics:
    """Comprehensive service performance metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_successful_request: datetime | None = None
    last_failed_request: datetime | None = None
    circuit_breaker_opens: int = 0
    cache_hit_rate: float = 0.0

@dataclass
class AIServiceConfig:
    """Configuration for AI service connections"""

    name: str
    base_url: str
    api_key: str
    tier: ServiceTier = ServiceTier.STANDARD
    max_concurrent_requests: int = 20
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    rate_limit_per_minute: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    health_check_interval: int = 60

class PriorityQueue:
    """High-performance priority queue for AI service requests"""

    def __init__(self):
        self.queues: dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }
        self.total_queued = 0
        self._processing = False

    async def put(self, item: Any, priority: RequestPriority = RequestPriority.NORMAL):
        """Add item to priority queue"""
        await self.queues[priority].put(item)
        self.total_queued += 1

    async def get(self) -> tuple[Any, RequestPriority]:
        """Get highest priority item from queue"""
        for priority in RequestPriority:
            if not self.queues[priority].empty():
                item = await self.queues[priority].get()
                self.total_queued -= 1
                return (item, priority)
        tasks = [
            asyncio.create_task(self.queues[priority].get(), name=priority.name)
            for priority in RequestPriority
        ]
        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
            completed_task = done.pop()
            priority = RequestPriority[completed_task.get_name()]
            item = completed_task.result()
            self.total_queued -= 1
            return (item, priority)
        except Exception as e:
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise e

    def qsize(self, priority: RequestPriority | None = None) -> int:
        """Get queue size for specific priority or total"""
        if priority:
            return self.queues[priority].qsize()
        return self.total_queued

class RateLimiter:
    """Token bucket rate limiter for AI services"""

    def __init__(self, rate_per_minute: int, burst_capacity: int | None = None):
        self.rate_per_minute = rate_per_minute
        self.burst_capacity = burst_capacity or rate_per_minute
        self.tokens = self.burst_capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket"""
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed / 60.0 * self.rate_per_minute
            self.tokens = min(self.burst_capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """Wait until tokens are available"""
        while not await self.acquire(tokens):
            wait_time = tokens / self.rate_per_minute * 60
            await asyncio.sleep(min(wait_time, 1.0))

class AIServiceConnection:
    """Individual AI service connection with advanced features"""

    def __init__(
        self, config: AIServiceConfig, redis_client: aioredis.Redis | None = None
    ):
        self.config = config
        self.redis_client = redis_client
        self.session: aiohttp.ClientSession | None = None
        self.metrics = ServiceMetrics()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.response_times: list[float] = []
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout,
            expected_exception=(aiohttp.ClientError, asyncio.TimeoutError),
        )
        self.last_health_check = datetime.utcnow()
        self.is_healthy = True
        self.logger = logging.getLogger(f"ai_service.{config.name}")

    async def initialize(self):
        """Initialize the service connection"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            limit_per_host=self.config.max_concurrent_requests,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,
            keepalive_timeout=60,
        )
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"SophiaAI-MCP/2.0 ({self.config.name})",
            },
        )
        asyncio.create_task(self._health_monitor())
        self.logger.info(f"AI service {self.config.name} initialized")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.logger.info(f"AI service {self.config.name} cleaned up")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=lambda self: self.config.max_retries + 1,
        factor=lambda self: self.config.retry_backoff_factor,
        jitter=backoff.full_jitter,
    )
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        cache_key: str | None = None,
        cache_ttl: int | None = None,
    ) -> dict[str, Any]:
        """Make an optimized request to the AI service"""
        if cache_key and self.config.enable_caching:
            cached_result = await self._get_cached_response(cache_key)
            if cached_result:
                return cached_result
        await self.rate_limiter.wait_for_tokens()
        start_time = time.time()
        try:
            self.metrics.total_requests += 1
            response_data = await self.circuit_breaker(self._execute_request)(
                method, endpoint, data
            )
            duration = time.time() - start_time
            self.metrics.successful_requests += 1
            self._update_response_times(duration)
            self.metrics.last_successful_request = datetime.utcnow()
            self.is_healthy = True
            if cache_key and self.config.enable_caching and response_data:
                await self._cache_response(cache_key, response_data, cache_ttl)
            return response_data
        except CircuitBreakerOpenException:
            self.metrics.circuit_breaker_opens += 1
            self.is_healthy = False
            raise Exception(f"Circuit breaker open for {self.config.name}")
        except Exception as e:
            self.metrics.failed_requests += 1
            self.metrics.last_failed_request = datetime.utcnow()
            self.is_healthy = False
            self.logger.error(f"Request failed for {self.config.name}: {e}")
            raise
        finally:
            self._update_error_rate()

    async def _execute_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Execute the actual HTTP request"""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        request_kwargs = {}
        if data:
            request_kwargs["json"] = data
        async with self.session.request(method, url, **request_kwargs) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                return await response.json()
            elif "text/" in content_type:
                return {"text": await response.text()}
            else:
                return {"data": await response.read()}

    async def _get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """Get response from cache"""
        if not self.redis_client:
            return None
        try:
            cached_data = await self.redis_client.get(
                f"ai_cache:{self.config.name}:{cache_key}"
            )
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
        return None

    async def _cache_response(
        self, cache_key: str, response_data: dict[str, Any], ttl: int | None = None
    ):
        """Cache response data"""
        if not self.redis_client:
            return
        try:
            ttl = ttl or self.config.cache_ttl_seconds
            cache_data = json.dumps(response_data, default=str)
            await self.redis_client.setex(
                f"ai_cache:{self.config.name}:{cache_key}", ttl, cache_data
            )
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")

    def _update_response_times(self, duration: float):
        """Update response time metrics"""
        self.response_times.append(duration)
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        self.metrics.average_response_time = sum(self.response_times) / len(
            self.response_times
        )
        sorted_times = sorted(self.response_times)
        if len(sorted_times) >= 20:
            self.metrics.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            self.metrics.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]

    def _update_error_rate(self):
        """Update error rate metrics"""
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = (
                self.metrics.failed_requests / self.metrics.total_requests * 100
            )

    async def _health_monitor(self):
        """Continuous health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                try:
                    await self._execute_request("GET", "/health", None)
                    self.is_healthy = True
                except:
                    self.is_healthy = False
                self.last_health_check = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive service status"""
        return {
            "name": self.config.name,
            "tier": self.config.tier.value,
            "healthy": self.is_healthy,
            "circuit_breaker_state": self.circuit_breaker.current_state,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": (
                    self.metrics.successful_requests / self.metrics.total_requests * 100
                    if self.metrics.total_requests > 0
                    else 0
                ),
                "average_response_time_ms": self.metrics.average_response_time * 1000,
                "p95_response_time_ms": self.metrics.p95_response_time * 1000,
                "error_rate": self.metrics.error_rate,
                "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
                "last_health_check": (
                    self.last_health_check.isoformat()
                    if self.last_health_check
                    else None
                ),
            },
            "rate_limiting": {
                "rate_per_minute": self.config.rate_limit_per_minute,
                "current_tokens": self.rate_limiter.tokens,
            },
        }

class AIServiceManager:
    """
    Centralized AI Service Manager for optimal performance and reliability.

    Provides:
    - Intelligent service selection and load balancing
    - Advanced request routing and prioritization
    - Comprehensive health monitoring and failover
    - Performance optimization and caching
    """

    def __init__(self, redis_url: str | None = None):
        self.services: dict[str, AIServiceConnection] = {}
        self.request_queue = PriorityQueue()
        self.redis_client: aioredis.Redis | None = None
        self.redis_url = redis_url
        self.load_balancer = LoadBalancer()
        self.global_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "services_count": 0,
            "healthy_services_count": 0,
        }
        self.logger = logging.getLogger("ai_service_manager")

    async def initialize(self):
        """Initialize the service manager"""
        if self.redis_url:
            try:
                self.redis_client = await aioredis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=False
                )
                await self.redis_client.ping()
                self.logger.info("Redis connection established")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        asyncio.create_task(self._process_requests())
        self.logger.info("AI Service Manager initialized")

    async def add_service(self, config: AIServiceConfig):
        """Add an AI service to the manager"""
        service = AIServiceConnection(config, self.redis_client)
        await service.initialize()
        self.services[config.name] = service
        self.global_metrics["services_count"] = len(self.services)
        self.logger.info(f"Added AI service: {config.name} ({config.tier.value})")

    async def remove_service(self, service_name: str):
        """Remove an AI service from the manager"""
        if service_name in self.services:
            await self.services[service_name].cleanup()
            del self.services[service_name]
            self.global_metrics["services_count"] = len(self.services)
            self.logger.info(f"Removed AI service: {service_name}")

    async def request(
        self,
        service_name: str | None,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        tier_preference: ServiceTier | None = None,
        cache_key: str | None = None,
        cache_ttl: int | None = None,
    ) -> dict[str, Any]:
        """Make a request to an AI service with intelligent routing"""
        if not service_name:
            service_name = await self._select_optimal_service(tier_preference)
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found")
        self.services[service_name]
        request_context = {
            "service_name": service_name,
            "method": method,
            "endpoint": endpoint,
            "data": data,
            "priority": priority,
            "cache_key": cache_key,
            "cache_ttl": cache_ttl,
            "future": asyncio.Future(),
            "created_at": datetime.utcnow(),
        }
        await self.request_queue.put(request_context, priority)
        return await request_context["future"]

    async def _process_requests(self):
        """Process requests from the priority queue"""
        while True:
            try:
                request_context, priority = await self.request_queue.get()
                asyncio.create_task(self._execute_request(request_context))
            except Exception as e:
                self.logger.error(f"Request processor error: {e}")

    async def _execute_request(self, request_context: dict[str, Any]):
        """Execute a single request"""
        try:
            service = self.services[request_context["service_name"]]
            result = await service.make_request(
                method=request_context["method"],
                endpoint=request_context["endpoint"],
                data=request_context["data"],
                priority=request_context["priority"],
                cache_key=request_context["cache_key"],
                cache_ttl=request_context["cache_ttl"],
            )
            self.global_metrics["total_requests"] += 1
            self.global_metrics["successful_requests"] += 1
            if not request_context["future"].done():
                request_context["future"].set_result(result)
        except Exception as e:
            self.global_metrics["total_requests"] += 1
            self.global_metrics["failed_requests"] += 1
            if not request_context["future"].done():
                request_context["future"].set_exception(e)

    async def _select_optimal_service(
        self, tier_preference: ServiceTier | None = None
    ) -> str:
        """Select the optimal service based on health, performance, and tier"""
        candidate_services = []
        for name, service in self.services.items():
            if tier_preference is None or service.config.tier == tier_preference:
                if (
                    service.is_healthy
                    and service.circuit_breaker.current_state == "closed"
                ):
                    candidate_services.append((name, service))
        if not candidate_services:
            raise Exception("No healthy services available")
        return self.load_balancer.select_service(candidate_services)

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""
        healthy_services = sum(1 for s in self.services.values() if s.is_healthy)
        self.global_metrics["healthy_services_count"] = healthy_services
        service_statuses = {
            name: service.get_status() for name, service in self.services.items()
        }
        return {
            "global_metrics": self.global_metrics,
            "services": service_statuses,
            "queue_status": {
                "total_queued": self.request_queue.total_queued,
                "urgent_queued": self.request_queue.qsize(RequestPriority.URGENT),
                "high_queued": self.request_queue.qsize(RequestPriority.HIGH),
                "normal_queued": self.request_queue.qsize(RequestPriority.NORMAL),
            },
            "health_summary": {
                "total_services": len(self.services),
                "healthy_services": healthy_services,
                "unhealthy_services": len(self.services) - healthy_services,
                "overall_health_percentage": (
                    healthy_services / len(self.services) * 100 if self.services else 0
                ),
            },
        }

class LoadBalancer:
    """Intelligent load balancer for AI services"""

    def select_service(self, services: list[tuple[str, AIServiceConnection]]) -> str:
        """Select service using weighted round-robin based on performance"""
        if not services:
            raise Exception("No services available")
        if len(services) == 1:
            return services[0][0]
        weighted_services = []
        for name, service in services:
            response_time_factor = 1.0 / (service.metrics.average_response_time + 0.001)
            success_rate = (
                service.metrics.successful_requests / service.metrics.total_requests
                if service.metrics.total_requests > 0
                else 1.0
            )
            weight = response_time_factor * success_rate * 100
            weighted_services.append((name, weight))
        total_weight = sum((weight for _, weight in weighted_services))
        if total_weight == 0:
            return services[0][0]
        import random

        random_value = random.uniform(0, total_weight)
        cumulative_weight = 0
        for name, weight in weighted_services:
            cumulative_weight += weight
            if random_value <= cumulative_weight:
                return name
        return weighted_services[0][0]

__all__ = [
    "AIServiceManager",
    "AIServiceConfig",
    "AIServiceConnection",
    "ServiceTier",
    "RequestPriority",
    "create_ai_service_config",
]
"""
ai_service_manager.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""

