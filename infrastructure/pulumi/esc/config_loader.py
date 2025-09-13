"""
Dynamic Configuration Loader for Pulumi ESC Integration
Provides runtime configuration loading with caching, fallbacks, and hot reloading.
"""
import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import aiofiles
from pydantic import BaseModel, Field
from watchfiles import awatch
from .secrets_manager import ESCSecretsManager
logger = logging.getLogger(__name__)
class ConfigSource(str, Enum):
    """Configuration source types"""
    ESC = "esc"
    ENV_FILE = "env_file"
    ENVIRONMENT = "environment"
    DEFAULT = "default"
class ConfigPriority(int, Enum):
    """Configuration priority levels"""
    ESC = 1  # Highest priority
    ENVIRONMENT = 2  # Environment variables
    ENV_FILE = 3  # .env files
    DEFAULT = 4  # Default values (lowest priority)
@dataclass
class ConfigEntry:
    """Configuration entry with metadata"""
    key: str
    value: Any
    source: ConfigSource
    priority: ConfigPriority
    last_updated: datetime
    is_secret: bool = False
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
class ConfigCache(BaseModel):
    """Configuration cache with hierarchical structure"""
    entries: Dict[str, ConfigEntry] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_refresh: Optional[datetime] = None
    refresh_interval: int = Field(default=300)  # 5 minutes
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.last_refresh:
            return False
        return (datetime.utcnow() - self.last_refresh).seconds < self.refresh_interval
    def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value by key"""
        entry = self.entries.get(key)
        return entry.value if entry else None
    def set_config(
        self,
        key: str,
        value: Any,
        source: ConfigSource,
        is_secret: bool = False,
        description: Optional[str] = None,
    ):
        """Set configuration entry"""
        priority = ConfigPriority[source.name]
        entry = ConfigEntry(
            key=key,
            value=value,
            source=source,
            priority=priority,
            last_updated=datetime.utcnow(),
            is_secret=is_secret,
            description=description,
        )
        # Only update if new entry has higher priority
        existing = self.entries.get(key)
        if not existing or priority.value <= existing.priority.value:
            self.entries[key] = entry
    def merge_configs(self, configs: Dict[str, Any], source: ConfigSource):
        """Merge flat or nested configuration dictionary"""
        def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
            """Flatten nested dictionary with dot notation"""
            items = []
            for k, v in d.items():
                new_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        flattened = _flatten_dict(configs)
        for key, value in flattened.items():
            self.set_config(key, value, source)
class ESCConfigLoader:
    """Dynamic configuration loader with ESC integration"""
    def __init__(
        self,
        secrets_manager: ESCSecretsManager,
        environment: str = "dev",
        fallback_env_files: Optional[List[str]] = None,
        auto_refresh: bool = True,
        refresh_interval: int = 300,
        watch_files: bool = True,
    ):
        self.secrets_manager = secrets_manager
        self.environment = environment
        self.fallback_env_files = fallback_env_files or [".env", f".env.{environment}"]
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.watch_files = watch_files
        # Configuration cache
        self.cache = ConfigCache(refresh_interval=refresh_interval)
        # File watchers and background tasks
        self._file_watchers: Dict[str, asyncio.Task] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        # Runtime state
        self._initialization_complete = False
        self._last_esc_sync: Optional[datetime] = None
        self._fallback_mode = False
    async def initialize(self) -> bool:
        """Initialize the configuration loader"""
        try:
            logger.info("Initializing ESC Configuration Loader...")
            # Load initial configuration
            await self._load_all_configurations()
            # Start background tasks
            if self.auto_refresh:
                await self._start_background_tasks()
            self._initialization_complete = True
            logger.info(
                f"ESC Configuration Loader initialized with {len(self.cache.entries)} entries"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ESC Configuration Loader: {e}")
            # Enable fallback mode
            await self._enable_fallback_mode()
            return False
    async def _load_all_configurations(self):
        """Load configurations from all sources in priority order"""
        # 1. Load default configurations (lowest priority)
        await self._load_default_config()
        # 2. Load from .env files
        await self._load_env_files()
        # 3. Load from environment variables
        await self._load_environment_variables()
        # 4. Load from ESC (highest priority)
        await self._load_esc_config()
        self.cache.last_refresh = datetime.utcnow()
    async def _load_default_config(self):
        """Load default configuration values"""
        defaults = {
            "application.debug": False,
            "application.log_level": "info",
            "application.cors_origins": ["http://localhost:3000"],
            "infrastructure.redis.max_connections": 50,
            "infrastructure.redis.timeout": 30,
            "infrastructure.vector_db.primary": "qdrant",
            "security.api_key_rotation_days": 90,
            "security.session_timeout_minutes": 30,
            "monitoring.metrics_enabled": True,
            "monitoring.health_check_interval": 30,
        }
        self.cache.merge_configs(defaults, ConfigSource.DEFAULT)
        logger.debug(f"Loaded {len(defaults)} default configuration entries")
    async def _load_env_files(self):
        """Load configuration from .env files"""
        for env_file in self.fallback_env_files:
            await self._load_single_env_file(env_file)
    async def _load_single_env_file(self, file_path: str):
        """Load a single .env file"""
        try:
            if not Path(file_path).exists():
                logger.debug(f"Env file not found: {file_path}")
                return
            async with aiofiles.open(file_path) as f:
                content = await f.read()
            env_vars = {}
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Convert to nested key format
                    nested_key = self._convert_env_key_to_nested(key)
                    env_vars[nested_key] = value
            self.cache.merge_configs(env_vars, ConfigSource.ENV_FILE)
            logger.debug(f"Loaded {len(env_vars)} entries from {file_path}")
        except Exception as e:
            logger.warning(f"Failed to load env file {file_path}: {e}")
    async def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_vars = {}
        # Get all environment variables
        for key, value in os.environ.items():
            # Convert environment variable names to nested config keys
            nested_key = self._convert_env_key_to_nested(key)
            env_vars[nested_key] = value
        self.cache.merge_configs(env_vars, ConfigSource.ENVIRONMENT)
        logger.debug(f"Loaded {len(env_vars)} environment variables")
    async def _load_esc_config(self):
        """Load configuration from Pulumi ESC"""
        try:
            esc_config = await self.secrets_manager.get_environment_config(self.environment)
            if esc_config:
                self.cache.merge_configs(esc_config, ConfigSource.ESC)
                self._last_esc_sync = datetime.utcnow()
                self._fallback_mode = False
                logger.info(f"Loaded configuration from ESC environment: {self.environment}")
            else:
                logger.warning("No configuration found in ESC, using fallback sources")
        except Exception as e:
            logger.error(f"Failed to load ESC configuration: {e}")
            await self._enable_fallback_mode()
    def _convert_env_key_to_nested(self, env_key: str) -> str:
        """Convert environment variable key to nested configuration key"""
        # Common environment variable patterns
        key_mappings = {
            "REDIS_URL": "infrastructure.redis.url",
            "REDIS_PASSWORD": "infrastructure.redis.password",
            "REDIS_MAX_CONNECTIONS": "infrastructure.redis.max_connections",
            "QDRANT_API_KEY": "infrastructure.vector_db.qdrant.api_key",
            "QDRANT_URL": "infrastructure.vector_db.qdrant.url",
            "WEAVIATE_API_KEY": "infrastructure.vector_db.weaviate.api_key",
            "WEAVIATE_URL": "infrastructure.vector_db.weaviate.url",
            "OPENAI_API_KEY": "llm_providers.direct_keys.openai",
            "ANTHROPIC_API_KEY": "llm_providers.direct_keys.anthropic",
            "PORTKEY_API_KEY": "llm_providers.portkey.api_key",
            "MEM0_API_KEY": "infrastructure_providers.mem0.api_key",
            "N8N_API_KEY": "infrastructure_providers.n8n.api_key",
            "PULUMI_API_KEY": "pulumi.api_key",
        }
        # Direct mapping if exists
        if env_key in key_mappings:
            return key_mappings[env_key]
        # Generic conversion: lowercase and replace underscores with dots
        return env_key.lower().replace("_", ".")
    async def _enable_fallback_mode(self):
        """Enable fallback mode when ESC is unavailable"""
        self._fallback_mode = True
        logger.warning("Enabled fallback mode - using local configuration sources")
        # Ensure we have at least basic configuration from local sources
        await self._load_env_files()
        await self._load_environment_variables()
    async def _start_background_tasks(self):
        """Start background refresh and file watching tasks"""
        # Start auto-refresh task
        if self.auto_refresh:
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
        # Start file watchers
        if self.watch_files:
            for env_file in self.fallback_env_files:
                if Path(env_file).exists():
                    task = asyncio.create_task(self._watch_file(env_file))
                    self._file_watchers[env_file] = task
    async def _auto_refresh_loop(self):
        """Background task for automatic configuration refresh"""
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.refresh_config()
            except asyncio.CancelledError:
                logger.info("Auto-refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-refresh loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    async def _watch_file(self, file_path: str):
        """Watch a file for changes and reload configuration"""
        try:
            async for changes in awatch(file_path):
                logger.info(f"Configuration file changed: {file_path}")
                await self._load_single_env_file(file_path)
                await self._notify_config_change(f"file:{file_path}", "reload", None)
        except asyncio.CancelledError:
            logger.info(f"File watcher cancelled for {file_path}")
        except Exception as e:
            logger.error(f"Error watching file {file_path}: {e}")
    async def refresh_config(self, force: bool = False) -> bool:
        """Manually refresh configuration from all sources"""
        try:
            if not force and self.cache.is_valid():
                return True
            logger.info("Refreshing configuration from all sources")
            old_config = dict(self.cache.entries)
            # Reload from all sources
            await self._load_all_configurations()
            # Check for changes
            await self._detect_config_changes(old_config)
            return True
        except Exception as e:
            logger.error(f"Failed to refresh configuration: {e}")
            return False
    async def _detect_config_changes(self, old_config: Dict[str, ConfigEntry]):
        """Detect and notify about configuration changes"""
        for key, entry in self.cache.entries.items():
            old_entry = old_config.get(key)
            if not old_entry:
                # New configuration
                await self._notify_config_change(key, "added", entry.value)
            elif old_entry.value != entry.value:
                # Changed configuration
                await self._notify_config_change(key, "changed", entry.value, old_entry.value)
    async def _notify_config_change(
        self, key: str, change_type: str, new_value: Any, old_value: Any = None
    ):
        """Notify registered callbacks about configuration changes"""
        for callback in self._change_callbacks:
            try:
                callback(key, new_value, old_value)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        value = self.cache.get_config(key)
        return value if value is not None else default
    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation"""
        return self.get(key_path, default)
    async def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret configuration value (always fetched fresh)"""
        try:
            secret_value = await self.secrets_manager.get_secret(
                key, self.environment, use_cache=False
            )
            return secret_value if secret_value is not None else default
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return default
    def get_all(self, prefix: str = "") -> Dict[str, Any]:
        """Get all configuration values with optional prefix filter"""
        result = {}
        for key, entry in self.cache.entries.items():
            if not prefix or key.startswith(prefix):
                # Remove prefix from key if specified
                display_key = key[len(prefix) :].lstrip(".") if prefix else key
                result[display_key] = entry.value
        return result
    def get_by_source(self, source: ConfigSource) -> Dict[str, Any]:
        """Get all configuration values from a specific source"""
        return {
            key: entry.value for key, entry in self.cache.entries.items() if entry.source == source
        }
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """Add callback for configuration changes"""
        self._change_callbacks.append(callback)
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]):
        """Remove configuration change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    def get_config_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a configuration entry"""
        entry = self.cache.entries.get(key)
        if not entry:
            return None
        return {
            "key": entry.key,
            "value": entry.value if not entry.is_secret else "***REDACTED***",
            "source": entry.source.value,
            "priority": entry.priority.value,
            "last_updated": entry.last_updated.isoformat(),
            "is_secret": entry.is_secret,
            "description": entry.description,
            "tags": entry.tags,
        }
    def get_status(self) -> Dict[str, Any]:
        """Get loader status and statistics"""
        return {
            "initialized": self._initialization_complete,
            "fallback_mode": self._fallback_mode,
            "environment": self.environment,
            "total_entries": len(self.cache.entries),
            "cache_valid": self.cache.is_valid(),
            "last_refresh": (
                self.cache.last_refresh.isoformat() if self.cache.last_refresh else None
            ),
            "last_esc_sync": self._last_esc_sync.isoformat() if self._last_esc_sync else None,
            "auto_refresh": self.auto_refresh,
            "file_watchers": len(self._file_watchers),
            "sources_summary": self._get_sources_summary(),
        }
    def _get_sources_summary(self) -> Dict[str, int]:
        """Get summary of configuration entries by source"""
        summary = {}
        for entry in self.cache.entries.values():
            source = entry.source.value
            summary[source] = summary.get(source, 0) + 1
        return summary
    async def shutdown(self):
        """Shutdown the configuration loader and cleanup resources"""
        logger.info("Shutting down ESC Configuration Loader")
        # Cancel background tasks
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        # Cancel file watchers
        for task in self._file_watchers.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._file_watchers.clear()
        logger.info("ESC Configuration Loader shutdown complete")
