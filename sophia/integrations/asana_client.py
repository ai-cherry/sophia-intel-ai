"""
Asana API Client
Production-ready client for Asana integration with SOPHIA.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import httpx
from sophia.core.constants import ENV_VARS, TIMEOUTS, RATE_LIMITS

logger = logging.getLogger(__name__)

@dataclass
class AsanaProject:
    """Represents an Asana project"""
    gid: str
    name: str
    team: Optional[str] = None
    archived: bool = False

@dataclass
class AsanaTask:
    """Represents an Asana task"""
    gid: str
    name: str
    notes: Optional[str] = None
    assignee: Optional[str] = None
    project: Optional[str] = None
    completed: bool = False
    due_on: Optional[str] = None
    permalink_url: Optional[str] = None

class AsanaClient:
    """
    Production-ready Asana API client with comprehensive error handling,
    rate limiting, retries, and timeout management.
    """
    
    def __init__(
        self, 
        token: Optional[str] = None, 
        timeout: int = TIMEOUTS["DEFAULT"]
    ):
        self.token = token or os.getenv("ASANA_ACCESS_TOKEN")
        
        if not self.token:
            raise EnvironmentError(
                "Missing required environment variable: ASANA_ACCESS_TOKEN"
            )
        
        self.base_url = "https://app.asana.com/api/1.0"
        self.timeout = timeout
        self.rate_limit = 150  # Asana allows 150 requests per minute
        
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "SOPHIA-AI-Orchestrator/1.1.0"
            }
        )
        
        # Rate limiting
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
    
    async def _rate_limit_check(self) -> None:
        """Enforce rate limiting"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < 60]
            
            if len(self._request_times) >= self.rate_limit:
                sleep_time = 60 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(now)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make HTTP request with retries and error handling"""
        await self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if attempt == retries:
                    logger.error(f"HTTP error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.RequestError as e:
                if attempt == retries:
                    logger.error(f"Request error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    async def get_me(self) -> Dict[str, Any]:
        """Get current user information (health check)"""
        try:
            response = await self._make_request("GET", "/users/me")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    async def list_projects(
        self, 
        workspace_gid: Optional[str] = None,
        team_gid: Optional[str] = None,
        archived: bool = False
    ) -> List[AsanaProject]:
        """
        List projects in workspace or team
        
        Args:
            workspace_gid: Workspace GID to filter by
            team_gid: Team GID to filter by
            archived: Include archived projects
        """
        params = {
            "archived": archived,
            "opt_fields": "name,team.name,archived"
        }
        
        if workspace_gid:
            params["workspace"] = workspace_gid
        if team_gid:
            params["team"] = team_gid
        
        try:
            response = await self._make_request("GET", "/projects", params=params)
            
            projects = []
            for project_data in response.get("data", []):
                project = AsanaProject(
                    gid=project_data["gid"],
                    name=project_data["name"],
                    team=project_data.get("team", {}).get("name"),
                    archived=project_data.get("archived", False)
                )
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise
    
    async def create_task(
        self,
        name: str,
        notes: Optional[str] = None,
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        due_on: Optional[str] = None,
        parent: Optional[str] = None
    ) -> AsanaTask:
        """
        Create a new task
        
        Args:
            name: Task name
            notes: Task description/notes
            assignee: Assignee GID
            project: Project GID
            due_on: Due date (YYYY-MM-DD format)
            parent: Parent task GID
        """
        task_data = {
            "data": {
                "name": name,
                "notes": notes or "",
                "opt_fields": "name,notes,assignee.name,projects.name,completed,due_on,permalink_url"
            }
        }
        
        if assignee:
            task_data["data"]["assignee"] = assignee
        if project:
            task_data["data"]["projects"] = [project]
        if due_on:
            task_data["data"]["due_on"] = due_on
        if parent:
            task_data["data"]["parent"] = parent
        
        try:
            response = await self._make_request("POST", "/tasks", json_data=task_data)
            task_info = response.get("data", {})
            
            task = AsanaTask(
                gid=task_info["gid"],
                name=task_info["name"],
                notes=task_info.get("notes"),
                assignee=task_info.get("assignee", {}).get("name"),
                project=task_info.get("projects", [{}])[0].get("name") if task_info.get("projects") else None,
                completed=task_info.get("completed", False),
                due_on=task_info.get("due_on"),
                permalink_url=task_info.get("permalink_url")
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def update_task(
        self,
        task_gid: str,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        completed: Optional[bool] = None,
        assignee: Optional[str] = None,
        due_on: Optional[str] = None
    ) -> AsanaTask:
        """Update an existing task"""
        task_data = {
            "data": {
                "opt_fields": "name,notes,assignee.name,projects.name,completed,due_on,permalink_url"
            }
        }
        
        if name is not None:
            task_data["data"]["name"] = name
        if notes is not None:
            task_data["data"]["notes"] = notes
        if completed is not None:
            task_data["data"]["completed"] = completed
        if assignee is not None:
            task_data["data"]["assignee"] = assignee
        if due_on is not None:
            task_data["data"]["due_on"] = due_on
        
        try:
            response = await self._make_request("PUT", f"/tasks/{task_gid}", json_data=task_data)
            task_info = response.get("data", {})
            
            task = AsanaTask(
                gid=task_info["gid"],
                name=task_info["name"],
                notes=task_info.get("notes"),
                assignee=task_info.get("assignee", {}).get("name"),
                project=task_info.get("projects", [{}])[0].get("name") if task_info.get("projects") else None,
                completed=task_info.get("completed", False),
                due_on=task_info.get("due_on"),
                permalink_url=task_info.get("permalink_url")
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to update task {task_gid}: {e}")
            raise
    
    async def list_tasks(
        self,
        project_gid: Optional[str] = None,
        assignee: Optional[str] = None,
        completed_since: Optional[str] = None,
        modified_since: Optional[str] = None
    ) -> List[AsanaTask]:
        """List tasks with filters"""
        params = {
            "opt_fields": "name,notes,assignee.name,projects.name,completed,due_on,permalink_url"
        }
        
        if project_gid:
            endpoint = f"/projects/{project_gid}/tasks"
        else:
            endpoint = "/tasks"
            if assignee:
                params["assignee"] = assignee
        
        if completed_since:
            params["completed_since"] = completed_since
        if modified_since:
            params["modified_since"] = modified_since
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            
            tasks = []
            for task_data in response.get("data", []):
                task = AsanaTask(
                    gid=task_data["gid"],
                    name=task_data["name"],
                    notes=task_data.get("notes"),
                    assignee=task_data.get("assignee", {}).get("name"),
                    project=task_data.get("projects", [{}])[0].get("name") if task_data.get("projects") else None,
                    completed=task_data.get("completed", False),
                    due_on=task_data.get("due_on"),
                    permalink_url=task_data.get("permalink_url")
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            user_info = await self.get_me()
            response_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "user_gid": user_info.get("gid"),
                "user_name": user_info.get("name"),
                "user_email": user_info.get("email"),
                "base_url": self.base_url,
                "rate_limit": self.rate_limit,
                "requests_in_last_minute": len(self._request_times)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "base_url": self.base_url
            }
    
    async def aclose(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

