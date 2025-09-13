"""
Integration Adapter for Central Model Configuration
====================================================
This module connects all three systems to the central model manager
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.model_manager import get_model_manager, get_system_config

class UnifiedModelRouter:
    """
    Unified router that all systems use to get models
    Single point of integration with user_models_config.yaml
    """
    
    def __init__(self):
        self.manager = get_model_manager()
        self.config = self.manager.config
        
    # ========================================================================
    # BUILDER APP INTEGRATION
    # ========================================================================
    
    def get_builder_model(self, agent_type: str, task: str = "") -> Dict[str, str]:
        """
        Get model for Builder app agents
        
        Args:
            agent_type: 'planner', 'coder', or 'reviewer'
            task: Optional task description for better routing
            
        Returns:
            Dict with model_id, provider, virtual_key
        """
        config = get_system_config("builder_app")
        
        # Map agent types to model lists
        if agent_type == "planner":
            models = config["planner_models"]
        elif agent_type == "coder":
            models = config["coder_models"]
        elif agent_type == "reviewer":
            models = config["reviewer_models"]
        else:
            # Default to balanced policy
            return self.manager.select_model_for_task(task, policy="balanced", system="builder_app")
        
        # Return first available model
        if models:
            model = models[0]
            return {
                "model_id": model["id"],
                "provider": model["provider"],
                "virtual_key": model["virtual_key"],
                "display_name": model["display_name"]
            }
        
        # Fallback
        return self.get_default_model()
    
    def get_builder_routing_for_providers(self) -> Dict[str, Any]:
        """
        Get routing configuration for BuilderProvidersClient
        Replaces hardcoded model_policy dictionary
        """
        policies = {}
        
        # Convert user policies to provider format
        for policy_name, policy_config in self.manager.policies.items():
            models_list = []
            for model_id in policy_config["models"]:
                if model_id in self.manager.models:
                    model = self.manager.models[model_id]
                    models_list.append((model["provider"], model_id))
            
            policies[policy_name] = {
                "preferred": models_list,
                "characteristics": []  # Can be extended
            }
        
        return policies
    
    # ========================================================================
    # LITELLM SQUAD INTEGRATION
    # ========================================================================
    
    def get_litellm_models(self) -> List[Dict[str, Any]]:
        """
        Get all models for LiteLLM Squad
        Returns list of model configurations
        """
        config = get_system_config("litellm_squad")
        return config["models"]
    
    def get_litellm_router_config(self) -> Dict[str, Any]:
        """
        Get complete LiteLLM router configuration
        Replaces static YAML config
        """
        config = get_system_config("litellm_squad")
        
        # Format for LiteLLM
        model_list = []
        for model in config["models"]:
            model_list.append({
                "model_name": model["id"],
                "litellm_params": {
                    "model": f"{model['provider']}/{model['id']}",
                    "api_key": model["virtual_key"],
                    "api_base": "https://api.portkey.ai/v1",
                    "custom_llm_provider": "portkey"
                }
            })
        
        return {
            "model_list": model_list,
            "default_model": config["models"][0]["id"] if config["models"] else "gpt-4.1-mini",
            "routing_strategy": config.get("default_policy", "balanced"),
            "parallel_requests": config.get("parallel_requests", 5)
        }
    
    # ========================================================================
    # SOPHIA INTEL APP INTEGRATION
    # ========================================================================
    
    def get_sophia_model_for_task(self, task_type: str, task_description: str = "") -> Dict[str, str]:
        """
        Get model for Sophia Intel tasks
        
        Args:
            task_type: Type of task (chat, reasoning, creative, etc.)
            task_description: Optional task description
            
        Returns:
            Model configuration
        """
        config = get_system_config("sophia_intel")
        
        # Map task types to policies
        policy_map = {
            "chat": config.get("chat_policy", "balanced"),
            "reasoning": config.get("reasoning_policy", "quality_max"),
            "creative": config.get("creative_policy", "creative"),
            "code": "coding",
            "research": "research"
        }
        
        policy = policy_map.get(task_type, config.get("default_policy", "my_default"))
        
        model = self.manager.select_model_for_task(
            task_description or task_type,
            policy=policy,
            system="sophia_intel"
        )
        
        return {
            "model_id": model["id"],
            "provider": model["provider"],
            "virtual_key": model["virtual_key"],
            "display_name": model["display_name"],
            "context_window": model["context"]
        }
    
    def get_portkey_routing_config(self) -> Dict[str, Any]:
        """
        Get routing configuration for PortkeyManager
        Replaces hardcoded MODEL_CONFIGS
        """
        models_config = {}
        
        for model_id, model in self.manager.models.items():
            models_config[f"{model['provider']}/{model_id}"] = {
                "provider": model["provider"],
                "model": model_id,
                "virtual_key": model["virtual_key"],
                "max_tokens": 8192,  # Default
                "temperature": 0.2,   # Default
                "cost_per_1k_tokens": 0.01,  # Should be updated with real costs
                "supports_streaming": True,
                "context_window": model["context"]
            }
        
        return models_config
    
    # ========================================================================
    # COMMON UTILITIES
    # ========================================================================
    
    def get_default_model(self) -> Dict[str, str]:
        """Get the default model configuration"""
        models = self.manager.get_models_by_priority(1)
        if models:
            model = models[0]
            return {
                "model_id": model["id"],
                "provider": model["provider"],
                "virtual_key": model["virtual_key"],
                "display_name": model["display_name"]
            }
        
        # Emergency fallback
        return {
            "model_id": "gpt-4.1-mini",
            "provider": "openai",
            "virtual_key": "openai-vk-190a60",
            "display_name": "GPT-4.1 Mini (Fallback)"
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration for all systems"""
        return self.manager.get_monitoring_config()
    
    def reload(self):
        """Reload configuration from file"""
        self.manager.reload_config()
        print("✅ Configuration reloaded for all systems")

# ========================================================================
# SINGLETON INSTANCE
# ========================================================================

_router_instance = None

def get_unified_router() -> UnifiedModelRouter:
    """Get the singleton router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = UnifiedModelRouter()
    return _router_instance

# ========================================================================
# INTEGRATION HOOKS FOR EACH SYSTEM
# ========================================================================

def builder_get_model(agent_type: str, task: str = "") -> Dict[str, str]:
    """Builder App hook"""
    router = get_unified_router()
    return router.get_builder_model(agent_type, task)

def litellm_get_config() -> Dict[str, Any]:
    """LiteLLM Squad hook"""
    router = get_unified_router()
    return router.get_litellm_router_config()

def sophia_get_model(task_type: str, task: str = "") -> Dict[str, str]:
    """Sophia Intel hook"""
    router = get_unified_router()
    return router.get_sophia_model_for_task(task_type, task)

# ========================================================================
# VERIFICATION
# ========================================================================

if __name__ == "__main__":
    router = get_unified_router()
    
    print("="*70)
    print("UNIFIED MODEL ROUTER - INTEGRATION TEST")
    print("="*70)
    
    print("\n1️⃣ BUILDER APP:")
    print("  Planner:", router.get_builder_model("planner", "Create architecture")["display_name"])
    print("  Coder:", router.get_builder_model("coder", "Write code")["display_name"])
    print("  Reviewer:", router.get_builder_model("reviewer", "Review code")["display_name"])
    
    print("\n2️⃣ LITELLM SQUAD:")
    litellm_config = router.get_litellm_router_config()
    print(f"  Models available: {len(litellm_config['model_list'])}")
    print(f"  Default model: {litellm_config['default_model']}")
    print(f"  Routing strategy: {litellm_config['routing_strategy']}")
    
    print("\n3️⃣ SOPHIA INTEL:")
    print("  Chat:", router.get_sophia_model_for_task("chat", "Hello")["display_name"])
    print("  Reasoning:", router.get_sophia_model_for_task("reasoning", "Complex problem")["display_name"])
    print("  Creative:", router.get_sophia_model_for_task("creative", "Write story")["display_name"])
    
    print("\n📊 MONITORING:")
    monitoring = router.get_monitoring_config()
    print(f"  Daily Budget: ${monitoring['daily_budget']:,.2f}")
    print(f"  Alert Threshold: ${monitoring['cost_alert_threshold']:,.2f}")
    
    print("\n✅ All systems integrated with central configuration!")