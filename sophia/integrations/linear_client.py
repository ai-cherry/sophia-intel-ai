"""
Linear API Client
Production-ready client for Linear integration with SOPHIA.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import httpx
from sophia.core.constants import ENV_VARS, TIMEOUTS

logger = logging.getLogger(__name__)

@dataclass
class LinearTeam:
    """Represents a Linear team"""
    id: str
    name: str
    key: str
    description: Optional[str] = None

@dataclass
class LinearIssue:
    """Represents a Linear issue"""
    id: str
    identifier: str
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    team: Optional[str] = None
    state: Optional[str] = None
    priority: Optional[int] = None
    url: Optional[str] = None
    created_at: Optional[str] = None

class LinearClient:
    """
    Production-ready Linear API client using GraphQL with comprehensive 
    error handling, rate limiting, retries, and timeout management.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        timeout: int = TIMEOUTS["DEFAULT"]
    ):
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        
        if not self.api_key:
            raise EnvironmentError(
                "Missing required environment variable: LINEAR_API_KEY"
            )
        
        self.base_url = "https://api.linear.app/graphql"
        self.timeout = timeout
        self.rate_limit = 1800  # Linear allows 1800 requests per hour
        
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "SOPHIA-AI-Orchestrator/1.1.0"
            }
        )
        
        # Rate limiting
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
    
    async def _rate_limit_check(self) -> None:
        """Enforce rate limiting (1800 requests per hour)"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Remove requests older than 1 hour
            self._request_times = [t for t in self._request_times if now - t < 3600]
            
            if len(self._request_times) >= self.rate_limit:
                sleep_time = 3600 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(now)
    
    async def _make_request(
        self, 
        query: str, 
        variables: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make GraphQL request with retries and error handling"""
        await self._rate_limit_check()
        
        json_data = {
            "query": query,
            "variables": variables or {}
        }
        
        for attempt in range(retries + 1):
            try:
                response = await self._client.post(
                    self.base_url,
                    json=json_data
                )
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result
                
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
    
    async def get_viewer(self) -> Dict[str, Any]:
        """Get current user information (health check)"""
        query = """
        query {
            viewer {
                id
                name
                email
                displayName
            }
        }
        """
        
        try:
            response = await self._make_request(query)
            return response.get("data", {}).get("viewer", {})
        except Exception as e:
            logger.error(f"Failed to get viewer info: {e}")
            raise
    
    async def list_teams(self) -> List[LinearTeam]:
        """List all teams"""
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        
        try:
            response = await self._make_request(query)
            teams_data = response.get("data", {}).get("teams", {}).get("nodes", [])
            
            teams = []
            for team_data in teams_data:
                team = LinearTeam(
                    id=team_data["id"],
                    name=team_data["name"],
                    key=team_data["key"],
                    description=team_data.get("description")
                )
                teams.append(team)
            
            return teams
            
        except Exception as e:
            logger.error(f"Failed to list teams: {e}")
            raise
    
    async def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None
    ) -> LinearIssue:
        """
        Create a new issue
        
        Args:
            title: Issue title
            description: Issue description
            team_id: Team ID to create issue in
            assignee_id: Assignee user ID
            priority: Priority level (0=No priority, 1=Urgent, 2=High, 3=Normal, 4=Low)
            state_id: State ID for the issue
        """
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    assignee {
                        name
                    }
                    team {
                        name
                    }
                    state {
                        name
                    }
                    priority
                    url
                    createdAt
                }
            }
        }
        """
        
        variables = {
            "input": {
                "title": title,
                "description": description or "",
            }
        }
        
        if team_id:
            variables["input"]["teamId"] = team_id
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id
        if priority is not None:
            variables["input"]["priority"] = priority
        if state_id:
            variables["input"]["stateId"] = state_id
        
        try:
            response = await self._make_request(query, variables)
            issue_data = response.get("data", {}).get("issueCreate", {}).get("issue", {})
            
            if not issue_data:
                raise Exception("Failed to create issue")
            
            issue = LinearIssue(
                id=issue_data["id"],
                identifier=issue_data["identifier"],
                title=issue_data["title"],
                description=issue_data.get("description"),
                assignee=issue_data.get("assignee", {}).get("name"),
                team=issue_data.get("team", {}).get("name"),
                state=issue_data.get("state", {}).get("name"),
                priority=issue_data.get("priority"),
                url=issue_data.get("url"),
                created_at=issue_data.get("createdAt")
            )
            
            return issue
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise
    
    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None
    ) -> LinearIssue:
        """Update an existing issue"""
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    assignee {
                        name
                    }
                    team {
                        name
                    }
                    state {
                        name
                    }
                    priority
                    url
                    createdAt
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "input": {}
        }
        
        if title is not None:
            variables["input"]["title"] = title
        if description is not None:
            variables["input"]["description"] = description
        if assignee_id is not None:
            variables["input"]["assigneeId"] = assignee_id
        if priority is not None:
            variables["input"]["priority"] = priority
        if state_id is not None:
            variables["input"]["stateId"] = state_id
        
        try:
            response = await self._make_request(query, variables)
            issue_data = response.get("data", {}).get("issueUpdate", {}).get("issue", {})
            
            issue = LinearIssue(
                id=issue_data["id"],
                identifier=issue_data["identifier"],
                title=issue_data["title"],
                description=issue_data.get("description"),
                assignee=issue_data.get("assignee", {}).get("name"),
                team=issue_data.get("team", {}).get("name"),
                state=issue_data.get("state", {}).get("name"),
                priority=issue_data.get("priority"),
                url=issue_data.get("url"),
                created_at=issue_data.get("createdAt")
            )
            
            return issue
            
        except Exception as e:
            logger.error(f"Failed to update issue {issue_id}: {e}")
            raise
    
    async def list_issues(
        self,
        team_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state_name: Optional[str] = None,
        limit: int = 50
    ) -> List[LinearIssue]:
        """List issues with filters"""
        query = """
        query Issues($filter: IssueFilter, $first: Int) {
            issues(filter: $filter, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    description
                    assignee {
                        name
                    }
                    team {
                        name
                    }
                    state {
                        name
                    }
                    priority
                    url
                    createdAt
                }
            }
        }
        """
        
        filter_conditions = {}
        if team_id:
            filter_conditions["team"] = {"id": {"eq": team_id}}
        if assignee_id:
            filter_conditions["assignee"] = {"id": {"eq": assignee_id}}
        if state_name:
            filter_conditions["state"] = {"name": {"eq": state_name}}
        
        variables = {
            "filter": filter_conditions,
            "first": limit
        }
        
        try:
            response = await self._make_request(query, variables)
            issues_data = response.get("data", {}).get("issues", {}).get("nodes", [])
            
            issues = []
            for issue_data in issues_data:
                issue = LinearIssue(
                    id=issue_data["id"],
                    identifier=issue_data["identifier"],
                    title=issue_data["title"],
                    description=issue_data.get("description"),
                    assignee=issue_data.get("assignee", {}).get("name"),
                    team=issue_data.get("team", {}).get("name"),
                    state=issue_data.get("state", {}).get("name"),
                    priority=issue_data.get("priority"),
                    url=issue_data.get("url"),
                    created_at=issue_data.get("createdAt")
                )
                issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to list issues: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            viewer_info = await self.get_viewer()
            response_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "user_id": viewer_info.get("id"),
                "user_name": viewer_info.get("name"),
                "user_email": viewer_info.get("email"),
                "base_url": self.base_url,
                "rate_limit": self.rate_limit,
                "requests_in_last_hour": len(self._request_times)
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

