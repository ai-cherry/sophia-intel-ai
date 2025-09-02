
import httpx


class MCPAssistantCoordinator:
    """Manages authentication and API calls for external assistants"""

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.token = None

    async def initialize(self):
        """Authenticate and get JWT token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/initialize",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            self.token = response.json()["token"]

    async def memory_store(self, content: str, metadata: dict):
        """Store memory via MCP server"""
        return await self._call_mcp("memory/store", {
            "content": content,
            "metadata": metadata
        })

    async def memory_search(self, query: str, filters: dict = None):
        """Search memory via MCP server"""
        return await self._call_mcp("memory/search", {
            "query": query,
            "filters": filters or {}
        })

    async def _call_mcp(self, endpoint: str, data: dict):
        """Generic MCP API call"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
