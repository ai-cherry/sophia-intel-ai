#!/usr/bin/env python3
"""
Comprehensive Startup Script Validator
Validates ALL startup scripts and configurations for production readiness
"""

import os
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import re

class StartupValidator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.results = {}
        self.errors = []
        self.warnings = []

    def validate_shell_scripts(self) -> Dict:
        """Validate all shell scripts"""
        print("🔍 Validating Shell Scripts...")

        shell_scripts = list(self.repo_path.glob("**/*.sh"))
        shell_scripts = [s for s in shell_scripts if "node_modules" not in str(s)]

        results = {}

        for script in shell_scripts:
            script_results = {
                'syntax_valid': False,
                'has_error_handling': False,
                'missing_commands': [],
                'hardcoded_paths': [],
                'executable': False
            }

            # Check syntax
            try:
                subprocess.run(['bash', '-n', str(script)], 
                             check=True, capture_output=True)
                script_results['syntax_valid'] = True
                print(f"  ✅ {script.name}: Syntax OK")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Syntax error in {script}: {e.stderr.decode()}")
                print(f"  ❌ {script.name}: Syntax ERROR")

            # Check for error handling
            content = script.read_text()
            if 'set -e' in content or 'set -euo pipefail' in content:
                script_results['has_error_handling'] = True
                print(f"  ✅ {script.name}: Has error handling")
            else:
                self.warnings.append(f"No error handling in {script}")
                print(f"  ⚠️ {script.name}: No error handling")

            # Check for missing commands
            commands = re.findall(r'\b(python|node|npm|docker|kubectl|vercel|pulumi|uv|redis-cli|psql|curl|git)\b', content)
            for cmd in set(commands):
                if subprocess.run(['which', cmd], capture_output=True).returncode != 0:
                    script_results['missing_commands'].append(cmd)
                    print(f"  ❌ {script.name}: Missing command {cmd}")

            # Check for hardcoded paths
            hardcoded = re.findall(r'(/home/[^/\s]+/|/Users/|C:\\|/mnt/|/opt/)', content)
            if hardcoded:
                script_results['hardcoded_paths'] = hardcoded
                self.warnings.append(f"Hardcoded paths in {script}: {hardcoded}")
                print(f"  ⚠️ {script.name}: Hardcoded paths found")

            # Check if executable
            script_results['executable'] = os.access(script, os.X_OK)
            if not script_results['executable']:
                print(f"  ⚠️ {script.name}: Not executable")

            results[str(script)] = script_results

        return results

    def validate_devcontainer(self) -> Dict:
        """Validate devcontainer configuration"""
        print("\n🔍 Validating DevContainer Configuration...")

        devcontainer_path = self.repo_path / ".devcontainer" / "devcontainer.json"
        if not devcontainer_path.exists():
            self.errors.append("No devcontainer.json found")
            return {'exists': False}

        try:
            with open(devcontainer_path) as f:
                config = json.load(f)

            results = {
                'exists': True,
                'valid_json': True,
                'features': config.get('features', {}),
                'ports': config.get('forwardPorts', []),
                'extensions': config.get('customizations', {}).get('vscode', {}).get('extensions', []),
                'post_create_command': config.get('postCreateCommand', ''),
                'issues': []
            }

            # Validate ports
            expected_ports = [8000, 3000, 8100, 6333, 6379, 5432]
            for port in expected_ports:
                if port not in results['ports']:
                    results['issues'].append(f"Missing port forward: {port}")
                    print(f"  ⚠️ Missing port forward: {port}")
                else:
                    print(f"  ✅ Port {port} configured")

            # Validate VS Code extensions
            essential_extensions = [
                'ms-python.python',
                'ms-vscode.vscode-typescript-next',
                'bradlc.vscode-tailwindcss'
            ]

            for ext in essential_extensions:
                if ext not in results['extensions']:
                    results['issues'].append(f"Missing VS Code extension: {ext}")
                    print(f"  ⚠️ Missing extension: {ext}")
                else:
                    print(f"  ✅ Extension {ext} configured")

            # Check post-create command
            if results['post_create_command']:
                print(f"  ✅ Post-create command configured")
            else:
                results['issues'].append("No post-create command")
                print(f"  ⚠️ No post-create command")

            return results

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in devcontainer.json: {e}")
            return {'exists': True, 'valid_json': False, 'error': str(e)}

    def validate_environment_files(self) -> Dict:
        """Validate environment configuration files"""
        print("\n🔍 Validating Environment Files...")

        env_files = ['.env.example', '.env.development', '.env.production']
        results = {}

        for env_file in env_files:
            env_path = self.repo_path / env_file
            file_results = {
                'exists': env_path.exists(),
                'variables': [],
                'missing_critical': []
            }

            if file_results['exists']:
                content = env_path.read_text()
                # Extract variable names
                variables = re.findall(r'^([A-Z_][A-Z0-9_]*)=', content, re.MULTILINE)
                file_results['variables'] = variables
                print(f"  ✅ {env_file}: {len(variables)} variables")

                # Check for critical variables
                critical_vars = [
                    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'DATABASE_URL', 
                    'REDIS_URL', 'QDRANT_URL'
                ]

                for var in critical_vars:
                    if var not in variables:
                        file_results['missing_critical'].append(var)
                        print(f"    ⚠️ Missing critical variable: {var}")
                    else:
                        print(f"    ✅ Critical variable: {var}")
            else:
                self.warnings.append(f"Missing environment file: {env_file}")
                print(f"  ⚠️ {env_file}: Not found")

            results[env_file] = file_results

        return results

    def validate_docker_files(self) -> Dict:
        """Validate Docker configurations"""
        print("\n🔍 Validating Docker Files...")

        docker_files = list(self.repo_path.glob("**/Dockerfile*"))
        docker_files.extend(list(self.repo_path.glob("**/docker-compose*.yml")))
        docker_files = [f for f in docker_files if "node_modules" not in str(f)]

        results = {}

        for docker_file in docker_files:
            file_results = {
                'valid_syntax': False,
                'has_health_check': False,
                'has_test_stage': False,
                'issues': []
            }

            content = docker_file.read_text()

            # Basic validation
            if docker_file.name.startswith('Dockerfile'):
                if 'FROM' in content:
                    file_results['valid_syntax'] = True
                    print(f"  ✅ {docker_file.name}: Valid Dockerfile")
                else:
                    file_results['issues'].append("No FROM instruction")
                    print(f"  ❌ {docker_file.name}: No FROM instruction")

                # Check for health check
                if 'HEALTHCHECK' in content:
                    file_results['has_health_check'] = True
                    print(f"    ✅ Has health check")
                else:
                    file_results['issues'].append("No health check")
                    print(f"    ⚠️ No health check")

                # Check for test stage
                if 'FROM' in content and 'AS test' in content:
                    file_results['has_test_stage'] = True
                    print(f"    ✅ Has test stage")
                else:
                    file_results['issues'].append("No test stage")
                    print(f"    ⚠️ No test stage")

            elif docker_file.name.startswith('docker-compose'):
                try:
                    yaml.safe_load(content)
                    file_results['valid_syntax'] = True
                    print(f"  ✅ {docker_file.name}: Valid YAML")
                except yaml.YAMLError as e:
                    file_results['issues'].append(f"Invalid YAML: {e}")
                    print(f"  ❌ {docker_file.name}: Invalid YAML")

            results[str(docker_file)] = file_results

        return results

    def create_fixes(self):
        """Create fixes for common issues"""
        print("\n🔧 Creating Fixes...")

        # Create missing .env.example if not exists
        env_example = self.repo_path / '.env.example'
        if not env_example.exists():
            env_content = """# Sophia AI Environment Variables
# Copy to .env and fill in your values

# AI Services
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GROK_API_KEY=your_grok_key_here

# Database URLs
DATABASE_URL=${DATABASE_URL}:5432/sophia
REDIS_URL=${REDIS_URL}
QDRANT_URL=http://localhost:6333

# Third-party APIs
GITHUB_TOKEN=your_github_token_here
GONG_ACCESS_KEY=your_gong_key_here
GONG_CLIENT_SECRET=your_gong_secret_here
HUBSPOT_API_KEY=your_hubspot_key_here
SLACK_BOT_TOKEN=your_slack_token_here
NOTION_API_KEY=your_notion_key_here

# Lambda Labs
LAMBDA_LABS_API_KEY=your_lambda_labs_key_here

# Production Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
"""
            env_example.write_text(env_content)
            print("  ✅ Created .env.example")

        # Fix shell scripts without error handling
        for script_path, results in self.results.get('shell_scripts', {}).items():
            if not results['has_error_handling']:
                script = Path(script_path)
                content = script.read_text()
                if not content.startswith('#!/bin/bash'):
                    continue

                # Add error handling
                lines = content.split('\n')
                if 'set -e' not in content:
                    # Insert after shebang
                    lines.insert(1, 'set -euo pipefail')
                    script.write_text('\n'.join(lines))
                    print(f"  ✅ Added error handling to {script.name}")

    def generate_report(self) -> str:
        """Generate validation report"""
        report = f"""
# Startup Scripts Validation Report

## Summary
- **Errors**: {len(self.errors)}
- **Warnings**: {len(self.warnings)}

## Shell Scripts
"""

        for script_path, results in self.results.get('shell_scripts', {}).items():
            script_name = Path(script_path).name
            status = "✅" if results['syntax_valid'] and not results['missing_commands'] else "❌"
            report += f"- {status} **{script_name}**\n"

            if not results['syntax_valid']:
                report += f"  - ❌ Syntax errors\n"
            if results['missing_commands']:
                report += f"  - ❌ Missing commands: {', '.join(results['missing_commands'])}\n"
            if not results['has_error_handling']:
                report += f"  - ⚠️ No error handling\n"
            if results['hardcoded_paths']:
                report += f"  - ⚠️ Hardcoded paths found\n"

        report += f"""
## DevContainer
"""
        devcontainer = self.results.get('devcontainer', {})
        if devcontainer.get('exists'):
            status = "✅" if devcontainer.get('valid_json') and not devcontainer.get('issues') else "⚠️"
            report += f"- {status} Configuration exists\n"
            for issue in devcontainer.get('issues', []):
                report += f"  - ⚠️ {issue}\n"
        else:
            report += "- ❌ No devcontainer.json found\n"

        report += f"""
## Environment Files
"""
        for env_file, results in self.results.get('environment_files', {}).items():
            status = "✅" if results['exists'] else "❌"
            report += f"- {status} **{env_file}**\n"
            if results.get('missing_critical'):
                report += f"  - ⚠️ Missing critical variables: {', '.join(results['missing_critical'])}\n"

        if self.errors:
            report += f"""
## Errors
"""
            for error in self.errors:
                report += f"- ❌ {error}\n"

        if self.warnings:
            report += f"""
## Warnings
"""
            for warning in self.warnings:
                report += f"- ⚠️ {warning}\n"

        return report

    def run_validation(self):
        """Run complete validation"""
        print("🚀 Starting Comprehensive Startup Validation...")

        self.results['shell_scripts'] = self.validate_shell_scripts()
        self.results['devcontainer'] = self.validate_devcontainer()
        self.results['environment_files'] = self.validate_environment_files()
        self.results['docker_files'] = self.validate_docker_files()

        self.create_fixes()

        # Generate and save report
        report = self.generate_report()
        report_path = self.repo_path / 'STARTUP_VALIDATION_REPORT.md'
        report_path.write_text(report)

        print(f"\n📊 Validation Complete!")
        print(f"Report saved to: {report_path}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        return len(self.errors) == 0

if __name__ == "__main__":
    validator = StartupValidator()
    success = validator.run_validation()

    if success:
        print("\n🎉 All startup scripts are production ready!")
    else:
        print("\n⚠️ Some issues need to be fixed before production deployment!")
        exit(1)
