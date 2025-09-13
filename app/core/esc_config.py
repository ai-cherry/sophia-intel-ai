"""
ESC Integration Layer for Sophia Intel AI
Runtime configuration loading with automatic refresh and backward compatibility.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field
from infrastructure.pulumi.esc.audit_logger import (
    AuditAction,
    AuditContext,
    AuditLevel,
    AuditStorageBackend,
    ESCAuditLogger,
)
from infrastructure.pulumi.esc.config_loader import ESCConfigLoader
# Import ESC components
from infrastructure.pulumi.esc.secrets_manager import ESCSecretsManager
logger = logging.getLogger(__name__)
@dataclass
class ESCIntegrationConfig:
    """Configuration for ESC integration"""
    pulumi_api_token: str
    pulumi_organization: str = "sophia-intel"
    environment: str = "dev"
    cache_ttl: int = 300  # 5 minutes
    auto_refresh: bool = True
    refresh_interval: int = 300
    watch_files: bool = True
    fallback_env_files: list[str] = field(default_factory=lambda: [])
    enable_audit_logging: bool = True
    backward_compatibility: bool = True
    hot_reload_enabled: bool = True
class ESCRuntimeConfig(BaseModel):
    """Runtime configuration state"""
    initialized: bool = False
    last_refresh: Optional[datetime] = None
    fallback_mode: bool = False
    config_entries: int = 0
    source_summary: dict[str, int] = Field(default_factory=dict)
    integration_health: str = "unknown"  # healthy, degraded, failed
    change_callbacks: int = 0
class SophiaESCConfig:
    """Main ESC configuration integration for Sophia Intel AI"""
    def __init__(self, config: ESCIntegrationConfig):
        self.config = config
        self.runtime_state = ESCRuntimeConfig()
        # Core components
        self.secrets_manager: Optional[ESCSecretsManager] = None
        self.config_loader: Optional[ESCConfigLoader] = None
        self.audit_logger: Optional[ESCAuditLogger] = None
        # Backward compatibility - environment variable fallbacks
        self._env_fallbacks: dict[str, str] = {}
        # Change notification system
        self._change_callbacks: list[Callable[[str, Any, Any], None]] = []
        self._critical_config_keys = {
            "infrastructure.redis.url",
            "infrastructure.redis.password",
            "llm_providers.portkey.api_key",
            "infrastructure.vector_db.qdrant.api_key",
            "infrastructure.vector_db.weaviate.api_key",
        }
        # Initialization state
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
    async def initialize(self) -> bool:
        """Initialize ESC integration with fallback support"""
        async with self._initialization_lock:
            if self._initialized:
                return True
            try:
                logger.info("Initializing Sophia ESC Configuration...")
                # Initialize audit logging
                if self.config.enable_audit_logging:
                    await self._initialize_audit_logging()
                # Initialize secrets manager
                await self._initialize_secrets_manager()
                # Initialize config loader
                await self._initialize_config_loader()
                # Load initial configuration
                await self._load_initial_configuration()
                # Setup backward compatibility
                if self.config.backward_compatibility:
                    await self._setup_backward_compatibility()
                # Start monitoring
                if self.config.hot_reload_enabled:
                    await self._start_hot_reload_monitoring()
                self._initialized = True
                self.runtime_state.initialized = True
                self.runtime_state.integration_health = "healthy"
                await self._log_initialization_success()
                logger.info("ESC Configuration initialized successfully")
                return True
            except Exception as e:
                logger.error(f"ESC Configuration initialization failed: {e}")
                await self._enable_fallback_mode(str(e))
                return False
    async def _initialize_audit_logging(self):
        """Initialize audit logging system"""
        audit_backends = [
            AuditStorageBackend(
                backend_type="file",
                connection_params={"file_path": "logs/esc_integration_audit.log"},
                encryption_enabled=True,
                compression_enabled=True,
            )
        ]
        self.audit_logger = ESCAuditLogger(
            storage_backends=audit_backends, compliance_mode=True
        )
        await self.audit_logger.start()
        await self.audit_logger.log_event(
            level=AuditLevel.INFO,
            action=AuditAction.SYSTEM_START,
            resource="esc_integration",
            message="ESC integration audit logging started",
            context=AuditContext(
                service_name="sophia_esc_config", environment=self.config.environment
            ),
        )
    async def _initialize_secrets_manager(self):
        """Initialize ESC secrets manager"""
        self.secrets_manager = ESCSecretsManager(
            api_token=self.config.pulumi_api_token,
            organization=self.config.pulumi_organization,
            cache_ttl=self.config.cache_ttl,
        )
        # Test connection
        if self.secrets_manager:
            health_status = await self.secrets_manager.health_check()
            if health_status["status"] != "healthy":
                raise ConnectionError(f"ESC connection unhealthy: {health_status}")
    async def _initialize_config_loader(self):
        """Initialize ESC config loader"""
        if not self.secrets_manager:
            raise ValueError("Secrets manager not initialized")
        self.config_loader = ESCConfigLoader(
            secrets_manager=self.secrets_manager,
            environment=self.config.environment,
            fallback_env_files=self.config.fallback_env_files,
            auto_refresh=self.config.auto_refresh,
            refresh_interval=self.config.refresh_interval,
            watch_files=self.config.watch_files,
        )
        # Add change callback
        self.config_loader.add_change_callback(self._handle_config_change)
        success = await self.config_loader.initialize()
        if not success:
            raise RuntimeError("Config loader initialization failed")
    async def _load_initial_configuration(self):
        """Load initial configuration and update runtime state"""
        if not self.config_loader:
            return
        # Update runtime state
        status = self.config_loader.get_status()
        self.runtime_state.last_refresh = datetime.utcnow()
        self.runtime_state.config_entries = status["total_entries"]
        self.runtime_state.source_summary = status["sources_summary"]
        # Validate critical configurations
        await self._validate_critical_config()
    async def _setup_backward_compatibility(self):
        """Setup backward compatibility with environment variables"""
        logger.info("Setting up backward compatibility with environment variables")
        # Map ESC keys to environment variable names
        env_mappings = {
            "infrastructure.redis.url": "REDIS_URL",
            "infrastructure.redis.password": "REDIS_PASSWORD",
            "llm_providers.portkey.api_key": "PORTKEY_API_KEY",
            "llm_providers.direct_keys.openai": "OPENAI_API_KEY",
            "llm_providers.direct_keys.anthropic": "ANTHROPIC_API_KEY",
            "infrastructure.vector_db.qdrant.api_key": "QDRANT_API_KEY",
            "infrastructure.vector_db.qdrant.url": "QDRANT_URL",
            "infrastructure.vector_db.weaviate.api_key": "WEAVIATE_API_KEY",
            "infrastructure.vector_db.weaviate.url": "WEAVIATE_URL",
            "infrastructure_providers.mem0.api_key": "MEM0_API_KEY",
            "infrastructure_providers.n8n.api_key": "N8N_API_KEY",
            "pulumi.api_key": "PULUMI_API_KEY",
        }
        # Set environment variables from ESC
        if self.config_loader:
            for esc_key, env_var in env_mappings.items():
                try:
                    value = self.config_loader.get(esc_key)
                    if value:
                        os.environ[env_var] = str(value)
                        self._env_fallbacks[env_var] = esc_key
                        logger.debug(f"Set {env_var} from ESC key {esc_key}")
                except Exception as e:
                    logger.warning(f"Failed to set {env_var} from {esc_key}: {e}")
        logger.info(
            f"Backward compatibility setup complete: {len(self._env_fallbacks)} mappings"
        )
    async def _start_hot_reload_monitoring(self):
        """Start hot reload monitoring for configuration changes"""
        logger.info("Starting hot reload monitoring")
        # Start background task for health monitoring
        asyncio.create_task(self._health_monitor_loop())
        # Register for critical config changes
        self.add_change_callback(self._handle_critical_config_change)
    async def _handle_config_change(self, key: str, new_value: Any, old_value: Any):
        """Handle configuration changes"""
        try:
            logger.info(f"Configuration changed: {key}")
            # Update environment variables for backward compatibility
            if self.config.backward_compatibility:
                await self._update_env_var_for_key(key, new_value)
            # Notify registered callbacks
            for callback in self._change_callbacks:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    logger.error(f"Error in change callback: {e}")
            # Log the change
            if self.audit_logger:
                await self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    action=AuditAction.CONFIG_REFRESH,
                    resource=key,
                    message=f"Configuration changed: {key}",
                    context=AuditContext(
                        service_name="sophia_esc_config",
                        environment=self.config.environment,
                    ),
                    data={
                        "old_value_type": type(old_value).__name__,
                        "new_value_type": type(new_value).__name__,
                    },
                )
        except Exception as e:
            logger.error(f"Error handling config change for {key}: {e}")
    async def _handle_critical_config_change(
        self, key: str, new_value: Any, old_value: Any
    ):
        """Handle changes to critical configuration"""
        if key in self._critical_config_keys:
            logger.warning(f"Critical configuration changed: {key}")
            if self.audit_logger:
                await self.audit_logger.log_event(
                    level=AuditLevel.SECURITY,
                    action=AuditAction.CONFIG_REFRESH,
                    resource=key,
                    message=f"Critical configuration changed: {key}",
                    context=AuditContext(
                        service_name="sophia_esc_config",
                        environment=self.config.environment,
                    ),
                    data={"critical": True},
                )
    async def _update_env_var_for_key(self, key: str, value: Any):
        """Update environment variable for ESC key"""
        # Find corresponding environment variable
        for env_var, esc_key in self._env_fallbacks.items():
            if esc_key == key:
                os.environ[env_var] = str(value)
                logger.debug(
                    f"Updated environment variable {env_var} with new value from {key}"
                )
                break
    async def _validate_critical_config(self):
        """Validate critical configuration is present"""
        if not self.config_loader:
            return
        missing_critical = []
        for key in self._critical_config_keys:
            value = self.config_loader.get(key)
            if not value:
                missing_critical.append(key)
        if missing_critical:
            logger.warning(f"Missing critical configuration: {missing_critical}")
            self.runtime_state.integration_health = "degraded"
            if self.audit_logger:
                await self.audit_logger.log_event(
                    level=AuditLevel.WARNING,
                    action=AuditAction.CONFIG_LOAD,
                    resource="critical_config",
                    message=f"Missing critical configuration keys: {missing_critical}",
                    context=AuditContext(
                        service_name="sophia_esc_config",
                        environment=self.config.environment,
                    ),
                    data={"missing_keys": missing_critical},
                )
    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_integration_health()
            except asyncio.CancelledError:
                logger.info("Health monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    async def _check_integration_health(self):
        """Check integration health and update status"""
        try:
            if self.secrets_manager:
                health = await self.secrets_manager.health_check()
                if health["status"] == "healthy":
                    if self.runtime_state.integration_health != "healthy":
                        self.runtime_state.integration_health = "healthy"
                        logger.info("ESC integration health restored")
                else:
                    self.runtime_state.integration_health = "degraded"
                    logger.warning(f"ESC integration health degraded: {health}")
        except Exception as e:
            self.runtime_state.integration_health = "failed"
            logger.error(f"ESC integration health check failed: {e}")
    async def _enable_fallback_mode(self, error_message: str):
        """Enable fallback mode when ESC is unavailable"""
        logger.warning(f"Enabling fallback mode: {error_message}")
        self.runtime_state.fallback_mode = True
        self.runtime_state.integration_health = "failed"
        # Ensure critical environment variables are set from .env files
        await self._load_fallback_env_files()
        if self.audit_logger:
            try:
                await self.audit_logger.log_event(
                    level=AuditLevel.ERROR,
                    action=AuditAction.ERROR_OCCURRED,
                    resource="esc_integration",
                    message=f"Fallback mode enabled: {error_message}",
                    context=AuditContext(
                        service_name="sophia_esc_config",
                        environment=self.config.environment,
                    ),
                    success=False,
                    error_details=error_message,
                )
            except Exception:
                pass  # Don't fail if audit logging also fails
    async def _load_fallback_env_files(self):
        """Load environment files as fallback"""
        for env_file in self.config.fallback_env_files:
            try:
                if os.path.exists(env_file):
                    with open(env_file) as f:
                        for line in f:
                            line = line.strip()
                            if line and "=" in line and not line.startswith("#"):
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if value:
                                    os.environ[key] = value
                    logger.info(f"Loaded fallback environment file: {env_file}")
            except Exception as e:
                logger.error(f"Failed to load fallback env file {env_file}: {e}")
    async def _log_initialization_success(self):
        """Log successful initialization"""
        if self.audit_logger:
            await self.audit_logger.log_event(
                level=AuditLevel.INFO,
                action=AuditAction.SYSTEM_START,
                resource="esc_integration",
                message="ESC integration initialized successfully",
                context=AuditContext(
                    service_name="sophia_esc_config",
                    environment=self.config.environment,
                ),
                data={
                    "config_entries": self.runtime_state.config_entries,
                    "fallback_mode": self.runtime_state.fallback_mode,
                    "backward_compatibility": self.config.backward_compatibility,
                    "auto_refresh": self.config.auto_refresh,
                },
            )
    # Public API methods
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if self.config_loader and not self.runtime_state.fallback_mode:
            return self.config_loader.get(key, default)
        else:
            # Fallback to environment variables
            env_key = key.replace(".", "_").upper()
            return os.getenv(env_key, default)
    async def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret configuration value"""
        if self.config_loader and not self.runtime_state.fallback_mode:
            return await self.config_loader.get_secret(key, default)
        else:
            # Fallback to environment variables
            env_key = key.replace(".", "_").upper()
            return os.getenv(env_key, default)
    def get_all(self, prefix: str = "") -> dict[str, Any]:
        """Get all configuration values with optional prefix"""
        if self.config_loader and not self.runtime_state.fallback_mode:
            return self.config_loader.get_all(prefix)
        else:
            # Fallback to environment variables
            env_vars = {}
            prefix_upper = prefix.replace(".", "_").upper()
            for key, value in os.environ.items():
                if not prefix_upper or key.startswith(prefix_upper):
                    display_key = key.lower().replace("_", ".")
                    if prefix:
                        display_key = display_key[len(prefix) :].lstrip(".")
                    env_vars[display_key] = value
            return env_vars
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """Add callback for configuration changes"""
        self._change_callbacks.append(callback)
        self.runtime_state.change_callbacks = len(self._change_callbacks)
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """Remove configuration change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            self.runtime_state.change_callbacks = len(self._change_callbacks)
    async def refresh_config(self, force: bool = False) -> bool:
        """Manually refresh configuration"""
        if self.config_loader and not self.runtime_state.fallback_mode:
            success = await self.config_loader.refresh_config(force)
            if success:
                self.runtime_state.last_refresh = datetime.utcnow()
            return success
        return False
    def get_status(self) -> dict[str, Any]:
        """Get integration status"""
        loader_status = {}
        if self.config_loader:
            loader_status = self.config_loader.get_status()
        return {
            "initialized": self.runtime_state.initialized,
            "fallback_mode": self.runtime_state.fallback_mode,
            "integration_health": self.runtime_state.integration_health,
            "last_refresh": (
                self.runtime_state.last_refresh.isoformat()
                if self.runtime_state.last_refresh
                else None
            ),
            "config_entries": self.runtime_state.config_entries,
            "source_summary": self.runtime_state.source_summary,
            "change_callbacks": self.runtime_state.change_callbacks,
            "environment": self.config.environment,
            "backward_compatibility": self.config.backward_compatibility,
            "auto_refresh": self.config.auto_refresh,
            "config_loader": loader_status,
        }
    def get_health_summary(self) -> dict[str, Any]:
        """Get health summary for monitoring"""
        return {
            "healthy": self.runtime_state.integration_health == "healthy",
            "status": self.runtime_state.integration_health,
            "fallback_mode": self.runtime_state.fallback_mode,
            "last_refresh": self.runtime_state.last_refresh,
            "config_entries": self.runtime_state.config_entries,
            "initialized": self.runtime_state.initialized,
        }
    async def shutdown(self):
        """Shutdown ESC integration gracefully"""
        logger.info("Shutting down ESC integration")
        try:
            if self.config_loader:
                await self.config_loader.shutdown()
            if self.audit_logger:
                await self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    action=AuditAction.SYSTEM_STOP,
                    resource="esc_integration",
                    message="ESC integration shutdown",
                    context=AuditContext(
                        service_name="sophia_esc_config",
                        environment=self.config.environment,
                    ),
                )
                await self.audit_logger.stop()
            self._initialized = False
            self.runtime_state.initialized = False
        except Exception as e:
            logger.error(f"Error during ESC integration shutdown: {e}")
# Global instance for application use
_global_esc_config: Optional[SophiaESCConfig] = None
async def initialize_esc_config(
    pulumi_api_token: Optional[str] = None, environment: Optional[str] = None, **kwargs
) -> SophiaESCConfig:
    """Initialize global ESC configuration"""
    global _global_esc_config
    # Get configuration from environment if not provided
    if not pulumi_api_token:
        pulumi_api_token = os.getenv("PULUMI_API_KEY")
    if not pulumi_api_token:
        raise ValueError("Pulumi API token required for ESC integration")
    if not environment:
        environment = os.getenv("ENVIRONMENT", "dev")
    # Create configuration
    config = ESCIntegrationConfig(
        pulumi_api_token=pulumi_api_token, environment=environment, **kwargs
    )
    # Initialize ESC config
    _global_esc_config = SophiaESCConfig(config)
    success = await _global_esc_config.initialize()
    if not success:
        logger.warning("ESC configuration initialized in fallback mode")
    return _global_esc_config
def get_esc_config() -> Optional[SophiaESCConfig]:
    """Get global ESC configuration instance"""
    return _global_esc_config
@asynccontextmanager
async def esc_config_context(**kwargs):
    """Context manager for ESC configuration"""
    config = await initialize_esc_config(**kwargs)
    try:
        yield config
    finally:
        await config.shutdown()
# Convenience functions for backward compatibility
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value (backward compatible)"""
    config = get_esc_config()
    if config:
        return config.get(key, default)
    else:
        # Fallback to environment variables
        env_key = key.replace(".", "_").upper()
        return os.getenv(env_key, default)
async def get_secret_config(key: str, default: Any = None) -> Any:
    """Get secret configuration value (backward compatible)"""
    config = get_esc_config()
    if config:
        return await config.get_secret(key, default)
    else:
        # Fallback to environment variables
        env_key = key.replace(".", "_").upper()
        return os.getenv(env_key, default)
def get_all_config(prefix: str = "") -> dict[str, Any]:
    """Get all configuration values (backward compatible)"""
    config = get_esc_config()
    if config:
        return config.get_all(prefix)
    else:
        # Fallback to environment variables
        env_vars = {}
        prefix_upper = prefix.replace(".", "_").upper()
        for key, value in os.environ.items():
            if not prefix_upper or key.startswith(prefix_upper):
                display_key = key.lower().replace("_", ".")
                if prefix:
                    display_key = display_key[len(prefix) :].lstrip(".")
                env_vars[display_key] = value
        return env_vars
