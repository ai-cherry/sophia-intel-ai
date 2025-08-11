#!/usr/bin/env python3
"""
Repository Audit Tool for SOPHIA Intel
=====================================
Conducts comprehensive analysis to identify:
- Code duplication patterns  
- Configuration inconsistencies
- Dead/unused imports and modules
- Circular import dependencies
- Consolidation opportunities

Part of MEGA PROMPT Step 0-A: Full Repository Re-Audit
"""
import ast
import json
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DuplicationReport:
    total_lines: int
    duplicate_lines: int
    duplicate_percentage: float
    duplicate_blocks: List[Dict]

@dataclass
class ConfigInconsistency:
    key: str
    sources: List[str]
    values: List[str]
    issue_type: str  # "mismatch", "missing", "duplicate"

@dataclass
class ModuleAnalysis:
    path: str
    imports: Set[str]
    exports: Set[str]
    functions: Set[str]
    classes: Set[str]
    responsibilities: Set[str]

class RepoAuditor:
    """Comprehensive repository auditor for consolidation planning."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.python_files = list(self.repo_path.rglob("*.py"))
        self.config_files = list(self.repo_path.rglob("*.yaml")) + list(self.repo_path.rglob("*.yml")) + [self.repo_path / ".env.example"]
        
        # Results storage
        self.module_analysis = {}
        self.duplications = []
        self.config_issues = []
        self.circular_imports = []
        
    def run_full_audit(self) -> Dict:
        """Run complete audit and return consolidated report."""
        print("🔍 Starting SOPHIA Repository Audit...")
        
        # Core analyses
        duplication_report = self.analyze_code_duplication()
        config_issues = self.analyze_config_consistency() 
        circular_imports = self.detect_circular_imports()
        module_analysis = self.analyze_module_responsibilities()
        unused_code = self.find_unused_code()
        lint_baseline = self.capture_lint_baseline()
        
        # Generate consolidation recommendations
        consolidation_plan = self.generate_consolidation_plan()
        
        report = {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "repository_stats": self.get_repo_stats(),
            "duplication_analysis": duplication_report,
            "config_inconsistencies": config_issues,
            "circular_imports": circular_imports,
            "module_analysis": module_analysis,
            "unused_code": unused_code,
            "lint_baseline": lint_baseline,
            "consolidation_recommendations": consolidation_plan
        }
        
        # Save detailed report
        self.save_reports(report)
        return report
    
    def analyze_code_duplication(self) -> Dict:
        """Detect code duplication using AST-based analysis."""
        print("  📝 Analyzing code duplication...")
        
        # Extract function/class signatures and content hashes
        code_blocks = {}
        total_lines = 0
        
        for file_path in self.python_files:
            if file_path.name.startswith('.') or 'venv' in str(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                total_lines += len(content.splitlines())
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        # Extract code block
                        start_line = node.lineno
                        end_line = getattr(node, 'end_lineno', start_line + 10)
                        lines = content.splitlines()[start_line-1:end_line]
                        block_content = '\n'.join(lines)
                        
                        # Create content hash (ignore whitespace differences)
                        normalized = re.sub(r'\s+', ' ', block_content).strip()
                        content_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
                        
                        if content_hash not in code_blocks:
                            code_blocks[content_hash] = []
                        code_blocks[content_hash].append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "name": node.name,
                            "type": type(node).__name__,
                            "lines": len(lines),
                            "content_preview": normalized[:100] + "..." if len(normalized) > 100 else normalized
                        })
                        
            except Exception as e:
                print(f"    ⚠️ Error parsing {file_path}: {e}")
                continue
        
        # Find duplicates
        duplicates = {h: blocks for h, blocks in code_blocks.items() if len(blocks) > 1}
        duplicate_lines = sum(sum(b["lines"] for b in blocks) for blocks in duplicates.values())
        
        return {
            "total_lines_analyzed": total_lines,
            "duplicate_lines": duplicate_lines,
            "duplication_percentage": round((duplicate_lines / total_lines) * 100, 2) if total_lines > 0 else 0,
            "duplicate_blocks_count": len(duplicates),
            "duplicate_blocks": list(duplicates.values())[:10]  # Top 10 for reporting
        }
    
    def analyze_config_consistency(self) -> List[Dict]:
        """Find configuration key inconsistencies across files."""
        print("  ⚙️ Analyzing configuration consistency...")
        
        config_keys = defaultdict(list)
        
        # Extract from Python files (settings usage)
        for file_path in self.python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                # Find settings.KEY_NAME patterns
                settings_refs = re.findall(r'settings\.([A-Z_]+)', content)
                # Find os.getenv patterns  
                env_refs = re.findall(r'os\.getenv\(["\']([A-Z_]+)["\']', content)
                
                for key in settings_refs + env_refs:
                    config_keys[key].append({
                        "file": str(file_path.relative_to(self.repo_path)),
                        "type": "python_usage"
                    })
                    
            except Exception:
                continue
        
        # Extract from config files
        yaml_files = [f for f in self.config_files if f.suffix in ['.yaml', '.yml']]
        for file_path in yaml_files:
            try:
                import yaml
                content = file_path.read_text(encoding='utf-8')
                data = yaml.safe_load(content) or {}
                
                def extract_keys(obj, prefix=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            full_key = f"{prefix}{k}".upper()
                            config_keys[full_key].append({
                                "file": str(file_path.relative_to(self.repo_path)),
                                "type": "yaml_definition", 
                                "value": str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
                            })
                            if isinstance(v, dict):
                                extract_keys(v, f"{k}_")
                                
                extract_keys(data)
                
            except Exception:
                continue
        
        # Extract from .env.example
        env_file = self.repo_path / ".env.example"
        if env_file.exists():
            try:
                content = env_file.read_text(encoding='utf-8')
                for line in content.splitlines():
                    if '=' in line and not line.strip().startswith('#'):
                        key = line.split('=')[0].strip()
                        value = line.split('=')[1].strip()
                        config_keys[key].append({
                            "file": ".env.example",
                            "type": "env_definition",
                            "value": value
                        })
            except Exception:
                pass
        
        # Find inconsistencies
        issues = []
        for key, sources in config_keys.items():
            # Check for multiple definitions with different values
            definitions = [s for s in sources if s["type"] in ["yaml_definition", "env_definition"]]
            if len(definitions) > 1:
                values = [d.get("value", "") for d in definitions]
                if len(set(values)) > 1:
                    issues.append({
                        "key": key,
                        "issue": "value_mismatch",
                        "sources": definitions,
                        "severity": "high"
                    })
            
            # Check for usage without definition
            usages = [s for s in sources if s["type"] == "python_usage"] 
            if usages and not definitions:
                issues.append({
                    "key": key,
                    "issue": "used_but_not_defined",
                    "sources": usages,
                    "severity": "medium"
                })
        
        return issues
    
    def detect_circular_imports(self) -> List[Dict]:
        """Detect circular import dependencies."""
        print("  🔄 Detecting circular imports...")
        
        import_graph = defaultdict(set)
        
        for file_path in self.python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                module_name = str(file_path.relative_to(self.repo_path)).replace('/', '.').replace('.py', '')
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_graph[module_name].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_graph[module_name].add(node.module)
                            
            except Exception:
                continue
        
        # Find cycles using DFS
        def find_cycles(graph):
            cycles = []
            visited = set()
            path = []
            
            def dfs(node):
                if node in path:
                    cycle_start = path.index(node)
                    cycles.append(path[cycle_start:] + [node])
                    return
                if node in visited:
                    return
                    
                visited.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor in graph:  # Only follow internal modules
                        dfs(neighbor)
                        
                path.pop()
            
            for node in graph:
                if node not in visited:
                    dfs(node)
                    
            return cycles
        
        cycles = find_cycles(import_graph)
        return [{"cycle": cycle, "length": len(cycle)} for cycle in cycles]
    
    def analyze_module_responsibilities(self) -> Dict:
        """Analyze module responsibilities for consolidation opportunities."""
        print("  📋 Analyzing module responsibilities...")
        
        modules = {}
        
        for file_path in self.python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                # Extract responsibilities based on names and docstrings
                responsibilities = set()
                
                # From docstrings
                if ast.get_docstring(tree):
                    doc = ast.get_docstring(tree).lower()
                    if any(word in doc for word in ['agent', 'llm', 'ai']):
                        responsibilities.add('agent_system')
                    if any(word in doc for word in ['memory', 'vector', 'embed']):
                        responsibilities.add('memory_system')  
                    if any(word in doc for word in ['config', 'setting']):
                        responsibilities.add('configuration')
                    if any(word in doc for word in ['api', 'endpoint', 'service']):
                        responsibilities.add('api_service')
                
                # From class and function names
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        name_lower = node.name.lower()
                        if 'agent' in name_lower:
                            responsibilities.add('agent_system')
                        if any(word in name_lower for word in ['memory', 'embed', 'vector']):
                            responsibilities.add('memory_system')
                        if any(word in name_lower for word in ['config', 'setting']):
                            responsibilities.add('configuration')
                        if any(word in name_lower for word in ['client', 'api', 'service']):
                            responsibilities.add('api_service')
                        if 'test' in name_lower:
                            responsibilities.add('testing')
                
                modules[str(file_path.relative_to(self.repo_path))] = {
                    "responsibilities": list(responsibilities),
                    "lines": len(content.splitlines()),
                    "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                    "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                }
                
            except Exception:
                continue
                
        return modules
    
    def find_unused_code(self) -> Dict:
        """Find potentially unused imports and functions."""
        print("  🗑️ Finding unused code...")
        
        # Run ruff to get unused imports
        import subprocess
        try:
            result = subprocess.run(['ruff', 'check', '--select=F401', '--format=json', '.'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                unused_imports = json.loads(result.stdout) if result.stdout.strip() else []
            else:
                unused_imports = []
        except Exception:
            unused_imports = []
        
        return {
            "unused_imports_count": len(unused_imports),
            "unused_imports": unused_imports[:20]  # Limit for reporting
        }
    
    def capture_lint_baseline(self) -> Dict:
        """Capture current linting state as baseline."""
        print("  ✅ Capturing lint baseline...")
        
        import subprocess
        
        tools = {
            'ruff': ['ruff', 'check', '.'],
            'black': ['black', '--check', '--diff', '.']
        }
        
        results = {}
        for tool, cmd in tools.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                results[tool] = {
                    "exit_code": result.returncode,
                    "issues_count": len(result.stdout.splitlines()) if result.stdout else 0,
                    "passed": result.returncode == 0
                }
            except Exception as e:
                results[tool] = {
                    "exit_code": -1,
                    "error": str(e),
                    "passed": False
                }
        
        return results
    
    def generate_consolidation_plan(self) -> Dict:
        """Generate consolidation recommendations based on analysis."""
        print("  📋 Generating consolidation plan...")
        
        recommendations = {
            "duplicates_to_merge": [],
            "config_consolidations": [],
            "module_consolidations": [],
            "cleanup_actions": []
        }
        
        # Config consolidation recommendations
        for issue in self.config_issues:
            if issue.get("issue") == "value_mismatch":
                recommendations["config_consolidations"].append({
                    "action": "resolve_config_mismatch",
                    "key": issue["key"],
                    "recommendation": f"Standardize {issue['key']} value across all config files"
                })
        
        # Module consolidation opportunities
        responsibility_groups = defaultdict(list)
        if hasattr(self, 'module_analysis'):
            for module_path, analysis in self.module_analysis.items():
                for resp in analysis.get("responsibilities", []):
                    responsibility_groups[resp].append(module_path)
        
        for responsibility, modules in responsibility_groups.items():
            if len(modules) > 2:  # Multiple modules handling same responsibility
                recommendations["module_consolidations"].append({
                    "responsibility": responsibility,
                    "modules": modules,
                    "recommendation": f"Consider consolidating {responsibility} logic"
                })
        
        # Cleanup actions
        recommendations["cleanup_actions"].extend([
            {"action": "fix_unused_imports", "description": "Remove unused imports found by ruff"},
            {"action": "standardize_formatting", "description": "Apply black formatting"},
            {"action": "remove_dead_code", "description": "Remove unused functions and variables"}
        ])
        
        return recommendations
    
    def get_repo_stats(self) -> Dict:
        """Get basic repository statistics."""
        python_lines = sum(len(f.read_text(encoding='utf-8', errors='ignore').splitlines()) 
                          for f in self.python_files if f.is_file())
        
        return {
            "total_python_files": len(self.python_files),
            "total_python_lines": python_lines,
            "config_files": len(self.config_files),
            "audit_scope": str(self.repo_path.absolute())
        }
    
    def save_reports(self, report: Dict):
        """Save audit reports to files."""
        # JSON report for programmatic use
        json_path = self.repo_path / "reports" / "repo_audit.json"
        json_path.parent.mkdir(exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Detailed audit report saved to: {json_path}")
        
        # Summary report for human review
        self.generate_summary_report(report)
    
    def generate_summary_report(self, report: Dict):
        """Generate human-readable summary report."""
        summary_path = self.repo_path / "reports" / "audit_summary.md"
        
        duplication = report["duplication_analysis"]
        config_issues = report["config_inconsistencies"] 
        
        content = f"""# SOPHIA Repository Audit Summary
Generated: {report["audit_timestamp"]}

## 📊 Repository Statistics
- **Python Files:** {report["repository_stats"]["total_python_files"]}
- **Total Lines:** {report["repository_stats"]["total_python_lines"]:,}
- **Config Files:** {report["repository_stats"]["config_files"]}

## 🔍 Duplication Analysis
- **Duplicate Lines:** {duplication["duplicate_lines"]} ({duplication["duplication_percentage"]}%)
- **Duplicate Blocks:** {duplication["duplicate_blocks_count"]}
- **Threshold Target:** < 2% (current: {duplication["duplication_percentage"]}%)

## ⚙️ Configuration Issues
- **Total Issues:** {len(config_issues)}
- **High Severity:** {len([i for i in config_issues if i.get("severity") == "high"])}
- **Medium Severity:** {len([i for i in config_issues if i.get("severity") == "medium"])}

## 🔄 Circular Imports  
- **Cycles Found:** {len(report["circular_imports"])}

## ✅ Lint Baseline
- **Ruff Status:** {"✅ PASSED" if report["lint_baseline"]["ruff"]["passed"] else "❌ FAILED"}
- **Black Status:** {"✅ PASSED" if report["lint_baseline"]["black"]["passed"] else "❌ FAILED"}

## 📋 Next Steps
1. Address high-severity configuration mismatches
2. Reduce code duplication to < 2%
3. Fix circular import dependencies
4. Clean up unused imports ({report["unused_code"]["unused_imports_count"]} found)

## 🎯 MEGA PROMPT Compliance
{"✅ READY for Step 1" if duplication["duplication_percentage"] < 2 and len(report["circular_imports"]) == 0 else "⚠️ BLOCKED - needs consolidation"}
"""
        
        with open(summary_path, 'w') as f:
            f.write(content)
            
        print(f"📋 Summary report saved to: {summary_path}")

def main():
    """Run repository audit."""
    auditor = RepoAuditor()
    report = auditor.run_full_audit()
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 SOPHIA REPOSITORY AUDIT COMPLETE")
    print("="*60)
    print(f"📊 Duplication: {report['duplication_analysis']['duplication_percentage']}%")
    print(f"⚙️ Config Issues: {len(report['config_inconsistencies'])}")
    print(f"🔄 Circular Imports: {len(report['circular_imports'])}")
    print(f"🗑️ Unused Imports: {report['unused_code']['unused_imports_count']}")
    
    # Gate decision
    duplication_ok = report['duplication_analysis']['duplication_percentage'] < 2
    no_circular = len(report['circular_imports']) == 0
    
    if duplication_ok and no_circular:
        print("\n✅ GATE: CONTINUE - Repository ready for consolidation")
        return 0
    else:
        print("\n❌ GATE: BLOCKED - Needs consolidation before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())