#!/usr/bin/env python3
"""
Unified Configuration Manager
Single source of truth for all configuration across Sophia Intelligence Platform
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConfigContext:
    """Configuration context for environment-aware loading"""

    environment: str = "development"
    service: Optional[str] = None
    override_path: Optional[str] = None


class UnifiedConfigManager:
    """Manages all configuration with hierarchy: base -> environment -> service -> overrides"""

    def __init__(self, config_root: Optional[str] = None):
        self.config_root = Path(config_root) if config_root else Path("config")
        self.cache = {}
        self._load_base_config()

    def _load_base_config(self):
        """Load base configuration"""
        base_path = self.config_root / "base.json"
        if base_path.exists():
            self.base_config = json.loads(base_path.read_text())
        else:
            self.base_config = {}

    def get_config(self, context: ConfigContext) -> dict[str, Any]:
        """Get configuration for given context with hierarchy"""

        cache_key = f"{context.environment}_{context.service}_{context.override_path}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Start with base configuration
        config = self.base_config.copy()

        # Layer environment-specific config
        env_config = self._load_environment_config(context.environment)
        config = self._merge_configs(config, env_config)

        # Layer service-specific config
        if context.service:
            service_config = self._load_service_config(context.service)
            config = self._merge_configs(config, service_config)

        # Layer integration configs
        integration_configs = self._load_integration_configs()
        config = self._merge_configs(config, integration_configs)

        # Layer environment variables
        env_vars = self._load_environment_variables()
        config = self._overlay_env_vars(config, env_vars)

        # Layer override config if provided
        if context.override_path:
            override_config = self._load_override_config(context.override_path)
            config = self._merge_configs(config, override_config)

        # Cache the result
        self.cache[cache_key] = config
        return config

    def _load_environment_config(self, environment: str) -> dict[str, Any]:
        """Load environment-specific configuration"""
        env_path = self.config_root / "environments" / f"{environment}.json"
        if env_path.exists():
            return json.loads(env_path.read_text())
        return {}

    def _load_service_config(self, service: str) -> dict[str, Any]:
        """Load service-specific configuration"""
        service_path = self.config_root / "services" / f"{service}.json"
        if service_path.exists():
            return json.loads(service_path.read_text())
        return {}

    def _load_integration_configs(self) -> dict[str, Any]:
        """Load all integration configurations"""
        integrations = {}
        integration_dir = self.config_root / "integrations"

        if integration_dir.exists():
            for integration_file in integration_dir.glob("*.json"):
                integration_name = integration_file.stem
                integrations[f"integrations_{integration_name}"] = json.loads(
                    integration_file.read_text()
                )

        return integrations

    def _load_environment_variables(self) -> dict[str, str]:
        """Load environment variables from .env files"""
        env_vars = {}

        # Load from secrets directory
        secrets_dir = self.config_root / "secrets"
        env_files = [".env.local", ".env"]

        for env_file in env_files:
            env_path = secrets_dir / env_file
            if env_path.exists():
                env_vars.update(self._parse_env_file(env_path))

        return env_vars

    def _parse_env_file(self, env_path: Path) -> dict[str, str]:
        """Parse .env file into dictionary"""
        env_vars = {}
        try:
            content = env_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"')
                    env_vars[key.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"Could not parse env file {env_path}: {e}")
        return env_vars

    def _load_override_config(self, override_path: str) -> dict[str, Any]:
        """Load override configuration from path"""
        override_file = Path(override_path)
        if override_file.exists():
            return json.loads(override_file.read_text())
        return {}

    def _merge_configs(
        self, base: dict[str, Any], overlay: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = base.copy()

        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _overlay_env_vars(
        self, config: dict[str, Any], env_vars: dict[str, str]
    ) -> dict[str, Any]:
        """Overlay environment variables onto configuration"""
        result = config.copy()

        # Map common environment variables to config paths
        env_mappings = {
            "SOPHIA_PORT": "defaults.ports.sophia",
            "ARTEMIS_PORT": "defaults.ports.artemis",
            "MCP_PORT": "defaults.ports.mcp",
            "LOG_LEVEL": "defaults.logging.level",
            "DEBUG": "debug",
        }

        for env_var, config_path in env_mappings.items():
            if env_var in env_vars:
                self._set_nested_value(result, config_path, env_vars[env_var])

        return result

    def _set_nested_value(self, config: dict[str, Any], path: str, value: str):
        """Set nested configuration value using dot notation path"""
        keys = path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Convert value to appropriate type
        final_key = keys[-1]
        if value.lower() in ("true", "false"):
            current[final_key] = value.lower() == "true"
        elif value.isdigit():
            current[final_key] = int(value)
        else:
            current[final_key] = value

    def get_service_config(
        self, service: str, environment: str = "development"
    ) -> dict[str, Any]:
        """Get configuration for a specific service"""
        context = ConfigContext(environment=environment, service=service)
        return self.get_config(context)

    def get_integration_config(
        self, integration: str, environment: str = "development"
    ) -> dict[str, Any]:
        """Get configuration for a specific integration"""
        context = ConfigContext(environment=environment)
        config = self.get_config(context)
        return config.get(f"integrations_{integration}", {})

    def refresh_cache(self):
        """Clear configuration cache to force reload"""
        self.cache.clear()
        self._load_base_config()


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> UnifiedConfigManager:
    """Get singleton configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigManager()
    return _config_manager


def get_config(service: str = None, environment: str = None) -> dict[str, Any]:
    """Convenience function to get configuration"""
    environment = environment or os.getenv("ENVIRONMENT", "development")
    context = ConfigContext(environment=environment, service=service)
    return get_config_manager().get_config(context)
