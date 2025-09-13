"""
Model Manager - Central control system for all AI models
=========================================================
Reads from user_models_config.yaml and provides unified interface
for LiteLLM Squad, Builder App, and Sophia Intel App
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Load user configuration
CONFIG_PATH = Path(__file__).parent / "user_models_config.yaml"

class ModelManager:
    """
    Central model management system that YOU control
    All configuration comes from user_models_config.yaml
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with user configuration"""
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.virtual_keys = self.config.get("virtual_keys", {})
        
        # Load user preferences FIRST (before processing models)
        prefs = self.config.get("preferences", {})
        self.prioritize_quality = prefs.get("prioritize_quality", True)
        self.prioritize_performance = prefs.get("prioritize_performance", True)
        self.allow_experimental = prefs.get("allow_experimental", False)
        self.max_latency = prefs.get("max_latency_ms", 1000)
        self.min_context = prefs.get("min_context_tokens", 128000)
        
        # Now process models and policies (after preferences are loaded)
        self.models = self._process_models()
        self.policies = self._process_policies()
        
        logger.info(f"ModelManager initialized with {len(self.models)} active models")
    
    def _load_config(self) -> Dict:
        """Load user configuration from YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create user_models_config.yaml to control model routing"
            )
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _process_models(self) -> Dict[str, Dict]:
        """Process and filter models based on user settings"""
        models = {}
        
        for model_id, model_config in self.config.get("models", {}).items():
            # Skip disabled models
            if not model_config.get("enabled", False):
                continue
            
            # Skip experimental if not allowed
            if not self.allow_experimental and model_config.get("priority", 1) >= 10:
                continue
            
            # Get virtual key for provider
            provider = model_config.get("provider", "")
            virtual_key = self.virtual_keys.get(provider, f"{provider}-vk-default")
            
            models[model_id] = {
                "id": model_id,
                "provider": provider,
                "display_name": model_config.get("display_name", model_id),
                "context": model_config.get("context", 128000),
                "priority": model_config.get("priority", 5),
                "virtual_key": virtual_key,
                "notes": model_config.get("my_notes", ""),
                "enabled": True
            }
        
        return models
    
    def _process_policies(self) -> Dict[str, Dict]:
        """Process routing policies from configuration"""
        policies = {}
        
        for policy_id, policy_config in self.config.get("routing_policies", {}).items():
            policies[policy_id] = {
                "name": policy_config.get("name", policy_id),
                "description": policy_config.get("description", ""),
                "models": policy_config.get("models", []),
                "fallback": policy_config.get("fallback", [])
            }
        
        return policies
    
    # ========================================================================
    # PUBLIC API - Used by all systems
    # ========================================================================
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get a specific model configuration"""
        return self.models.get(model_id)
    
    def get_all_models(self) -> List[Dict]:
        """Get all enabled models sorted by priority"""
        models = list(self.models.values())
        models.sort(key=lambda x: x["priority"])
        return models
    
    def get_models_by_priority(self, max_priority: int = 5) -> List[Dict]:
        """Get models up to a certain priority level"""
        models = [m for m in self.models.values() if m["priority"] <= max_priority]
        models.sort(key=lambda x: x["priority"])
        return models
    
    def select_model_for_task(
        self,
        task: str,
        policy: Optional[str] = None,
        system: Optional[str] = None
    ) -> Dict:
        """
        Select the best model for a task
        
        Args:
            task: The task description
            policy: Specific policy to use (optional)
            system: The calling system (litellm_squad, builder_app, sophia_intel)
        
        Returns:
            Model configuration dict
        """
        # Check for system-specific overrides
        if system:
            overrides = self.config.get("system_overrides", {}).get(system, {})
            if not policy:
                policy = overrides.get("default_policy", "my_default")
        
        # Apply task routing rules
        for rule in self.config.get("task_rules", []):
            condition = rule.get("condition", "")
            
            # Simple keyword matching for now
            keywords = condition.replace(" in task", "").split(" or ")
            if any(keyword in task.lower() for keyword in keywords):
                if "use_policy" in rule:
                    policy = rule["use_policy"]
                    break
                elif "use_models" in rule:
                    # Return first available model from the list
                    for model_id in rule["use_models"]:
                        if model_id in self.models:
                            return self.models[model_id]
        
        # Use specified or default policy
        if not policy:
            policy = "my_default"
        
        # Get models from policy
        if policy in self.policies:
            policy_config = self.policies[policy]
            
            # Try primary models first
            for model_id in policy_config["models"]:
                if model_id in self.models:
                    return self.models[model_id]
            
            # Try fallback models
            for model_id in policy_config.get("fallback", []):
                if model_id in self.models:
                    return self.models[model_id]
        
        # Final fallback: return highest priority model
        if self.models:
            return min(self.models.values(), key=lambda x: x["priority"])
        
        # Emergency fallback
        return {
            "id": "gpt-4.1-mini",
            "provider": "openai",
            "display_name": "GPT-4.1 Mini (Fallback)",
            "virtual_key": self.virtual_keys.get("openai", "openai-vk-190a60")
        }
    
    def get_policy(self, policy_name: str) -> Dict:
        """Get a specific routing policy"""
        return self.policies.get(policy_name, self.policies.get("my_default", {}))
    
    def get_models_for_policy(self, policy_name: str) -> List[Dict]:
        """Get all models for a specific policy"""
        policy = self.get_policy(policy_name)
        models = []
        
        # Add primary models
        for model_id in policy.get("models", []):
            if model_id in self.models:
                models.append(self.models[model_id])
        
        # Add fallback models
        for model_id in policy.get("fallback", []):
            if model_id in self.models:
                model = self.models[model_id].copy()
                model["is_fallback"] = True
                models.append(model)
        
        return models
    
    # ========================================================================
    # SYSTEM-SPECIFIC METHODS
    # ========================================================================
    
    def get_litellm_config(self) -> Dict:
        """Get configuration for LiteLLM Squad"""
        overrides = self.config.get("system_overrides", {}).get("litellm_squad", {})
        
        return {
            "models": self.get_all_models() if overrides.get("allow_all_models", True) else self.get_models_by_priority(3),
            "default_policy": overrides.get("default_policy", "balanced"),
            "parallel_requests": overrides.get("parallel_requests", 5),
            "policies": self.policies,
            "virtual_keys": self.virtual_keys
        }
    
    def get_builder_config(self) -> Dict:
        """Get configuration for Builder App"""
        overrides = self.config.get("system_overrides", {}).get("builder_app", {})
        
        # Get models for each agent type
        planner_models = self.get_models_for_policy(
            overrides.get("planner_policy", "quality_max")
        )
        coder_models = self.get_models_for_policy(
            overrides.get("coder_policy", "coding")
        )
        reviewer_models = self.get_models_for_policy(
            overrides.get("reviewer_policy", "quality_max")
        )
        
        return {
            "planner_models": planner_models,
            "coder_models": coder_models,
            "reviewer_models": reviewer_models,
            "allow_fallbacks": overrides.get("allow_fallbacks", True),
            "virtual_keys": self.virtual_keys
        }
    
    def get_sophia_config(self) -> Dict:
        """Get configuration for Sophia Intel App"""
        overrides = self.config.get("system_overrides", {}).get("sophia_intel", {})
        
        return {
            "default_policy": overrides.get("default_policy", "my_default"),
            "chat_policy": overrides.get("chat_policy", "balanced"),
            "reasoning_policy": overrides.get("reasoning_policy", "quality_max"),
            "creative_policy": overrides.get("creative_policy", "creative"),
            "models": self.get_all_models(),
            "policies": self.policies,
            "virtual_keys": self.virtual_keys
        }
    
    # ========================================================================
    # MONITORING & ANALYTICS
    # ========================================================================
    
    def get_monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self.config.get("monitoring", {
            "track_costs": True,
            "cost_alert_threshold": 25.00,
            "track_performance": True,
            "log_slow_requests": True,
            "log_failed_requests": True,
            "daily_budget": 100.00
        })
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the configuration file
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if any models are enabled
        if not self.models:
            issues.append("No models are enabled in configuration")
        
        # Check if virtual keys are configured
        if not self.virtual_keys:
            issues.append("No virtual keys configured")
        
        # Check if at least one policy exists
        if not self.policies:
            issues.append("No routing policies defined")
        
        # Check for missing virtual keys
        for model in self.models.values():
            provider = model["provider"]
            if provider not in self.virtual_keys:
                issues.append(f"Missing virtual key for provider: {provider}")
        
        # Check Portkey API key
        portkey_config = self.config.get("portkey", {})
        if not portkey_config.get("api_key"):
            issues.append("Portkey API key not configured")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self.models = self._process_models()
        self.policies = self._process_policies()
        self.virtual_keys = self.config.get("virtual_keys", {})
        logger.info("Configuration reloaded")
    
    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*60)
        print("MODEL MANAGER CONFIGURATION SUMMARY")
        print("="*60)
        
        print(f"\nActive Models: {len(self.models)}")
        for model in self.get_models_by_priority(3):
            print(f"  • {model['display_name']} (Priority {model['priority']})")
        
        print(f"\nRouting Policies: {len(self.policies)}")
        for policy_id, policy in self.policies.items():
            print(f"  • {policy['name']}: {len(policy['models'])} models")
        
        print(f"\nPreferences:")
        print(f"  • Quality First: {self.prioritize_quality}")
        print(f"  • Performance First: {self.prioritize_performance}")
        print(f"  • Allow Experimental: {self.allow_experimental}")
        
        monitoring = self.get_monitoring_config()
        print(f"\nMonitoring:")
        print(f"  • Cost Tracking: {monitoring.get('track_costs', False)}")
        print(f"  • Daily Budget: ${monitoring.get('daily_budget', 0)}")
        print(f"  • Alert Threshold: ${monitoring.get('cost_alert_threshold', 0)}")
        
        is_valid, issues = self.validate_config()
        if is_valid:
            print(f"\n✅ Configuration is valid")
        else:
            print(f"\n⚠️  Configuration has issues:")
            for issue in issues:
                print(f"  • {issue}")
        
        print("="*60 + "\n")

# ========================================================================
# SINGLETON INSTANCE
# ========================================================================

_manager_instance = None

def get_model_manager() -> ModelManager:
    """Get the singleton ModelManager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModelManager()
    return _manager_instance

def reload_manager():
    """Force reload of configuration"""
    global _manager_instance
    if _manager_instance:
        _manager_instance.reload_config()
    else:
        _manager_instance = ModelManager()
    return _manager_instance

# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def select_model(task: str, policy: Optional[str] = None, system: Optional[str] = None) -> Dict:
    """Quick model selection"""
    manager = get_model_manager()
    return manager.select_model_for_task(task, policy, system)

def get_virtual_key(provider: str) -> str:
    """Get virtual key for a provider"""
    manager = get_model_manager()
    return manager.virtual_keys.get(provider, f"{provider}-vk-default")

def get_system_config(system: str) -> Dict:
    """Get configuration for a specific system"""
    manager = get_model_manager()
    
    if system == "litellm_squad":
        return manager.get_litellm_config()
    elif system == "builder_app":
        return manager.get_builder_config()
    elif system == "sophia_intel":
        return manager.get_sophia_config()
    else:
        raise ValueError(f"Unknown system: {system}")

# ========================================================================
# CLI INTERFACE
# ========================================================================

if __name__ == "__main__":
    import sys
    
    manager = get_model_manager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            is_valid, issues = manager.validate_config()
            if is_valid:
                print("✅ Configuration is valid")
            else:
                print("❌ Configuration has issues:")
                for issue in issues:
                    print(f"  • {issue}")
            sys.exit(0 if is_valid else 1)
        
        elif command == "reload":
            manager.reload_config()
            print("✅ Configuration reloaded")
        
        elif command == "models":
            print("\nActive Models:")
            for model in manager.get_all_models():
                print(f"  • {model['display_name']} ({model['provider']})")
        
        elif command == "policies":
            print("\nRouting Policies:")
            for policy_id, policy in manager.policies.items():
                print(f"  • {policy['name']}: {', '.join(policy['models'][:3])}")
        
        elif command == "test":
            # Test model selection
            test_tasks = [
                "Write a Python function",
                "Debug this code quickly",
                "Create a creative story",
                "Research quantum computing"
            ]
            
            print("\nModel Selection Tests:")
            for task in test_tasks:
                model = manager.select_model_for_task(task)
                print(f"  Task: '{task}'")
                print(f"  Selected: {model['display_name']}\n")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, reload, models, policies, test")
    
    else:
        # Default action: print summary
        manager.print_summary()