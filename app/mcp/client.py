#!/usr/bin/env python3
"""
MCP Bridge Client
Provides connection to MCP servers for AI agents
Ensures proper domain isolation between Sophia and 
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
import httpx
logger = logging.getLogger(__name__)
class MCPBridgeClient:
    """Client for connecting to MCP bridge servers"""
    def __init__(self, domain: str = ""):
        """
        Initialize MCP client
        Args:
            domain: Domain context (, sophia, or shared)
        """
        self.domain = domain
        self.connected = False
        # Get configuration from environment
        self.memory_host = os.getenv("MCP_MEMORY_HOST", "localhost")
        self.memory_port = int(os.getenv("MCP_MEMORY_PORT", 8765))
        self.bridge_port = int(os.getenv("MCP_BRIDGE_PORT", 8766))
        # Domain-specific endpoints
        self.endpoints = {
            "": {
                "memory": f"http://{self.memory_host}:{self.memory_port}/",
                "bridge": f"ws://{self.memory_host}:{self.bridge_port}/",
            },
            "sophia": {
                "memory": f"http://{self.memory_host}:{self.memory_port}/sophia",
                "bridge": f"ws://{self.memory_host}:{self.bridge_port}/sophia",
            },
            "shared": {
                "memory": f"http://{self.memory_host}:{self.memory_port}/shared",
                "bridge": f"ws://{self.memory_host}:{self.bridge_port}/shared",
            },
        }
        self.ws_connection = None
        self.http_client = httpx.AsyncClient()
    async def connect(self) -> bool:
        """Connect to MCP bridge"""
        if self.connected:
            return True
        try:
            # Test HTTP endpoint
            response = await self.http_client.get(
                f"{self.endpoints[self.domain]['memory']}/health"
            )
            if response.status_code == 200:
                self.connected = True
                logger.info(f"✅ Connected to MCP bridge ({self.domain} domain)")
                return True
            else:
                logger.error(
                    f"❌ MCP bridge health check failed: {response.status_code}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP bridge: {e}")
            return False
    async def disconnect(self):
        """Disconnect from MCP bridge"""
        if self.ws_connection:
            await self.ws_connection.close()
        await self.http_client.aclose()
        self.connected = False
        logger.info(f"Disconnected from MCP bridge ({self.domain} domain)")
    async def get_context(self, task_id: str) -> Dict[str, Any]:
        """
        Get context for a task from MCP memory
        Args:
            task_id: Unique task identifier
        Returns:
            Context dictionary
        """
        if not self.connected:
            await self.connect()
        try:
            response = await self.http_client.get(
                f"{self.endpoints[self.domain]['memory']}/context/{task_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"No context found for task {task_id}")
                return {}
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return {}
    async def save_result(self, task_id: str, result: Any) -> bool:
        """
        Save task result to MCP memory
        Args:
            task_id: Unique task identifier
            result: Result data to save
        Returns:
            Success status
        """
        if not self.connected:
            await self.connect()
        try:
            response = await self.http_client.post(
                f"{self.endpoints[self.domain]['memory']}/results/{task_id}",
                json={
                    "task_id": task_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "domain": self.domain,
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error saving result: {e}")
            return False
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search MCP memory
        Args:
            query: Search query
            limit: Maximum results
        Returns:
            List of search results
        """
        if not self.connected:
            await self.connect()
        try:
            response = await self.http_client.post(
                f"{self.endpoints[self.domain]['memory']}/search",
                json={"query": query, "limit": limit, "domain": self.domain},
            )
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    async def execute__task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task in  domain (for coding tasks)
        Args:
            request: Task request
        Returns:
            Task result
        """
        if self.domain != "":
            logger.warning("Switching to  domain for coding task")
            self.domain = ""
            self.connected = False
            await self.connect()
        task_id = request.get("id", f"task_{datetime.now().timestamp()}")
        # Get context
        context = await self.get_context(task_id)
        # Enrich request with context
        request["context"] = context
        request["domain"] = ""
        # Execute task (would call actual  service in production)
        result = {
            "task_id": task_id,
            "status": "completed",
            "domain": "",
            "result": request,
            "timestamp": datetime.now().isoformat(),
        }
        # Save result
        await self.save_result(task_id, result)
        return result
    async def execute_sophia_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task in Sophia domain (for business tasks)
        Args:
            request: Task request
        Returns:
            Task result
        """
        if self.domain != "sophia":
            logger.warning("Switching to Sophia domain for business task")
            self.domain = "sophia"
            self.connected = False
            await self.connect()
        task_id = request.get("id", f"task_{datetime.now().timestamp()}")
        # Get context
        context = await self.get_context(task_id)
        # Enrich request with context
        request["context"] = context
        request["domain"] = "sophia"
        # Execute task (would call actual Sophia service in production)
        result = {
            "task_id": task_id,
            "status": "completed",
            "domain": "sophia",
            "result": request,
            "timestamp": datetime.now().isoformat(),
        }
        # Save result
        await self.save_result(task_id, result)
        return result
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for text from shared domain
        Args:
            text: Text to embed
        Returns:
            Embedding vector
        """
        try:
            response = await self.http_client.post(
                f"{self.endpoints['shared']['memory']}/embeddings",
                json={"text": text, "domain": self.domain},
            )
            if response.status_code == 200:
                return response.json().get("embeddings", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return []
    async def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index document in shared knowledge base
        Args:
            document: Document to index
        Returns:
            Success status
        """
        try:
            response = await self.http_client.post(
                f"{self.endpoints['shared']['memory']}/index",
                json={
                    "document": document,
                    "domain": self.domain,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return False
# Convenience functions for direct usage
async def get__client() -> MCPBridgeClient:
    """Get client configured for  domain"""
    client = MCPBridgeClient(domain="")
    await client.connect()
    return client
async def get_sophia_client() -> MCPBridgeClient:
    """Get client configured for Sophia domain"""
    client = MCPBridgeClient(domain="sophia")
    await client.connect()
    return client
async def get_shared_client() -> MCPBridgeClient:
    """Get client configured for shared domain"""
    client = MCPBridgeClient(domain="shared")
    await client.connect()
    return client
