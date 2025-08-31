"""
Plugin Architecture for Sophia Intel AI
Base classes and interfaces for dynamic plugin loading.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================
# Plugin Metadata
# ============================================

class PluginMetadata(BaseModel):
    """Metadata for plugin identification and configuration."""
    name: str = Field(..., description="Unique plugin name")
    version: str = Field(..., description="Semantic version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    entry_points: List[str] = Field(default_factory=list, description="Entry points")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================
# Base Plugin Classes
# ============================================

class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self._initialized = False
        self._config: Dict[str, Any] = {}
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self._config = config
        self._initialized = True
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True  # Override in subclasses

class SwarmPlugin(Plugin):
    """Base class for swarm plugins."""
    
    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """Execute a swarm task.
        
        Args:
            task: Task description
            context: Execution context
            stream: Whether to stream results
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of agents in the swarm.
        
        Returns:
            List of agent configurations
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get swarm capabilities.
        
        Returns:
            List of capability strings
        """
        pass

class ToolPlugin(Plugin):
    """Base class for tool plugins."""
    
    @abstractmethod
    async def execute(
        self,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute a tool operation.
        
        Args:
            operation: Operation to perform
            parameters: Operation parameters
            
        Returns:
            Operation result
        """
        pass
    
    @abstractmethod
    def get_operations(self) -> List[str]:
        """Get available operations.
        
        Returns:
            List of operation names
        """
        pass

class MemoryPlugin(Plugin):
    """Base class for memory plugins."""
    
    @abstractmethod
    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store data in memory.
        
        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        key: str
    ) -> Optional[Any]:
        """Retrieve data from memory.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memory.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Search results
        """
        pass

# ============================================
# Plugin Interfaces
# ============================================

class IPluginValidator:
    """Interface for plugin validation."""
    
    def validate_metadata(self, metadata: PluginMetadata) -> bool:
        """Validate plugin metadata."""
        required_fields = ['name', 'version', 'description', 'author']
        for field in required_fields:
            if not getattr(metadata, field, None):
                return False
        return True
    
    def validate_dependencies(self, dependencies: List[str]) -> bool:
        """Validate plugin dependencies."""
        # Check if all dependencies are available
        return True  # Implement actual check
    
    def validate_interface(self, plugin: Plugin) -> bool:
        """Validate plugin implements required interface."""
        required_methods = {
            SwarmPlugin: ['execute_task', 'get_agents', 'get_capabilities'],
            ToolPlugin: ['execute', 'get_operations'],
            MemoryPlugin: ['store', 'retrieve', 'search']
        }
        
        plugin_type = type(plugin).__bases__[0]
        if plugin_type in required_methods:
            for method in required_methods[plugin_type]:
                if not hasattr(plugin, method):
                    return False
        return True

# ============================================
# Plugin Events
# ============================================

class PluginEvent(BaseModel):
    """Event emitted by plugins."""
    plugin_name: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)

class PluginEventHandler:
    """Handle plugin events."""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = {}
    
    def register_handler(
        self,
        event_type: str,
        handler: callable
    ) -> None:
        """Register event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def emit(
        self,
        event: PluginEvent
    ) -> None:
        """Emit plugin event.
        
        Args:
            event: Event to emit
        """
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event.event_type}: {e}")

# ============================================
# Plugin Hooks
# ============================================

class PluginHooks:
    """Hooks for plugin lifecycle."""
    
    @staticmethod
    async def on_load(plugin: Plugin) -> None:
        """Called when plugin is loaded."""
        logger.info(f"Plugin {plugin.metadata.name} loaded")
    
    @staticmethod
    async def on_initialize(plugin: Plugin) -> None:
        """Called when plugin is initialized."""
        logger.info(f"Plugin {plugin.metadata.name} initialized")
    
    @staticmethod
    async def on_execute(plugin: Plugin, task: str) -> None:
        """Called before plugin executes task."""
        logger.debug(f"Plugin {plugin.metadata.name} executing: {task}")
    
    @staticmethod
    async def on_cleanup(plugin: Plugin) -> None:
        """Called when plugin is cleaned up."""
        logger.info(f"Plugin {plugin.metadata.name} cleaned up")
    
    @staticmethod
    async def on_error(plugin: Plugin, error: Exception) -> None:
        """Called when plugin encounters error."""
        logger.error(f"Plugin {plugin.metadata.name} error: {error}")

# ============================================
# Export
# ============================================

__all__ = [
    "Plugin",
    "SwarmPlugin",
    "ToolPlugin",
    "MemoryPlugin",
    "PluginMetadata",
    "IPluginValidator",
    "PluginEvent",
    "PluginEventHandler",
    "PluginHooks"
]