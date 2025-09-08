#!/usr/bin/env python3
"""
BRUTAL HONEST REPOSITORY AUDIT
No bullshit, no marketing speak - just the fucking truth about what's broken
"""

import os
import sys
import json
import subprocess
import glob
from collections import defaultdict, Counter
from pathlib import Path
import re

class BrutalRepoAudit:
    def __init__(self):
        self.repo_path = "/home/ubuntu/sophia-main"
        self.issues = []
        self.duplicates = []
        self.conflicts = []
        self.broken_shit = []
        self.working_shit = []
        
    def log_issue(self, category, severity, description, file_path=None):
        """Log an issue without any bullshit"""
        self.issues.append({
            "category": category,
            "severity": severity,
            "description": description,
            "file": file_path,
            "fix_needed": True
        })
        print(f"[{severity.upper()}] {category}: {description}")
        if file_path:
            print(f"    File: {file_path}")
    
    def scan_for_duplicates(self):
        """Find duplicate files and functionality"""
        print("\n🔍 SCANNING FOR DUPLICATES...")
        
        # Find files with similar names
        all_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git and other noise
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    all_files.append(os.path.join(root, file))
        
        # Group by base name patterns
        name_groups = defaultdict(list)
        for file_path in all_files:
            base_name = os.path.basename(file_path)
            # Remove version numbers, dates, etc.
            clean_name = re.sub(r'[_v0-9\-\.]+', '', base_name.lower())
            name_groups[clean_name].append(file_path)
        
        # Find actual duplicates
        for clean_name, files in name_groups.items():
            if len(files) > 1:
                # Check if they're actually similar
                similar_files = []
                for file_path in files:
                    base = os.path.basename(file_path)
                    if any(keyword in base.lower() for keyword in ['dashboard', 'secret', 'env', 'deploy', 'setup', 'config']):
                        similar_files.append(file_path)
                
                if len(similar_files) > 1:
                    self.log_issue("DUPLICATES", "HIGH", f"Multiple similar files found: {similar_files}")
                    self.duplicates.extend(similar_files)
    
    def scan_for_conflicts(self):
        """Find conflicting configurations and implementations"""
        print("\n⚔️ SCANNING FOR CONFLICTS...")
        
        # Find conflicting environment files
        env_files = glob.glob(f"{self.repo_path}/**/*.env*", recursive=True)
        env_files.extend(glob.glob(f"{self.repo_path}/**/env_*", recursive=True))
        
        if len(env_files) > 3:
            self.log_issue("CONFLICTS", "CRITICAL", f"Too many environment files ({len(env_files)}): {env_files}")
        
        # Find conflicting deployment scripts
        deploy_scripts = []
        for pattern in ['deploy*', '*deploy*', 'setup*', '*setup*']:
            deploy_scripts.extend(glob.glob(f"{self.repo_path}/**/{pattern}.sh", recursive=True))
            deploy_scripts.extend(glob.glob(f"{self.repo_path}/**/{pattern}.py", recursive=True))
        
        if len(deploy_scripts) > 5:
            self.log_issue("CONFLICTS", "HIGH", f"Too many deployment scripts ({len(deploy_scripts)})")
        
        # Find conflicting Docker files
        docker_files = glob.glob(f"{self.repo_path}/**/docker-compose*.yml", recursive=True)
        docker_files.extend(glob.glob(f"{self.repo_path}/**/Dockerfile*", recursive=True))
        
        if len(docker_files) > 4:
            self.log_issue("CONFLICTS", "MEDIUM", f"Multiple Docker configurations ({len(docker_files)})")
        
        # Find conflicting secret management
        secret_files = []
        for pattern in ['*secret*', '*env*manager*', '*pulumi*']:
            secret_files.extend(glob.glob(f"{self.repo_path}/**/{pattern}.py", recursive=True))
        
        if len(secret_files) > 3:
            self.log_issue("CONFLICTS", "CRITICAL", f"Multiple secret management systems ({len(secret_files)})")
    
    def test_what_works(self):
        """Test what actually fucking works"""
        print("\n🧪 TESTING WHAT ACTUALLY WORKS...")
        
        # Test Python files for syntax errors
        python_files = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
        broken_python = []
        working_python = []
        
        for py_file in python_files:
            if '__pycache__' in py_file or '.git' in py_file:
                continue
                
            try:
                result = subprocess.run(['python3', '-m', 'py_compile', py_file], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    working_python.append(py_file)
                else:
                    broken_python.append((py_file, result.stderr))
                    self.log_issue("BROKEN_CODE", "HIGH", f"Syntax error in {py_file}: {result.stderr.strip()}")
            except Exception as e:
                broken_python.append((py_file, str(e)))
                self.log_issue("BROKEN_CODE", "HIGH", f"Cannot compile {py_file}: {str(e)}")
        
        print(f"Python files: {len(working_python)} working, {len(broken_python)} broken")
        
        # Test shell scripts
        shell_scripts = glob.glob(f"{self.repo_path}/**/*.sh", recursive=True)
        broken_shell = []
        working_shell = []
        
        for sh_file in shell_scripts:
            try:
                result = subprocess.run(['bash', '-n', sh_file], capture_output=True, text=True)
                if result.returncode == 0:
                    working_shell.append(sh_file)
                else:
                    broken_shell.append((sh_file, result.stderr))
                    self.log_issue("BROKEN_SCRIPT", "MEDIUM", f"Shell syntax error in {sh_file}")
            except Exception as e:
                broken_shell.append((sh_file, str(e)))
        
        print(f"Shell scripts: {len(working_shell)} working, {len(broken_shell)} broken")
        
        # Test if key files exist and are executable
        key_files = [
            'deploy_multi_instance.sh',
            'setup_persistent_auth.sh', 
            'install_auto_login.sh',
            'create_system_service.sh',
            'sophia.sh'
        ]
        
        for key_file in key_files:
            file_path = os.path.join(self.repo_path, key_file)
            if os.path.exists(file_path):
                if os.access(file_path, os.X_OK):
                    self.working_shit.append(f"{key_file} (executable)")
                else:
                    self.log_issue("BROKEN_PERMS", "MEDIUM", f"{key_file} exists but not executable")
            else:
                self.log_issue("MISSING_FILE", "HIGH", f"Key file missing: {key_file}")
    
    def check_dependencies(self):
        """Check if dependencies are properly defined"""
        print("\n📦 CHECKING DEPENDENCIES...")
        
        # Find all requirements files
        req_files = glob.glob(f"{self.repo_path}/**/requirements*.txt", recursive=True)
        
        if not req_files:
            self.log_issue("MISSING_DEPS", "CRITICAL", "No requirements.txt files found")
        elif len(req_files) > 3:
            self.log_issue("CONFLICTS", "MEDIUM", f"Too many requirements files: {req_files}")
        
        # Check for import errors in Python files
        python_files = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
        import_issues = []
        
        for py_file in python_files[:10]:  # Sample first 10 files
            if '__pycache__' in py_file:
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                # Find imports
                imports = re.findall(r'^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
                
                # Check for common problematic imports
                problematic = ['fastapi', 'uvicorn', 'pulumi', 'requests', 'docker']
                for imp in imports:
                    if imp in problematic:
                        # Try to import it
                        try:
                            result = subprocess.run(['python3', '-c', f'import {imp}'], 
                                                  capture_output=True, text=True)
                            if result.returncode != 0:
                                import_issues.append((py_file, imp))
                        except:
                            pass
                            
            except Exception as e:
                pass
        
        if import_issues:
            self.log_issue("MISSING_DEPS", "HIGH", f"Import issues found: {len(import_issues)} files have missing dependencies")
    
    def check_configuration_mess(self):
        """Check for configuration file chaos"""
        print("\n⚙️ CHECKING CONFIGURATION CHAOS...")
        
        # Find all config files
        config_patterns = ['*.json', '*.yml', '*.yaml', '*.toml', '*.ini', '*.conf']
        config_files = []
        
        for pattern in config_patterns:
            config_files.extend(glob.glob(f"{self.repo_path}/**/{pattern}", recursive=True))
        
        # Group by type
        config_types = defaultdict(list)
        for config_file in config_files:
            if '.git' in config_file or '__pycache__' in config_file:
                continue
                
            base_name = os.path.basename(config_file).lower()
            
            if 'docker' in base_name:
                config_types['docker'].append(config_file)
            elif 'deploy' in base_name:
                config_types['deployment'].append(config_file)
            elif 'env' in base_name or 'secret' in base_name:
                config_types['environment'].append(config_file)
            elif 'prometheus' in base_name or 'grafana' in base_name:
                config_types['monitoring'].append(config_file)
            else:
                config_types['other'].append(config_file)
        
        # Report on chaos
        for config_type, files in config_types.items():
            if len(files) > 2:
                self.log_issue("CONFIG_CHAOS", "MEDIUM", f"Too many {config_type} configs: {len(files)} files")
    
    def check_secret_exposure(self):
        """Check for exposed secrets (the real shit)"""
        print("\n🔐 CHECKING FOR EXPOSED SECRETS...")
        
        # Patterns that indicate secrets
        secret_patterns = [
            r'pul-[a-f0-9]{40}',  # Pulumi tokens
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI keys
            r'secret_[a-zA-Z0-9_]+\.[a-zA-Z0-9]+',  # Lambda Labs keys
            r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',  # UUIDs (often API keys)
        ]
        
        exposed_secrets = []
        
        # Check all text files
        text_files = []
        for ext in ['*.py', '*.sh', '*.md', '*.txt', '*.yml', '*.yaml', '*.json']:
            text_files.extend(glob.glob(f"{self.repo_path}/**/{ext}", recursive=True))
        
        for file_path in text_files:
            if '.git' in file_path or '__pycache__' in file_path:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        exposed_secrets.append((file_path, len(matches)))
                        self.log_issue("EXPOSED_SECRETS", "CRITICAL", 
                                     f"Potential secrets found in {file_path}: {len(matches)} matches")
                        
            except Exception as e:
                pass
        
        return len(exposed_secrets)
    
    def generate_brutal_report(self):
        """Generate the brutal honest report"""
        print("\n" + "="*80)
        print("🔥 BRUTAL HONEST REPOSITORY AUDIT REPORT 🔥")
        print("="*80)
        
        # Count issues by severity
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']
        
        print(f"\n📊 ISSUE SUMMARY:")
        print(f"   CRITICAL: {len(critical_issues)}")
        print(f"   HIGH:     {len(high_issues)}")
        print(f"   MEDIUM:   {len(medium_issues)}")
        print(f"   TOTAL:    {len(self.issues)}")
        
        # Calculate a real fucking score
        total_weight = len(critical_issues) * 10 + len(high_issues) * 5 + len(medium_issues) * 2
        max_possible = 100  # Assume 10 critical issues would be 100% fucked
        
        fucked_percentage = min(100, (total_weight / max_possible) * 100)
        health_percentage = max(0, 100 - fucked_percentage)
        
        print(f"\n🎯 REAL STATUS:")
        print(f"   Repository Health: {health_percentage:.1f}%")
        print(f"   Fucked Level: {fucked_percentage:.1f}%")
        
        if health_percentage >= 80:
            status = "MOSTLY WORKING"
        elif health_percentage >= 60:
            status = "NEEDS WORK"
        elif health_percentage >= 40:
            status = "PRETTY FUCKED"
        else:
            status = "COMPLETELY FUCKED"
        
        print(f"   Overall Status: {status}")
        
        # Top issues to fix
        print(f"\n🔥 TOP ISSUES TO FIX:")
        critical_and_high = critical_issues + high_issues
        for i, issue in enumerate(critical_and_high[:10], 1):
            print(f"   {i}. [{issue['severity']}] {issue['description']}")
        
        # What actually works
        print(f"\n✅ WHAT ACTUALLY WORKS:")
        for item in self.working_shit[:10]:
            print(f"   - {item}")
        
        # Save detailed report
        report = {
            "timestamp": "2025-08-09",
            "health_percentage": health_percentage,
            "fucked_percentage": fucked_percentage,
            "status": status,
            "total_issues": len(self.issues),
            "critical_issues": len(critical_issues),
            "high_issues": len(high_issues),
            "medium_issues": len(medium_issues),
            "all_issues": self.issues,
            "working_components": self.working_shit,
            "duplicates_found": len(self.duplicates),
            "conflicts_found": len(self.conflicts)
        }
        
        with open(f"{self.repo_path}/BRUTAL_AUDIT_REPORT.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: BRUTAL_AUDIT_REPORT.json")
        
        return health_percentage, status
    
    def run_full_audit(self):
        """Run the complete brutal audit"""
        print("🔥 STARTING BRUTAL REPOSITORY AUDIT...")
        print("No bullshit, no marketing speak - just the fucking truth")
        print("-" * 60)
        
        self.scan_for_duplicates()
        self.scan_for_conflicts()
        self.test_what_works()
        self.check_dependencies()
        self.check_configuration_mess()
        exposed_count = self.check_secret_exposure()
        
        health, status = self.generate_brutal_report()
        
        print(f"\n🎯 FINAL VERDICT:")
        print(f"   Your repository is {health:.1f}% healthy")
        print(f"   Status: {status}")
        print(f"   Exposed secrets: {exposed_count}")
        print(f"   Issues to fix: {len(self.issues)}")
        
        if health >= 80:
            print("   🎉 Actually not bad! Just fix the critical issues.")
        elif health >= 60:
            print("   ⚠️ Needs some work but salvageable.")
        elif health >= 40:
            print("   🔥 Pretty fucked but can be fixed.")
        else:
            print("   💀 This is a disaster. Start over or major cleanup needed.")
        
        return health, status

if __name__ == "__main__":
    auditor = BrutalRepoAudit()
    health, status = auditor.run_full_audit()
    
    if health < 60:
        sys.exit(1)
    else:
        sys.exit(0)

