"""
Notion API Client
Production-ready client for Notion integration with SOPHIA.
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
class NotionDatabase:
    """Represents a Notion database"""
    id: str
    title: str
    url: Optional[str] = None
    created_time: Optional[str] = None
    last_edited_time: Optional[str] = None

@dataclass
class NotionPage:
    """Represents a Notion page"""
    id: str
    title: str
    url: Optional[str] = None
    parent_id: Optional[str] = None
    created_time: Optional[str] = None
    last_edited_time: Optional[str] = None

class NotionClient:
    """
    Production-ready Notion API client with comprehensive error handling,
    rate limiting, retries, and timeout management.
    """
    
    def __init__(
        self, 
        token: Optional[str] = None, 
        timeout: int = TIMEOUTS["DEFAULT"]
    ):
        self.token = token or os.getenv("NOTION_API_KEY")
        
        if not self.token:
            raise EnvironmentError(
                "Missing required environment variable: NOTION_API_KEY"
            )
        
        self.base_url = "https://api.notion.com/v1"
        self.timeout = timeout
        self.rate_limit = 3  # Notion allows 3 requests per second
        
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
                "User-Agent": "SOPHIA-AI-Orchestrator/1.1.0"
            }
        )
        
        # Rate limiting (3 requests per second)
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
    
    async def _rate_limit_check(self) -> None:
        """Enforce rate limiting (3 requests per second)"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Remove requests older than 1 second
            self._request_times = [t for t in self._request_times if now - t < 1]
            
            if len(self._request_times) >= self.rate_limit:
                sleep_time = 1 - (now - self._request_times[0])
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
                    retry_after = int(response.headers.get("Retry-After", 1))
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
        """Get bot information (health check)"""
        try:
            return await self._make_request("GET", "/users/me")
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            raise
    
    async def list_databases(
        self, 
        start_cursor: Optional[str] = None,
        page_size: int = 100
    ) -> List[NotionDatabase]:
        """
        List databases accessible to the integration
        
        Args:
            start_cursor: Cursor for pagination
            page_size: Number of results per page (max 100)
        """
        json_data = {
            "page_size": min(page_size, 100)
        }
        
        if start_cursor:
            json_data["start_cursor"] = start_cursor
        
        try:
            response = await self._make_request("POST", "/search", json_data=json_data)
            
            databases = []
            for result in response.get("results", []):
                if result.get("object") == "database":
                    title = ""
                    if result.get("title"):
                        title = "".join([t.get("plain_text", "") for t in result["title"]])
                    
                    database = NotionDatabase(
                        id=result["id"],
                        title=title,
                        url=result.get("url"),
                        created_time=result.get("created_time"),
                        last_edited_time=result.get("last_edited_time")
                    )
                    databases.append(database)
            
            return databases
            
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            raise
    
    async def create_page(
        self,
        parent_id: str,
        title: str,
        content: Optional[str] = None,
        is_database_parent: bool = True
    ) -> NotionPage:
        """
        Create a new page
        
        Args:
            parent_id: Parent database or page ID
            title: Page title
            content: Page content (markdown-like)
            is_database_parent: Whether parent is a database (True) or page (False)
        """
        # Build parent object
        if is_database_parent:
            parent = {"database_id": parent_id}
        else:
            parent = {"page_id": parent_id}
        
        # Build properties (for database pages)
        properties = {}
        if is_database_parent:
            properties["Name"] = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        
        # Build children (content blocks)
        children = []
        if content:
            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": paragraph.strip()
                                    }
                                }
                            ]
                        }
                    })
        
        page_data = {
            "parent": parent,
            "properties": properties,
            "children": children
        }
        
        # For non-database pages, set title differently
        if not is_database_parent:
            page_data["properties"] = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        
        try:
            response = await self._make_request("POST", "/pages", json_data=page_data)
            
            # Extract title from properties
            page_title = title
            if response.get("properties", {}).get("Name"):
                title_prop = response["properties"]["Name"]
                if title_prop.get("title"):
                    page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
            elif response.get("properties", {}).get("title"):
                title_prop = response["properties"]["title"]
                if title_prop.get("title"):
                    page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
            
            page = NotionPage(
                id=response["id"],
                title=page_title,
                url=response.get("url"),
                parent_id=parent_id,
                created_time=response.get("created_time"),
                last_edited_time=response.get("last_edited_time")
            )
            
            return page
            
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise
    
    async def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        archived: Optional[bool] = None
    ) -> NotionPage:
        """Update an existing page"""
        page_data = {}
        
        if title is not None:
            page_data["properties"] = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        
        if archived is not None:
            page_data["archived"] = archived
        
        try:
            response = await self._make_request("PATCH", f"/pages/{page_id}", json_data=page_data)
            
            # Extract title from properties
            page_title = ""
            if response.get("properties", {}).get("Name"):
                title_prop = response["properties"]["Name"]
                if title_prop.get("title"):
                    page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
            elif response.get("properties", {}).get("title"):
                title_prop = response["properties"]["title"]
                if title_prop.get("title"):
                    page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
            
            page = NotionPage(
                id=response["id"],
                title=page_title,
                url=response.get("url"),
                created_time=response.get("created_time"),
                last_edited_time=response.get("last_edited_time")
            )
            
            return page
            
        except Exception as e:
            logger.error(f"Failed to update page {page_id}: {e}")
            raise
    
    async def append_block_children(
        self,
        block_id: str,
        children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Append content blocks to a page or block"""
        json_data = {
            "children": children
        }
        
        try:
            return await self._make_request("PATCH", f"/blocks/{block_id}/children", json_data=json_data)
        except Exception as e:
            logger.error(f"Failed to append blocks to {block_id}: {e}")
            raise
    
    async def search_pages(
        self,
        query: str,
        filter_type: Optional[str] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100
    ) -> List[NotionPage]:
        """Search for pages and databases"""
        json_data = {
            "query": query,
            "page_size": min(page_size, 100)
        }
        
        if filter_type:
            json_data["filter"] = {
                "value": filter_type,
                "property": "object"
            }
        
        if start_cursor:
            json_data["start_cursor"] = start_cursor
        
        try:
            response = await self._make_request("POST", "/search", json_data=json_data)
            
            pages = []
            for result in response.get("results", []):
                if result.get("object") == "page":
                    # Extract title
                    page_title = ""
                    if result.get("properties", {}).get("Name"):
                        title_prop = result["properties"]["Name"]
                        if title_prop.get("title"):
                            page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
                    elif result.get("properties", {}).get("title"):
                        title_prop = result["properties"]["title"]
                        if title_prop.get("title"):
                            page_title = "".join([t.get("plain_text", "") for t in title_prop["title"]])
                    
                    page = NotionPage(
                        id=result["id"],
                        title=page_title,
                        url=result.get("url"),
                        created_time=result.get("created_time"),
                        last_edited_time=result.get("last_edited_time")
                    )
                    pages.append(page)
            
            return pages
            
        except Exception as e:
            logger.error(f"Failed to search pages: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            bot_info = await self.get_me()
            response_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "bot_id": bot_info.get("id"),
                "bot_name": bot_info.get("name"),
                "bot_type": bot_info.get("type"),
                "base_url": self.base_url,
                "rate_limit": self.rate_limit,
                "requests_in_last_second": len(self._request_times)
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

