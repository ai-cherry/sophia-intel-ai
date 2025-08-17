"""
Notion Integration Service for SOPHIA Intel
Provides deep integration with Notion for knowledge management and documentation
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel

from config.config import settings


class NotionSearchRequest(BaseModel):
    query: str
    database_id: Optional[str] = None
    filter_criteria: Optional[Dict[str, Any]] = None
    max_results: int = 20


class NotionCreatePageRequest(BaseModel):
    database_id: str
    title: str
    content: str
    properties: Optional[Dict[str, Any]] = None


class NotionService:
    """
    Notion integration service for knowledge management
    """

    def __init__(self):
        self.api_key = getattr(settings, "NOTION_API_KEY", "")
        self.knowledge_db_id = getattr(settings, "NOTION_KNOWLEDGE_DB_ID", "")
        self.principles_db_id = getattr(settings, "NOTION_PRINCIPLES_DB_ID", "")
        self.base_url = "https://api.notion.com/v1"

        # Cache for database schemas and results
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def search_databases(
        self, query: str, database_id: Optional[str] = None, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search Notion databases for pages matching the query
        """
        try:
            if not self.api_key:
                raise ValueError("Notion API key not configured")

            # Use knowledge database if no specific database provided
            target_db = database_id or self.knowledge_db_id
            if not target_db:
                raise ValueError("No Notion database ID configured")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            # Search using Notion's database query endpoint
            search_payload = {
                "filter": {
                    "or": [
                        {"property": "Name", "title": {"contains": query}},
                        {"property": "Content", "rich_text": {"contains": query}},
                    ]
                },
                "page_size": min(max_results, 100),
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{target_db}/query", headers=headers, json=search_payload
                )
                response.raise_for_status()
                data = response.json()

                # Format results
                results = []
                for page in data.get("results", []):
                    formatted_page = await self._format_page_result(page)
                    if formatted_page:
                        results.append(formatted_page)

                return results

        except Exception as e:
            logger.error(f"Notion database search failed: {e}")
            return []

    async def create_page(
        self, database_id: str, title: str, content: str, properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new page in a Notion database
        """
        try:
            if not self.api_key:
                raise ValueError("Notion API key not configured")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            # Prepare page properties
            page_properties = {"Name": {"title": [{"text": {"content": title}}]}}

            # Add custom properties if provided
            if properties:
                page_properties.update(properties)

            # Prepare page content as blocks
            content_blocks = []
            if content:
                # Split content into paragraphs and create blocks
                paragraphs = content.split("\\n\\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        content_blocks.append(
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {"rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]},
                            }
                        )

            page_payload = {
                "parent": {"database_id": database_id},
                "properties": page_properties,
                "children": content_blocks,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/pages", headers=headers, json=page_payload)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Notion page creation failed: {e}")
            raise

    async def get_pending_principles(self) -> List[Dict[str, Any]]:
        """
        Get pending canonical principles from Notion
        """
        try:
            if not self.principles_db_id:
                return []

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            # Query for pending principles
            query_payload = {
                "filter": {"property": "Status", "select": {"equals": "Pending"}},
                "sorts": [{"property": "Created", "direction": "descending"}],
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{self.principles_db_id}/query", headers=headers, json=query_payload
                )
                response.raise_for_status()
                data = response.json()

                # Format results
                principles = []
                for page in data.get("results", []):
                    formatted_principle = await self._format_principle_result(page)
                    if formatted_principle:
                        principles.append(formatted_principle)

                return principles

        except Exception as e:
            logger.error(f"Failed to get pending principles: {e}")
            return []

    async def approve_principle(self, page_id: str) -> Dict[str, Any]:
        """
        Approve a canonical principle by updating its status
        """
        try:
            if not self.api_key:
                raise ValueError("Notion API key not configured")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            update_payload = {
                "properties": {
                    "Status": {"select": {"name": "Approved"}},
                    "Approved Date": {"date": {"start": datetime.now().isoformat()}},
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(f"{self.base_url}/pages/{page_id}", headers=headers, json=update_payload)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to approve principle: {e}")
            raise

    async def query_database(
        self, database_id: str, filter_criteria: Optional[Dict[str, Any]] = None, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query a Notion database with optional filters
        """
        try:
            if not self.api_key:
                raise ValueError("Notion API key not configured")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            query_payload = {"page_size": min(max_results, 100)}

            if filter_criteria:
                query_payload["filter"] = filter_criteria

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{database_id}/query", headers=headers, json=query_payload
                )
                response.raise_for_status()
                data = response.json()

                # Format results
                results = []
                for page in data.get("results", []):
                    formatted_page = await self._format_page_result(page)
                    if formatted_page:
                        results.append(formatted_page)

                return results

        except Exception as e:
            logger.error(f"Notion database query failed: {e}")
            return []

    async def get_page_content(self, page_id: str) -> str:
        """
        Get the full content of a Notion page
        """
        try:
            if not self.api_key:
                raise ValueError("Notion API key not configured")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get page blocks
                response = await client.get(f"{self.base_url}/blocks/{page_id}/children", headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract text content from blocks
                content_parts = []
                for block in data.get("results", []):
                    text = self._extract_text_from_block(block)
                    if text:
                        content_parts.append(text)

                return "\\n\\n".join(content_parts)

        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return ""

    async def _format_page_result(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format a Notion page result for consistent output
        """
        try:
            properties = page.get("properties", {})

            # Extract title
            title = ""
            if "Name" in properties:
                title_prop = properties["Name"]
                if title_prop.get("title"):
                    title = "".join([t.get("plain_text", "") for t in title_prop["title"]])

            # Extract other properties
            content = ""
            tags = []
            created_time = page.get("created_time", "")

            # Try to get content from rich text properties
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "rich_text" and prop_data.get("rich_text"):
                    prop_content = "".join([t.get("plain_text", "") for t in prop_data["rich_text"]])
                    if prop_content and prop_name.lower() in ["content", "description", "summary"]:
                        content = prop_content
                        break

            # Extract tags from multi-select properties
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "multi_select":
                    tags.extend([tag.get("name", "") for tag in prop_data.get("multi_select", [])])

            return {
                "id": page.get("id", ""),
                "title": title,
                "content": content,
                "url": page.get("url", ""),
                "created_time": created_time,
                "tags": tags,
                "source": "notion",
            }

        except Exception as e:
            logger.warning(f"Failed to format page result: {e}")
            return None

    async def _format_principle_result(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format a canonical principle result
        """
        try:
            properties = page.get("properties", {})

            # Extract principle details
            title = ""
            description = ""
            category = ""
            status = ""

            if "Name" in properties and properties["Name"].get("title"):
                title = "".join([t.get("plain_text", "") for t in properties["Name"]["title"]])

            if "Description" in properties and properties["Description"].get("rich_text"):
                description = "".join([t.get("plain_text", "") for t in properties["Description"]["rich_text"]])

            if "Category" in properties and properties["Category"].get("select"):
                category = properties["Category"]["select"].get("name", "")

            if "Status" in properties and properties["Status"].get("select"):
                status = properties["Status"]["select"].get("name", "")

            return {
                "id": page.get("id", ""),
                "title": title,
                "description": description,
                "category": category,
                "status": status,
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to format principle result: {e}")
            return None

    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """
        Extract text content from a Notion block
        """
        try:
            block_type = block.get("type", "")

            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                return "".join([t.get("plain_text", "") for t in rich_text])

            elif block_type == "heading_1":
                rich_text = block.get("heading_1", {}).get("rich_text", [])
                return "# " + "".join([t.get("plain_text", "") for t in rich_text])

            elif block_type == "heading_2":
                rich_text = block.get("heading_2", {}).get("rich_text", [])
                return "## " + "".join([t.get("plain_text", "") for t in rich_text])

            elif block_type == "heading_3":
                rich_text = block.get("heading_3", {}).get("rich_text", [])
                return "### " + "".join([t.get("plain_text", "") for t in rich_text])

            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                return "• " + "".join([t.get("plain_text", "") for t in rich_text])

            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                return "1. " + "".join([t.get("plain_text", "") for t in rich_text])

            return ""

        except Exception as e:
            logger.warning(f"Failed to extract text from block: {e}")
            return ""
