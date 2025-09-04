"""
Configuration and Deployment Management for Code Refactoring Swarm
Production-ready configuration with safety controls and monitoring
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.swarms.refactoring.code_refactoring_swarm import RefactoringRisk, RefactoringType


class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"


class MonitoringLevel(Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class SafetyConfiguration:
    """Safety controls for refactoring operations"""
    max_files_per_session: int = 50
    max_changes_per_file: int = 20
    require_backup: bool = True
    require_tests: bool = True
    rollback_timeout_minutes: int = 60
    approval_required_for_risk: List[RefactoringRisk] = field(
        default_factory=lambda: [RefactoringRisk.HIGH, RefactoringRisk.CRITICAL]
    )
    allowed_file_extensions: List[str] = field(
        default_factory=lambda: [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"]
    )
    forbidden_paths: List[str] = field(
        default_factory=lambda: ["/config/", "/secrets/", "/.env", "/credentials/"]
    )


@dataclass
class ResourceConfiguration:
    """Resource allocation and limits"""
    max_concurrent_agents: int = 10
    max_memory_per_agent_mb: int = 512
    max_execution_time_minutes: int = 120
    circuit_breaker_threshold: int = 5
    retry_attempts: int = 3
    rate_limit_requests_per_minute: int = 300
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


@dataclass 
class MonitoringConfiguration:
    """Monitoring and observability settings"""
    level: MonitoringLevel = MonitoringLevel.DETAILED
    metrics_enabled: bool = True
    logging_enabled: bool = True
    tracing_enabled: bool = True
    alerts_enabled: bool = True
    dashboard_enabled: bool = True
    export_prometheus: bool = True
    webhook_notifications: List[str] = field(default_factory=list)
    slack_channel: Optional[str] = None
    email_notifications: List[str] = field(default_factory=list)


@dataclass
class RefactoringSwarmConfiguration:
    """Complete configuration for Code Refactoring Swarm deployment"""
    
    # Environment settings
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    swarm_name: str = "code-refactoring-swarm"
    version: str = "1.0.0"
    
    # Core settings
    enabled_refactoring_types: List[RefactoringType] = field(
        default_factory=lambda: list(RefactoringType)
    )
    default_risk_tolerance: RefactoringRisk = RefactoringRisk.MEDIUM
    dry_run_default: bool = True
    
    # Component configurations
    safety: SafetyConfiguration = field(default_factory=SafetyConfiguration)
    resources: ResourceConfiguration = field(default_factory=ResourceConfiguration)
    monitoring: MonitoringConfiguration = field(default_factory=MonitoringConfiguration)
    
    # Agent settings
    agent_model_overrides: Dict[str, str] = field(default_factory=dict)
    agent_temperature_overrides: Dict[str, float] = field(default_factory=dict)
    debate_rounds: int = 3
    consensus_threshold: float = 0.8
    
    # Integration settings
    git_integration: bool = True
    ci_cd_integration: bool = False
    ide_integration: bool = False
    api_enabled: bool = True
    api_port: int = 8080
    
    # Storage and persistence
    session_storage_enabled: bool = True
    session_retention_days: int = 30
    backup_retention_days: int = 7
    memory_enabled: bool = True
    
    @classmethod
    def for_environment(cls, env: DeploymentEnvironment) -> 'RefactoringSwarmConfiguration':
        """Create configuration optimized for specific environment"""
        
        if env == DeploymentEnvironment.DEVELOPMENT:
            return cls._development_config()
        elif env == DeploymentEnvironment.STAGING:
            return cls._staging_config()
        elif env == DeploymentEnvironment.PRODUCTION:
            return cls._production_config()
        elif env == DeploymentEnvironment.ENTERPRISE:
            return cls._enterprise_config()
        else:
            return cls()

    @classmethod
    def _development_config(cls) -> 'RefactoringSwarmConfiguration':
        """Development environment configuration"""
        return cls(
            environment=DeploymentEnvironment.DEVELOPMENT,
            dry_run_default=True,
            safety=SafetyConfiguration(
                max_files_per_session=20,
                max_changes_per_file=10,
                require_backup=False,
                require_tests=False,
                approval_required_for_risk=[RefactoringRisk.CRITICAL]
            ),
            resources=ResourceConfiguration(
                max_concurrent_agents=5,
                max_memory_per_agent_mb=256,
                max_execution_time_minutes=60,
                rate_limit_requests_per_minute=100
            ),
            monitoring=MonitoringConfiguration(
                level=MonitoringLevel.BASIC,
                alerts_enabled=False,
                dashboard_enabled=True
            )
        )

    @classmethod
    def _staging_config(cls) -> 'RefactoringSwarmConfiguration':
        """Staging environment configuration"""
        return cls(
            environment=DeploymentEnvironment.STAGING,
            dry_run_default=True,
            safety=SafetyConfiguration(
                max_files_per_session=35,
                max_changes_per_file=15,
                require_backup=True,
                require_tests=True,
                approval_required_for_risk=[RefactoringRisk.HIGH, RefactoringRisk.CRITICAL]
            ),
            resources=ResourceConfiguration(
                max_concurrent_agents=8,
                max_memory_per_agent_mb=384,
                max_execution_time_minutes=90,
                rate_limit_requests_per_minute=200
            ),
            monitoring=MonitoringConfiguration(
                level=MonitoringLevel.DETAILED,
                alerts_enabled=True,
                dashboard_enabled=True
            )
        )

    @classmethod
    def _production_config(cls) -> 'RefactoringSwarmConfiguration':
        """Production environment configuration"""
        return cls(
            environment=DeploymentEnvironment.PRODUCTION,
            dry_run_default=False,
            safety=SafetyConfiguration(
                max_files_per_session=50,
                max_changes_per_file=20,
                require_backup=True,
                require_tests=True,
                rollback_timeout_minutes=30,
                approval_required_for_risk=[RefactoringRisk.HIGH, RefactoringRisk.CRITICAL]
            ),
            resources=ResourceConfiguration(
                max_concurrent_agents=10,
                max_memory_per_agent_mb=512,
                max_execution_time_minutes=120,
                circuit_breaker_threshold=3,
                rate_limit_requests_per_minute=300
            ),
            monitoring=MonitoringConfiguration(
                level=MonitoringLevel.COMPREHENSIVE,
                alerts_enabled=True,
                dashboard_enabled=True,
                export_prometheus=True,
                tracing_enabled=True
            ),
            ci_cd_integration=True
        )

    @classmethod
    def _enterprise_config(cls) -> 'RefactoringSwarmConfiguration':
        """Enterprise environment configuration"""
        return cls(
            environment=DeploymentEnvironment.ENTERPRISE,
            dry_run_default=False,
            safety=SafetyConfiguration(
                max_files_per_session=100,
                max_changes_per_file=30,
                require_backup=True,
                require_tests=True,
                rollback_timeout_minutes=15,
                approval_required_for_risk=[RefactoringRisk.MEDIUM, RefactoringRisk.HIGH, RefactoringRisk.CRITICAL]
            ),
            resources=ResourceConfiguration(
                max_concurrent_agents=20,
                max_memory_per_agent_mb=1024,
                max_execution_time_minutes=240,
                circuit_breaker_threshold=2,
                rate_limit_requests_per_minute=500
            ),
            monitoring=MonitoringConfiguration(
                level=MonitoringLevel.COMPREHENSIVE,
                alerts_enabled=True,
                dashboard_enabled=True,
                export_prometheus=True,
                tracing_enabled=True,
                webhook_notifications=["https://hooks.slack.com/services/enterprise"]
            ),
            ci_cd_integration=True,
            ide_integration=True,
            session_retention_days=90,
            backup_retention_days=30
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Safety validation
        if self.safety.max_files_per_session < 1:
            issues.append("max_files_per_session must be >= 1")
            
        if self.safety.max_changes_per_file < 1:
            issues.append("max_changes_per_file must be >= 1")
            
        if self.safety.rollback_timeout_minutes < 5:
            issues.append("rollback_timeout_minutes must be >= 5")
        
        # Resource validation
        if self.resources.max_concurrent_agents < 1:
            issues.append("max_concurrent_agents must be >= 1")
            
        if self.resources.max_memory_per_agent_mb < 128:
            issues.append("max_memory_per_agent_mb must be >= 128")
            
        if self.resources.max_execution_time_minutes < 5:
            issues.append("max_execution_time_minutes must be >= 5")
        
        # Agent validation
        if self.debate_rounds < 1 or self.debate_rounds > 10:
            issues.append("debate_rounds must be between 1 and 10")
            
        if not 0.5 <= self.consensus_threshold <= 1.0:
            issues.append("consensus_threshold must be between 0.5 and 1.0")
            
        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "swarm_name": self.swarm_name,
            "version": self.version,
            "enabled_refactoring_types": [rt.value for rt in self.enabled_refactoring_types],
            "default_risk_tolerance": self.default_risk_tolerance.value,
            "dry_run_default": self.dry_run_default,
            "safety": {
                "max_files_per_session": self.safety.max_files_per_session,
                "max_changes_per_file": self.safety.max_changes_per_file,
                "require_backup": self.safety.require_backup,
                "require_tests": self.safety.require_tests,
                "rollback_timeout_minutes": self.safety.rollback_timeout_minutes,
                "approval_required_for_risk": [r.value for r in self.safety.approval_required_for_risk],
                "allowed_file_extensions": self.safety.allowed_file_extensions,
                "forbidden_paths": self.safety.forbidden_paths
            },
            "resources": {
                "max_concurrent_agents": self.resources.max_concurrent_agents,
                "max_memory_per_agent_mb": self.resources.max_memory_per_agent_mb,
                "max_execution_time_minutes": self.resources.max_execution_time_minutes,
                "circuit_breaker_threshold": self.resources.circuit_breaker_threshold,
                "retry_attempts": self.resources.retry_attempts,
                "rate_limit_requests_per_minute": self.resources.rate_limit_requests_per_minute,
                "cache_enabled": self.resources.cache_enabled,
                "cache_ttl_seconds": self.resources.cache_ttl_seconds
            },
            "monitoring": {
                "level": self.monitoring.level.value,
                "metrics_enabled": self.monitoring.metrics_enabled,
                "logging_enabled": self.monitoring.logging_enabled,
                "tracing_enabled": self.monitoring.tracing_enabled,
                "alerts_enabled": self.monitoring.alerts_enabled,
                "dashboard_enabled": self.monitoring.dashboard_enabled,
                "export_prometheus": self.monitoring.export_prometheus,
                "webhook_notifications": self.monitoring.webhook_notifications,
                "slack_channel": self.monitoring.slack_channel,
                "email_notifications": self.monitoring.email_notifications
            },
            "agent_model_overrides": self.agent_model_overrides,
            "agent_temperature_overrides": self.agent_temperature_overrides,
            "debate_rounds": self.debate_rounds,
            "consensus_threshold": self.consensus_threshold,
            "git_integration": self.git_integration,
            "ci_cd_integration": self.ci_cd_integration,
            "ide_integration": self.ide_integration,
            "api_enabled": self.api_enabled,
            "api_port": self.api_port,
            "session_storage_enabled": self.session_storage_enabled,
            "session_retention_days": self.session_retention_days,
            "backup_retention_days": self.backup_retention_days,
            "memory_enabled": self.memory_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefactoringSwarmConfiguration':
        """Create configuration from dictionary"""
        config = cls()
        
        # Basic settings
        config.environment = DeploymentEnvironment(data.get("environment", "development"))
        config.swarm_name = data.get("swarm_name", "code-refactoring-swarm")
        config.version = data.get("version", "1.0.0")
        
        # Refactoring settings
        config.enabled_refactoring_types = [
            RefactoringType(rt) for rt in data.get("enabled_refactoring_types", [])
        ]
        config.default_risk_tolerance = RefactoringRisk(
            data.get("default_risk_tolerance", "medium")
        )
        config.dry_run_default = data.get("dry_run_default", True)
        
        # Safety settings
        safety_data = data.get("safety", {})
        config.safety = SafetyConfiguration(
            max_files_per_session=safety_data.get("max_files_per_session", 50),
            max_changes_per_file=safety_data.get("max_changes_per_file", 20),
            require_backup=safety_data.get("require_backup", True),
            require_tests=safety_data.get("require_tests", True),
            rollback_timeout_minutes=safety_data.get("rollback_timeout_minutes", 60),
            approval_required_for_risk=[
                RefactoringRisk(r) for r in safety_data.get("approval_required_for_risk", ["high", "critical"])
            ],
            allowed_file_extensions=safety_data.get("allowed_file_extensions", [".py", ".js", ".ts"]),
            forbidden_paths=safety_data.get("forbidden_paths", ["/config/", "/secrets/"])
        )
        
        # Resource settings
        resources_data = data.get("resources", {})
        config.resources = ResourceConfiguration(
            max_concurrent_agents=resources_data.get("max_concurrent_agents", 10),
            max_memory_per_agent_mb=resources_data.get("max_memory_per_agent_mb", 512),
            max_execution_time_minutes=resources_data.get("max_execution_time_minutes", 120),
            circuit_breaker_threshold=resources_data.get("circuit_breaker_threshold", 5),
            retry_attempts=resources_data.get("retry_attempts", 3),
            rate_limit_requests_per_minute=resources_data.get("rate_limit_requests_per_minute", 300),
            cache_enabled=resources_data.get("cache_enabled", True),
            cache_ttl_seconds=resources_data.get("cache_ttl_seconds", 3600)
        )
        
        # Monitoring settings
        monitoring_data = data.get("monitoring", {})
        config.monitoring = MonitoringConfiguration(
            level=MonitoringLevel(monitoring_data.get("level", "detailed")),
            metrics_enabled=monitoring_data.get("metrics_enabled", True),
            logging_enabled=monitoring_data.get("logging_enabled", True),
            tracing_enabled=monitoring_data.get("tracing_enabled", True),
            alerts_enabled=monitoring_data.get("alerts_enabled", True),
            dashboard_enabled=monitoring_data.get("dashboard_enabled", True),
            export_prometheus=monitoring_data.get("export_prometheus", True),
            webhook_notifications=monitoring_data.get("webhook_notifications", []),
            slack_channel=monitoring_data.get("slack_channel"),
            email_notifications=monitoring_data.get("email_notifications", [])
        )
        
        # Agent settings
        config.agent_model_overrides = data.get("agent_model_overrides", {})
        config.agent_temperature_overrides = data.get("agent_temperature_overrides", {})
        config.debate_rounds = data.get("debate_rounds", 3)
        config.consensus_threshold = data.get("consensus_threshold", 0.8)
        
        # Integration settings
        config.git_integration = data.get("git_integration", True)
        config.ci_cd_integration = data.get("ci_cd_integration", False)
        config.ide_integration = data.get("ide_integration", False)
        config.api_enabled = data.get("api_enabled", True)
        config.api_port = data.get("api_port", 8080)
        
        # Storage settings
        config.session_storage_enabled = data.get("session_storage_enabled", True)
        config.session_retention_days = data.get("session_retention_days", 30)
        config.backup_retention_days = data.get("backup_retention_days", 7)
        config.memory_enabled = data.get("memory_enabled", True)
        
        return config

    @classmethod
    def from_env(cls) -> 'RefactoringSwarmConfiguration':
        """Create configuration from environment variables"""
        env = DeploymentEnvironment(
            os.getenv("REFACTORING_SWARM_ENV", "development")
        )
        
        config = cls.for_environment(env)
        
        # Override with environment variables if present
        if os.getenv("REFACTORING_MAX_FILES"):
            config.safety.max_files_per_session = int(os.getenv("REFACTORING_MAX_FILES"))
            
        if os.getenv("REFACTORING_MAX_AGENTS"):
            config.resources.max_concurrent_agents = int(os.getenv("REFACTORING_MAX_AGENTS"))
            
        if os.getenv("REFACTORING_DRY_RUN"):
            config.dry_run_default = os.getenv("REFACTORING_DRY_RUN").lower() == "true"
            
        if os.getenv("REFACTORING_API_PORT"):
            config.api_port = int(os.getenv("REFACTORING_API_PORT"))
            
        return config


# Predefined configurations for common scenarios
DEVELOPMENT_CONFIG = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.DEVELOPMENT)
STAGING_CONFIG = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.STAGING) 
PRODUCTION_CONFIG = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.PRODUCTION)
ENTERPRISE_CONFIG = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.ENTERPRISE)