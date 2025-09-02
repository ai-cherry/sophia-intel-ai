from app.memory.supermemory_mcp import SupermemoryStore

class UnifiedMemoryStore:
    """Unified interface for memory operations"""
    
    def __init__(self, config: dict):
        self.supermemory = SupermemoryStore(config)
    
    async def initialize(self):
        await self.supermemory.initialize()
    
    async def store_memory(self, content: str, metadata: dict):
        return await self.supermemory.add_memory(content, metadata)
    
    async def search_memory(self, query: str, filters: dict = None):
        return await self.supermemory.search_memory(query, filters or {})
    
    async def update_memory(self, memory_id: str, content: str, metadata: dict):
        # Implementation using SupermemoryStore
        pass
    
    async def delete_memory(self, memory_id: str):
        # Implementation using SupermemoryStore
        pass