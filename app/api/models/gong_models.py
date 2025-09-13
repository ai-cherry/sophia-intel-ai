from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GongCall(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    participants: List[Dict[str, Any]] = []
    sentiment: Optional[str] = None


class GongCallsResponse(BaseModel):
    configured: bool
    calls: List[GongCall] = []
    error: Optional[str] = None


class GongClientHealth(BaseModel):
    generated_at: str
    window_days: int
    accounts: List[Dict[str, Any]] = []
    notes: List[str] = []

