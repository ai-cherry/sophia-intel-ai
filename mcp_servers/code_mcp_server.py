"""
MCP Code Server - Dedicated coding agent with GitHub integration
Provides real tools for repository operations, code analysis, and PR management
"""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
import aiohttp
import uvicorn

from config.config import settings


# Request/Response Models
class CodeRequest(BaseModel):
    """Code operation request"""
    operation: str = Field(..., description="Operation type: read_repo, propose_diff, create_branch, open_pr")
    repository: str = Field(..., description="Repository name (owner/repo)")
    branch: Optional[str] = Field(default="main", description="Target branch")
    file_path: Optional[str] = Field(default=None, description="File path for operations")
    content: Optional[str] = Field(default=None, description="Content for file operations")
    commit_message: Optional[str] = Field(default=None, description="Commit message")
    pr_title: Optional[str] = Field(default=None, description="Pull request title")
    pr_description: Optional[str] = Field(default=None, description="Pull request description")
    diff_content: Optional[str] = Field(default=None, description="Diff content for proposals")


class CodeResponse(BaseModel):
    """Code operation response"""
    success: bool
    operation: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GitHubTools:
    """Real GitHub integration tools"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_PAT')
        self.base_url = "https://api.github.com"
        
        if not self.github_token:
            logger.error("GITHUB_PAT environment variable not set")
            raise ValueError("GitHub PAT token required")
    
    async def _make_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated GitHub API request"""
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sophia-Intel-MCP-Code-Server"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"GitHub API error {response.status}: {error_text}")
                    raise HTTPException(status_code=response.status, detail=error_text)
                
                return await response.json()
    
    async def read_repository_structure(self, repository: str, branch: str = "main") -> Dict:
        """Read repository structure and key files"""
        try:
            # Get repository info
            repo_url = f"{self.base_url}/repos/{repository}"
            repo_info = await self._make_request("GET", repo_url)
            
            # Get repository tree
            tree_url = f"{self.base_url}/repos/{repository}/git/trees/{branch}?recursive=1"
            tree_data = await self._make_request("GET", tree_url)
            
            # Get key files content
            key_files = ["README.md", "pyproject.toml", "requirements.txt", "package.json"]
            file_contents = {}
            
            for file_info in tree_data.get("tree", []):
                if file_info["path"] in key_files and file_info["type"] == "blob":
                    content_url = f"{self.base_url}/repos/{repository}/contents/{file_info['path']}"
                    try:
                        content_data = await self._make_request("GET", content_url)
                        if content_data.get("content"):
                            import base64
                            content = base64.b64decode(content_data["content"]).decode('utf-8')
                            file_contents[file_info["path"]] = content
                    except Exception as e:
                        logger.warning(f"Could not read {file_info['path']}: {e}")
            
            return {
                "repository": repo_info,
                "structure": tree_data,
                "key_files": file_contents,
                "total_files": len([f for f in tree_data.get("tree", []) if f["type"] == "blob"]),
                "languages": repo_info.get("language", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Error reading repository {repository}: {e}")
            raise
    
    async def read_file_content(self, repository: str, file_path: str, branch: str = "main") -> str:
        """Read specific file content from repository"""
        try:
            content_url = f"{self.base_url}/repos/{repository}/contents/{file_path}?ref={branch}"
            content_data = await self._make_request("GET", content_url)
            
            if content_data.get("content"):
                import base64
                return base64.b64decode(content_data["content"]).decode('utf-8')
            else:
                raise ValueError(f"No content found for {file_path}")
                
        except Exception as e:
            logger.error(f"Error reading file {file_path} from {repository}: {e}")
            raise
    
    async def create_branch(self, repository: str, new_branch: str, source_branch: str = "main") -> Dict:
        """Create a new branch from source branch"""
        try:
            # Get source branch SHA
            ref_url = f"{self.base_url}/repos/{repository}/git/ref/heads/{source_branch}"
            ref_data = await self._make_request("GET", ref_url)
            source_sha = ref_data["object"]["sha"]
            
            # Create new branch
            create_url = f"{self.base_url}/repos/{repository}/git/refs"
            create_data = {
                "ref": f"refs/heads/{new_branch}",
                "sha": source_sha
            }
            
            result = await self._make_request("POST", create_url, create_data)
            
            return {
                "branch": new_branch,
                "sha": result["object"]["sha"],
                "source_branch": source_branch,
                "source_sha": source_sha
            }
            
        except Exception as e:
            logger.error(f"Error creating branch {new_branch} in {repository}: {e}")
            raise
    
    async def commit_file_change(self, repository: str, file_path: str, content: str, 
                                commit_message: str, branch: str) -> Dict:
        """Commit a file change to repository"""
        try:
            # Get current file SHA if it exists
            file_sha = None
            try:
                content_url = f"{self.base_url}/repos/{repository}/contents/{file_path}?ref={branch}"
                existing_file = await self._make_request("GET", content_url)
                file_sha = existing_file.get("sha")
            except HTTPException as e:
                if e.status_code != 404:
                    raise
                # File doesn't exist, that's OK for new files
            
            # Commit the file
            commit_url = f"{self.base_url}/repos/{repository}/contents/{file_path}"
            commit_data = {
                "message": commit_message,
                "content": content.encode('utf-8').hex() if isinstance(content, str) else content,
                "branch": branch
            }
            
            if file_sha:
                commit_data["sha"] = file_sha
            
            # Convert content to base64
            import base64
            commit_data["content"] = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            result = await self._make_request("PUT", commit_url, commit_data)
            
            return {
                "file_path": file_path,
                "commit_sha": result["commit"]["sha"],
                "branch": branch,
                "message": commit_message
            }
            
        except Exception as e:
            logger.error(f"Error committing file {file_path} to {repository}: {e}")
            raise
    
    async def create_pull_request(self, repository: str, title: str, description: str,
                                 head_branch: str, base_branch: str = "main") -> Dict:
        """Create a pull request"""
        try:
            pr_url = f"{self.base_url}/repos/{repository}/pulls"
            pr_data = {
                "title": title,
                "body": description,
                "head": head_branch,
                "base": base_branch
            }
            
            result = await self._make_request("POST", pr_url, pr_data)
            
            return {
                "pr_number": result["number"],
                "pr_url": result["html_url"],
                "title": result["title"],
                "head_branch": head_branch,
                "base_branch": base_branch,
                "state": result["state"]
            }
            
        except Exception as e:
            logger.error(f"Error creating PR in {repository}: {e}")
            raise


class MCPCodeServer:
    """MCP Code Server for coding operations"""
    
    def __init__(self):
        self.github_tools = GitHubTools()
        self.app = FastAPI(
            title="MCP Code Server",
            description="Dedicated coding agent with GitHub integration",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "mcp-code-server", "timestamp": datetime.utcnow()}
        
        @self.app.post("/code/operation", response_model=CodeResponse)
        async def execute_code_operation(request: CodeRequest):
            """Execute code operation"""
            try:
                logger.info(f"Executing code operation: {request.operation}")
                
                if request.operation == "read_repo":
                    data = await self.github_tools.read_repository_structure(
                        request.repository, request.branch or "main"
                    )
                    
                elif request.operation == "read_file":
                    if not request.file_path:
                        raise ValueError("file_path required for read_file operation")
                    
                    content = await self.github_tools.read_file_content(
                        request.repository, request.file_path, request.branch or "main"
                    )
                    data = {"file_path": request.file_path, "content": content}
                    
                elif request.operation == "create_branch":
                    if not request.branch:
                        raise ValueError("branch name required for create_branch operation")
                    
                    data = await self.github_tools.create_branch(
                        request.repository, request.branch, "main"
                    )
                    
                elif request.operation == "commit_file":
                    if not all([request.file_path, request.content, request.commit_message, request.branch]):
                        raise ValueError("file_path, content, commit_message, and branch required for commit_file")
                    
                    data = await self.github_tools.commit_file_change(
                        request.repository, request.file_path, request.content,
                        request.commit_message, request.branch
                    )
                    
                elif request.operation == "create_pr":
                    if not all([request.pr_title, request.pr_description, request.branch]):
                        raise ValueError("pr_title, pr_description, and branch required for create_pr")
                    
                    data = await self.github_tools.create_pull_request(
                        request.repository, request.pr_title, request.pr_description, request.branch
                    )
                    
                else:
                    raise ValueError(f"Unknown operation: {request.operation}")
                
                return CodeResponse(
                    success=True,
                    operation=request.operation,
                    data=data,
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "repository": request.repository
                    }
                )
                
            except Exception as e:
                logger.error(f"Code operation failed: {e}")
                return CodeResponse(
                    success=False,
                    operation=request.operation,
                    error=str(e)
                )
        
        @self.app.get("/code/repositories")
        async def list_repositories():
            """List accessible repositories"""
            try:
                # This would typically list user's repositories
                # For now, return the sophia-intel repository
                return {
                    "repositories": [
                        {
                            "name": "ai-cherry/sophia-intel",
                            "description": "Sophia Intel AI Platform",
                            "private": True,
                            "default_branch": "main"
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Error listing repositories: {e}")
                raise HTTPException(status_code=500, detail=str(e))


def create_app() -> FastAPI:
    """Create and configure the MCP Code Server app"""
    server = MCPCodeServer()
    return server.app


if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault('GITHUB_PAT', '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')
    
    app = create_app()
    
    logger.info("Starting MCP Code Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )

