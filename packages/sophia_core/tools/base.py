"""
Base Tool Interfaces

Defines abstract base classes and data structures for AI agent tools,
including parameter validation, execution context, and result handling.
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Dict, List, Optional, Any, Union, Callable, Type, 
    TypeVar, Generic, get_type_hints, get_origin, get_args
)
from datetime import datetime
from uuid import uuid4
import json

from pydantic import BaseModel, Field, validator, create_model
from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ToolParameterType(str, Enum):
    """Supported tool parameter types."""
    STRING = "string"
    INTEGER = "integer" 
    FLOAT = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


class ToolParameter(BaseModel):
    """
    Defines a tool parameter with validation rules.
    """
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    
    # Validation constraints
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    
    # Array/object specific
    items: Optional['ToolParameter'] = None  # For arrays
    properties: Optional[Dict[str, 'ToolParameter']] = None  # For objects
    
    @validator('default')
    def validate_default(cls, v, values):
        """Validate default value matches parameter type."""
        if v is None:
            return v
        
        param_type = values.get('type')
        if param_type == ToolParameterType.STRING and not isinstance(v, str):
            raise ValueError("Default value must be string")
        elif param_type == ToolParameterType.INTEGER and not isinstance(v, int):
            raise ValueError("Default value must be integer")
        elif param_type == ToolParameterType.FLOAT and not isinstance(v, (int, float)):
            raise ValueError("Default value must be number")
        elif param_type == ToolParameterType.BOOLEAN and not isinstance(v, bool):
            raise ValueError("Default value must be boolean")
        elif param_type == ToolParameterType.ARRAY and not isinstance(v, list):
            raise ValueError("Default value must be array")
        elif param_type == ToolParameterType.OBJECT and not isinstance(v, dict):
            raise ValueError("Default value must be object")
        
        return v
    
    def validate_value(self, value: Any) -> Any:
        """
        Validate a parameter value against constraints.
        
        Args:
            value: Value to validate
            
        Returns:
            Any: Validated value
            
        Raises:
            ValueError: If validation fails
        """
        if value is None:
            if self.required:
                raise ValueError(f"Parameter '{self.name}' is required")
            return self.default
        
        # Type validation
        if self.type == ToolParameterType.STRING:
            if not isinstance(value, str):
                value = str(value)
            
            if self.min_length and len(value) < self.min_length:
                raise ValueError(f"String too short (minimum {self.min_length})")
            if self.max_length and len(value) > self.max_length:
                raise ValueError(f"String too long (maximum {self.max_length})")
            
            if self.pattern:
                import re
                if not re.match(self.pattern, value):
                    raise ValueError(f"String does not match pattern: {self.pattern}")
        
        elif self.type == ToolParameterType.INTEGER:
            if not isinstance(value, int):
                value = int(value)
            
            if self.min_value and value < self.min_value:
                raise ValueError(f"Value too small (minimum {self.min_value})")
            if self.max_value and value > self.max_value:
                raise ValueError(f"Value too large (maximum {self.max_value})")
        
        elif self.type == ToolParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                value = float(value)
            
            if self.min_value and value < self.min_value:
                raise ValueError(f"Value too small (minimum {self.min_value})")
            if self.max_value and value > self.max_value:
                raise ValueError(f"Value too large (maximum {self.max_value})")
        
        elif self.type == ToolParameterType.BOOLEAN:
            if not isinstance(value, bool):
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    value = bool(value)
        
        elif self.type == ToolParameterType.ARRAY:
            if not isinstance(value, list):
                raise ValueError("Value must be an array")
            
            if self.min_length and len(value) < self.min_length:
                raise ValueError(f"Array too short (minimum {self.min_length})")
            if self.max_length and len(value) > self.max_length:
                raise ValueError(f"Array too long (maximum {self.max_length})")
            
            # Validate array items if item schema provided
            if self.items:
                validated_items = []
                for i, item in enumerate(value):
                    try:
                        validated_items.append(self.items.validate_value(item))
                    except ValueError as e:
                        raise ValueError(f"Array item {i}: {e}")
                value = validated_items
        
        elif self.type == ToolParameterType.OBJECT:
            if not isinstance(value, dict):
                raise ValueError("Value must be an object")
            
            # Validate object properties if schema provided
            if self.properties:
                validated_obj = {}
                for key, prop_schema in self.properties.items():
                    prop_value = value.get(key)
                    try:
                        validated_obj[key] = prop_schema.validate_value(prop_value)
                    except ValueError as e:
                        raise ValueError(f"Property '{key}': {e}")
                
                # Include any additional properties not in schema
                for key, val in value.items():
                    if key not in validated_obj:
                        validated_obj[key] = val
                
                value = validated_obj
        
        # Enum validation
        if self.enum_values and value not in self.enum_values:
            raise ValueError(f"Value must be one of: {self.enum_values}")
        
        return value


class ToolSchema(BaseModel):
    """
    Complete tool schema definition.
    """
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    return_type: Optional[str] = None
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Convert to OpenAI function calling schema format.
        
        Returns:
            Dict[str, Any]: OpenAI compatible schema
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            param_schema = {
                "type": param.type.value,
                "description": param.description
            }
            
            # Add constraints
            if param.min_value is not None:
                param_schema["minimum"] = param.min_value
            if param.max_value is not None:
                param_schema["maximum"] = param.max_value
            if param.min_length is not None:
                param_schema["minLength"] = param.min_length
            if param.max_length is not None:
                param_schema["maxLength"] = param.max_length
            if param.pattern:
                param_schema["pattern"] = param.pattern
            if param.enum_values:
                param_schema["enum"] = param.enum_values
            
            # Array items
            if param.items and param.type == ToolParameterType.ARRAY:
                param_schema["items"] = {
                    "type": param.items.type.value,
                    "description": param.items.description
                }
            
            # Object properties
            if param.properties and param.type == ToolParameterType.OBJECT:
                param_schema["properties"] = {}
                param_schema["required"] = []
                
                for prop_name, prop_param in param.properties.items():
                    param_schema["properties"][prop_name] = {
                        "type": prop_param.type.value,
                        "description": prop_param.description
                    }
                    
                    if prop_param.required:
                        param_schema["required"].append(prop_name)
            
            properties[param.name] = param_schema
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            Dict[str, Any]: Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        validated = {}
        
        for param in self.parameters:
            value = parameters.get(param.name)
            try:
                validated[param.name] = param.validate_value(value)
            except ValueError as e:
                raise ValueError(f"Parameter '{param.name}': {e}")
        
        # Check for unexpected parameters
        unexpected = set(parameters.keys()) - {p.name for p in self.parameters}
        if unexpected:
            logger.warning(f"Unexpected parameters for {self.name}: {unexpected}")
        
        return validated


class ToolExecutionContext(BaseModel):
    """
    Context information for tool execution.
    """
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Execution environment
    environment: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    
    # Timing information
    started_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_seconds: Optional[float] = None
    
    # Memory access
    memory_access: bool = True
    memory_types: List[str] = Field(default_factory=list)
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        return permission in self.permissions
    
    def get_remaining_time(self) -> Optional[float]:
        """Get remaining execution time in seconds."""
        if self.timeout_seconds is None:
            return None
        
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return max(0, self.timeout_seconds - elapsed)
    
    def is_expired(self) -> bool:
        """Check if execution context has expired."""
        remaining = self.get_remaining_time()
        return remaining is not None and remaining <= 0


class ToolResult(BaseModel):
    """
    Result from tool execution.
    """
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Metadata
    execution_time: float = 0.0
    memory_used: int = 0
    tokens_used: int = 0
    
    # Tool-specific metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def success_result(
        cls,
        result: Any,
        execution_time: float = 0.0,
        **metadata
    ) -> 'ToolResult':
        """Create successful result."""
        return cls(
            success=True,
            result=result,
            execution_time=execution_time,
            metadata=metadata
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        execution_time: float = 0.0,
        **metadata
    ) -> 'ToolResult':
        """Create error result."""
        return cls(
            success=False,
            error=error,
            execution_time=execution_time,
            metadata=metadata
        )
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps({
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }, default=str)


# Exception classes
class ToolError(Exception):
    """Base class for tool errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool parameter validation fails."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    """
    
    def __init__(self, schema: ToolSchema):
        """
        Initialize tool with schema.
        
        Args:
            schema: Tool schema definition
        """
        self.schema = schema
        self._execution_count = 0
        self._total_execution_time = 0.0
        
        logger.info(f"Initialized tool: {schema.name}")
    
    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Tool parameters
            context: Execution context
            
        Returns:
            ToolResult: Execution result
            
        Raises:
            ToolError: If execution fails
        """
        pass
    
    async def validate_and_execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Validate parameters and execute tool.
        
        Args:
            parameters: Tool parameters
            context: Execution context
            
        Returns:
            ToolResult: Execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate parameters
            validated_params = self.schema.validate_parameters(parameters)
            
            # Check execution timeout
            if context.is_expired():
                return ToolResult.error_result(
                    "Tool execution timed out before starting",
                    execution_time=0.0
                )
            
            # Execute tool
            result = await self.execute(validated_params, context)
            
            # Update statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self._execution_count += 1
            self._total_execution_time += execution_time
            
            logger.debug(f"Tool {self.schema.name} executed in {execution_time:.3f}s")
            return result
            
        except ToolValidationError as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Tool {self.schema.name} validation error: {e}")
            return ToolResult.error_result(
                f"Parameter validation failed: {e}",
                execution_time=execution_time
            )
            
        except ToolExecutionError as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Tool {self.schema.name} execution error: {e}")
            return ToolResult.error_result(
                f"Execution failed: {e}",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Tool {self.schema.name} unexpected error: {e}")
            return ToolResult.error_result(
                f"Unexpected error: {e}",
                execution_time=execution_time
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        avg_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0 else 0.0
        )
        
        return {
            "name": self.schema.name,
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_time,
            "version": self.schema.version
        }
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return self.schema.to_openai_schema()


class AsyncTool(BaseTool):
    """
    Base class for async tools that run asynchronously.
    """
    
    @abstractmethod
    async def _execute_async(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> Any:
        """
        Async implementation of tool execution.
        
        Args:
            parameters: Validated parameters
            context: Execution context
            
        Returns:
            Any: Tool result
        """
        pass
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute async tool with timeout handling."""
        try:
            # Set up timeout
            timeout = context.get_remaining_time()
            
            if timeout and timeout > 0:
                result = await asyncio.wait_for(
                    self._execute_async(parameters, context),
                    timeout=timeout
                )
            else:
                result = await self._execute_async(parameters, context)
            
            return ToolResult.success_result(result)
            
        except asyncio.TimeoutError:
            raise ToolExecutionError("Tool execution timed out")
        except Exception as e:
            raise ToolExecutionError(f"Async execution failed: {e}")


class SyncTool(BaseTool):
    """
    Base class for synchronous tools that run in thread pool.
    """
    
    @abstractmethod
    def _execute_sync(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> Any:
        """
        Synchronous implementation of tool execution.
        
        Args:
            parameters: Validated parameters
            context: Execution context
            
        Returns:
            Any: Tool result
        """
        pass
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute sync tool in thread pool."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._execute_sync(parameters, context)
            )
            
            return ToolResult.success_result(result)
            
        except Exception as e:
            raise ToolExecutionError(f"Sync execution failed: {e}")


class ToolRegistry:
    """
    Registry for managing and discovering tools.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.info("Initialized tool registry")
    
    def register(
        self,
        tool: BaseTool,
        category: Optional[str] = None,
        replace_existing: bool = False
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool to register
            category: Optional category for organization
            replace_existing: Whether to replace existing tool with same name
            
        Raises:
            ValueError: If tool name already exists and replace_existing is False
        """
        name = tool.schema.name
        
        if name in self._tools and not replace_existing:
            raise ValueError(f"Tool '{name}' already registered")
        
        self._tools[name] = tool
        
        if category:
            if category not in self._categories:
                self._categories[category] = []
            
            if name not in self._categories[category]:
                self._categories[category].append(name)
        
        logger.info(f"Registered tool '{name}' in category '{category or 'default'}'")
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
            
        Returns:
            bool: True if tool was unregistered
        """
        if name in self._tools:
            del self._tools[name]
            
            # Remove from categories
            for category, tool_names in self._categories.items():
                if name in tool_names:
                    tool_names.remove(name)
            
            logger.info(f"Unregistered tool '{name}'")
            return True
        
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[BaseTool]: Tool if found
        """
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List available tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List[str]: Tool names
        """
        if category:
            return self._categories.get(category, [])
        
        return list(self._tools.keys())
    
    def get_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get OpenAI schemas for tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List[Dict[str, Any]]: OpenAI compatible schemas
        """
        tool_names = self.list_tools(category)
        schemas = []
        
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.to_openai_schema())
        
        return schemas
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "categories": list(self._categories.keys()),
            "tools_by_category": {
                cat: len(tools) for cat, tools in self._categories.items()
            },
            "tool_stats": {
                name: tool.get_statistics()
                for name, tool in self._tools.items()
            }
        }
    
    async def execute_tool(
        self,
        name: str,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            parameters: Tool parameters
            context: Execution context
            
        Returns:
            ToolResult: Execution result
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        return await tool.validate_and_execute(parameters, context)


# Update forward references
ToolParameter.model_rebuild()