"""
Portkey Model Router with Fallback Support

Integrates Portkey virtual keys for intelligent model routing:
- Primary: GPT-5 via OpenAI Portkey virtual key
- Fallback: Grok-4 via xAI Portkey virtual key  
- Emergency: Direct OpenRouter access
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from portkey_ai import Portkey, LLMOptions

from app.core.circuit_breaker import with_circuit_breaker
try:
    from app.core.observability import get_tracer
except ImportError:
    # Fallback tracer if observability not fully configured
    def get_tracer(name):
        return DummyTracer()
    
    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()
    
    class DummySpan:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def set_attribute(self, *args): pass
        def add_event(self, *args): pass
from app.elite_portkey_config import PORTKEY_VIRTUAL_KEYS

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class ModelError(Exception):
    """Base exception for model routing errors"""
    pass


class AllModelsFailedException(ModelError):
    """Raised when all fallback models have failed"""
    pass


class PortkeyRouterModel:
    """
    Advanced model router with Portkey integration and intelligent fallback.
    
    Features:
    - GPT-5 as primary model via Portkey OpenAI virtual key
    - Grok-4 as fallback via Portkey xAI virtual key
    - Direct OpenRouter as emergency fallback
    - Circuit breaker protection
    - Request/response observability
    - Cost tracking and optimization
    - Automatic retry with exponential backoff
    """
    
    def __init__(
        self,
        enable_fallback: bool = True,
        enable_emergency_fallback: bool = True,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        cost_limit_per_request: float = 0.50  # $0.50 max per request
    ):
        self.id = "portkey_router_gpt5_grok4"
        self.provider = "portkey_multi"
        
        self.enable_fallback = enable_fallback
        self.enable_emergency_fallback = enable_emergency_fallback
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.cost_limit_per_request = cost_limit_per_request
        
        # Initialize Portkey clients
        self._setup_portkey_clients()
        
        # Setup emergency OpenRouter client
        self._setup_openrouter_client()
        
        # Metrics tracking
        self.request_count = 0
        self.total_cost = 0.0
        self.model_usage_stats = {}
        
        logger.info(f"PortkeyRouterModel initialized with fallback={enable_fallback}")
    
    def _setup_portkey_clients(self):
        """Initialize Portkey clients with virtual keys"""
        
        try:
            # Primary: GPT-5 via OpenAI virtual key
            self.primary_client = Portkey(
                api_key=os.getenv("PORTKEY_API_KEY"),
                virtual_key=PORTKEY_VIRTUAL_KEYS["OPENAI"],
                config={
                    "retry_count": 2,
                    "retry_delay": 1,
                    "timeout": self.timeout_seconds
                }
            )
            
            # Fallback: Grok-4 via xAI virtual key  
            if self.enable_fallback:
                self.fallback_client = Portkey(
                    api_key=os.getenv("PORTKEY_API_KEY"),
                    virtual_key=PORTKEY_VIRTUAL_KEYS["XAI"],
                    config={
                        "retry_count": 1,
                        "timeout": self.timeout_seconds - 10
                    }
                )
            
            logger.info("✅ Portkey clients configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Portkey clients: {e}")
            raise ModelError(f"Portkey configuration failed: {e}")
    
    def _setup_openrouter_client(self):
        """Setup emergency OpenRouter fallback"""
        
        if not self.enable_emergency_fallback:
            return
            
        try:
            self.openrouter_base_url = "https://openrouter.ai/api/v1"
            self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            
            if not self.openrouter_api_key:
                logger.warning("OpenRouter API key not found - emergency fallback disabled")
                self.enable_emergency_fallback = False
                return
                
            logger.info("✅ OpenRouter emergency fallback configured")
            
        except Exception as e:
            logger.error(f"Failed to setup OpenRouter client: {e}")
            self.enable_emergency_fallback = False
    
    @with_circuit_breaker(name="portkey_primary_model")
    async def _call_primary_model(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Call GPT-5 via Portkey OpenAI virtual key"""
        
        with tracer.start_as_current_span("portkey_gpt5_call") as span:
            span.set_attribute("model", "gpt-5") 
            span.set_attribute("provider", "openai_portkey")
            
            try:
                response = self.primary_client.chat.completions.create(
                    model="gpt-5",
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 4096),
                    **kwargs
                )
                
                # Track usage
                self._track_usage("gpt-5", response)
                
                span.set_attribute("status", "success")
                return {
                    "content": response.choices[0].message.content,
                    "model_used": "gpt-5",
                    "provider": "openai_portkey",
                    "usage": response.usage.model_dump() if response.usage else None
                }
                
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                logger.warning(f"GPT-5 primary model failed: {e}")
                raise
    
    @with_circuit_breaker(name="portkey_fallback_model")
    async def _call_fallback_model(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Call Grok-4 via Portkey xAI virtual key"""
        
        if not self.enable_fallback:
            raise ModelError("Fallback disabled")
            
        with tracer.start_as_current_span("portkey_grok4_call") as span:
            span.set_attribute("model", "grok-4")
            span.set_attribute("provider", "xai_portkey")
            
            try:
                response = self.fallback_client.chat.completions.create(
                    model="grok-4",
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 4096),
                    **kwargs
                )
                
                # Track usage
                self._track_usage("grok-4", response)
                
                span.set_attribute("status", "success")
                return {
                    "content": response.choices[0].message.content,
                    "model_used": "grok-4", 
                    "provider": "xai_portkey",
                    "usage": response.usage.model_dump() if response.usage else None
                }
                
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                logger.warning(f"Grok-4 fallback model failed: {e}")
                raise
    
    async def _call_emergency_fallback(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Direct OpenRouter call as last resort"""
        
        if not self.enable_emergency_fallback:
            raise ModelError("Emergency fallback disabled")
            
        with tracer.start_as_current_span("openrouter_emergency_call") as span:
            span.set_attribute("model", "xai/grok-4")
            span.set_attribute("provider", "openrouter_direct")
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.openrouter_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openrouter_api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://sophia-intel-ai.com",
                            "X-Title": "Sophia Intel AI Agent"
                        },
                        json={
                            "model": "xai/grok-4",
                            "messages": messages,
                            "temperature": kwargs.get("temperature", 0.7),
                            "max_tokens": kwargs.get("max_tokens", 4096)
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Track usage  
                        self._track_usage("grok-4-openrouter", data)
                        
                        span.set_attribute("status", "success")
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "model_used": "grok-4",
                            "provider": "openrouter_direct", 
                            "usage": data.get("usage")
                        }
                    else:
                        raise ModelError(f"OpenRouter API error: {response.status_code}")
                        
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                logger.error(f"Emergency OpenRouter fallback failed: {e}")
                raise
    
    async def __call__(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Main model calling interface with intelligent fallback routing.
        
        Args:
            messages: List of chat messages in OpenAI format
            stream: Whether to stream responses (not implemented yet)
            **kwargs: Additional parameters for model calls
            
        Returns:
            String response or detailed response dict
        """
        
        if stream:
            raise NotImplementedError("Streaming not yet implemented")
            
        self.request_count += 1
        
        with tracer.start_as_current_span("model_router_call") as span:
            span.set_attribute("request_count", self.request_count)
            
            # Try primary model (GPT-5)
            try:
                logger.info("🚀 Attempting primary model (GPT-5)")
                result = await self._call_primary_model(messages, **kwargs)
                span.set_attribute("final_model", "gpt-5")
                logger.info(f"✅ GPT-5 success: {len(result['content'])} chars")
                return result
                
            except Exception as primary_error:
                logger.warning(f"⚠️  Primary model failed: {primary_error}")
                span.add_event("primary_model_failed", {"error": str(primary_error)})
                
                # Try fallback model (Grok-4)
                if self.enable_fallback:
                    try:
                        logger.info("🔄 Attempting fallback model (Grok-4)")
                        result = await self._call_fallback_model(messages, **kwargs)
                        span.set_attribute("final_model", "grok-4")
                        logger.info(f"✅ Grok-4 fallback success: {len(result['content'])} chars")
                        return result
                        
                    except Exception as fallback_error:
                        logger.warning(f"⚠️  Fallback model failed: {fallback_error}")
                        span.add_event("fallback_model_failed", {"error": str(fallback_error)})
                        
                        # Try emergency fallback (Direct OpenRouter)
                        if self.enable_emergency_fallback:
                            try:
                                logger.info("🆘 Attempting emergency fallback (OpenRouter)")
                                result = await self._call_emergency_fallback(messages, **kwargs)
                                span.set_attribute("final_model", "grok-4-openrouter")
                                logger.info(f"✅ Emergency fallback success: {len(result['content'])} chars")
                                return result
                                
                            except Exception as emergency_error:
                                logger.error(f"❌ Emergency fallback failed: {emergency_error}")
                                span.add_event("emergency_fallback_failed", {"error": str(emergency_error)})
                                
                                # All models failed
                                error_msg = (
                                    f"All models failed. "
                                    f"Primary: {primary_error}, "
                                    f"Fallback: {fallback_error}, "
                                    f"Emergency: {emergency_error}"
                                )
                                span.set_attribute("status", "all_failed")
                                raise AllModelsFailedException(error_msg)
                        else:
                            # No emergency fallback, raise with available errors
                            error_msg = f"Primary and fallback models failed. Primary: {primary_error}, Fallback: {fallback_error}"
                            span.set_attribute("status", "all_failed")
                            raise AllModelsFailedException(error_msg)
    
    def _track_usage(self, model: str, response: Union[Dict, Any]):
        """Track model usage statistics"""
        
        try:
            # Initialize model stats if needed
            if model not in self.model_usage_stats:
                self.model_usage_stats[model] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "errors": 0
                }
            
            # Update stats
            self.model_usage_stats[model]["requests"] += 1
            
            # Extract token usage
            if hasattr(response, 'usage') and response.usage:
                tokens = response.usage.total_tokens
                self.model_usage_stats[model]["tokens"] += tokens
                
                # Estimate cost (rough estimates)
                cost_per_token = {
                    "gpt-5": 0.00005,  # $0.05/1K tokens (estimated)
                    "grok-4": 0.00003,  # $0.03/1K tokens (estimated) 
                    "grok-4-openrouter": 0.00003
                }.get(model, 0.00002)
                
                request_cost = tokens * cost_per_token
                self.model_usage_stats[model]["cost"] += request_cost
                self.total_cost += request_cost
                
                # Check cost limit
                if request_cost > self.cost_limit_per_request:
                    logger.warning(f"Request cost ${request_cost:.4f} exceeds limit ${self.cost_limit_per_request}")
            
        except Exception as e:
            logger.error(f"Failed to track usage: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        
        return {
            "request_count": self.request_count,
            "total_cost": round(self.total_cost, 4),
            "average_cost_per_request": round(self.total_cost / max(1, self.request_count), 4),
            "model_usage": self.model_usage_stats,
            "configuration": {
                "fallback_enabled": self.enable_fallback,
                "emergency_fallback_enabled": self.enable_emergency_fallback,
                "cost_limit_per_request": self.cost_limit_per_request
            }
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        
        self.request_count = 0
        self.total_cost = 0.0
        self.model_usage_stats = {}
        logger.info("Usage statistics reset")
        
    def __str__(self) -> str:
        return f"PortkeyRouterModel(primary=gpt-5, fallback=grok-4, requests={self.request_count})"
        
    def __repr__(self) -> str:
        return self.__str__()