"""
Pluggable Tool Registry

This module implements a plugin-based registry that enables optional tools
without hard dependencies, allowing agents to dynamically load and use tools.
"""

import asyncio
import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional, Union

from pydantic import BaseModel, Field

from app.tools.tool_schemas import (
    ToolCall,
    ToolCategory,
    ToolDefinition,
    ToolResponse,
)

logger = logging.getLogger(__name__)


class ToolPlugin(ABC):
    """Abstract base class for tool plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    def dependencies(self) -> list[str]:
        """List of required dependencies"""
        return []
    
    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            category=self.category,
            parameters=self.get_parameters(),
            returns=self.get_return_description()
        )
    
    @abstractmethod
    def get_parameters(self) -> list:
        """Get tool parameters"""
        pass
    
    @abstractmethod
    def get_return_description(self) -> str:
        """Get return value description"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        pass
    
    def validate_dependencies(self) -> bool:
        """Check if all dependencies are available"""
        for dep in self.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"Missing dependency for {self.name}: {dep}")
                return False
        return True
    
    async def initialize(self) -> bool:
        """Initialize the tool (optional)"""
        return True
    
    async def cleanup(self) -> None:
        """Cleanup resources (optional)"""
        pass


class PluginMetadata(BaseModel):
    """Metadata for a loaded plugin"""
    name: str
    category: ToolCategory
    module_path: str
    class_name: str
    version: str = "1.0.0"
    author: Optional[str] = None
    enabled: bool = True
    load_priority: int = Field(0, ge=0, le=100)
    dependencies_satisfied: bool = True
    initialization_status: str = "pending"  # pending, success, failed
    error_message: Optional[str] = None


class PluggableToolRegistry:
    """Dynamic tool registry with plugin support"""
    
    def __init__(self, plugin_dirs: Optional[list[Path]] = None):
        self.plugins: dict[str, ToolPlugin] = {}
        self.metadata: dict[str, PluginMetadata] = {}
        self.plugin_dirs = plugin_dirs or [Path("app/tools/plugins")]
        self._executors: dict[str, Callable] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the registry and load plugins"""
        if self._initialized:
            return
        
        logger.info("Initializing pluggable tool registry...")
        
        # Load built-in plugins
        await self._load_builtin_plugins()
        
        # Discover and load external plugins
        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists():
                await self._discover_plugins(plugin_dir)
        
        # Initialize all loaded plugins
        await self._initialize_plugins()
        
        self._initialized = True
        logger.info(f"Registry initialized with {len(self.plugins)} plugins")
    
    async def _load_builtin_plugins(self) -> None:
        """Load built-in tool plugins"""
        builtin_plugins = [
            CodeSearchPlugin,
            WebSearchPlugin,
            FileOperationsPlugin,
            GitOperationsPlugin,
        ]
        
        for plugin_class in builtin_plugins:
            try:
                plugin = plugin_class()
                await self._register_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to load builtin plugin {plugin_class.__name__}: {e}")
    
    async def _discover_plugins(self, plugin_dir: Path) -> None:
        """Discover plugins in a directory"""
        for file_path in plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                module_name = f"app.tools.plugins.{file_path.stem}"
                module = importlib.import_module(module_name)
                
                # Find plugin classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, ToolPlugin) and 
                        obj != ToolPlugin):
                        
                        plugin = obj()
                        await self._register_plugin(plugin)
                        
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")
    
    async def _register_plugin(self, plugin: ToolPlugin) -> bool:
        """Register a plugin"""
        try:
            # Check dependencies
            if not plugin.validate_dependencies():
                logger.warning(f"Skipping {plugin.name}: dependencies not satisfied")
                self.metadata[plugin.name] = PluginMetadata(
                    name=plugin.name,
                    category=plugin.category,
                    module_path=plugin.__class__.__module__,
                    class_name=plugin.__class__.__name__,
                    dependencies_satisfied=False,
                    initialization_status="skipped"
                )
                return False
            
            # Register the plugin
            self.plugins[plugin.name] = plugin
            self.metadata[plugin.name] = PluginMetadata(
                name=plugin.name,
                category=plugin.category,
                module_path=plugin.__class__.__module__,
                class_name=plugin.__class__.__name__,
                dependencies_satisfied=True,
                initialization_status="registered"
            )
            
            logger.info(f"Registered plugin: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {e}")
            return False
    
    async def _initialize_plugins(self) -> None:
        """Initialize all registered plugins"""
        for name, plugin in self.plugins.items():
            try:
                success = await plugin.initialize()
                if success:
                    self.metadata[name].initialization_status = "success"
                    logger.info(f"Initialized plugin: {name}")
                else:
                    self.metadata[name].initialization_status = "failed"
                    logger.warning(f"Plugin initialization failed: {name}")
                    
            except Exception as e:
                self.metadata[name].initialization_status = "failed"
                self.metadata[name].error_message = str(e)
                logger.error(f"Error initializing plugin {name}: {e}")
    
    async def execute_tool(self, call: ToolCall) -> ToolResponse:
        """Execute a tool by name"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if call.tool_name not in self.plugins:
                return ToolResponse(
                    tool_name=call.tool_name,
                    success=False,
                    error=f"Tool not found: {call.tool_name}",
                    execution_time=asyncio.get_event_loop().time() - start_time
                )
            
            plugin = self.plugins[call.tool_name]
            
            # Validate call against definition
            is_valid, error = plugin.definition.validate_call(call)
            if not is_valid:
                return ToolResponse(
                    tool_name=call.tool_name,
                    success=False,
                    error=error,
                    execution_time=asyncio.get_event_loop().time() - start_time
                )
            
            # Execute the tool
            result = await plugin.execute(**call.parameters)
            
            return ToolResponse(
                tool_name=call.tool_name,
                success=True,
                result=result,
                execution_time=asyncio.get_event_loop().time() - start_time,
                metadata={"plugin_version": self.metadata[call.tool_name].version}
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed for {call.tool_name}: {e}")
            return ToolResponse(
                tool_name=call.tool_name,
                success=False,
                error=str(e),
                execution_time=asyncio.get_event_loop().time() - start_time
            )
    
    def get_available_tools(self, category: Optional[ToolCategory] = None) -> list[str]:
        """Get list of available tools"""
        if category:
            return [
                name for name, plugin in self.plugins.items()
                if plugin.category == category
            ]
        return list(self.plugins.keys())
    
    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        plugin = self.plugins.get(name)
        return plugin.definition if plugin else None
    
    def get_tools_by_category(self, category: ToolCategory) -> dict[str, ToolDefinition]:
        """Get all tools in a category"""
        return {
            name: plugin.definition
            for name, plugin in self.plugins.items()
            if plugin.category == category
        }
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name in self.metadata:
            self.metadata[name].enabled = True
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        if name in self.metadata:
            self.metadata[name].enabled = False
            return True
        return False
    
    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin"""
        if name not in self.metadata:
            return False
        
        try:
            # Cleanup old plugin
            if name in self.plugins:
                await self.plugins[name].cleanup()
                del self.plugins[name]
            
            # Reload module
            metadata = self.metadata[name]
            module = importlib.reload(importlib.import_module(metadata.module_path))
            
            # Instantiate new plugin
            plugin_class = getattr(module, metadata.class_name)
            plugin = plugin_class()
            
            # Re-register and initialize
            if await self._register_plugin(plugin):
                success = await plugin.initialize()
                self.metadata[name].initialization_status = "success" if success else "failed"
                return success
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {name}: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin.name}: {e}")
        
        self.plugins.clear()
        self.metadata.clear()
        self._initialized = False


# Example built-in plugins

class CodeSearchPlugin(ToolPlugin):
    """Plugin for searching code"""
    
    @property
    def name(self) -> str:
        return "code_search"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING
    
    @property
    def description(self) -> str:
        return "Search for code patterns in the repository"
    
    def get_parameters(self) -> list:
        from app.tools.tool_schemas import ToolParameter
        return [
            ToolParameter(name="query", type="str", description="Search query"),
            ToolParameter(name="language", type="str", description="Programming language", required=False),
            ToolParameter(name="max_results", type="int", description="Maximum results", default=10),
        ]
    
    def get_return_description(self) -> str:
        return "List of code matches with file paths and line numbers"
    
    async def execute(self, query: str, language: str = None, max_results: int = 10) -> list:
        """Execute code search"""
        # Simplified implementation
        results = []
        
        # Would use actual code search logic here
        import glob
        pattern = "**/*.py" if language == "python" else "**/*"
        
        for file_path in glob.glob(pattern, recursive=True)[:max_results]:
            results.append({
                "file": file_path,
                "matches": ["Example match"]
            })
        
        return results


class WebSearchPlugin(ToolPlugin):
    """Plugin for web search"""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.RESEARCH
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    @property
    def dependencies(self) -> list[str]:
        return ["httpx"]  # Example dependency
    
    def get_parameters(self) -> list:
        from app.tools.tool_schemas import ToolParameter
        return [
            ToolParameter(name="query", type="str", description="Search query"),
            ToolParameter(name="max_results", type="int", description="Maximum results", default=10),
        ]
    
    def get_return_description(self) -> str:
        return "List of search results with URLs and snippets"
    
    async def execute(self, query: str, max_results: int = 10) -> list:
        """Execute web search"""
        # Would use actual web search API here
        return [
            {"url": f"https://example.com/{i}", "snippet": f"Result for {query}"}
            for i in range(min(max_results, 3))
        ]


class FileOperationsPlugin(ToolPlugin):
    """Plugin for file operations"""
    
    @property
    def name(self) -> str:
        return "file_operations"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE_OPERATIONS
    
    @property
    def description(self) -> str:
        return "Perform file system operations"
    
    def get_parameters(self) -> list:
        from app.tools.tool_schemas import ToolParameter
        return [
            ToolParameter(name="operation", type="str", description="Operation type", enum_values=["read", "write", "delete", "list"]),
            ToolParameter(name="path", type="str", description="File or directory path"),
            ToolParameter(name="content", type="str", description="Content for write operations", required=False),
        ]
    
    def get_return_description(self) -> str:
        return "Operation result"
    
    async def execute(self, operation: str, path: str, content: str = None) -> Any:
        """Execute file operation"""
        from pathlib import Path
        
        p = Path(path)
        
        if operation == "read":
            if p.exists():
                return p.read_text()
            return f"File not found: {path}"
        elif operation == "list":
            if p.is_dir():
                return [str(f) for f in p.iterdir()]
            return f"Not a directory: {path}"
        
        # Other operations would be implemented
        return f"Operation {operation} completed"


class GitOperationsPlugin(ToolPlugin):
    """Plugin for Git operations"""
    
    @property
    def name(self) -> str:
        return "git_operations"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING
    
    @property
    def description(self) -> str:
        return "Perform Git repository operations"
    
    def get_parameters(self) -> list:
        from app.tools.tool_schemas import ToolParameter
        return [
            ToolParameter(name="command", type="str", description="Git command", enum_values=["status", "diff", "log", "branch"]),
            ToolParameter(name="args", type="list", description="Command arguments", required=False, default=[]),
        ]
    
    def get_return_description(self) -> str:
        return "Git command output"
    
    async def execute(self, command: str, args: list = None) -> str:
        """Execute Git command"""
        import subprocess
        
        try:
            cmd = ["git", command] + (args or [])
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Git operation failed: {e}"


# Global registry instance
global_plugin_registry = PluggableToolRegistry()