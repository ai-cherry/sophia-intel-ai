"""
Dynamic Tool Integration Layer
================================
Production-ready tool integration system for Sophia and Artemis orchestrators.
Provides unified API testing, monitoring, and integration capabilities.
Built to eliminate tech debt and integrate seamlessly with existing infrastructure.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Type, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx
import json
from functools import wraps
import redis.asyncio as aioredis
import os

# Simple configuration
class Settings:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

settings = Settings()

# Simple circuit breaker implementation
class CircuitBreaker:
    """Simple circuit breaker for tool connections"""
    def __init__(self, failure_threshold=3, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
        
    async def __aenter__(self):
        if self.is_open:
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed < self.recovery_timeout:
                    raise Exception("Circuit breaker is open")
                else:
                    self.is_open = False
                    self.failure_count = 0
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
        else:
            self.failure_count = 0
        return False

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool connection and health status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"
    INITIALIZING = "initializing"
    DEGRADED = "degraded"


class IntegrationPriority(Enum):
    """Priority levels for tool operations"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class ToolCredentials:
    """Secure credentials management for tools"""
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, prefix: str) -> "ToolCredentials":
        """Load credentials from environment variables"""
        import os
        creds = cls(
            api_key=os.getenv(f"{prefix}_API_KEY"),
            client_id=os.getenv(f"{prefix}_CLIENT_ID"),
            client_secret=os.getenv(f"{prefix}_CLIENT_SECRET"),
            access_token=os.getenv(f"{prefix}_ACCESS_TOKEN"),
            base_url=os.getenv(f"{prefix}_BASE_URL")
        )
        # For Gong, use access token as the API key if available
        if prefix == "GONG" and creds.access_token:
            creds.api_key = creds.access_token
        return creds


@dataclass
class ToolTestResult:
    """Result of tool connection test"""
    tool_name: str
    status: ToolStatus
    success: bool
    latency_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    capabilities: List[str] = field(default_factory=list)
    rate_limits: Optional[Dict[str, Any]] = None


class BaseToolConnector(ABC):
    """
    Base class for all tool connectors.
    Implements circuit breaker pattern and health monitoring.
    """
    
    def __init__(
        self,
        name: str,
        credentials: ToolCredentials,
        priority: IntegrationPriority = IntegrationPriority.NORMAL
    ):
        self.name = name
        self.credentials = credentials
        self.priority = priority
        self.status = ToolStatus.INITIALIZING
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=Exception
        )
        self._cache: Optional[aioredis.Redis] = None
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check: Optional[datetime] = None
        
    async def initialize(self) -> bool:
        """Initialize the tool connector"""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.credentials.base_url or "",
                timeout=30.0,
                headers=self._get_headers()
            )
            
            # Initialize Redis cache if available
            try:
                self._cache = await aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                await self._cache.ping()
            except Exception:
                logger.warning(f"Cache unavailable for {self.name}")
                self._cache = None
            
            # Perform initial connection test
            result = await self.test_connection()
            self.status = ToolStatus.CONNECTED if result.success else ToolStatus.ERROR
            
            return result.success
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {str(e)}")
            self.status = ToolStatus.ERROR
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {"Content-Type": "application/json"}
        
        # Gong uses Basic auth with access key and secret
        if self.name == "gong" and self.credentials.api_key:
            import base64
            # Gong expects "accessKey:accessSecret" in Basic auth
            access_key = os.getenv("GONG_API_KEY", "")
            access_secret = self.credentials.api_key  # This is the token
            auth_string = f"{access_key}:{access_secret}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif self.credentials.api_key:
            headers["Authorization"] = f"Bearer {self.credentials.api_key}"
        elif self.credentials.access_token:
            headers["Authorization"] = f"Bearer {self.credentials.access_token}"
            
        return headers
    
    @abstractmethod
    async def test_connection(self) -> ToolTestResult:
        """Test the connection to the tool"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities this tool provides"""
        pass
    
    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool operation with circuit breaker protection"""
        try:
            async with self._circuit_breaker:
                method = getattr(self, f"_{operation}", None)
                if not method:
                    raise ValueError(f"Operation {operation} not supported by {self.name}")
                
                return await method(**params)
                
        except Exception as e:
            logger.error(f"{self.name} operation {operation} failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool": self.name,
                "operation": operation
            }
    
    async def health_check(self) -> bool:
        """Perform health check on the tool"""
        now = datetime.utcnow()
        
        # Check if we need to run health check
        if self._last_health_check:
            elapsed = (now - self._last_health_check).total_seconds()
            if elapsed < self._health_check_interval:
                return self.status == ToolStatus.CONNECTED
        
        result = await self.test_connection()
        self._last_health_check = now
        self.status = ToolStatus.CONNECTED if result.success else ToolStatus.ERROR
        
        return result.success
    
    async def cleanup(self):
        """Clean up resources"""
        if self._client:
            await self._client.aclose()
        if self._cache:
            await self._cache.close()


class GongConnector(BaseToolConnector):
    """Gong.io API connector for call analytics and insights"""
    
    def __init__(self, credentials: Optional[ToolCredentials] = None):
        if not credentials:
            credentials = ToolCredentials.from_env("GONG")
            if not credentials.base_url:
                credentials.base_url = "https://api.gong.io/v2"
            # Gong uses access token directly, not API key format
            if credentials.access_token:
                credentials.api_key = credentials.access_token
        
        super().__init__("gong", credentials, IntegrationPriority.HIGH)
        
    async def test_connection(self) -> ToolTestResult:
        """Test Gong API connection"""
        import time
        start_time = time.time()
        
        try:
            response = await self._client.get("/users")
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return ToolTestResult(
                    tool_name="gong",
                    status=ToolStatus.CONNECTED,
                    success=True,
                    latency_ms=latency_ms,
                    message="Successfully connected to Gong API",
                    details={
                        "total_users": data.get("totalRecords", 0),
                        "api_version": "v2"
                    },
                    capabilities=await self.get_capabilities()
                )
            else:
                return ToolTestResult(
                    tool_name="gong",
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=latency_ms,
                    message=f"Gong API returned status {response.status_code}",
                    details={"status_code": response.status_code}
                )
                
        except Exception as e:
            return ToolTestResult(
                tool_name="gong",
                status=ToolStatus.ERROR,
                success=False,
                latency_ms=0,
                message=f"Failed to connect to Gong: {str(e)}",
                details={"error": str(e)}
            )
    
    async def get_capabilities(self) -> List[str]:
        """Get Gong capabilities"""
        return [
            "call_recordings",
            "transcripts",
            "call_analytics",
            "conversation_insights",
            "team_analytics",
            "deal_intelligence",
            "coaching_insights"
        ]
    
    async def _get_calls(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get calls within date range"""
        response = await self._client.get(
            "/calls",
            params={"fromDateTime": from_date, "toDateTime": to_date}
        )
        return response.json()
    
    async def _get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Get transcript for a specific call"""
        response = await self._client.get(f"/calls/{call_id}/transcript")
        return response.json()


class HubSpotConnector(BaseToolConnector):
    """HubSpot CRM API connector"""
    
    def __init__(self, credentials: Optional[ToolCredentials] = None):
        if not credentials:
            credentials = ToolCredentials.from_env("HUBSPOT")
            if not credentials.base_url:
                credentials.base_url = "https://api.hubapi.com"
        
        super().__init__("hubspot", credentials, IntegrationPriority.HIGH)
        
    async def test_connection(self) -> ToolTestResult:
        """Test HubSpot API connection"""
        import time
        start_time = time.time()
        
        try:
            response = await self._client.get("/account-info/v3/details")
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return ToolTestResult(
                    tool_name="hubspot",
                    status=ToolStatus.CONNECTED,
                    success=True,
                    latency_ms=latency_ms,
                    message="Successfully connected to HubSpot API",
                    details={
                        "portal_id": data.get("portalId"),
                        "time_zone": data.get("timeZone"),
                        "currency": data.get("currency")
                    },
                    capabilities=await self.get_capabilities(),
                    rate_limits={
                        "daily_limit": data.get("dailyApiUsageLimit"),
                        "current_usage": data.get("currentApiUsage")
                    }
                )
            else:
                return ToolTestResult(
                    tool_name="hubspot",
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=latency_ms,
                    message=f"HubSpot API returned status {response.status_code}",
                    details={"status_code": response.status_code}
                )
                
        except Exception as e:
            return ToolTestResult(
                tool_name="hubspot",
                status=ToolStatus.ERROR,
                success=False,
                latency_ms=0,
                message=f"Failed to connect to HubSpot: {str(e)}",
                details={"error": str(e)}
            )
    
    async def get_capabilities(self) -> List[str]:
        """Get HubSpot capabilities"""
        return [
            "contacts",
            "companies",
            "deals",
            "tickets",
            "pipelines",
            "analytics",
            "marketing_emails",
            "workflows",
            "forms",
            "lists"
        ]
    
    async def _get_contacts(self, limit: int = 100) -> Dict[str, Any]:
        """Get contacts from HubSpot"""
        response = await self._client.get(
            "/crm/v3/objects/contacts",
            params={"limit": limit}
        )
        return response.json()
    
    async def _get_deals(self, limit: int = 100) -> Dict[str, Any]:
        """Get deals from HubSpot"""
        response = await self._client.get(
            "/crm/v3/objects/deals",
            params={"limit": limit}
        )
        return response.json()


class SalesforceConnector(BaseToolConnector):
    """Salesforce CRM API connector"""
    
    def __init__(self, credentials: Optional[ToolCredentials] = None):
        if not credentials:
            credentials = ToolCredentials.from_env("SALESFORCE")
        
        super().__init__("salesforce", credentials, IntegrationPriority.HIGH)
        self._instance_url: Optional[str] = None
        
    async def test_connection(self) -> ToolTestResult:
        """Test Salesforce API connection"""
        import time
        start_time = time.time()
        
        try:
            # First authenticate to get instance URL
            auth_response = await self._authenticate()
            if not auth_response:
                return ToolTestResult(
                    tool_name="salesforce",
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=0,
                    message="Failed to authenticate with Salesforce"
                )
            
            # Test API with a simple query
            response = await self._client.get(
                f"{self._instance_url}/services/data/v59.0/sobjects"
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ToolTestResult(
                    tool_name="salesforce",
                    status=ToolStatus.CONNECTED,
                    success=True,
                    latency_ms=latency_ms,
                    message="Successfully connected to Salesforce API",
                    details={
                        "instance_url": self._instance_url,
                        "api_version": "v59.0"
                    },
                    capabilities=await self.get_capabilities()
                )
            else:
                return ToolTestResult(
                    tool_name="salesforce",
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=latency_ms,
                    message=f"Salesforce API returned status {response.status_code}"
                )
                
        except Exception as e:
            return ToolTestResult(
                tool_name="salesforce",
                status=ToolStatus.ERROR,
                success=False,
                latency_ms=0,
                message=f"Failed to connect to Salesforce: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _authenticate(self) -> bool:
        """Authenticate with Salesforce OAuth"""
        try:
            response = await self._client.post(
                "https://login.salesforce.com/services/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.credentials.access_token = data["access_token"]
                self._instance_url = data["instance_url"]
                return True
                
        except Exception as e:
            logger.error(f"Salesforce authentication failed: {str(e)}")
            
        return False
    
    async def get_capabilities(self) -> List[str]:
        """Get Salesforce capabilities"""
        return [
            "accounts",
            "contacts",
            "leads",
            "opportunities",
            "cases",
            "campaigns",
            "reports",
            "dashboards",
            "custom_objects",
            "soql_queries"
        ]


class GitHubConnector(BaseToolConnector):
    """GitHub API connector for repository management"""
    
    def __init__(self, credentials: Optional[ToolCredentials] = None):
        if not credentials:
            credentials = ToolCredentials.from_env("GITHUB")
            if not credentials.base_url:
                credentials.base_url = "https://api.github.com"
        
        super().__init__("github", credentials, IntegrationPriority.NORMAL)
        
    async def test_connection(self) -> ToolTestResult:
        """Test GitHub API connection"""
        import time
        start_time = time.time()
        
        try:
            response = await self._client.get("/user")
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return ToolTestResult(
                    tool_name="github",
                    status=ToolStatus.CONNECTED,
                    success=True,
                    latency_ms=latency_ms,
                    message="Successfully connected to GitHub API",
                    details={
                        "user": data.get("login"),
                        "name": data.get("name"),
                        "public_repos": data.get("public_repos")
                    },
                    capabilities=await self.get_capabilities(),
                    rate_limits={
                        "limit": response.headers.get("X-RateLimit-Limit"),
                        "remaining": response.headers.get("X-RateLimit-Remaining")
                    }
                )
            else:
                return ToolTestResult(
                    tool_name="github",
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=latency_ms,
                    message=f"GitHub API returned status {response.status_code}"
                )
                
        except Exception as e:
            return ToolTestResult(
                tool_name="github",
                status=ToolStatus.ERROR,
                success=False,
                latency_ms=0,
                message=f"Failed to connect to GitHub: {str(e)}"
            )
    
    async def get_capabilities(self) -> List[str]:
        """Get GitHub capabilities"""
        return [
            "repositories",
            "issues",
            "pull_requests",
            "actions",
            "webhooks",
            "releases",
            "commits",
            "branches",
            "collaborators"
        ]


class DynamicToolRegistry:
    """
    Central registry for managing all tool connectors.
    Provides unified interface for tool discovery, initialization, and execution.
    Integrates seamlessly with orchestrators.
    """
    
    def __init__(self):
        self._connectors: Dict[str, BaseToolConnector] = {}
        self._connector_classes: Dict[str, Type[BaseToolConnector]] = {
            "gong": GongConnector,
            "hubspot": HubSpotConnector,
            "salesforce": SalesforceConnector,
            "github": GitHubConnector
        }
        self._initialization_lock = asyncio.Lock()
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._cache: Optional[aioredis.Redis] = None
        
    async def initialize(self, tools: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Initialize specified tools or all available tools.
        Returns initialization status for each tool.
        """
        async with self._initialization_lock:
            results = {}
            
            # Initialize cache
            try:
                self._cache = await aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                await self._cache.ping()
                logger.info("Tool registry cache initialized")
            except Exception as e:
                logger.warning(f"Cache unavailable for tool registry: {str(e)}")
            
            # Determine which tools to initialize
            tools_to_init = tools or list(self._connector_classes.keys())
            
            # Initialize each tool
            for tool_name in tools_to_init:
                if tool_name in self._connector_classes:
                    try:
                        connector_class = self._connector_classes[tool_name]
                        connector = connector_class()
                        
                        # Initialize the connector
                        success = await connector.initialize()
                        
                        if success:
                            self._connectors[tool_name] = connector
                            logger.info(f"✅ Successfully initialized {tool_name} connector")
                        else:
                            logger.warning(f"⚠️ Failed to initialize {tool_name} connector")
                        
                        results[tool_name] = success
                        
                    except Exception as e:
                        logger.error(f"❌ Error initializing {tool_name}: {str(e)}")
                        results[tool_name] = False
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
                    results[tool_name] = False
            
            # Start health monitoring
            if self._connectors and not self._health_monitor_task:
                self._health_monitor_task = asyncio.create_task(self._health_monitor())
            
            return results
    
    async def test_connection(self, tool_name: str) -> ToolTestResult:
        """
        Test connection for a specific tool.
        This is the main method called when users request API testing.
        """
        if tool_name not in self._connectors:
            # Try to initialize the tool if not already done
            init_result = await self.initialize([tool_name])
            
            if not init_result.get(tool_name, False):
                return ToolTestResult(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    success=False,
                    latency_ms=0,
                    message=f"Failed to initialize {tool_name} connector. Check credentials."
                )
        
        connector = self._connectors.get(tool_name)
        if connector:
            result = await connector.test_connection()
            
            # Cache the result
            if self._cache:
                try:
                    await self._cache.setex(
                        f"tool_test:{tool_name}",
                        300,  # Cache for 5 minutes
                        json.dumps({
                            "status": result.status.value,
                            "success": result.success,
                            "message": result.message,
                            "timestamp": result.timestamp
                        })
                    )
                except Exception:
                    pass  # Cache errors are non-critical
            
            return result
        
        return ToolTestResult(
            tool_name=tool_name,
            status=ToolStatus.ERROR,
            success=False,
            latency_ms=0,
            message=f"Tool {tool_name} not found or not initialized"
        )
    
    async def execute_operation(
        self,
        tool_name: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific operation on a tool"""
        connector = self._connectors.get(tool_name)
        
        if not connector:
            return {
                "success": False,
                "error": f"Tool {tool_name} not initialized",
                "tool": tool_name,
                "operation": operation
            }
        
        # Check tool health before executing
        if connector.status != ToolStatus.CONNECTED:
            health_ok = await connector.health_check()
            if not health_ok:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} is not healthy",
                    "status": connector.status.value,
                    "tool": tool_name,
                    "operation": operation
                }
        
        # Execute the operation
        return await connector.execute(operation, params)
    
    async def get_tool_status(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of a specific tool or all tools"""
        if tool_name:
            connector = self._connectors.get(tool_name)
            if connector:
                return {
                    "name": tool_name,
                    "status": connector.status.value,
                    "priority": connector.priority.value,
                    "capabilities": await connector.get_capabilities()
                }
            return {"error": f"Tool {tool_name} not found"}
        
        # Return status of all tools
        status = {}
        for name, connector in self._connectors.items():
            status[name] = {
                "status": connector.status.value,
                "priority": connector.priority.value
            }
        
        return status
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools and their capabilities"""
        tools = []
        
        for name, connector_class in self._connector_classes.items():
            initialized = name in self._connectors
            status = self._connectors[name].status.value if initialized else "not_initialized"
            
            tool_info = {
                "name": name,
                "initialized": initialized,
                "status": status,
                "capabilities": []
            }
            
            if initialized:
                tool_info["capabilities"] = await self._connectors[name].get_capabilities()
            
            tools.append(tool_info)
        
        return tools
    
    async def _health_monitor(self):
        """Background task to monitor tool health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                for name, connector in self._connectors.items():
                    try:
                        await connector.health_check()
                        logger.debug(f"Health check for {name}: {connector.status.value}")
                    except Exception as e:
                        logger.error(f"Health check failed for {name}: {str(e)}")
                        connector.status = ToolStatus.ERROR
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {str(e)}")
                await asyncio.sleep(60)  # Shorter sleep on error
    
    async def cleanup(self):
        """Clean up all resources"""
        # Cancel health monitor
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all connectors
        for connector in self._connectors.values():
            await connector.cleanup()
        
        # Close cache connection
        if self._cache:
            await self._cache.close()
        
        self._connectors.clear()


# Global registry instance
tool_registry = DynamicToolRegistry()


async def handle_api_test_command(
    service: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Handle API test commands from orchestrators.
    This is the main entry point for testing API connections.
    """
    logger.info(f"🔧 Testing {service} API connection...")
    
    # Test the connection
    result = await tool_registry.test_connection(service)
    
    # Format response for orchestrator
    response = {
        "success": result.success,
        "service": service,
        "status": result.status.value,
        "message": result.message,
        "latency_ms": result.latency_ms,
        "timestamp": result.timestamp
    }
    
    if result.success:
        response["capabilities"] = result.capabilities
        response["details"] = result.details
        
        if result.rate_limits:
            response["rate_limits"] = result.rate_limits
        
        # Suggest follow-up actions
        response["suggestions"] = [
            f"You can now use {service} for data retrieval",
            f"Available operations: {', '.join(result.capabilities[:3])}",
            "Run 'check {service} status' for ongoing monitoring"
        ]
    else:
        response["troubleshooting"] = [
            "Verify API credentials are correct",
            "Check if the API endpoint is accessible",
            "Ensure required permissions are granted",
            f"Review {service.upper()}_API_KEY in environment variables"
        ]
    
    return response