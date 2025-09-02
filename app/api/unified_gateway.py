"""
Elite Unified Gateway - Consolidates Portkey, OpenRouter, and Together AI
2025 Architecture with Advanced Observability and Smart Caching
"""

import os
import json
import time
import asyncio
import hashlib
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import httpx
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

from app.models.requests import (
    ExecutionResponse, SystemStatus, ComponentHealth,
    MemoryEntry, SwarmResponse
)
from app.core.circuit_breaker import with_circuit_breaker

# Load environment
load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# CORE CONFIGURATION
# =============================================================================

class Environment(Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

class TaskType(Enum):
    """Unified task-based routing"""
    REASONING = "reasoning"
    CREATIVE = "creative"
    CODING = "coding"
    FAST = "fast"
    GENERAL = "general"
    EMBEDDINGS = "embeddings"
    MEMORY = "memory"
    SWARM = "swarm"

class Role(Enum):
    """Agent roles for observability"""
    PLANNER = "planner"
    CRITIC = "critic"
    JUDGE = "judge"
    GENERATOR = "generator"
    RUNNER = "runner"
    COORDINATOR = "coordinator"

@dataclass
class ElitePortkeyConfig:
    """Unified configuration combining all gateway approaches"""
    # Core settings
    environment: Environment = Environment.DEV
    base_url: str = "https://api.portkey.ai/v1"

    # API Keys (virtual keys supported)
    portkey_key: str = ""
    openrouter_vk: str = ""
    together_vk: str = ""
    anthropic_key: str = ""

    # Performance settings
    timeout_ms: int = 30000
    stream_timeout_ms: int = 600000
    max_retries: int = 3

    # Caching settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    semantic_similarity_threshold: float = 0.95

    def __post_init__(self):
        # Load from environment with fallback
        self.portkey_key = os.getenv("PORTKEY_API_KEY") or self.portkey_key
        self.openrouter_vk = os.getenv("VK_OPENROUTER", os.getenv("OPENROUTER_API_KEY")) or self.openrouter_vk
        self.together_vk = os.getenv("VK_TOGETHER", os.getenv("TOGETHER_API_KEY")) or self.together_vk
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY") or self.anthropic_key

        # Validate required keys
        if not self.portkey_key:
            raise ValueError("PORTKEY_API_KEY required")
        if not (self.openrouter_vk or self.anthropic_key):
            raise ValueError("At least one LLM provider required (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)")


@dataclass
class PathwayModel:
    """Model configuration for each pathway"""
    model_name: str
    provider: str  # openrouter, together, anthropic
    virtual_key: str
    max_tokens: int = 4000
    temperature: float = 0.7
    capability_tags: List[str] = None

    def __post_init__(self):
        if self.capability_tags is None:
            self.capability_tags = []


# =============================================================================
# OBSERVABILITY & MONITORING (from portkey_config)
# =============================================================================

@dataclass
class UnifiedObservabilityHeaders:
    """Combined metadata for tracking and monitoring"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: str = "dev"
    feature: Optional[str] = None
    cost_center: Optional[str] = None
    role: Optional[Role] = None
    swarm: Optional[str] = None
    ticket_id: Optional[str] = None
    task_type: Optional[str] = None

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for Portkey"""
        headers = {
            "x-user-id": self.user_id or "",
            "x-session-id": self.session_id or "",
            "x-environment": self.environment,
            "x-timestamp": datetime.now().isoformat(),
            "x-request-id": hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:8]
        }

        if self.feature:
            headers["x-feature"] = self.feature
        if self.cost_center:
            headers["x-cost-center"] = self.cost_center

        # Enhanced metadata for Portkey
        metadata = {}
        if self.role:
            metadata["role"] = self.role.value
        if self.swarm:
            metadata["swarm"] = self.swarm
        if self.ticket_id:
            metadata["ticket"] = self.ticket_id
        if self.task_type:
            metadata["task_type"] = self.task_type

        if metadata:
            headers["x-portkey-metadata"] = json.dumps(metadata)

        return {k: v for k, v in headers.items() if v}  # Remove empty values


# =============================================================================
# ELITE UNIFIED GATEWAY - THE COMBINED POWER
# =============================================================================

class EliteUnifiedGateway:
    """
    Elite Unified Gateway - Combining the best of all worlds:
    - Portkey observability and caching
    - OpenRouter's latest models with virtual keys
    - Together AI embeddings with 32k context
    - Anthropic Claude integration
    - Advanced health monitoring and failover
    """

    def __init__(self, config: Optional[ElitePortkeyConfig] = None):
        self.config = config or ElitePortkeyConfig()
        self._initialized = False

        # Performance tracking
        self.metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "provider_failures": {},
            "response_times": [],
            "cost_savings": 0.0,
            "pathway_usage": {}
        }

        # Pathway configurations (elite 2025 models)
        self._setup_pathways()
        self._setup_clients()

        logger.info("🏗️ Elite Unified Gateway initialized with all providers")

    def _setup_pathways(self):
        """Setup elite 2025 model pathways"""
        self.pathways = {

            # Reasoning - Latest xAI models via OpenRouter
            TaskType.REASONING: PathwayModel(
                model_name="x-ai/grok-2-1212",
                provider="openrouter",
                virtual_key=self.config.openrouter_vk,
                max_tokens=4000,
                temperature=0.3,
                capability_tags=["reasoning", "analysis", "logic", "math"]
            ),

            # Creative - Latest Gemini via OpenRouter
            TaskType.CREATIVE: PathwayModel(
                model_name="google/gemini-2.0-flash-exp",
                provider="openrouter",
                virtual_key=self.config.openrouter_vk,
                max_tokens=6000,
                temperature=0.8,
                capability_tags=["creative", "writing", "art", "design"]
            ),

            # Coding - Claude Sonnet 4 via OpenRouter
            TaskType.CODING: PathwayModel(
                model_name="anthropic/claude-3.5-sonnet-20241022",
                provider="openrouter" if self.config.openrouter_vk else "anthropic",
                virtual_key=self.config.openrouter_vk or self.config.anthropic_key,
                max_tokens=4000,
                temperature=0.2,
                capability_tags=["coding", "debugging", "architecture", "algorithms"]
            ),

            # Fast - GPT-4o Mini via OpenRouter
            TaskType.FAST: PathwayModel(
                model_name="openai/gpt-4o-mini-2024-07-18",
                provider="openrouter",
                virtual_key=self.config.openrouter_vk,
                max_tokens=2000,
                temperature=0.7,
                capability_tags=["fast", "simple", "brief", "quick"]
            ),

            # General - Reliable Claude via OpenRouter
            TaskType.GENERAL: PathwayModel(
                model_name="anthropic/claude-3.5-sonnet-20241022",
                provider="openrouter" if self.config.openrouter_vk else "anthropic",
                virtual_key=self.config.openrouter_vk or self.config.anthropic_key,
                max_tokens=3000,
                temperature=0.7,
                capability_tags=["general", "chat", "help", "advice"]
            ),

            # Embeddings - 32k context via Together AI
            TaskType.EMBEDDINGS: PathwayModel(
                model_name="togethercomputer/m2-bert-80M-32k-retrieval",
                provider="together",
                virtual_key=self.config.together_vk,
                max_tokens=1,  # Not applicable for embeddings
                temperature=0.0,
                capability_tags=["embeddings", "text-embeddings", "semantic-search"]
            ),

            # Memory - Specialized for RAG/retrieval
            TaskType.MEMORY: PathwayModel(
                model_name="openai/text-embedding-3-large",
                provider="openrouter",
                virtual_key=self.config.openrouter_vk,
                max_tokens=1,
                temperature=0.0,
                capability_tags=["memory", "rag", "retrieval", "context"]
            ),

            # Swarm - Coordinator model
            TaskType.SWARM: PathwayModel(
                model_name="x-ai/grok-2-1212",
                provider="openrouter",
                virtual_key=self.config.openrouter_vk,
                max_tokens=2000,
                temperature=0.5,
                capability_tags=["swarm", "coordination", "synthesis", "consensus"]
            )
        }

    def _setup_clients(self):
        """Initialize API clients with Portkey routing"""
        try:
            # Primary client with Portkey
            self.chat_client = OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.portkey_key,
                max_retries=self.config.max_retries,
                timeout=self.config.timeout_ms / 1000
            )

            self.async_chat_client = AsyncOpenAI(
                base_url=self.config.base_url,
                api_key=self.config.portkey_key,
                max_retries=self.config.max_retries,
                timeout=self.config.timeout_ms / 1000
            )

            # HTTP client for custom endpoints
            self.http_client = httpx.AsyncClient(timeout=30.0)

            self._initialized = True

        except Exception as e:
            logger.error(f"Client initialization failed: {e}")
            raise

    @with_circuit_breaker("llm")
    async def execute_smart(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        role: Optional[Role] = None,
        swarm: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ExecutionResponse:
        """Smart execution with automatic routing and failover"""

        start_time = time.time()
        self.metrics["requests_total"] += 1

        try:
            # Get pathway configuration
            pathway = self.pathways[task_type]

            # Track pathway usage
            pathway_key = f"{pathway.provider}:{pathway.model_name}"
            self.metrics["pathway_usage"][pathway_key] = self.metrics["pathway_usage"].get(pathway_key, 0) + 1

            # Prepare observability
            obs = UnifiedObservabilityHeaders(
                role=role,
                swarm=swarm,
                session_id=session_id,
                task_type=task_type.value,
                environment=self.config.environment.value
            )
            headers = obs.to_headers()

            # Portkey configuration
            portkey_config = {
                "strategy": {"mode": "single"},
                "retry": {
                    "attempts": self.config.max_retries,
                    "on_status_codes": [429, 500, 502, 503, 504]
                },
                "cache": {
                    "enabled": self.config.cache_enabled,
                    "mode": "semantic",
                    "ttl": self.config.cache_ttl_seconds,
                    "similarity_threshold": self.config.semantic_similarity_threshold
                },
                "metadata": {
                    "environment": self.config.environment.value,
                    "version": "2025.1"
                }
            }

            headers["x-portkey-config"] = json.dumps(portkey_config)

            # Provider-specific configuration
            if pathway.provider == "openrouter":
                # Use OpenRouter virtual key through Portkey
                provider_config = {
                    "provider": "openrouter",
                    "api_key": self.config.openrouter_vk
                }
            elif pathway.provider == "together":
                provider_config = {
                    "provider": "together",
                    "api_key": self.config.together_vk
                }
            elif pathway.provider == "anthropic":
                provider_config = {
                    "provider": "anthropic",
                    "api_key": self.config.anthropic_key
                }
            else:
                raise ValueError(f"Unsupported provider: {pathway.provider}")

            headers["x-portkey-provider"] = json.dumps(provider_config)

            # Temperature adjustment based on role
            temperature = pathway.temperature
            if role == Role.CRITIC and temperature > 0.1:
                temperature = 0.1
            elif role == Role.JUDGE and temperature > 0.2:
                temperature = 0.2
            elif role == Role.PLANNER and temperature > 0.3:
                temperature = 0.3

            # Prepare payload
            payload = {
                "model": pathway.model_name,
                "messages": messages,
                "max_tokens": pathway.max_tokens,
                "temperature": temperature,
                **kwargs
            }

            # Execute through Portkey
            response = await self.async_chat_client.chat.completions.create(
                **payload,
                extra_headers=headers
            )

            # Track response time
            response_time = time.time() - start_time
            self.metrics["response_times"].append(response_time)

            # Check for cache hit
            cache_hit = "cache_hit" in str(response).lower()
            if cache_hit:
                self.metrics["cache_hits"] += 1
                self.metrics["cost_savings"] += self._estimate_cost_saving(task_type)
            else:
                self.metrics["cache_misses"] += 1

            # Extract result
            if hasattr(response, 'choices') and response.choices:
                result = response.choices[0].message.content
            else:
                result = str(response)

            return ExecutionResponse(
                execution_id=obs.to_headers().get("x-request-id", ""),
                status="completed",
                result=result,
                metrics={
                    "response_time_seconds": response_time,
                    "model_used": pathway.model_name,
                    "provider": pathway.provider,
                    "cache_hit": cache_hit,
                    "task_type": task_type.value,
                    "role": role.value if role else None
                },
                duration_seconds=response_time,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Smart execution failed: {e}")

            # Track failure
            provider_key = pathway.provider if 'pathway' in locals() else "unknown"
            self.metrics["provider_failures"][provider_key] = self.metrics["provider_failures"].get(provider_key, 0) + 1

            # Try failover if possible
            return await self._failover_execution(messages, task_type, role, swarm, session_id, **kwargs)

    async def _failover_execution(
        self,
        messages: List[Dict[str, str]],
        original_task_type: TaskType,
        role: Optional[Role] = None,
        swarm: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ExecutionResponse:
        """Smart failover to alternative pathways"""

        # Define failover mappings
        failover_map = {
            TaskType.REASONING: [TaskType.GENERAL, TaskType.FAST],
            TaskType.CREATIVE: [TaskType.GENERAL, TaskType.FAST],
            TaskType.CODING: [TaskType.FAST, TaskType.GENERAL],
            TaskType.FAST: [TaskType.GENERAL],
            TaskType.GENERAL: [TaskType.FAST],
            TaskType.EMBEDDINGS: [],  # No easy failover for embeddings
            TaskType.MEMORY: [TaskType.EMBEDDINGS],
            TaskType.SWARM: [TaskType.REASONING]
        }

        fallback_types = failover_map.get(original_task_type, [TaskType.GENERAL])

        for fallback_type in fallback_types:
            try:
                logger.info(f"Attempting failover from {original_task_type.value} to {fallback_type.value}")
                return await self.execute_smart(
                    messages, fallback_type, role, swarm, session_id, **kwargs
                )
            except Exception as fallback_error:
                logger.warning(f"Failover to {fallback_type.value} failed: {fallback_error}")
                continue

        # All failovers failed
        execution_id = hashlib.sha256(f"{time.time()}:failure".encode()).hexdigest()[:8]
        return ExecutionResponse(
            execution_id=execution_id,
            status="failed",
            result=None,
            metrics={"error": "all_failover_attempts_failed", "original_task": original_task_type.value},
            duration_seconds=time.time() - time.time(),  # Will be set by caller
            timestamp=datetime.now()
        )

    @with_circuit_breaker("embeddings")
    async def generate_embeddings(
        self,
        texts: List[str],
        task_type: TaskType = TaskType.EMBEDDINGS
    ) -> ExecutionResponse:
        """Generate embeddings with smart routing"""

        try:
            pathway = self.pathways[task_type]

            headers = {
                "x-portkey-api-key": self.config.portkey_key,
                "x-portkey-config": json.dumps({
                    "strategy": {"mode": "single"},
                    "cache": {
                        "enabled": True,
                        "mode": "semantic",
                        "ttl": self.config.cache_ttl_seconds * 2,  # Longer for embeddings
                        "similarity_threshold": self.config.semantic_similarity_threshold
                    }
                }),
                "x-portkey-provider": json.dumps({
                    "provider": "together",
                    "api_key": self.config.together_vk
                }),
                "content-type": "application/json"
            }

            payload = {
                "input": texts,
                "model": pathway.model_name
            }

            # Make embedding request through Portkey
            response = await self.http_client.post(
                f"{self.config.base_url}/embeddings",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Embedding request failed: {response.status_code}",
                    request=response.request,
                    response=response
                )

            result = response.json()
            embeddings = [d["embedding"] for d in result.get("data", [])]

            return ExecutionResponse(
                execution_id=hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:8],
                status="completed",
                result={"embeddings": embeddings, "model": pathway.model_name},
                metrics={
                    "embeddings_count": len(embeddings),
                    "total_texts": len(texts),
                    "provider": "together_ai"
                },
                duration_seconds=time.time() - time.time(),
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            execution_id = hashlib.sha256(f"{time.time()}:failure".encode()).hexdigest()[:8]
            return ExecutionResponse(
                execution_id=execution_id,
                status="failed",
                result=None,
                metrics={"error": str(e)},
                duration_seconds=0,
                timestamp=datetime.now()
            )

    @with_circuit_breaker("health_check")
    async def health_check(self) -> SystemStatus:
        """Comprehensive health check across all providers"""

        components = {}

        # Test each pathway
        for task_type, pathway in self.pathways.items():
            try:
                if task_type == TaskType.EMBEDDINGS:
                    # Test embeddings
                    result = await self.generate_embeddings(["health check"])
                    status = "healthy" if result.status == "completed" else "degraded"
                else:
                    # Test chat completion
                    test_messages = [{"role": "user", "content": "Say 'OK' if you can hear me"}]
                    result = await self.execute_smart(test_messages, task_type)
                    status = "healthy" if result.status == "completed" and "OK" in str(result.result) else "degraded"

                components[task_type.value] = ComponentHealth(
                    name=task_type.value,
                    status=status,
                    last_check=datetime.now(),
                    response_time_seconds=result.duration_seconds if hasattr(result, 'duration_seconds') else None,
                    metrics=result.metrics if hasattr(result, 'metrics') else {}
                )

            except Exception as e:
                components[task_type.value] = ComponentHealth(
                    name=task_type.value,
                    status="unhealthy",
                    last_check=datetime.now(),
                    error_message=str(e)
                )

        # Overall system health
        healthy_count = sum(1 for comp in components.values() if comp.status == "healthy")
        total_count = len(components)

        return SystemStatus(
            status="healthy" if healthy_count == total_count else "degraded",
            version="2025.1",
            uptime_seconds=None,  # Could be calculated from PID start time
            components=components,
            metrics=self.metrics,
            timestamp=datetime.now()
        )

    def get_gateway_metrics(self) -> Dict[str, Any]:
        """Get comprehensive gateway performance metrics"""
        total_requests = self.metrics["requests_total"]
        cache_hits = self.metrics["cache_hits"]
        cache_misses = self.metrics["cache_misses"]

        return {
            "total_requests": total_requests,
            "cache_hit_rate": (cache_hits / max(total_requests, 1)) * 100,
            "cache_efficiency": cache_hits / max(cache_hits + cache_misses, 1),
            "pathway_usage": self.metrics["pathway_usage"],
            "provider_failures": self.metrics["provider_failures"],
            "estimated_cost_saved": f"${self.metrics['cost_savings']:.4f}",
            "avg_response_time": sum(self.metrics["response_times"]) / max(len(self.metrics["response_times"]), 1),
            "config": {
                "environment": self.config.environment.value,
                "cache_enabled": self.config.cache_enabled,
                "timeout_ms": self.config.timeout_ms,
                "max_retries": self.config.max_retries
            }
        }

    def _estimate_cost_saving(self, task_type: TaskType) -> float:
        """Estimate cost savings for cached requests"""
        # Very rough estimation based on typical costs
        cost_map = {
            TaskType.REASONING: 0.03,
            TaskType.CREATIVE: 0.02,
            TaskType.CODING: 0.015,
            TaskType.FAST: 0.001,
            TaskType.GENERAL: 0.002,
            TaskType.EMBEDDINGS: 0.0001,
            TaskType.MEMORY: 0.0005,
            TaskType.SWARM: 0.005
        }
        return cost_map.get(task_type, 0.001)

    async def close(self):
        """Cleanup resources"""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_unified_gateway = None

@with_circuit_breaker("gateway_init")
def get_elite_unified_gateway() -> EliteUnifiedGateway:
    """Get or create the global Elite Unified Gateway instance"""
    global _unified_gateway
    if _unified_gateway is None:
        _unified_gateway = EliteUnifiedGateway()
    return _unified_gateway

# Convenience instance
try:
    elite_gateway = EliteUnifiedGateway()
except Exception as e:
    logger.warning(f"Elite Unified Gateway lazy loading: {e}")
    elite_gateway = None


# =============================================================================
# PROTOCOLS AND VALIDATION
# =============================================================================

def validate_gateway_config() -> Dict[str, Any]:
    """Validate gateway configuration and dependencies"""
    issues = []

    # Check required environment variables
    required_vars = ["PORTKEY_API_KEY"]
    optional_vars = ["VK_OPENROUTER", "VK_TOGETHER", "OPENROUTER_API_KEY", "TOGETHER_API_KEY", "ANTHROPIC_API_KEY"]

    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing required: {var}")

    available_providers = []
    for var in optional_vars:
        if os.getenv(var):
            available_providers.append(var.split('_')[0].lower())

    if not available_providers:
        issues.append("No LLM providers configured")

    if issues:
        status = "configuration_incomplete"
    else:
        status = "ready"

    return {
        "status": status,
        "issues": issues,
        "available_providers": available_providers,
        "config_valid": len(issues) == 0
    }


# =============================================================================
# MODEL RECOMMENDATIONS (from portkey_config)
# =============================================================================

MODEL_RECOMMENDATIONS = {
    Role.PLANNER: {
        "preferred_task_types": [TaskType.REASONING, TaskType.GENERAL],
        "temperature": 0.3,
        "max_tokens": 2000
    },
    Role.CRITIC: {
        "preferred_task_types": [TaskType.REASONING, TaskType.CODING],
        "temperature": 0.1,
        "max_tokens": 1500
    },
    Role.JUDGE: {
        "preferred_task_types": [TaskType.REASONING, TaskType.GENERAL],
        "temperature": 0.2,
        "max_tokens": 1000
    },
    Role.GENERATOR: {
        "fast": {"task_type": TaskType.FAST, "temperature": 0.7},
        "creative": {"task_type": TaskType.CREATIVE, "temperature": 0.8},
        "balanced": {"task_type": TaskType.GENERAL, "temperature": 0.7}
    },
    Role.RUNNER: {
        "preferred_task_types": [TaskType.FAST, TaskType.CODING],
        "temperature": 0.5,
        "max_tokens": 3000
    },
    Role.COORDINATOR: {
        "preferred_task_types": [TaskType.SWARM, TaskType.REASONING],
        "temperature": 0.4,
        "max_tokens": 2500
    }
}


if __name__ == "__main__":
    print("🧪 Validating Elite Unified Gateway configuration...")
    validation = validate_gateway_config()
    print(f"Status: {validation['status']}")
    if validation['issues']:
        for issue in validation['issues']:
            print(f"⚠️  {issue}")
    if validation['available_providers']:
        print(f"✅ Providers: {', '.join(validation['available_providers'])}")
    print("\n🏗️  Gateway will initialize with available providers on first API call.")
