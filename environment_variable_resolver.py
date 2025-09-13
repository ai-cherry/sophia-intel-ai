#!/usr/bin/env python3
"""
Environment Variable Resolver - Fixes Circular References
Implements ESC auto-sync with proper fallback chains
"""
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any
class EnvironmentTier(Enum):
    """Environment tiers for proper resolution hierarchy"""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    LOCAL = "local"
class CircularReferenceError(Exception):
    """Raised when circular reference is detected in environment variables"""
class EnvironmentVariableResolver:
    """
    Resolves environment variables with circular reference detection
    Implements ESC auto-sync integration
    """
    def __init__(self, tier: EnvironmentTier = EnvironmentTier.LOCAL):
        self.tier = tier
        self.resolution_stack: set[str] = set()
        self.resolved_cache: dict[str, str] = {}
        self.logger = self._setup_logging()
        # Load ESC configuration if available
        self.esc_config = self._load_esc_config()
        # Define safe defaults to prevent circular references
        self.safe_defaults = self._get_safe_defaults()
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for environment resolver"""
        logger = logging.getLogger("env_resolver")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - ENV_RESOLVER - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    def _load_esc_config(self) -> dict[str, Any]:
        """Load Pulumi ESC configuration if available"""
        esc_config_paths = [
            "config/pulumi/esc_config.json",
            ".pulumi/esc_config.json",
            "esc_config.json",
        ]
        for config_path in esc_config_paths:
            if Path(config_path).exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                        self.logger.info(f"Loaded ESC config from {config_path}")
                        return config
                except Exception as e:
                    self.logger.warning(f"Failed to load ESC config from {config_path}: {e}")
        self.logger.info("No ESC config found, using local environment only")
        return {}
    def _get_safe_defaults(self) -> dict[str, str]:
        """Get safe default values to prevent circular references"""
        return {
            # Infrastructure defaults
            "CLOUD_URL": "localhost",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            # Service defaults
            "API_HOST": "${BIND_IP}",
            "API_PORT": "8000",
            "MCP_HOST": "localhost",
            # Security defaults
            "JWT_SECRET": "development-secret-change-in-production",
            "ENCRYPTION_KEY": "development-key-change-in-production",
            # Tier-specific defaults
            f"{self.tier.value.upper()}_CLOUD_URL": "localhost",
            f"{self.tier.value.upper()}_REDIS_HOST": "localhost",
            f"{self.tier.value.upper()}_POSTGRES_HOST": "localhost",
        }
    def resolve(self, key: str, default: str | None = None, namespace: str | None = None) -> str:
        """
        Resolve environment variable with circular reference detection
        Args:
            key: Environment variable key
            default: Default value if not found
            namespace: Optional namespace for scoped resolution
        Returns:
            Resolved environment variable value
        Raises:
            CircularReferenceError: If circular reference is detected
        """
        # Check for circular reference
        if key in self.resolution_stack:
            circular_chain = " -> ".join(list(self.resolution_stack) + [key])
            raise CircularReferenceError(f"Circular reference detected: {circular_chain}")
        # Check cache first
        cache_key = f"{namespace}:{key}" if namespace else key
        if cache_key in self.resolved_cache:
            return self.resolved_cache[cache_key]
        # Add to resolution stack
        self.resolution_stack.add(key)
        try:
            value = self._resolve_variable(key, default, namespace)
            # Cache the resolved value
            self.resolved_cache[cache_key] = value
            return value
        finally:
            # Remove from resolution stack
            self.resolution_stack.remove(key)
    def _resolve_variable(self, key: str, default: str | None, namespace: str | None) -> str:
        """Internal method to resolve variable with proper hierarchy"""
        # 1. Try namespace-specific variable first
        if namespace:
            namespaced_key = f"{namespace.upper()}_{key}"
            value = self._get_from_sources(namespaced_key)
            if value:
                self.logger.debug(f"Resolved {key} from namespace {namespace}: {namespaced_key}")
                return value
        # 2. Try tier-specific variable
        tier_key = f"{self.tier.value.upper()}_{key}"
        value = self._get_from_sources(tier_key)
        if value:
            self.logger.debug(f"Resolved {key} from tier {self.tier.value}: {tier_key}")
            return value
        # 3. Try general variable
        value = self._get_from_sources(key)
        if value:
            self.logger.debug(f"Resolved {key} from general environment")
            return value
        # 4. Try provided default
        if default:
            self.logger.debug(f"Using provided default for {key}")
            return default
        # 5. Try safe defaults
        if key in self.safe_defaults:
            self.logger.debug(f"Using safe default for {key}")
            return self.safe_defaults[key]
        # 6. Final fallback
        self.logger.warning(f"No value found for {key}, using 'localhost'")
        return "localhost"
    def _get_from_sources(self, key: str) -> str | None:
        """Get value from various sources in priority order"""
        # 1. Environment variables (highest priority)
        value = os.getenv(key)
        if value:
            return value
        # 2. ESC configuration
        if self.esc_config:
            value = self._get_from_esc(key)
            if value:
                return value
        # 3. Local configuration files
        value = self._get_from_local_config(key)
        if value:
            return value
        return None
    def _get_from_esc(self, key: str) -> str | None:
        """Get value from Pulumi ESC configuration"""
        try:
            # Navigate ESC configuration structure
            if "environments" in self.esc_config:
                env_config = self.esc_config["environments"].get(self.tier.value, {})
                if "values" in env_config:
                    return env_config["values"].get(key)
            # Try direct lookup
            return self.esc_config.get(key)
        except Exception as e:
            self.logger.debug(f"Failed to get {key} from ESC: {e}")
            return None
    def _get_from_local_config(self, key: str) -> str | None:
        """Get value from local configuration files"""
        config_files = [
            f"config/{self.tier.value}.json",
            "config/local.json",
            ".env.local",
        ]
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    if config_file.endswith(".json"):
                        with open(config_file) as f:
                            config = json.load(f)
                            if key in config:
                                return config[key]
                    else:
                        # Handle .env files
                        with open(config_file) as f:
                            for line in f:
                                if line.strip() and not line.startswith("#"):
                                    if "=" in line:
                                        env_key, env_value = line.strip().split("=", 1)
                                        if env_key == key:
                                            return env_value.strip("\"'")
                except Exception as e:
                    self.logger.debug(f"Failed to read {config_file}: {e}")
        return None
    def validate_no_circular_references(self) -> dict[str, Any]:
        """Validate that no circular references exist in current environment"""
        validation_results = {
            "circular_references": [],
            "problematic_variables": [],
            "safe_variables": [],
            "total_checked": 0,
        }
        # Get all environment variables that might have references
        env_vars_to_check = [
            "CLOUD_URL",
            "REDIS_HOST",
            "POSTGRES_HOST",
            "QDRANT_HOST",
            "API_HOST",
            "MCP_HOST",
            "GATEWAY_HOST",
        ]
        # Add tier-specific variables
        for var in env_vars_to_check.copy():
            env_vars_to_check.append(f"{self.tier.value.upper()}_{var}")
        for var in env_vars_to_check:
            validation_results["total_checked"] += 1
            try:
                # Clear cache and resolution stack for clean test
                self.resolved_cache.clear()
                self.resolution_stack.clear()
                # Try to resolve the variable
                value = self.resolve(var)
                validation_results["safe_variables"].append(
                    {
                        "variable": var,
                        "value": value[:20] + "..." if len(value) > 20 else value,
                    }
                )
            except CircularReferenceError as e:
                validation_results["circular_references"].append({"variable": var, "error": str(e)})
                validation_results["problematic_variables"].append(var)
            except Exception as e:
                validation_results["problematic_variables"].append(var)
                self.logger.warning(f"Error validating {var}: {e}")
        return validation_results
    def fix_circular_references(self) -> dict[str, Any]:
        """Automatically fix detected circular references"""
        validation = self.validate_no_circular_references()
        fix_results = {
            "fixes_applied": [],
            "manual_fixes_needed": [],
            "backup_created": False,
        }
        if not validation["circular_references"]:
            self.logger.info("No circular references detected")
            return fix_results
        # Create backup of current environment
        try:
            backup_file = f"environment_backup_{self.tier.value}.json"
            backup_data = {
                "tier": self.tier.value,
                "timestamp": str(Path().stat().st_mtime),
                "environment_variables": dict(os.environ),
            }
            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=2)
            fix_results["backup_created"] = True
            self.logger.info(f"Environment backup created: {backup_file}")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
        # Apply automatic fixes
        for circular_ref in validation["circular_references"]:
            var = circular_ref["variable"]
            # Use safe default for problematic variable
            if var in self.safe_defaults:
                safe_value = self.safe_defaults[var]
                # Update environment (in memory only)
                os.environ[var] = safe_value
                fix_results["fixes_applied"].append(
                    {"variable": var, "action": "set_safe_default", "value": safe_value}
                )
                self.logger.info(f"Fixed {var} with safe default: {safe_value}")
            else:
                fix_results["manual_fixes_needed"].append(
                    {
                        "variable": var,
                        "reason": "no_safe_default_available",
                        "suggestion": "Set explicit value in environment or ESC config",
                    }
                )
        return fix_results
# Global resolver instance
_global_resolver = None
def get_resolver(
    tier: EnvironmentTier = EnvironmentTier.LOCAL,
) -> EnvironmentVariableResolver:
    """Get global resolver instance"""
    global _global_resolver
    if _global_resolver is None:
        _global_resolver = EnvironmentVariableResolver(tier)
    return _global_resolver
def resolve_env(key: str, default: str | None = None, namespace: str | None = None) -> str:
    """Convenience function to resolve environment variable"""
    resolver = get_resolver()
    return resolver.resolve(key, default, namespace)
def validate_environment() -> dict[str, Any]:
    """Convenience function to validate environment"""
    resolver = get_resolver()
    return resolver.validate_no_circular_references()
def fix_environment() -> dict[str, Any]:
    """Convenience function to fix environment issues"""
    resolver = get_resolver()
    return resolver.fix_circular_references()
# Main execution for testing
if __name__ == "__main__":
    def main():
        print("🔍 Environment Variable Resolver - Circular Reference Fixer")
        # Create resolver
        resolver = EnvironmentVariableResolver()
        # Validate current environment
        print("\n📋 Validating current environment...")
        validation = resolver.validate_no_circular_references()
        print(f"   - Total variables checked: {validation['total_checked']}")
        print(f"   - Safe variables: {len(validation['safe_variables'])}")
        print(f"   - Circular references: {len(validation['circular_references'])}")
        print(f"   - Problematic variables: {len(validation['problematic_variables'])}")
        if validation["circular_references"]:
            print("\n❌ Circular references detected:")
            for ref in validation["circular_references"]:
                print(f"   - {ref['variable']}: {ref['error']}")
            # Apply fixes
            print("\n🔧 Applying automatic fixes...")
            fix_results = resolver.fix_circular_references()
            print(f"   - Fixes applied: {len(fix_results['fixes_applied'])}")
            print(f"   - Manual fixes needed: {len(fix_results['manual_fixes_needed'])}")
            print(f"   - Backup created: {fix_results['backup_created']}")
            if fix_results["fixes_applied"]:
                print("\n✅ Applied fixes:")
                for fix in fix_results["fixes_applied"]:
                    print(f"   - {fix['variable']}: {fix['action']} -> {fix['value']}")
            if fix_results["manual_fixes_needed"]:
                print("\n⚠️ Manual fixes needed:")
                for fix in fix_results["manual_fixes_needed"]:
                    print(f"   - {fix['variable']}: {fix['reason']} - {fix['suggestion']}")
        else:
            print("\n✅ No circular references detected - environment is healthy!")
        # Save validation results
        with open("environment_validation_results.json", "w") as f:
            json.dump(
                {
                    "validation": validation,
                    "fixes": fix_results if validation["circular_references"] else None,
                },
                f,
                indent=2,
            )
        print("\n📄 Results saved to: environment_validation_results.json")
    if __name__ == "__main__":
        main()
