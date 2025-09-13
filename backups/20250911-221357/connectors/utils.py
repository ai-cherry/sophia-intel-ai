from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def async_retry(max_attempts: int = 2, base_delay: float = 0.5) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        async def wrapper(*args, **kwargs):  # type: ignore
            attempt = 0
            last_exc: Exception | None = None
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:  # noqa: BLE001
                    last_exc = e
                    attempt += 1
                    await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
            if last_exc:
                raise last_exc
        return wrapper  # type: ignore
    return decorator

