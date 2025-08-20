"""
SOPHIA MCP Client
HTTP client for communicating with MCP servers.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import httpx
import asyncio

logger = logging.getLogger(__name__)

class SOPHIAMCPClient:
    """
    Client for communicating with SOPHIA MCP servers.
    Provides async HTTP interface to all MCP server endpoints.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize MCP client.
        
        Args:
            base_url: Base URL of MCP server (defaults to MCP_SERVER_URL env var)
        """
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Initialized MCP client with base URL: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    # Health and Status Methods
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health."""
        try:
            response = await self.client.get(f"{self.base_url}/healthz")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    # Code Server Methods
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Generate code using MCP code server."""
        try:
            payload = {
                "prompt": prompt,
                "language": language,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = await self.client.post(f"{self.base_url}/code/generate", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    async def search_code(
        self,
        query: str,
        filename: Optional[str] = None,
        function_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for code snippets."""
        try:
            params = {"query": query, "limit": limit}
            if filename:
                params["filename"] = filename
            if function_name:
                params["function_name"] = function_name
            
            response = await self.client.get(f"{self.base_url}/code/search", params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Code search failed: {e}")
            raise
    
    async def index_code(
        self,
        repository_url: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index code for search."""
        try:
            payload = {}
            if repository_url:
                payload["repository_url"] = repository_url
            if file_paths:
                payload["file_paths"] = file_paths
            if content:
                payload["content"] = content
            if metadata:
                payload["metadata"] = metadata
            
            response = await self.client.post(f"{self.base_url}/code/index", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Code indexing failed: {e}")
            raise
    
    async def evaluate_code(
        self,
        code: str,
        language: str,
        test_cases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Evaluate code for errors and performance."""
        try:
            payload = {
                "code": code,
                "language": language
            }
            if test_cases:
                payload["test_cases"] = test_cases
            
            response = await self.client.post(f"{self.base_url}/code/evaluate", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Code evaluation failed: {e}")
            raise
    
    # Context Server Methods
    async def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new context session."""
        try:
            payload = {}
            if user_id:
                payload["user_id"] = user_id
            if metadata:
                payload["metadata"] = metadata
            
            response = await self.client.post(f"{self.base_url}/context/sessions", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise
    
    async def get_session_context(
        self,
        session_id: str,
        limit: int = 50,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Get session context with messages."""
        try:
            params = {"limit": limit, "include_metadata": include_metadata}
            response = await self.client.get(f"{self.base_url}/context/sessions/{session_id}", params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            raise
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add message to session context."""
        try:
            payload = {
                "role": role,
                "content": content
            }
            if metadata:
                payload["metadata"] = metadata
            
            response = await self.client.post(f"{self.base_url}/context/sessions/{session_id}/messages", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Message addition failed: {e}")
            raise
    
    # Memory Server Methods
    async def store_embedding(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Store text as embedding."""
        try:
            payload = {
                "text": text,
                "collection_name": collection_name
            }
            if metadata:
                payload["metadata"] = metadata
            
            response = await self.client.post(f"{self.base_url}/memory/embeddings", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Embedding storage failed: {e}")
            raise
    
    async def search_embeddings(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Search for similar embeddings."""
        try:
            payload = {
                "query": query,
                "collection_name": collection_name,
                "top_k": top_k,
                "score_threshold": score_threshold
            }
            
            response = await self.client.post(f"{self.base_url}/memory/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            raise
    
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store memory item."""
        try:
            payload = {
                "content": content,
                "memory_type": memory_type
            }
            if session_id:
                payload["session_id"] = session_id
            if metadata:
                payload["metadata"] = metadata
            
            response = await self.client.post(f"{self.base_url}/memory/memories", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve memories based on query."""
        try:
            payload = {
                "query": query,
                "limit": limit
            }
            if memory_type:
                payload["memory_type"] = memory_type
            if session_id:
                payload["session_id"] = session_id
            
            response = await self.client.post(f"{self.base_url}/memory/memories/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            raise
    
    # Research Server Methods
    async def conduct_research(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 10,
        include_content: bool = True,
        summarize: bool = True
    ) -> Dict[str, Any]:
        """Conduct research across multiple sources."""
        try:
            payload = {
                "query": query,
                "max_results_per_source": max_results_per_source,
                "include_content": include_content,
                "summarize": summarize
            }
            if sources:
                payload["sources"] = sources
            
            response = await self.client.post(f"{self.base_url}/research/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            raise
    
    async def conduct_deep_research(
        self,
        topic: str,
        research_depth: str = "standard",
        focus_areas: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive deep research."""
        try:
            payload = {
                "topic": topic,
                "research_depth": research_depth
            }
            if focus_areas:
                payload["focus_areas"] = focus_areas
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains
            
            response = await self.client.post(f"{self.base_url}/research/deep-research", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            raise
    
    async def get_research_result(self, research_id: str) -> Dict[str, Any]:
        """Get stored research result."""
        try:
            response = await self.client.get(f"{self.base_url}/research/research/{research_id}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Research result retrieval failed: {e}")
            raise
    
    # Business Server Methods
    async def fetch_business_data(
        self,
        source: str,
        data_type: str,
        date_range: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch data from business source."""
        try:
            payload = {
                "source": source,
                "data_type": data_type
            }
            if date_range:
                payload["date_range"] = date_range
            if filters:
                payload["filters"] = filters
            
            response = await self.client.post(f"{self.base_url}/business/data", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Business data fetch failed: {e}")
            raise
    
    async def get_customer_insights(
        self,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        include_calls: bool = True,
        include_emails: bool = True,
        include_deals: bool = True,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive customer insights."""
        try:
            payload = {
                "include_calls": include_calls,
                "include_emails": include_emails,
                "include_deals": include_deals,
                "days_back": days_back
            }
            if customer_id:
                payload["customer_id"] = customer_id
            if customer_email:
                payload["customer_email"] = customer_email
            
            response = await self.client.post(f"{self.base_url}/business/customer-insights", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Customer insights failed: {e}")
            raise
    
    async def get_sales_metrics(
        self,
        metric_types: List[str],
        time_period: str = "monthly",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get sales performance metrics."""
        try:
            payload = {
                "metric_types": metric_types,
                "time_period": time_period
            }
            if date_range:
                payload["date_range"] = date_range
            
            response = await self.client.post(f"{self.base_url}/business/sales-metrics", json=payload)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Sales metrics failed: {e}")
            raise

