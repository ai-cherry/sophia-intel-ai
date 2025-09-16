from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from .factory_db import AgentORM, SwarmORM, init_factory_db, get_session
from app.api.security.rbac import require_admin
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/factory", tags=["factory", "agents", "swarms"]) 


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: Optional[str] = None
    specialty: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    published: bool = False
    created_at: float = Field(default_factory=lambda: time.time())
    updated_at: float = Field(default_factory=lambda: time.time())


class AgentCreate(BaseModel):
    name: str
    role: Optional[str] = None
    specialty: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    specialty: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    published: Optional[bool] = None


class Swarm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    template: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    published: bool = False
    created_at: float = Field(default_factory=lambda: time.time())
    updated_at: float = Field(default_factory=lambda: time.time())


class SwarmCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    template: Dict[str, Any] = Field(default_factory=dict)


class SwarmUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    template: Optional[Dict[str, Any]] = None
    published: Optional[bool] = None


@router.on_event("startup")
async def _startup_factory():
    await init_factory_db()


# ---------------- Agents ----------------


@router.get("/agents", response_model=List[Agent])
async def list_agents(session: AsyncSession = Depends(get_session)) -> List[Agent]:
    res = await session.execute(select(AgentORM))
    rows = res.scalars().all()
    return [
        Agent(
            id=r.id,
            name=r.name,
            role=r.role,
            specialty=r.specialty,
            description=r.description,
            config=r.config,
            version=r.version,
            published=r.published,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.post("/agents", response_model=Agent, status_code=201, dependencies=[Depends(require_admin)])
async def create_agent(payload: AgentCreate, session: AsyncSession = Depends(get_session)) -> Agent:
    agent = Agent(**payload.model_dump())
    row = AgentORM(**agent.model_dump())
    session.add(row)
    await session.commit()
    return agent


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, session: AsyncSession = Depends(get_session)) -> Agent:
    row = await session.get(AgentORM, agent_id)
    if not row:
        raise HTTPException(404, "agent not found")
    return Agent(**row.model_dump())


@router.put("/agents/{agent_id}", response_model=Agent, dependencies=[Depends(require_admin)])
async def update_agent(agent_id: str, payload: AgentUpdate, session: AsyncSession = Depends(get_session)) -> Agent:
    row = await session.get(AgentORM, agent_id)
    if not row:
        raise HTTPException(404, "agent not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = time.time()
    await session.commit()
    return Agent(**row.model_dump())


@router.post("/agents/{agent_id}/publish", response_model=Agent, dependencies=[Depends(require_admin)])
async def publish_agent(agent_id: str, session: AsyncSession = Depends(get_session)) -> Agent:
    row = await session.get(AgentORM, agent_id)
    if not row:
        raise HTTPException(404, "agent not found")
    row.published = True
    row.version += 1
    row.updated_at = time.time()
    await session.commit()
    return Agent(**row.model_dump())


@router.delete("/agents/{agent_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_agent(agent_id: str, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(AgentORM, agent_id)
    if row:
        await session.delete(row)
        await session.commit()
    return None


# ---------------- Swarms ----------------


@router.get("/swarms", response_model=List[Swarm])
async def list_swarms(session: AsyncSession = Depends(get_session)) -> List[Swarm]:
    res = await session.execute(select(SwarmORM))
    rows = res.scalars().all()
    return [
        Swarm(
            id=r.id,
            name=r.name,
            description=r.description,
            agent_ids=r.agent_ids,
            template=r.template,
            version=r.version,
            published=r.published,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.post("/swarms", response_model=Swarm, status_code=201, dependencies=[Depends(require_admin)])
async def create_swarm(payload: SwarmCreate, session: AsyncSession = Depends(get_session)) -> Swarm:
    swarm = Swarm(**payload.model_dump())
    row = SwarmORM(**swarm.model_dump())
    session.add(row)
    await session.commit()
    return swarm


@router.get("/swarms/{swarm_id}", response_model=Swarm)
async def get_swarm(swarm_id: str, session: AsyncSession = Depends(get_session)) -> Swarm:
    row = await session.get(SwarmORM, swarm_id)
    if not row:
        raise HTTPException(404, "swarm not found")
    return Swarm(**row.model_dump())


@router.put("/swarms/{swarm_id}", response_model=Swarm, dependencies=[Depends(require_admin)])
async def update_swarm(swarm_id: str, payload: SwarmUpdate, session: AsyncSession = Depends(get_session)) -> Swarm:
    row = await session.get(SwarmORM, swarm_id)
    if not row:
        raise HTTPException(404, "swarm not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = time.time()
    await session.commit()
    return Swarm(**row.model_dump())


@router.post("/swarms/{swarm_id}/publish", response_model=Swarm, dependencies=[Depends(require_admin)])
async def publish_swarm(swarm_id: str, session: AsyncSession = Depends(get_session)) -> Swarm:
    row = await session.get(SwarmORM, swarm_id)
    if not row:
        raise HTTPException(404, "swarm not found")
    row.published = True
    row.version += 1
    row.updated_at = time.time()
    await session.commit()
    return Swarm(**row.model_dump())


@router.delete("/swarms/{swarm_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_swarm(swarm_id: str, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(SwarmORM, swarm_id)
    if row:
        await session.delete(row)
        await session.commit()
    return None
