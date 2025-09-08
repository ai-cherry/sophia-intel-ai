"""
Base Model Interfaces

Defines abstract base classes and data structures for AI language models,
including message handling, tool calling, and response processing.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Dict, List, Optional, Any, Union, AsyncGenerator, 
    Callable, Type, Generic, TypeVar
)
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel as PydanticBaseModel, Field, validator

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MessageRole(str, Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"  # Legacy support


class Message(PydanticBaseModel):
    """
    Represents a single message in a conversation.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: Optional[str] = None
    name: Optional[str] = None  # For function/tool messages
    tool_calls: Optional[List['ToolCall']] = None
    tool_call_id: Optional[str] = None  # For tool response messages
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('tool_calls', pre=True)
    def validate_tool_calls(cls, v, values):
        """Ensure tool_calls is only present for assistant messages."""
        role = values.get('role')
        if v is not None and role != MessageRole.ASSISTANT:
            raise ValueError("tool_calls can only be present for assistant messages")
        return v
    
    @validator('tool_call_id', pre=True)
    def validate_tool_call_id(cls, v, values):
        """Ensure tool_call_id is only present for tool messages."""
        role = values.get('role')
        if v is not None and role != MessageRole.TOOL:
            raise ValueError("tool_call_id can only be present for tool messages")
        return v
    
    class Config:
        validate_assignment = True
        use_enum_values = True


class ToolCall(PydanticBaseModel):
    """
    Represents a tool/function call made by the model.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str = Field(default="function")
    function: Dict[str, Any]  # Contains 'name' and 'arguments'
    
    @property
    def name(self) -> str:
        """Get the function name."""
        return self.function.get('name', '')
    
    @property
    def arguments(self) -> Dict[str, Any]:
        """Get parsed function arguments."""
        import json
        args_str = self.function.get('arguments', '{}')
        try:
            return json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse tool call arguments: {args_str}")
            return {}


class ToolResult(PydanticBaseModel):
    """
    Represents the result of a tool/function call.
    """
    tool_call_id: str
    name: str
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: Optional[float] = None  # seconds


class ModelUsage(PydanticBaseModel):
    """
    Token usage information from model response.
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @validator('total_tokens', always=True)
    def calculate_total_tokens(cls, v, values):
        """Auto-calculate total tokens if not provided."""
        if v == 0:
            return values.get('prompt_tokens', 0) + values.get('completion_tokens', 0)
        return v


class ModelParameters(PydanticBaseModel):
    """
    Parameters for model inference.
    """
    model: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    
    # Provider-specific parameters
    extra_params: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True


class ModelCapabilities(PydanticBaseModel):
    """
    Model capabilities and limitations.
    """
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    supports_system_messages: bool = True
    max_context_length: int = 4096
    max_output_tokens: int = 4096
    supported_formats: List[str] = Field(default_factory=lambda: ["text"])
    
    # Model-specific capabilities
    supports_json_mode: bool = False
    supports_function_calling: bool = False
    supports_parallel_tools: bool = False


class ModelResponse(PydanticBaseModel):
    """
    Response from a language model.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    model: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    usage: Optional[ModelUsage] = None
    response_time: Optional[float] = None  # seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class StreamingResponse(PydanticBaseModel):
    """
    Streaming response chunk from a language model.
    """
    id: str
    model: str
    delta: Dict[str, Any]  # Contains the incremental content
    finish_reason: Optional[str] = None
    usage: Optional[ModelUsage] = None
    
    @property
    def content_delta(self) -> Optional[str]:
        """Get content delta from the chunk."""
        return self.delta.get('content')
    
    @property
    def is_complete(self) -> bool:
        """Check if this is the final chunk."""
        return self.finish_reason is not None


class ConversationHistory(PydanticBaseModel):
    """
    Manages conversation history with message ordering and limits.
    """
    messages: List[Message] = Field(default_factory=list)
    max_messages: Optional[int] = None
    max_tokens: Optional[int] = None
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        
        # Apply message limit
        if self.max_messages and len(self.messages) > self.max_messages:
            # Keep system messages and trim from the middle
            system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]
            
            if len(other_messages) > self.max_messages - len(system_messages):
                keep_count = self.max_messages - len(system_messages)
                other_messages = other_messages[-keep_count:]
            
            self.messages = system_messages + other_messages
    
    def get_messages_for_model(self) -> List[Dict[str, Any]]:
        """
        Get messages formatted for model API.
        
        Returns:
            List[Dict[str, Any]]: Messages in API format
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"tool_calls": [tc.dict() for tc in msg.tool_calls]} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
            }
            for msg in self.messages
        ]
    
    def clear(self) -> None:
        """Clear all messages except system messages."""
        self.messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the last assistant message."""
        for message in reversed(self.messages):
            if message.role == MessageRole.ASSISTANT:
                return message
        return None
    
    def count_tokens(self, tokenizer_func: Optional[Callable[[str], int]] = None) -> int:
        """
        Estimate token count for the conversation.
        
        Args:
            tokenizer_func: Optional function to count tokens
            
        Returns:
            int: Estimated token count
        """
        if tokenizer_func:
            total = 0
            for message in self.messages:
                if message.content:
                    total += tokenizer_func(message.content)
            return total
        else:
            # Simple estimation: ~4 characters per token
            total_chars = sum(len(m.content or "") for m in self.messages)
            return total_chars // 4


class BaseModel(ABC):
    """
    Abstract base class for language model implementations.
    """
    
    def __init__(
        self,
        model_name: str,
        capabilities: Optional[ModelCapabilities] = None,
        **kwargs
    ):
        """
        Initialize the model.
        
        Args:
            model_name: Name/identifier of the model
            capabilities: Model capabilities
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.capabilities = capabilities or ModelCapabilities()
        self._config = kwargs
        logger.info(f"Initialized {self.__class__.__name__} with model {model_name}")
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        parameters: Optional[ModelParameters] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate a response from the model.
        
        Args:
            messages: List of conversation messages
            parameters: Generation parameters
            **kwargs: Additional arguments
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        parameters: Optional[ModelParameters] = None,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """
        Stream responses from the model.
        
        Args:
            messages: List of conversation messages  
            parameters: Generation parameters
            **kwargs: Additional arguments
            
        Yields:
            StreamingResponse: Streaming response chunks
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    async def chat(
        self,
        conversation: ConversationHistory,
        parameters: Optional[ModelParameters] = None,
        **kwargs
    ) -> ModelResponse:
        """
        High-level chat interface using conversation history.
        
        Args:
            conversation: Conversation history
            parameters: Generation parameters
            **kwargs: Additional arguments
            
        Returns:
            ModelResponse: Model response
        """
        messages = conversation.messages
        response = await self.generate(messages, parameters, **kwargs)
        
        # Add assistant response to conversation
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=response.content,
            tool_calls=response.tool_calls,
            metadata={"model_response_id": response.id}
        )
        conversation.add_message(assistant_message)
        
        return response
    
    def validate_parameters(self, parameters: ModelParameters) -> ModelParameters:
        """
        Validate and adjust parameters based on model capabilities.
        
        Args:
            parameters: Input parameters
            
        Returns:
            ModelParameters: Validated parameters
        """
        # Validate max_tokens against model capability
        if parameters.max_tokens:
            max_allowed = self.capabilities.max_output_tokens
            if parameters.max_tokens > max_allowed:
                logger.warning(
                    f"max_tokens {parameters.max_tokens} exceeds model limit {max_allowed}, "
                    f"adjusting to {max_allowed}"
                )
                parameters.max_tokens = max_allowed
        
        # Validate tool support
        if parameters.tools and not self.capabilities.supports_tools:
            logger.warning(f"Model {self.model_name} does not support tools, ignoring tool parameters")
            parameters.tools = None
            parameters.tool_choice = None
        
        return parameters
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get model system information.
        
        Returns:
            Dict[str, Any]: System information
        """
        return {
            "model_name": self.model_name,
            "capabilities": self.capabilities.dict(),
            "class": self.__class__.__name__,
            "config": self._config
        }


# Update forward references
Message.model_rebuild()
ToolCall.model_rebuild()
ModelResponse.model_rebuild()