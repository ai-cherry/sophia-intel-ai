"""Database connection and session management"""

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://sophia:localdev@localhost:5432/sophia"
)

engine = None
SessionLocal = None


async def init_db():
    """Initialize database connection"""
    global engine, SessionLocal

    engine = create_async_engine(
        DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True, echo=False
    )

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Test connection
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")

    logger.info("Database initialized")


async def check_connection():
    """Check if database is accessible"""
    if not engine:
        return False
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except:
        return False


async def get_db():
    """Dependency for FastAPI routes"""
    if not SessionLocal:
        await init_db()
    async with SessionLocal() as session:
        yield session
