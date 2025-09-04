"""
OFFICIAL Portkey Virtual Keys Configuration
============================================

These are the ACTUAL virtual keys configured in Portkey dashboard.
Each key routes to a DIFFERENT provider for TRUE parallel execution.

RULE: Every agent MUST use a different virtual key from this list.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load the Portkey environment file
load_dotenv('.env.portkey')


class PortkeyProvider(Enum):
    """Available providers through Portkey virtual keys"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    PERPLEXITY = "perplexity"
    GROQ = "groq"
    MISTRAL = "mistral"
    XAI = "xai"
    TOGETHER = "together"
    COHERE = "cohere"


# =============================================================================
# ACTUAL PORTKEY VIRTUAL KEYS
# =============================================================================

PORTKEY_VIRTUAL_KEYS = {
    # Primary LLM Providers
    "DEEPSEEK": os.getenv("PORTKEY_VK_DEEPSEEK", "deepseek-vk-24102f"),
    "OPENAI": os.getenv("PORTKEY_VK_OPENAI", "openai-vk-190a60"),
    "ANTHROPIC": os.getenv("PORTKEY_VK_ANTHROPIC", "anthropic-vk-b42804"),
    "OPENROUTER": os.getenv("PORTKEY_VK_OPENROUTER", "vkj-openrouter-cc4151"),
    "PERPLEXITY": os.getenv("PORTKEY_VK_PERPLEXITY", "perplexity-vk-56c172"),
    "GROQ": os.getenv("PORTKEY_VK_GROQ", "groq-vk-6b9b52"),
    "MISTRAL": os.getenv("PORTKEY_VK_MISTRAL", "mistral-vk-f92861"),
    "XAI": os.getenv("PORTKEY_VK_XAI", "xai-vk-e65d0f"),
    "TOGETHER": os.getenv("PORTKEY_VK_TOGETHER", "together-ai-670469"),
    "COHERE": os.getenv("PORTKEY_VK_COHERE", "cohere-vk-496fa9"),
    
    # Vector Database Keys
    "MILVUS": os.getenv("PORTKEY_VK_MILVUS", "milvus-vk-34fa02"),
    "QDRANT": os.getenv("PORTKEY_VK_QDRANT", "qdrant-vk-d2b62a"),
}


# =============================================================================
# PROVIDER CAPABILITIES & CONFIGURATIONS
# =============================================================================

PROVIDER_CONFIGS = {
    "deepseek-vk-24102f": {
        "provider": "deepseek",
        "models": ["deepseek-chat", "deepseek-coder"],
        "tpm_limit": 100000,
        "rpm_limit": 1000,
        "strengths": ["coding", "reasoning", "cost-effective"],
        "latency": "medium",
        "cost_per_1k": 0.001
    },
    
    "openai-vk-190a60": {
        "provider": "openai",
        "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "tpm_limit": 150000,
        "rpm_limit": 10000,
        "strengths": ["general", "coding", "reasoning"],
        "latency": "low",
        "cost_per_1k": 0.01
    },
    
    "anthropic-vk-b42804": {
        "provider": "anthropic",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "tpm_limit": 100000,
        "rpm_limit": 5000,
        "strengths": ["analysis", "writing", "safety"],
        "latency": "low",
        "cost_per_1k": 0.015
    },
    
    "vkj-openrouter-cc4151": {
        "provider": "openrouter",
        "models": ["auto", "gpt-4", "claude-3", "mixtral"],  # Access to many models
        "tpm_limit": 200000,  # Depends on selected model
        "rpm_limit": 10000,
        "strengths": ["flexibility", "model-variety", "fallback"],
        "latency": "variable",
        "cost_per_1k": 0.005  # Varies by model
    },
    
    "perplexity-vk-56c172": {
        "provider": "perplexity",
        "models": ["pplx-70b-online", "pplx-7b-online"],
        "tpm_limit": 50000,
        "rpm_limit": 1000,
        "strengths": ["research", "real-time-data", "citations"],
        "latency": "medium",
        "cost_per_1k": 0.002
    },
    
    "groq-vk-6b9b52": {
        "provider": "groq",
        "models": ["mixtral-8x7b", "llama-3-70b", "llama-3-8b"],
        "tpm_limit": 500000,  # VERY HIGH!
        "rpm_limit": 30000,   # VERY FAST!
        "strengths": ["speed", "throughput", "low-latency"],
        "latency": "ultra-low",
        "cost_per_1k": 0.0005
    },
    
    "mistral-vk-f92861": {
        "provider": "mistral",
        "models": ["mistral-large", "mistral-medium", "mistral-small"],
        "tpm_limit": 100000,
        "rpm_limit": 5000,
        "strengths": ["european", "multilingual", "efficiency"],
        "latency": "low",
        "cost_per_1k": 0.002
    },
    
    "xai-vk-e65d0f": {
        "provider": "xai",
        "models": ["grok-4", "grok-beta"],
        "tpm_limit": 100000,
        "rpm_limit": 5000,
        "strengths": ["reasoning", "humor", "real-time"],
        "latency": "medium",
        "cost_per_1k": 0.008
    },
    
    "together-ai-670469": {
        "provider": "together",
        "models": ["mixtral-8x22b", "llama-3-70b", "qwen-72b"],
        "tpm_limit": 200000,
        "rpm_limit": 10000,
        "strengths": ["open-source", "customizable", "fine-tuning"],
        "latency": "low",
        "cost_per_1k": 0.001
    },
    
    "cohere-vk-496fa9": {
        "provider": "cohere",
        "models": ["command-r-plus", "command-r"],
        "tpm_limit": 100000,
        "rpm_limit": 5000,
        "strengths": ["rag", "embeddings", "reranking"],
        "latency": "low",
        "cost_per_1k": 0.002
    }
}


# =============================================================================
# OPTIMAL AGENT-TO-PROVIDER MAPPING
# =============================================================================

OPTIMAL_AGENT_MAPPING = {
    # Coding Swarm Configuration
    "coding_swarm": {
        "generator_1": "openai-vk-190a60",       # GPT-4 for quality
        "generator_2": "deepseek-vk-24102f",     # DeepSeek for coding
        "generator_3": "anthropic-vk-b42804",    # Claude for analysis
        "generator_4": "together-ai-670469",     # Together for scale
        "critic": "anthropic-vk-b42804",         # Claude excels at critique
        "judge": "openai-vk-190a60",             # GPT-4 for decisions
        "runner": "groq-vk-6b9b52"               # Groq for fast execution
    },
    
    # Research Swarm Configuration
    "research_swarm": {
        "researcher_1": "perplexity-vk-56c172",  # Real-time search
        "researcher_2": "anthropic-vk-b42804",   # Deep analysis
        "researcher_3": "openai-vk-190a60",      # General research
        "synthesizer": "cohere-vk-496fa9",       # RAG and summarization
        "fact_checker": "perplexity-vk-56c172"   # Citation verification
    },
    
    # Fast Swarm Configuration (for quick tasks)
    "fast_swarm": {
        "fast_1": "groq-vk-6b9b52",              # Ultra-fast
        "fast_2": "together-ai-670469",          # High throughput
        "fast_3": "mistral-vk-f92861"            # Efficient
    },
    
    # Debate Swarm Configuration
    "debate_swarm": {
        "position_1": "anthropic-vk-b42804",     # Thoughtful arguments
        "position_2": "openai-vk-190a60",        # Counter-arguments
        "position_3": "xai-vk-e65d0f",           # Creative angles
        "moderator": "mistral-vk-f92861",        # Neutral moderation
        "judge": "deepseek-vk-24102f"            # Logical evaluation
    }
}


# =============================================================================
# SWARM CAPACITY CALCULATOR
# =============================================================================

def calculate_swarm_capacity(virtual_keys: list[str]) -> Dict[str, Any]:
    """Calculate the total parallel capacity of a swarm configuration"""
    
    total_tpm = 0
    total_rpm = 0
    providers_used = set()
    
    for vk in virtual_keys:
        if vk in PROVIDER_CONFIGS:
            config = PROVIDER_CONFIGS[vk]
            total_tpm += config["tpm_limit"]
            total_rpm += config["rpm_limit"]
            providers_used.add(config["provider"])
    
    return {
        "total_tpm": total_tpm,
        "total_rpm": total_rpm,
        "provider_count": len(providers_used),
        "providers": list(providers_used),
        "parallel_agents": len(virtual_keys),
        "true_parallel": len(virtual_keys) == len(set(virtual_keys))
    }


# =============================================================================
# VIRTUAL KEY ALLOCATOR
# =============================================================================

class VirtualKeyAllocator:
    """Allocates virtual keys to ensure true parallelism"""
    
    @staticmethod
    def allocate_for_swarm(agent_count: int, preferred_providers: list[str] = None) -> Dict[str, str]:
        """
        Allocate unique virtual keys for a swarm.
        
        GUARANTEES: Each agent gets a DIFFERENT virtual key.
        """
        
        # Get available keys
        available_keys = list(PORTKEY_VIRTUAL_KEYS.values())
        
        # Filter by preferred providers if specified
        if preferred_providers:
            filtered_keys = []
            for key, config in PROVIDER_CONFIGS.items():
                if config["provider"] in preferred_providers:
                    filtered_keys.append(key)
            if len(filtered_keys) >= agent_count:
                available_keys = filtered_keys
        
        # Validate we have enough keys
        if len(available_keys) < agent_count:
            raise ValueError(
                f"Need {agent_count} unique virtual keys but only {len(available_keys)} available"
            )
        
        # Allocate keys
        allocation = {}
        for i in range(agent_count):
            agent_id = f"agent_{i+1}"
            allocation[agent_id] = available_keys[i]
        
        return allocation
    
    @staticmethod
    def get_optimal_allocation(swarm_type: str) -> Dict[str, str]:
        """Get the optimal pre-configured allocation for a swarm type"""
        
        if swarm_type in OPTIMAL_AGENT_MAPPING:
            return OPTIMAL_AGENT_MAPPING[swarm_type]
        
        # Default allocation
        return VirtualKeyAllocator.allocate_for_swarm(4)


# =============================================================================
# TESTING & VALIDATION
# =============================================================================

def validate_virtual_keys() -> bool:
    """Validate that all virtual keys are configured correctly"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    issues = []
    
    # Check each virtual key
    for name, key in PORTKEY_VIRTUAL_KEYS.items():
        if not key or key == "None":
            issues.append(f"{name} virtual key not configured")
        elif key not in PROVIDER_CONFIGS:
            issues.append(f"{name} key '{key}' not in provider configs")
    
    # Check for duplicates (would break parallelism)
    key_values = [v for v in PORTKEY_VIRTUAL_KEYS.values() if v]
    if len(key_values) != len(set(key_values)):
        issues.append("DUPLICATE virtual keys detected - this breaks parallelism!")
    
    if issues:
        for issue in issues:
            logger.error(f"❌ {issue}")
        return False
    
    logger.info(f"✅ All {len(PORTKEY_VIRTUAL_KEYS)} virtual keys validated")
    logger.info(f"✅ Total parallel capacity: {calculate_swarm_capacity(list(PORTKEY_VIRTUAL_KEYS.values()))}")
    
    return True


# =============================================================================
# QUICK ACCESS FUNCTIONS
# =============================================================================

def get_virtual_key(provider: str) -> str:
    """Get virtual key for a specific provider"""
    return PORTKEY_VIRTUAL_KEYS.get(provider.upper())


def get_all_virtual_keys() -> Dict[str, str]:
    """Get all configured virtual keys"""
    return PORTKEY_VIRTUAL_KEYS.copy()


def get_provider_info(virtual_key: str) -> Optional[Dict[str, Any]]:
    """Get provider configuration for a virtual key"""
    return PROVIDER_CONFIGS.get(virtual_key)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PORTKEY VIRTUAL KEYS CONFIGURATION")
    print("=" * 70)
    
    # Show all virtual keys
    print("\n📋 Configured Virtual Keys:")
    for name, key in PORTKEY_VIRTUAL_KEYS.items():
        if key in PROVIDER_CONFIGS:
            config = PROVIDER_CONFIGS[key]
            print(f"   {name:12} → {key:20} → {config['provider']:10} ({config['tpm_limit']:,} TPM)")
        else:
            print(f"   {name:12} → {key:20}")
    
    # Calculate total capacity
    capacity = calculate_swarm_capacity(list(PORTKEY_VIRTUAL_KEYS.values()))
    print(f"\n💪 Total Parallel Capacity:")
    print(f"   TPM: {capacity['total_tpm']:,}")
    print(f"   RPM: {capacity['total_rpm']:,}")
    print(f"   Providers: {', '.join(capacity['providers'])}")
    
    # Show optimal swarm configs
    print(f"\n🎯 Optimal Swarm Configurations:")
    for swarm_type, mapping in OPTIMAL_AGENT_MAPPING.items():
        swarm_capacity = calculate_swarm_capacity(list(mapping.values()))
        print(f"\n   {swarm_type}:")
        print(f"      Agents: {len(mapping)}")
        print(f"      TPM: {swarm_capacity['total_tpm']:,}")
        print(f"      Providers: {', '.join(swarm_capacity['providers'])}")
    
    # Validate
    print(f"\n✅ Validation:")
    validate_virtual_keys()