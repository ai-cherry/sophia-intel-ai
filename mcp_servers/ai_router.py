"""
AI Router - Intelligent Model Selection and Routing
Implements sophisticated AI model routing based on task characteristics,
performance requirements, and cost optimization.
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import aiohttp
import numpy as np
from datetime import datetime, timedelta

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
        """Initialize the model registry with current capabilities"""
        return {
            # OpenAI Models
            "gpt-4o": ModelCapability(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o",
                max_tokens=4096,
                cost_per_1k_tokens=0.03,
                avg_response_time=2.5,
                quality_score=0.95,
                specialties=[TaskType.CODE_GENERATION, TaskType.REASONING, TaskType.ANALYSIS],
                context_window=128000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=10000
            ),
            "gpt-4o-mini": ModelCapability(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o-mini",
                max_tokens=4096,
                cost_per_1k_tokens=0.0015,
                avg_response_time=1.8,
                quality_score=0.88,
                specialties=[TaskType.GENERAL_CHAT, TaskType.DOCUMENTATION],
                context_window=128000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=30000
            ),
            "gpt-4.1-mini": ModelCapability(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4.1-mini",
                max_tokens=4096,
                cost_per_1k_tokens=0.0012,
                avg_response_time=1.5,
                quality_score=0.91,
                specialties=[TaskType.CODE_GENERATION, TaskType.GENERAL_CHAT, TaskType.FUNCTION_CALLING],
                context_window=200000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=40000
            ),
            
            # Anthropic Models
            "claude-3-5-sonnet": ModelCapability(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                cost_per_1k_tokens=0.015,
                avg_response_time=3.2,
                quality_score=0.97,
                specialties=[TaskType.CODE_REVIEW, TaskType.ANALYSIS, TaskType.CREATIVE_WRITING],
                context_window=200000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=5000
            ),
            "claude-4-sonnet": ModelCapability(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-4-sonnet",
                max_tokens=8192,
                cost_per_1k_tokens=0.018,
                avg_response_time=2.8,
                quality_score=0.98,
                specialties=[TaskType.CODE_GENERATION, TaskType.CODE_REVIEW, TaskType.REASONING, TaskType.ANALYSIS],
                context_window=300000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=4000
            ),
            "claude-4-opus-4.1": ModelCapability(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-4-opus-4.1",
                max_tokens=8192,
                cost_per_1k_tokens=0.045,
                avg_response_time=4.2,
                quality_score=0.99,
                specialties=[TaskType.REASONING, TaskType.CREATIVE_WRITING, TaskType.CODE_GENERATION, TaskType.MATH],
                context_window=500000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=2000
            ),
            "claude-3-haiku": ModelCapability(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                max_tokens=4096,
                cost_per_1k_tokens=0.0008,
                avg_response_time=1.2,
                quality_score=0.82,
                specialties=[TaskType.GENERAL_CHAT, TaskType.DOCUMENTATION],
                context_window=200000,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=15000
            ),
            
            # Google Models
            "gemini-1.5-pro": ModelCapability(
                provider=ModelProvider.GOOGLE,
                model_name="gemini-1.5-pro",
                max_tokens=8192,
                cost_per_1k_tokens=0.0125,
                avg_response_time=2.8,
                quality_score=0.92,
                specialties=[TaskType.REASONING, TaskType.MATH, TaskType.ANALYSIS],
                context_window=2000000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=8000
            ),
            "gemini-2.5-pro": ModelCapability(
                provider=ModelProvider.GOOGLE,
                model_name="gemini-2.5-pro",
                max_tokens=8192,
                cost_per_1k_tokens=0.014,
                avg_response_time=2.5,
                quality_score=0.95,
                specialties=[TaskType.REASONING, TaskType.MATH, TaskType.CODE_GENERATION, TaskType.ANALYSIS],
                context_window=2000000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=10000
            ),
            
            # Groq Models (Fast inference)
            "llama-3.3-70b": ModelCapability(
                provider=ModelProvider.GROQ,
                model_name="llama-3.3-70b-versatile",
                max_tokens=4096,
                cost_per_1k_tokens=0.0009,
                avg_response_time=0.4,
                quality_score=0.88,
                specialties=[TaskType.GENERAL_CHAT, TaskType.CODE_GENERATION],
                context_window=131072,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=35000
            ),
            "llama-3.1-70b": ModelCapability(
                provider=ModelProvider.GROQ,
                model_name="llama-3.1-70b-versatile",
                max_tokens=4096,
                cost_per_1k_tokens=0.0008,
                avg_response_time=0.5,
                quality_score=0.85,
                specialties=[TaskType.GENERAL_CHAT, TaskType.CODE_GENERATION],
                context_window=131072,
                supports_function_calling=True,
                supports_structured_output=False,
                rate_limit_rpm=30000
            ),
            "mixtral-8x7b": ModelCapability(
                provider=ModelProvider.GROQ,
                model_name="mixtral-8x7b-32768",
                max_tokens=4096,
                cost_per_1k_tokens=0.0005,
                avg_response_time=0.3,
                quality_score=0.82,
                specialties=[TaskType.GENERAL_CHAT, TaskType.DOCUMENTATION],
                context_window=32768,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=50000
            ),
            
            # DeepSeek Models (Code specialist)
            "deepseek-v3": ModelCapability(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-v3",
                max_tokens=8192,
                cost_per_1k_tokens=0.0010,
                avg_response_time=1.8,
                quality_score=0.94,
                specialties=[TaskType.CODE_GENERATION, TaskType.CODE_REVIEW, TaskType.REASONING, TaskType.MATH],
                context_window=64000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=25000
            ),
            "deepseek-coder": ModelCapability(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-coder",
                max_tokens=4096,
                cost_per_1k_tokens=0.0014,
                avg_response_time=2.1,
                quality_score=0.91,
                specialties=[TaskType.CODE_GENERATION, TaskType.CODE_REVIEW],
                context_window=16384,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=20000
            ),
            
            # Grok Models
            "grok-beta": ModelCapability(
                provider=ModelProvider.GROK,
                model_name="grok-beta",
                max_tokens=4096,
                cost_per_1k_tokens=0.02,
                avg_response_time=3.5,
                quality_score=0.89,
                specialties=[TaskType.CREATIVE_WRITING, TaskType.GENERAL_CHAT],
                context_window=131072,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=5000
            ),
            
            # Qwen Models (Alibaba - Code specialist)
            "qwen-coder-3": ModelCapability(
                provider=ModelProvider.QWEN,
                model_name="qwen-coder-3",
                max_tokens=8192,
                cost_per_1k_tokens=0.0008,
                avg_response_time=1.6,
                quality_score=0.90,
                specialties=[TaskType.CODE_GENERATION, TaskType.CODE_REVIEW, TaskType.DOCUMENTATION],
                context_window=32768,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=30000
            ),
            "qwen-2.5-coder-7b": ModelCapability(
                provider=ModelProvider.QWEN,
                model_name="qwen-2.5-coder-7b",
                max_tokens=4096,
                cost_per_1k_tokens=0.0005,
                avg_response_time=1.2,
                quality_score=0.86,
                specialties=[TaskType.CODE_GENERATION, TaskType.GENERAL_CHAT],
                context_window=131072,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=40000
            ),
            
            # Kimi Models (Moonshot AI - Long context specialist)
            "kimi-moonshot-2": ModelCapability(
                provider=ModelProvider.KIMI,
                model_name="moonshot-v1-128k",
                max_tokens=8192,
                cost_per_1k_tokens=0.0012,
                avg_response_time=2.2,
                quality_score=0.87,
                specialties=[TaskType.ANALYSIS, TaskType.DOCUMENTATION, TaskType.GENERAL_CHAT],
                context_window=128000,
                supports_function_calling=True,
                supports_structured_output=False,
                rate_limit_rpm=20000
            ),
            "kimi-moonshot-2-32k": ModelCapability(
                provider=ModelProvider.KIMI,
                model_name="moonshot-v1-32k",
                max_tokens=4096,
                cost_per_1k_tokens=0.0008,
                avg_response_time=1.8,
                quality_score=0.84,
                specialties=[TaskType.GENERAL_CHAT, TaskType.CREATIVE_WRITING],
                context_window=32768,
                supports_function_calling=False,
                supports_structured_output=False,
                rate_limit_rpm=25000
            ),
            
            # New OpenAI Models (GPT-5 Series)
            "gpt-5": ModelCapability(
                provider=ModelProvider.OPENAI,
                model_name="openai/gpt-5",
                max_tokens=8192,
                cost_per_1k_tokens=0.06,
                avg_response_time=3.8,
                quality_score=0.99,
                specialties=[TaskType.REASONING, TaskType.ANALYSIS, TaskType.CREATIVE_WRITING, TaskType.CODE_GENERATION],
                context_window=256000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=5000
            ),
            "gpt-5-mini": ModelCapability(
                provider=ModelProvider.OPENAI,
                model_name="openai/gpt-5-mini",
                max_tokens=4096,
                cost_per_1k_tokens=0.002,
                avg_response_time=2.0,
                quality_score=0.92,
                specialties=[TaskType.GENERAL_CHAT, TaskType.DOCUMENTATION, TaskType.CODE_GENERATION],
                context_window=200000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=25000
            ),
            
            # New Google Models (Gemini 2.5 Series)
            "gemini-2.5-flash": ModelCapability(
                provider=ModelProvider.GOOGLE,
                model_name="google/gemini-2.5-flash",
                max_tokens=4096,
                cost_per_1k_tokens=0.001,
                avg_response_time=0.8,
                quality_score=0.89,
                specialties=[TaskType.GENERAL_CHAT, TaskType.ANALYSIS, TaskType.DOCUMENTATION],
                context_window=1000000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=45000
            ),
            
            # ZhipuAI Models (Chinese multilingual specialist)
            "glm-4.5": ModelCapability(
                provider=ModelProvider.ZHIPUAI,
                model_name="z-ai/glm-4.5",
                max_tokens=8192,
                cost_per_1k_tokens=0.0018,
                avg_response_time=2.5,
                quality_score=0.90,
                specialties=[TaskType.CREATIVE_WRITING, TaskType.ANALYSIS, TaskType.GENERAL_CHAT],
                context_window=128000,
                supports_function_calling=True,
                supports_structured_output=True,
                rate_limit_rpm=20000
            )
        }
    
    async def route_request(self, request: TaskRequest) -> RoutingDecision:
        """
        Route a request to the optimal AI model based on task characteristics
        and performance requirements.
        """
        logger.info(f"Routing request for task type: {request.task_type}")
        
        # Score all available models
        model_scores = {}
        for model_id, model in self.models.items():
            score = await self._score_model(model, request)
            model_scores[model_id] = score
        
        # Sort by score (highest first)
        sorted_models = sorted(
            model_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Select primary model and fallbacks
        primary_model_id = sorted_models[0][0]
        primary_model = self.models[primary_model_id]
        
        fallback_options = [
            (self.models[model_id].provider, self.models[model_id].model_name)
            for model_id, _ in sorted_models[1:4]  # Top 3 fallbacks
        ]
        
        # Calculate estimates
        estimated_cost = self._estimate_cost(primary_model, request)
        estimated_latency = self._estimate_latency(primary_model, request)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary_model, request, model_scores[primary_model_id])
        
        decision = RoutingDecision(
            selected_provider=primary_model.provider,
            selected_model=primary_model.model_name,
            confidence_score=model_scores[primary_model_id],
            reasoning=reasoning,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
            fallback_options=fallback_options
        )
        
        logger.info(f"Selected {primary_model.provider.value}:{primary_model.model_name} "
                   f"with confidence {decision.confidence_score:.3f}")
        
        return decision
    
    async def execute_task(self, request: TaskRequest, decision: RoutingDecision) -> Dict[str, Any]:
        """
        Execute a task using the selected model from routing decision
        
        Args:
            request: The original task request
            decision: The routing decision with selected model
            
        Returns:
            Task execution result
        """
        try:
            start_time = time.time()
            
            # For now, return a structured response indicating the routing
            # In a full implementation, this would make the actual API call to the selected model
            result = {
                "status": "success",
                "provider": decision.selected_provider.value,
                "model": decision.selected_model,
                "confidence": decision.confidence_score,
                "estimated_cost": decision.estimated_cost,
                "estimated_latency": decision.estimated_latency,
                "reasoning": decision.reasoning,
                "response": f"Task '{request.task_type.value}' routed to {decision.selected_model}",
                "execution_time": time.time() - start_time
            }
            
            # Record successful execution
            await self.record_performance(
                decision.selected_provider,
                decision.selected_model,
                success=True,
                response_time=time.time() - start_time,
                cost=decision.estimated_cost
            )
            
            logger.info(f"Task executed successfully using {decision.selected_model}")
            return result
            
        except Exception as e:
            # Record failure
            await self.record_failure(decision.selected_provider, decision.selected_model)
            logger.error(f"Task execution failed: {e}")
            
            return {
                "status": "error",
                "provider": decision.selected_provider.value,
                "model": decision.selected_model,
                "error": str(e),
                "execution_time": time.time() - start_time if 'start_time' in locals() else 0.0
            }
    
    async def _score_model(self, model: ModelCapability, request: TaskRequest) -> float:
        """Score a model's suitability for a given request"""
        score = 0.0
        
        # Task type specialty bonus
        if request.task_type in model.specialties:
            score += 0.3
        
        # Quality requirement matching
        quality_weights = {
            "basic": 0.1,
            "good": 0.2,
            "high": 0.3,
            "premium": 0.4
        }
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
        recent_failure_count = sum(
            1 for failure_time in recent_failures
            if now - failure_time < timedelta(hours=1)
        )
        
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
    
    async def record_performance(self, provider: ModelProvider, model_name: str, 
                               success: bool, response_time: float, cost: float):
        """Record performance metrics for continuous improvement"""
        model_key = f"{provider.value}:{model_name}"
        
        if model_key not in self.performance_history:
            self.performance_history[model_key] = []
        
        self.performance_history[model_key].append({
            "timestamp": datetime.now(),
            "success": success,
            "response_time": response_time,
            "cost": cost
        })
        
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
            failure_time for failure_time in self.failure_tracking[model_key]
            if failure_time > cutoff
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
                    "total_requests": len(history)
                }
            }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the AI Router"""
        return {
            "status": "healthy",
            "models_available": len(self.models),
            "performance_data_points": sum(len(h) for h in self.performance_history.values()),
            "active_providers": list(set(m.provider.value for m in self.models.values()))
        }


# Global AI Router instance
ai_router = AIRouter()

