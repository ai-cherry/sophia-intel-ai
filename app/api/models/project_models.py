from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceStatus(BaseModel):
    configured: bool
    details: Optional[str] = None


class IntegrationStatus(BaseModel):
    asana: SourceStatus
    linear: SourceStatus
    slack: SourceStatus
    airtable: SourceStatus


class ProjectItem(BaseModel):
    name: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = Field(default="active")
    risk: Optional[str] = None
    due_date: Optional[str] = None
    is_overdue: Optional[bool] = None
    source: str


class ProjectsOverview(BaseModel):
    generated_at: str
    window: Dict[str, str]
    sources: IntegrationStatus
    major_projects: List[ProjectItem] = []
    blockages: List[Dict[str, Any]] = []
    communication_issues: List[Dict[str, Any]] = []
    departments_scorecard: List[Dict[str, Any]] = []
    notes: List[str] = []


class ProjectsSyncStatus(BaseModel):
    checked_at: str
    sources: IntegrationStatus

