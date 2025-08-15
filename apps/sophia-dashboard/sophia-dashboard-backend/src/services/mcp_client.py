import os
import uuid
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class MCPClient:
    """Client for Enhanced MCP Code Server"""
    
    def __init__(self):
        self.base_url = os.getenv('MCP_BASE_URL')
        self.auth_token = os.getenv('MCP_AUTH_TOKEN')
        
        if not self.base_url or not self.auth_token:
            raise ValueError("MCP_BASE_URL and MCP_AUTH_TOKEN must be configured")
    
    def _get_headers(self, correlation_id: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with auth and correlation ID"""
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        if correlation_id:
            headers['X-Correlation-ID'] = correlation_id
        
        return headers
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        correlation_id = str(uuid.uuid4())
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers(correlation_id)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "healthy",
                            "correlation_id": correlation_id,
                            "response": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "correlation_id": correlation_id,
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def read_repo(self, repo: str, path: Optional[str] = None) -> Dict[str, Any]:
        """Read repository content"""
        correlation_id = str(uuid.uuid4())
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"repo": repo}
                if path:
                    params["path"] = path
                
                async with session.get(
                    f"{self.base_url}/repo/read",
                    params=params,
                    headers=self._get_headers(correlation_id)
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "success" if resp.status == 200 else "error",
                        "correlation_id": correlation_id,
                        "data": data
                    }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def write_file(self, repo: str, path: str, content: str, message: str) -> Dict[str, Any]:
        """Write file to repository"""
        correlation_id = str(uuid.uuid4())
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "repo": repo,
                    "path": path,
                    "content": content,
                    "message": message
                }
                
                async with session.post(
                    f"{self.base_url}/repo/write",
                    json=payload,
                    headers=self._get_headers(correlation_id)
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "success" if resp.status == 200 else "error",
                        "correlation_id": correlation_id,
                        "data": data
                    }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def create_branch(self, repo: str, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch"""
        correlation_id = str(uuid.uuid4())
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "repo": repo,
                    "branch_name": branch_name,
                    "base_branch": base_branch
                }
                
                async with session.post(
                    f"{self.base_url}/repo/branch/create",
                    json=payload,
                    headers=self._get_headers(correlation_id)
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "success" if resp.status == 200 else "error",
                        "correlation_id": correlation_id,
                        "data": data
                    }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def open_pr(self, repo: str, branch: str, title: str, body: str, base: str = "main") -> Dict[str, Any]:
        """Open a pull request"""
        correlation_id = str(uuid.uuid4())
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "repo": repo,
                    "head": branch,
                    "base": base,
                    "title": title,
                    "body": body
                }
                
                async with session.post(
                    f"{self.base_url}/repo/pr/create",
                    json=payload,
                    headers=self._get_headers(correlation_id)
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "success" if resp.status == 200 else "error",
                        "correlation_id": correlation_id,
                        "data": data
                    }
        except Exception as e:
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def get_operation_logs(self, correlation_id: str) -> Dict[str, Any]:
        """Get operation logs by correlation ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/logs/{correlation_id}",
                    headers=self._get_headers()
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "success" if resp.status == 200 else "error",
                        "data": data
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

