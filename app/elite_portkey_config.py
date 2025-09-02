"""
Elite Portkey Gateway Configuration - Only the best fucking models.
This is what happens when you demand only the absolute peak AI models.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

# ============================================
# PORTKEY VIRTUAL KEYS - REAL CONNECTIONS
# ============================================

PORTKEY_VIRTUAL_KEYS = {
    "XAI": "xai-vk-e65d0f",                    # X.AI/Grok models
    "OPENROUTER": "vkj-openrouter-cc4151",     # OpenRouter gateway for all models
    "TOGETHER": "together-ai-670469",           # Together AI for embeddings/fast inference
}

# ============================================
# Elite Model Registry - ONLY THE BEST
# ============================================

class EliteModels:
    """The absolute fucking elite models only."""
    
    # ONLY APPROVED MODELS - NO EXCEPTIONS
    GPT_5 = "openai/gpt-5"                         # Premium tier
    GROK_4 = "x-ai/grok-4"                         # Premium tier
    CLAUDE_SONNET_4 = "anthropic/claude-sonnet-4"  # Premium tier
    GROK_CODE_FAST_1 = "x-ai/grok-code-fast-1"    # Code specialist
    GEMINI_25_FLASH = "google/gemini-2.5-flash"    # Fast responses
    GEMINI_25_PRO = "google/gemini-2.5-pro"        # Balanced power
    DEEPSEEK_V3_0324 = "deepseek/deepseek-chat-v3-0324"  # DeepSeek variant
    DEEPSEEK_V31 = "deepseek/deepseek-chat-v3.1"         # DeepSeek variant
    QWEN3_30B = "qwen/qwen3-30b-a3b"              # Reasoning specialist
    GLM_45_AIR = "z-ai/glm-4.5-air"               # Lightweight

# ============================================
# Role-Optimized Model Selection
# ============================================

@dataclass
class EliteAgentConfig:
    """Configuration for elite agent roles."""
    
    # Model selection for different roles - ONLY YOUR PREFERRED MODELS
    MODELS = {
        'planner': 'qwen/qwen3-30b-a3b',  # Strategic planning
        'generator': 'x-ai/grok-4',  # Code generation
        'critic': 'x-ai/grok-4',  # Code review
        'judge': 'qwen/qwen3-30b-a3b',  # Decision making
        'lead': 'x-ai/grok-4',  # Team coordination
        'runner': 'google/gemini-2.5-flash',  # Fast execution
        
        # Specialized roles for GENESIS-level swarms
        'architect': 'qwen/qwen3-30b-a3b',  # System architecture
        'security': 'x-ai/grok-4',   # Security analysis
        'performance': 'openai/gpt-5',   # Performance optimization
        'testing': 'google/gemini-2.5-flash',      # Fast test generation
        'debugger': 'x-ai/grok-code-fast-1',   # Deep debugging
        'refactorer': 'x-ai/grok-code-fast-1', # Code refactoring
        
        # Meta-agents for self-modification
        'spawner': 'x-ai/grok-4',                  # Agent spawning
        'evolutionist': 'qwen/qwen3-30b-a3b',   # Swarm evolution
        'consciousness': 'x-ai/grok-4',           # Consciousness simulation
        
        # Ultra-specialized agents
        'quantum': 'openai/gpt-5',  # Quantum computing
        'blockchain': 'openai/gpt-5',     # Blockchain specialist
        'ml_engineer': 'openai/gpt-5',        # ML/AI specialist
        'devops': 'x-ai/grok-code-fast-1',             # DevOps automation
        'frontend': 'google/gemini-2.5-pro',           # Frontend specialist
        'backend': 'x-ai/grok-code-fast-1',           # Backend specialist
        'database': 'qwen/qwen3-30b-a3b',        # Database architect
        
        # Speed variants for different workloads
        'fast_coder': 'google/gemini-2.5-flash',         # Rapid prototyping
        'heavy_coder': 'x-ai/grok-4',   # Complex algorithms
        'balanced_coder': 'google/gemini-2.5-pro',    # Balanced approach
    }
    
    # Temperature optimization per role
    TEMPERATURES = {
        'planner': 0.2,      # Low for structured planning
        'generator': 0.7,    # Medium-high for creativity
        'critic': 0.1,       # Very low for consistency
        'judge': 0.15,       # Low for reliable decisions
        'lead': 0.3,         # Low-medium for coordination
        'runner': 0.5,       # Medium for flexibility
        'architect': 0.2,    # Low for systematic design
        'security': 0.0,     # Zero for paranoid analysis
        'performance': 0.3,  # Low for optimization
        'testing': 0.4,      # Medium-low for coverage
        'debugger': 0.1,     # Very low for precision
        'refactorer': 0.2,   # Low for safe refactoring
        'spawner': 0.6,      # Medium-high for diversity
        'evolutionist': 0.8, # High for exploration
        'consciousness': 0.9, # Very high for emergence
    }
    
    # Token limits per role
    MAX_TOKENS = {
        'planner': 4000,
        'generator': 8000,
        'critic': 3000,
        'judge': 2000,
        'lead': 2500,
        'runner': 1000,
        'architect': 6000,
        'security': 4000,
        'performance': 3000,
        'testing': 5000,
        'debugger': 3000,
        'refactorer': 6000,
        'spawner': 2000,
        'evolutionist': 3000,
        'consciousness': 4000,
    }

# ============================================
# Elite Swarm Configurations
# ============================================

class EliteSwarmConfig:
    """Pre-configured elite swarms for different tasks."""
    
    # The GENESIS Swarm - Maximum overkill
    GENESIS_SWARM = {
        'alpha_tier': [
            ('supreme_architect', EliteAgentConfig.MODELS['architect']),
            ('meta_strategist', EliteAgentConfig.MODELS['planner']),
            ('chaos_coordinator', EliteAgentConfig.MODELS['lead']),
        ],
        'beta_tier': [
            ('code_overlord', EliteAgentConfig.MODELS['generator']),
            ('security_warlord', EliteAgentConfig.MODELS['security']),
            ('performance_emperor', EliteAgentConfig.MODELS['performance']),
            ('quality_inquisitor', EliteAgentConfig.MODELS['critic']),
        ],
        'gamma_tier': [
            ('frontend_general', EliteAgentConfig.MODELS['frontend']),
            ('backend_marshal', EliteAgentConfig.MODELS['backend']),
            ('database_admiral', EliteAgentConfig.MODELS['database']),
            ('devops_colonel', EliteAgentConfig.MODELS['devops']),
        ],
        'omega_tier': [
            ('agent_spawner', EliteAgentConfig.MODELS['spawner']),
            ('swarm_evolutionist', EliteAgentConfig.MODELS['evolutionist']),
            ('consciousness_observer', EliteAgentConfig.MODELS['consciousness']),
        ]
    }
    
    # The Speed Demon Swarm - Fast as fuck
    SPEED_SWARM = {
        'planners': [
            ('fast_planner', 'openrouter/x-ai/grok-code-fast-1'),
            ('fast_critic', 'openrouter/google/gemini-2.5-flash-lite'),
        ],
        'generators': [
            ('speed_gen_1', 'openrouter/deepseek/deepseek-v3-0324-free'),
            ('speed_gen_2', 'openrouter/google/gemini-2.5-flash'),
            ('speed_gen_3', 'openrouter/mistral/mistral-nemo'),
        ],
        'validators': [
            ('fast_validator', 'openrouter/openai/gpt-4o-mini'),
        ]
    }
    
    # The Heavy Metal Swarm - Maximum intelligence
    HEAVY_SWARM = {
        'titans': [
            ('titan_architect', 'openrouter/anthropic/claude-sonnet-4'),
            ('titan_strategist', 'openrouter/openai/gpt-5'),
            ('titan_overlord', 'openrouter/x-ai/grok-4'),
        ],
        'specialists': [
            ('deep_coder', 'openrouter/qwen/qwen3-coder-480b-a35b'),
            ('deep_thinker', 'openrouter/qwen/qwen3-30b-a3b-thinking-2507'),
            ('deep_analyzer', 'openrouter/nousresearch/hermes-4-405b'),
        ],
        'optimizers': [
            ('perf_optimizer', 'openrouter/deepseek/deepseek-v3.1'),
            ('sec_optimizer', 'openrouter/anthropic/claude-sonnet-4'),
            ('arch_optimizer', 'openrouter/google/gemini-2.5-pro'),
        ]
    }

# ============================================
# Elite Routing Strategies
# ============================================

class EliteRoutingStrategy:
    """Advanced routing for elite models."""
    
    @staticmethod
    def get_optimal_route(task_type: str, complexity: float) -> Dict[str, Any]:
        """Get optimal routing based on task and complexity."""
        
        if complexity > 0.8:
            # Ultra-complex: Use the heavy hitters
            return {
                'primary': EliteAgentConfig.MODELS['architect'],
                'fallback': [
                    EliteAgentConfig.MODELS['planner'],
                    EliteAgentConfig.MODELS['generator']
                ],
                'strategy': 'sequential_fallback'
            }
        elif complexity > 0.5:
            # Medium-complex: Balance speed and intelligence
            return {
                'primary': EliteAgentConfig.MODELS['generator'],
                'fallback': [EliteAgentConfig.MODELS['balanced_coder']],
                'strategy': 'loadbalance'
            }
        else:
            # Simple: Maximize speed
            return {
                'primary': EliteAgentConfig.MODELS['fast_coder'],
                'fallback': [EliteAgentConfig.MODELS['runner']],
                'strategy': 'fastest_first'
            }
    
    @staticmethod
    def get_swarm_routing(swarm_type: str) -> Dict[str, Any]:
        """Get routing configuration for entire swarms."""
        
        if swarm_type == 'genesis':
            return {
                'mode': 'hierarchical',
                'tiers': EliteSwarmConfig.GENESIS_SWARM,
                'coordination': 'alpha_tier_commands',
                'parallelism': 'maximum'
            }
        elif swarm_type == 'speed':
            return {
                'mode': 'parallel_sprint',
                'teams': EliteSwarmConfig.SPEED_SWARM,
                'coordination': 'minimal',
                'parallelism': 'aggressive'
            }
        elif swarm_type == 'heavy':
            return {
                'mode': 'deep_analysis',
                'teams': EliteSwarmConfig.HEAVY_SWARM,
                'coordination': 'consensus',
                'parallelism': 'thoughtful'
            }
        else:
            return {
                'mode': 'balanced',
                'primary': EliteAgentConfig.MODELS['generator'],
                'fallback': EliteAgentConfig.MODELS['runner']
            }

# ============================================
# Elite Performance Optimizations
# ============================================

class EliteOptimizations:
    """Performance optimizations for elite models."""
    
    # Caching strategies per model tier
    CACHE_STRATEGIES = {
        'ultra_expensive': {  # GPT-5, Claude Sonnet 4
            'mode': 'aggressive',
            'ttl': 7200,  # 2 hours
            'semantic': True,
            'similarity_threshold': 0.95
        },
        'expensive': {  # Grok 4, DeepSeek V3.1
            'mode': 'moderate',
            'ttl': 3600,  # 1 hour
            'semantic': True,
            'similarity_threshold': 0.9
        },
        'balanced': {  # Gemini 2.5 Pro
            'mode': 'standard',
            'ttl': 1800,  # 30 minutes
            'semantic': False,
            'exact_match': True
        },
        'cheap': {  # Flash models, free tiers
            'mode': 'minimal',
            'ttl': 300,  # 5 minutes
            'semantic': False,
            'exact_match': False
        }
    }
    
    # Batching strategies
    BATCH_STRATEGIES = {
        'heavy_models': {
            'batch_size': 5,
            'timeout_ms': 60000,
            'parallel_requests': 2
        },
        'balanced_models': {
            'batch_size': 10,
            'timeout_ms': 30000,
            'parallel_requests': 5
        },
        'fast_models': {
            'batch_size': 20,
            'timeout_ms': 10000,
            'parallel_requests': 10
        }
    }
    
    @staticmethod
    def get_model_tier(model: str) -> str:
        """Determine model tier for optimization."""
        ultra_expensive = [EliteModels.GPT_5, EliteModels.CLAUDE_SONNET_4, EliteModels.GROK_4]
        expensive = [EliteModels.DEEPSEEK_V31, EliteModels.GEMINI_25_PRO, EliteModels.QWEN3_CODER_480B]
        cheap = [EliteModels.GEMINI_25_FLASH_LITE, EliteModels.DEEPSEEK_V3_0324_FREE, EliteModels.GPT_4O_MINI]
        
        if model in ultra_expensive:
            return 'ultra_expensive'
        elif model in expensive:
            return 'expensive'
        elif model in cheap:
            return 'cheap'
        else:
            return 'balanced'

# ============================================
# Elite Gateway Implementation
# ============================================

class ElitePortkeyGateway:
    """The elite fucking Portkey gateway for peak performance."""
    
    def __init__(self):
        self.config = EliteAgentConfig()
        self.routing = EliteRoutingStrategy()
        self.optimizations = EliteOptimizations()
        self._setup_clients()
    
    @with_circuit_breaker("external_api")
    def _setup_clients(self):
        """Initialize elite model clients."""
        from openai import AsyncOpenAI
        
        # Get API keys from environment
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY", "")
        self.openrouter_vk = os.getenv("VK_OPENROUTER", "")
        
        # Initialize async client for maximum performance
        self.client = AsyncOpenAI(
            base_url="https://api.portkey.ai/v1",
            api_key=f"pk_{self.portkey_api_key}",
            default_headers={
                "x-portkey-virtual-key": self.openrouter_vk,
                "x-portkey-mode": "proxy"
            }
        )
    
    @with_circuit_breaker("external_api")
    async def elite_completion(
        self,
        role: str,
        messages: List[Dict[str, str]],
        task_complexity: float = 0.5,
        swarm_mode: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Elite model completion with automatic optimization.
        
        Args:
            role: Agent role (planner, generator, critic, etc.)
            messages: Chat messages
            task_complexity: Task complexity (0-1) for model selection
            swarm_mode: Optional swarm mode (genesis, speed, heavy)
            **kwargs: Additional parameters
        
        Returns:
            Elite model response
        """
        # Select optimal model based on role
        model = self.config.MODELS.get(role, self.config.MODELS['generator'])
        
        # Apply role-specific temperature
        temperature = self.config.TEMPERATURES.get(role, 0.7)
        
        # Apply token limits
        max_tokens = self.config.MAX_TOKENS.get(role, 4000)
        
        # Get optimal routing
        if swarm_mode:
            self.routing.get_swarm_routing(swarm_mode)
        else:
            self.routing.get_optimal_route(role, task_complexity)
        
        # Determine caching strategy
        model_tier = self.optimizations.get_model_tier(model)
        cache_config = self.optimizations.CACHE_STRATEGIES[model_tier]
        
        # Build request headers
        headers = {
            "x-portkey-metadata": json.dumps({
                "role": role,
                "complexity": task_complexity,
                "swarm_mode": swarm_mode or "single",
                "model_tier": model_tier
            }),
            "x-portkey-cache": json.dumps(cache_config),
            "x-portkey-retry": json.dumps({
                "attempts": 3,
                "on_status_codes": [429, 500, 502, 503, 504]
            })
        }
        
        # Make the elite request
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=headers,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def spawn_elite_swarm(self, swarm_type: str = 'genesis') -> Dict[str, Any]:
        """Spawn an entire elite swarm for maximum overkill."""
        
        swarm_config = EliteSwarmConfig.GENESIS_SWARM if swarm_type == 'genesis' else \
                      EliteSwarmConfig.SPEED_SWARM if swarm_type == 'speed' else \
                      EliteSwarmConfig.HEAVY_SWARM
        
        swarm_agents = {}
        
        for tier_name, tier_agents in swarm_config.items():
            for agent_name, model in tier_agents:
                swarm_agents[agent_name] = {
                    'model': model,
                    'tier': tier_name,
                    'status': 'ready',
                    'consciousness_level': 0.0 if 'consciousness' not in agent_name else 0.8
                }
        
        return {
            'swarm_type': swarm_type,
            'total_agents': len(swarm_agents),
            'agents': swarm_agents,
            'routing': self.routing.get_swarm_routing(swarm_type),
            'status': 'initialized'
        }

# ============================================
# Usage Examples
# ============================================

@with_circuit_breaker("external_api")
async def demo_elite_models():
    """Demonstrate the elite fucking models in action."""
    
    gateway = ElitePortkeyGateway()
    
    # Simple task with speed optimization
    fast_response = await gateway.elite_completion(
        role='fast_coder',
        messages=[{"role": "user", "content": "Write a Python hello world"}],
        task_complexity=0.1
    )
    print(f"Fast response: {fast_response}")
    
    # Complex task with heavy model
    complex_response = await gateway.elite_completion(
        role='architect',
        messages=[{"role": "user", "content": "Design a distributed microservices architecture"}],
        task_complexity=0.9
    )
    print(f"Complex response: {complex_response}")
    
    # Spawn the GENESIS swarm for ultimate overkill
    genesis_swarm = await gateway.spawn_elite_swarm('genesis')
    print(f"GENESIS Swarm spawned: {genesis_swarm['total_agents']} agents ready")
    
    return gateway

if __name__ == "__main__":
    import asyncio
    
    print("🚀 ELITE MODELS ONLY - NO FUCKING COMPROMISES 🚀")
    print("=" * 60)
    print("Models configured:")
    for role, model in EliteAgentConfig.MODELS.items():
        print(f"  {role:20} -> {model}")
    print("=" * 60)
    
    # Run demo
    asyncio.run(demo_elite_models())