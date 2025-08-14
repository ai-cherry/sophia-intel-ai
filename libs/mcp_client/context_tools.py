"""
Context-Aware Tool Wrapper
Enhances existing SOPHIA tools with MCP-powered context awareness and learning
"""

import asyncio
import json
import time
import inspect
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
import logging
from functools import wraps

from .sophia_client import SophiaMCPClient, MCPServerError

logger = logging.getLogger(__name__)


class ContextAwareToolWrapper:
    """
    Wrapper that adds context awareness and learning to existing SOPHIA tools.
    Stores tool usage patterns and retrieves relevant context before execution.
    """

    def __init__(self, mcp_client: SophiaMCPClient):
        self.mcp_client = mcp_client
        self.tool_stats = {}
        self.context_cache = {}

    async def wrap_tool(self, 
                       tool_func: Callable, 
                       tool_name: Optional[str] = None,
                       context_types: Optional[List[str]] = None) -> Callable:
        """
        Wrap a tool function with context awareness
        
        Args:
            tool_func: The original tool function to wrap
            tool_name: Optional name for the tool (uses function name if None)
            context_types: Types of context relevant to this tool
            
        Returns:
            Context-aware wrapped function
        """
        actual_tool_name = tool_name or tool_func.__name__
        relevant_context_types = context_types or ["tool_usage", "code_change"]
        
        @wraps(tool_func)
        async def context_aware_wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Initialize tool stats if not present
            if actual_tool_name not in self.tool_stats:
                self.tool_stats[actual_tool_name] = {
                    "usage_count": 0,
                    "total_execution_time": 0.0,
                    "success_count": 0,
                    "error_count": 0,
                    "last_used": None
                }
            
            try:
                # Get relevant context before execution
                context_query = self._build_context_query(
                    actual_tool_name, args, kwargs
                )
                
                relevant_context = await self.mcp_client.query_context(
                    query=context_query,
                    top_k=3,
                    threshold=0.6,
                    context_types=relevant_context_types
                )
                
                # Log context retrieval
                logger.info(
                    f"Retrieved {len(relevant_context)} context entries for {actual_tool_name}"
                )
                
                # Execute the original tool with enhanced parameters
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(*args, **kwargs)
                else:
                    result = tool_func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                
                # Store successful tool usage
                await self._store_tool_execution(
                    actual_tool_name,
                    args, kwargs,
                    result,
                    execution_time,
                    relevant_context,
                    success=True
                )
                
                # Update stats
                self._update_tool_stats(actual_tool_name, execution_time, success=True)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Tool {actual_tool_name} failed: {e}")
                
                # Store failed execution for learning
                await self._store_tool_execution(
                    actual_tool_name,
                    args, kwargs,
                    {"error": str(e)},
                    execution_time,
                    [],
                    success=False
                )
                
                # Update stats
                self._update_tool_stats(actual_tool_name, execution_time, success=False)
                
                # Re-raise the original exception
                raise
        
        return context_aware_wrapper

    async def get_tool_suggestions(self, 
                                 current_context: str,
                                 file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tool usage suggestions based on current context
        
        Args:
            current_context: Description of current situation
            file_path: Optional file path for file-specific suggestions
            
        Returns:
            List of suggested tools with confidence scores
        """
        try:
            query_parts = [current_context]
            if file_path:
                query_parts.append(f"file:{file_path}")
            
            query = " ".join(query_parts)
            
            # Get relevant past tool usages
            relevant_context = await self.mcp_client.query_context(
                query=query,
                top_k=10,
                threshold=0.5,
                context_types=["tool_usage"]
            )
            
            # Analyze patterns and suggest tools
            tool_suggestions = self._analyze_tool_patterns(relevant_context)
            
            return tool_suggestions
            
        except Exception as e:
            logger.error(f"Failed to get tool suggestions: {e}")
            return []

    async def get_similar_executions(self, 
                                   tool_name: str,
                                   params: Dict[str, Any],
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar past executions of a tool
        
        Args:
            tool_name: Name of the tool
            params: Parameters for the tool
            limit: Maximum number of similar executions to return
            
        Returns:
            List of similar past executions
        """
        try:
            # Create query from tool name and key parameters
            param_str = " ".join(f"{k}:{v}" for k, v in params.items() if v is not None)
            query = f"{tool_name} {param_str}"
            
            similar_executions = await self.mcp_client.query_context(
                query=query,
                top_k=limit,
                threshold=0.7,
                context_types=["tool_usage"]
            )
            
            return similar_executions
            
        except Exception as e:
            logger.error(f"Failed to get similar executions: {e}")
            return []

    async def learn_from_feedback(self, 
                                tool_name: str,
                                execution_id: str,
                                feedback: Dict[str, Any]):
        """
        Learn from user feedback on tool execution results
        
        Args:
            tool_name: Name of the tool
            execution_id: ID of the execution to provide feedback on
            feedback: Feedback data (e.g., {"helpful": True, "suggestions": "..."})
        """
        try:
            feedback_data = {
                "tool_name": tool_name,
                "execution_id": execution_id,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.mcp_client.store_context(
                content=json.dumps(feedback_data, default=str),
                context_type="tool_feedback",
                metadata={
                    "tool_name": tool_name,
                    "execution_id": execution_id,
                    "feedback_type": "user_feedback"
                }
            )
            
            logger.info(f"Stored feedback for {tool_name} execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics for all wrapped tools"""
        return {
            "tools": dict(self.tool_stats),
            "total_tools": len(self.tool_stats),
            "cache_size": len(self.context_cache)
        }

    async def _store_tool_execution(self,
                                  tool_name: str,
                                  args: tuple,
                                  kwargs: Dict[str, Any],
                                  result: Any,
                                  execution_time: float,
                                  context_used: List[Dict[str, Any]],
                                  success: bool):
        """Store details of tool execution for future learning"""
        try:
            # Create execution record
            execution_data = {
                "tool_name": tool_name,
                "parameters": {
                    "args": [str(arg) for arg in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()}
                },
                "result_summary": self._summarize_result(result),
                "execution_time": execution_time,
                "success": success,
                "context_used": len(context_used),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add file path information if available
            file_path = self._extract_file_path(args, kwargs)
            if file_path:
                execution_data["file_path"] = file_path
            
            await self.mcp_client.store_tool_usage(
                tool_name=tool_name,
                params=execution_data["parameters"],
                result=execution_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Failed to store tool execution: {e}")

    def _build_context_query(self, 
                           tool_name: str, 
                           args: tuple, 
                           kwargs: Dict[str, Any]) -> str:
        """Build a context query based on tool name and parameters"""
        query_parts = [tool_name]
        
        # Extract file path if present
        file_path = self._extract_file_path(args, kwargs)
        if file_path:
            query_parts.append(f"file:{file_path}")
        
        # Add key parameter information
        for key, value in kwargs.items():
            if key in ["path", "pattern", "query", "content"] and value:
                query_parts.append(f"{key}:{str(value)[:50]}")
        
        return " ".join(query_parts)

    def _extract_file_path(self, args: tuple, kwargs: Dict[str, Any]) -> Optional[str]:
        """Extract file path from tool parameters"""
        # Check common parameter names
        for param_name in ["path", "file_path", "filename"]:
            if param_name in kwargs:
                return str(kwargs[param_name])
        
        # Check first argument if it looks like a path
        if args and isinstance(args[0], (str, Path)):
            path_str = str(args[0])
            if "/" in path_str or "\\" in path_str or path_str.endswith(('.py', '.js', '.ts', '.md', '.json')):
                return path_str
        
        return None

    def _summarize_result(self, result: Any) -> str:
        """Create a summary of tool result"""
        if result is None:
            return "No result"
        
        if isinstance(result, dict):
            keys = list(result.keys())[:3]
            return f"Dict with {len(result)} keys: {keys}"
        elif isinstance(result, list):
            return f"List with {len(result)} items"
        elif isinstance(result, str):
            return result[:100] + "..." if len(result) > 100 else result
        elif isinstance(result, bool):
            return f"Boolean: {result}"
        else:
            return f"{type(result).__name__}: {str(result)[:50]}"

    def _analyze_tool_patterns(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze tool usage patterns to generate suggestions"""
        tool_counts = {}
        tool_contexts = {}
        
        for entry in context:
            try:
                content = json.loads(entry.get("content", "{}"))
                tool_name = content.get("tool_name")
                
                if tool_name:
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                    if tool_name not in tool_contexts:
                        tool_contexts[tool_name] = []
                    tool_contexts[tool_name].append(content)
            except json.JSONDecodeError:
                continue
        
        # Generate suggestions based on frequency and context
        suggestions = []
        total_usages = sum(tool_counts.values())
        
        for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            confidence = count / total_usages if total_usages > 0 else 0
            
            # Get common parameters for this tool
            common_params = self._extract_common_params(tool_contexts[tool_name])
            
            suggestions.append({
                "tool_name": tool_name,
                "confidence": confidence,
                "usage_count": count,
                "common_params": common_params,
                "reason": f"Used {count} times in similar contexts"
            })
        
        return suggestions[:5]  # Return top 5 suggestions

    def _extract_common_params(self, tool_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract commonly used parameters for a tool"""
        param_counts = {}
        
        for context in tool_contexts:
            params = context.get("parameters", {})
            kwargs = params.get("kwargs", {})
            
            for param, value in kwargs.items():
                if param not in param_counts:
                    param_counts[param] = {}
                
                if value not in param_counts[param]:
                    param_counts[param][value] = 0
                param_counts[param][value] += 1
        
        # Find most common values for each parameter
        common_params = {}
        for param, value_counts in param_counts.items():
            if value_counts:
                most_common_value = max(value_counts, key=value_counts.get)
                common_params[param] = {
                    "value": most_common_value,
                    "frequency": value_counts[most_common_value]
                }
        
        return common_params

    def _update_tool_stats(self, tool_name: str, execution_time: float, success: bool):
        """Update tool usage statistics"""
        stats = self.tool_stats[tool_name]
        
        stats["usage_count"] += 1
        stats["total_execution_time"] += execution_time
        stats["last_used"] = datetime.now().isoformat()
        
        if success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1


# Convenience function for creating context-aware tools
def make_context_aware(mcp_client: SophiaMCPClient):
    """
    Decorator factory for making tools context-aware
    
    Args:
        mcp_client: The MCP client to use for context operations
        
    Returns:
        Decorator function
    """
    wrapper = ContextAwareToolWrapper(mcp_client)
    
    def decorator(tool_func: Callable) -> Callable:
        return asyncio.create_task(wrapper.wrap_tool(tool_func))
    
    return decorator


# Enhanced tool implementations
class EnhancedFileOperations:
    """Enhanced file operations with context awareness"""
    
    def __init__(self, mcp_client: SophiaMCPClient):
        self.mcp_client = mcp_client
        self.wrapper = ContextAwareToolWrapper(mcp_client)
    
    async def read_file_with_context(self, 
                                   file_path: str,
                                   include_context: bool = True) -> Dict[str, Any]:
        """
        Read a file with relevant context from previous interactions
        
        Args:
            file_path: Path to the file to read
            include_context: Whether to include related context
            
        Returns:
            Dict containing file content and related context
        """
        # Read the file (original functionality)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {"error": str(e), "file_path": file_path}
        
        result = {
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "lines": content.count('\n') + 1 if content else 0
        }
        
        if include_context:
            # Get relevant context for this file
            file_context = await self.mcp_client.get_file_context(file_path)
            result["related_context"] = file_context
            
            # Get suggestions for next actions
            suggestions = await self.wrapper.get_tool_suggestions(
                f"reading file {file_path}",
                file_path
            )
            result["suggested_actions"] = suggestions
        
        # Store this file access
        await self.mcp_client.store_context(
            content=f"Read file: {file_path} ({len(content)} chars)",
            context_type="file_access",
            metadata={
                "file_path": file_path,
                "operation": "read",
                "file_size": len(content)
            }
        )
        
        return result