#!/usr/bin/env python3
"""
Sophia AI Platform - Local Syntax Validator
Comprehensive syntax and code quality validation for local development
"""

import os
import sys
import subprocess
import json
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class ValidationResult:
    """Result of a validation check"""
    file_path: str
    check_type: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    line_number: Optional[int] = None

class SyntaxValidator:
    """Comprehensive syntax validator for Sophia AI Platform"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.results: List[ValidationResult] = []
        self.stats = {
            'files_checked': 0,
            'errors': 0,
            'warnings': 0,
            'passed': 0
        }
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Starting comprehensive syntax validation...")
        print(f"📁 Project root: {self.project_root}")
        print("=" * 60)
        
        # Run all validation checks
        self.validate_python_syntax()
        self.validate_shell_scripts()
        self.validate_yaml_json()
        self.validate_docker_files()
        self.check_security_issues()
        self.validate_imports()
        
        # Generate report
        self.generate_report()
        
        # Return overall success
        return self.stats['errors'] == 0
    
    def validate_python_syntax(self):
        """Validate Python file syntax"""
        print("🐍 Validating Python syntax...")
        
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_skip_file(f)]
        
        for file_path in python_files:
            self.stats['files_checked'] += 1
            
            try:
                # Check syntax by compiling
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                ast.parse(source, filename=str(file_path))
                
                self._add_result(file_path, 'python_syntax', 'pass', 'Valid Python syntax')
                self.stats['passed'] += 1
                
            except SyntaxError as e:
                self._add_result(
                    file_path, 'python_syntax', 'fail', 
                    f'Syntax error: {e.msg}', e.lineno
                )
                self.stats['errors'] += 1
                
            except Exception as e:
                self._add_result(
                    file_path, 'python_syntax', 'fail', 
                    f'Error reading file: {e}'
                )
                self.stats['errors'] += 1
    
    def validate_shell_scripts(self):
        """Validate shell script syntax"""
        print("🐚 Validating shell scripts...")
        
        shell_files = list(self.project_root.rglob("*.sh"))
        shell_files = [f for f in shell_files if not self._should_skip_file(f)]
        
        for file_path in shell_files:
            self.stats['files_checked'] += 1
            
            try:
                # Check syntax with bash -n
                result = subprocess.run(
                    ['bash', '-n', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self._add_result(file_path, 'shell_syntax', 'pass', 'Valid shell syntax')
                    self.stats['passed'] += 1
                else:
                    self._add_result(
                        file_path, 'shell_syntax', 'fail', 
                        f'Shell syntax error: {result.stderr.strip()}'
                    )
                    self.stats['errors'] += 1
                    
            except subprocess.TimeoutExpired:
                self._add_result(
                    file_path, 'shell_syntax', 'fail', 
                    'Timeout during syntax check'
                )
                self.stats['errors'] += 1
                
            except Exception as e:
                self._add_result(
                    file_path, 'shell_syntax', 'fail', 
                    f'Error checking shell script: {e}'
                )
                self.stats['errors'] += 1
    
    def validate_yaml_json(self):
        """Validate YAML and JSON files"""
        print("📄 Validating YAML and JSON files...")
        
        # YAML files
        yaml_files = list(self.project_root.rglob("*.yml")) + list(self.project_root.rglob("*.yaml"))
        yaml_files = [f for f in yaml_files if not self._should_skip_file(f)]
        
        for file_path in yaml_files:
            self.stats['files_checked'] += 1
            
            try:
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                
                self._add_result(file_path, 'yaml_syntax', 'pass', 'Valid YAML syntax')
                self.stats['passed'] += 1
                
            except yaml.YAMLError as e:
                self._add_result(
                    file_path, 'yaml_syntax', 'fail', 
                    f'YAML syntax error: {e}'
                )
                self.stats['errors'] += 1
                
            except Exception as e:
                self._add_result(
                    file_path, 'yaml_syntax', 'fail', 
                    f'Error reading YAML file: {e}'
                )
                self.stats['errors'] += 1
        
        # JSON files
        json_files = list(self.project_root.rglob("*.json"))
        json_files = [f for f in json_files if not self._should_skip_file(f)]
        
        for file_path in json_files:
            self.stats['files_checked'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                self._add_result(file_path, 'json_syntax', 'pass', 'Valid JSON syntax')
                self.stats['passed'] += 1
                
            except json.JSONDecodeError as e:
                self._add_result(
                    file_path, 'json_syntax', 'fail', 
                    f'JSON syntax error: {e.msg}', e.lineno
                )
                self.stats['errors'] += 1
                
            except Exception as e:
                self._add_result(
                    file_path, 'json_syntax', 'fail', 
                    f'Error reading JSON file: {e}'
                )
                self.stats['errors'] += 1
    
    def validate_docker_files(self):
        """Validate Dockerfile syntax"""
        print("🐳 Validating Docker files...")
        
        docker_files = list(self.project_root.rglob("Dockerfile*"))
        docker_files = [f for f in docker_files if not self._should_skip_file(f)]
        
        for file_path in docker_files:
            self.stats['files_checked'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic Dockerfile validation
                lines = content.split('\n')
                has_from = any(line.strip().upper().startswith('FROM') for line in lines)
                
                if has_from:
                    self._add_result(file_path, 'dockerfile_syntax', 'pass', 'Valid Dockerfile structure')
                    self.stats['passed'] += 1
                else:
                    self._add_result(
                        file_path, 'dockerfile_syntax', 'warning', 
                        'Dockerfile missing FROM instruction'
                    )
                    self.stats['warnings'] += 1
                    
            except Exception as e:
                self._add_result(
                    file_path, 'dockerfile_syntax', 'fail', 
                    f'Error reading Dockerfile: {e}'
                )
                self.stats['errors'] += 1
    
    def check_security_issues(self):
        """Check for common security issues"""
        print("🔒 Checking for security issues...")
        
        # Patterns to look for
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token detected'),
            (r'-----BEGIN.*PRIVATE.*KEY-----', 'Private key detected'),
        ]
        
        # Check Python, JavaScript, TypeScript, YAML, JSON files
        file_patterns = ["*.py", "*.js", "*.ts", "*.yml", "*.yaml", "*.json"]
        
        for pattern in file_patterns:
            files = list(self.project_root.rglob(pattern))
            files = [f for f in files if not self._should_skip_file(f)]
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for regex_pattern, message in security_patterns:
                        matches = re.finditer(regex_pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            self._add_result(
                                file_path, 'security_check', 'warning', 
                                message, line_num
                            )
                            self.stats['warnings'] += 1
                            
                except Exception as e:
                    self._add_result(
                        file_path, 'security_check', 'fail', 
                        f'Error reading file for security check: {e}'
                    )
                    self.stats['errors'] += 1
    
    def validate_imports(self):
        """Validate Python imports"""
        print("📦 Validating Python imports...")
        
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_skip_file(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to check imports
                tree = ast.parse(content, filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._check_import_availability(file_path, alias.name, node.lineno)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._check_import_availability(file_path, node.module, node.lineno)
                            
            except SyntaxError:
                # Already caught in syntax validation
            except Exception as e:
                self._add_result(
                    file_path, 'import_check', 'fail', 
                    f'Error checking imports: {e}'
                )
                self.stats['errors'] += 1
    
    def _check_import_availability(self, file_path: Path, module_name: str, line_num: int):
        """Check if a module can be imported"""
        # Skip standard library and common modules
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 'subprocess', 'pathlib', 'datetime',
            'typing', 'dataclasses', 're', 'logging', 'asyncio', 'time',
            'collections', 'itertools', 'functools', 'hashlib', 'base64'
        }
        
        if module_name.split('.')[0] in stdlib_modules:
            return
        
        try:
            __import__(module_name)
            self._add_result(
                file_path, 'import_check', 'pass', 
                f'Import available: {module_name}', line_num
            )
        except ImportError:
            self._add_result(
                file_path, 'import_check', 'warning', 
                f'Import not available: {module_name}', line_num
            )
            self.stats['warnings'] += 1
        except Exception:
            # Skip modules that can't be imported for other reasons
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', '.env', 'dist', 'build', '.mypy_cache'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _add_result(self, file_path: Path, check_type: str, status: str, 
                   message: str, line_number: Optional[int] = None):
        """Add a validation result"""
        relative_path = file_path.relative_to(self.project_root)
        result = ValidationResult(
            file_path=str(relative_path),
            check_type=check_type,
            status=status,
            message=message,
            line_number=line_number
        )
        self.results.append(result)
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION REPORT")
        print("=" * 60)
        
        # Summary statistics
        print(f"📁 Files checked: {self.stats['files_checked']}")
        print(f"✅ Passed: {self.stats['passed']}")
        print(f"⚠️  Warnings: {self.stats['warnings']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        # Overall status
        if self.stats['errors'] == 0:
            if self.stats['warnings'] == 0:
                print("\n🎉 ALL CHECKS PASSED! No issues found.")
            else:
                print(f"\n⚠️  PASSED WITH WARNINGS ({self.stats['warnings']} warnings)")
        else:
            print(f"\n❌ VALIDATION FAILED ({self.stats['errors']} errors)")
        
        # Detailed results
        if self.stats['errors'] > 0 or self.stats['warnings'] > 0:
            print("\n📋 DETAILED RESULTS:")
            print("-" * 60)
            
            # Group by status
            errors = [r for r in self.results if r.status == 'fail']
            warnings = [r for r in self.results if r.status == 'warning']
            
            if errors:
                print("\n❌ ERRORS:")
                for result in errors:
                    line_info = f":{result.line_number}" if result.line_number else ""
                    print(f"  {result.file_path}{line_info} - {result.message}")
            
            if warnings:
                print("\n⚠️  WARNINGS:")
                for result in warnings:
                    line_info = f":{result.line_number}" if result.line_number else ""
                    print(f"  {result.file_path}{line_info} - {result.message}")
        
        # Save detailed report
        self._save_json_report()
    
    def _save_json_report(self):
        """Save detailed report as JSON"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'statistics': self.stats,
            'results': [
                {
                    'file_path': r.file_path,
                    'check_type': r.check_type,
                    'status': r.status,
                    'message': r.message,
                    'line_number': r.line_number
                }
                for r in self.results
            ]
        }
        
        report_file = self.project_root / 'syntax_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sophia AI Platform Syntax Validator')
    parser.add_argument('--project-root', type=Path, help='Project root directory')
    parser.add_argument('--check', choices=[
        'python', 'shell', 'yaml', 'json', 'docker', 'security', 'imports', 'all'
    ], default='all', help='Specific check to run')
    
    args = parser.parse_args()
    
    validator = SyntaxValidator(args.project_root)
    
    if args.check == 'all':
        success = validator.validate_all()
    elif args.check == 'python':
        validator.validate_python_syntax()
        success = validator.stats['errors'] == 0
    elif args.check == 'shell':
        validator.validate_shell_scripts()
        success = validator.stats['errors'] == 0
    elif args.check == 'yaml':
        validator.validate_yaml_json()
        success = validator.stats['errors'] == 0
    elif args.check == 'docker':
        validator.validate_docker_files()
        success = validator.stats['errors'] == 0
    elif args.check == 'security':
        validator.check_security_issues()
        success = validator.stats['errors'] == 0
    elif args.check == 'imports':
        validator.validate_imports()
        success = validator.stats['errors'] == 0
    
    if args.check != 'all':
        validator.generate_report()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

