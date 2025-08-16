"""
AI Router - Intelligent Model Selection and Routing
Implements sophisticated AI model routing based on task characteristics,
performance requirements, and cost optimization with Lambda Inference API and OpenRouter.
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import numpy as np
from loguru import logger

from config.config import settings


class TaskType(str, Enum):
    """Task type classification for optimal model selection"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    CREATIVE_WRITING = "creative_writing"
    REASONING = "reasoning"
    MATH = "math"
    GENERAL_CHAT = "general_chat"
    FUNCTION_CALLING = "function_calling"
    STRUCTURED_OUTPUT = "structured_output"


class ModelProvider(str, Enum):
    """Supported AI model providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    GROK = "grok"
    QWEN = "qwen"
    KIMI = "kimi"
    ZHIPUAI = "z-ai"


@dataclass
class ModelCapability:
    """Model capability and performance characteristics"""

    provider: ModelProvider
    model_name: str
    max_tokens: int
    cost_per_1k_tokens: float
    avg_response_time: float
    quality_score: float
    specialties: List[TaskType]
    context_window: int
    supports_function_calling: bool
    supports_structured_output: bool
    rate_limit_rpm: int


@dataclass
class TaskRequest:
    """Task request with routing metadata"""

    prompt: str
    task_type: TaskType
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    priority: str = "normal"  # low, normal, high, critical
    cost_preference: str = "balanced"  # cost_optimized, balanced, performance_optimized
    latency_requirement: str = "normal"  # low_latency, normal, batch
    quality_requirement: str = "high"  # basic, good, high, premium
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RoutingDecision:
    """AI Router decision with reasoning"""

    selected_provider: ModelProvider
    selected_model: str
    confidence_score: float
    reasoning: str
    estimated_cost: float
    estimated_latency: float
    fallback_options: List[Tuple[ModelProvider, str]]


class AIRouter:
    """
    Intelligent AI model router that selects optimal models based on
    task characteristics, performance requirements, and cost considerations.
    """

    def __init__(self):
        self.models = self._initialize_model_registry()
        self.performance_history = {}
        self.cost_tracking = {}
        self.failure_tracking = {}
        self.session = None

    def _initialize_model_registry(self) -> Dict[str, ModelCapability]:
        """Initialize the model registry with Claude Sonnet 4 as primary model"""
        return {
            # Primary Model - Claude Sonnet 4 (Anthropic)
            "claude-sonnet-4": ModelCapability(
                provider=ModelProvider.OPENROUTER,
                model_name="anthropic/claude-sonnet-4",
                max_tokens=8192,
                cost_per_1k_tokens=0.003,
                avg_response_time=2.0,
                quality_score=0.98,
                specialties=[
                    TaskType.CODE_GENERATION,
                    TaskType.REASONING,
                    TaskType.ANALYSIS,
                    TaskType.CREATIVE_WRITING,
                    TaskType.DOCUMENTATION,
                    TaskType.FUNCTION_CALLING,
                ],
                context_window=500000,  # 500B tokens
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=15000,
            ),
            # Embedding Specialist - For vector search and semantic tasks only
            "embedding-model": ModelCapability(
                provider=ModelProvider.OPENROUTER,
                model_name="text-embedding-3-large",
                max_tokens=8192,
                cost_per_1k_tokens=0.00013,
                avg_response_time=0.5,
                quality_score=0.85,
                specialties=[TaskType.EMBEDDING, TaskType.SEMANTIC_SEARCH],
                context_window=8192,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=100000,
            ),
            # Fallback Models - Only for specific edge cases
            "deepseek-v3-fallback": ModelCapability(
                provider=ModelProvider.OPENROUTER,
                model_name="deepseek/deepseek-v3-0324",
                max_tokens=8192,
                cost_per_1k_tokens=0.0014,
                avg_response_time=1.8,
                quality_score=0.90,
                specialties=[TaskType.MATH, TaskType.CODE_REVIEW],
                context_window=173000,  # 173B tokens
                supports_function_calling=False,
                supports_structured_output=True,
                rate_limit_rpm=30000,
            ),
            "gemini-flash-fallback": ModelCapability(
                provider=ModelProvider.OPENROUTER,
                model_name="google/gemini-2.0-flash",
                max_tokens=8192,
                cost_per_1k_tokens=0.0002,
                avg_response_time=1.2,
                quality_score=0.88,
                specialties=[TaskType.GENERAL_CHAT, TaskType.QUICK_TASKS],
                context_window=272000,  # 272B tokens
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=60000,
            ),
        }

    async def route_request(self, request: TaskRequest) -> RoutingDecision:
        """
        Route request to the optimal model with Claude Sonnet 4 as primary choice
        """
        logger.info(f"Routing request for task type: {request.task_type}")

        try:
            # Special case: Embedding tasks go to embedding model
            if request.task_type == TaskType.EMBEDDING or request.task_type == TaskType.SEMANTIC_SEARCH:
                selected_model = "embedding-model"
                confidence = 1.0
                reasoning = "Specialized embedding model for vector search tasks"

            # Special case: Pure math tasks can use DeepSeek V3 for cost optimization
            elif (
                request.task_type == TaskType.MATH
                and request.preferences.cost_preference == CostPreference.MINIMAL
                and len(request.prompt) < 4000
            ):  # Only for shorter math problems
                selected_model = "deepseek-v3-fallback"
                confidence = 0.85
                reasoning = "Cost-optimized DeepSeek V3 for mathematical computations"

            # Special case: Very simple, quick tasks can use Gemini Flash
            elif (
                request.task_type == TaskType.GENERAL_CHAT
                and request.preferences.cost_preference == CostPreference.MINIMAL
                and len(request.prompt) < 500
            ):  # Very short prompts only
                selected_model = "gemini-flash-fallback"
                confidence = 0.80
                reasoning = "Fast and cost-effective Gemini Flash for simple queries"

            # Default: Claude Sonnet 4 for everything else (95%+ of use cases)
            else:
                selected_model = "claude-sonnet-4"
                confidence = 0.98
                reasoning = "Claude Sonnet 4 - Primary model for comprehensive AI capabilities"

            # Get model capability
            model_capability = self.model_registry[selected_model]

            # Calculate estimated cost and latency
            estimated_tokens = len(request.prompt.split()) * 1.3  # Rough token estimation
            estimated_cost = (estimated_tokens / 1000) * model_capability.cost_per_1k_tokens
            estimated_latency = model_capability.avg_response_time * 1000  # Convert to ms

            # Create fallback chain (always Claude Sonnet 4 first, then others)
            fallback_options = []
            if selected_model != "claude-sonnet-4":
                fallback_options.append(("openrouter", "anthropic/claude-sonnet-4"))
            if selected_model != "deepseek-v3-fallback":
                fallback_options.append(("openrouter", "deepseek/deepseek-v3-0324"))
            if selected_model != "gemini-flash-fallback":
                fallback_options.append(("openrouter", "google/gemini-2.0-flash"))

            decision = RoutingDecision(
                selected_provider=model_capability.provider.value,
                selected_model=model_capability.model_name,
                confidence_score=confidence,
                reasoning=reasoning,
                estimated_cost=estimated_cost,
                estimated_latency_ms=int(estimated_latency),
                fallback_options=fallback_options[:2],  # Limit to 2 fallbacks
            )

            logger.info(
                f"Selected {model_capability.provider.value}:{model_capability.model_name} "
                f"with confidence {confidence:.3f}"
            )

            return decision

        except Exception as e:
            logger.error(f"Error in routing decision: {e}")
            # Emergency fallback to Claude Sonnet 4
            return RoutingDecision(
                selected_provider="openrouter",
                selected_model="anthropic/claude-sonnet-4",
                confidence_score=0.95,
                reasoning="Emergency fallback to Claude Sonnet 4 due to routing error",
                estimated_cost=0.01,
                estimated_latency_ms=2000,
                fallback_options=[("openrouter", "google/gemini-2.0-flash")],
            )

    async def execute_task(self, request: TaskRequest, decision: RoutingDecision) -> Any:
        """
        Execute a task using the selected model from routing decision with real API calls

        Args:
            request: The original task request
            decision: The routing decision with selected model

        Returns:
            Task execution result
        """
        start_time = time.time()
        try:
            # Determine API endpoint and headers based on provider
            if decision.selected_model.startswith("lambda-"):
                # Lambda Inference API
                api_url = "https://api.lambda.ai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {os.getenv('LAMBDA_API_KEY')}", "Content-Type": "application/json"}
                # Map lambda model names to actual API model names
                model_name = decision.selected_model.replace("lambda-", "")
            else:
                # OpenRouter API
                api_url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://sophia-intel.ai",
                    "X-Title": "SOPHIA Intel AI Router",
                }
                model_name = decision.selected_model

            # Prepare the API request payload
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_tokens or 2000,
                "temperature": request.temperature,
                "stream": False,
            }

            # Add context if provided
            if request.context:
                payload["messages"].insert(0, {"role": "system", "content": request.context})

            # Make the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_content = result["choices"][0]["message"]["content"]

                        # Calculate actual cost based on usage
                        usage = result.get("usage", {})
                        actual_cost = self._calculate_actual_cost(usage, decision)

                        # Record successful execution
                        await self.record_performance(
                            decision.selected_provider,
                            decision.selected_model,
                            success=True,
                            response_time=time.time() - start_time,
                            cost=actual_cost,
                        )

                        logger.info(f"Task executed successfully using {decision.selected_model}")

                        # Return structured result
                        class TaskResult:
                            def __init__(
                                self, content, provider, model, confidence, cost, reasoning, execution_time, usage
                            ):
                                self.content = content
                                self.provider = provider
                                self.model = model
                                self.confidence = confidence
                                self.cost = cost
                                self.reasoning = reasoning
                                self.execution_time = execution_time
                                self.usage = usage
                                self.status = "success"

                        return TaskResult(
                            content=response_content,
                            provider=decision.selected_provider.value,
                            model=decision.selected_model,
                            confidence=decision.confidence_score,
                            cost=actual_cost,
                            reasoning=decision.reasoning,
                            execution_time=time.time() - start_time,
                            usage=usage,
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")

        except Exception as e:
            execution_time = time.time() - start_time

            # Record failure
            await self.record_failure(decision.selected_provider, decision.selected_model)
            logger.error(f"Task execution failed: {e}")

            # Try fallback if available
            if decision.fallback_options:
                logger.info(f"Attempting fallback to {decision.fallback_options[0]}")
                fallback_provider, fallback_model = decision.fallback_options[0]

                # Create fallback decision
                fallback_decision = RoutingDecision(
                    selected_provider=fallback_provider,
                    selected_model=fallback_model,
                    confidence_score=0.5,
                    reasoning="Fallback due to primary model failure",
                    estimated_cost=decision.estimated_cost,
                    estimated_latency=decision.estimated_latency,
                    fallback_options=decision.fallback_options[1:],
                )

                # Recursive call with fallback
                return await self.execute_task(request, fallback_decision)

            # Return error result if no fallbacks available
            class ErrorResult:
                def __init__(self, error_msg, provider, model, execution_time):
                    self.content = f"Error: {error_msg}"
                    self.status = "error"
                    self.provider = provider
                    self.model = model
                    self.error = error_msg
                    self.execution_time = execution_time

            return ErrorResult(str(e), decision.selected_provider.value, decision.selected_model, execution_time)

    def _calculate_actual_cost(self, usage: Dict[str, Any], decision: RoutingDecision) -> float:
        """Calculate actual cost based on API usage response"""
        if not usage:
            return decision.estimated_cost

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        # Get model cost per 1k tokens
        model_key = f"{decision.selected_provider.value}:{decision.selected_model}"
        if model_key in self.models:
            cost_per_1k = self.models[model_key].cost_per_1k_tokens
        else:
            # Fallback to estimated cost
            return decision.estimated_cost

        return (total_tokens / 1000) * cost_per_1k

    async def _score_model(self, model: ModelCapability, request: TaskRequest) -> float:
        """Score a model's suitability for a given request"""
        score = 0.0

        # Task type specialty bonus
        if request.task_type in model.specialties:
            score += 0.3

        # Quality requirement matching
        quality_weights = {"basic": 0.1, "good": 0.2, "high": 0.3, "premium": 0.4}
        quality_weight = quality_weights.get(request.quality_requirement, 0.2)
        score += model.quality_score * quality_weight

        # Cost preference matching
        cost_score = await self._calculate_cost_score(model, request)
        score += cost_score * 0.2

        # Latency requirement matching
        latency_score = await self._calculate_latency_score(model, request)
        score += latency_score * 0.15

        # Capability requirements
        if request.metadata and request.metadata.get("requires_function_calling"):
            if model.supports_function_calling:
                score += 0.1
            else:
                score -= 0.3

        if request.metadata and request.metadata.get("requires_structured_output"):
            if model.supports_structured_output:
                score += 0.1
            else:
                score -= 0.2

        # Historical performance bonus
        performance_bonus = await self._get_performance_bonus(model)
        score += performance_bonus * 0.1

        # Availability penalty (if model has recent failures)
        availability_penalty = await self._get_availability_penalty(model)
        score -= availability_penalty

        return max(0.0, min(1.0, score))

    async def _calculate_cost_score(self, model: ModelCapability, request: TaskRequest) -> float:
        """Calculate cost score based on preference"""
        if request.cost_preference == "cost_optimized":
            # Prefer cheaper models
            max_cost = max(m.cost_per_1k_tokens for m in self.models.values())
            return 1.0 - (model.cost_per_1k_tokens / max_cost)
        elif request.cost_preference == "performance_optimized":
            # Cost is less important
            return 0.5
        else:  # balanced
            # Moderate cost consideration
            max_cost = max(m.cost_per_1k_tokens for m in self.models.values())
            cost_ratio = model.cost_per_1k_tokens / max_cost
            return 1.0 - (cost_ratio * 0.5)

    async def _calculate_latency_score(self, model: ModelCapability, request: TaskRequest) -> float:
        """Calculate latency score based on requirement"""
        if request.latency_requirement == "low_latency":
            # Strongly prefer fast models
            max_latency = max(m.avg_response_time for m in self.models.values())
            return 1.0 - (model.avg_response_time / max_latency)
        elif request.latency_requirement == "batch":
            # Latency is not important
            return 0.5
        else:  # normal
            # Moderate latency consideration
            max_latency = max(m.avg_response_time for m in self.models.values())
            latency_ratio = model.avg_response_time / max_latency
            return 1.0 - (latency_ratio * 0.3)

    async def _get_performance_bonus(self, model: ModelCapability) -> float:
        """Get performance bonus based on historical data"""
        model_key = f"{model.provider.value}:{model.model_name}"
        if model_key not in self.performance_history:
            return 0.0

        history = self.performance_history[model_key]
        if len(history) < 5:  # Need minimum data points
            return 0.0

        # Calculate average success rate and response time
        recent_history = history[-20:]  # Last 20 requests
        success_rate = sum(1 for h in recent_history if h.get("success", False)) / len(recent_history)
        avg_response_time = np.mean([h.get("response_time", 0) for h in recent_history])

        # Bonus for high success rate and good response time
        bonus = (success_rate - 0.8) * 0.5  # Bonus for >80% success rate
        if avg_response_time < model.avg_response_time:
            bonus += 0.1  # Bonus for better than expected response time

        return max(0.0, bonus)

    async def _get_availability_penalty(self, model: ModelCapability) -> float:
        """Get availability penalty based on recent failures"""
        model_key = f"{model.provider.value}:{model.model_name}"
        if model_key not in self.failure_tracking:
            return 0.0

        recent_failures = self.failure_tracking[model_key]
        now = datetime.now()

        # Count failures in last hour
        recent_failure_count = sum(1 for failure_time in recent_failures if now - failure_time < timedelta(hours=1))

        # Penalty increases with recent failures
        return min(0.5, recent_failure_count * 0.1)

    def _estimate_cost(self, model: ModelCapability, request: TaskRequest) -> float:
        """Estimate cost for the request"""
        # Rough token estimation (prompt + response)
        prompt_tokens = len(request.prompt.split()) * 1.3  # Rough approximation
        response_tokens = request.max_tokens or 1000
        total_tokens = prompt_tokens + response_tokens

        return (total_tokens / 1000) * model.cost_per_1k_tokens

    def _estimate_latency(self, model: ModelCapability, request: TaskRequest) -> float:
        """Estimate response latency"""
        base_latency = model.avg_response_time

        # Adjust for token count
        response_tokens = request.max_tokens or 1000
        if response_tokens > 2000:
            base_latency *= 1.5
        elif response_tokens > 4000:
            base_latency *= 2.0

        return base_latency

    def _generate_reasoning(self, model: ModelCapability, request: TaskRequest, score: float) -> str:
        """Generate human-readable reasoning for the selection"""
        reasons = []

        if request.task_type in model.specialties:
            reasons.append(f"specialized for {request.task_type.value}")

        if request.cost_preference == "cost_optimized" and model.cost_per_1k_tokens < 0.01:
            reasons.append("cost-effective option")

        if request.latency_requirement == "low_latency" and model.avg_response_time < 2.0:
            reasons.append("fast response time")

        if model.quality_score > 0.9:
            reasons.append("high quality outputs")

        if model.context_window > 100000:
            reasons.append("large context window")

        reasoning = f"Selected due to: {', '.join(reasons)}. "
        reasoning += f"Confidence score: {score:.3f}"

        return reasoning

    async def record_performance(
        self, provider: ModelProvider, model_name: str, success: bool, response_time: float, cost: float
    ):
        """Record performance metrics for continuous improvement"""
        model_key = f"{provider.value}:{model_name}"

        if model_key not in self.performance_history:
            self.performance_history[model_key] = []

        self.performance_history[model_key].append(
            {"timestamp": datetime.now(), "success": success, "response_time": response_time, "cost": cost}
        )

        # Keep only recent history
        if len(self.performance_history[model_key]) > 100:
            self.performance_history[model_key] = self.performance_history[model_key][-100:]

    async def record_failure(self, provider: ModelProvider, model_name: str):
        """Record model failure for availability tracking"""
        model_key = f"{provider.value}:{model_name}"

        if model_key not in self.failure_tracking:
            self.failure_tracking[model_key] = []

        self.failure_tracking[model_key].append(datetime.now())

        # Keep only recent failures (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.failure_tracking[model_key] = [
            failure_time for failure_time in self.failure_tracking[model_key] if failure_time > cutoff
        ]

    async def get_model_stats(self) -> Dict[str, Any]:
        """Get comprehensive model performance statistics"""
        stats = {}

        for model_id, model in self.models.items():
            model_key = f"{model.provider.value}:{model.model_name}"

            # Performance stats
            history = self.performance_history.get(model_key, [])
            if history:
                recent_history = history[-20:]
                success_rate = sum(1 for h in recent_history if h.get("success", False)) / len(recent_history)
                avg_response_time = np.mean([h.get("response_time", 0) for h in recent_history])
                avg_cost = np.mean([h.get("cost", 0) for h in recent_history])
            else:
                success_rate = 0.0
                avg_response_time = 0.0
                avg_cost = 0.0

            # Failure stats
            recent_failures = len(self.failure_tracking.get(model_key, []))

            stats[model_id] = {
                "provider": model.provider.value,
                "model_name": model.model_name,
                "specialties": [s.value for s in model.specialties],
                "quality_score": model.quality_score,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "context_window": model.context_window,
                "performance": {
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "avg_cost": avg_cost,
                    "recent_failures": recent_failures,
                    "total_requests": len(history),
                },
            }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the AI Router"""
        return {
            "status": "healthy",
            "models_available": len(self.models),
            "performance_data_points": sum(len(h) for h in self.performance_history.values()),
            "active_providers": list(set(m.provider.value for m in self.models.values())),
        }


# Global AI Router instance
ai_router = AIRouter()
