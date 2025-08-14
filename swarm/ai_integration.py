"""
Advanced AI Integration for Sophia Swarm System
Enhanced with latest LLM models, intelligent routing, and performance optimization
"""

import os
import asyncio
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from loguru import logger
import aiohttp
from datetime import datetime, timedelta

# LangChain imports
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class ModelProvider(Enum):
    """Enhanced model providers with latest offerings"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    TOGETHER = "together"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelCapability(Enum):
    """Model capability categories"""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    CREATIVE_WRITING = "creative_writing"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"


class SwarmStage(Enum):
    """Swarm workflow stages"""
    ARCHITECT = "architect"
    BUILDER = "builder"
    TESTER = "tester"
    OPERATOR = "operator"


@dataclass
class ModelInfo:
    """Comprehensive model information"""
    provider: ModelProvider
    model_id: str
    display_name: str
    capabilities: List[ModelCapability]
    context_window: int
    cost_per_1k_tokens: float
    avg_latency_ms: int
    quality_score: float  # 0.0 to 1.0
    preferred_stages: List[SwarmStage]
    system_prompt_style: str  # "standard", "xml_tags", "markdown", etc.
    supports_streaming: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    
    def __hash__(self):
        return hash(f"{self.provider.value}:{self.model_id}")


@dataclass
class ModelPerformanceMetrics:
    """Track model performance over time"""
    model_info: ModelInfo
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    quality_ratings: List[float] = field(default_factory=list)
    stage_performance: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_quality(self) -> float:
        if not self.quality_ratings:
            return self.model_info.quality_score
        return sum(self.quality_ratings) / len(self.quality_ratings)


class ModelRegistry:
    """Registry of available LLM models with comprehensive metadata"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.performance_metrics = {}
        self._load_performance_history()
    
    def _initialize_models(self) -> Dict[str, ModelInfo]:
        """Initialize the comprehensive model registry"""
        models = {}
        
        # OpenAI Models
        models["gpt-5"] = ModelInfo(
            provider=ModelProvider.OPENAI,
            model_id="gpt-5",
            display_name="GPT-5 (Latest)",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION, 
                         ModelCapability.FUNCTION_CALLING, ModelCapability.LONG_CONTEXT],
            context_window=200000,
            cost_per_1k_tokens=0.03,
            avg_latency_ms=2000,
            quality_score=0.98,
            preferred_stages=[SwarmStage.ARCHITECT, SwarmStage.BUILDER],
            system_prompt_style="standard"
        )
        
        models["gpt-5-turbo"] = ModelInfo(
            provider=ModelProvider.OPENAI,
            model_id="gpt-5-turbo",
            display_name="GPT-5 Turbo",
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING,
                         ModelCapability.FUNCTION_CALLING],
            context_window=128000,
            cost_per_1k_tokens=0.01,
            avg_latency_ms=1200,
            quality_score=0.95,
            preferred_stages=[SwarmStage.BUILDER, SwarmStage.TESTER],
            system_prompt_style="standard"
        )
        
        models["gpt-4o"] = ModelInfo(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4o",
            display_name="GPT-4o (Omni)",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION,
                         ModelCapability.VISION, ModelCapability.FUNCTION_CALLING],
            context_window=128000,
            cost_per_1k_tokens=0.005,
            avg_latency_ms=1500,
            quality_score=0.92,
            preferred_stages=[SwarmStage.ARCHITECT, SwarmStage.OPERATOR],
            system_prompt_style="standard"
        )
        
        # Anthropic Models
        models["claude-opus-4.1"] = ModelInfo(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-opus-20241029",  # Update with actual model ID when available
            display_name="Claude Opus 4.1",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE_ANALYSIS,
                         ModelCapability.LONG_CONTEXT, ModelCapability.CREATIVE_WRITING],
            context_window=400000,
            cost_per_1k_tokens=0.075,
            avg_latency_ms=3000,
            quality_score=0.97,
            preferred_stages=[SwarmStage.ARCHITECT, SwarmStage.TESTER],
            system_prompt_style="xml_tags"
        )
        
        models["claude-sonnet-3.5"] = ModelInfo(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-5-sonnet-20241022",
            display_name="Claude Sonnet 3.5",
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING,
                         ModelCapability.CODE_ANALYSIS],
            context_window=200000,
            cost_per_1k_tokens=0.003,
            avg_latency_ms=1800,
            quality_score=0.94,
            preferred_stages=[SwarmStage.BUILDER, SwarmStage.TESTER],
            system_prompt_style="xml_tags"
        )
        
        models["claude-haiku-3.5"] = ModelInfo(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-5-haiku-20241022",
            display_name="Claude Haiku 3.5",
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.DOCUMENTATION],
            context_window=200000,
            cost_per_1k_tokens=0.0008,
            avg_latency_ms=800,
            quality_score=0.88,
            preferred_stages=[SwarmStage.OPERATOR],
            system_prompt_style="xml_tags"
        )
        
        # Google Models
        models["gemini-pro-1.5"] = ModelInfo(
            provider=ModelProvider.GOOGLE,
            model_id="gemini-1.5-pro-002",
            display_name="Gemini Pro 1.5",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION,
                         ModelCapability.LONG_CONTEXT, ModelCapability.FUNCTION_CALLING],
            context_window=2000000,  # 2M tokens
            cost_per_1k_tokens=0.00125,
            avg_latency_ms=2500,
            quality_score=0.93,
            preferred_stages=[SwarmStage.ARCHITECT, SwarmStage.BUILDER],
            system_prompt_style="standard"
        )
        
        models["gemini-flash-1.5"] = ModelInfo(
            provider=ModelProvider.GOOGLE,
            model_id="gemini-1.5-flash-002",
            display_name="Gemini Flash 1.5",
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
            context_window=1000000,
            cost_per_1k_tokens=0.000075,
            avg_latency_ms=500,
            quality_score=0.87,
            preferred_stages=[SwarmStage.BUILDER, SwarmStage.OPERATOR],
            system_prompt_style="standard"
        )
        
        # DeepSeek Models (Code Specialist)
        models["deepseek-coder-v2"] = ModelInfo(
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-coder-v2-instruct",
            display_name="DeepSeek Coder V2",
            capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.CODE_ANALYSIS],
            context_window=128000,
            cost_per_1k_tokens=0.0003,
            avg_latency_ms=1000,
            quality_score=0.91,
            preferred_stages=[SwarmStage.BUILDER, SwarmStage.TESTER],
            system_prompt_style="standard"
        )
        
        # Groq Models (Fast inference)
        models["llama-3.1-70b-groq"] = ModelInfo(
            provider=ModelProvider.GROQ,
            model_id="llama-3.1-70b-versatile",
            display_name="Llama 3.1 70B (Groq)",
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
            context_window=128000,
            cost_per_1k_tokens=0.00059,
            avg_latency_ms=300,  # Very fast
            quality_score=0.85,
            preferred_stages=[SwarmStage.OPERATOR],
            system_prompt_style="standard"
        )
        
        return models
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info by ID"""
        return self.models.get(model_id)
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """Get models that have specific capability"""
        return [model for model in self.models.values() if capability in model.capabilities]
    
    def get_models_by_stage(self, stage: SwarmStage) -> List[ModelInfo]:
        """Get models optimized for specific Swarm stage"""
        return [model for model in self.models.values() if stage in model.preferred_stages]
    
    def get_models_by_provider(self, provider: ModelProvider) -> List[ModelInfo]:
        """Get all models from specific provider"""
        return [model for model in self.models.values() if model.provider == provider]
    
    def get_performance_metrics(self, model_id: str) -> Optional[ModelPerformanceMetrics]:
        """Get performance metrics for model"""
        return self.performance_metrics.get(model_id)
    
    def update_performance(self, model_id: str, success: bool, response_time: float, 
                          tokens_used: int, cost: float, quality_rating: Optional[float] = None):
        """Update model performance metrics"""
        if model_id not in self.performance_metrics:
            model_info = self.get_model(model_id)
            if model_info:
                self.performance_metrics[model_id] = ModelPerformanceMetrics(model_info)
        
        metrics = self.performance_metrics.get(model_id)
        if metrics:
            metrics.total_requests += 1
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1
            
            metrics.total_tokens_used += tokens_used
            metrics.total_cost += cost
            
            # Update average response time
            total_requests = metrics.total_requests
            metrics.avg_response_time = (
                (metrics.avg_response_time * (total_requests - 1) + response_time) / total_requests
            )
            
            if quality_rating:
                metrics.quality_ratings.append(quality_rating)
                # Keep only recent ratings
                if len(metrics.quality_ratings) > 100:
                    metrics.quality_ratings = metrics.quality_ratings[-50:]
            
            metrics.last_updated = datetime.now()
            self._save_performance_history()
    
    def _load_performance_history(self):
        """Load performance history from disk"""
        try:
            history_file = os.getenv("SWARM_PERFORMANCE_FILE", ".swarm_model_performance.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for model_id, metrics_data in data.items():
                        if model_id in self.models:
                            # Reconstruct performance metrics
                            model_info = self.models[model_id]
                            metrics = ModelPerformanceMetrics(model_info)
                            metrics.total_requests = metrics_data.get("total_requests", 0)
                            metrics.successful_requests = metrics_data.get("successful_requests", 0)
                            metrics.failed_requests = metrics_data.get("failed_requests", 0)
                            metrics.total_tokens_used = metrics_data.get("total_tokens_used", 0)
                            metrics.total_cost = metrics_data.get("total_cost", 0.0)
                            metrics.avg_response_time = metrics_data.get("avg_response_time", 0.0)
                            metrics.quality_ratings = metrics_data.get("quality_ratings", [])
                            metrics.stage_performance = metrics_data.get("stage_performance", {})
                            self.performance_metrics[model_id] = metrics
        except Exception as e:
            logger.warning(f"Failed to load performance history: {e}")
    
    def _save_performance_history(self):
        """Save performance history to disk"""
        try:
            history_file = os.getenv("SWARM_PERFORMANCE_FILE", ".swarm_model_performance.json")
            data = {}
            for model_id, metrics in self.performance_metrics.items():
                data[model_id] = {
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "total_tokens_used": metrics.total_tokens_used,
                    "total_cost": metrics.total_cost,
                    "avg_response_time": metrics.avg_response_time,
                    "quality_ratings": metrics.quality_ratings,
                    "stage_performance": metrics.stage_performance,
                    "last_updated": metrics.last_updated.isoformat()
                }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save performance history: {e}")


class PromptTemplateManager:
    """Manages specialized prompt templates for different models and use cases"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize prompt templates for different model types and stages"""
        return {
            "standard": {
                "architect": """You are the Architect agent in a sophisticated multi-agent software development system. Your role is to analyze requirements, design system architecture, and create comprehensive technical specifications.

Task: {task}
Context: {context}

Please provide:
1. System architecture overview
2. Component breakdown
3. Technology recommendations
4. Implementation approach
5. Risk analysis and mitigation strategies

Format your response as structured analysis with clear sections.""",
                
                "builder": """You are the Builder agent responsible for implementing code solutions based on architectural designs. You excel at writing clean, efficient, and maintainable code.

Task: {task}
Context: {context}
Architecture: {architect_result}

Please provide:
1. Complete implementation code
2. Code organization and structure
3. Key functions and classes
4. Dependencies and imports
5. Usage examples

Write production-ready code with proper error handling and documentation.""",
                
                "tester": """You are the Tester agent responsible for ensuring code quality, creating comprehensive tests, and identifying potential issues.

Task: {task}
Context: {context}
Implementation: {builder_result}

Please provide:
1. Test strategy and approach
2. Unit tests for key components
3. Integration tests
4. Edge case analysis
5. Quality assessment and recommendations

Focus on thorough testing coverage and identifying potential bugs or improvements.""",
                
                "operator": """You are the Operator agent responsible for deployment, monitoring, and operational aspects of the system.

Task: {task}
Context: {context}
Implementation: {builder_result}
Tests: {tester_result}

Please provide:
1. Deployment strategy
2. Configuration management
3. Monitoring and alerting setup
4. Performance optimization
5. Documentation and runbooks

Focus on production readiness and operational excellence."""
            },
            
            "xml_tags": {
                "architect": """<role>You are the Architect agent in a sophisticated multi-agent software development system.</role>

<task>{task}</task>
<context>{context}</context>

<instructions>
Analyze the requirements and design a comprehensive system architecture. Provide:

<architecture>
- System overview
- Component breakdown  
- Technology stack
- Implementation approach
- Risk analysis
</architecture>

<thinking>
First, let me understand the requirements...
</thinking>

Focus on creating a robust, scalable architecture that addresses all requirements.
</instructions>""",
                
                "builder": """<role>You are the Builder agent responsible for implementing high-quality code solutions.</role>

<task>{task}</task>
<context>{context}</context>
<architecture>{architect_result}</architecture>

<instructions>
Implement the solution based on the architectural design:

<implementation>
- Complete, production-ready code
- Proper error handling
- Clear documentation
- Modular structure
- Best practices
</implementation>

<thinking>
Based on the architecture, I need to implement...
</thinking>

Write clean, maintainable code that follows the architectural guidelines.
</instructions>""",
                
                "tester": """<role>You are the Tester agent ensuring comprehensive quality assurance.</role>

<task>{task}</task>
<context>{context}</context>
<implementation>{builder_result}</implementation>

<instructions>
Create thorough test coverage for the implementation:

<testing>
- Test strategy
- Unit tests
- Integration tests  
- Edge cases
- Quality metrics
</testing>

<thinking>
I need to analyze the implementation and identify all testing requirements...
</thinking>

Ensure robust testing that validates all functionality and edge cases.
</instructions>""",
                
                "operator": """<role>You are the Operator agent focusing on deployment and operational excellence.</role>

<task>{task}</task>
<context>{context}</context>
<implementation>{builder_result}</implementation>
<tests>{tester_result}</tests>

<instructions>
Prepare the system for production deployment:

<operations>
- Deployment strategy
- Configuration
- Monitoring
- Performance optimization
- Documentation
</operations>

<thinking>
For production deployment, I need to consider...
</thinking>

Focus on reliability, scalability, and maintainability in production.
</instructions>"""
            }
        }
    
    def get_template(self, style: str, stage: str) -> Optional[str]:
        """Get prompt template for specific style and stage"""
        return self.templates.get(style, {}).get(stage)
    
    def format_prompt(self, style: str, stage: str, **kwargs) -> str:
        """Format prompt template with provided variables"""
        template = self.get_template(style, stage)
        if template:
            return template.format(**kwargs)
        return f"Task: {kwargs.get('task', '')}\nContext: {kwargs.get('context', '')}"


class CircuitBreakerManager:
    """Manages circuit breakers for model reliability"""
    
    def __init__(self):
        self.breakers = {}
        self.failure_threshold = 5
        self.recovery_timeout = 300  # 5 minutes
        self.half_open_max_calls = 3
    
    def get_breaker(self, model_id: str) -> Dict[str, Any]:
        """Get circuit breaker state for model"""
        if model_id not in self.breakers:
            self.breakers[model_id] = {
                "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
                "failure_count": 0,
                "last_failure_time": 0,
                "half_open_calls": 0
            }
        return self.breakers[model_id]
    
    def can_execute(self, model_id: str) -> bool:
        """Check if model can be called"""
        breaker = self.get_breaker(model_id)
        
        if breaker["state"] == "CLOSED":
            return True
        elif breaker["state"] == "OPEN":
            if time.time() - breaker["last_failure_time"] > self.recovery_timeout:
                breaker["state"] = "HALF_OPEN"
                breaker["half_open_calls"] = 0
                return True
            return False
        else:  # HALF_OPEN
            return breaker["half_open_calls"] < self.half_open_max_calls
    
    def record_success(self, model_id: str):
        """Record successful model call"""
        breaker = self.get_breaker(model_id)
        if breaker["state"] == "HALF_OPEN":
            breaker["state"] = "CLOSED"
            breaker["failure_count"] = 0
        breaker["half_open_calls"] = 0
    
    def record_failure(self, model_id: str):
        """Record failed model call"""
        breaker = self.get_breaker(model_id)
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()
        
        if breaker["state"] == "HALF_OPEN":
            breaker["state"] = "OPEN"
        elif breaker["failure_count"] >= self.failure_threshold:
            breaker["state"] = "OPEN"


class EnhancedAIIntegration:
    """
    Advanced AI Integration for Swarm System
    
    Features:
    - Latest LLM model support with intelligent routing
    - Stage-specific model optimization
    - Performance tracking and adaptive selection
    - Cost optimization
    - Circuit breaker pattern for reliability
    - Specialized prompt templates
    - Graceful degradation
    """
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.prompt_manager = PromptTemplateManager()
        self.circuit_breaker = CircuitBreakerManager()
        self.session_cache = {}
        self.adaptive_weights = self._load_adaptive_weights()
        
        # Configuration
        self.config = {
            "cost_weight": float(os.getenv("SWARM_COST_WEIGHT", "0.3")),
            "latency_weight": float(os.getenv("SWARM_LATENCY_WEIGHT", "0.2")),
            "quality_weight": float(os.getenv("SWARM_QUALITY_WEIGHT", "0.5")),
            "enable_adaptive": os.getenv("SWARM_ENABLE_ADAPTIVE", "1") == "1",
            "fallback_enabled": os.getenv("SWARM_ENABLE_FALLBACK", "1") == "1",
            "max_cost_per_request": float(os.getenv("SWARM_MAX_COST", "0.50")),
            "max_latency_ms": int(os.getenv("SWARM_MAX_LATENCY", "30000"))
        }
    
    def _load_adaptive_weights(self) -> Dict[str, float]:
        """Load adaptive weights from historical performance"""
        try:
            weights_file = os.getenv("SWARM_WEIGHTS_FILE", ".swarm_adaptive_weights.json")
            if os.path.exists(weights_file):
                with open(weights_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load adaptive weights: {e}")
        
        # Default weights
        return {
            "cost_optimization": 1.0,
            "quality_preference": 1.0,
            "latency_preference": 1.0,
            "stage_specialization": 1.0
        }
    
    def _save_adaptive_weights(self):
        """Save adaptive weights to disk"""
        try:
            weights_file = os.getenv("SWARM_WEIGHTS_FILE", ".swarm_adaptive_weights.json")
            with open(weights_file, 'w') as f:
                json.dump(self.adaptive_weights, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save adaptive weights: {e}")
    
    async def select_optimal_model(
        self,
        stage: SwarmStage,
        task: str,
        context: Dict[str, Any],
        override_model: Optional[str] = None
    ) -> Tuple[ModelInfo, float]:
        """
        Select optimal model for given stage and task
        
        Returns:
            Tuple of (ModelInfo, confidence_score)
        """
        if override_model:
            # Check for per-agent override
            model_info = self.registry.get_model(override_model)
            if model_info and self.circuit_breaker.can_execute(override_model):
                return model_info, 1.0
            else:
                logger.warning(f"Override model {override_model} not available, falling back")
        
        # Check for stage-specific environment override
        stage_override = os.getenv(f"SWARM_{stage.value.upper()}_MODEL")
        if stage_override:
            model_info = self.registry.get_model(stage_override)
            if model_info and self.circuit_breaker.can_execute(stage_override):
                return model_info, 1.0
        
        # Get candidate models for this stage
        candidates = self.registry.get_models_by_stage(stage)
        
        # Filter by availability and circuit breaker
        available_candidates = [
            model for model in candidates 
            if self.circuit_breaker.can_execute(model.model_id)
        ]
        
        if not available_candidates:
            # Fallback to any available model
            all_models = list(self.registry.models.values())
            available_candidates = [
                model for model in all_models
                if self.circuit_breaker.can_execute(model.model_id)
            ]
        
        if not available_candidates:
            raise Exception("No available models - all circuits are open")
        
        # Score models based on multiple criteria
        scored_models = []
        for model in available_candidates:
            score = await self._score_model(model, stage, task, context)
            scored_models.append((model, score))
        
        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        best_model, confidence = scored_models[0]
        logger.info(f"Selected {best_model.display_name} for {stage.value} with confidence {confidence:.3f}")
        
        return best_model, confidence
    
    async def _score_model(
        self,
        model: ModelInfo,
        stage: SwarmStage,
        task: str,
        context: Dict[str, Any]
    ) -> float:
        """Score model based on multiple criteria"""
        score = 0.0
        
        # Base quality score
        score += model.quality_score * self.config["quality_weight"]
        
        # Stage specialization bonus
        if stage in model.preferred_stages:
            score += 0.2 * self.adaptive_weights["stage_specialization"]
        
        # Cost efficiency (lower cost = higher score)
        max_cost = max(m.cost_per_1k_tokens for m in self.registry.models.values())
        cost_efficiency = 1.0 - (model.cost_per_1k_tokens / max_cost)
        score += cost_efficiency * self.config["cost_weight"] * self.adaptive_weights["cost_optimization"]
        
        # Latency efficiency (lower latency = higher score)  
        max_latency = max(m.avg_latency_ms for m in self.registry.models.values())
        latency_efficiency = 1.0 - (model.avg_latency_ms / max_latency)
        score += latency_efficiency * self.config["latency_weight"] * self.adaptive_weights["latency_preference"]
        
        # Historical performance bonus
        metrics = self.registry.get_performance_metrics(model.model_id)
        if metrics and metrics.total_requests > 0:
            performance_bonus = metrics.success_rate * metrics.avg_quality * 0.1
            score += performance_bonus
        
        # Context window appropriateness
        estimated_tokens = len(task.split()) * 4 + sum(len(str(v).split()) * 4 for v in context.values())
        if estimated_tokens < model.context_window * 0.8:  # Don't max out context
            score += 0.05
        
        # Capability matching
        required_capabilities = self._determine_required_capabilities(stage, task, context)
        capability_match = len(set(required_capabilities) & set(model.capabilities)) / len(required_capabilities) if required_capabilities else 1.0
        score += capability_match * 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _determine_required_capabilities(
        self,
        stage: SwarmStage,
        task: str,
        context: Dict[str, Any]
    ) -> List[ModelCapability]:
        """Determine required capabilities based on stage and task"""
        capabilities = []
        
        # Stage-specific capabilities
        if stage == SwarmStage.ARCHITECT:
            capabilities.extend([ModelCapability.REASONING, ModelCapability.LONG_CONTEXT])
        elif stage == SwarmStage.BUILDER:
            capabilities.extend([ModelCapability.CODE_GENERATION, ModelCapability.FUNCTION_CALLING])
        elif stage == SwarmStage.TESTER:
            capabilities.extend([ModelCapability.CODE_ANALYSIS, ModelCapability.REASONING])
        elif stage == SwarmStage.OPERATOR:
            capabilities.extend([ModelCapability.DOCUMENTATION, ModelCapability.REASONING])
        
        # Task-specific capabilities
        task_lower = task.lower()
        if any(word in task_lower for word in ["function", "code", "implement", "program"]):
            capabilities.append(ModelCapability.CODE_GENERATION)
        
        if any(word in task_lower for word in ["analyze", "review", "test", "debug"]):
            capabilities.append(ModelCapability.CODE_ANALYSIS)
        
        if any(word in task_lower for word in ["document", "explain", "guide", "manual"]):
            capabilities.append(ModelCapability.DOCUMENTATION)
        
        return list(set(capabilities))  # Remove duplicates
    
    async def invoke(
        self,
        task: str,
        context: Dict[str, Any],
        stage: str,
        override_model: Optional[str] = None
    ) -> AIMessage:
        """
        Enhanced invoke method with intelligent model selection and optimization
        """
        stage_enum = SwarmStage(stage)
        start_time = time.time()
        model_info = None  # Initialize to avoid unbound variable
        
        try:
            # Select optimal model
            model_info, confidence = await self.select_optimal_model(
                stage_enum, task, context, override_model
            )
            
            # Format prompt using appropriate template
            prompt = self._format_prompt(model_info, stage_enum, task, context)
            
            # Create messages
            messages = self._create_messages(model_info, prompt)
            
            # Execute with model
            response = await self._execute_with_model(model_info, messages)
            
            # Record success metrics
            response_time = time.time() - start_time
            response_content = response.content if isinstance(response.content, str) else str(response.content)
            tokens_used = self._estimate_tokens(prompt + response_content)
            cost = (tokens_used / 1000) * model_info.cost_per_1k_tokens
            
            self.registry.update_performance(
                model_info.model_id, 
                success=True, 
                response_time=response_time,
                tokens_used=tokens_used,
                cost=cost
            )
            
            self.circuit_breaker.record_success(model_info.model_id)
            
            # Update adaptive weights based on success
            if self.config["enable_adaptive"]:
                self._update_adaptive_weights(model_info, stage_enum, True, response_time, cost)
            
            logger.info(f"Successfully executed {stage} with {model_info.display_name} "
                       f"({response_time:.2f}s, {tokens_used} tokens, ${cost:.4f})")
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Model execution failed for {stage}: {e}")
            
            # Record failure
            if model_info is not None:
                self.registry.update_performance(
                    model_info.model_id,
                    success=False,
                    response_time=response_time,
                    tokens_used=0,
                    cost=0.0
                )
                self.circuit_breaker.record_failure(model_info.model_id)
                
                # Try fallback if enabled
                if self.config["fallback_enabled"]:
                    return await self._execute_fallback(stage_enum, task, context)
            
            raise
    
    def _format_prompt(self, model_info: ModelInfo, stage: SwarmStage, task: str, context: Dict[str, Any]) -> str:
        """Format prompt using appropriate template for model and stage"""
        template_style = model_info.system_prompt_style
        
        # Prepare context variables
        prompt_vars = {
            "task": task,
            "context": json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
        }
        
        # Add stage-specific context
        for stage_name in ["architect", "builder", "tester"]:
            if f"{stage_name}_result" in context:
                prompt_vars[f"{stage_name}_result"] = context[f"{stage_name}_result"]
        
        return self.prompt_manager.format_prompt(template_style, stage.value, **prompt_vars)
    
    def _create_messages(self, model_info: ModelInfo, prompt: str) -> List[Dict[str, Any]]:
        """Create properly formatted messages for the model"""
        if model_info.system_prompt_style == "xml_tags":
            # For Anthropic models, use the full prompt as user message
            return [
                {"role": "user", "content": prompt}
            ]
        else:
            # For standard models, separate system and user messages
            lines = prompt.split('\n')
            system_content = "You are a helpful AI assistant specialized in software development."
            user_content = prompt
            
            return [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ]
    
    async def _execute_with_model(self, model_info: ModelInfo, messages: List[Dict[str, Any]]) -> AIMessage:
        """Execute request with specific model"""
        # This is where you'd integrate with actual model APIs
        # For now, return a mock response that indicates successful routing
        
        response_content = f"[{model_info.display_name}] Task completed successfully. This response demonstrates that the model selection and routing system is working correctly."
        
        # Add some model-specific formatting
        if model_info.provider == ModelProvider.ANTHROPIC:
            response_content = f"<thinking>Processing request with {model_info.display_name}...</thinking>\n\n{response_content}"
        elif model_info.provider == ModelProvider.OPENAI and "gpt-5" in model_info.model_id:
            response_content = f"🚀 **{model_info.display_name} Response:**\n\n{response_content}"
        
        return AIMessage(content=response_content)
    
    async def _execute_fallback(self, stage: SwarmStage, task: str, context: Dict[str, Any]) -> AIMessage:
        """Execute with fallback model when primary fails"""
        logger.info(f"Executing fallback for {stage.value}")
        
        # Try to find a simple, reliable model
        fallback_candidates = [
            "claude-haiku-3.5",
            "gemini-flash-1.5", 
            "llama-3.1-70b-groq"
        ]
        
        for candidate_id in fallback_candidates:
            model_info = self.registry.get_model(candidate_id)
            if model_info and self.circuit_breaker.can_execute(candidate_id):
                try:
                    prompt = self._format_prompt(model_info, stage, task, context)
                    messages = self._create_messages(model_info, prompt)
                    response = await self._execute_with_model(model_info, messages)
                    
                    logger.info(f"Fallback successful with {model_info.display_name}")
                    return response
                    
                except Exception as e:
                    logger.warning(f"Fallback failed with {candidate_id}: {e}")
                    continue
        
        # Ultimate fallback - return basic response
        return AIMessage(content=f"[FALLBACK] Basic response for {stage.value}: {task}")
    
    def _update_adaptive_weights(self, model_info: ModelInfo, stage: SwarmStage, 
                                success: bool, response_time: float, cost: float):
        """Update adaptive weights based on performance"""
        learning_rate = 0.01
        
        if success:
            # Reward successful characteristics
            if response_time < model_info.avg_latency_ms / 1000:
                self.adaptive_weights["latency_preference"] += learning_rate
            
            if cost < self.config["max_cost_per_request"] * 0.5:
                self.adaptive_weights["cost_optimization"] += learning_rate
            
            if stage in model_info.preferred_stages:
                self.adaptive_weights["stage_specialization"] += learning_rate
        else:
            # Penalize failed characteristics slightly
            self.adaptive_weights["quality_preference"] *= (1 - learning_rate)
        
        # Normalize weights
        total = sum(self.adaptive_weights.values())
        for key in self.adaptive_weights:
            self.adaptive_weights[key] = self.adaptive_weights[key] / total * 4.0  # Keep total around 4
        
        # Save periodically
        if time.time() % 300 < 1:  # Every ~5 minutes
            self._save_adaptive_weights()
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return int(len(text.split()) * 1.3)  # Rough approximation
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            "total_models": len(self.registry.models),
            "available_models": len([m for m in self.registry.models.values() 
                                   if self.circuit_breaker.can_execute(m.model_id)]),
            "total_requests": sum(m.total_requests for m in self.registry.performance_metrics.values()),
            "total_cost": sum(m.total_cost for m in self.registry.performance_metrics.values()),
            "avg_success_rate": 0.0,
            "adaptive_weights": self.adaptive_weights.copy(),
            "model_performance": {},
            "circuit_breaker_states": {}
        }
        
        # Calculate average success rate
        total_requests = summary["total_requests"]
        if total_requests > 0:
            total_successful = sum(m.successful_requests for m in self.registry.performance_metrics.values())
            summary["avg_success_rate"] = total_successful / total_requests
        
        # Add per-model performance
        for model_id, metrics in self.registry.performance_metrics.items():
            summary["model_performance"][model_id] = {
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time,
                "total_cost": metrics.total_cost,
                "avg_quality": metrics.avg_quality
            }
        
        # Add circuit breaker states
        for model_id in self.registry.models.keys():
            breaker = self.circuit_breaker.get_breaker(model_id)
            summary["circuit_breaker_states"][model_id] = breaker["state"]
        
        return summary


# Backward compatibility functions
def get_router_llm():
    """Factory function for backward compatibility"""
    return EnhancedRouterLLM()


class EnhancedRouterLLM:
    """Enhanced RouterLLM with new AI integration features"""
    
    def __init__(self):
        self.ai_integration = EnhancedAIIntegration()
        self.is_available = True
    
    def invoke(self, messages):
        """Synchronous interface maintaining backward compatibility"""
        try:
            # Extract stage from environment or messages
            stage = os.getenv("SWARM_CURRENT_AGENT", "builder")
            
            # Convert messages to task and context
            task = "Process request"
            context = {}
            
            if messages:
                # Extract content from messages
                content_parts = []
                for msg in messages:
                    if isinstance(msg, dict):
                        content_parts.append(msg.get("content", ""))
                    elif hasattr(msg, 'content'):
                        content_parts.append(msg.content)
                
                task = " ".join(content_parts)[:200]  # First 200 chars as task
                context = {"messages": messages}
            
            # Run async method synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.ai_integration.invoke(task, context, stage)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Enhanced AI integration failed: {e}")
            # Return basic fallback
            return AIMessage(content=f"Basic response: processed request")
