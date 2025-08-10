"""
Lambda Labs cloud client for GPU resource management.
Provides comprehensive GPU instance management and quota tracking.
"""
import httpx
from typing import Dict, List, Any, Optional
from loguru import logger
from config.config import settings
import time
import asyncio

class LambdaClient:
    """
    Client for Lambda Labs Cloud GPU management.
    Provides instance management, quota tracking, and resource monitoring.
    """
    
    def __init__(self):
        self.api_key = settings.LAMBDA_API_KEY
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
        # Request configuration
        self.default_timeout = 60
        self.max_retries = 3
        self.retry_delay = 2.0
        
        # Request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }

    async def quota(self) -> Dict[str, Any]:
        """Get current quota and usage information."""
        return await self._make_request("GET", "/quota")

    async def list_instances(self) -> Dict[str, Any]:
        """List all GPU instances."""
        return await self._make_request("GET", "/instances")

    async def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get details for a specific instance."""
        return await self._make_request("GET", f"/instances/{instance_id}")

    async def launch_instance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Launch a new GPU instance.
        
        Args:
            config: Instance configuration including:
                - instance_type: GPU instance type (e.g., "gpu_1x_a100_sxm4")
                - region: Region to launch in
                - name: Instance name (optional)
                - ssh_key_names: List of SSH key names
        """
        required_fields = ["instance_type", "region"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        return await self._make_request("POST", "/instances", json=config)

    async def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate a GPU instance."""
        return await self._make_request("DELETE", f"/instances/{instance_id}")

    async def restart_instance(self, instance_id: str) -> Dict[str, Any]:
        """Restart a GPU instance."""
        return await self._make_request("POST", f"/instances/{instance_id}/restart")

    async def list_ssh_keys(self) -> Dict[str, Any]:
        """List SSH keys associated with the account."""
        return await self._make_request("GET", "/ssh-keys")

    async def add_ssh_key(self, name: str, public_key: str) -> Dict[str, Any]:
        """Add a new SSH key."""
        return await self._make_request("POST", "/ssh-keys", json={
            "name": name,
            "public_key": public_key
        })

    async def list_instance_types(self) -> Dict[str, Any]:
        """List available GPU instance types."""
        return await self._make_request("GET", "/instance-types")

    async def health_check(self) -> Dict[str, Any]:
        """Check Lambda Labs API connectivity."""
        try:
            quota_info = await self.quota()
            return {
                "status": "healthy",
                "api_accessible": True,
                "quota_info": quota_info
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e)
            }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        timeout: float = None,
        retries: int = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Lambda Labs API with retries and error handling.
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        if not self.api_key:
            raise ValueError("LAMBDA_API_KEY is not set")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.default_timeout
        retries = retries if retries is not None else self.max_retries
        
        last_exception = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.debug(f"Lambda Labs API {method} {url} (attempt {attempt + 1})")
                    
                    response = await client.request(method, url, headers=headers, json=json)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Update statistics
                    duration = time.time() - start_time
                    self.stats["successful_requests"] += 1
                    self._update_average_response_time(duration)
                    
                    logger.debug(f"Lambda Labs API request completed in {duration:.2f}s")
                    return result
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Lambda Labs API request failed (attempt {attempt + 1}/{retries + 1}): {e}")
                
                # Don't retry on authentication errors
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code in [401, 403]:
                    break
                
                # Exponential backoff for retries
                if attempt < retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.debug(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        duration = time.time() - start_time
        self.stats["failed_requests"] += 1
        self._update_average_response_time(duration)
        
        logger.error(f"Lambda Labs API request failed after {retries + 1} attempts: {last_exception}")
        raise last_exception

    def _update_average_response_time(self, duration: float) -> None:
        """Update running average response time."""
        current_avg = self.stats["average_response_time"]
        total_requests = self.stats["total_requests"]
        
        if total_requests == 1:
            self.stats["average_response_time"] = duration
        else:
            # Running average calculation
            new_avg = ((current_avg * (total_requests - 1)) + duration) / total_requests
            self.stats["average_response_time"] = new_avg

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "has_api_key": bool(self.api_key)
        }