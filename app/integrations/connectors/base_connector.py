"""
Base Connector Pattern for Enterprise Integrations
Foundation for all external service connectors
"""

import asyncio
import contextlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp

from app.core.circuit_breaker import CircuitBreaker
from app.core.secrets_manager import get_secrets_manager
from app.memory.unified_memory_router import DocChunk, MemoryDomain, get_memory_router

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Connector health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    EXPONENTIAL_BACKOFF = "exponential_backoff"


@dataclass
class ConnectorConfig:
    """Configuration for a connector"""

    name: str
    base_url: str
    api_version: str = "v1"
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_calls: int = 100
    rate_limit_period: int = 60  # seconds
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    cache_ttl: int = 300  # seconds
    sync_interval: int = 3600  # seconds
    webhook_enabled: bool = False
    webhook_secret: Optional[str] = None


@dataclass
class SyncReport:
    """Report from sync operation"""

    success: bool
    records_fetched: int
    records_stored: int
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    next_sync: Optional[datetime] = None


@dataclass
class RateLimiter:
    """Rate limiting implementation"""

    max_calls: int
    period_seconds: int
    strategy: RateLimitStrategy
    _call_times: list[datetime] = field(default_factory=list)
    _tokens: float = field(init=False)

    def __post_init__(self):
        self._tokens = float(self.max_calls)

    async def acquire(self) -> bool:
        """Acquire permission to make a call"""
        now = datetime.now()

        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            # Remove old calls outside window
            cutoff = now - timedelta(seconds=self.period_seconds)
            self._call_times = [t for t in self._call_times if t > cutoff]

            if len(self._call_times) < self.max_calls:
                self._call_times.append(now)
                return True
            return False

        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            # Refill tokens based on time passed
            if hasattr(self, "_last_refill"):
                time_passed = (now - self._last_refill).total_seconds()
                refill_rate = self.max_calls / self.period_seconds
                self._tokens = min(
                    self.max_calls, self._tokens + time_passed * refill_rate
                )

            self._last_refill = now

            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

        return True  # Default allow

    async def wait_if_needed(self) -> None:
        """Wait if rate limit exceeded"""
        while not await self.acquire():
            await asyncio.sleep(1)


class BaseConnector(ABC):
    """
    Base class for all enterprise connectors.
    Provides common functionality for authentication, rate limiting, caching, and sync.
    """

    def __init__(self, config: ConnectorConfig):
        """
        Initialize base connector

        Args:
            config: Connector configuration
        """
        self.config = config
        self.name = config.name

        # Get credentials from secrets manager
        self.secrets = get_secrets_manager()
        self.credentials = self._load_credentials()

        # Initialize HTTP client
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_calls=config.rate_limit_calls,
            period_seconds=config.rate_limit_period,
            strategy=config.rate_limit_strategy,
        )

        # Circuit breaker for fault tolerance
        from app.core.circuit_breaker import CircuitBreakerConfig

        breaker_config = CircuitBreakerConfig(
            failure_threshold=5, timeout=60, expected_exception=aiohttp.ClientError
        )
        self.circuit_breaker = CircuitBreaker(
            name=f"{self.name}_breaker", config=breaker_config
        )

        # Memory router for caching and storage
        self.memory = get_memory_router()

        # Sync state
        self.last_sync: Optional[datetime] = None
        self.sync_in_progress = False
        self._sync_task: Optional[asyncio.Task] = None

        # Metrics
        self.metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "total_records": 0,
            "last_error": None,
        }

        # Status
        self.status = ConnectorStatus.DISCONNECTED

        logger.info(f"Initialized {self.name} connector")

    def _load_credentials(self) -> dict[str, Optional[str]]:
        """Load credentials from secrets manager"""
        return self.secrets.get_integration_credentials(self.name)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to service"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers=self._get_default_headers(),
            )

        # Test connection
        if await self.test_connection():
            self.status = ConnectorStatus.HEALTHY
            logger.info(f"{self.name} connector connected successfully")
        else:
            self.status = ConnectorStatus.UNHEALTHY
            logger.warning(f"{self.name} connector failed to connect")

    async def disconnect(self) -> None:
        """Close connection to service"""
        if self._sync_task:
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task

        if self.session:
            await self.session.close()
            self.session = None

        self.status = ConnectorStatus.DISCONNECTED
        logger.info(f"{self.name} connector disconnected")

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            "User-Agent": f"SophiaIntelAI/{self.config.name}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Add authentication headers
        if self.credentials.get("api_key"):
            headers["Authorization"] = f"Bearer {self.credentials['api_key']}"
        elif self.credentials.get("access_token"):
            headers["Authorization"] = f"Bearer {self.credentials['access_token']}"

        return headers

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the service

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def fetch_data(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch data from the service

        Args:
            params: Query parameters

        Returns:
            Fetched data
        """
        pass

    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with rate limiting and circuit breaker

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers

        Returns:
            Response data
        """
        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        # Build URL
        url = f"{self.config.base_url}/{self.config.api_version}/{endpoint}"

        # Merge headers
        req_headers = self._get_default_headers()
        if headers:
            req_headers.update(headers)

        # Make request with circuit breaker
        async def _request():
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=req_headers,
            ) as response:
                self.metrics["requests_total"] += 1

                if response.status >= 400:
                    self.metrics["requests_failed"] += 1
                    self.metrics["last_error"] = (
                        f"{response.status}: {await response.text()}"
                    )
                    response.raise_for_status()

                return await response.json()

        try:
            return await self.circuit_breaker.call(_request)
        except Exception as e:
            logger.error(f"{self.name} request failed: {e}")
            self.status = ConnectorStatus.DEGRADED
            raise

    async def sync(self, full_sync: bool = False) -> SyncReport:
        """
        Sync data from service to memory

        Args:
            full_sync: Whether to do full sync or incremental

        Returns:
            Sync report
        """
        if self.sync_in_progress:
            logger.warning(f"{self.name} sync already in progress")
            return SyncReport(success=False, records_fetched=0, records_stored=0)

        self.sync_in_progress = True
        start_time = datetime.now()
        report = SyncReport(success=False, records_fetched=0, records_stored=0)

        try:
            # Determine sync parameters
            params = self._get_sync_params(full_sync)

            # Fetch data
            data = await self.fetch_data(params)
            report.records_fetched = self._count_records(data)

            # Transform data to chunks
            chunks = await self._transform_to_chunks(data)

            # Store in memory
            if chunks:
                upsert_report = await self.memory.upsert_chunks(
                    chunks, domain=MemoryDomain.SOPHIA
                )
                report.records_stored = upsert_report.chunks_stored

            # Cache raw data
            await self._cache_data(data)

            # Update sync state
            self.last_sync = datetime.now()
            report.success = True
            report.next_sync = self.last_sync + timedelta(
                seconds=self.config.sync_interval
            )

            logger.info(
                f"{self.name} sync completed: {report.records_fetched} fetched, {report.records_stored} stored"
            )

        except Exception as e:
            logger.error(f"{self.name} sync failed: {e}")
            report.errors.append(str(e))
            self.status = ConnectorStatus.DEGRADED

        finally:
            self.sync_in_progress = False
            report.duration_seconds = (datetime.now() - start_time).total_seconds()

        return report

    def _get_sync_params(self, full_sync: bool) -> dict[str, Any]:
        """Get parameters for sync operation"""
        params = {}

        if not full_sync and self.last_sync:
            # Incremental sync from last sync time
            params["modified_since"] = self.last_sync.isoformat()
            params["limit"] = 1000
        else:
            # Full sync with pagination
            params["limit"] = 1000
            params["offset"] = 0

        return params

    def _count_records(self, data: dict[str, Any]) -> int:
        """Count records in fetched data"""
        # Default implementation - override in subclasses
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Look for common keys
            for key in ["records", "data", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
        return 1

    async def _transform_to_chunks(self, data: dict[str, Any]) -> list[DocChunk]:
        """
        Transform fetched data to document chunks for storage

        Args:
            data: Raw fetched data

        Returns:
            List of document chunks
        """
        chunks = []

        # Default implementation - override in subclasses
        if isinstance(data, list):
            for item in data:
                chunk = DocChunk(
                    content=json.dumps(item),
                    source_uri=f"{self.name}://{item.get('id', 'unknown')}",
                    domain=MemoryDomain.SOPHIA,
                    metadata={
                        "connector": self.name,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                chunks.append(chunk)

        return chunks

    async def _cache_data(self, data: dict[str, Any]) -> None:
        """Cache raw data in memory"""
        cache_key = f"{self.name}:latest_data"
        await self.memory.put_ephemeral(cache_key, data, ttl_s=self.config.cache_ttl)

    async def get_cached_data(self) -> Optional[dict[str, Any]]:
        """Get cached data if available"""
        cache_key = f"{self.name}:latest_data"
        return await self.memory.get_ephemeral(cache_key)

    def start_auto_sync(self) -> None:
        """Start automatic periodic sync"""
        if self._sync_task:
            logger.warning(f"{self.name} auto-sync already running")
            return

        self._sync_task = asyncio.create_task(self._auto_sync_loop())
        logger.info(
            f"{self.name} auto-sync started (interval: {self.config.sync_interval}s)"
        )

    def stop_auto_sync(self) -> None:
        """Stop automatic sync"""
        if self._sync_task:
            self._sync_task.cancel()
            self._sync_task = None
            logger.info(f"{self.name} auto-sync stopped")

    async def _auto_sync_loop(self) -> None:
        """Auto sync loop"""
        while True:
            try:
                await asyncio.sleep(self.config.sync_interval)
                await self.sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.name} auto-sync error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def handle_webhook(
        self, payload: dict[str, Any], signature: Optional[str] = None
    ) -> bool:
        """
        Handle webhook from service

        Args:
            payload: Webhook payload
            signature: Webhook signature for verification

        Returns:
            True if handled successfully
        """
        if not self.config.webhook_enabled:
            logger.warning(f"{self.name} webhook received but webhooks disabled")
            return False

        # Verify signature if configured
        if self.config.webhook_secret and not self._verify_webhook_signature(
            payload, signature
        ):
            logger.warning(f"{self.name} webhook signature verification failed")
            return False

        # Process webhook
        try:
            await self._process_webhook(payload)
            return True
        except Exception as e:
            logger.error(f"{self.name} webhook processing failed: {e}")
            return False

    def _verify_webhook_signature(
        self, payload: dict[str, Any], signature: Optional[str]
    ) -> bool:
        """Verify webhook signature"""
        # Implementation depends on service
        # This is a placeholder
        return True

    @abstractmethod
    async def _process_webhook(self, payload: dict[str, Any]) -> None:
        """
        Process webhook payload

        Args:
            payload: Webhook payload
        """
        pass

    def get_status(self) -> dict[str, Any]:
        """Get connector status"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_in_progress": self.sync_in_progress,
            "metrics": self.metrics,
            "circuit_breaker_state": self.circuit_breaker.state,
            "config": {
                "base_url": self.config.base_url,
                "sync_interval": self.config.sync_interval,
                "webhook_enabled": self.config.webhook_enabled,
            },
        }
