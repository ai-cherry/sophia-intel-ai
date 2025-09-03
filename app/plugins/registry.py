"""
Plugin Registry for Dynamic Plugin Loading
Handles discovery, validation, and management of plugins.
"""

import importlib
import importlib.metadata
import inspect
import logging
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Union

from app.plugins.base import (
    IPluginValidator,
    MemoryPlugin,
    Plugin,
    PluginHooks,
    PluginMetadata,
    SwarmPlugin,
    ToolPlugin,
)

logger = logging.getLogger(__name__)

# ============================================
# Plugin Registry
# ============================================

class PluginRegistry:
    """Central registry for managing plugins."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the registry."""
        self._plugins: dict[str, Plugin] = {}
        self._plugin_types: dict[type[Plugin], list[str]] = {
            SwarmPlugin: [],
            ToolPlugin: [],
            MemoryPlugin: []
        }
        self._validator = IPluginValidator()
        self._hooks = PluginHooks()
        self._config: dict[str, Any] = {}

    async def discover_plugins(self) -> list[str]:
        """Discover plugins using entry points.
        
        Returns:
            List of discovered plugin names
        """
        discovered = []

        # Discover from entry points
        entry_points = importlib.metadata.entry_points()

        if "sophia.plugins" in entry_points:
            for entry_point in entry_points["sophia.plugins"]:
                try:
                    plugin_class = entry_point.load()
                    plugin_name = entry_point.name

                    if await self.register_plugin_class(plugin_name, plugin_class):
                        discovered.append(plugin_name)
                        logger.info(f"Discovered plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {entry_point.name}: {e}")

        # Discover from plugins directory
        plugins_dir = Path(__file__).parent
        for file_path in plugins_dir.glob("*.py"):
            if file_path.stem in ["base", "registry", "__init__"]:
                continue

            try:
                module_name = f"app.plugins.{file_path.stem}"
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Plugin)
                        and obj not in [Plugin, SwarmPlugin, ToolPlugin, MemoryPlugin]
                    ):
                        plugin_name = file_path.stem
                        if await self.register_plugin_class(plugin_name, obj):
                            discovered.append(plugin_name)
                            logger.info(f"Discovered plugin from file: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")

        return discovered

    async def register_plugin_class(
        self,
        name: str,
        plugin_class: type[Plugin]
    ) -> bool:
        """Register a plugin class.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class to register
            
        Returns:
            Success status
        """
        try:
            # Instantiate plugin
            plugin = plugin_class()

            # Set metadata if not present
            if not plugin.metadata:
                plugin.metadata = PluginMetadata(
                    name=name,
                    version="1.0.0",
                    description=plugin_class.__doc__ or "No description",
                    author="Unknown"
                )

            # Validate plugin
            if not self._validate_plugin(plugin):
                logger.error(f"Plugin {name} failed validation")
                return False

            # Register plugin
            self._plugins[name] = plugin

            # Categorize by type
            for plugin_type, plugins in self._plugin_types.items():
                if isinstance(plugin, plugin_type):
                    plugins.append(name)
                    break

            # Call load hook
            await self._hooks.on_load(plugin)

            return True

        except Exception as e:
            logger.error(f"Failed to register plugin {name}: {e}")
            return False

    def register_plugin(
        self,
        plugin: Plugin
    ) -> bool:
        """Register an instantiated plugin.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            Success status
        """
        if not plugin.metadata:
            logger.error("Plugin missing metadata")
            return False

        name = plugin.metadata.name

        if not self._validate_plugin(plugin):
            logger.error(f"Plugin {name} failed validation")
            return False

        self._plugins[name] = plugin

        # Categorize by type
        for plugin_type, plugins in self._plugin_types.items():
            if isinstance(plugin, plugin_type):
                plugins.append(name)
                break

        logger.info(f"Registered plugin: {name}")
        return True

    def _validate_plugin(self, plugin: Plugin) -> bool:
        """Validate a plugin.
        
        Args:
            plugin: Plugin to validate
            
        Returns:
            Validation status
        """
        # Validate metadata
        if not self._validator.validate_metadata(plugin.metadata):
            return False

        # Validate interface
        if not self._validator.validate_interface(plugin):
            return False

        # Validate dependencies
        if not self._validator.validate_dependencies(
            plugin.metadata.dependencies
        ):
            return False

        return True

    async def initialize_plugin(
        self,
        name: str,
        config: Optional[dict[str, Any]] = None
    ) -> bool:
        """Initialize a plugin.
        
        Args:
            name: Plugin name
            config: Plugin configuration
            
        Returns:
            Success status
        """
        if name not in self._plugins:
            logger.error(f"Plugin {name} not found")
            return False

        plugin = self._plugins[name]

        if plugin.is_initialized:
            logger.warning(f"Plugin {name} already initialized")
            return True

        try:
            config = config or self._config.get(name, {})

            if not plugin.validate_config(config):
                logger.error(f"Invalid configuration for plugin {name}")
                return False

            await plugin.initialize(config)
            await self._hooks.on_initialize(plugin)

            logger.info(f"Initialized plugin: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin {name}: {e}")
            await self._hooks.on_error(plugin, e)
            return False

    async def initialize_all(
        self,
        config: Optional[dict[str, dict[str, Any]]] = None
    ) -> int:
        """Initialize all registered plugins.
        
        Args:
            config: Configuration for all plugins
            
        Returns:
            Number of successfully initialized plugins
        """
        self._config = config or {}
        initialized = 0

        for name in self._plugins:
            if await self.initialize_plugin(name):
                initialized += 1

        return initialized

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def get_plugins_by_type(
        self,
        plugin_type: type[Plugin]
    ) -> list[Plugin]:
        """Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to get
            
        Returns:
            List of plugins
        """
        plugin_names = self._plugin_types.get(plugin_type, [])
        return [
            self._plugins[name]
            for name in plugin_names
            if name in self._plugins
        ]

    def get_swarm_plugins(self) -> list[SwarmPlugin]:
        """Get all swarm plugins.
        
        Returns:
            List of swarm plugins
        """
        return self.get_plugins_by_type(SwarmPlugin)

    def get_tool_plugins(self) -> list[ToolPlugin]:
        """Get all tool plugins.
        
        Returns:
            List of tool plugins
        """
        return self.get_plugins_by_type(ToolPlugin)

    def get_memory_plugins(self) -> list[MemoryPlugin]:
        """Get all memory plugins.
        
        Returns:
            List of memory plugins
        """
        return self.get_plugins_by_type(MemoryPlugin)

    def list_plugins(self) -> dict[str, dict[str, Any]]:
        """List all registered plugins.
        
        Returns:
            Dictionary of plugin information
        """
        plugins_info = {}

        for name, plugin in self._plugins.items():
            plugins_info[name] = {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "author": plugin.metadata.author,
                "type": type(plugin).__name__,
                "initialized": plugin.is_initialized,
                "tags": plugin.metadata.tags
            }

        return plugins_info

    async def cleanup_plugin(self, name: str) -> bool:
        """Cleanup a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Success status
        """
        if name not in self._plugins:
            logger.error(f"Plugin {name} not found")
            return False

        plugin = self._plugins[name]

        try:
            await plugin.cleanup()
            await self._hooks.on_cleanup(plugin)

            logger.info(f"Cleaned up plugin: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup plugin {name}: {e}")
            await self._hooks.on_error(plugin, e)
            return False

    async def cleanup_all(self) -> int:
        """Cleanup all plugins.
        
        Returns:
            Number of successfully cleaned up plugins
        """
        cleaned = 0

        for name in list(self._plugins.keys()):
            if await self.cleanup_plugin(name):
                cleaned += 1

        return cleaned

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Success status
        """
        if name not in self._plugins:
            logger.error(f"Plugin {name} not found")
            return False

        # Remove from registry
        del self._plugins[name]

        # Remove from type lists
        for plugins in self._plugin_types.values():
            if name in plugins:
                plugins.remove(name)

        logger.info(f"Unregistered plugin: {name}")
        return True

    def clear(self) -> None:
        """Clear all plugins from registry."""
        self._plugins.clear()
        for plugins in self._plugin_types.values():
            plugins.clear()
        logger.info("Cleared plugin registry")

# ============================================
# Global Registry Instance
# ============================================

registry = PluginRegistry()

# ============================================
# Convenience Functions
# ============================================

async def discover_and_initialize_plugins(
    config: Optional[dict[str, dict[str, Any]]] = None
) -> dict[str, Any]:
    """Discover and initialize all plugins.
    
    Args:
        config: Plugin configurations
        
    Returns:
        Summary of discovered and initialized plugins
    """
    discovered = await registry.discover_plugins()
    initialized = await registry.initialize_all(config)

    return {
        "discovered": discovered,
        "initialized": initialized,
        "plugins": registry.list_plugins()
    }

def get_plugin(name: str) -> Optional[Plugin]:
    """Get a plugin by name.
    
    Args:
        name: Plugin name
        
    Returns:
        Plugin instance or None
    """
    return registry.get_plugin(name)

def get_swarm_plugins() -> list[SwarmPlugin]:
    """Get all swarm plugins.
    
    Returns:
        List of swarm plugins
    """
    return registry.get_swarm_plugins()

# ============================================
# Export
# ============================================

__all__ = [
    "PluginRegistry",
    "registry",
    "discover_and_initialize_plugins",
    "get_plugin",
    "get_swarm_plugins"
]
