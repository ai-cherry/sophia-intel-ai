"""
SOPHIA Intel - Model Router
Stage C: Scale Safely - Model routing with cost-efficient defaults and auto-escalation
"""
import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    EFFICIENT = "efficient"    # Cost-optimized models
    STANDARD = "standard"      # Balanced performance/cost
    PREMIUM = "premium"        # High-performance models
    SPECIALIZED = "specialized" # Task-specific models

@dataclass
class ModelConfig:
    name: str
    provider: str
    tier: ModelTier
    cost_per_token: float
    max_tokens: int
    capabilities: List[str]
    latency_p95_ms: int
    quality_score: float
    context_window: int

@dataclass
class RoutingRequest:
    task_type: str
    content: str
    tenant_id: str
    session_id: str
    user_preference: Optional[str] = None
    max_cost: Optional[float] = None
    max_latency_ms: Optional[int] = None
    quality_threshold: Optional[float] = None

@dataclass
class RoutingResult:
    model: ModelConfig
    estimated_cost: float
    estimated_latency_ms: int
    confidence: float
    reasoning: str
    fallback_models: List[str]

class ModelRouter:
    """
    SOPHIA Intel Model Router
    - Default to cost-efficient models
    - Auto-escalate on low confidence
    - Stream tokens for perceived latency
    - Route based on task complexity
    """
    
    def __init__(self):
        self.models = self._initialize_models()
        self.routing_history: Dict[str, List[Dict]] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize available models with their configurations - Current 2025 OpenRouter Models"""
        return {
            # Efficient Tier - Cost optimized
            "openai/gpt-oss-20b": ModelConfig(
                name="openai/gpt-oss-20b",
                provider="openai",
                tier=ModelTier.EFFICIENT,
                cost_per_token=0.0,  # Free tier
                max_tokens=4096,
                capabilities=["chat", "analysis", "code"],
                latency_p95_ms=1000,
                quality_score=0.80,
                context_window=32000
            ),
            
            "ai21/jamba-mini-1.7": ModelConfig(
                name="ai21/jamba-mini-1.7",
                provider="ai21",
                tier=ModelTier.EFFICIENT,
                cost_per_token=0.0002,  # $0.20/M input
                max_tokens=8192,
                capabilities=["chat", "code", "analysis"],
                latency_p95_ms=900,
                quality_score=0.85,
                context_window=256000
            ),
            
            "baidu/ernie-4.5-21b-a3b": ModelConfig(
                name="baidu/ernie-4.5-21b-a3b",
                provider="baidu",
                tier=ModelTier.EFFICIENT,
                cost_per_token=0.00107,  # $1.07/M input
                max_tokens=4096,
                capabilities=["chat", "analysis", "code"],
                latency_p95_ms=1200,
                quality_score=0.87,
                context_window=120000
            ),
            
            # Standard Tier - Balanced
            "mistralai/mistral-medium-3.1": ModelConfig(
                name="mistralai/mistral-medium-3.1",
                provider="mistralai",
                tier=ModelTier.STANDARD,
                cost_per_token=0.0004,  # Estimated
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning"],
                latency_p95_ms=1400,
                quality_score=0.90,
                context_window=262000
            ),
            
            "ai21/jamba-large-1.7": ModelConfig(
                name="ai21/jamba-large-1.7",
                provider="ai21",
                tier=ModelTier.STANDARD,
                cost_per_token=0.002,  # $2/M input
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning"],
                latency_p95_ms=1600,
                quality_score=0.92,
                context_window=256000
            ),
            
            "z-ai/glm-4.5v": ModelConfig(
                name="z-ai/glm-4.5v",
                provider="z-ai",
                tier=ModelTier.STANDARD,
                cost_per_token=0.0005,  # $0.50/M input
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning", "vision"],
                latency_p95_ms=1500,
                quality_score=0.89,
                context_window=600000
            ),
            
            "baidu/ernie-4.5-vl-28b-a3b": ModelConfig(
                name="baidu/ernie-4.5-vl-28b-a3b",
                provider="baidu",
                tier=ModelTier.STANDARD,
                cost_per_token=0.00014,  # $0.14/M input
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning", "vision"],
                latency_p95_ms=1700,
                quality_score=0.91,
                context_window=300000
            ),
            
            # Premium Tier - High performance
            "openai/gpt-5-nano": ModelConfig(
                name="openai/gpt-5-nano",
                provider="openai",
                tier=ModelTier.PREMIUM,
                cost_per_token=0.0005,  # $0.05/M input estimated
                max_tokens=4096,
                capabilities=["chat", "analysis", "code", "reasoning"],
                latency_p95_ms=800,
                quality_score=0.93,
                context_window=400000
            ),
            
            "openai/gpt-5-mini": ModelConfig(
                name="openai/gpt-5-mini",
                provider="openai",
                tier=ModelTier.PREMIUM,
                cost_per_token=0.00025,  # $0.25/M input estimated
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning", "health"],
                latency_p95_ms=1000,
                quality_score=0.95,
                context_window=400000
            ),
            
            "openai/gpt-5-chat": ModelConfig(
                name="openai/gpt-5-chat",
                provider="openai",
                tier=ModelTier.PREMIUM,
                cost_per_token=0.00125,  # $1.25/M input
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning", "multimodal"],
                latency_p95_ms=1200,
                quality_score=0.97,
                context_window=400000
            ),
            
            "openai/gpt-5": ModelConfig(
                name="openai/gpt-5",
                provider="openai",
                tier=ModelTier.PREMIUM,
                cost_per_token=0.00125,  # $1.25/M input, $10/M output
                max_tokens=8192,
                capabilities=["chat", "analysis", "code", "reasoning", "multimodal", "health"],
                latency_p95_ms=1500,
                quality_score=0.98,
                context_window=400000
            ),
            
            # Specialized models
            "openai/gpt-oss-120b": ModelConfig(
                name="openai/gpt-oss-120b",
                provider="openai",
                tier=ModelTier.SPECIALIZED,
                cost_per_token=0.00073,  # $0.73/M input estimated
                max_tokens=16384,
                capabilities=["code", "analysis", "science", "health", "legal", "finance"],
                latency_p95_ms=2000,
                quality_score=0.94,
                context_window=131000
            )
        }
    
    async def route_request(self, request: RoutingRequest) -> RoutingResult:
        """Route request to optimal model based on requirements"""
        try:
            # Analyze request complexity
            complexity_score = self._analyze_complexity(request)
            
            # Get candidate models
            candidates = self._get_candidate_models(request, complexity_score)
            
            # Score and rank candidates
            scored_candidates = []
            for model in candidates:
                score = await self._score_model(model, request, complexity_score)
                scored_candidates.append((model, score))
            
            # Sort by score (higher is better)
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            if not scored_candidates:
                # Fallback to default efficient model
                fallback_model = self.models["openai/gpt-oss-20b"]
                return RoutingResult(
                    model=fallback_model,
                    estimated_cost=self._estimate_cost(fallback_model, request),
                    estimated_latency_ms=fallback_model.latency_p95_ms,
                    confidence=0.5,
                    reasoning="Fallback to default efficient model",
                    fallback_models=["ai21/jamba-mini-1.7"]
                )
            
            # Select best model
            best_model, best_score = scored_candidates[0]
            
            # Prepare fallback options
            fallback_models = [model.name for model, _ in scored_candidates[1:3]]
            
            # Check if we should auto-escalate
            if best_score < 0.7 and len(scored_candidates) > 1:
                # Auto-escalate to next tier if confidence is low
                next_tier_candidates = [
                    (model, score) for model, score in scored_candidates 
                    if model.tier.value != best_model.tier.value
                ]
                
                if next_tier_candidates:
                    escalated_model, escalated_score = next_tier_candidates[0]
                    if escalated_score > best_score + 0.1:  # Significant improvement
                        best_model = escalated_model
                        best_score = escalated_score
            
            result = RoutingResult(
                model=best_model,
                estimated_cost=self._estimate_cost(best_model, request),
                estimated_latency_ms=best_model.latency_p95_ms,
                confidence=best_score,
                reasoning=self._generate_reasoning(best_model, request, complexity_score),
                fallback_models=fallback_models
            )
            
            # Record routing decision
            await self._record_routing_decision(request, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Model routing failed: {e}")
            # Return safe fallback
            fallback_model = self.models["openai/gpt-oss-20b"]
            return RoutingResult(
                model=fallback_model,
                estimated_cost=0.0,  # Free model
                estimated_latency_ms=1000,
                confidence=0.3,
                reasoning=f"Error in routing, using fallback: {e}",
                fallback_models=[]
            )
    
    def _analyze_complexity(self, request: RoutingRequest) -> float:
        """Analyze request complexity (0.0 to 1.0)"""
        complexity = 0.0
        
        # Content length factor
        content_length = len(request.content)
        if content_length > 5000:
            complexity += 0.3
        elif content_length > 1000:
            complexity += 0.2
        elif content_length > 500:
            complexity += 0.1
        
        # Task type factor
        complex_tasks = ["reasoning", "analysis", "creative", "research"]
        if request.task_type in complex_tasks:
            complexity += 0.4
        elif request.task_type in ["code", "technical"]:
            complexity += 0.3
        elif request.task_type in ["chat", "simple"]:
            complexity += 0.1
        
        # Content complexity indicators
        complexity_indicators = [
            "analyze", "compare", "evaluate", "synthesize", "create",
            "complex", "detailed", "comprehensive", "multi-step"
        ]
        
        content_lower = request.content.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in content_lower)
        complexity += min(0.3, indicator_count * 0.1)
        
        return min(1.0, complexity)
    
    def _get_candidate_models(self, request: RoutingRequest, complexity_score: float) -> List[ModelConfig]:
        """Get candidate models based on request requirements"""
        candidates = []
        
        # Filter by capabilities
        for model in self.models.values():
            if request.task_type in model.capabilities or "chat" in model.capabilities:
                candidates.append(model)
        
        # Apply user preferences
        if request.user_preference:
            if request.user_preference == "cost":
                candidates = [m for m in candidates if m.tier in [ModelTier.EFFICIENT, ModelTier.STANDARD]]
            elif request.user_preference == "quality":
                candidates = [m for m in candidates if m.tier in [ModelTier.STANDARD, ModelTier.PREMIUM]]
            elif request.user_preference == "speed":
                candidates = [m for m in candidates if m.latency_p95_ms < 2000]
        
        # Apply constraints
        if request.max_cost:
            estimated_costs = [self._estimate_cost(m, request) for m in candidates]
            candidates = [m for m, cost in zip(candidates, estimated_costs) if cost <= request.max_cost]
        
        if request.max_latency_ms:
            candidates = [m for m in candidates if m.latency_p95_ms <= request.max_latency_ms]
        
        if request.quality_threshold:
            candidates = [m for m in candidates if m.quality_score >= request.quality_threshold]
        
        return candidates
    
    async def _score_model(self, model: ModelConfig, request: RoutingRequest, complexity_score: float) -> float:
        """Score model for given request (0.0 to 1.0)"""
        score = 0.0
        
        # Base quality score
        score += model.quality_score * 0.4
        
        # Complexity matching
        if complexity_score < 0.3:  # Simple tasks
            if model.tier == ModelTier.EFFICIENT:
                score += 0.3
            elif model.tier == ModelTier.STANDARD:
                score += 0.1
        elif complexity_score < 0.7:  # Medium tasks
            if model.tier == ModelTier.STANDARD:
                score += 0.3
            elif model.tier == ModelTier.EFFICIENT:
                score += 0.2
            elif model.tier == ModelTier.PREMIUM:
                score += 0.1
        else:  # Complex tasks
            if model.tier == ModelTier.PREMIUM:
                score += 0.3
            elif model.tier == ModelTier.STANDARD:
                score += 0.2
        
        # Cost efficiency (lower cost = higher score)
        estimated_cost = self._estimate_cost(model, request)
        if estimated_cost < 0.01:
            score += 0.2
        elif estimated_cost < 0.05:
            score += 0.1
        
        # Latency preference (lower latency = higher score)
        if model.latency_p95_ms < 1000:
            score += 0.1
        elif model.latency_p95_ms > 3000:
            score -= 0.1
        
        # Historical performance
        model_history = self.performance_metrics.get(model.name, {})
        success_rate = model_history.get('success_rate', 0.9)
        score += (success_rate - 0.5) * 0.2  # Bonus/penalty based on success rate
        
        return min(1.0, max(0.0, score))
    
    def _estimate_cost(self, model: ModelConfig, request: RoutingRequest) -> float:
        """Estimate cost for request with given model"""
        # Rough token estimation (words * 1.3)
        estimated_tokens = len(request.content.split()) * 1.3
        
        # Add response tokens estimate
        if request.task_type in ["code", "analysis"]:
            estimated_tokens += 1000  # Longer responses
        else:
            estimated_tokens += 300   # Shorter responses
        
        return estimated_tokens * model.cost_per_token
    
    def _generate_reasoning(self, model: ModelConfig, request: RoutingRequest, complexity_score: float) -> str:
        """Generate human-readable reasoning for model selection"""
        reasons = []
        
        reasons.append(f"Selected {model.name} ({model.tier.value} tier)")
        
        if complexity_score < 0.3:
            reasons.append("Simple task - cost-efficient model preferred")
        elif complexity_score < 0.7:
            reasons.append("Medium complexity - balanced model selected")
        else:
            reasons.append("Complex task - high-performance model chosen")
        
        estimated_cost = self._estimate_cost(model, request)
        reasons.append(f"Estimated cost: ${estimated_cost:.4f}")
        
        if model.latency_p95_ms < 1500:
            reasons.append("Fast response expected")
        
        return "; ".join(reasons)
    
    async def _record_routing_decision(self, request: RoutingRequest, result: RoutingResult):
        """Record routing decision for learning"""
        decision = {
            "timestamp": time.time(),
            "task_type": request.task_type,
            "content_length": len(request.content),
            "selected_model": result.model.name,
            "estimated_cost": result.estimated_cost,
            "confidence": result.confidence,
            "tenant_id": request.tenant_id
        }
        
        # Store in routing history (in production, this would go to a database)
        if request.tenant_id not in self.routing_history:
            self.routing_history[request.tenant_id] = []
        
        self.routing_history[request.tenant_id].append(decision)
        
        # Keep only last 100 decisions per tenant
        if len(self.routing_history[request.tenant_id]) > 100:
            self.routing_history[request.tenant_id] = self.routing_history[request.tenant_id][-100:]
    
    async def update_model_performance(self, model_name: str, success: bool, latency_ms: int, quality_rating: Optional[float] = None):
        """Update model performance metrics"""
        if model_name not in self.performance_metrics:
            self.performance_metrics[model_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "success_rate": 0.9,
                "avg_latency_ms": 0,
                "quality_ratings": []
            }
        
        metrics = self.performance_metrics[model_name]
        metrics["total_requests"] += 1
        
        if success:
            metrics["successful_requests"] += 1
        
        metrics["success_rate"] = metrics["successful_requests"] / metrics["total_requests"]
        
        # Update average latency (exponential moving average)
        if metrics["avg_latency_ms"] == 0:
            metrics["avg_latency_ms"] = latency_ms
        else:
            metrics["avg_latency_ms"] = 0.9 * metrics["avg_latency_ms"] + 0.1 * latency_ms
        
        if quality_rating is not None:
            metrics["quality_ratings"].append(quality_rating)
            # Keep only last 50 ratings
            if len(metrics["quality_ratings"]) > 50:
                metrics["quality_ratings"] = metrics["quality_ratings"][-50:]
    
    def get_routing_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get routing statistics for a tenant"""
        history = self.routing_history.get(tenant_id, [])
        
        if not history:
            return {"message": "No routing history available"}
        
        # Calculate statistics
        total_requests = len(history)
        total_cost = sum(d["estimated_cost"] for d in history)
        avg_confidence = sum(d["confidence"] for d in history) / total_requests
        
        model_usage = {}
        for decision in history:
            model = decision["selected_model"]
            model_usage[model] = model_usage.get(model, 0) + 1
        
        return {
            "total_requests": total_requests,
            "total_estimated_cost": round(total_cost, 4),
            "average_confidence": round(avg_confidence, 3),
            "model_usage": model_usage,
            "cost_per_request": round(total_cost / total_requests, 4) if total_requests > 0 else 0
        }

# Global model router instance
model_router = ModelRouter()

# Convenience functions
async def route_chat_request(content: str, tenant_id: str, session_id: str, user_preference: Optional[str] = None) -> RoutingResult:
    """Route a chat request"""
    request = RoutingRequest(
        task_type="chat",
        content=content,
        tenant_id=tenant_id,
        session_id=session_id,
        user_preference=user_preference
    )
    return await model_router.route_request(request)

async def route_code_request(content: str, tenant_id: str, session_id: str) -> RoutingResult:
    """Route a code generation request"""
    request = RoutingRequest(
        task_type="code",
        content=content,
        tenant_id=tenant_id,
        session_id=session_id,
        user_preference="quality"  # Code tasks prefer quality
    )
    return await model_router.route_request(request)

async def route_analysis_request(content: str, tenant_id: str, session_id: str) -> RoutingResult:
    """Route an analysis request"""
    request = RoutingRequest(
        task_type="analysis",
        content=content,
        tenant_id=tenant_id,
        session_id=session_id
    )
    return await model_router.route_request(request)

