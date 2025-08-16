"""
SOPHIA Intel Shared Secret Manager
Centralized secret management for all MCP services
Integrates with Kubernetes secrets and environment variables
"""

import os
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecretConfig:
    """Configuration for a secret"""
    name: str
    env_var: str
    required: bool = True
    description: str = ""
    service: str = "all"

class SecretManager:
    """Centralized secret management for SOPHIA Intel MCP services"""
    
    # Define all secrets used across MCP services
    SECRET_CONFIGS = [
        # AI & LLM Services
        SecretConfig("openai_api_key", "OPENAI_API_KEY", True, "OpenAI API key for embeddings", "embedding"),
        SecretConfig("openrouter_api_key", "OPENROUTER_API_KEY", True, "OpenRouter API key for LLM inference", "all"),
        SecretConfig("elevenlabs_api_key", "ELEVENLABS_API_KEY", False, "ElevenLabs API key for voice synthesis", "voice"),
        
        # Vector Databases
        SecretConfig("qdrant_api_key", "QDRANT_API_KEY", False, "Qdrant API key for vector operations", "embedding"),
        SecretConfig("qdrant_url", "QDRANT_URL", False, "Qdrant cluster URL", "embedding"),
        SecretConfig("weaviate_admin_api_key", "WEAVIATE_ADMIN_API_KEY", True, "Weaviate admin API key", "embedding"),
        SecretConfig("weaviate_url", "WEAVIATE_URL", False, "Weaviate cluster URL", "embedding"),
        
        # Data & Research Services
        SecretConfig("brightdata_api_key", "BRIGHTDATA_API_KEY", True, "BrightData API key for web scraping", "research"),
        SecretConfig("neon_api_key", "NEON_API_KEY", True, "Neon PostgreSQL API key", "all"),
        SecretConfig("notion_api_key", "NOTION_API_KEY", True, "Notion API key for governance", "notion"),
        
        # Infrastructure & Cloud
        SecretConfig("lambda_cloud_api_key", "LAMBDA_CLOUD_API_KEY", False, "Lambda Labs API key", "telemetry"),
        SecretConfig("dnsimple_api_key", "DNSIMPLE_API_KEY", False, "DNSimple API key for DNS", "telemetry"),
        
        # Monitoring & Alerts
        SecretConfig("slack_webhook_url", "SLACK_WEBHOOK_URL", False, "Slack webhook for alerts", "telemetry"),
        
        # GitHub Integration
        SecretConfig("github_pat", "GITHUB_PAT", False, "GitHub Personal Access Token", "all"),
        
        # Database Configuration
        SecretConfig("notion_canonical_principles_db", "NOTION_CANONICAL_PRINCIPLES_DB", False, "Notion canonical principles database ID", "notion"),
        SecretConfig("notion_knowledge_base_db", "NOTION_KNOWLEDGE_BASE_DB", False, "Notion knowledge base database ID", "notion"),
    ]
    
    def __init__(self, service_name: str = "all"):
        """Initialize secret manager for specific service"""
        self.service_name = service_name
        self.secrets = {}
        self.missing_secrets = []
        self.load_secrets()
        
        logger.info(f"Secret manager initialized for service: {service_name}")
    
    def load_secrets(self):
        """Load secrets from environment variables"""
        for config in self.SECRET_CONFIGS:
            # Check if this secret applies to current service
            if config.service != "all" and config.service != self.service_name:
                continue
            
            value = os.getenv(config.env_var)
            
            if value:
                self.secrets[config.name] = value
                logger.debug(f"Loaded secret: {config.name}")
            else:
                if config.required:
                    self.missing_secrets.append(config)
                    logger.warning(f"Missing required secret: {config.name} ({config.env_var})")
                else:
                    logger.info(f"Optional secret not configured: {config.name}")
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret value by name"""
        return self.secrets.get(secret_name)
    
    def get_required_secret(self, secret_name: str) -> str:
        """Get a required secret, raise exception if missing"""
        value = self.secrets.get(secret_name)
        if value is None:
            raise ValueError(f"Required secret '{secret_name}' is not configured")
        return value
    
    def has_secret(self, secret_name: str) -> bool:
        """Check if a secret is available"""
        return secret_name in self.secrets
    
    def get_all_secrets(self) -> Dict[str, str]:
        """Get all loaded secrets (for debugging - be careful with logging)"""
        return self.secrets.copy()
    
    def get_secret_status(self) -> Dict:
        """Get status of all secrets for this service"""
        status = {
            "service": self.service_name,
            "loaded_secrets": [],
            "missing_required": [],
            "missing_optional": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for config in self.SECRET_CONFIGS:
            if config.service != "all" and config.service != self.service_name:
                continue
            
            if config.name in self.secrets:
                status["loaded_secrets"].append({
                    "name": config.name,
                    "description": config.description,
                    "required": config.required
                })
            else:
                if config.required:
                    status["missing_required"].append({
                        "name": config.name,
                        "env_var": config.env_var,
                        "description": config.description
                    })
                else:
                    status["missing_optional"].append({
                        "name": config.name,
                        "env_var": config.env_var,
                        "description": config.description
                    })
        
        return status
    
    def validate_service_secrets(self) -> Dict:
        """Validate that all required secrets for this service are available"""
        validation = {
            "service": self.service_name,
            "valid": len(self.missing_secrets) == 0,
            "missing_count": len(self.missing_secrets),
            "loaded_count": len(self.secrets),
            "missing_secrets": [
                {
                    "name": config.name,
                    "env_var": config.env_var,
                    "description": config.description
                }
                for config in self.missing_secrets
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not validation["valid"]:
            logger.error(f"Service {self.service_name} missing {len(self.missing_secrets)} required secrets")
        
        return validation
    
    @classmethod
    def get_all_secret_configs(cls) -> List[SecretConfig]:
        """Get all secret configurations"""
        return cls.SECRET_CONFIGS.copy()
    
    @classmethod
    def get_service_secrets(cls, service_name: str) -> List[SecretConfig]:
        """Get secret configurations for a specific service"""
        return [
            config for config in cls.SECRET_CONFIGS
            if config.service == "all" or config.service == service_name
        ]

# Convenience functions for common use cases
def get_secret_manager(service_name: str) -> SecretManager:
    """Get a secret manager instance for a service"""
    return SecretManager(service_name)

def validate_all_services() -> Dict:
    """Validate secrets for all services"""
    services = ["embedding", "research", "notion", "telemetry", "voice"]
    results = {}
    
    for service in services:
        manager = SecretManager(service)
        results[service] = manager.validate_service_secrets()
    
    # Overall validation
    all_valid = all(result["valid"] for result in results.values())
    
    return {
        "overall_valid": all_valid,
        "services": results,
        "timestamp": datetime.utcnow().isoformat()
    }

def get_global_secret_status() -> Dict:
    """Get status of all secrets across all services"""
    all_configs = SecretManager.get_all_secret_configs()
    
    status = {
        "total_secrets": len(all_configs),
        "loaded_secrets": [],
        "missing_secrets": [],
        "services": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check each secret
    for config in all_configs:
        value = os.getenv(config.env_var)
        
        secret_info = {
            "name": config.name,
            "env_var": config.env_var,
            "service": config.service,
            "required": config.required,
            "description": config.description
        }
        
        if value:
            status["loaded_secrets"].append(secret_info)
        else:
            status["missing_secrets"].append(secret_info)
    
    # Get per-service status
    services = ["embedding", "research", "notion", "telemetry", "voice"]
    for service in services:
        manager = SecretManager(service)
        status["services"][service] = manager.get_secret_status()
    
    return status

