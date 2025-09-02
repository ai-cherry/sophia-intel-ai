from app.mcp.assistant_coordinator import MCPAssistantCoordinator


class PythonAgentClient:
    """Python client for custom agents and swarms"""

    def __init__(self, server_url: str, api_key: str):
        self.coordinator = MCPAssistantCoordinator(server_url, api_key)

    async def initialize(self):
        await self.coordinator.initialize()

    async def store_memory(self, content: str, metadata: dict):
        return await self.coordinator.memory_store(content, metadata)

    async def search_memory(self, query: str, filters: dict = None):
        return await self.coordinator.memory_search(query, filters)
