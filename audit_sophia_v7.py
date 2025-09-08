#!/usr/bin/env python3
"""
Sophia AI V7 Migration Audit Script
Comprehensive audit for Agno integration and Claude MAL/RBAC implementation
"""

import pandas as pd
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import yaml

class SophiaV7Auditor:
    def __init__(self):
        self.audit_results = {}
        self.timestamp = datetime.now().isoformat()

    def run_comprehensive_audit(self):
        """Run complete audit for V7 migration"""
        print("🚀 SOPHIA AI V7 MIGRATION AUDIT - AGNO INTEGRATION")
        print("=" * 60)

        # Step 1: RBAC Policy Evaluation
        print("\n🔐 STEP 1: RBAC POLICY EVALUATION")
        self.audit_rbac_policies()

        # Step 2: Dependency Analysis
        print("\n📦 STEP 2: DEPENDENCY ANALYSIS")
        self.audit_dependencies()

        # Step 3: Git Trends Analysis (last 100 commits)
        print("\n📈 STEP 3: GIT TRENDS ANALYSIS")
        self.audit_git_trends()

        # Step 4: Architecture Assessment
        print("\n🏗️ STEP 4: ARCHITECTURE ASSESSMENT")
        self.audit_architecture()

        # Step 5: Agno Readiness Check
        print("\n🤖 STEP 5: AGNO READINESS ASSESSMENT")
        self.audit_agno_readiness()

        # Generate final report
        self.generate_audit_report()

    def audit_rbac_policies(self):
        """Audit existing RBAC policies and test Cerbos integration"""

        # Check existing RBAC files
        rbac_files = [
            "./config/security/rbac_rules.json",
            "./core/security/dynamic_rbac_optimizer.py",
            "./mcp/security/rbac.py"
        ]

        rbac_status = {}

        for file_path in rbac_files:
            if os.path.exists(file_path):
                rbac_status[file_path] = "exists"
                if file_path.endswith('.json'):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            rbac_status[f"{file_path}_rules"] = len(data) if isinstance(data, list) else len(data.keys())
                    except Exception as e:
                        rbac_status[f"{file_path}_error"] = str(e)
            else:
                rbac_status[file_path] = "missing"

        # Sample Cerbos policy evaluation
        sample_policy_eval = self.create_sample_cerbos_policy()

        self.audit_results["rbac"] = {
            "existing_files": rbac_status,
            "sample_policy": sample_policy_eval,
            "readiness_score": self.calculate_rbac_readiness(rbac_status)
        }

        print(f"  ✅ RBAC files found: {len([k for k, v in rbac_status.items() if v == 'exists'])}")
        print(f"  📊 RBAC readiness score: {self.audit_results['rbac']['readiness_score']:.1f}/10")

    def create_sample_cerbos_policy(self):
        """Create sample Cerbos policy for Sophia domains"""

        policy = {
            "apiVersion": "api.cerbos.dev/v1",
            "resourcePolicy": {
                "version": "default",
                "resource": "sophia:domain",
                "rules": [
                    {
                        "actions": ["read", "write", "admin"],
                        "effect": "EFFECT_ALLOW",
                        "roles": ["admin"],
                        "condition": {"match": {"expr": "true"}}
                    },
                    {
                        "actions": ["read", "write"],
                        "effect": "EFFECT_ALLOW",
                        "roles": ["sales_manager"],
                        "condition": {
                            "match": {
                                "expr": "request.resource.attr.domain in ['gong', 'hubspot', 'salesforce']"
                            }
                        }
                    },
                    {
                        "actions": ["read", "write", "execute"],
                        "effect": "EFFECT_ALLOW",
                        "roles": ["developer"],
                        "condition": {
                            "match": {
                                "expr": "request.resource.attr.domain in ['artemis', 'github', 'linear']"
                            }
                        }
                    }
                ]
            }
        }

        # Save sample policy
        with open("cerbos_sophia_v7_policy.yaml", "w") as f:
            yaml.dump(policy, f, default_flow_style=False)

        # Test policy evaluation
        sophia_cases = [
            {"principal": "admin", "resource": "sophia:gong", "action": "read", "expected": True},
            {"principal": "sales_manager", "resource": "sophia:hubspot", "action": "write", "expected": True},
            {"principal": "developer", "resource": "sophia:artemis", "action": "execute", "expected": True},
            {"principal": "sales_manager", "resource": "sophia:artemis", "action": "read", "expected": False}
        ]

        policy_results = []
        for test in sophia_cases:
            result = self.evaluate_policy_rule(test, policy["resourcePolicy"]["rules"])
            policy_results.append({
                "test": test,
                "result": result,
                "passed": result == test["expected"]
            })

        success_rate = sum(1 for r in policy_results if r["passed"]) / len(policy_results) * 100

        print(f"  🧪 Policy evaluation tests: {len(policy_results)} tests, {success_rate:.0f}% success rate")

        return {
            "policy": policy,
            "sophia_results": policy_results,
            "success_rate": success_rate
        }

    def evaluate_policy_rule(self, sophia_case, rules):
        """Simple policy rule evaluation"""
        principal = sophia_case["principal"]
        action = sophia_case["action"]
        resource = sophia_case["resource"]

        for rule in rules:
            if principal in rule["roles"] and action in rule["actions"]:
                # Simple condition evaluation
                condition = rule["condition"]["match"]["expr"]
                if condition == "true":
                    return rule["effect"] == "EFFECT_ALLOW"
                elif "domain in" in condition and resource:
                    domain = resource.split(":")[-1]
                    if "['gong', 'hubspot', 'salesforce']" in condition:
                        return domain in ["gong", "hubspot", "salesforce"] and rule["effect"] == "EFFECT_ALLOW"
                    elif "['artemis', 'github', 'linear']" in condition:
                        return domain in ["artemis", "github", "linear"] and rule["effect"] == "EFFECT_ALLOW"

        return False  # Default deny

    def calculate_rbac_readiness(self, rbac_status):
        """Calculate RBAC readiness score"""
        score = 0
        if rbac_status.get("./config/security/rbac_rules.json") == "exists":
            score += 3
        if rbac_status.get("./core/security/dynamic_rbac_optimizer.py") == "exists":
            score += 3
        if rbac_status.get("./mcp/security/rbac.py") == "exists":
            score += 2

        # Bonus for rule count
        rule_count = rbac_status.get("./config/security/rbac_rules.json_rules", 0)
        if rule_count > 0:
            score += min(rule_count / 5, 2)  # Up to 2 bonus points

        return min(score, 10)

    def audit_dependencies(self):
        """Audit current dependencies and check for Agno requirements"""

        # Check for pyproject.toml or requirements.txt
        dep_files = ["pyproject.toml", "requirements.txt", "uv.lock"]
        found_files = [f for f in dep_files if os.path.exists(f)]

        # Required dependencies for Agno integration
        required_deps = {
            "agno": ">=0.1.0",
            "langgraph": ">=0.3.5", 
            "litellm": ">=1.55.0",
            "qdrant-client": ">=1.12.0",
            "redis": ">=5.2.0",
            "zep-python": ">=2.1.0",
            "portkey-ai": ">=1.0.0",
            "mem0ai": ">=0.1.0"
        }

        # Check current dependencies
        current_deps = {}
        if os.path.exists("pyproject.toml"):
            try:
                import tomli
                with open("pyproject.toml", "rb") as f:
                    data = tomli.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    for dep in deps:
                        if "==" in dep:
                            name, version = dep.split("==")
                            current_deps[name] = version
                        elif ">=" in dep:
                            name, version = dep.split(">=")
                            current_deps[name] = f">={version}"
            except Exception as e:
                print(f"  ⚠️ Error reading pyproject.toml: {e}")

        # Check missing dependencies
        missing_deps = []
        for dep, version in required_deps.items():
            if dep not in current_deps:
                missing_deps.append(f"{dep}{version}")

        self.audit_results["dependencies"] = {
            "found_files": found_files,
            "current_deps": current_deps,
            "required_deps": required_deps,
            "missing_deps": missing_deps,
            "readiness_score": (len(required_deps) - len(missing_deps)) / len(required_deps) * 10
        }

        print(f"  📋 Dependency files found: {', '.join(found_files)}")
        print(f"  ❌ Missing dependencies: {len(missing_deps)}")
        print(f"  📊 Dependency readiness: {self.audit_results['dependencies']['readiness_score']:.1f}/10")

    def audit_git_trends(self):
        """Analyze git trends for last 100 commits"""

        try:
            # Get git log data
            result = subprocess.run([
                "git", "log", "--oneline", "-100", 
                "--pretty=format:%h|%ad|%an|%s", "--date=short"
            ], capture_output=True, text=True, cwd=".")

            if result.returncode != 0:
                print(f"  ❌ Git log failed: {result.stderr}")
                return

            # Parse commits
            commits = []
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'date': parts[1],
                            'author': parts[2],
                            'message': '|'.join(parts[3:])
                        })

            if not commits:
                print("  ⚠️ No commits found")
                return

            # Create DataFrame for analysis
            df = pd.DataFrame(commits)
            df['date'] = pd.to_datetime(df['date'])

            # Analyze patterns
            author_counts = df['author'].value_counts()

            # Categorize commits
            categories = {
                'Agno/AI': ['agno', 'ai', 'agent', 'swarm', 'langgraph'],
                'Infrastructure': ['infrastructure', 'deploy', 'config', 'pulumi'],
                'Security': ['security', 'rbac', 'auth', 'cerbos'],
                'Memory/Storage': ['memory', 'storage', 'qdrant', 'redis', 'neo4j'],
                'Features': ['feature', 'add', 'implement', 'new'],
                'Fixes': ['fix', 'bug', 'error', 'resolve'],
                'Refactor': ['refactor', 'cleanup', 'optimize']
            }

            commit_categories = {cat: 0 for cat in categories}

            for _, commit in df.iterrows():
                message = commit['message'].lower()
                categorized = False
                for category, keywords in categories.items():
                    if any(keyword in message for keyword in keywords):
                        commit_categories[category] += 1
                        categorized = True
                        break
                if not categorized:
                    commit_categories['Other'] = commit_categories.get('Other', 0) + 1

            # Calculate trends
            daily_commits = df.groupby(df['date'].dt.date).size()
            avg_commits_per_day = daily_commits.mean()

            # Migration readiness indicators
            migration_keywords = ['agno', 'langgraph', 'agent', 'swarm', 'memory', 'qdrant']
            migration_commits = sum(1 for _, commit in df.iterrows() 
                                  if any(keyword in commit['message'].lower() for keyword in migration_keywords))
            migration_readiness = (migration_commits / len(df)) * 10

            self.audit_results["git_trends"] = {
                "total_commits": len(df),
                "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
                "top_authors": dict(author_counts.head(5)),
                "commit_categories": commit_categories,
                "avg_commits_per_day": avg_commits_per_day,
                "migration_commits": migration_commits,
                "migration_readiness": migration_readiness
            }

            print(f"  📊 Analyzed {len(df)} commits")
            print(f"  👥 Top author: {author_counts.index[0]} ({author_counts.iloc[0]} commits)")
            print(f"  🤖 Migration-related commits: {migration_commits} ({migration_commits/len(df)*100:.1f}%)")
            print(f"  📈 Migration readiness: {migration_readiness:.1f}/10")

        except Exception as e:
            print(f"  ❌ Git analysis failed: {e}")
            self.audit_results["git_trends"] = {"error": str(e)}

    def audit_architecture(self):
        """Audit current architecture for V7 migration"""

        # Check key directories
        key_dirs = [
            "core/", "mcp/", "orchestration/", "libs/", 
            "agents/", "memory/", "services/", "config/"
        ]

        dir_status = {}
        for dir_path in key_dirs:
            if os.path.exists(dir_path):
                file_count = len(list(Path(dir_path).rglob("*.py")))
                dir_status[dir_path] = {"exists": True, "python_files": file_count}
            else:
                dir_status[dir_path] = {"exists": False, "python_files": 0}

        # Check for existing agent/swarm implementations
        agent_files = list(Path(".").rglob("*agent*.py"))
        swarm_files = list(Path(".").rglob("*swarm*.py"))
        langgraph_files = list(Path(".").rglob("*langgraph*.py"))

        # Architecture readiness score
        existing_dirs = sum(1 for status in dir_status.values() if status["exists"])
        total_python_files = sum(status["python_files"] for status in dir_status.values())

        arch_readiness = (existing_dirs / len(key_dirs)) * 5 + min(total_python_files / 50, 5)

        self.audit_results["architecture"] = {
            "directory_status": dir_status,
            "agent_files": len(agent_files),
            "swarm_files": len(swarm_files),
            "langgraph_files": len(langgraph_files),
            "total_python_files": total_python_files,
            "readiness_score": arch_readiness
        }

        print(f"  📁 Key directories found: {existing_dirs}/{len(key_dirs)}")
        print(f"  🐍 Total Python files: {total_python_files}")
        print(f"  🤖 Agent-related files: {len(agent_files)}")
        print(f"  📊 Architecture readiness: {arch_readiness:.1f}/10")

    def audit_agno_readiness(self):
        """Assess readiness for Agno integration"""

        # Check for existing async patterns
        async_files = []
        for py_file in Path(".").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'async def' in content or 'await ' in content:
                        async_files.append(str(py_file))
            except:
                continue

        # Check for existing agent patterns
        agent_patterns = {
            "class Agent": 0,
            "class Team": 0,
            "async def": len(async_files),
            "from langgraph": 0,
            "from agno": 0
        }

        for py_file in Path(".").rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in agent_patterns:
                        if pattern in content:
                            agent_patterns[pattern] += content.count(pattern)
            except:
                continue

        # Calculate Agno readiness
        async_score = min(len(async_files) / 10, 3)  # Up to 3 points for async
        agent_score = min(agent_patterns["class Agent"] / 5, 2)  # Up to 2 points for agents
        team_score = min(agent_patterns["class Team"] / 3, 2)  # Up to 2 points for teams
        langgraph_score = min(agent_patterns["from langgraph"] / 2, 2)  # Up to 2 points for langgraph
        agno_score = 1 if agent_patterns["from agno"] > 0 else 0  # 1 point if agno already used

        total_agno_readiness = async_score + agent_score + team_score + langgraph_score + agno_score

        self.audit_results["agno_readiness"] = {
            "async_files": len(async_files),
            "agent_patterns": agent_patterns,
            "scores": {
                "async": async_score,
                "agents": agent_score,
                "teams": team_score,
                "langgraph": langgraph_score,
                "agno": agno_score
            },
            "total_readiness": total_agno_readiness
        }

        print(f"  ⚡ Async files found: {len(async_files)}")
        print(f"  🤖 Agent classes: {agent_patterns['class Agent']}")
        print(f"  👥 Team classes: {agent_patterns['class Team']}")
        print(f"  📊 Agno readiness: {total_agno_readiness:.1f}/10")

    def generate_audit_report(self):
        """Generate comprehensive audit report"""

        # Calculate overall readiness
        scores = [
            self.audit_results.get("rbac", {}).get("readiness_score", 0),
            self.audit_results.get("dependencies", {}).get("readiness_score", 0),
            self.audit_results.get("git_trends", {}).get("migration_readiness", 0),
            self.audit_results.get("architecture", {}).get("readiness_score", 0),
            self.audit_results.get("agno_readiness", {}).get("total_readiness", 0)
        ]

        overall_readiness = sum(scores) / len(scores)

        # Generate report
        report = {
            "audit_timestamp": self.timestamp,
            "overall_readiness": overall_readiness,
            "component_scores": {
                "rbac": scores[0],
                "dependencies": scores[1], 
                "git_trends": scores[2],
                "architecture": scores[3],
                "agno_readiness": scores[4]
            },
            "detailed_results": self.audit_results,
            "recommendations": self.generate_recommendations()
        }

        # Save report
        with open("sophia_v7_audit_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n🎯 AUDIT SUMMARY")
        print("=" * 40)
        print(f"Overall V7 Migration Readiness: {overall_readiness:.1f}/10")
        print(f"RBAC Readiness: {scores[0]:.1f}/10")
        print(f"Dependencies: {scores[1]:.1f}/10") 
        print(f"Git Trends: {scores[2]:.1f}/10")
        print(f"Architecture: {scores[3]:.1f}/10")
        print(f"Agno Readiness: {scores[4]:.1f}/10")

        if overall_readiness >= 8:
            print("✅ READY for V7 migration with Agno integration")
        elif overall_readiness >= 6:
            print("⚠️ MOSTLY READY - minor preparations needed")
        else:
            print("❌ NOT READY - significant preparation required")

        print(f"\n📄 Detailed report saved: sophia_v7_audit_report.json")

        return report

    def generate_recommendations(self):
        """Generate specific recommendations based on audit"""

        recommendations = []

        # RBAC recommendations
        rbac_score = self.audit_results.get("rbac", {}).get("readiness_score", 0)
        if rbac_score < 7:
            recommendations.append({
                "category": "RBAC",
                "priority": "HIGH",
                "action": "Implement comprehensive Cerbos policies for domain isolation",
                "details": "Create policies for each Sophia domain with proper role-based access"
            })

        # Dependency recommendations
        missing_deps = self.audit_results.get("dependencies", {}).get("missing_deps", [])
        if missing_deps:
            recommendations.append({
                "category": "Dependencies",
                "priority": "HIGH", 
                "action": f"Install missing dependencies: {', '.join(missing_deps)}",
                "details": "Use uv add to install Agno and related packages"
            })

        # Architecture recommendations
        arch_score = self.audit_results.get("architecture", {}).get("readiness_score", 0)
        if arch_score < 6:
            recommendations.append({
                "category": "Architecture",
                "priority": "MEDIUM",
                "action": "Restructure codebase for domain-sectioned architecture",
                "details": "Create /sections/ and /core/sophia/ directory structure"
            })

        # Agno recommendations
        agno_score = self.audit_results.get("agno_readiness", {}).get("total_readiness", 0)
        if agno_score < 5:
            recommendations.append({
                "category": "Agno Integration",
                "priority": "HIGH",
                "action": "Implement async patterns and Agent/Team classes",
                "details": "Convert synchronous code to async and create Agno-compatible agents"
            })

        return recommendations

def main():
    """Run the comprehensive audit"""
    auditor = SophiaV7Auditor()
    auditor.run_comprehensive_audit()

if __name__ == "__main__":
    main()
