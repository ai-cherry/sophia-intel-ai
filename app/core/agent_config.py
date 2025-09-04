"""
Centralized Configuration Management for Agents and Services

This module provides a unified configuration layer for all agents and microservices,
enabling environment-based overrides and reducing duplication across the codebase.
"""

import os
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator
from app.models.schemas import ModelFieldsModel


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ModelConfig(BaseModel):
    """Configuration for AI model settings"""
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4096, ge=1, le=128000)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    cost_limit_per_request: float = Field(1.0, ge=0.0)
    timeout_seconds: int = Field(120, ge=1)
    retry_attempts: int = Field(3, ge=0, le=10)
    enable_fallback: bool = True
    enable_emergency_fallback: bool = True


class AgentRoleConfig(ModelFieldsModel):
    """Role-specific agent configuration"""
    role_name: str
    system_prompt_template: Optional[str] = None
    model_settings: ModelConfig = Field(default_factory=ModelConfig)
    max_reasoning_steps: int = Field(10, ge=1, le=50)
    enable_reasoning: bool = True
    enable_memory: bool = True
    enable_knowledge: bool = True
    tools: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    
    @validator('model_settings', pre=True)
    def merge_model_settings(cls, v):
        if isinstance(v, dict):
            return ModelConfig(**v)
        return v


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = Field(60, ge=1)
    requests_per_hour: int = Field(1000, ge=1)
    requests_per_day: int = Field(10000, ge=1)
    burst_size: int = Field(10, ge=1)
    enable_rate_limiting: bool = True


class SecurityConfig(BaseModel):
    """Security configuration"""
    enable_api_key_auth: bool = True
    enable_jwt_auth: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_credentials: bool = True
    cors_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_headers: list[str] = Field(default_factory=lambda: ["*"])
    secrets_provider: str = "environment"  # environment, vault, aws_secrets
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    aws_region: Optional[str] = None


class ObservabilityConfig(BaseModel):
    """Observability and monitoring configuration"""
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_logging: bool = True
    tracing_sample_rate: float = Field(1.0, ge=0.0, le=1.0)
    metrics_export_interval: int = Field(60, ge=1)
    log_level: str = "INFO"
    jaeger_endpoint: Optional[str] = None
    prometheus_port: int = Field(9090, ge=1024, le=65535)
    log_format: str = "json"  # json, text


class ServiceConfig(BaseModel):
    """Microservice configuration"""
    service_name: str
    service_port: int = Field(8000, ge=1024, le=65535)
    service_host: str = "0.0.0.0"
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    enable_swagger: bool = True
    swagger_path: str = "/docs"
    workers: int = Field(4, ge=1)
    worker_class: str = "uvicorn.workers.UvicornWorker"


class AgentConfig(BaseModel):
    """Complete agent configuration"""
    environment: Environment
    service: ServiceConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    default_model: ModelConfig = Field(default_factory=ModelConfig)
    role_configs: dict[str, AgentRoleConfig] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


def get_role_defaults() -> dict[str, AgentRoleConfig]:
    """Get default configurations for each agent role"""
    return {
        "planner": AgentRoleConfig(
            role_name="planner",
            model_config=ModelConfig(temperature=0.2, cost_limit_per_request=0.75),
            max_reasoning_steps=15,
            tools=["create_timeline", "analyze_dependencies", "estimate_resources", "assess_risks"]
        ),
        "coder": AgentRoleConfig(
            role_name="coder",
            model_config=ModelConfig(temperature=0.3, cost_limit_per_request=0.60),
            max_reasoning_steps=12,
            tools=["code_search", "git_operations", "testing"]
        ),
        "critic": AgentRoleConfig(
            role_name="critic",
            model_config=ModelConfig(temperature=0.4, cost_limit_per_request=0.50),
            max_reasoning_steps=10,
            tools=["analyze", "compare", "evaluate"]
        ),
        "researcher": AgentRoleConfig(
            role_name="researcher",
            model_config=ModelConfig(temperature=0.5, cost_limit_per_request=0.65),
            max_reasoning_steps=20,
            enable_knowledge=True,
            tools=["web_search", "document_analysis", "summarize"]
        ),
        "security": AgentRoleConfig(
            role_name="security",
            model_config=ModelConfig(temperature=0.1, cost_limit_per_request=0.70),
            max_reasoning_steps=15,
            tools=["vulnerability_scan", "compliance_check", "threat_model"]
        ),
        "tester": AgentRoleConfig(
            role_name="tester",
            model_config=ModelConfig(temperature=0.2, cost_limit_per_request=0.55),
            max_reasoning_steps=12,
            tools=["test_runner", "coverage_analyzer", "edge_case_generator"]
        ),
        "orchestrator": AgentRoleConfig(
            role_name="orchestrator",
            model_config=ModelConfig(temperature=0.3, cost_limit_per_request=0.80),
            max_reasoning_steps=25,
            tools=["agent_manager", "workflow_engine", "conflict_resolver"]
        )
    }


class ConfigManager:
    """Singleton configuration manager"""
    
    _instance = None
    _config: Optional[AgentConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_config(self, config_path: Optional[str] = None) -> AgentConfig:
        """Load configuration from file or environment"""
        if self._config is not None:
            return self._config
        
        # Determine environment
        env_name = os.getenv("SOPHIA_ENV", "development").lower()
        environment = Environment(env_name)
        
        # Load base configuration
        service_config = ServiceConfig(
            service_name=os.getenv("SERVICE_NAME", "sophia-agent"),
            service_port=int(os.getenv("AGENT_API_PORT", "8003")),
            service_host=os.getenv("SERVICE_HOST", "0.0.0.0")
        )
        
        # Load security configuration
        security_config = SecurityConfig(
            enable_api_key_auth=os.getenv("ENABLE_API_KEY_AUTH", "true").lower() == "true",
            secrets_provider=os.getenv("SECRETS_PROVIDER", "environment"),
            vault_url=os.getenv("VAULT_URL"),
            vault_token=os.getenv("VAULT_TOKEN"),
            aws_region=os.getenv("AWS_REGION")
        )
        
        # Load observability configuration
        observability_config = ObservabilityConfig(
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090"))
        )
        
        # Load rate limiting configuration
        rate_limit_config = RateLimitConfig(
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
        )
        
        # Load default model configuration
        default_model_config = ModelConfig(
            temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4096")),
            cost_limit_per_request=float(os.getenv("DEFAULT_COST_LIMIT", "1.0")),
            timeout_seconds=int(os.getenv("MODEL_TIMEOUT", "120"))
        )
        
        # Create configuration
        self._config = AgentConfig(
            environment=environment,
            service=service_config,
            security=security_config,
            rate_limit=rate_limit_config,
            observability=observability_config,
            default_model=default_model_config,
            role_configs=get_role_defaults()
        )
        
        # Override with config file if provided
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                overrides = json.load(f)
                self._config = AgentConfig(**{**self._config.dict(), **overrides})
        
        return self._config
    
    def get_role_config(self, role: str) -> AgentRoleConfig:
        """Get configuration for a specific role"""
        if self._config is None:
            self.load_config()
        
        return self._config.role_configs.get(
            role,
            AgentRoleConfig(role_name=role, model_config=self._config.default_model)
        )
    
    def get_model_config(self, role: Optional[str] = None) -> ModelConfig:
        """Get model configuration for a role or default"""
        if self._config is None:
            self.load_config()
        
        if role:
            role_config = self.get_role_config(role)
            return role_config.model_settings
        
        return self._config.default_model
    
    def reload_config(self) -> None:
        """Force reload configuration"""
        self._config = None
        self.load_config()


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> AgentConfig:
    """Get current configuration"""
    return config_manager.load_config()


def get_role_config(role: str) -> AgentRoleConfig:
    """Get configuration for a specific role"""
    return config_manager.get_role_config(role)


def get_model_config(role: Optional[str] = None) -> ModelConfig:
    """Get model configuration"""
    return config_manager.get_model_config(role)