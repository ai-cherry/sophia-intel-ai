"""
Gong Schema Definitions

This module contains Pydantic models for Gong API data structures.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class MCPError(Exception):
    """
    Exception raised for MCP-related errors.

    Attributes:
        error_type: The type of error (e.g., "upstream_error", "request_error")
        message: The error message
        status_code: The HTTP status code
    """

    def __init__(self, error_type: str, message: str, status_code: int = 500):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class Participant(BaseModel):
    """Model for a call participant."""

    id: str
    name: str
    email: Optional[str] = None
    role: str = Field(..., description="Role such as 'speaker', 'listener'")
    company: Optional[str] = None


class TranscriptSegment(BaseModel):
    """Model for a segment of a call transcript."""

    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    speaker_id: str
    text: str


class CallTranscript(BaseModel):
    """Model for a complete call transcript."""

    call_id: str
    title: Optional[str] = None
    date: datetime
    duration: float = Field(..., description="Call duration in seconds")
    participants: List[Participant]
    segments: List[TranscriptSegment]


class CallInsight(BaseModel):
    """Model for an AI-generated insight from a call."""

    id: str
    call_id: str
    category: str = Field(...,
                          description="Category such as 'objection', 'question'")
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    segment_ids: List[str] = Field(default_factory=list)
    timestamp: float = Field(..., description="Timestamp in seconds")


class CallTopic(BaseModel):
    """Model for a detected topic in a call."""

    name: str
    importance: float = Field(..., ge=0.0, le=1.0)
    segments: List[int] = Field(default_factory=list)


class CallSummary(BaseModel):
    """Model for a call summary."""

    call_id: str
    title: Optional[str] = None
    date: datetime
    duration: float
    summary_text: str
    topics: List[CallTopic] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)


class PaginationMeta(BaseModel):
    """Metadata for paginated responses."""

    has_more: bool = False
    next_cursor: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""

    data: List[Any]
    meta: PaginationMeta
