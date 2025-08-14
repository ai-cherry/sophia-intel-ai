"""
SOPHIA MCP Client
Core client for integrating with SOPHIA's MCP server infrastructure
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MCPServerError(Exception):
    """Exception raised for MCP server communication errors"""
    pass


class SophiaMCPClient:
    """
    Enhanced MCP client that provides seamless integration between SOPHIA 
    and the existing MCP server infrastructure for contextualized coding memory.
    """

    def __init__(self, session_id: str, mcp_port: int = 8000):
        self.session_id = session_id
        self.mcp_base_url = f"http://localhost:{mcp_port}"
        self.session = None
        self.connected = False
        self.context_cache = {}
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Initialize connection to MCP servers"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection to memory service
            await self.health_check()
            self.connected = True
            logger.info(f"SOPHIA MCP Client connected for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP servers: {e}")
            if self.session:
                await self.session.close()
            raise MCPServerError(f"Connection failed: {e}")

    async def disconnect(self):
        """Close connection and cleanup resources"""
        if self.session:
            await self.session.close()
            self.connected = False
            logger.info(f"SOPHIA MCP Client disconnected for session {self.session_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Check health of MCP servers"""
        try:
            async with self.session.get(f"{self.mcp_base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    return health_data
                else:
                    raise MCPServerError(f"Health check failed: {response.status}")
        except Exception as e:
            raise MCPServerError(f"Health check error: {e}")

    async def store_context(self, 
                          content: str, 
                          context_type: str = "general",
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store context in the memory service with enhanced metadata
        
        Args:
            content: The content to store
            context_type: Type of context (e.g., "code_change", "tool_usage", "interaction")
            metadata: Additional metadata to store with the context
            
        Returns:
            Dict containing success status, ID, and summary
        """
        start_time = time.time()
        
        try:
            payload = {
                "session_id": self.session_id,
                "content": content,
                "context_type": context_type,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "client": "sophia_mcp_client",
                    **(metadata or {})
                }
            }
            
            async with self.session.post(
                f"{self.mcp_base_url}/context/store",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Update performance stats
                    self._update_stats(time.time() - start_time)
                    
                    logger.info(f"Stored context for session {self.session_id}: {result.get('id')}")
                    return result
                else:
                    error_text = await response.text()
                    raise MCPServerError(f"Store context failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to store context: {e}")
            raise MCPServerError(f"Context storage error: {e}")

    async def query_context(self, 
                          query: str, 
                          top_k: int = 5, 
                          threshold: float = 0.7,
                          context_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Query context from memory service with intelligent caching
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            threshold: Similarity threshold (0.0 to 1.0)
            context_types: Filter by specific context types
            
        Returns:
            List of relevant context entries
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{query}_{top_k}_{threshold}_{context_types}"
        if cache_key in self.context_cache:
            self.performance_stats["cache_hits"] += 1
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.context_cache[cache_key]
        
        try:
            payload = {
                "session_id": self.session_id,
                "query": query,
                "top_k": top_k,
                "threshold": threshold
            }
            
            async with self.session.post(
                f"{self.mcp_base_url}/context/query",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    results = result.get("results", [])
                    
                    # Filter by context types if specified
                    if context_types:
                        results = [
                            r for r in results 
                            if r.get("metadata", {}).get("context_type") in context_types
                        ]
                    
                    # Cache the results
                    self.context_cache[cache_key] = results
                    
                    # Update performance stats
                    self._update_stats(time.time() - start_time)
                    
                    logger.info(f"Retrieved {len(results)} context entries for query: {query[:50]}...")
                    return results
                else:
                    error_text = await response.text()
                    raise MCPServerError(f"Query context failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to query context: {e}")
            raise MCPServerError(f"Context query error: {e}")

    async def store_tool_usage(self, 
                             tool_name: str, 
                             params: Dict[str, Any], 
                             result: Any,
                             execution_time: float = 0.0) -> Dict[str, Any]:
        """
        Store tool usage patterns for learning and optimization
        
        Args:
            tool_name: Name of the tool used
            params: Parameters passed to the tool
            result: Result returned by the tool
            execution_time: Time taken to execute the tool
            
        Returns:
            Storage confirmation
        """
        content = {
            "tool_name": tool_name,
            "parameters": params,
            "result_summary": self._summarize_result(result),
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        metadata = {
            "context_type": "tool_usage",
            "tool_name": tool_name,
            "has_result": result is not None,
            "execution_time": execution_time
        }
        
        return await self.store_context(
            content=json.dumps(content, default=str),
            context_type="tool_usage", 
            metadata=metadata
        )

    async def get_relevant_context(self, 
                                 current_action: str, 
                                 file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get contextually relevant information for current action
        
        Args:
            current_action: Description of current action being performed
            file_path: Optional file path for file-specific context
            
        Returns:
            List of relevant context entries
        """
        queries = [current_action]
        
        # Add file-specific queries if file path provided
        if file_path:
            path_obj = Path(file_path)
            queries.extend([
                f"file:{file_path}",
                f"extension:{path_obj.suffix}",
                f"filename:{path_obj.name}"
            ])
        
        all_results = []
        for query in queries:
            results = await self.query_context(query, top_k=3, threshold=0.6)
            all_results.extend(results)
        
        # Deduplicate and sort by relevance score
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.get("id") not in seen_ids:
                seen_ids.add(result.get("id"))
                unique_results.append(result)
        
        # Sort by score (highest first) and return top results
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique_results[:5]

    async def get_file_context(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get context specific to a file (previous edits, patterns, etc.)
        
        Args:
            file_path: Path to the file
            
        Returns:
            File-specific context entries
        """
        return await self.query_context(
            f"file:{file_path}",
            top_k=10,
            threshold=0.5,
            context_types=["code_change", "tool_usage"]
        )

    async def store_code_change(self, 
                              file_path: str, 
                              change_description: str, 
                              diff: Optional[str] = None,
                              intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Store a code change with rich context
        
        Args:
            file_path: Path to the changed file
            change_description: Description of what was changed
            diff: Optional diff content
            intent: Optional description of the intent behind the change
            
        Returns:
            Storage confirmation
        """
        content = {
            "file_path": file_path,
            "change_description": change_description,
            "diff": diff,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
        
        metadata = {
            "context_type": "code_change",
            "file_path": file_path,
            "file_extension": Path(file_path).suffix,
            "has_diff": diff is not None,
            "has_intent": intent is not None
        }
        
        return await self.store_context(
            content=json.dumps(content, default=str),
            context_type="code_change",
            metadata=metadata
        )

    async def clear_cache(self):
        """Clear the local context cache"""
        self.context_cache.clear()
        logger.info("Context cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.performance_stats,
            "cache_size": len(self.context_cache),
            "connected": self.connected,
            "session_id": self.session_id
        }

    def _update_stats(self, response_time: float):
        """Update performance statistics"""
        self.performance_stats["total_requests"] += 1
        current_avg = self.performance_stats["avg_response_time"]
        total_requests = self.performance_stats["total_requests"]
        
        self.performance_stats["avg_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )

    def _summarize_result(self, result: Any) -> str:
        """Create a summary of tool result for storage"""
        if result is None:
            return "No result"
        
        if isinstance(result, dict):
            return f"Dict with {len(result)} keys: {list(result.keys())[:3]}"
        elif isinstance(result, list):
            return f"List with {len(result)} items"
        elif isinstance(result, str):
            return result[:200] + "..." if len(result) > 200 else result
        else:
            return str(type(result).__name__)