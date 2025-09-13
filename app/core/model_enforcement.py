#!/usr/bin/env python3
"""
Sophia Intel AI - Model Enforcement System
Prevents AI agents from using outdated or deprecated models
Enforces approved model lists and routing policies
"""

import os
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"
    TESTING = "testing"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: str
    status: ModelStatus
    tier: str  # premium, standard, basic
    cost_per_1k_tokens: float
    max_tokens: int
    context_window: int
    approval_date: Optional[str] = None
    deprecation_date: Optional[str] = None
    replacement_model: Optional[str] = None
    notes: Optional[str] = None

class ModelEnforcement:
    """Central model enforcement and routing system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/Users/lynnmusil/sophia-intel-ai/app/core/approved_models.json"
        self.approved_models: Dict[str, ModelConfig] = {}
        self.blocked_models: Set[str] = set()
        self.deprecated_models: Dict[str, str] = {}  # deprecated_model -> replacement
        self.load_model_config()
        
    def load_model_config(self):
        """Load approved model configurations"""
        # Default approved models - LATEST AND MOST CAPABLE
        default_config = {
            # OpenAI - Latest models only
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                provider="openai", 
                status=ModelStatus.APPROVED,
                tier="premium",
                cost_per_1k_tokens=0.015,
                max_tokens=4096,
                context_window=128000,
                approval_date="2024-12-01",
                notes="Latest GPT-4 Omni model - preferred for complex tasks"
            ),
            "gpt-4o-mini": ModelConfig(
                name="gpt-4o-mini",
                provider="openai",
                status=ModelStatus.APPROVED,
                tier="standard",
                cost_per_1k_tokens=0.00015,
                max_tokens=16384,
                context_window=128000,
                approval_date="2024-12-01",
                notes="Cost-effective GPT-4 variant"
            ),
            
            # Anthropic - Latest Claude models only
            "claude-3-5-sonnet-20241022": ModelConfig(
                name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                status=ModelStatus.APPROVED,
                tier="premium",
                cost_per_1k_tokens=0.015,
                max_tokens=8192,
                context_window=200000,
                approval_date="2024-12-01",
                notes="Latest Claude 3.5 Sonnet - excellent for code and analysis"
            ),
            "claude-3-5-haiku-20241022": ModelConfig(
                name="claude-3-5-haiku-20241022",
                provider="anthropic",
                status=ModelStatus.APPROVED,
                tier="standard",
                cost_per_1k_tokens=0.0025,
                max_tokens=8192,
                context_window=200000,
                approval_date="2024-12-01",
                notes="Fast and efficient Claude variant"
            ),
            
            # Google - Latest Gemini models
            "gemini-2.0-flash-exp": ModelConfig(
                name="gemini-2.0-flash-exp",
                provider="google",
                status=ModelStatus.APPROVED,
                tier="premium",
                cost_per_1k_tokens=0.010,
                max_tokens=8192,
                context_window=1000000,
                approval_date="2024-12-01",
                notes="Latest Gemini 2.0 experimental - huge context window"
            ),
            "gemini-1.5-pro": ModelConfig(
                name="gemini-1.5-pro",
                provider="google",
                status=ModelStatus.APPROVED,
                tier="premium",
                cost_per_1k_tokens=0.0075,
                max_tokens=8192,
                context_window=2000000,
                approval_date="2024-12-01",
                notes="Stable Gemini Pro with massive context"
            ),
            
            # Specialized models
            "deepseek-coder-v2": ModelConfig(
                name="deepseek-coder-v2",
                provider="deepseek",
                status=ModelStatus.APPROVED,
                tier="standard",
                cost_per_1k_tokens=0.0014,
                max_tokens=32000,
                context_window=128000,
                approval_date="2024-12-01",
                notes="Excellent for coding tasks"
            ),
            "grok-beta": ModelConfig(
                name="grok-beta",
                provider="xai",
                status=ModelStatus.APPROVED,
                tier="premium",
                cost_per_1k_tokens=0.005,
                max_tokens=32768,
                context_window=131072,
                approval_date="2024-12-01",
                notes="Latest Grok model from xAI"
            )
        }
        
        # BLOCKED MODELS - Prevent usage of outdated models
        blocked_models = {
            # Old GPT models
            "gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k",
            "text-davinci-003", "text-curie-001", "text-babbage-001",
            
            # Old GPT-4 models  
            "gpt-4", "gpt-4-0613", "gpt-4-32k", "gpt-4-turbo", "gpt-4-turbo-preview",
            
            # Old Claude models
            "claude-instant-1", "claude-instant-1.2", "claude-2", "claude-2.0", "claude-2.1",
            "claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229",
            
            # Old Gemini models
            "gemini-pro", "gemini-1.0-pro", "gemini-1.5-flash",
            
            # Other deprecated models
            "text-embedding-ada-002", "davinci", "curie", "babbage", "ada"
        }
        
        # Add blocked models to config
        for model_name in blocked_models:
            default_config[model_name] = ModelConfig(
                name=model_name,
                provider="deprecated",
                status=ModelStatus.BLOCKED,
                tier="blocked",
                cost_per_1k_tokens=0.0,
                max_tokens=0,
                context_window=0,
                deprecation_date="2024-12-01",
                notes="BLOCKED: Outdated model - use latest alternatives"
            )
        
        self.approved_models = default_config
        
        # Save default config if file doesn't exist
        config_path = Path(self.config_path)
        if not config_path.exists():
            self.save_model_config()
            
    def save_model_config(self):
        """Save model configuration to file"""
        config_data = {}
        for name, model in self.approved_models.items():
            config_data[name] = {
                "name": model.name,
                "provider": model.provider,
                "status": model.status.value,
                "tier": model.tier,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "max_tokens": model.max_tokens,
                "context_window": model.context_window,
                "approval_date": model.approval_date,
                "deprecation_date": model.deprecation_date,
                "replacement_model": model.replacement_model,
                "notes": model.notes
            }
        
        config_path = Path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Saved model configuration to {config_path}")
    
    def is_model_approved(self, model_name: str) -> bool:
        """Check if a model is approved for use"""
        if model_name not in self.approved_models:
            logger.warning(f"Unknown model requested: {model_name}")
            return False
            
        model = self.approved_models[model_name]
        
        if model.status == ModelStatus.BLOCKED:
            logger.error(f"BLOCKED model requested: {model_name} - {model.notes}")
            return False
        elif model.status == ModelStatus.DEPRECATED:
            logger.warning(f"DEPRECATED model requested: {model_name}")
            if model.replacement_model:
                logger.info(f"Suggested replacement: {model.replacement_model}")
            return False
        elif model.status == ModelStatus.APPROVED:
            return True
        elif model.status == ModelStatus.TESTING:
            logger.info(f"Testing model requested: {model_name}")
            return True
            
        return False
    
    def get_approved_models(self, provider: Optional[str] = None, tier: Optional[str] = None) -> List[ModelConfig]:
        """Get list of approved models, optionally filtered by provider or tier"""
        models = []
        for model in self.approved_models.values():
            if model.status != ModelStatus.APPROVED:
                continue
            if provider and model.provider != provider:
                continue  
            if tier and model.tier != tier:
                continue
            models.append(model)
        
        return sorted(models, key=lambda x: x.cost_per_1k_tokens)
    
    def get_replacement_model(self, deprecated_model: str) -> Optional[str]:
        """Get replacement for a deprecated model"""
        if deprecated_model in self.approved_models:
            model = self.approved_models[deprecated_model]
            return model.replacement_model
        return None
    
    def enforce_model_choice(self, requested_model: str, fallback: bool = True) -> str:
        """Enforce model choice, returning approved model or raising error"""
        if self.is_model_approved(requested_model):
            return requested_model
            
        if requested_model in self.approved_models:
            model = self.approved_models[requested_model]
            
            # If blocked or deprecated, try to find replacement
            if model.status in [ModelStatus.BLOCKED, ModelStatus.DEPRECATED]:
                if model.replacement_model and fallback:
                    logger.info(f"Replacing {requested_model} with {model.replacement_model}")
                    return model.replacement_model
                    
        if fallback:
            # Default fallback logic
            fallback_models = {
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-haiku-20241022", 
                "google": "gemini-1.5-pro",
                "xai": "grok-beta",
                "deepseek": "deepseek-coder-v2"
            }
            
            # Try to infer provider from model name
            for provider, fallback_model in fallback_models.items():
                if provider in requested_model.lower():
                    logger.info(f"Using fallback model {fallback_model} for {requested_model}")
                    return fallback_model
                    
            # Ultimate fallback
            logger.info(f"Using ultimate fallback gpt-4o-mini for {requested_model}")
            return "gpt-4o-mini"
        
        raise ValueError(f"Model {requested_model} is not approved and fallback disabled")
    
    def validate_api_request(self, model_name: str, raise_on_invalid: bool = True) -> bool:
        """Validate API request before sending to provider"""
        if not self.is_model_approved(model_name):
            error_msg = f"API request blocked: Model '{model_name}' is not approved"
            logger.error(error_msg)
            
            if raise_on_invalid:
                raise ValueError(error_msg)
            return False
            
        return True
    
    def get_model_stats(self) -> Dict[str, int]:
        """Get statistics about model usage"""
        stats = {
            "approved": 0,
            "blocked": 0,
            "deprecated": 0,
            "testing": 0
        }
        
        for model in self.approved_models.values():
            stats[model.status.value] += 1
            
        return stats

# Global model enforcement instance
model_enforcer = ModelEnforcement()

def enforce_model(model_name: str, fallback: bool = True) -> str:
    """Global function to enforce model choice"""
    return model_enforcer.enforce_model_choice(model_name, fallback)

def validate_model(model_name: str, raise_on_invalid: bool = True) -> bool:
    """Global function to validate model"""
    return model_enforcer.validate_api_request(model_name, raise_on_invalid)

if __name__ == "__main__":
    # Test the enforcement system
    enforcer = ModelEnforcement()
    
    print("🔒 Model Enforcement System Test")
    print("=" * 50)
    
    # Test approved models
    approved = enforcer.get_approved_models()
    print(f"✅ Approved models: {len(approved)}")
    for model in approved[:5]:  # Show first 5
        print(f"  - {model.name} ({model.provider}) - ${model.cost_per_1k_tokens:.4f}/1k tokens")
    
    # Test blocked models
    test_models = ["gpt-3.5-turbo", "gpt-4o", "claude-2", "claude-3-5-sonnet-20241022"]
    
    for model in test_models:
        try:
            result = enforcer.enforce_model_choice(model)
            print(f"✅ {model} -> {result}")
        except ValueError as e:
            print(f"❌ {model} -> {e}")
    
    # Print stats
    stats = enforcer.get_model_stats()
    print(f"\n📊 Model Statistics:")
    for status, count in stats.items():
        print(f"  {status}: {count}")