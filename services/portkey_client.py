"""
Portkey client for LLM API access via OpenRouter.
Provides unified interface for various LLM providers with routing, fallbacks, and analytics.
"""
import httpx
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from config.config import settings
import time
import asyncio

class PortkeyClient:
    """
    Client for Portkey AI gateway with OpenRouter integration.
    Handles LLM requests with proper async implementation, error handling, and retries.
    """
    
    def __init__(self):
        self.portkey_key = settings.PORTKEY_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://api.portkey.ai/v1"
        
        # Request configuration
        self.default_timeout = 60
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "average_response_time": 0.0
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openrouter/auto",
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        timeout: float = None,
        retries: int = None
    ) -> Dict[str, Any]:
        """
        Send chat completion request via Portkey to OpenRouter.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model identifier (e.g., "openrouter/auto", "anthropic/claude-3-sonnet")
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented yet)
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            
        Returns:
            Chat completion response dictionary
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication
        if self.portkey_key:
            headers["Authorization"] = f"Bearer {self.portkey_key}"
            headers["X-ROUTER-TARGET"] = "openrouter"
            if self.openrouter_key:
                headers["X-OPENROUTER-API-KEY"] = self.openrouter_key
        else:
            # Direct OpenRouter access fallback
            if not self.openrouter_key:
                raise ValueError("Either PORTKEY_API_KEY or OPENROUTER_API_KEY must be provided")
            headers["Authorization"] = f"Bearer {self.openrouter_key}"
        
        # Prepare payload
        payload = {
            "model": model,
            "messages": messages
        }
        
        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature
        else:
            payload["temperature"] = settings.TEMPERATURE
            
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = settings.MAX_TOKENS
            
        if stream:
            payload["stream"] = True
            # TODO: Implement streaming support
            logger.warning("Streaming not yet implemented, using non-streaming mode")
        
        # Use provided values or defaults
        timeout = timeout or self.default_timeout
        retries = retries if retries is not None else self.max_retries
        
        # Make request with retries
        last_exception = None
        for attempt in range(retries + 1):
            try:
                # Choose endpoint based on authentication method
                url = f"{self.base_url}/chat/completions" if self.portkey_key else "https://openrouter.ai/api/v1/chat/completions"
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.debug(f"Sending chat request to {url} (attempt {attempt + 1})")
                    
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Update statistics
                    duration = time.time() - start_time
                    self.stats["successful_requests"] += 1
                    self._update_stats(result, duration)
                    
                    logger.info(f"Chat request completed in {duration:.2f}s")
                    return result
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Chat request failed (attempt {attempt + 1}/{retries + 1}): {e}")
                
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
        
        logger.error(f"Chat request failed after {retries + 1} attempts: {last_exception}")
        raise last_exception

    async def embeddings(
        self,
        input: str,
        model: str = "openai/text-embedding-3-small",
        timeout: float = None,
        retries: int = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings via Portkey to OpenRouter.
        
        Args:
            input: Text to embed
            model: Embedding model identifier
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            
        Returns:
            Embeddings response dictionary
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication
        if self.portkey_key:
            headers["Authorization"] = f"Bearer {self.portkey_key}"
            headers["X-ROUTER-TARGET"] = "openrouter"
            if self.openrouter_key:
                headers["X-OPENROUTER-API-KEY"] = self.openrouter_key
        else:
            # Direct OpenRouter access fallback
            if not self.openrouter_key:
                raise ValueError("Either PORTKEY_API_KEY or OPENROUTER_API_KEY must be provided")
            headers["Authorization"] = f"Bearer {self.openrouter_key}"
        
        # Prepare payload
        payload = {
            "model": model,
            "input": input
        }
        
        # Use provided values or defaults
        timeout = timeout or self.default_timeout
        retries = retries if retries is not None else self.max_retries
        
        # Make request with retries
        last_exception = None
        for attempt in range(retries + 1):
            try:
                # Choose endpoint based on authentication method
                url = f"{self.base_url}/embeddings" if self.portkey_key else "https://openrouter.ai/api/v1/embeddings"
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.debug(f"Sending embeddings request to {url} (attempt {attempt + 1})")
                    
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Update statistics
                    duration = time.time() - start_time
                    self.stats["successful_requests"] += 1
                    self._update_average_response_time(duration)
                    
                    logger.debug(f"Embeddings request completed in {duration:.2f}s")
                    return result
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Embeddings request failed (attempt {attempt + 1}/{retries + 1}): {e}")
                
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
        
        logger.error(f"Embeddings request failed after {retries + 1} attempts: {last_exception}")
        raise last_exception

    async def get_models(self) -> Dict[str, Any]:
        """Get available models from OpenRouter."""
        try:
            headers = {}
            if self.openrouter_key:
                headers["Authorization"] = f"Bearer {self.openrouter_key}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            raise

    async def get_usage(self) -> Dict[str, Any]:
        """Get usage statistics from Portkey (if available)."""
        if not self.portkey_key:
            return {"error": "Portkey API key required for usage statistics"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.portkey_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/usage",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {"error": str(e)}

    def _update_stats(self, response: Dict[str, Any], duration: float) -> None:
        """Update client statistics."""
        # Extract token usage if available
        usage = response.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        self.stats["total_tokens"] += total_tokens
        
        # Update average response time
        self._update_average_response_time(duration)

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
            "has_portkey_key": bool(self.portkey_key),
            "has_openrouter_key": bool(self.openrouter_key)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check client health by making a minimal API call."""
        try:
            # Make a minimal chat request
            test_messages = [{"role": "user", "content": "Hello"}]
            
            await self.chat(
                messages=test_messages,
                model="openrouter/auto",
                max_tokens=1,
                timeout=10,
                retries=1
            )
            
            return {
                "status": "healthy",
                "portkey_available": bool(self.portkey_key),
                "openrouter_available": bool(self.openrouter_key)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "portkey_available": bool(self.portkey_key),
                "openrouter_available": bool(self.openrouter_key)
            }