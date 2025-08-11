"""
Orchestrator service for coordinating requests across multiple services.
Provides unified interface for agent execution, LLM routing, and service coordination.
"""

from typing import Any, Dict
from enum import Enum
from loguru import logger
import httpx
import asyncio
import time
from datetime import datetime

from .portkey_client import PortkeyClient
from .lambda_client import LambdaClient
from config.config import settings


class RequestType(str, Enum):
    CODE = "code"
    CHAT = "chat"
    GPU = "gpu"
    MEMORY = "memory"
    HEALTH = "health"


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class Orchestrator:
    """
    Central orchestrator for coordinating requests across multiple services.
    Handles routing, fallbacks, retries, and service health monitoring.
    """

    def __init__(self):
        self.portkey = PortkeyClient()
        self.lambda_client = LambdaClient()

        # Service endpoints
        self.services = {
            "agno_api": "http://localhost:7777",
            "mcp_server": f"http://localhost:{settings.MCP_PORT}",
            "backend_api": f"http://localhost:{settings.API_PORT}",
        }

        # Circuit breaker state
        self.circuit_breakers = {
            service: {
                "failures": 0,
                "last_failure": None,
                "status": ServiceStatus.HEALTHY,
            }
            for service in self.services
        }

        # Request statistics
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_request_time": None,
        }

    async def handle_request(
        self,
        request_type: str,
        payload: Dict[str, Any],
        timeout: int = 300,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Handle incoming request with proper routing, error handling, and retries.

        Args:
            request_type: Type of request (code, chat, gpu, memory, health)
            payload: Request payload
            timeout: Request timeout in seconds
            retries: Number of retry attempts

        Returns:
            Response dictionary with success status and result/error
        """
        start_time = time.time()
        self.request_stats["total_requests"] += 1
        self.request_stats["last_request_time"] = datetime.utcnow().isoformat()

        try:
            logger.info(f"Orchestrating {request_type} request")

            # Route request to appropriate handler
            if request_type == RequestType.CODE:
                result = await self._handle_code_request(payload, timeout, retries)
            elif request_type == RequestType.CHAT:
                result = await self._handle_chat_request(payload, timeout, retries)
            elif request_type == RequestType.GPU:
                result = await self._handle_gpu_request(payload, timeout, retries)
            elif request_type == RequestType.MEMORY:
                result = await self._handle_memory_request(payload, timeout, retries)
            elif request_type == RequestType.HEALTH:
                result = await self._handle_health_request(payload)
            else:
                raise ValueError(f"Unknown request type: {request_type}")

            # Update statistics
            duration = time.time() - start_time
            self.request_stats["successful_requests"] += 1
            self._update_average_response_time(duration)

            return {
                "success": True,
                "result": result,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            duration = time.time() - start_time
            self.request_stats["failed_requests"] += 1
            self._update_average_response_time(duration)

            logger.error(f"Request handling failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _handle_code_request(
        self, payload: Dict[str, Any], timeout: int, retries: int
    ) -> Dict[str, Any]:
        """Handle coding requests via Agno API."""
        return await self._make_service_request(
            "agno_api", "/agent/coding", payload, timeout, retries
        )

    async def _handle_chat_request(
        self, payload: Dict[str, Any], timeout: int, retries: int
    ) -> Dict[str, Any]:
        """Handle chat requests via Portkey client."""
        messages = payload.get("messages", [])
        model = payload.get("model", "openrouter/auto")

        try:
            response = await self.portkey.chat(messages, model)
            return response
        except Exception as e:
            logger.error(f"Portkey chat request failed: {e}")
            raise

    async def _handle_gpu_request(
        self, payload: Dict[str, Any], timeout: int, retries: int
    ) -> Dict[str, Any]:
        """Handle GPU resource requests via Lambda Labs client."""
        request_type = payload.get("type", "quota")

        try:
            logger.info(f"Processing GPU request: {request_type}")

            if request_type == "quota":
                response = await self.lambda_client.quota()

            elif request_type == "list_instances":
                response = await self.lambda_client.list_instances()

            elif request_type == "get_instance":
                instance_id = payload.get("instance_id")
                if not instance_id:
                    raise ValueError("instance_id is required for get_instance request")
                response = await self.lambda_client.get_instance(instance_id)

            elif request_type == "launch_instance":
                config = payload.get("config", {})
                if not config:
                    raise ValueError("config is required for launch_instance request")
                response = await self.lambda_client.launch_instance(config)

            elif request_type == "terminate_instance":
                instance_id = payload.get("instance_id")
                if not instance_id:
                    raise ValueError(
                        "instance_id is required for terminate_instance request"
                    )
                response = await self.lambda_client.terminate_instance(instance_id)

            elif request_type == "restart_instance":
                instance_id = payload.get("instance_id")
                if not instance_id:
                    raise ValueError(
                        "instance_id is required for restart_instance request"
                    )
                response = await self.lambda_client.restart_instance(instance_id)

            elif request_type == "list_ssh_keys":
                response = await self.lambda_client.list_ssh_keys()

            elif request_type == "add_ssh_key":
                name = payload.get("name")
                public_key = payload.get("public_key")
                if not name or not public_key:
                    raise ValueError(
                        "name and public_key are required for add_ssh_key request"
                    )
                response = await self.lambda_client.add_ssh_key(name, public_key)

            elif request_type == "list_instance_types":
                response = await self.lambda_client.list_instance_types()

            elif request_type == "health_check":
                response = await self.lambda_client.health_check()

            else:
                raise ValueError(f"Unknown GPU request type: {request_type}")

            logger.info(f"GPU request {request_type} completed successfully")
            return response

        except Exception as e:
            logger.error(f"Lambda Labs GPU request failed: {e}")
            # Return structured error response instead of just raising
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "request_type": request_type,
            }

    async def _handle_memory_request(
        self, payload: Dict[str, Any], timeout: int, retries: int
    ) -> Dict[str, Any]:
        """Handle memory requests via MCP server."""
        operation = payload.get("operation", "query")

        if operation == "store":
            endpoint = "/context/store"
        elif operation == "query":
            endpoint = "/context/query"
        else:
            raise ValueError(f"Unknown memory operation: {operation}")

        return await self._make_service_request(
            "mcp_server", endpoint, payload.get("data", {}), timeout, retries
        )

    async def _handle_health_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests."""
        service_healths = {}

        # Check all services
        for service_name in self.services:
            try:
                health = await self._check_service_health(service_name)
                service_healths[service_name] = health
            except Exception as e:
                service_healths[service_name] = {
                    "status": ServiceStatus.UNHEALTHY,
                    "error": str(e),
                }

        # Overall health status
        all_healthy = all(
            h.get("status") == ServiceStatus.HEALTHY.value
            for h in service_healths.values()
        )

        return {
            "overall_status": (
                ServiceStatus.HEALTHY.value
                if all_healthy
                else ServiceStatus.DEGRADED.value
            ),
            "services": service_healths,
            "circuit_breakers": self.circuit_breakers,
            "request_stats": self.request_stats,
        }

    async def _make_service_request(
        self,
        service_name: str,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: int,
        retries: int,
    ) -> Dict[str, Any]:
        """Make HTTP request to service with circuit breaker and retry logic."""

        # Check circuit breaker
        if not self._is_circuit_open(service_name):
            raise Exception(f"Circuit breaker open for service {service_name}")

        base_url = self.services[service_name]
        url = f"{base_url}{endpoint}"

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()

                    # Reset circuit breaker on success
                    self._reset_circuit_breaker(service_name)

                    return response.json()

            except Exception as e:
                logger.warning(f"Service request failed (attempt {attempt + 1}): {e}")

                # Record failure
                self._record_circuit_failure(service_name)

                # Retry with exponential backoff
                if attempt < retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise

    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        base_url = self.services[service_name]

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{base_url}/health")
                response.raise_for_status()

                result = response.json()
                result["status"] = ServiceStatus.HEALTHY.value
                return result

        except Exception as e:
            return {"status": ServiceStatus.UNHEALTHY.value, "error": str(e)}

    def _is_circuit_open(self, service_name: str) -> bool:
        """Check if circuit breaker allows requests."""
        breaker = self.circuit_breakers[service_name]

        # Circuit is open if too many failures
        if breaker["failures"] >= 5:
            # Allow retry after 60 seconds
            if breaker["last_failure"]:
                time_since_failure = time.time() - breaker["last_failure"]
                if time_since_failure > 60:
                    breaker["failures"] = 0
                    return True
            return False

        return True

    def _record_circuit_failure(self, service_name: str) -> None:
        """Record a circuit breaker failure."""
        breaker = self.circuit_breakers[service_name]
        breaker["failures"] += 1
        breaker["last_failure"] = time.time()

        if breaker["failures"] >= 5:
            breaker["status"] = ServiceStatus.UNHEALTHY
            logger.warning(f"Circuit breaker opened for service {service_name}")

    def _reset_circuit_breaker(self, service_name: str) -> None:
        """Reset circuit breaker on successful request."""
        breaker = self.circuit_breakers[service_name]
        breaker["failures"] = 0
        breaker["last_failure"] = None
        breaker["status"] = ServiceStatus.HEALTHY

    def _update_average_response_time(self, duration: float) -> None:
        """Update running average response time."""
        current_avg = self.request_stats["average_response_time"]
        total_requests = self.request_stats["total_requests"]

        if total_requests == 1:
            self.request_stats["average_response_time"] = duration
        else:
            # Running average calculation
            new_avg = ((current_avg * (total_requests - 1)) + duration) / total_requests
            self.request_stats["average_response_time"] = new_avg

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "request_stats": self.request_stats,
            "circuit_breakers": self.circuit_breakers,
            "services": list(self.services.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }
