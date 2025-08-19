"""
RobustFlyAgent - Advanced Fly.io API Client with Retry Logic
Designed to crush API errors and deploy SOPHIA V4 successfully
"""

import asyncio
import aiohttp
import os
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

@dataclass
class FlyConfig:
    """Configuration for Fly.io API access"""
    org_token: str
    machines_api: str = "https://api.machines.dev/v1"
    graphql_api: str = "https://api.fly.io/graphql"
    timeout: int = 60
    max_retries: int = 5

class FlyAPIError(Exception):
    """Custom exception for Fly.io API errors"""
    def __init__(self, status_code: int, message: str, request_id: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.request_id = request_id
        super().__init__(f"Fly.io API Error {status_code}: {message}")

class FlyAIAgent:
    """Base Fly.io AI Agent with core API functionality"""
    
    def __init__(self, config: FlyConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.org_token}",
            "Content-Type": "application/json",
            "User-Agent": "SOPHIA-V4-RobustAgent/1.0"
        }
    
    async def graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL request with error handling"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.config.graphql_api,
                headers=self.headers,
                json=payload,
                timeout=timeout
            ) as response:
                response_text = await response.text()
                request_id = response.headers.get('fly-request-id')
                
                if response.status != 200:
                    logger.error(f"GraphQL request failed: {response.status} - {response_text}")
                    raise FlyAPIError(response.status, response_text, request_id)
                
                try:
                    data = await response.json()
                except Exception as e:
                    logger.error(f"Failed to parse GraphQL response: {e}")
                    raise FlyAPIError(500, f"Invalid JSON response: {response_text}", request_id)
                
                if "errors" in data:
                    error_msg = str(data["errors"])
                    logger.error(f"GraphQL errors: {error_msg}")
                    raise FlyAPIError(400, error_msg, request_id)
                
                return data.get("data", {})
    
    async def machines_request(self, method: str, endpoint: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Machines API request with error handling"""
        url = f"{self.config.machines_api}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, 
                url, 
                headers=self.headers, 
                json=json_data,
                timeout=timeout
            ) as response:
                response_text = await response.text()
                request_id = response.headers.get('fly-request-id')
                
                if response.status not in [200, 201, 202]:
                    logger.error(f"Machines API {method} failed: {response.status} - {response_text}")
                    raise FlyAPIError(response.status, response_text, request_id)
                
                try:
                    return await response.json()
                except Exception as e:
                    logger.warning(f"Non-JSON response from Machines API: {response_text}")
                    return {"status": "success", "message": response_text}

class RobustFlyAgent(FlyAIAgent):
    """Advanced Fly.io Agent with robust retry logic and error handling"""
    
    def __init__(self, org_token: Optional[str] = None):
        token = org_token or os.getenv("FLY_ORG_TOKEN") or os.getenv("FLY_API_TOKEN")
        if not token:
            raise ValueError("FLY_ORG_TOKEN or FLY_API_TOKEN must be provided")
        
        config = FlyConfig(org_token=token)
        super().__init__(config)
        
        logger.info(f"RobustFlyAgent initialized with token: {token[:10]}...")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, FlyAPIError))
    )
    async def execute_with_retry(self, operation, operation_name: str = "operation"):
        """Execute operation with comprehensive retry logic"""
        try:
            logger.info(f"Executing {operation_name}...")
            result = await operation()
            logger.info(f"{operation_name} completed successfully")
            return result
            
        except FlyAPIError as e:
            # Don't retry on authentication/authorization errors
            if e.status_code in [401, 403, 404, 422]:
                logger.error(f"{operation_name} failed with non-retryable error: {e}")
                raise
            
            logger.warning(f"{operation_name} failed with retryable error: {e}")
            raise  # Retry on 429, 500, 502, 503, 504
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"{operation_name} failed with network error: {e}")
            raise  # Retry on network errors
            
        except Exception as e:
            logger.error(f"{operation_name} failed with unexpected error: {e}")
            raise  # Don't retry on unexpected errors
    
    async def get_app_info(self, app_name: str) -> Dict[str, Any]:
        """Get application information"""
        query = """
        query GetApp($appName: String!) {
            app(name: $appName) {
                id
                name
                status
                deployed
                hostname
                organization { id, name }
                currentRelease { id, version, status }
            }
        }
        """
        variables = {"appName": app_name}
        
        return await self.execute_with_retry(
            lambda: self.graphql_request(query, variables),
            f"get_app_info({app_name})"
        )
    
    async def list_machines(self, app_name: str) -> Dict[str, Any]:
        """List all machines for an app"""
        endpoint = f"/apps/{app_name}/machines"
        
        return await self.execute_with_retry(
            lambda: self.machines_request("GET", endpoint),
            f"list_machines({app_name})"
        )
    
    async def get_machine_status(self, app_name: str, machine_id: str) -> Dict[str, Any]:
        """Get machine status"""
        endpoint = f"/apps/{app_name}/machines/{machine_id}"
        
        return await self.execute_with_retry(
            lambda: self.machines_request("GET", endpoint),
            f"get_machine_status({app_name}, {machine_id})"
        )
    
    async def restart_machine(self, app_name: str, machine_id: str) -> Dict[str, Any]:
        """Restart a machine with retry logic"""
        endpoint = f"/apps/{app_name}/machines/{machine_id}/restart"
        
        return await self.execute_with_retry(
            lambda: self.machines_request("POST", endpoint),
            f"restart_machine({app_name}, {machine_id})"
        )
    
    async def stop_machine(self, app_name: str, machine_id: str) -> Dict[str, Any]:
        """Stop a machine with retry logic"""
        endpoint = f"/apps/{app_name}/machines/{machine_id}/stop"
        
        return await self.execute_with_retry(
            lambda: self.machines_request("POST", endpoint),
            f"stop_machine({app_name}, {machine_id})"
        )
    
    async def deploy_image(self, app_name: str, image_ref: str, strategy: str = "IMMEDIATE") -> Dict[str, Any]:
        """Deploy image using GraphQL with retry logic"""
        query = """
        mutation DeployImage($input: DeployImageInput!) {
            deployImage(input: $input) {
                release { 
                    id 
                    version 
                    status 
                    createdAt
                }
                app { name, status }
            }
        }
        """
        
        variables = {
            "input": {
                "appId": app_name,
                "image": image_ref,
                "strategy": strategy
            }
        }
        
        return await self.execute_with_retry(
            lambda: self.graphql_request(query, variables),
            f"deploy_image({app_name}, {image_ref})"
        )
    
    async def health_check(self, hostname: str, path: str = "/health", timeout: int = 10) -> bool:
        """Perform health check with retry logic"""
        url = f"https://{hostname}{path}"
        
        async def check_health():
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout_config) as response:
                    if response.status == 200:
                        return True
                    else:
                        raise FlyAPIError(response.status, f"Health check failed: {await response.text()}")
        
        try:
            return await self.execute_with_retry(
                check_health,
                f"health_check({hostname}{path})"
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Convenience function for quick access
def create_robust_fly_agent(org_token: Optional[str] = None) -> RobustFlyAgent:
    """Create a RobustFlyAgent instance"""
    return RobustFlyAgent(org_token)

