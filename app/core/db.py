from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str | None:
    # Prefer DATABASE_URL; fallback to unified env var names if present
    return os.getenv("DATABASE_URL")


def get_engine() -> AsyncEngine | None:
    global _engine
    if _engine is not None:
        return _engine
    url = get_database_url()
    if not url:
        return None
    # Ensure async driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    _engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    global _session_factory
    if _session_factory is not None:
        return _session_factory
    engine = get_engine()
    if not engine:
        return None
    _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def session_scope() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("No database configured (DATABASE_URL missing)")
    async with factory() as session:
        yield session

