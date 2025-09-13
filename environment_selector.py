#!/usr/bin/env python3
"""
Environment Selection and Management System
Professional environment switching with Pulumi ESC integration
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class EnvironmentManager:
    """Professional environment selection and management system"""
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_dir = self.project_root / ".sophia" / "environments"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Environment configurations
        self.environments = {
            "production": {
                "pulumi_env": "sophia-ai/sophia-prod",
                "description": "Production environment with full AI provider suite",
                "domain": "api.sophia-intel.ai",
                "required_secrets": [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "LAMBDA_API_KEY",
                    "EXA_API_KEY",
                    "HUGGINGFACE_API_TOKEN",
                    "TOGETHER_AI_API_KEY",
                    "OPENROUTER_API_KEY",
                    "PORTKEY_API_KEY",
                    "PULUMI_ACCESS_TOKEN",
                    "ARIZE_SPACE_ID",
                    "ARIZE_API_KEY",
                    "APIFY_API_TOKEN",
                    "DOCKER_USER_NAME",
                    "DOCKER_PERSONAL_ACCESS_TOKEN",
                    "PHANTOM_BUSTER_API_KEY",
                    "TWINGLY_API_KEY",
                    "TAVILY_API_KEY",
                    "ZENROWS_API_KEY",
                ],
                "aliases": ["prod", "live"],
            },
            "staging": {
                "pulumi_env": "sophia-ai/sophia-staging",
                "description": "Staging environment for pre-production testing",
                "domain": "staging-api.sophia-intel.ai",
                "required_secrets": [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "LAMBDA_API_KEY",
                    "EXA_API_KEY",
                    "PULUMI_ACCESS_TOKEN",
                    "HUGGINGFACE_API_TOKEN",
                ],
                "aliases": ["stage", "test"],
            },
            "development": {
                "pulumi_env": "sophia-ai/sophia-dev",
                "description": "Development environment with minimal providers",
                "domain": "dev-api.sophia-intel.ai",
                "required_secrets": ["OPENAI_API_KEY", "LAMBDA_API_KEY", "EXA_API_KEY"],
                "aliases": ["dev", "local"],
            },
        }
        # Load current environment
        self.current_env = self._load_current_environment()
    def _load_current_environment(self) -> Optional[str]:
        """Load the currently active environment"""
        env_file = self.config_dir / "current_environment"
        if env_file.exists():
            try:
                return env_file.read_text().strip()
            except Exception:
                return None
        return None
    def _save_current_environment(self, environment: str):
        """Save the currently active environment"""
        env_file = self.config_dir / "current_environment"
        env_file.write_text(environment)
    def _resolve_environment_name(self, env_input: str) -> Optional[str]:
        """Resolve environment name from input (handles aliases)"""
        # Direct match
        if env_input in self.environments:
            return env_input
        # Check aliases
        for env_name, config in self.environments.items():
            if env_input in config.get("aliases", []):
                return env_name
        return None
    def list_environments(self) -> Dict:
        """List all available environments with their configurations"""
        env_list = []
        for env_name, config in self.environments.items():
            env_info = {
                "name": env_name,
                "description": config["description"],
                "domain": config["domain"],
                "pulumi_env": config["pulumi_env"],
                "secret_count": len(config["required_secrets"]),
                "aliases": config.get("aliases", []),
                "is_current": env_name == self.current_env,
            }
            env_list.append(env_info)
        return {
            "environments": env_list,
            "current_environment": self.current_env,
            "total_environments": len(env_list),
        }
    def switch_environment(self, environment: str, validate: bool = True) -> Dict:
        """Switch to specified environment with optional validation"""
        # Resolve environment name
        env_name = self._resolve_environment_name(environment)
        if not env_name:
            return {
                "status": "error",
                "message": f"Unknown environment: {environment}",
                "available_environments": list(self.environments.keys()),
            }
        env_config = self.environments[env_name]
        logger.info(f"🔄 Switching to {env_name} environment")
        try:
            # Load environment from Pulumi ESC
            load_result = self._load_pulumi_environment(env_config["pulumi_env"])
            if load_result["status"] == "success":
                # Save as current environment
                self._save_current_environment(env_name)
                self.current_env = env_name
                # Validate if requested
                validation_result = None
                if validate:
                    validation_result = self._validate_environment_secrets(env_name)
                # Create shell aliases
                self._create_environment_aliases(env_name)
                logger.info(f"✅ Successfully switched to {env_name}")
                return {
                    "status": "success",
                    "environment": env_name,
                    "description": env_config["description"],
                    "domain": env_config["domain"],
                    "loaded_secrets": load_result.get("loaded_secrets", []),
                    "validation": validation_result,
                    "aliases_created": True,
                }
            else:
                logger.error(f"❌ Failed to load {env_name} environment")
                return {
                    "status": "failed",
                    "environment": env_name,
                    "error": load_result.get("error", "Unknown error"),
                    "fallback_available": True,
                }
        except Exception as e:
            logger.error(f"❌ Error switching to {env_name}: {e}")
            return {"status": "error", "environment": env_name, "error": str(e)}
    def _load_pulumi_environment(self, pulumi_env: str) -> Dict:
        """Load environment from Pulumi ESC"""
        try:
            # Check if Pulumi is available
            result = subprocess.run(["which", "pulumi"], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "status": "pulumi_not_found",
                    "error": "Pulumi CLI not found. Install with: curl -fsSL https://get.pulumi.com | sh",
                }
            # Load environment
            result = subprocess.run(
                ["pulumi", "env", "open", pulumi_env, "--format", "shell"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Parse and set environment variables
                env_lines = result.stdout.strip().split("\\n")
                loaded_secrets = []
                for line in env_lines:
                    if line.startswith("export "):
                        # Parse export statement
                        export_part = line[7:]  # Remove 'export '
                        if "=" in export_part:
                            key, value = export_part.split("=", 1)
                            # Remove quotes if present
                            value = value.strip("\"'")  # Remove quotes
                            os.environ[key] = value
                            loaded_secrets.append(key)
                return {
                    "status": "success",
                    "pulumi_environment": pulumi_env,
                    "loaded_secrets": loaded_secrets,
                    "secret_count": len(loaded_secrets),
                }
            else:
                return {
                    "status": "failed",
                    "error": result.stderr.strip(),
                    "pulumi_environment": pulumi_env,
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Pulumi ESC request timed out",
                "pulumi_environment": pulumi_env,
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "pulumi_environment": pulumi_env}
    def _validate_environment_secrets(self, environment: str) -> Dict:
        """Validate that all required secrets are available"""
        env_config = self.environments[environment]
        required_secrets = env_config["required_secrets"]
        missing = []
        present = []
        for secret in required_secrets:
            if os.getenv(secret):
                present.append(secret)
            else:
                missing.append(secret)
        coverage = (len(present) / len(required_secrets)) * 100 if required_secrets else 100
        return {
            "total_secrets": len(required_secrets),
            "present_secrets": len(present),
            "missing_secrets": missing,
            "coverage_percentage": round(coverage, 1),
            "status": "healthy" if not missing else "incomplete",
        }
    def _create_environment_aliases(self, environment: str):
        """Create convenient shell aliases for the current environment"""
        env_config = self.environments[environment]
        # Create alias script
        alias_script = self.config_dir / f"{environment}_aliases.sh"
        aliases = f"""#!/bin/bash
# Sophia AI Platform - {environment.title()} Environment Aliases
# Generated: {datetime.now().isoformat()}
# Environment management
alias sophia-env="echo 'Current environment: {environment}'"
alias sophia-switch="python3 {self.project_root}/environment_selector.py switch"
alias sophia-list="python3 {self.project_root}/environment_selector.py list"
# Environment-specific operations
alias sophia-deploy-{environment}="./deploy-production.sh --env {environment}"
alias sophia-validate-{environment}="python3 enhanced_secret_manager.py --env {environment}"
alias sophia-status-{environment}="./sophia.sh status --env {environment}"
# Quick environment switching
alias sophia-prod="python3 {self.project_root}/environment_selector.py switch production"
alias sophia-staging="python3 {self.project_root}/environment_selector.py switch staging"
alias sophia-dev="python3 {self.project_root}/environment_selector.py switch development"
# API endpoints for current environment
export SOPHIA_API_BASE="https://{env_config['domain']}/v1"
export SOPHIA_ENVIRONMENT="{environment}"
# Convenient functions
sophia-env() {{
    local env=${{1:-{environment}}}
    python3 {self.project_root}/environment_selector.py switch "$env"
}}
sophia-secrets() {{
    python3 {self.project_root}/enhanced_secret_manager.py validate --env {environment}
}}
sophia-health() {{
    curl -s "https://{env_config['domain']}/v1/health" | jq .
}}
echo "✅ Sophia AI Platform - {environment.title()} environment loaded"
echo "🌐 API Base: https://{env_config['domain']}/v1"
echo "📋 Use 'sophia-env' to check current environment"
"""
        alias_script.write_text(aliases)
        alias_script.chmod(0o755)
        # Source the aliases in current shell (if possible)
        try:
            subprocess.run(["source", str(alias_script)], shell=True)
        except Exception:
            pass  # Silently fail if sourcing doesn't work
    def get_environment_status(self, environment: Optional[str] = None) -> Dict:
        """Get detailed status of specified environment or current environment"""
        env_name = environment or self.current_env
        if not env_name:
            return {"status": "no_environment", "message": "No environment currently selected"}
        if env_name not in self.environments:
            return {"status": "invalid_environment", "message": f"Unknown environment: {env_name}"}
        env_config = self.environments[env_name]
        # Get secret validation
        validation = self._validate_environment_secrets(env_name)
        # Check Pulumi ESC connectivity
        pulumi_status = self._check_pulumi_connectivity(env_config["pulumi_env"])
        # Get environment variables
        env_vars = {
            key: "***" if os.getenv(key) else None for key in env_config["required_secrets"]
        }
        return {
            "environment": env_name,
            "description": env_config["description"],
            "domain": env_config["domain"],
            "pulumi_environment": env_config["pulumi_env"],
            "is_current": env_name == self.current_env,
            "secret_validation": validation,
            "pulumi_connectivity": pulumi_status,
            "environment_variables": env_vars,
            "aliases": env_config.get("aliases", []),
            "last_updated": datetime.now().isoformat(),
        }
    def _check_pulumi_connectivity(self, pulumi_env: str) -> Dict:
        """Check connectivity to Pulumi ESC environment"""
        try:
            result = subprocess.run(
                ["pulumi", "env", "get", pulumi_env], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return {"status": "connected", "message": "Pulumi ESC environment accessible"}
            else:
                return {"status": "error", "message": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Pulumi ESC request timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    def create_environment_backup(self, environment: str) -> Dict:
        """Create backup of environment configuration and secrets"""
        env_name = self._resolve_environment_name(environment)
        if not env_name:
            return {"status": "error", "message": f"Unknown environment: {environment}"}
        backup_dir = self.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{env_name}_backup_{timestamp}.json"
        # Get environment status
        env_status = self.get_environment_status(env_name)
        # Create backup data
        backup_data = {
            "environment": env_name,
            "backup_timestamp": datetime.now().isoformat(),
            "configuration": self.environments[env_name],
            "status": env_status,
            "backup_version": "1.0",
        }
        # Save backup
        backup_file.write_text(json.dumps(backup_data, indent=2))
        return {
            "status": "success",
            "environment": env_name,
            "backup_file": str(backup_file),
            "backup_size": backup_file.stat().st_size,
            "timestamp": timestamp,
        }
    def setup_environment_monitoring(self) -> Dict:
        """Setup monitoring for environment health and secret validation"""
        monitoring_script = self.config_dir / "environment_monitor.sh"
        monitor_content = f"""#!/bin/bash
# Sophia AI Platform - Environment Monitoring
# Monitors environment health and secret validation
SOPHIA_ROOT="{self.project_root}"
LOG_FILE="{self.config_dir}/environment_monitor.log"
log_message() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}}
# Monitor current environment
current_env=$(cat "{self.config_dir}/current_environment" 2>/dev/null || echo "none")
if [ "$current_env" != "none" ]; then
    log_message "Monitoring environment: $current_env"
    # Validate secrets
    python3 "$SOPHIA_ROOT/enhanced_secret_manager.py" validate --env "$current_env" --quiet >> "$LOG_FILE" 2>&1
    # Check environment status
    python3 "$SOPHIA_ROOT/environment_selector.py" status "$current_env" --quiet >> "$LOG_FILE" 2>&1
    log_message "Environment monitoring complete"
else
    log_message "No environment currently selected"
fi
"""
        monitoring_script.write_text(monitor_content)
        monitoring_script.chmod(0o755)
        return {
            "status": "success",
            "monitoring_script": str(monitoring_script),
            "log_file": str(self.config_dir / "environment_monitor.log"),
            "setup_complete": True,
        }
def main():
    """Main CLI interface for environment management"""
    parser = argparse.ArgumentParser(description="Sophia AI Platform - Environment Management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    # List environments
    list_parser = subparsers.add_parser("list", help="List all environments")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")
    # Switch environment
    switch_parser = subparsers.add_parser("switch", help="Switch to environment")
    switch_parser.add_argument("environment", help="Environment name or alias")
    switch_parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    # Environment status
    status_parser = subparsers.add_parser("status", help="Get environment status")
    status_parser.add_argument("environment", nargs="?", help="Environment name (default: current)")
    status_parser.add_argument("--quiet", action="store_true", help="Quiet output")
    # Backup environment
    backup_parser = subparsers.add_parser("backup", help="Backup environment")
    backup_parser.add_argument("environment", help="Environment name")
    # Setup monitoring
    monitor_parser = subparsers.add_parser("monitor", help="Setup environment monitoring")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    manager = EnvironmentManager()
    if args.command == "list":
        result = manager.list_environments()
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print("🌍 Sophia AI Platform - Available Environments")
            print("=" * 60)
            for env in result["environments"]:
                current_marker = " (CURRENT)" if env["is_current"] else ""
                print(f"📋 {env['name'].upper()}{current_marker}")
                print(f"   Description: {env['description']}")
                print(f"   Domain: {env['domain']}")
                print(f"   Secrets: {env['secret_count']}")
                print(f"   Aliases: {', '.join(env['aliases'])}")
                print()
    elif args.command == "switch":
        validate = not args.no_validate
        result = manager.switch_environment(args.environment, validate=validate)
        if result["status"] == "success":
            print(f"✅ Switched to {result['environment']} environment")
            print(f"🌐 API Base: https://{result['domain']}/v1")
            print(f"📦 Loaded {len(result['loaded_secrets'])} secrets")
            if result.get("validation"):
                val = result["validation"]
                print(f"🔍 Validation: {val['coverage_percentage']:.1f}% coverage")
        else:
            print(f"❌ Failed to switch environment: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    elif args.command == "status":
        result = manager.get_environment_status(args.environment)
        if not args.quiet:
            if result.get("status") in ["no_environment", "invalid_environment"]:
                print(f"❌ {result['message']}")
                sys.exit(1)
            print(f"🌍 Environment Status: {result['environment'].upper()}")
            print("=" * 50)
            print(f"Description: {result['description']}")
            print(f"Domain: {result['domain']}")
            print(f"Pulumi Environment: {result['pulumi_environment']}")
            val = result["secret_validation"]
            print(
                f"Secret Coverage: {val['coverage_percentage']:.1f}% ({val['present_secrets']}/{val['total_secrets']})"
            )
            if val["missing_secrets"]:
                print(f"Missing Secrets: {', '.join(val['missing_secrets'])}")
            pulumi = result["pulumi_connectivity"]
            print(f"Pulumi ESC: {pulumi['status']}")
        # Exit with appropriate code
        if result.get("secret_validation", {}).get("status") == "healthy":
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.command == "backup":
        result = manager.create_environment_backup(args.environment)
        if result["status"] == "success":
            print(f"✅ Environment backup created: {result['backup_file']}")
            print(f"📦 Backup size: {result['backup_size']} bytes")
        else:
            print(f"❌ Backup failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)
    elif args.command == "monitor":
        result = manager.setup_environment_monitoring()
        if result["status"] == "success":
            print("✅ Environment monitoring setup complete")
            print(f"📊 Monitoring script: {result['monitoring_script']}")
            print(f"📝 Log file: {result['log_file']}")
        else:
            print("❌ Monitoring setup failed")
            sys.exit(1)
if __name__ == "__main__":
    main()
