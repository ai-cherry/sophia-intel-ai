from __future__ import annotations

from typing import AsyncGenerator

from sqlmodel import SQLModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "sqlite+aiosqlite:///./factory.db"

engine = create_async_engine(
    DATABASE_URL, echo=False, future=True
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)


class AgentORM(SQLModel, table=True):
    __tablename__ = "agents"
    id: str = Field(primary_key=True)
    name: str
    role: str | None = None
    specialty: str | None = None
    description: str | None = None
    config: dict = Field(default_factory=dict, sa_column_kwargs={"nullable": False})
    version: int = 1
    published: bool = False
    created_at: float
    updated_at: float


class SwarmORM(SQLModel, table=True):
    __tablename__ = "swarms"
    id: str = Field(primary_key=True)
    name: str
    description: str | None = None
    agent_ids: list[str] = Field(default_factory=list, sa_column_kwargs={"nullable": False})
    template: dict = Field(default_factory=dict, sa_column_kwargs={"nullable": False})
    version: int = 1
    published: bool = False
    created_at: float
    updated_at: float


async def init_factory_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

