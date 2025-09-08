"""
MCP Memory Client - Python client for the MCP Memory Server
"""

import json
import httpx
from typing import Dict, List, Any, Optional

class MCPMemoryClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the MCP Memory Server"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()

    async def store_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store an item in memory"""
        payload = {"key": key, "value": value}
        if ttl is not None:
            payload["ttl"] = ttl

        response = await self.client.post(f"{self.base_url}/memory/store", json=payload)
        return response.json()

    async def retrieve_memory(self, key: str) -> Dict[str, Any]:
        """Retrieve an item from memory by key"""
        response = await self.client.get(f"{self.base_url}/memory/{key}")
        return response.json()

    async def delete_memory(self, key: str) -> Dict[str, Any]:
        """Delete an item from memory"""
        response = await self.client.delete(f"{self.base_url}/memory/{key}")
        return response.json()

    async def store_vector(self, text: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Store a vector embedding"""
        payload = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        }

        response = await self.client.post(f"{self.base_url}/vector/store", json=payload)
        return response.json()

    async def search_vector(self, embedding: List[float], limit: int = 10) -> Dict[str, Any]:
        """Search for similar vectors"""
        payload = {
            "text": "",  # Placeholder
            "embedding": embedding,
            "metadata": {"limit": limit}
        }

        response = await self.client.post(f"{self.base_url}/vector/search", json=payload)
        return response.json()

    async def store_context(self, agent_id: str, context_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Store context information"""
        payload = {
            "agent_id": agent_id,
            "context_type": context_type,
            "content": content
        }

        response = await self.client.post(f"{self.base_url}/context/store", json=payload)
        return response.json()

    async def get_context(self, agent_id: str, context_type: str) -> Dict[str, Any]:
        """Retrieve context for a specific agent and type"""
        response = await self.client.get(f"{self.base_url}/context/{agent_id}/{context_type}")
        return response.json()

    # Synchronous version of the client for simpler usage
    @classmethod
    def sync(cls, base_url: str = "http://localhost:8001"):
        """Create a synchronous version of the client"""
        return MCPMemoryClientSync(base_url)

class MCPMemoryClientSync:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the MCP Memory Server"""
        response = self.client.get(f"{self.base_url}/health")
        return response.json()

    def store_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store an item in memory"""
        payload = {"key": key, "value": value}
        if ttl is not None:
            payload["ttl"] = ttl

        response = self.client.post(f"{self.base_url}/memory/store", json=payload)
        return response.json()

    def retrieve_memory(self, key: str) -> Dict[str, Any]:
        """Retrieve an item from memory by key"""
        response = self.client.get(f"{self.base_url}/memory/{key}")
        return response.json()

    def delete_memory(self, key: str) -> Dict[str, Any]:
        """Delete an item from memory"""
        response = self.client.delete(f"{self.base_url}/memory/{key}")
        return response.json()

    def store_vector(self, text: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Store a vector embedding"""
        payload = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        }

        response = self.client.post(f"{self.base_url}/vector/store", json=payload)
        return response.json()

    def search_vector(self, embedding: List[float], limit: int = 10) -> Dict[str, Any]:
        """Search for similar vectors"""
        payload = {
            "text": "",  # Placeholder
            "embedding": embedding,
            "metadata": {"limit": limit}
        }

        response = self.client.post(f"{self.base_url}/vector/search", json=payload)
        return response.json()

    def store_context(self, agent_id: str, context_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Store context information"""
        payload = {
            "agent_id": agent_id,
            "context_type": context_type,
            "content": content
        }

        response = self.client.post(f"{self.base_url}/context/store", json=payload)
        return response.json()

    def get_context(self, agent_id: str, context_type: str) -> Dict[str, Any]:
        """Retrieve context for a specific agent and type"""
        response = self.client.get(f"{self.base_url}/context/{agent_id}/{context_type}")
        return response.json()
