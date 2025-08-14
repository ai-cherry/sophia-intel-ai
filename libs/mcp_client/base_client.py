"""
Base MCP Client Library
Provides standardized interface for MCP service integration with Swarm system
"""
import os
import time
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from loguru import logger


@dataclass
class SearchResult:
    """Standardized search result from MCP services"""
    id: str
    content: str
    score: float
    service: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class MCPServiceConfig:
    """Configuration for MCP service connection"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 300  # 5 minutes
    
    @classmethod
    def from_env(cls, service_name: str) -> 'MCPServiceConfig':
        """Create config from environment variables"""
        service_upper = service_name.upper()
        return cls(
            base_url=os.getenv(f"{service_upper}_MCP_URL", f"http://localhost:800{hash(service_name) % 100}"),
            api_key=os.getenv(f"{service_upper}_API_KEY"),
            timeout=int(os.getenv(f"{service_upper}_TIMEOUT", "30")),
            max_retries=int(os.getenv(f"{service_upper}_MAX_RETRIES", "3")),
            circuit_breaker_threshold=int(os.getenv(f"{service_upper}_CB_THRESHOLD", "3")),
            circuit_breaker_timeout=int(os.getenv(f"{service_upper}_CB_TIMEOUT", "300"))
        )


class CircuitBreakerState:
    """Circuit breaker implementation for service resilience"""
    
    def __init__(self, threshold: int = 3, timeout: int = 300):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = "OPEN"


class BaseMCPClient(ABC):
    """
    Base MCP Client with standardized interface
    
    Features:
    - Service discovery and health checking
    - Circuit breaker pattern for resilience
    - Standardized search and context operations
    - Swarm integration with session management
    - Performance monitoring and caching
    """
    
    def __init__(self, service_name: str, config: Optional[MCPServiceConfig] = None):
        self.service_name = service_name
        self.config = config or MCPServiceConfig.from_env(service_name)
        self.circuit_breaker = CircuitBreakerState(
            self.config.circuit_breaker_threshold,
            self.config.circuit_breaker_timeout
        )
        self.session = None
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "cache_hits": 0
        }
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Swarm integration fields
        self.swarm_stage = None
        self.session_id = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {"User-Agent": f"Sophia-MCP-Client/{self.service_name}"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def _make_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with circuit breaker and retry logic"""
        if not self.circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for {self.service_name}")
            return None
        
        url = f"{self.config.base_url.rstrip('/')}{path}"
        start_time = time.time()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                session = await self._get_session()
                
                if method.upper() == "GET":
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            self._record_success(time.time() - start_time)
                            return result
                        elif response.status == 404:
                            return None  # Not found is not a failure
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
                
                elif method.upper() == "POST":
                    async with session.post(url, params=params, json=json_data) as response:
                        if response.status in [200, 201]:
                            result = await response.json()
                            self._record_success(time.time() - start_time)
                            return result
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
                            
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {self.service_name}: {e}")
                if attempt == self.config.max_retries:
                    self._record_failure()
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _record_success(self, response_time: float):
        """Record successful request metrics"""
        self.circuit_breaker.record_success()
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["successful_requests"] += 1
        
        # Update average response time
        total = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def _record_failure(self):
        """Record failed request metrics"""
        self.circuit_breaker.record_failure()
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["failed_requests"] += 1
    
    async def health_check(self) -> bool:
        """Check service health"""
        try:
            result = await self._make_request("GET", "/health")
            return result is not None and result.get("status") == "healthy"
        except Exception:
            return False
    
    async def semantic_search(
        self, 
        query: str, 
        k: int = 8, 
        swarm_stage: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search across service content
        
        Args:
            query: Search query
            k: Number of results to return
            swarm_stage: Current Swarm stage for context-aware search
            filters: Service-specific filters
            
        Returns:
            List of SearchResult objects
        """
        # Check cache first
        cache_key = f"{query}_{k}_{swarm_stage}_{filters}"
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.performance_metrics["cache_hits"] += 1
                return cache_entry["results"]
        
        # Prepare search parameters
        params = {
            "query": query,
            "k": k
        }
        if swarm_stage:
            params["swarm_stage"] = swarm_stage
        if filters:
            params.update(self._get_service_filters(filters))
        
        try:
            response = await self._make_request("GET", "/search", params)
            if not response:
                return []
            
            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    id=item.get("id", f"{self.service_name}_{hash(item.get('content', ''))}"),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    service=self.service_name,
                    metadata=item.get("metadata", {}),
                    timestamp=time.time()
                )
                results.append(result)
            
            # Cache results
            self.search_cache[cache_key] = {
                "results": results,
                "timestamp": time.time()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed for {self.service_name}: {e}")
            return []
    
    async def store_context(
        self,
        content: str,
        context_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store context for future retrieval"""
        try:
            payload = {
                "content": content,
                "context_type": context_type,
                "service": self.service_name,
                "metadata": {
                    **(metadata or {}),
                    **self._get_context_fields(),
                    "timestamp": time.time()
                }
            }
            
            result = await self._make_request("POST", "/context", json_data=payload)
            return result is not None
            
        except Exception as e:
            logger.error(f"Context storage failed for {self.service_name}: {e}")
            return False
    
    async def execute_swarm_action(
        self,
        action: str,
        payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute Swarm-specific action through MCP service"""
        try:
            # Add Swarm metadata
            swarm_payload = {
                **payload,
                "swarm_metadata": {
                    "stage": self.swarm_stage,
                    "session_id": self.session_id,
                    "service": self.service_name,
                    "timestamp": time.time()
                }
            }
            
            result = await self._make_request("POST", f"/swarm/{action}", json_data=swarm_payload)
            return result
            
        except Exception as e:
            logger.error(f"Swarm action {action} failed for {self.service_name}: {e}")
            return None
    
    def set_swarm_context(self, stage: Optional[str] = None, session_id: Optional[str] = None):
        """Set Swarm context for this client"""
        if stage:
            self.swarm_stage = stage
        if session_id:
            self.session_id = session_id
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        return {
            **self.performance_metrics,
            "circuit_breaker_state": self.circuit_breaker.state,
            "cache_size": len(self.search_cache),
            "service": self.service_name
        }
    
    async def close(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # Abstract methods that subclasses should implement
    
    @abstractmethod
    def _get_service_filters(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get service-specific search filters"""
        pass
    
    @abstractmethod
    def _get_context_fields(self) -> Dict[str, Any]:
        """Get service-specific context fields"""
        pass
    
    # Backward compatibility methods for existing Swarm system
    
    @abstractmethod
    def code_map(self, paths: List[str]) -> Dict[str, Any]:
        """Get code mapping (for services that support it)"""
        pass
    
    @abstractmethod
    def next_actions(
        self, 
        tool_name: str, 
        context: str = "", 
        swarm_stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get suggested next actions"""
        pass
    
    @abstractmethod
    def learn(self, event: Dict[str, Any]) -> None:
        """Learn from events (synchronous for backward compatibility)"""
        pass


class MCPClientManager:
    """
    Manages multiple MCP service clients
    
    Features:
    - Service discovery and registration
    - Load balancing and failover
    - Unified search across multiple services
    - Performance monitoring
    """
    
    def __init__(self):
        self.clients: Dict[str, BaseMCPClient] = {}
        self.service_configs: Dict[str, MCPServiceConfig] = {}
        self.service_health: Dict[str, bool] = {}
        
    async def register_client(self, client: BaseMCPClient):
        """Register an MCP client"""
        self.clients[client.service_name] = client
        self.service_configs[client.service_name] = client.config
        
        # Check initial health
        self.service_health[client.service_name] = await client.health_check()
        logger.info(f"Registered {client.service_name} client, healthy: {self.service_health[client.service_name]}")
    
    async def get_client(self, service_name: str) -> Optional[BaseMCPClient]:
        """Get client for specific service"""
        client = self.clients.get(service_name)
        if client and self.service_health.get(service_name, False):
            return client
        return None
    
    async def search_all(
        self, 
        query: str, 
        k: int = 8, 
        swarm_stage: Optional[str] = None
    ) -> List[SearchResult]:
        """Search across all available services"""
        all_results = []
        
        # Perform searches concurrently
        search_tasks = []
        for service_name, client in self.clients.items():
            if self.service_health.get(service_name, False):
                task = client.semantic_search(query, k, swarm_stage)
                search_tasks.append(task)
        
        if search_tasks:
            results_lists = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for results in results_lists:
                if isinstance(results, list):
                    all_results.extend(results)
        
        # Sort by score and return top k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:k]
    
    async def health_check_all(self):
        """Check health of all registered services"""
        health_tasks = []
        for service_name, client in self.clients.items():
            task = client.health_check()
            health_tasks.append((service_name, task))
        
        for service_name, task in health_tasks:
            try:
                is_healthy = await task
                self.service_health[service_name] = is_healthy
                if not is_healthy:
                    logger.warning(f"Service {service_name} is unhealthy")
            except Exception as e:
                self.service_health[service_name] = False
                logger.error(f"Health check failed for {service_name}: {e}")
    
    def get_available_services(self) -> List[str]:
        """Get list of healthy services"""
        return [
            service for service, healthy in self.service_health.items() 
            if healthy
        ]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all clients"""
        metrics = {}
        for service_name, client in self.clients.items():
            metrics[service_name] = client.get_performance_metrics()
        return metrics
    
    async def close_all(self):
        """Close all client connections"""
        for client in self.clients.values():
            await client.close()


# Global client manager instance
_client_manager = None

async def get_client_manager() -> MCPClientManager:
    """Get global client manager instance"""
    global _client_manager
    if _client_manager is None:
        _client_manager = MCPClientManager()
        
        # Auto-register available clients if enabled
        if os.getenv("AUTO_REGISTER_MCP_CLIENTS", "1") == "1":
            await _auto_register_clients(_client_manager)
    
    return _client_manager

async def _auto_register_clients(manager: MCPClientManager):
    """Auto-register available MCP clients"""
    try:
        # Import and register Slack client
        from libs.mcp_client.slack import SlackClient
        slack_client = SlackClient()
        await manager.register_client(slack_client)
    except ImportError:
        logger.info("Slack client not available")
    except Exception as e:
        logger.warning(f"Failed to register Slack client: {e}")
    
    # Add more service registrations as they become available
    # This pattern allows graceful degradation if services aren't available