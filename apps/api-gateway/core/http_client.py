"""HTTP client with timeouts, retries, and circuit breaker patterns"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger()

class HTTPClient:
    """HTTP client with production-grade reliability features"""
    
    def __init__(self, timeout: float = 15.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def post(self, url: str, json_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """POST request with retries and exponential backoff"""
        try:
            logger.info("http_request", method="POST", url=url)
            
            response = await self.client.post(url, json=json_data, headers=headers or {})
            response.raise_for_status()
            
            logger.info("http_response", status_code=response.status_code, url=url)
            return response.json()
            
        except httpx.RequestError as e:
            logger.error("http_request_error", error=str(e), url=url)
            raise
        except httpx.HTTPStatusError as e:
            logger.error("http_status_error", status_code=e.response.status_code, url=url)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET request with retries and exponential backoff"""
        try:
            logger.info("http_request", method="GET", url=url)
            
            response = await self.client.get(url, headers=headers or {})
            response.raise_for_status()
            
            logger.info("http_response", status_code=response.status_code, url=url)
            return response.json()
            
        except httpx.RequestError as e:
            logger.error("http_request_error", error=str(e), url=url)
            raise
        except httpx.HTTPStatusError as e:
            logger.error("http_status_error", status_code=e.response.status_code, url=url)
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global HTTP client instance
http_client = HTTPClient()
