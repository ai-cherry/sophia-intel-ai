#!/usr/bin/env python3
"""
Sophia Intel AI - Preflight Validator

This tool validates the system configuration before starting services,
checking for port availability, dependencies, environment variables,
and potential conflicts.
"""

import os
import sys
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.service_registry import ServiceRegistry, ServiceType, ServiceDefinition
    from app.core.unified_config import get_config, validate_configuration
    HAS_SOPHIA_IMPORTS = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import Sophia modules: {e}")
    print("   Running in standalone mode with limited functionality")
    HAS_SOPHIA_IMPORTS = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreflightValidator:
    """
    Comprehensive preflight validation for Sophia Intel AI.
    
    This validator checks all system requirements, configuration,
    and dependencies before services are started.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []
        
        # Default port configuration (fallback if imports fail)
        self.default_ports = {
            "unified_api": 8003,
            "agent_ui": 3000,
            "postgres": 5432,
            "redis": 6379,
            "mcp_memory": 8081,
            "mcp_filesystem": 8082,
            "mcp_web": 8083,
            "mcp_git": 8084,
            "weaviate": 8080,
            "neo4j": 7687,
            "jupyter": 8888,
            "prometheus": 9090,
            "grafana": 3001,
        }
        
        if HAS_SOPHIA_IMPORTS:
            try:
                self.config = get_config()
            except Exception as e:
                self.config = None
                self.warnings.append(f"Could not load configuration: {e}")
    
    def log(self, message: str, level: str = "info") -> None:
        """Log a message with appropriate level."""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    def check_python_requirements(self) -> bool:
        """Check Python version and basic requirements."""
        self.log("🐍 Checking Python requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.errors.append(f"Python 3.8+ required, found {sys.version}")
            return False
        
        self.passed_checks.append(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check critical imports
        critical_packages = [
            ("fastapi", "FastAPI web framework"),
            ("uvicorn", "ASGI server"),
            ("redis", "Redis client"),
            ("psycopg2", "PostgreSQL adapter"),
        ]
        
        missing_packages = []
        for package, description in critical_packages:
            try:
                __import__(package)
                self.passed_checks.append(f"✓ {package} available")
            except ImportError:
                missing_packages.append(f"{package} ({description})")
        
        if missing_packages:
            self.errors.append(f"Missing Python packages: {', '.join(missing_packages)}")
            return False
        
        return True
    
    def check_port_availability(self) -> bool:
        """Check if required ports are available."""
        self.log("🔌 Checking port availability...")
        
        # Get ports from configuration or use defaults
        if HAS_SOPHIA_IMPORTS and self.config:
            try:
                ports = self.config.get_all_ports()
            except Exception:
                ports = self.default_ports
        else:
            ports = self.default_ports
        
        conflicts = []
        available_ports = []
        
        for service, port in ports.items():
            if self.is_port_in_use(port):
                process_info = self.get_port_process(port)
                conflicts.append(f"Port {port} ({service}) in use by: {process_info}")
            else:
                available_ports.append(f"✓ Port {port} ({service}) available")
        
        # Log results
        for check in available_ports:
            self.passed_checks.append(check)
        
        if conflicts:
            for conflict in conflicts:
                self.errors.append(f"✗ {conflict}")
            return False
        
        return True
    
    def is_port_in_use(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
    
    def get_port_process(self, port: int) -> str:
        """Get process information for a port."""
        try:
            # Try lsof first
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    process_line = lines[1]
                    parts = process_line.split()
                    if len(parts) >= 2:
                        return f"{parts[0]} (PID: {parts[1]})"
            
            # Fallback to netstat
            result = subprocess.run(
                ["netstat", "-tulpn", f"| grep :{port}"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            
            return "unknown process"
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return "unknown process"
    
    def check_dependencies(self) -> bool:
        """Check for required system dependencies."""
        self.log("📦 Checking system dependencies...")
        
        # Required system commands
        required_commands = [
            ("docker", "Docker container runtime"),
            ("git", "Version control"),
            ("curl", "HTTP client"),
            ("lsof", "Port checking"),
        ]
        
        # Optional but recommended commands
        optional_commands = [
            ("docker-compose", "Docker Compose"),
            ("nc", "Network testing"),
            ("jq", "JSON processing"),
            ("htop", "System monitoring"),
        ]
        
        missing_required = []
        missing_optional = []
        
        # Check required commands
        for cmd, description in required_commands:
            if self.command_exists(cmd):
                version = self.get_command_version(cmd)
                self.passed_checks.append(f"✓ {cmd} {version}")
            else:
                missing_required.append(f"{cmd} ({description})")
        
        # Check optional commands
        for cmd, description in optional_commands:
            if self.command_exists(cmd):
                version = self.get_command_version(cmd)
                self.passed_checks.append(f"✓ {cmd} {version} (optional)")
            else:
                missing_optional.append(f"{cmd} ({description})")
        
        if missing_required:
            self.errors.append(f"Missing required commands: {', '.join(missing_required)}")
        
        if missing_optional:
            self.warnings.append(f"Missing optional commands: {', '.join(missing_optional)}")
        
        return len(missing_required) == 0
    
    def command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ["which", command],
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_command_version(self, command: str) -> str:
        """Get version of a command."""
        version_flags = ["--version", "-v", "-V", "version"]
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [command, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    # Extract version number from output
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        return lines[0][:50]  # Limit length
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return "(version unknown)"
    
    def check_environment_variables(self) -> bool:
        """Check required environment variables."""
        self.log("🔧 Checking environment variables...")
        
        if not HAS_SOPHIA_IMPORTS or not self.config:
            self.warnings.append("Cannot validate environment variables without configuration")
            return True
        
        try:
            validation_result = validate_configuration()
            
            if validation_result.get("missing_env_vars"):
                for var in validation_result["missing_env_vars"]:
                    self.warnings.append(f"Missing or default value: {var}")
            
            if validation_result.get("port_conflicts"):
                for conflict in validation_result["port_conflicts"]:
                    self.errors.append(f"Port conflict: {conflict}")
            
            # Check critical environment variables
            critical_vars = [
                "WORKSPACE_PATH",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
            ]
            
            missing_critical = []
            for var in critical_vars:
                value = os.getenv(var)
                if not value or "YOUR-" in value or "CHANGEME" in value:
                    missing_critical.append(var)
                else:
                    # Don't log actual values for security
                    self.passed_checks.append(f"✓ {var} configured")
            
            if missing_critical:
                self.errors.append(f"Missing critical environment variables: {', '.join(missing_critical)}")
                return False
            
            return True
            
        except Exception as e:
            self.warnings.append(f"Error validating environment: {e}")
            return True
    
    def check_workspace(self) -> bool:
        """Check workspace configuration and permissions."""
        self.log("📁 Checking workspace...")
        
        workspace_path = os.getenv("WORKSPACE_PATH", str(project_root))
        workspace = Path(workspace_path)
        
        if not workspace.exists():
            self.errors.append(f"Workspace directory does not exist: {workspace}")
            return False
        
        if not workspace.is_dir():
            self.errors.append(f"Workspace path is not a directory: {workspace}")
            return False
        
        # Check permissions
        if not os.access(workspace, os.R_OK):
            self.errors.append(f"Workspace is not readable: {workspace}")
            return False
        
        if not os.access(workspace, os.W_OK):
            self.warnings.append(f"Workspace is not writable: {workspace}")
        
        self.passed_checks.append(f"✓ Workspace accessible: {workspace}")
        
        # Check for key files/directories
        important_paths = [
            "app",
            "scripts",
            "tools",
            ".env.example",
        ]
        
        for path_name in important_paths:
            path = workspace / path_name
            if path.exists():
                self.passed_checks.append(f"✓ Found: {path_name}")
            else:
                self.warnings.append(f"Missing: {path_name}")
        
        return True
    
    def check_docker_services(self) -> bool:
        """Check Docker and running services."""
        self.log("🐳 Checking Docker services...")
        
        if not self.command_exists("docker"):
            self.warnings.append("Docker not available - some services may not work")
            return True
        
        try:
            # Check Docker daemon
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.warnings.append("Docker daemon not running")
                return True
            
            self.passed_checks.append("✓ Docker daemon running")
            
            # Check for running containers
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # More than just header
                    self.passed_checks.append(f"✓ Found {len(lines) - 1} running containers")
                    if self.verbose:
                        for line in lines[1:]:  # Skip header
                            self.log(f"  Container: {line}")
            
            return True
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            self.warnings.append(f"Error checking Docker: {e}")
            return True
    
    def check_network_connectivity(self) -> bool:
        """Check network connectivity to external services."""
        self.log("🌐 Checking network connectivity...")
        
        # Test URLs
        test_urls = [
            ("api.openai.com", 443, "OpenAI API"),
            ("api.anthropic.com", 443, "Anthropic API"),
            ("api.github.com", 443, "GitHub API"),
            ("google.com", 80, "Internet connectivity"),
        ]
        
        for host, port, description in test_urls:
            if self.test_connection(host, port, timeout=5):
                self.passed_checks.append(f"✓ {description} reachable")
            else:
                self.warnings.append(f"Cannot reach {description} ({host}:{port})")
        
        return True
    
    def test_connection(self, host: str, port: int, timeout: int = 5) -> bool:
        """Test connection to a host:port."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
    
    def check_configuration_conflicts(self) -> bool:
        """Check for configuration conflicts and issues."""
        self.log("⚙️  Checking configuration conflicts...")
        
        if not HAS_SOPHIA_IMPORTS:
            self.warnings.append("Cannot check configuration conflicts without imports")
            return True
        
        try:
            # Check service registry conflicts
            conflicts = ServiceRegistry.check_conflicts()
            if conflicts:
                for svc1, svc2, port in conflicts:
                    self.errors.append(f"Service registry conflict: {svc1} and {svc2} both use port {port}")
            
            # Check dependency validation
            dep_errors = ServiceRegistry.validate_dependencies()
            if dep_errors:
                for error in dep_errors:
                    self.errors.append(f"Dependency error: {error}")
            
            if not conflicts and not dep_errors:
                self.passed_checks.append("✓ No configuration conflicts detected")
            
            return len(conflicts) == 0 and len(dep_errors) == 0
            
        except Exception as e:
            self.warnings.append(f"Error checking configuration: {e}")
            return True
    
    def run_all_checks(self) -> bool:
        """Run all preflight checks."""
        print("🚀 Sophia Intel AI - Preflight Validator")
        print("=" * 50)
        print()
        
        checks = [
            ("Python Requirements", self.check_python_requirements),
            ("Port Availability", self.check_port_availability),
            ("System Dependencies", self.check_dependencies),
            ("Environment Variables", self.check_environment_variables),
            ("Workspace", self.check_workspace),
            ("Docker Services", self.check_docker_services),
            ("Network Connectivity", self.check_network_connectivity),
            ("Configuration", self.check_configuration_conflicts),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                start_time = time.time()
                result = check_func()
                duration = time.time() - start_time
                
                if result:
                    print(f"✅ {check_name} ({duration:.2f}s)")
                else:
                    print(f"❌ {check_name} ({duration:.2f}s)")
                    all_passed = False
                    
            except Exception as e:
                print(f"💥 {check_name} - Error: {e}")
                self.errors.append(f"{check_name} check failed: {e}")
                all_passed = False
            
            if self.verbose and (self.errors or self.warnings):
                for error in self.errors[-5:]:  # Show last 5 errors
                    print(f"   ❌ {error}")
                for warning in self.warnings[-5:]:  # Show last 5 warnings
                    print(f"   ⚠️  {warning}")
                self.errors = self.errors[:-5] if len(self.errors) > 5 else []
                self.warnings = self.warnings[:-5] if len(self.warnings) > 5 else []
        
        print()
        self.print_summary(all_passed)
        return all_passed
    
    def print_summary(self, all_passed: bool) -> None:
        """Print validation summary."""
        print("📋 VALIDATION SUMMARY")
        print("=" * 50)
        
        if self.passed_checks:
            print(f"\n✅ PASSED ({len(self.passed_checks)}):")
            for check in self.passed_checks:
                print(f"   {check}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        print()
        if all_passed:
            print("🎉 ALL CHECKS PASSED! System is ready for Sophia Intel AI.")
        else:
            print("⚠️  SOME CHECKS FAILED! Please address the errors above.")
            print("\nFor help, see: https://github.com/your-org/sophia-intel-ai/docs/troubleshooting.md")
        
        print("\n" + "=" * 50)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sophia Intel AI Preflight Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/preflight_validator.py              # Run all checks
  python tools/preflight_validator.py --verbose    # Verbose output
  python tools/preflight_validator.py --help       # Show this help
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--check",
        choices=["python", "ports", "deps", "env", "workspace", "docker", "network", "config"],
        help="Run only a specific check"
    )
    
    args = parser.parse_args()
    
    validator = PreflightValidator(verbose=args.verbose)
    
    if args.check:
        # Run specific check
        check_map = {
            "python": validator.check_python_requirements,
            "ports": validator.check_port_availability,
            "deps": validator.check_dependencies,
            "env": validator.check_environment_variables,
            "workspace": validator.check_workspace,
            "docker": validator.check_docker_services,
            "network": validator.check_network_connectivity,
            "config": validator.check_configuration_conflicts,
        }
        
        check_func = check_map[args.check]
        print(f"🔍 Running {args.check} check...")
        result = check_func()
        validator.print_summary(result)
        sys.exit(0 if result else 1)
    else:
        # Run all checks
        result = validator.run_all_checks()
        sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()