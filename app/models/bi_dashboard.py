"""Pydantic models for the Pay Ready BI dashboard surface."""
from __future__ import annotations
from typing import Literal
import re
from pydantic import BaseModel, Field, validator

FlowwiseStatus = Literal["online", "degraded", "offline"]
AgnoHealth = Literal["green", "yellow", "red"]
TrendDirection = Literal["up", "down", "flat"]


class BusinessMetric(BaseModel):
    """Normalized KPI representation surfaced on the dashboard."""

    id: str = Field(..., description="Unique metric identifier")
    label: str = Field(..., description="Human readable label")
    value: float = Field(..., description="Current metric value")
    unit: str | None = Field(default=None, description="Unit suffix displayed next to the metric")
    trend: TrendDirection | None = Field(default=None, description="Directional trend versus previous period")
    target: float | None = Field(default=None, description="Goal target for the metric")
    tags: dict[str, str] = Field(default_factory=dict, description="Canonical meta tags applied to the metric")


class FlowwiseAgent(BaseModel):
    """Flowwise agent entry respecting canonical naming requirements."""

    id: str = Field(..., description="Canonical Flowwise agent id (FLW_[DEPT]_[FUNCTION])")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Short summary of the agent purpose")
    owner: str = Field(..., description="Team owner")
    tags: list[str] = Field(default_factory=list, description="Normalized taxonomy tags")
    version: str = Field(..., min_length=1, description="Agent version string")
    endpoint: str = Field(..., description="Flowwise invocation endpoint")

    @validator("id")
    def validate_id(cls, value: str) -> str:  # noqa: D417
        pattern = re.compile(r'^FLW_[A-Z]{2,}_[A-Z0-9_]+$')
        if not pattern.match(value):
            raise ValueError('Flowwise agents must follow FLW_[DEPT]_[FUNCTION] convention')
        return value


class FlowwiseFactory(BaseModel):
    """Flowwise factory summary for Agent Factory tab."""

    id: str = Field(..., description="Factory identifier")
    department: str = Field(..., description="Owning department")
    function: str = Field(..., description="Business function")
    status: FlowwiseStatus = Field(..., description="Operational status")
    agents: list[FlowwiseAgent] = Field(default_factory=list, description="Published Flowwise agents")


class AgnoAgent(BaseModel):
    """Agno v2 agent entry with canonical naming."""

    id: str = Field(..., description="Canonical Agno agent id (AGN_[PURPOSE]_vX)")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="Agent summary")
    owner: str = Field(..., description="Maintainer or squad")
    tags: list[str] = Field(default_factory=list, description="Tag metadata")
    version: str = Field(..., description="Current version")

    @validator("id")
    def validate_id(cls, value: str) -> str:  # noqa: D417
        pattern = re.compile(r'^AGN_[A-Z0-9]+_v[0-9]+$')
        if not pattern.match(value):
            raise ValueError('Agno agents must follow AGN_[PURPOSE]_vVERSION convention')
        return value


class AgnoWorkspace(BaseModel):
    """Agno v2 workspace details for Developer Studio tab."""

    id: str = Field(..., description="Workspace id")
    purpose: str = Field(..., description="Business purpose")
    version: str = Field(..., description="Agno runtime version")
    maintainer: str = Field(..., description="Primary contact")
    pipelines: int = Field(..., ge=0, description="Active pipelines count")
    health: AgnoHealth = Field(..., description="Operational health status")
    agents: list[AgnoAgent] = Field(default_factory=list, description="Published agents")
