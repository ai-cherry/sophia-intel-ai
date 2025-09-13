"""
Centralized Approved Models List for Sophia Intel AI
======================================================
Single source of truth for all model configurations across:
- LiteLLM Squad
- Builder App  
- Sophia Intel App

Quality & Performance focused - using 2025's top models
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Any
import os
from datetime import datetime

# Model Categories
class ModelCategory(Enum):
    """Categories for model selection"""
    FLAGSHIP = "flagship"           # Best of the best
    PERFORMANCE = "performance"      # Fast and powerful
    CODE = "code"                   # Code-optimized
    CREATIVE = "creative"           # Creative tasks
    RESEARCH = "research"           # Long context, analysis
    MINI = "mini"                   # Efficient but capable
    EXPERIMENTAL = "experimental"   # Cutting edge

class UseCase(Enum):
    """Specific use cases for routing"""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CHAT = "chat"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    RAPID_PROTOTYPING = "rapid_prototyping"

@dataclass
class ModelSpec:
    """Complete specification for a model"""
    provider: str
    model_id: str
    display_name: str
    category: ModelCategory
    context_window: int
    max_output: int
    tokens_per_second: int
    latency_ms: int
    strengths: List[UseCase]
    supports_streaming: bool = True
    supports_functions: bool = True
    supports_vision: bool = False
    supports_json_mode: bool = True
    virtual_key: Optional[str] = None
    priority: int = 1  # 1 = highest priority
    active: bool = True

# ============================================================================
# CENTRALIZED APPROVED MODELS LIST - 2025 TOP PERFORMERS
# ============================================================================

APPROVED_MODELS = {
    # ========== FLAGSHIP MODELS ==========
    "gpt-5": ModelSpec(
        provider="openai",
        model_id="gpt-5",
        display_name="GPT-5",
        category=ModelCategory.FLAGSHIP,
        context_window=256000,
        max_output=32000,
        tokens_per_second=120,
        latency_ms=800,
        strengths=[
            UseCase.REASONING,
            UseCase.ARCHITECTURE,
            UseCase.PLANNING,
            UseCase.ANALYSIS
        ],
        supports_vision=True,
        virtual_key=os.getenv("PORTKEY_VK_OPENAI"),
        priority=1
    ),
    
    "claude-sonnet-4": ModelSpec(
        provider="anthropic",
        model_id="claude-sonnet-4",
        display_name="Claude Sonnet 4",
        category=ModelCategory.FLAGSHIP,
        context_window=200000,
        max_output=8192,
        tokens_per_second=150,
        latency_ms=600,
        strengths=[
            UseCase.CODE_GENERATION,
            UseCase.ANALYSIS,
            UseCase.CREATIVE_WRITING,
            UseCase.TECHNICAL_WRITING
        ],
        supports_vision=True,
        virtual_key=os.getenv("PORTKEY_VK_ANTHROPIC"),
        priority=1
    ),
    
    "gemini-2.5-pro": ModelSpec(
        provider="google",
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        category=ModelCategory.FLAGSHIP,
        context_window=2000000,  # 2M tokens!
        max_output=8192,
        tokens_per_second=200,
        latency_ms=500,
        strengths=[
            UseCase.RESEARCH,
            UseCase.ANALYSIS,
            UseCase.SUMMARIZATION
        ],
        supports_vision=True,
        virtual_key=os.getenv("PORTKEY_VK_GOOGLE", "google-vk-default"),
        priority=1
    ),
    
    # ========== PERFORMANCE MODELS ==========
    "grok-code-fast-1": ModelSpec(
        provider="x-ai",
        model_id="grok-code-fast-1",
        display_name="Grok Code Fast 1",
        category=ModelCategory.PERFORMANCE,
        context_window=128000,
        max_output=8192,
        tokens_per_second=400,
        latency_ms=200,
        strengths=[
            UseCase.CODE_GENERATION,
            UseCase.RAPID_PROTOTYPING,
            UseCase.DEBUGGING
        ],
        virtual_key=os.getenv("PORTKEY_VK_XAI"),
        priority=2
    ),
    
    "gemini-2.5-flash": ModelSpec(
        provider="google",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        category=ModelCategory.PERFORMANCE,
        context_window=1000000,
        max_output=8192,
        tokens_per_second=350,
        latency_ms=250,
        strengths=[
            UseCase.CHAT,
            UseCase.ANALYSIS,
            UseCase.RAPID_PROTOTYPING
        ],
        supports_vision=True,
        virtual_key=os.getenv("PORTKEY_VK_GOOGLE", "google-vk-default"),
        priority=2
    ),
    
    "gemini-2.0-flash": ModelSpec(
        provider="google",
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        category=ModelCategory.PERFORMANCE,
        context_window=1000000,
        max_output=8192,
        tokens_per_second=380,
        latency_ms=220,
        strengths=[
            UseCase.CHAT,
            UseCase.RAPID_PROTOTYPING
        ],
        supports_vision=True,
        virtual_key=os.getenv("PORTKEY_VK_GOOGLE", "google-vk-default"),
        priority=2
    ),
    
    "deepseek-v3.1": ModelSpec(
        provider="deepseek",
        model_id="deepseek-v3.1",
        display_name="DeepSeek V3.1",
        category=ModelCategory.PERFORMANCE,
        context_window=128000,
        max_output=8192,
        tokens_per_second=250,
        latency_ms=400,
        strengths=[
            UseCase.CODE_REVIEW,
            UseCase.DEBUGGING,
            UseCase.REASONING
        ],
        virtual_key=os.getenv("PORTKEY_VK_DEEPSEEK"),
        priority=2
    ),
    
    # ========== SPECIALIZED MODELS ==========
    "sonoma-sky-alpha": ModelSpec(
        provider="openrouter",
        model_id="sonoma-sky-alpha",
        display_name="Sonoma Sky Alpha",
        category=ModelCategory.CREATIVE,
        context_window=200000,
        max_output=8192,
        tokens_per_second=180,
        latency_ms=500,
        strengths=[
            UseCase.CREATIVE_WRITING,
            UseCase.TECHNICAL_WRITING
        ],
        virtual_key=os.getenv("PORTKEY_VK_OPENROUTER"),
        priority=3
    ),
    
    "sonoma-dusk-alpha": ModelSpec(
        provider="openrouter",
        model_id="sonoma-dusk-alpha",
        display_name="Sonoma Dusk Alpha",
        category=ModelCategory.CREATIVE,
        context_window=200000,
        max_output=8192,
        tokens_per_second=180,
        latency_ms=500,
        strengths=[
            UseCase.TECHNICAL_WRITING,
            UseCase.ANALYSIS
        ],
        virtual_key=os.getenv("PORTKEY_VK_OPENROUTER"),
        priority=3
    ),
    
    "qwen3-30b-a3b": ModelSpec(
        provider="qwen",
        model_id="qwen3-30b-a3b",
        display_name="Qwen3 30B A3B",
        category=ModelCategory.RESEARCH,
        context_window=32768,
        max_output=4096,
        tokens_per_second=150,
        latency_ms=600,
        strengths=[
            UseCase.TRANSLATION,
            UseCase.RESEARCH
        ],
        virtual_key=os.getenv("PORTKEY_VK_QWEN", "qwen-vk-default"),
        priority=3
    ),
    
    "glm-4.5": ModelSpec(
        provider="z-ai",
        model_id="glm-4.5",
        display_name="GLM 4.5",
        category=ModelCategory.RESEARCH,
        context_window=128000,
        max_output=8192,
        tokens_per_second=160,
        latency_ms=550,
        strengths=[
            UseCase.RESEARCH,
            UseCase.ANALYSIS
        ],
        virtual_key=os.getenv("PORTKEY_VK_ZAI", "zai-vk-default"),
        priority=3
    ),
    
    # ========== MINI MODELS ==========
    "gpt-4.1-mini": ModelSpec(
        provider="openai",
        model_id="gpt-4.1-mini",
        display_name="GPT-4.1 Mini",
        category=ModelCategory.MINI,
        context_window=128000,
        max_output=16384,
        tokens_per_second=250,
        latency_ms=300,
        strengths=[
            UseCase.CHAT,
            UseCase.SUMMARIZATION
        ],
        virtual_key=os.getenv("PORTKEY_VK_OPENAI"),
        priority=4
    ),
    
    "gemini-2.5-flash-lite": ModelSpec(
        provider="google",
        model_id="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash Lite",
        category=ModelCategory.MINI,
        context_window=1000000,
        max_output=8192,
        tokens_per_second=450,
        latency_ms=150,
        strengths=[
            UseCase.CHAT,
            UseCase.RAPID_PROTOTYPING
        ],
        virtual_key=os.getenv("PORTKEY_VK_GOOGLE", "google-vk-default"),
        priority=4
    ),
    
    # ========== EXPERIMENTAL MODELS ==========
    "gpt-oss-120b": ModelSpec(
        provider="openai",
        model_id="gpt-oss-120b",
        display_name="GPT-OSS 120B",
        category=ModelCategory.EXPERIMENTAL,
        context_window=128000,
        max_output=8192,
        tokens_per_second=180,
        latency_ms=700,
        strengths=[
            UseCase.RESEARCH,
            UseCase.ANALYSIS
        ],
        virtual_key=os.getenv("PORTKEY_VK_OPENAI"),
        priority=5,
        active=False  # Experimental - opt-in only
    ),
    
    "deepseek-v3-0324": ModelSpec(
        provider="deepseek",
        model_id="deepseek-v3-0324",
        display_name="DeepSeek V3 0324",
        category=ModelCategory.EXPERIMENTAL,
        context_window=128000,
        max_output=8192,
        tokens_per_second=200,
        latency_ms=500,
        strengths=[
            UseCase.REASONING,
            UseCase.CODE_GENERATION
        ],
        virtual_key=os.getenv("PORTKEY_VK_DEEPSEEK"),
        priority=5,
        active=False  # Experimental - opt-in only
    ),
    
    "claude-3.7-sonnet": ModelSpec(
        provider="anthropic",
        model_id="claude-3.7-sonnet",
        display_name="Claude 3.7 Sonnet",
        category=ModelCategory.EXPERIMENTAL,
        context_window=200000,
        max_output=8192,
        tokens_per_second=170,
        latency_ms=650,
        strengths=[
            UseCase.CODE_GENERATION,
            UseCase.CREATIVE_WRITING
        ],
        virtual_key=os.getenv("PORTKEY_VK_ANTHROPIC"),
        priority=5,
        active=False  # Experimental - opt-in only
    ),
}

# ============================================================================
# FLEXIBLE ROUTING POLICIES
# ============================================================================

class RoutingPolicy:
    """Flexible routing policy that can be customized per request"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.models: List[str] = []
        self.fallback_models: List[str] = []
        self.filters: Dict[str, Any] = {}
    
    def add_model(self, model_id: str, is_fallback: bool = False):
        """Add a model to the policy"""
        if is_fallback:
            self.fallback_models.append(model_id)
        else:
            self.models.append(model_id)
        return self
    
    def filter_by_category(self, category: ModelCategory):
        """Filter models by category"""
        self.filters["category"] = category
        return self
    
    def filter_by_use_case(self, use_case: UseCase):
        """Filter models by use case"""
        self.filters["use_case"] = use_case
        return self
    
    def filter_by_latency(self, max_latency_ms: int):
        """Filter models by maximum latency"""
        self.filters["max_latency"] = max_latency_ms
        return self
    
    def filter_by_context(self, min_context: int):
        """Filter models by minimum context window"""
        self.filters["min_context"] = min_context
        return self
    
    def get_models(self) -> List[ModelSpec]:
        """Get filtered models based on policy"""
        models = []
        
        for model_id, spec in APPROVED_MODELS.items():
            if not spec.active:
                continue
                
            # Apply filters
            if "category" in self.filters and spec.category != self.filters["category"]:
                continue
            
            if "use_case" in self.filters and self.filters["use_case"] not in spec.strengths:
                continue
            
            if "max_latency" in self.filters and spec.latency_ms > self.filters["max_latency"]:
                continue
            
            if "min_context" in self.filters and spec.context_window < self.filters["min_context"]:
                continue
            
            # Check if explicitly included
            if model_id in self.models:
                models.append(spec)
            elif not self.models and not self.filters:  # No specific models, include all active
                models.append(spec)
        
        # Sort by priority
        models.sort(key=lambda x: x.priority)
        return models

# ============================================================================
# PRE-CONFIGURED ROUTING POLICIES
# ============================================================================

ROUTING_POLICIES = {
    "maximum_quality": RoutingPolicy("Maximum Quality", "Best possible output quality")
        .add_model("gpt-5")
        .add_model("claude-sonnet-4")
        .add_model("gemini-2.5-pro")
        .add_model("gpt-4.1-mini", is_fallback=True),
    
    "maximum_speed": RoutingPolicy("Maximum Speed", "Fastest possible response")
        .add_model("grok-code-fast-1")
        .add_model("gemini-2.5-flash")
        .add_model("gemini-2.0-flash")
        .add_model("gemini-2.5-flash-lite")
        .filter_by_latency(300),
    
    "code_specialist": RoutingPolicy("Code Specialist", "Optimized for coding tasks")
        .add_model("grok-code-fast-1")
        .add_model("claude-sonnet-4")
        .add_model("deepseek-v3.1")
        .add_model("gpt-5", is_fallback=True)
        .filter_by_use_case(UseCase.CODE_GENERATION),
    
    "creative_specialist": RoutingPolicy("Creative Specialist", "For creative tasks")
        .add_model("sonoma-sky-alpha")
        .add_model("claude-sonnet-4")
        .add_model("sonoma-dusk-alpha", is_fallback=True)
        .filter_by_use_case(UseCase.CREATIVE_WRITING),
    
    "research_specialist": RoutingPolicy("Research Specialist", "Deep analysis & long context")
        .add_model("gemini-2.5-pro")  # 2M context!
        .add_model("gpt-5")
        .add_model("glm-4.5")
        .filter_by_context(100000),
    
    "balanced": RoutingPolicy("Balanced", "Good balance of speed and quality")
        .filter_by_category(ModelCategory.PERFORMANCE),
    
    "auto": RoutingPolicy("Auto", "Automatic selection based on task")
        # Auto policy uses all active models and selects based on task
}

# ============================================================================
# HELPER FUNCTIONS FOR ALL SYSTEMS
# ============================================================================

def get_model_by_id(model_id: str) -> Optional[ModelSpec]:
    """Get a specific model by ID"""
    return APPROVED_MODELS.get(model_id)

def get_models_by_category(category: ModelCategory) -> List[ModelSpec]:
    """Get all models in a category"""
    return [
        spec for spec in APPROVED_MODELS.values()
        if spec.category == category and spec.active
    ]

def get_models_by_use_case(use_case: UseCase) -> List[ModelSpec]:
    """Get all models suitable for a use case"""
    models = [
        spec for spec in APPROVED_MODELS.values()
        if use_case in spec.strengths and spec.active
    ]
    models.sort(key=lambda x: x.priority)
    return models

def get_fastest_model_for_use_case(use_case: UseCase) -> Optional[ModelSpec]:
    """Get the fastest model for a specific use case"""
    suitable = get_models_by_use_case(use_case)
    if suitable:
        return min(suitable, key=lambda x: x.latency_ms)
    return None

def get_best_model_for_context(required_context: int) -> Optional[ModelSpec]:
    """Get the best model that can handle the required context"""
    suitable = [
        spec for spec in APPROVED_MODELS.values()
        if spec.context_window >= required_context and spec.active
    ]
    if suitable:
        suitable.sort(key=lambda x: (x.priority, -x.context_window))
        return suitable[0]
    return None

def select_model_for_task(
    task: str,
    use_case: Optional[UseCase] = None,
    max_latency_ms: Optional[int] = None,
    min_context: Optional[int] = None,
    policy_name: Optional[str] = None
) -> ModelSpec:
    """
    Smart model selection based on task requirements
    Used by all three systems (LiteLLM, Builder, Sophia)
    """
    # Use specified policy if provided
    if policy_name and policy_name in ROUTING_POLICIES:
        policy = ROUTING_POLICIES[policy_name]
        models = policy.get_models()
        if models:
            return models[0]
    
    # Otherwise, build dynamic policy
    policy = RoutingPolicy("Dynamic", "Task-specific selection")
    
    if use_case:
        policy.filter_by_use_case(use_case)
    
    if max_latency_ms:
        policy.filter_by_latency(max_latency_ms)
    
    if min_context:
        policy.filter_by_context(min_context)
    
    # Get suitable models
    models = policy.get_models()
    
    # If no models match filters, fall back to best available
    if not models:
        models = [
            spec for spec in APPROVED_MODELS.values()
            if spec.active
        ]
        models.sort(key=lambda x: x.priority)
    
    return models[0] if models else APPROVED_MODELS["gpt-5"]

# ============================================================================
# SYSTEM-SPECIFIC CONFIGURATIONS
# ============================================================================

class SystemConfig:
    """Configuration for each system using the approved models"""
    
    @staticmethod
    def litellm_squad_config() -> Dict[str, Any]:
        """Configuration for LiteLLM Squad"""
        return {
            "models": {
                model_id: {
                    "provider": spec.provider,
                    "model": spec.model_id,
                    "virtual_key": spec.virtual_key,
                    "max_tokens": spec.max_output,
                    "temperature": 0.7,
                    "stream": spec.supports_streaming
                }
                for model_id, spec in APPROVED_MODELS.items()
                if spec.active
            },
            "routing": ROUTING_POLICIES,
            "default_policy": "balanced"
        }
    
    @staticmethod
    def builder_app_config() -> Dict[str, Any]:
        """Configuration for Builder App"""
        return {
            "planner_models": [
                "gpt-5",
                "claude-sonnet-4",
                "gemini-2.5-pro"
            ],
            "coder_models": [
                "grok-code-fast-1",
                "claude-sonnet-4",
                "deepseek-v3.1"
            ],
            "reviewer_models": [
                "gpt-5",
                "claude-sonnet-4",
                "deepseek-v3.1"
            ],
            "default_policy": "code_specialist"
        }
    
    @staticmethod
    def sophia_intel_config() -> Dict[str, Any]:
        """Configuration for Sophia Intel App"""
        return {
            "chat_models": get_models_by_category(ModelCategory.PERFORMANCE),
            "reasoning_models": get_models_by_category(ModelCategory.FLAGSHIP),
            "creative_models": get_models_by_category(ModelCategory.CREATIVE),
            "routing_policies": ROUTING_POLICIES,
            "default_model": "claude-sonnet-4"
        }

# ============================================================================
# EXPORT FOR USE BY ALL SYSTEMS
# ============================================================================

__all__ = [
    "APPROVED_MODELS",
    "ROUTING_POLICIES",
    "ModelSpec",
    "ModelCategory",
    "UseCase",
    "RoutingPolicy",
    "get_model_by_id",
    "get_models_by_category",
    "get_models_by_use_case",
    "get_fastest_model_for_use_case",
    "get_best_model_for_context",
    "select_model_for_task",
    "SystemConfig"
]

# Print configuration summary when imported
if __name__ == "__main__":
    print(f"Approved Models Configuration - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total Models: {len(APPROVED_MODELS)}")
    print(f"Active Models: {sum(1 for m in APPROVED_MODELS.values() if m.active)}")
    print(f"Routing Policies: {len(ROUTING_POLICIES)}")
    print("\nCategories:")
    for category in ModelCategory:
        count = sum(1 for m in APPROVED_MODELS.values() if m.category == category and m.active)
        print(f"  {category.value}: {count} models")