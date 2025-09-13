#!/usr/bin/env python3
"""
Deep Configuration Audit Script
================================
Finds all configuration conflicts, tech debt, and confusion points
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

class ConfigAuditor:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path)
        self.issues = []
        self.conflicts = []
        self.tech_debt = []
        self.redundant_files = []
        
    def audit_all(self):
        """Run complete audit"""
        print("="*70)
        print("DEEP CONFIGURATION AUDIT")
        print("="*70)
        
        # 1. Find all configuration files
        print("\n1️⃣ CONFIGURATION FILES INVENTORY:")
        print("-"*50)
        config_files = self.find_config_files()
        
        # 2. Check for model configurations
        print("\n2️⃣ MODEL CONFIGURATIONS:")
        print("-"*50)
        model_configs = self.find_model_configs()
        
        # 3. Check for Portkey configurations
        print("\n3️⃣ PORTKEY CONFIGURATIONS:")
        print("-"*50)
        portkey_configs = self.find_portkey_configs()
        
        # 4. Check for conflicts
        print("\n4️⃣ CONFIGURATION CONFLICTS:")
        print("-"*50)
        self.check_conflicts()
        
        # 5. Check for tech debt
        print("\n5️⃣ TECH DEBT:")
        print("-"*50)
        self.check_tech_debt()
        
        # 6. Summary and recommendations
        print("\n6️⃣ SUMMARY & RECOMMENDATIONS:")
        print("-"*50)
        self.print_summary()
        
    def find_config_files(self) -> Dict[str, List[Path]]:
        """Find all configuration files"""
        configs = {
            "yaml": [],
            "json": [],
            "env": [],
            "py_config": []
        }
        
        # Find YAML/JSON configs
        for ext in ["yaml", "yml", "json"]:
            files = list(self.root.glob(f"**/*.{ext}"))
            # Filter out node_modules, .git, __pycache__
            files = [f for f in files if not any(
                x in str(f) for x in ["node_modules", ".git", "__pycache__", "venv", ".next"]
            )]
            
            if ext in ["yaml", "yml"]:
                configs["yaml"].extend(files)
            else:
                configs["json"].extend(files)
        
        # Find .env files
        env_files = list(self.root.glob(".env*"))
        configs["env"] = env_files
        
        # Find Python config files
        py_configs = []
        for py_file in self.root.glob("**/*config*.py"):
            if "__pycache__" not in str(py_file):
                py_configs.append(py_file)
        configs["py_config"] = py_configs
        
        # Print findings
        print(f"📁 YAML files: {len(configs['yaml'])}")
        print(f"📁 JSON files: {len(configs['json'])}")
        print(f"📁 ENV files: {len(configs['env'])}")
        print(f"📁 Python configs: {len(configs['py_config'])}")
        
        # Show key files
        important_configs = [
            "user_models_config.yaml",
            "portkey_config.json",
            "litellm_squad_config.yaml",
            "unified_squad_config.yaml",
            "openrouter_squad_config.yaml",
            ".env.portkey"
        ]
        
        print("\n🔍 Key Configuration Files:")
        for name in important_configs:
            found = [f for f in configs["yaml"] + configs["json"] + configs["env"] if name in str(f)]
            if found:
                print(f"  ✅ {name}: {found[0]}")
            else:
                print(f"  ❌ {name}: NOT FOUND")
        
        return configs
    
    def find_model_configs(self) -> List[Tuple[Path, str]]:
        """Find all model configuration patterns"""
        model_patterns = [
            r"model_policy",
            r"MODEL_CONFIGS",
            r"APPROVED_MODELS",
            r"PORTKEY_VIRTUAL_KEYS",
            r"models_config",
            r"model_list",
            r"routing_policies"
        ]
        
        findings = []
        
        # Search Python files
        for py_file in self.root.glob("**/*.py"):
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    for pattern in model_patterns:
                        if re.search(pattern, content):
                            findings.append((py_file, pattern))
            except:
                pass
        
        # Group by file
        file_patterns = {}
        for file, pattern in findings:
            if file not in file_patterns:
                file_patterns[file] = []
            file_patterns[file].append(pattern)
        
        # Show findings
        if file_patterns:
            print("⚠️  Found hardcoded model configurations in:")
            for file, patterns in list(file_patterns.items())[:10]:
                relative_path = file.relative_to(self.root)
                print(f"  • {relative_path}")
                print(f"    Patterns: {', '.join(set(patterns))}")
        else:
            print("✅ No hardcoded model configurations found")
        
        return findings
    
    def find_portkey_configs(self) -> List[Path]:
        """Find all Portkey-related configurations"""
        portkey_files = []
        
        # Search for Portkey references
        for file in self.root.glob("**/*"):
            if file.is_file() and file.suffix in ['.py', '.yaml', '.yml', '.json', '.env']:
                if "__pycache__" in str(file) or "node_modules" in str(file):
                    continue
                
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if "portkey" in content.lower() or "virtual_key" in content.lower():
                            portkey_files.append(file)
                except:
                    pass
        
        # Group by type
        portkey_by_type = {
            "env": [],
            "config": [],
            "code": []
        }
        
        for file in portkey_files:
            if ".env" in file.name:
                portkey_by_type["env"].append(file)
            elif file.suffix in ['.yaml', '.yml', '.json']:
                portkey_by_type["config"].append(file)
            else:
                portkey_by_type["code"].append(file)
        
        print(f"🔑 Portkey references found:")
        print(f"  ENV files: {len(portkey_by_type['env'])}")
        print(f"  Config files: {len(portkey_by_type['config'])}")
        print(f"  Code files: {len(portkey_by_type['code'])}")
        
        # Show key Portkey files
        if portkey_by_type["env"]:
            print("\n  Key Portkey ENV files:")
            for file in portkey_by_type["env"][:5]:
                print(f"    • {file.relative_to(self.root)}")
        
        return portkey_files
    
    def check_conflicts(self):
        """Check for configuration conflicts"""
        
        # 1. Multiple squad configs
        squad_configs = list(self.root.glob("**/*squad*.yaml"))
        squad_configs.extend(list(self.root.glob("**/*squad*.json")))
        
        if len(squad_configs) > 1:
            self.conflicts.append({
                "type": "Multiple Squad Configs",
                "files": [str(f.relative_to(self.root)) for f in squad_configs],
                "recommendation": "Use only config/user_models_config.yaml"
            })
        
        # 2. Multiple model lists
        model_files = []
        for pattern in ["*model*.yaml", "*model*.json", "*models*.py"]:
            model_files.extend(list(self.root.glob(f"**/{pattern}")))
        
        # Filter out our central config
        model_files = [f for f in model_files if "user_models_config" not in str(f)]
        model_files = [f for f in model_files if "model_manager" not in str(f)]
        model_files = [f for f in model_files if "__pycache__" not in str(f)]
        
        if len(model_files) > 5:  # Threshold for concern
            self.conflicts.append({
                "type": "Multiple Model Configurations",
                "count": len(model_files),
                "recommendation": "Consolidate to user_models_config.yaml"
            })
        
        # 3. Multiple Portkey configs
        portkey_envs = list(self.root.glob(".env*"))
        portkey_count = sum(1 for f in portkey_envs if "portkey" in f.name.lower())
        
        if portkey_count > 1:
            self.conflicts.append({
                "type": "Multiple Portkey ENV files",
                "count": portkey_count,
                "recommendation": "Use only .env.portkey"
            })
        
        # Print conflicts
        if self.conflicts:
            print("⚠️  CONFLICTS FOUND:")
            for conflict in self.conflicts:
                print(f"\n  Issue: {conflict['type']}")
                if 'files' in conflict:
                    print(f"  Files: {', '.join(conflict['files'][:5])}")
                if 'count' in conflict:
                    print(f"  Count: {conflict['count']}")
                print(f"  ➡️  {conflict['recommendation']}")
        else:
            print("✅ No major conflicts found")
    
    def check_tech_debt(self):
        """Check for technical debt"""
        
        # 1. Old model references
        old_models = [
            "gpt-4", "gpt-3.5", "claude-2", "claude-3", 
            "llama-2", "llama-3", "palm", "gemini-1"
        ]
        
        for py_file in self.root.glob("**/*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    for old_model in old_models:
                        if old_model in content:
                            self.tech_debt.append({
                                "type": "Old Model Reference",
                                "file": str(py_file.relative_to(self.root)),
                                "model": old_model
                            })
                            break
            except:
                pass
        
        # 2. Hardcoded API keys
        for file in self.root.glob("**/*.py"):
            if "__pycache__" in str(file):
                continue
            
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if re.search(r'api_key\s*=\s*["\'][^"\']+["\']', content):
                        if "os.getenv" not in content and "os.environ" not in content:
                            self.tech_debt.append({
                                "type": "Hardcoded API Key",
                                "file": str(file.relative_to(self.root))
                            })
            except:
                pass
        
        # 3. Duplicate functionality
        duplicate_patterns = {
            "model routing": ["route_model", "select_model", "get_model_for"],
            "config loading": ["load_config", "get_config", "read_config"]
        }
        
        for category, patterns in duplicate_patterns.items():
            files_with_pattern = set()
            for pattern in patterns:
                for py_file in self.root.glob("**/*.py"):
                    if "__pycache__" in str(py_file):
                        continue
                    
                    try:
                        with open(py_file, 'r') as f:
                            if pattern in f.read():
                                files_with_pattern.add(py_file)
                    except:
                        pass
            
            if len(files_with_pattern) > 3:
                self.tech_debt.append({
                    "type": f"Duplicate {category}",
                    "count": len(files_with_pattern),
                    "files": [str(f.relative_to(self.root)) for f in list(files_with_pattern)[:3]]
                })
        
        # Print tech debt
        if self.tech_debt:
            print("🔧 TECH DEBT FOUND:")
            
            # Group by type
            debt_by_type = {}
            for debt in self.tech_debt:
                debt_type = debt["type"]
                if debt_type not in debt_by_type:
                    debt_by_type[debt_type] = []
                debt_by_type[debt_type].append(debt)
            
            for debt_type, items in debt_by_type.items():
                print(f"\n  {debt_type}: {len(items)} instances")
                for item in items[:3]:  # Show first 3
                    if 'file' in item:
                        print(f"    • {item['file']}")
                    if 'model' in item:
                        print(f"      Model: {item['model']}")
        else:
            print("✅ No significant tech debt found")
    
    def print_summary(self):
        """Print summary and recommendations"""
        
        print("\n🎯 RECOMMENDATIONS:")
        print("-"*50)
        
        recommendations = [
            {
                "priority": "HIGH",
                "action": "Remove conflicting squad configs",
                "files": [
                    "config/litellm_squad_config.yaml",
                    "config/openrouter_squad_config.yaml",
                    "config/unified_squad_config.yaml"
                ],
                "reason": "Replaced by user_models_config.yaml"
            },
            {
                "priority": "HIGH",
                "action": "Update import statements",
                "files": [
                    "builder_cli/lib/providers.py",
                    "builder_cli/lib/agents.py",
                    "app/core/portkey_manager.py"
                ],
                "code": "from config.integration_adapter import get_unified_router"
            },
            {
                "priority": "MEDIUM",
                "action": "Remove old model references",
                "details": "Update any references to GPT-4, Claude-3, etc. to 2025 models"
            },
            {
                "priority": "MEDIUM",
                "action": "Consolidate ENV files",
                "keep": [".env", ".env.portkey"],
                "remove": "Other .env.* files if not needed"
            },
            {
                "priority": "LOW",
                "action": "Archive old configs",
                "details": "Remove obsolete config files or move to tmp/cleanup-<timestamp>"
            }
        ]
        
        for rec in recommendations:
            print(f"\n{rec['priority']} Priority:")
            print(f"  Action: {rec['action']}")
            if 'files' in rec:
                print(f"  Files: {', '.join(rec['files'])}")
            if 'code' in rec:
                print(f"  Add: {rec['code']}")
            if 'reason' in rec:
                print(f"  Reason: {rec['reason']}")
            if 'details' in rec:
                print(f"  Details: {rec['details']}")
        
        print("\n✅ CLEAN STATE CHECKLIST:")
        print("-"*50)
        print("□ Central config at config/user_models_config.yaml")
        print("□ Model manager at config/model_manager.py")
        print("□ Integration adapter at config/integration_adapter.py")
        print("□ All 3 apps import from integration_adapter")
        print("□ Old squad configs removed or archived")
        print("□ No hardcoded model lists in code")
        print("□ All models are 2025 versions")
        print("□ $1,000 daily budget configured")
        
        # Final stats
        total_issues = len(self.conflicts) + len(self.tech_debt)
        print(f"\n📊 AUDIT COMPLETE:")
        print(f"  Conflicts found: {len(self.conflicts)}")
        print(f"  Tech debt items: {len(self.tech_debt)}")
        print(f"  Total issues: {total_issues}")
        
        if total_issues == 0:
            print("\n🎉 Configuration is clean!")
        else:
            print(f"\n⚠️  {total_issues} issues need attention")

if __name__ == "__main__":
    auditor = ConfigAuditor("/Users/lynnmusil/sophia-intel-ai")
    auditor.audit_all()
