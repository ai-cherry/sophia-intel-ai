#!/usr/bin/env python3
"""
Sophia Intel AI Configuration Manager
Handles environment-based configuration loading and validation
"""

import os
import sys
import yaml
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import jinja2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Platform(Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    LAUNCHD = "launchd"


@dataclass
class ConfigurationContext:
    environment: Environment
    platform: Platform
    profile: str
    project_root: Path
    config_dir: Path
    templates_dir: Path
    output_dir: Path


class ConfigurationManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.automation_dir = self.project_root / "automation"
        self.config_dir = self.automation_dir / "config"
        self.templates_dir = self.automation_dir / "templates"
        self.output_dir = self.automation_dir / "generated"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load system configuration
        self.system_config = self._load_system_config()
        
        # Setup Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration from YAML"""
        config_file = self.config_dir / "system.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"System configuration not found: {config_file}")
            
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _detect_environment(self) -> Environment:
        """Auto-detect environment based on system indicators"""
        # Check environment variables
        env_name = os.getenv('SOPHIA_ENVIRONMENT', '').lower()
        if env_name in [e.value for e in Environment]:
            return Environment(env_name)
        
        # Check Kubernetes
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            return Environment.PRODUCTION
            
        # Check if running as root
        if os.getuid() == 0:
            return Environment.PRODUCTION
            
        # Check for staging indicators
        if 'staging' in os.getenv('HOSTNAME', '').lower():
            return Environment.STAGING
            
        # Default to development
        return Environment.DEVELOPMENT
    
    def _detect_platform(self) -> Platform:
        """Auto-detect platform based on system indicators"""
        # Check environment variables
        platform_name = os.getenv('SOPHIA_PLATFORM', '').lower()
        if platform_name in [p.value for p in Platform]:
            return Platform(platform_name)
            
        # Check Kubernetes
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            return Platform.KUBERNETES
            
        # Check Docker
        if os.path.exists('/.dockerenv') or os.getenv('DOCKER_HOST'):
            return Platform.DOCKER
            
        # Check systemd
        if Path('/etc/systemd/system').exists() and os.name == 'posix':
            return Platform.SYSTEMD
            
        # Check launchd (macOS)
        if Path('/Library/LaunchDaemons').exists() and sys.platform == 'darwin':
            return Platform.LAUNCHD
            
        # Default to docker
        return Platform.DOCKER
    
    def get_configuration(self, 
                         environment: Optional[Environment] = None,
                         platform: Optional[Platform] = None,
                         profile: Optional[str] = None) -> Dict[str, Any]:
        """Get complete configuration for environment and platform"""
        
        # Auto-detect if not specified
        env = environment or self._detect_environment()
        plat = platform or self._detect_platform()
        prof = profile or env.value
        
        logger.info(f"Loading configuration for {env.value}/{plat.value}/{prof}")
        
        # Start with base configuration
        config = self.system_config.copy()
        
        # Apply profile settings
        if prof in config.get('profiles', {}):
            profile_config = config['profiles'][prof]
            config = self._merge_configs(config, {'profile': profile_config})
        
        # Apply environment overrides
        if env.value in config.get('environment_overrides', {}):
            overrides = config['environment_overrides'][env.value]
            config = self._merge_configs(config, overrides)
            
        # Apply platform-specific settings
        if plat.value in config.get('platforms', {}):
            platform_config = config['platforms'][plat.value]
            config = self._merge_configs(config, {'platform': platform_config})
        
        # Add computed values
        config['computed'] = {
            'environment': env.value,
            'platform': plat.value,
            'profile': prof,
            'project_root': str(self.project_root),
            'config_dir': str(self.config_dir),
            'output_dir': str(self.output_dir),
            'timestamp': self._get_timestamp(),
            'hostname': os.getenv('HOSTNAME', 'localhost'),
            'namespace': config['platforms'].get(plat.value, {}).get('namespace', 'sophia-intel-ai')
        }
        
        return config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def load_environment_file(self, environment: Environment) -> Dict[str, str]:
        """Load environment-specific .env file"""
        env_file = self.project_root / f".env.{environment.value}"
        
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment file: {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
            
        # Return all environment variables
        return dict(os.environ)
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required sections
        required_sections = ['global', 'profiles', 'service_templates']
        for section in required_sections:
            if section not in config:
                issues.append(f"Missing required section: {section}")
        
        # Check environment profile exists
        env = config.get('computed', {}).get('environment')
        if env and env not in config.get('profiles', {}):
            issues.append(f"Environment profile '{env}' not found in configuration")
        
        # Check platform configuration
        platform = config.get('computed', {}).get('platform')
        if platform and platform not in config.get('platforms', {}):
            issues.append(f"Platform '{platform}' not found in configuration")
        
        # Validate service templates
        service_templates = config.get('service_templates', {})
        for category, services in service_templates.items():
            if not isinstance(services, dict):
                issues.append(f"Service template category '{category}' must be a dictionary")
                continue
                
            for service_name, service_config in services.items():
                if not isinstance(service_config, dict):
                    issues.append(f"Service '{service_name}' configuration must be a dictionary")
                    
                # Check required service fields
                required_fields = ['port']
                for field in required_fields:
                    if field not in service_config:
                        issues.append(f"Service '{service_name}' missing required field: {field}")
        
        # Validate resource limits
        profile_config = config.get('profile', {})
        resource_limits = profile_config.get('resource_limits', {})
        if resource_limits:
            for resource in ['cpu', 'memory']:
                if resource not in resource_limits:
                    issues.append(f"Resource limit '{resource}' not specified for profile")
        
        return issues
    
    def generate_configurations(self, 
                              environment: Optional[Environment] = None,
                              platform: Optional[Platform] = None,
                              profile: Optional[str] = None) -> Dict[str, Path]:
        """Generate all configuration files for the specified environment/platform"""
        
        # Get configuration
        config = self.get_configuration(environment, platform, profile)
        
        # Validate configuration
        issues = self.validate_configuration(config)
        if issues:
            for issue in issues:
                logger.error(f"Configuration validation error: {issue}")
            raise ValueError(f"Configuration validation failed with {len(issues)} issues")
        
        # Load environment variables
        env = Environment(config['computed']['environment'])
        env_vars = self.load_environment_file(env)
        config['env'] = env_vars
        
        # Generate files
        generated_files = {}
        
        # Platform-specific configurations
        plat = Platform(config['computed']['platform'])
        
        if plat == Platform.DOCKER:
            generated_files.update(self._generate_docker_configs(config))
        elif plat == Platform.KUBERNETES:
            generated_files.update(self._generate_k8s_configs(config))
        elif plat == Platform.SYSTEMD:
            generated_files.update(self._generate_systemd_configs(config))
        elif plat == Platform.LAUNCHD:
            generated_files.update(self._generate_launchd_configs(config))
        
        # Common configurations
        generated_files.update(self._generate_monitoring_configs(config))
        generated_files.update(self._generate_env_files(config))
        
        logger.info(f"Generated {len(generated_files)} configuration files")
        return generated_files
    
    def _generate_docker_configs(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate Docker Compose configurations"""
        files = {}
        
        # Generate docker-compose.yml
        template = self.jinja_env.get_template('docker-compose.yml.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'docker-compose.yml'
        with open(output_file, 'w') as f:
            f.write(content)
        files['docker-compose'] = output_file
        
        return files
    
    def _generate_k8s_configs(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate Kubernetes manifests"""
        files = {}
        
        # Generate namespace
        template = self.jinja_env.get_template('kubernetes/namespace.yml.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'namespace.yml'
        with open(output_file, 'w') as f:
            f.write(content)
        files['namespace'] = output_file
        
        # Generate deployments
        template = self.jinja_env.get_template('kubernetes/deployments.yml.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'deployments.yml'
        with open(output_file, 'w') as f:
            f.write(content)
        files['deployments'] = output_file
        
        return files
    
    def _generate_systemd_configs(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate systemd service files"""
        files = {}
        
        template = self.jinja_env.get_template('systemd/sophia-intel-ai.service.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'sophia-intel-ai.service'
        with open(output_file, 'w') as f:
            f.write(content)
        files['systemd-service'] = output_file
        
        return files
    
    def _generate_launchd_configs(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate launchd plist files"""
        files = {}
        
        template = self.jinja_env.get_template('launchd/com.sophia.intel.ai.plist.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'com.sophia.intel.ai.plist'
        with open(output_file, 'w') as f:
            f.write(content)
        files['launchd-plist'] = output_file
        
        return files
    
    def _generate_monitoring_configs(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate monitoring configurations"""
        files = {}
        
        # Prometheus config
        template = self.jinja_env.get_template('monitoring/prometheus.yml.j2')
        content = template.render(config=config)
        
        output_file = self.output_dir / 'prometheus.yml'
        with open(output_file, 'w') as f:
            f.write(content)
        files['prometheus-config'] = output_file
        
        return files
    
    def _generate_env_files(self, config: Dict[str, Any]) -> Dict[str, Path]:
        """Generate environment files"""
        files = {}
        
        # Generate .env file for current environment
        env_content = []
        
        # Basic settings
        env_content.append(f"SOPHIA_ENVIRONMENT={config['computed']['environment']}")
        env_content.append(f"SOPHIA_PLATFORM={config['computed']['platform']}")
        env_content.append(f"LOG_LEVEL={config.get('profile', {}).get('log_level', 'INFO')}")
        
        # Service URLs
        namespace = config['computed']['namespace']
        if config['computed']['platform'] == 'kubernetes':
            env_content.append(f"REDIS_URL=redis://redis-service.{namespace}.svc.cluster.local:6379")
            env_content.append(f"POSTGRES_URL=postgresql://sophia:${{POSTGRES_PASSWORD}}@postgres-service.{namespace}.svc.cluster.local:5432/sophia")
            env_content.append(f"WEAVIATE_URL=http://weaviate-service.{namespace}.svc.cluster.local:8080")
        else:
            env_content.append("REDIS_URL=redis://localhost:6380")
            env_content.append("POSTGRES_URL=postgresql://sophia:${POSTGRES_PASSWORD}@localhost:5432/sophia")
            env_content.append("WEAVIATE_URL=http://localhost:8081")
        
        output_file = self.output_dir / f'.env.{config["computed"]["environment"]}'
        with open(output_file, 'w') as f:
            f.write('\n'.join(env_content))
        files['env-file'] = output_file
        
        return files
    
    def export_config(self, 
                     output_format: str = "yaml",
                     environment: Optional[Environment] = None,
                     platform: Optional[Platform] = None,
                     profile: Optional[str] = None) -> str:
        """Export configuration in specified format"""
        
        config = self.get_configuration(environment, platform, profile)
        
        if output_format.lower() == "json":
            return json.dumps(config, indent=2, default=str)
        elif output_format.lower() == "yaml":
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")


def main():
    parser = argparse.ArgumentParser(description="Sophia Intel AI Configuration Manager")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--environment", choices=[e.value for e in Environment], help="Environment")
    parser.add_argument("--platform", choices=[p.value for p in Platform], help="Platform")
    parser.add_argument("--profile", help="Configuration profile")
    parser.add_argument("--action", choices=["validate", "generate", "export"], default="validate", help="Action to perform")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize configuration manager
        config_manager = ConfigurationManager(args.project_root)
        
        # Parse optional enums
        environment = Environment(args.environment) if args.environment else None
        platform = Platform(args.platform) if args.platform else None
        
        if args.action == "validate":
            config = config_manager.get_configuration(environment, platform, args.profile)
            issues = config_manager.validate_configuration(config)
            
            if issues:
                print("Configuration validation issues:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration validation successful")
                
        elif args.action == "generate":
            files = config_manager.generate_configurations(environment, platform, args.profile)
            print("Generated configuration files:")
            for name, path in files.items():
                print(f"  - {name}: {path}")
                
        elif args.action == "export":
            config_str = config_manager.export_config(args.format, environment, platform, args.profile)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(config_str)
                print(f"Configuration exported to {args.output}")
            else:
                print(config_str)
                
    except Exception as e:
        logger.error(f"Configuration management failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()