import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, validator
class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    text: str = Field(..., min_length=1, max_length=8192, description="Text to embed")
    model: str = Field(
        default="text-embedding-ada-002", description="Embedding model to use"
    )
    max_tokens: int = Field(
        default=150, ge=1, le=8192, description="Maximum tokens to process"
    )
    @validator("text")
    def validate_text_content(cls, v):
        if not v or v.isspace():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()
class MemoryStoreRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    content: str = Field(
        ..., min_length=1, max_length=65536, description="Content to store"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Associated metadata"
    )
    tags: Optional[list[str]] = Field(None, max_items=20, description="Content tags")
    source: Optional[str] = Field(None, max_length=255, description="Content source")
    priority: Optional[int] = Field(
        default=0, ge=0, le=10, description="Storage priority"
    )
    @validator("content")
    def validate_content(cls, v):
        if not v or v.isspace():
            raise ValueError("Content cannot be empty")
        return v.strip()
    @validator("tags")
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                    raise ValueError(f"Invalid tag format: {tag}")
        return v
class MemorySearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    query: str = Field(..., min_length=1, max_length=1024, description="Search query")
    filters: dict[str, Any] = Field(default_factory=dict, description="Search filters")
    top_k: int = Field(
        default=5, ge=1, le=100, description="Number of results to return"
    )
    similarity_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )
    search_type: str = Field(
        default="semantic", description="Type of search to perform"
    )
    @validator("query")
    def validate_query(cls, v):
        if not v or v.isspace():
            raise ValueError("Query cannot be empty")
        return v.strip()
    @validator("search_type")
    def validate_search_type(cls, v):
        allowed_types = ["semantic", "keyword", "hybrid"]
        if v not in allowed_types:
            raise ValueError(f"Search type must be one of {allowed_types}")
        return v
class MemoryUpdateRequest(BaseModel):
    memory_id: str
    content: str
    metadata: dict = {}
class MemoryDeleteRequest(BaseModel):
    memory_id: str
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(
        ..., min_length=1, max_length=32768, description="Message content"
    )
    name: Optional[str] = Field(None, max_length=64, description="Message author name")
    @validator("content")
    def validate_content(cls, v):
        if not v or v.isspace():
            raise ValueError("Message content cannot be empty")
        return v.strip()
class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    model: str = Field(..., min_length=1, description="Model identifier")
    messages: list[ChatMessage] = Field(
        ..., min_items=1, max_items=100, description="Conversation messages"
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=1000, ge=1, le=32768, description="Maximum tokens to generate"
    )
    stream: Optional[bool] = Field(
        default=False, description="Enable streaming response"
    )
    top_p: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="Presence penalty"
    )
    @validator("messages")
    def validate_messages_structure(cls, v):
        if not v:
            raise ValueError("At least one message is required")
        # Ensure conversation starts with system or user message
        if v[0].role not in [MessageRole.SYSTEM, MessageRole.USER]:
            raise ValueError("Conversation must start with system or user message")
        # Validate message alternation (basic check)
        for i in range(1, len(v)):
            if v[i].role == v[i - 1].role and v[i].role != MessageRole.SYSTEM:
                # Allow multiple system messages at the start, but not consecutive user/assistant
                if v[i].role in [MessageRole.USER, MessageRole.ASSISTANT]:
                    pass  # Allow for now, but could be stricter
        return v
class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
class SwarmResponse(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    content: str = Field(..., min_length=1, description="Response content")
    status: ExecutionStatus = Field(
        default=ExecutionStatus.SUCCESS, description="Execution status"
    )
    swarm_type: Optional[str] = Field(
        None, max_length=100, description="Type of swarm used"
    )
    execution_time: Optional[float] = Field(
        None, ge=0, description="Execution time in seconds"
    )
    agent_count: Optional[int] = Field(
        None, ge=1, le=100, description="Number of agents involved"
    )
    model_used: Optional[str] = Field(
        None, description="Model that generated the response"
    )
    token_usage: Optional[dict[str, int]] = Field(
        None, description="Token usage statistics"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    @validator("content")
    def validate_content(cls, v):
        if not v or v.isspace():
            raise ValueError("Response content cannot be empty")
        return v.strip()
