"""
Persona Domain Models - Voice and personality configuration
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VoiceSettings(BaseModel):
    """ElevenLabs voice configuration"""
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    voice_name: Optional[str] = Field(None, description="Human-readable voice name")
    stability: float = Field(0.5, ge=0.0, le=1.0, description="Voice stability (0-1)")
    similarity_boost: float = Field(0.5, ge=0.0, le=1.0, description="Similarity boost (0-1)")
    style: float = Field(0.0, ge=0.0, le=1.0, description="Style exaggeration (0-1)")
    use_speaker_boost: bool = Field(True, description="Enable speaker boost")
    
    # Advanced settings
    model_id: str = Field("eleven_multilingual_v2", description="ElevenLabs model ID")
    output_format: str = Field("mp3_44100_128", description="Audio output format")
    optimize_streaming_latency: int = Field(0, description="Streaming latency optimization")


class PersonaSettings(BaseModel):
    """Persona enhancement configuration"""
    enabled: bool = Field(False, description="Enable persona enhancement")
    persona_name: str = Field("SOPHIA", description="Persona name")
    
    # Personality traits
    personality_traits: List[str] = Field(
        default=["professional", "intelligent", "helpful", "concise"],
        description="Personality traits to emphasize"
    )
    
    # Communication style
    communication_style: str = Field(
        "professional",
        description="Communication style: professional, casual, technical, creative"
    )
    
    # Response enhancement
    enhance_responses: bool = Field(True, description="Enhance responses with persona")
    add_personality_markers: bool = Field(False, description="Add personality markers to responses")
    
    # Context awareness
    remember_preferences: bool = Field(True, description="Remember user preferences")
    adapt_to_context: bool = Field(True, description="Adapt responses to conversation context")
    
    # Custom prompts
    system_prompt_addition: Optional[str] = Field(
        None, 
        description="Additional system prompt for persona"
    )
    response_prefix: Optional[str] = Field(None, description="Prefix for responses")
    response_suffix: Optional[str] = Field(None, description="Suffix for responses")


class PersonaResponse(BaseModel):
    """Response from persona enhancement"""
    enhanced_response: str = Field(..., description="Enhanced response text")
    original_response: str = Field(..., description="Original response text")
    enhancements_applied: List[str] = Field(default_factory=list, description="List of applied enhancements")
    
    # Persona metadata
    persona_used: str = Field(..., description="Persona name used")
    confidence_score: float = Field(..., description="Enhancement confidence (0-1)")
    processing_time: float = Field(..., description="Enhancement processing time")
    
    # Voice generation
    voice_generated: bool = Field(False, description="Whether voice was generated")
    voice_url: Optional[str] = Field(None, description="Generated voice audio URL")
    voice_duration: Optional[float] = Field(None, description="Voice duration in seconds")


class VoiceGenerationRequest(BaseModel):
    """Request for voice generation"""
    text: str = Field(..., description="Text to convert to speech")
    voice_settings: VoiceSettings = Field(..., description="Voice configuration")
    
    # Generation options
    optimize_for_streaming: bool = Field(False, description="Optimize for streaming")
    previous_text: Optional[str] = Field(None, description="Previous text for context")
    next_text: Optional[str] = Field(None, description="Next text for context")
    
    # Output options
    output_filename: Optional[str] = Field(None, description="Custom output filename")
    return_url: bool = Field(True, description="Return URL instead of binary data")


class VoiceGenerationResponse(BaseModel):
    """Response from voice generation"""
    success: bool = Field(..., description="Generation success status")
    audio_url: Optional[str] = Field(None, description="Generated audio URL")
    audio_data: Optional[bytes] = Field(None, description="Generated audio binary data")
    
    # Metadata
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    file_size: Optional[int] = Field(None, description="Audio file size in bytes")
    format: str = Field(..., description="Audio format")
    
    # Generation details
    characters_processed: int = Field(..., description="Number of characters processed")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="ElevenLabs model used")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_after: Optional[int] = Field(None, description="Retry after seconds if rate limited")


class PersonaProfile(BaseModel):
    """Complete persona profile"""
    profile_id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    
    # Settings
    persona_settings: PersonaSettings = Field(..., description="Persona configuration")
    voice_settings: VoiceSettings = Field(..., description="Voice configuration")
    
    # Usage tracking
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = Field(0, description="Number of times used")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    # Performance metrics
    average_enhancement_time: float = Field(0.0, description="Average enhancement time")
    average_voice_generation_time: float = Field(0.0, description="Average voice generation time")
    success_rate: float = Field(1.0, description="Success rate (0-1)")


class AvailableVoice(BaseModel):
    """Available ElevenLabs voice"""
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    name: str = Field(..., description="Voice name")
    category: str = Field(..., description="Voice category")
    description: Optional[str] = Field(None, description="Voice description")
    
    # Voice characteristics
    gender: Optional[str] = Field(None, description="Voice gender")
    age: Optional[str] = Field(None, description="Voice age range")
    accent: Optional[str] = Field(None, description="Voice accent")
    use_case: Optional[str] = Field(None, description="Recommended use case")
    
    # Technical details
    sample_rate: Optional[int] = Field(None, description="Sample rate")
    available_models: List[str] = Field(default_factory=list, description="Compatible models")
    
    # Preview
    preview_url: Optional[str] = Field(None, description="Voice preview URL")
    is_premium: bool = Field(False, description="Whether voice requires premium subscription")

