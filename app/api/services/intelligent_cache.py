"""
Lightweight caching shim for integrations.
This is a non-persistent, no-op decorator by default to keep dependencies light.
Replace with a real cache if needed.
"""
from __future__ import annotations

from functools import wraps

def cached(func):  # type: ignore
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

