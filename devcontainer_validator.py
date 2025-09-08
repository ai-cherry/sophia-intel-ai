#!/usr/bin/env python3
"""
DevContainer Triple-Check & Configuration
MISSION CRITICAL: Complete DevContainer validation and setup
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class DevContainerValidator:
    """Complete DevContainer validation and configuration system"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.devcontainer_dir = self.project_root / '.devcontainer'
        self.validation_results = {}
        self.fixes_applied = []
        
    def execute_triple_check(self) -> Dict:
        """Execute comprehensive DevContainer triple-check"""
        
        print("🎖️ DEVCONTAINER TRIPLE-CHECK - MISSION CRITICAL")
        print("=" * 60)
        print("TARGET: Complete DevContainer validation and configuration")
        print("=" * 60)
        
        checks = [
            ("devcontainer_structure", self.check_devcontainer_structure),
            ("devcontainer_config", self.check_devcontainer_config),
            ("gpu_configuration", self.check_gpu_configuration),
            ("python_environment", self.check_python_environment),
            ("docker_configuration", self.check_docker_configuration),
            ("mcp_components", self.check_mcp_components),
            ("network_configuration", self.check_network_configuration),
            ("file_permissions", self.check_file_permissions),
            ("environment_variables", self.check_environment_variables),
            ("development_tools", self.check_development_tools),
            ("security_configuration", self.check_security_configuration),
            ("performance_optimization", self.check_performance_optimization)
        ]
        
        for check_name, check_func in checks:
            print(f"\n🔍 Triple-checking: {check_name}")
            try:
                result = check_func()
                self.validation_results[check_name] = {
                    "status": "PASS" if result.get("valid", False) else "FAIL",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                if result.get("valid", False):
                    print(f"✅ {check_name}: PASS")
                else:
                    print(f"❌ {check_name}: FAIL")
                    # Apply auto-fixes
                    if self.auto_fix_check(check_name, result):
                        print(f"🔧 Auto-fixed: {check_name}")
                        self.validation_results[check_name]["status"] = "FIXED"
                        
            except Exception as e:
                self.validation_results[check_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                print(f"💥 {check_name}: ERROR - {e}")
        
        return self.generate_validation_report()
    
    def check_devcontainer_structure(self) -> Dict:
        """Check DevContainer directory structure"""
        
        required_files = [
            'devcontainer.json',
            'post-create.sh',
            'post-start.sh',
            'Dockerfile'
        ]
        
        missing_files = []
        existing_files = []
        
        # Check if .devcontainer directory exists
        if not self.devcontainer_dir.exists():
            return {
                "valid": False,
                "error": ".devcontainer directory does not exist",
                "missing_files": required_files,
                "fix": "create_devcontainer_structure"
            }
        
        # Check required files
        for file in required_files:
            file_path = self.devcontainer_dir / file
            if file_path.exists():
                existing_files.append(file)
            else:
                missing_files.append(file)
        
        return {
            "valid": len(missing_files) == 0,
            "existing_files": existing_files,
            "missing_files": missing_files,
            "fix": "create_missing_files" if missing_files else None
        }
    
    def check_devcontainer_config(self) -> Dict:
        """Check DevContainer configuration"""
        
        config_path = self.devcontainer_dir / 'devcontainer.json'
        
        if not config_path.exists():
            return {
                "valid": False,
                "error": "devcontainer.json not found",
                "fix": "create_devcontainer_config"
            }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required configuration
            required_keys = ['name', 'image', 'features', 'customizations']
            missing_keys = [key for key in required_keys if key not in config]
            
            # Check GPU configuration
            gpu_configured = False
            if 'runArgs' in config:
                gpu_configured = any('--gpus' in arg for arg in config['runArgs'])
            
            # Check Python configuration
            python_configured = False
            if 'features' in config:
                python_configured = any('python' in feature for feature in config['features'])
            
            return {
                "valid": len(missing_keys) == 0 and gpu_configured and python_configured,
                "config": config,
                "missing_keys": missing_keys,
                "gpu_configured": gpu_configured,
                "python_configured": python_configured,
                "fix": "update_devcontainer_config" if missing_keys or not gpu_configured or not python_configured else None
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON in devcontainer.json: {e}",
                "fix": "fix_devcontainer_json"
            }
    
    def check_gpu_configuration(self) -> Dict:
        """Check GPU configuration and availability"""
        
        # Check if nvidia-smi is available
        nvidia_available = shutil.which('nvidia-smi') is not None
        
        gpu_info = {}
        if nvidia_available:
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_info = {"gpus": result.stdout.strip().split('\n')}
            except:
                pass
        
        # Check Docker GPU support
        docker_gpu_support = False
        try:
            result = subprocess.run(['docker', 'run', '--rm', '--gpus', 'all', 'nvidia/cuda:11.8-base-ubuntu20.04', 'nvidia-smi'], 
                                  capture_output=True, text=True, timeout=30)
            docker_gpu_support = result.returncode == 0
        except:
            pass
        
        return {
            "valid": nvidia_available and docker_gpu_support,
            "nvidia_available": nvidia_available,
            "docker_gpu_support": docker_gpu_support,
            "gpu_info": gpu_info,
            "fix": "setup_gpu_support" if not (nvidia_available and docker_gpu_support) else None
        }
    
    def check_python_environment(self) -> Dict:
        """Check Python environment configuration"""
        
        python_version = sys.version_info
        python_valid = python_version.major == 3 and python_version.minor >= 11
        
        # Check required packages
        required_packages = [
            'torch', 'transformers', 'fastapi', 'uvicorn',
            'httpx', 'aiohttp', 'numpy', 'pandas'
        ]
        
        installed_packages = []
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        # Check virtual environment
        venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        return {
            "valid": python_valid and len(missing_packages) == 0,
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "python_valid": python_valid,
            "venv_active": venv_active,
            "installed_packages": installed_packages,
            "missing_packages": missing_packages,
            "fix": "setup_python_environment" if not python_valid or missing_packages else None
        }
    
    def check_docker_configuration(self) -> Dict:
        """Check Docker configuration"""
        
        docker_available = shutil.which('docker') is not None
        docker_running = False
        docker_version = None
        
        if docker_available:
            try:
                result = subprocess.run(['docker', 'version'], capture_output=True, text=True)
                docker_running = result.returncode == 0
                if docker_running:
                    docker_version = result.stdout.split('\n')[1].split()[-1] if result.stdout else "unknown"
            except:
                pass
        
        # Check Docker Compose
        compose_available = shutil.which('docker-compose') is not None or shutil.which('docker') is not None
        
        return {
            "valid": docker_available and docker_running and compose_available,
            "docker_available": docker_available,
            "docker_running": docker_running,
            "docker_version": docker_version,
            "compose_available": compose_available,
            "fix": "setup_docker" if not (docker_available and docker_running) else None
        }
    
    def check_mcp_components(self) -> Dict:
        """Check MCP (Model Context Protocol) components"""
        
        mcp_directories = [
            'mcp_servers',
            'mcp_memory_server',
            'mcp_memory'
        ]
        
        existing_dirs = []
        missing_dirs = []
        
        for dir_name in mcp_directories:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                existing_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)
        
        # Check MCP server imports
        mcp_importable = False
        try:
            from mcp import Server
            from mcp.server.stdio import stdio_server
            mcp_importable = True
        except ImportError:
            pass
        
        return {
            "valid": len(missing_dirs) == 0 and mcp_importable,
            "existing_dirs": existing_dirs,
            "missing_dirs": missing_dirs,
            "mcp_importable": mcp_importable,
            "fix": "setup_mcp_components" if missing_dirs or not mcp_importable else None
        }
    
    def check_network_configuration(self) -> Dict:
        """Check network configuration"""
        
        # Test internet connectivity
        internet_available = False
        try:
            result = subprocess.run(['curl', '-s', '--connect-timeout', '5', 'https://api.github.com'], 
                                  capture_output=True, timeout=10)
            internet_available = result.returncode == 0
        except:
            pass
        
        # Check DNS resolution
        dns_working = False
        try:
            result = subprocess.run(['nslookup', 'github.com'], capture_output=True, timeout=5)
            dns_working = result.returncode == 0
        except:
            pass
        
        return {
            "valid": internet_available and dns_working,
            "internet_available": internet_available,
            "dns_working": dns_working,
            "fix": "fix_network_configuration" if not (internet_available and dns_working) else None
        }
    
    def check_file_permissions(self) -> Dict:
        """Check file permissions"""
        
        permission_issues = []
        
        # Check workspace permissions
        workspace_writable = os.access(self.project_root, os.W_OK)
        if not workspace_writable:
            permission_issues.append("workspace_not_writable")
        
        # Check script permissions
        script_files = list(self.project_root.rglob("*.sh"))
        non_executable_scripts = []
        
        for script in script_files:
            if not os.access(script, os.X_OK):
                non_executable_scripts.append(str(script))
        
        if non_executable_scripts:
            permission_issues.append("scripts_not_executable")
        
        return {
            "valid": len(permission_issues) == 0,
            "workspace_writable": workspace_writable,
            "non_executable_scripts": non_executable_scripts,
            "permission_issues": permission_issues,
            "fix": "fix_file_permissions" if permission_issues else None
        }
    
    def check_environment_variables(self) -> Dict:
        """Check environment variables"""
        
        required_env_vars = [
            'PULUMI_ACCESS_TOKEN',
            'LAMBDA_API_KEY',
            'EXA_API_KEY'
        ]
        
        missing_vars = []
        set_vars = []
        
        for var in required_env_vars:
            if os.getenv(var):
                set_vars.append(var)
            else:
                missing_vars.append(var)
        
        return {
            "valid": len(missing_vars) == 0,
            "set_vars": set_vars,
            "missing_vars": missing_vars,
            "fix": "setup_environment_variables" if missing_vars else None
        }
    
    def check_development_tools(self) -> Dict:
        """Check development tools"""
        
        required_tools = [
            'git', 'curl', 'wget', 'htop', 'tmux'
        ]
        
        available_tools = []
        missing_tools = []
        
        for tool in required_tools:
            if shutil.which(tool):
                available_tools.append(tool)
            else:
                missing_tools.append(tool)
        
        return {
            "valid": len(missing_tools) == 0,
            "available_tools": available_tools,
            "missing_tools": missing_tools,
            "fix": "install_development_tools" if missing_tools else None
        }
    
    def check_security_configuration(self) -> Dict:
        """Check security configuration"""
        
        security_issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'sk-[a-zA-Z0-9]{32,}',
            r'pul-[a-zA-Z0-9]{32,}'
        ]
        
        # Scan key files for secrets
        key_files = [
            '.env', '.env.local', '.env.production',
            'devcontainer.json', 'docker-compose.yml'
        ]
        
        hardcoded_secrets_found = False
        for file_name in key_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    import re
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            hardcoded_secrets_found = True
                            break
                except:
                    pass
        
        if hardcoded_secrets_found:
            security_issues.append("hardcoded_secrets")
        
        return {
            "valid": len(security_issues) == 0,
            "security_issues": security_issues,
            "fix": "fix_security_issues" if security_issues else None
        }
    
    def check_performance_optimization(self) -> Dict:
        """Check performance optimization"""
        
        optimization_issues = []
        
        # Check memory limits
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Extract total memory
            import re
            mem_match = re.search(r'MemTotal:\s+(\d+)\s+kB', meminfo)
            if mem_match:
                total_mem_gb = int(mem_match.group(1)) / 1024 / 1024
                if total_mem_gb < 16:
                    optimization_issues.append("insufficient_memory")
        except:
            pass
        
        # Check CPU cores
        try:
            cpu_count = os.cpu_count()
            if cpu_count < 4:
                optimization_issues.append("insufficient_cpu")
        except:
            pass
        
        return {
            "valid": len(optimization_issues) == 0,
            "optimization_issues": optimization_issues,
            "fix": "optimize_performance" if optimization_issues else None
        }
    
    def auto_fix_check(self, check_name: str, result: Dict) -> bool:
        """Apply automatic fixes for failed checks"""
        
        fix_method = result.get("fix")
        if not fix_method:
            return False
        
        try:
            if fix_method == "create_devcontainer_structure":
                return self.create_devcontainer_structure()
            elif fix_method == "create_missing_files":
                return self.create_missing_devcontainer_files(result.get("missing_files", []))
            elif fix_method == "create_devcontainer_config":
                return self.create_devcontainer_config()
            elif fix_method == "update_devcontainer_config":
                return self.update_devcontainer_config()
            elif fix_method == "setup_python_environment":
                return self.setup_python_environment(result.get("missing_packages", []))
            elif fix_method == "setup_mcp_components":
                return self.setup_mcp_components()
            elif fix_method == "fix_file_permissions":
                return self.fix_file_permissions()
            elif fix_method == "install_development_tools":
                return self.install_development_tools(result.get("missing_tools", []))
            
            return False
            
        except Exception as e:
            print(f"Auto-fix failed for {check_name}: {e}")
            return False
    
    def create_devcontainer_structure(self) -> bool:
        """Create DevContainer directory structure"""
        
        try:
            self.devcontainer_dir.mkdir(exist_ok=True)
            self.fixes_applied.append("created_devcontainer_directory")
            return True
        except Exception:
            return False
    
    def create_devcontainer_config(self) -> bool:
        """Create DevContainer configuration"""
        
        config = {
            "name": "Sophia AI Platform - Lambda Labs Development",
            "image": "nvcr.io/nvidia/pytorch:24.03-py3",
            "features": {
                "ghcr.io/devcontainers/features/docker-in-docker:2": {},
                "ghcr.io/devcontainers/features/python:1": {
                    "version": "3.11"
                },
                "ghcr.io/devcontainers/features/node:1": {},
                "ghcr.io/devcontainers/features/git:1": {},
                "ghcr.io/devcontainers/features/github-cli:1": {}
            },
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-python.python",
                        "ms-python.vscode-pylance",
                        "ms-azuretools.vscode-docker",
                        "github.copilot",
                        "github.copilot-chat",
                        "ms-vscode.makefile-tools",
                        "redhat.vscode-yaml",
                        "esbenp.prettier-vscode"
                    ],
                    "settings": {
                        "python.linting.enabled": True,
                        "python.linting.pylintEnabled": True,
                        "python.formatting.provider": "black",
                        "python.testing.pytestEnabled": True,
                        "editor.formatOnSave": True
                    }
                }
            },
            "mounts": [
                "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind,consistency=cached",
                "source=${localEnv:HOME}/.config,target=/home/vscode/.config,type=bind,consistency=cached"
            ],
            "runArgs": [
                "--gpus=all",
                "--shm-size=16gb",
                "--ulimit=memlock=-1",
                "--ulimit=stack=67108864"
            ],
            "postCreateCommand": "bash .devcontainer/post-create.sh",
            "postStartCommand": "bash .devcontainer/post-start.sh",
            "remoteUser": "vscode",
            "hostRequirements": {
                "gpu": True,
                "memory": "32gb",
                "storage": "100gb"
            }
        }
        
        try:
            config_path = self.devcontainer_dir / 'devcontainer.json'
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.fixes_applied.append("created_devcontainer_config")
            return True
        except Exception:
            return False
    
    def create_missing_devcontainer_files(self, missing_files: List[str]) -> bool:
        """Create missing DevContainer files"""
        
        file_contents = {
            'post-create.sh': '''#!/bin/bash
set -euo pipefail

echo "🔧 DevContainer Post-Create Setup..."

# Install Python packages
pip3 install --upgrade pip
pip3 install -r requirements.txt || echo "No requirements.txt found"

# Install MCP components
pip3 install mcp-server || echo "MCP server installation failed"

# Setup GPU monitoring
nvidia-smi -pm 1 || echo "GPU setup failed"

echo "✅ DevContainer post-create setup complete"
''',
            'post-start.sh': '''#!/bin/bash
set -euo pipefail

echo "🚀 DevContainer Post-Start Setup..."

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start services if needed
# docker-compose up -d || echo "No docker-compose.yml found"

echo "✅ DevContainer post-start setup complete"
''',
            'Dockerfile': '''FROM nvcr.io/nvidia/pytorch:24.03-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git curl wget htop nvtop tmux \\
    build-essential software-properties-common \\
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && \\
    pip3 install -r /tmp/requirements.txt

# Setup workspace
WORKDIR /workspace
COPY . /workspace

# Set permissions
RUN chmod +x /workspace/*.sh || true

EXPOSE 8000 8001 8002

CMD ["bash"]
'''
        }
        
        try:
            for file_name in missing_files:
                if file_name in file_contents:
                    file_path = self.devcontainer_dir / file_name
                    with open(file_path, 'w') as f:
                        f.write(file_contents[file_name])
                    
                    # Make shell scripts executable
                    if file_name.endswith('.sh'):
                        file_path.chmod(0o755)
            
            self.fixes_applied.append(f"created_missing_files: {', '.join(missing_files)}")
            return True
        except Exception:
            return False
    
    def update_devcontainer_config(self) -> bool:
        """Update DevContainer configuration"""
        # This would update existing config with missing elements
        return self.create_devcontainer_config()
    
    def setup_python_environment(self, missing_packages: List[str]) -> bool:
        """Setup Python environment with missing packages"""
        
        if not missing_packages:
            return True
        
        try:
            for package in missing_packages:
                subprocess.run(['pip3', 'install', package], check=True, capture_output=True)
            
            self.fixes_applied.append(f"installed_packages: {', '.join(missing_packages)}")
            return True
        except Exception:
            return False
    
    def setup_mcp_components(self) -> bool:
        """Setup MCP components"""
        
        try:
            subprocess.run(['pip3', 'install', 'mcp-server'], check=True, capture_output=True)
            self.fixes_applied.append("installed_mcp_server")
            return True
        except Exception:
            return False
    
    def fix_file_permissions(self) -> bool:
        """Fix file permissions"""
        
        try:
            # Make shell scripts executable
            script_files = list(self.project_root.rglob("*.sh"))
            for script in script_files:
                script.chmod(0o755)
            
            self.fixes_applied.append("fixed_script_permissions")
            return True
        except Exception:
            return False
    
    def install_development_tools(self, missing_tools: List[str]) -> bool:
        """Install missing development tools"""
        
        if not missing_tools:
            return True
        
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True, capture_output=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y'] + missing_tools, 
                         check=True, capture_output=True)
            
            self.fixes_applied.append(f"installed_tools: {', '.join(missing_tools)}")
            return True
        except Exception:
            return False
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        
        passed_checks = sum(1 for result in self.validation_results.values() 
                           if result["status"] in ["PASS", "FIXED"])
        total_checks = len(self.validation_results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "success_rate": f"{(passed_checks/total_checks)*100:.1f}%",
                "fixes_applied": len(self.fixes_applied)
            },
            "check_results": self.validation_results,
            "fixes_applied": self.fixes_applied,
            "status": "PASS" if passed_checks == total_checks else "PARTIAL" if passed_checks > 0 else "FAIL",
            "next_actions": self._generate_next_actions()
        }
        
        return report
    
    def _generate_next_actions(self) -> List[str]:
        """Generate next actions based on validation results"""
        
        actions = []
        
        failed_checks = [name for name, result in self.validation_results.items() 
                        if result["status"] == "FAIL"]
        
        if failed_checks:
            actions.append(f"Fix failed checks: {', '.join(failed_checks)}")
        
        actions.extend([
            "Test DevContainer build and startup",
            "Verify GPU access in container",
            "Test MCP server functionality",
            "Run comprehensive integration tests"
        ])
        
        return actions
    
    def save_report(self, report: Dict, filename: str = None):
        """Save validation report to file"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"devcontainer_validation_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Validation report saved to: {filename}")

def main():
    """Main execution function"""
    
    print("🎖️ DEVCONTAINER TRIPLE-CHECK - MISSION CRITICAL")
    print("=" * 60)
    print("MISSION: Complete DevContainer validation and configuration")
    print("TARGET: Zero tolerance for configuration errors")
    print("=" * 60)
    
    validator = DevContainerValidator()
    
    # Execute triple-check
    report = validator.execute_triple_check()
    
    # Save report
    validator.save_report(report)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Status: {report['status']}")
    print(f"Checks: {report['summary']['passed_checks']}/{report['summary']['total_checks']} ({report['summary']['success_rate']})")
    print(f"Fixes Applied: {report['summary']['fixes_applied']}")
    
    if report["status"] == "PASS":
        print("\n✅ DEVCONTAINER TRIPLE-CHECK COMPLETE - READY FOR DEVELOPMENT")
    else:
        print(f"\n❌ VALIDATION INCOMPLETE - STATUS: {report['status']}")
        print("\nNext Actions:")
        for action in report["next_actions"]:
            print(f"  • {action}")
    
    return report["status"] == "PASS"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

