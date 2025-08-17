"""
Chat Domain Models - Unified data models for all chat functionality
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Unified chat message model"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Unified chat request model with all feature flags"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    # Backend selection
    use_swarm: Optional[bool] = Field(False, description="Force use of Swarm system")
    backend_preference: Optional[str] = Field(None, description="Preferred backend: orchestrator, swarm, auto")
    
    # Feature flags
    web_access: Optional[bool] = Field(False, description="Enable web research")
    deep_research: Optional[bool] = Field(False, description="Enable deep research mode")
    training: Optional[bool] = Field(False, description="Training mode")
    streaming: Optional[bool] = Field(True, description="Enable streaming responses")
    
    # Persona and voice
    persona_enabled: Optional[bool] = Field(False, description="Enable persona enhancement")
    voice_enabled: Optional[bool] = Field(False, description="Enable voice output")
    voice_id: Optional[str] = Field(None, description="ElevenLabs voice ID")
    
    # Research configuration
    research_strategy: Optional[str] = Field("auto", description="Research provider: auto, tavily, serp, news")
    research_depth: Optional[str] = Field("standard", description="Research depth: quick, standard, deep, comprehensive")
    
    # Model configuration
    model: Optional[str] = Field("claude-3-5-sonnet-20241022", description="AI model to use")
    temperature: Optional[float] = Field(0.7, description="Response creativity")
    max_tokens: Optional[int] = Field(4000, description="Maximum response tokens")
    
    # Context
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Unified chat response model"""
    message: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session identifier")
    backend_used: str = Field(..., description="Backend that processed the request")
    
    # Response metadata
    response_time: float = Field(..., description="Response time in seconds")
    token_count: Optional[int] = Field(None, description="Response token count")
    model_used: str = Field(..., description="AI model used")
    
    # Feature results
    research_results: Optional[Dict[str, Any]] = Field(None, description="Web research results")
    persona_applied: Optional[bool] = Field(False, description="Whether persona was applied")
    voice_url: Optional[str] = Field(None, description="Generated voice audio URL")
    
    # Context and memory
    memory_updated: Optional[bool] = Field(False, description="Whether memory was updated")
    context_summary: Optional[str] = Field(None, description="Context summary for long conversations")
    
    # Analytics
    confidence_score: Optional[float] = Field(None, description="Response confidence")
    routing_reason: Optional[str] = Field(None, description="Why this backend was selected")
    
    # Streaming support
    is_streaming: Optional[bool] = Field(False, description="Whether response is streaming")
    stream_id: Optional[str] = Field(None, description="Stream identifier for partial responses")


class StreamingChatChunk(BaseModel):
    """Individual chunk in a streaming response"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    stream_id: str = Field(..., description="Stream identifier")
    content: str = Field(..., description="Chunk content")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """Chat session model for memory management"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Session configuration
    default_backend: Optional[str] = Field("auto", description="Default backend preference")
    persona_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    voice_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Session analytics
    message_count: int = Field(0, description="Total messages in session")
    backend_usage: Dict[str, int] = Field(default_factory=dict)
    feature_usage: Dict[str, int] = Field(default_factory=dict)
    
    # Context management
    context_window_size: int = Field(8000, description="Context window size in tokens")
    auto_summarize_threshold: int = Field(50, description="Auto-summarize after N messages")


class BackendAnalysis(BaseModel):
    """Analysis result for backend selection"""
    recommended_backend: str = Field(..., description="Recommended backend")
    confidence: float = Field(..., description="Confidence score 0-1")
    reasoning: str = Field(..., description="Explanation for recommendation")
    
    # Analysis factors
    complexity_score: float = Field(..., description="Message complexity 0-1")
    keyword_matches: Dict[str, List[str]] = Field(default_factory=dict)
    historical_performance: Optional[Dict[str, float]] = Field(None)
    
    # Alternative options
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)

