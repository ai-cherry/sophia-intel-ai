import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the standardized base client
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../../libs'))
from mcp_client.base_client import BaseMCPClient, MCPServiceConfig, SearchResult

class MCPClient(BaseMCPClient):
    """Enhanced MCP Code Server Client using standardized base client"""
    
    def __init__(self):
        config = MCPServiceConfig.from_env('MCP_CODE_SERVER')
        super().__init__('mcp_code_server', config)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health using base client"""
        correlation_id = str(uuid.uuid4())
        
        try:
            result = await self._make_request('GET', '/health')
            return {
                "status": "healthy" if result else "unhealthy",
                "correlation_id": correlation_id,
                "response": result
            }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def read_repo(self, repo: str, path: Optional[str] = None) -> Dict[str, Any]:
        """Read repository content using base client"""
        correlation_id = str(uuid.uuid4())
        
        try:
            params = {"repo": repo}
            if path:
                params["path"] = path
            
            result = await self._make_request('GET', '/repo/read', params=params)
            return {
                "status": "success" if result else "error",
                "correlation_id": correlation_id,
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def write_file(self, repo: str, path: str, content: str, message: str) -> Dict[str, Any]:
        """Write file to repository using base client"""
        correlation_id = str(uuid.uuid4())
        
        try:
            payload = {
                "repo": repo,
                "path": path,
                "content": content,
                "message": message
            }
            
            result = await self._make_request('POST', '/repo/write', json_data=payload)
            return {
                "status": "success" if result else "error",
                "correlation_id": correlation_id,
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def search_code(self, query: str, repo: Optional[str] = None) -> Dict[str, Any]:
        """Search code using base client"""
        correlation_id = str(uuid.uuid4())
        
        try:
            params = {"query": query}
            if repo:
                params["repo"] = repo
            
            result = await self._make_request('GET', '/search/code', params=params)
            return {
                "status": "success" if result else "error",
                "correlation_id": correlation_id,
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def get_context(self, repo: str, context_type: str = "full") -> Dict[str, Any]:
        """Get repository context using base client"""
        correlation_id = str(uuid.uuid4())
        
        try:
            params = {"repo": repo, "type": context_type}
            result = await self._make_request('GET', '/context', params=params)
            return {
                "status": "success" if result else "error",
                "correlation_id": correlation_id,
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }

