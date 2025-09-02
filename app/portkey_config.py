"""
Enhanced Portkey Gateway Configuration with Observability.
Implements best practices for routing, caching, and monitoring.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI, AsyncOpenAI
import hashlib
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

# ============================================
# Configuration Constants
# ============================================

class Environment(Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

class Role(Enum):
    PLANNER = "planner"
    CRITIC = "critic"
    JUDGE = "judge"
    GENERATOR = "generator"
    RUNNER = "runner"

@dataclass
class PortkeyConfig:
    """Portkey configuration with best practices."""
    
    # Base URLs
    base_url: str = "https://api.portkey.ai/v1"
    
    # Virtual Keys (from environment)
    openrouter_vk: str = ""
    together_vk: str = ""
    
    # Environment
    environment: Environment = Environment.DEV
    
    # Retry configuration
    max_retries: int = 3
    retry_status_codes: List[int] = None
    
    # Caching
    semantic_cache_enabled: bool = True
    cache_max_age_seconds: int = 3600
    
    # Timeouts (ms)
    timeout_ms: int = 30000
    stream_timeout_ms: int = 600000
    
    @with_circuit_breaker("external_api")
    def __post_init__(self):
        # Load VKs from environment
        self.openrouter_vk = os.getenv("VK_OPENROUTER", "")
        self.together_vk = os.getenv("VK_TOGETHER", "")
        
        # Default retry codes
        if self.retry_status_codes is None:
            self.retry_status_codes = [429, 500, 502, 503, 504]
        
        # Set environment from env var
        env_str = os.getenv("ENVIRONMENT", "dev").lower()
        self.environment = Environment(env_str) if env_str in ["dev", "staging", "prod"] else Environment.DEV

# ============================================
# Observability Headers
# ============================================

@dataclass
class ObservabilityHeaders:
    """Metadata headers for tracking and monitoring."""
    
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    feature: Optional[str] = None
    cost_center: Optional[str] = None
    role: Optional[Role] = None
    swarm: Optional[str] = None
    ticket_id: Optional[str] = None
    
    @with_circuit_breaker("external_api")
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers."""
        headers = {}
        
        if self.user_id:
            headers["x-user-id"] = self.user_id
        if self.session_id:
            headers["x-session-id"] = self.session_id
        if self.environment:
            headers["x-environment"] = self.environment
        if self.feature:
            headers["x-feature"] = self.feature
        if self.cost_center:
            headers["x-cost-center"] = self.cost_center
            
        # Portkey-specific metadata
        metadata = {}
        if self.role:
            metadata["role"] = self.role.value
        if self.swarm:
            metadata["swarm"] = self.swarm
        if self.ticket_id:
            metadata["ticket"] = self.ticket_id
            
        if metadata:
            headers["x-portkey-metadata"] = json.dumps(metadata)
            
        return headers

# ============================================
# Routing Strategies
# ============================================

class LoadBalanceStrategy:
    """Load balancing across multiple providers."""
    
    @with_circuit_breaker("external_api")
    def __init__(self, targets: List[Dict[str, Any]]):
        self.targets = targets
        
    def to_config(self) -> Dict[str, Any]:
        return {
            "mode": "loadbalance",
            "targets": self.targets
        }

class FallbackStrategy:
    """Fallback to alternative providers on failure."""
    
    def __init__(self, targets: List[Dict[str, Any]]):
        self.targets = targets
        
    def to_config(self) -> Dict[str, Any]:
        return {
            "strategy": "fallback",
            "targets": self.targets
        }

class ABTestStrategy:
    """A/B testing between models."""
    
    def __init__(self, targets: List[Dict[str, Any]], metric: str = "task_success_rate"):
        self.targets = targets
        self.metric = metric
        
    def to_config(self) -> Dict[str, Any]:
        return {
            "mode": "ab_test",
            "targets": self.targets,
            "metric": self.metric
        }

# ============================================
# Enhanced Portkey Client
# ============================================

class PortkeyGateway:
    """Enhanced Portkey gateway with observability and routing."""
    
    def __init__(self, config: Optional[PortkeyConfig] = None):
        self.config = config or PortkeyConfig()
        self._setup_clients()
        
    @with_circuit_breaker("external_api")
    def _setup_clients(self):
        """Initialize OpenAI clients with Portkey configuration."""
        # Get the real Portkey API key from environment
        portkey_key = os.getenv("PORTKEY_API_KEY")
        if not portkey_key:
            raise ValueError("PORTKEY_API_KEY environment variable is required")
        
        # Chat client (OpenRouter via Portkey)
        self.chat_client = OpenAI(
            base_url=self.config.base_url,
            api_key=portkey_key,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout_ms / 1000  # Convert to seconds
        )
        
        self.async_chat_client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key=portkey_key,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout_ms / 1000
        )
        
        # Embedding client (also via Portkey)
        self.embed_client = OpenAI(
            base_url=self.config.base_url,
            api_key=portkey_key,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout_ms / 1000
        )
        
        self.async_embed_client = AsyncOpenAI(
            base_url=self.config.base_url,
            api_key=portkey_key,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout_ms / 1000
        )
    
    @with_circuit_breaker("external_api")
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5",
        temperature: float = 0.7,
        role: Optional[Role] = None,
        swarm: Optional[str] = None,
        ticket_id: Optional[str] = None,
        routing_strategy: Optional[Any] = None,
        **kwargs
    ) -> str:
        """
        Enhanced chat completion with observability.
        
        Args:
            messages: Chat messages
            model: Model identifier
            temperature: Sampling temperature (lower for critic/judge)
            role: Agent role for tracking
            swarm: Swarm identifier
            ticket_id: Ticket/task identifier
            routing_strategy: Optional routing strategy
            **kwargs: Additional OpenAI parameters
        
        Returns:
            Assistant's response
        """
        # Build observability headers
        headers = ObservabilityHeaders(
            environment=self.config.environment.value,
            role=role,
            swarm=swarm,
            ticket_id=ticket_id,
            session_id=self._generate_session_id()
        ).to_headers()
        
        # Apply role-specific temperature
        if role == Role.CRITIC:
            temperature = min(temperature, 0.1)  # Very low for consistency
        elif role == Role.JUDGE:
            temperature = min(temperature, 0.2)  # Low for reliability
        elif role == Role.PLANNER:
            temperature = min(temperature, 0.3)  # Structured planning
        
        # Add routing strategy if provided
        if routing_strategy:
            headers["x-portkey-config"] = json.dumps(routing_strategy.to_config())
        
        # Add cache control for read-heavy operations
        if role in [Role.PLANNER, Role.CRITIC] and self.config.semantic_cache_enabled:
            headers["x-portkey-cache"] = json.dumps({
                "mode": "semantic",
                "max_age": self.config.cache_max_age_seconds
            })
        
        # Add Portkey config for OpenRouter
        config = {
            "provider": "openrouter", 
            "api_key": os.getenv('OPENROUTER_API_KEY')
        }
        headers["x-portkey-config"] = json.dumps(config)
        
        # Make the request
        response = self.chat_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            extra_headers=headers,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    @with_circuit_breaker("external_api")
    async def achat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5",
        temperature: float = 0.7,
        role: Optional[Role] = None,
        swarm: Optional[str] = None,
        ticket_id: Optional[str] = None,
        routing_strategy: Optional[Any] = None,
        stream: bool = False,
        **kwargs
    ):
        """Async chat with streaming support."""
        # Build headers
        headers = ObservabilityHeaders(
            environment=self.config.environment.value,
            role=role,
            swarm=swarm,
            ticket_id=ticket_id,
            session_id=self._generate_session_id()
        ).to_headers()
        
        # Apply role-specific temperature
        if role == Role.CRITIC:
            temperature = min(temperature, 0.1)
        elif role == Role.JUDGE:
            temperature = min(temperature, 0.2)
        elif role == Role.PLANNER:
            temperature = min(temperature, 0.3)
        
        # Streaming configuration
        if stream:
            headers["x-portkey-stream"] = "true"
            kwargs["stream"] = True
        
        # Add Portkey config for OpenRouter
        config = {
            "provider": "openrouter", 
            "api_key": os.getenv('OPENROUTER_API_KEY')
        }
        headers["x-portkey-config"] = json.dumps(config)
        
        response = await self.async_chat_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            extra_headers=headers,
            **kwargs
        )
        
        if stream:
            return response  # Return generator for streaming
        else:
            return response.choices[0].message.content
    
    @with_circuit_breaker("external_api")
    def embed(
        self,
        texts: List[str],
        model: str = "BAAI/bge-large-en-v1.5",
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings with caching.
        
        Args:
            texts: List of texts to embed
            model: Embedding model
            **kwargs: Additional parameters
        
        Returns:
            List of embedding vectors
        """
        headers = ObservabilityHeaders(
            environment=self.config.environment.value,
            feature="embedding",
            session_id=self._generate_session_id()
        ).to_headers()
        
        # Enable caching for embeddings
        if self.config.semantic_cache_enabled:
            headers["x-portkey-cache"] = json.dumps({
                "mode": "simple",
                "max_age": self.config.cache_max_age_seconds * 2  # Longer for embeddings
            })
        
        response = self.embed_client.embeddings.create(
            model=model,
            input=texts,
            extra_headers=headers,
            **kwargs
        )
        
        return [d.embedding for d in response.data]
    
    async def aembed(
        self,
        texts: List[str],
        model: str = "BAAI/bge-large-en-v1.5",
        batch_size: int = 100,
        **kwargs
    ) -> List[List[float]]:
        """Async embeddings with batching."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            headers = ObservabilityHeaders(
                environment=self.config.environment.value,
                feature="embedding",
                session_id=self._generate_session_id()
            ).to_headers()
            
            response = await self.async_embed_client.embeddings.create(
                model=model,
                input=batch,
                extra_headers=headers,
                **kwargs
            )
            
            all_embeddings.extend([d.embedding for d in response.data])
        
        return all_embeddings
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = str(time.time())
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]

# ============================================
# Default Gateway Instance
# ============================================

# Lazy gateway initialization
_gateway = None

@with_circuit_breaker("external_api")
def get_gateway():
    """Get or create the global gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = PortkeyGateway()
    return _gateway

# Create gateway instance for backward compatibility
try:
    gateway = PortkeyGateway()
except:
    # If initialization fails, use lazy loading
    gateway = None

# ============================================
# Model Recommendations by Role
# ============================================

MODEL_RECOMMENDATIONS = {
    Role.PLANNER: {
        "default": "qwen/qwen3-30b-a3b",
        "alternatives": ["openai/gpt-5", "x-ai/grok-4"],
        "temperature": 0.3
    },
    Role.CRITIC: {
        "default": "x-ai/grok-4",
        "alternatives": ["openai/gpt-5", "anthropic/claude-sonnet-4"],
        "temperature": 0.1
    },
    Role.JUDGE: {
        "default": "openai/gpt-5",
        "alternatives": ["x-ai/grok-4", "qwen/qwen3-30b-a3b"],
        "temperature": 0.2
    },
    Role.GENERATOR: {
        "fast": ["google/gemini-2.5-flash", "z-ai/glm-4.5-air"],
        "heavy": ["openai/gpt-5", "x-ai/grok-4"],
        "balanced": ["google/gemini-2.5-pro", "anthropic/claude-sonnet-4"],
        "temperature": 0.7
    }
}

# ============================================
# Guardrails Configuration
# ============================================

class Guardrails:
    """Guardrail configurations for content safety."""
    
    PII_DETECTION = "pii-detection-guardrail"
    CONTENT_MODERATION = "content-moderation-guardrail"
    PROMPT_INJECTION = "prompt-injection-detection"
    
    @staticmethod
    def get_before_hooks() -> List[str]:
        """Hooks to run before request."""
        return [Guardrails.PII_DETECTION, Guardrails.PROMPT_INJECTION]
    
    @staticmethod
    def get_after_hooks() -> List[str]:
        """Hooks to run after request."""
        return [Guardrails.CONTENT_MODERATION]