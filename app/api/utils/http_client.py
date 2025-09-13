from __future__ import annotations

import asyncio
import contextlib
from typing import Optional, Callable, Any

import httpx

_client: Optional[httpx.AsyncClient] = None
_lock = asyncio.Lock()


async def get_async_client(timeout: float = 20.0) -> httpx.AsyncClient:
    """Return a shared AsyncClient with connection pooling and sane defaults.

    Lazily initializes a single client per process. Callers must not close it.
    """
    global _client
    if _client is not None:
        return _client
    async with _lock:
        if _client is None:
            _client = httpx.AsyncClient(
                timeout=timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                transport=httpx.AsyncHTTPTransport(retries=0),
            )
        return _client


async def with_retries(
    func: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    retry_on: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Any:
    """Execute an async HTTP call with basic exponential backoff retries.

    Expects `func` to raise httpx.HTTPStatusError on HTTP error for status code checks
    or httpx.TransportError for transport failures.
    """
    delay = base_delay
    last_exc: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except httpx.HTTPStatusError as e:  # pragma: no cover - passthrough
            last_exc = e
            if e.response is None or e.response.status_code not in retry_on:
                raise
        except (httpx.TransportError, httpx.RemoteProtocolError) as e:  # pragma: no cover
            last_exc = e
        if attempt < attempts:
            await asyncio.sleep(delay)
            delay *= 2
    if last_exc:
        raise last_exc
    return None


@contextlib.asynccontextmanager
async def span(operation: str):
    """Lightweight context manager for future tracing integration.

    This avoids importing telemetry in hot paths to sidestep circular imports.
    """
    yield

