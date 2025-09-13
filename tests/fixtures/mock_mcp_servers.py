"""
Mock MCP Server Fixtures
Provides mock MCP servers for testing domain routing and resilience
"""
import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
@dataclass
class MockServerResponse:
    """Mock response from MCP server"""
    success: bool
    data: Any
    latency: float = 0.1
    error: Optional[str] = None
    server_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
class MockMCPServer:
    """
    Mock MCP server for testing
    Simulates various server behaviors including failures, latency, and rate limiting
    """
    def __init__(
        self,
        server_id: str,
        server_type: str,
        failure_rate: float = 0.0,
        latency_range: tuple = (0.01, 0.1),
        rate_limit: Optional[int] = None,
        circuit_breaker_threshold: int = 5,
    ):
        """
        Initialize mock MCP server
        Args:
            server_id: Unique server identifier
            server_type: Type of server (FILESYSTEM, CODE_ANALYSIS, WEB_SEARCH, etc.)
            failure_rate: Probability of request failure (0.0 to 1.0)
            latency_range: Min and max latency in seconds
            rate_limit: Maximum requests per second
            circuit_breaker_threshold: Failures before circuit opens
        """
        self.server_id = server_id
        self.server_type = server_type
        self.failure_rate = failure_rate
        self.latency_range = latency_range
        self.rate_limit = rate_limit
        self.circuit_breaker_threshold = circuit_breaker_threshold
        # State tracking
        self.is_healthy = True
        self.consecutive_failures = 0
        self.request_count = 0
        self.failure_count = 0
        self.last_request_time = None
        self.request_history: List[MockServerResponse] = []
        # Rate limiting
        self.request_times: List[datetime] = []
        # Mock capabilities based on server type
        self.capabilities = self._setup_capabilities()
    def _setup_capabilities(self) -> Dict[str, Any]:
        """Setup server capabilities based on type"""
        capabilities_map = {
            "FILESYSTEM": {
                "read": True,
                "write": True,
                "list": True,
                "delete": True,
                "move": True,
            },
            "CODE_ANALYSIS": {
                "analyze": True,
                "lint": True,
                "format": True,
                "refactor": True,
                "test": True,
            },
            "WEB_SEARCH": {
                "search": True,
                "fetch": True,
                "scrape": True,
                "index": True,
            },
            "DATABASE": {
                "query": True,
                "insert": True,
                "update": True,
                "delete": True,
                "transaction": True,
            },
            "NOTIFICATION": {
                "send": True,
                "schedule": True,
                "template": True,
                "history": True,
            },
        }
        return capabilities_map.get(self.server_type, {})
    async def execute(
        self, operation: str, params: Optional[Dict[str, Any]] = None
    ) -> MockServerResponse:
        """
        Execute an operation on the mock server
        Args:
            operation: Operation to execute
            params: Operation parameters
        Returns:
            Mock server response
        """
        # Update request tracking
        self.request_count += 1
        current_time = datetime.utcnow()
        self.last_request_time = current_time
        # Check rate limiting
        if self._is_rate_limited():
            return MockServerResponse(
                success=False,
                data=None,
                error="Rate limit exceeded",
                server_id=self.server_id,
            )
        # Simulate latency
        latency = random.uniform(*self.latency_range)
        await asyncio.sleep(latency)
        # Check if server is healthy (circuit breaker simulation)
        if not self.is_healthy:
            return MockServerResponse(
                success=False,
                data=None,
                error="Server circuit breaker is open",
                server_id=self.server_id,
                latency=latency,
            )
        # Simulate random failures
        if random.random() < self.failure_rate:
            self.failure_count += 1
            self.consecutive_failures += 1
            # Check circuit breaker threshold
            if self.consecutive_failures >= self.circuit_breaker_threshold:
                self.is_healthy = False
            response = MockServerResponse(
                success=False,
                data=None,
                error=f"Random failure in {operation}",
                server_id=self.server_id,
                latency=latency,
            )
        else:
            # Success case
            self.consecutive_failures = 0
            # Generate mock data based on operation
            mock_data = self._generate_mock_data(operation, params)
            response = MockServerResponse(
                success=True, data=mock_data, server_id=self.server_id, latency=latency
            )
        # Store in history
        self.request_history.append(response)
        return response
    def _is_rate_limited(self) -> bool:
        """Check if request is rate limited"""
        if not self.rate_limit:
            return False
        current_time = datetime.utcnow()
        # Clean old request times (older than 1 second)
        self.request_times = [
            t for t in self.request_times if (current_time - t).total_seconds() < 1.0
        ]
        # Check if we've exceeded rate limit
        if len(self.request_times) >= self.rate_limit:
            return True
        # Add current request time
        self.request_times.append(current_time)
        return False
    def _generate_mock_data(
        self, operation: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Generate mock data based on operation and server type"""
        if self.server_type == "FILESYSTEM":
            if operation == "read":
                return {"content": "Mock file content", "size": 1024}
            elif operation == "list":
                return {"files": ["file1.txt", "file2.py", "dir1/"]}
            elif operation == "write":
                return {"bytes_written": 512}
            else:
                return {"status": "success"}
        elif self.server_type == "CODE_ANALYSIS":
            if operation == "analyze":
                return {"complexity": 5.2, "lines": 150, "functions": 10, "issues": []}
            elif operation == "lint":
                return {"errors": 0, "warnings": 2, "info": 5}
            elif operation == "test":
                return {"passed": 10, "failed": 0, "skipped": 1}
            else:
                return {"result": "completed"}
        elif self.server_type == "WEB_SEARCH":
            if operation == "search":
                return {
                    "results": [
                        {"title": "Result 1", "url": "http://example.com/1"},
                        {"title": "Result 2", "url": "http://example.com/2"},
                    ],
                    "total": 2,
                }
            elif operation == "fetch":
                return {"content": "<html>Mock HTML content</html>"}
            else:
                return {"data": "mock data"}
        elif self.server_type == "DATABASE":
            if operation == "query":
                return {"rows": [{"id": 1, "name": "Item 1"}], "count": 1}
            elif operation in ["insert", "update", "delete"]:
                return {"affected_rows": 1}
            else:
                return {"transaction_id": "tx_123"}
        elif self.server_type == "NOTIFICATION":
            if operation == "send":
                return {"message_id": "msg_456", "status": "sent"}
            elif operation == "schedule":
                return {"job_id": "job_789", "scheduled_at": "2024-01-01T00:00:00Z"}
            else:
                return {"status": "completed"}
        return {"mock": "data"}
    def reset(self):
        """Reset server state"""
        self.is_healthy = True
        self.consecutive_failures = 0
        self.request_count = 0
        self.failure_count = 0
        self.last_request_time = None
        self.request_history.clear()
        self.request_times.clear()
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        success_count = sum(1 for r in self.request_history if r.success)
        avg_latency = (
            (sum(r.latency for r in self.request_history) / len(self.request_history))
            if self.request_history
            else 0
        )
        return {
            "server_id": self.server_id,
            "server_type": self.server_type,
            "is_healthy": self.is_healthy,
            "request_count": self.request_count,
            "failure_count": self.failure_count,
            "success_rate": success_count / max(self.request_count, 1),
            "average_latency": avg_latency,
            "consecutive_failures": self.consecutive_failures,
        }
class MockMCPServerCluster:
    """
    Mock MCP server cluster for testing load balancing and failover
    """
    def __init__(self, server_type: str, server_count: int = 3):
        """
        Initialize mock server cluster
        Args:
            server_type: Type of servers in cluster
            server_count: Number of servers in cluster
        """
        self.server_type = server_type
        self.servers: List[MockMCPServer] = []
        # Create servers with varying characteristics
        for i in range(server_count):
            server = MockMCPServer(
                server_id=f"{server_type.lower()}_server_{i+1}",
                server_type=server_type,
                failure_rate=0.05 * (i + 1),  # Increasing failure rates
                latency_range=(0.01 * (i + 1), 0.05 * (i + 1)),  # Varying latency
                rate_limit=100 - (i * 20),  # Decreasing rate limits
            )
            self.servers.append(server)
        self.current_server_index = 0
        self.load_balancing_strategy = "round_robin"
    async def execute_with_load_balancing(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        strategy: str = "round_robin",
    ) -> MockServerResponse:
        """
        Execute operation with load balancing
        Args:
            operation: Operation to execute
            params: Operation parameters
            strategy: Load balancing strategy (round_robin, least_loaded, random)
        Returns:
            Server response
        """
        server = self._select_server(strategy)
        if not server:
            return MockServerResponse(
                success=False,
                data=None,
                error="No healthy servers available",
                server_id="cluster",
            )
        return await server.execute(operation, params)
    def _select_server(self, strategy: str) -> Optional[MockMCPServer]:
        """Select a server based on load balancing strategy"""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        if strategy == "round_robin":
            # Round-robin selection
            server = healthy_servers[self.current_server_index % len(healthy_servers)]
            self.current_server_index += 1
            return server
        elif strategy == "least_loaded":
            # Select server with least requests
            return min(healthy_servers, key=lambda s: s.request_count)
        elif strategy == "random":
            # Random selection
            return random.choice(healthy_servers)
        else:
            # Default to round-robin
            return self._select_server("round_robin")
    async def execute_with_failover(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> MockServerResponse:
        """
        Execute operation with automatic failover
        Args:
            operation: Operation to execute
            params: Operation parameters
            max_retries: Maximum failover attempts
        Returns:
            Server response
        """
        attempted_servers = set()
        for attempt in range(max_retries):
            # Find a server we haven't tried
            available_servers = [
                s
                for s in self.servers
                if s.server_id not in attempted_servers and s.is_healthy
            ]
            if not available_servers:
                break
            server = random.choice(available_servers)
            attempted_servers.add(server.server_id)
            response = await server.execute(operation, params)
            if response.success:
                return response
        # All attempts failed
        return MockServerResponse(
            success=False,
            data=None,
            error=f"Failover failed after {len(attempted_servers)} attempts",
            server_id="cluster",
        )
    def simulate_server_failure(self, server_index: int):
        """Simulate a server failure"""
        if 0 <= server_index < len(self.servers):
            self.servers[server_index].is_healthy = False
    def simulate_server_recovery(self, server_index: int):
        """Simulate server recovery"""
        if 0 <= server_index < len(self.servers):
            self.servers[server_index].reset()
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics"""
        healthy_count = sum(1 for s in self.servers if s.is_healthy)
        total_requests = sum(s.request_count for s in self.servers)
        total_failures = sum(s.failure_count for s in self.servers)
        return {
            "server_type": self.server_type,
            "total_servers": len(self.servers),
            "healthy_servers": healthy_count,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "overall_success_rate": (
                (total_requests - total_failures) / max(total_requests, 1)
            ),
            "servers": [s.get_stats() for s in self.servers],
        }
def create__mock_servers() -> Dict[str, MockMCPServer]:
    """Create mock servers for  domain"""
    return {
        "filesystem": MockMCPServer(
            server_id="_filesystem",
            server_type="FILESYSTEM",
            failure_rate=0.02,
            latency_range=(0.01, 0.05),
        ),
        "code_analysis": MockMCPServer(
            server_id="_code_analysis",
            server_type="CODE_ANALYSIS",
            failure_rate=0.05,
            latency_range=(0.05, 0.2),
        ),
        "database": MockMCPServer(
            server_id="_database",
            server_type="DATABASE",
            failure_rate=0.01,
            latency_range=(0.02, 0.1),
            rate_limit=100,
        ),
    }
def create_sophia_mock_servers() -> Dict[str, MockMCPServer]:
    """Create mock servers for Sophia domain"""
    return {
        "web_search": MockMCPServer(
            server_id="sophia_web_search",
            server_type="WEB_SEARCH",
            failure_rate=0.1,
            latency_range=(0.1, 0.5),
            rate_limit=50,
        ),
        "database": MockMCPServer(
            server_id="sophia_database",
            server_type="DATABASE",
            failure_rate=0.01,
            latency_range=(0.02, 0.1),
            rate_limit=100,
        ),
        "notification": MockMCPServer(
            server_id="sophia_notification",
            server_type="NOTIFICATION",
            failure_rate=0.05,
            latency_range=(0.05, 0.15),
        ),
    }
def create_shared_mock_server_cluster() -> MockMCPServerCluster:
    """Create a shared database server cluster"""
    return MockMCPServerCluster(server_type="DATABASE", server_count=3)
