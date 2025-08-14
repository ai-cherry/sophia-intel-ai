"""
Secrets management for Sophia AI platform using Pulumi ESC and GitHub Secrets
"""

import pulumi
from pulumi import Config, Output
import os
from typing import Dict, Any, Optional

class SecretsManager:
    """
    Manages secrets integration between GitHub Organization Secrets and Pulumi ESC
    """
    
    def __init__(self):
        self.config = Config()
        self._secrets_cache = {}
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Output[str]:
        """
        Get a secret from the environment with fallback to config
        Secrets should be provided via GitHub Actions -> Pulumi ESC -> Environment
        """
        # First try environment variable (populated by Pulumi ESC)
        env_value = os.environ.get(key)
        if env_value:
            return Output.secret(env_value)
        
        # Fallback to Pulumi config
        config_value = self.config.get_secret(key)
        if config_value:
            return config_value
        
        # Fallback to default
        if default is not None:
            return Output.secret(default)
        
        raise Exception(f"Secret '{key}' not found in environment or config")
    
    def get_all_secrets(self) -> Dict[str, Output[str]]:
        """
        Get all required secrets for the Sophia AI platform
        """
        required_secrets = {
            # Core infrastructure
            'LAMBDA_CLOUD_API_KEY': None,
            'DNSIMPLE_API_KEY': None,
            'DNSIMPLE_ACCOUNT': None,
            
            # Data services
            'QDRANT_API_KEY': None,
            'REDIS_URL': None,
            'DATABASE_URL': None,
            'ESTUARY_ACCESS_TOKEN': None,
            
            # LLM providers
            'OPENROUTER_API_KEY': None,
            'PORTKEY_API_KEY': None,
            'PORTKEY_CONFIG': None,
            
            # Additional AI services
            'TOGETHER_AI_API_KEY': None,
            'HUGGINGFACE_API_TOKEN': None,
            'TAVILY_API_KEY': None,
            'ARIZE_API_KEY': None,
            'ARIZE_SPACE_ID': None,
            
            # Development and deployment
            'GITHUB_PAT': None,
            'DOCKER_USER_NAME': None,
            'DOCKER_PERSONAL_ACCESS_TOKEN': None,
            
            # Workflow automation
            'N8N_ENCRYPTION_KEY': None,
            'N8N_USER_MANAGEMENT_JWT_SECRET': None,
        }
        
        secrets = {}
        for key, default in required_secrets.items():
            try:
                secrets[key] = self.get_secret(key, default)
            except Exception as e:
                print(f"Warning: Could not load secret '{key}': {e}")
                if default is not None:
                    secrets[key] = Output.secret(default)
        
        return secrets
    
    def create_secret_outputs(self) -> Dict[str, Output[str]]:
        """
        Create Pulumi outputs for secrets that can be used by other resources
        """
        secrets = self.get_all_secrets()
        
        # Export secrets as stack outputs (they will be automatically marked as secret)
        for key, value in secrets.items():
            pulumi.export(f"secret_{key.lower()}", value)
        
        return secrets

def setup_secrets_management() -> SecretsManager:
    """
    Set up secrets management for the infrastructure
    """
    secrets_manager = SecretsManager()
    
    # Load and export all secrets
    secrets = secrets_manager.create_secret_outputs()
    
    # Create a summary of loaded secrets (without values)
    loaded_secrets = []
    for key in secrets.keys():
        if os.environ.get(key) or secrets_manager.config.get_secret(key):
            loaded_secrets.append(key)
    
    pulumi.export("secrets_loaded", loaded_secrets)
    pulumi.export("secrets_count", len(loaded_secrets))
    
    return secrets_manager

# Global secrets manager instance - initialize when needed
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager

# For backward compatibility
secrets_manager = get_secrets_manager()

