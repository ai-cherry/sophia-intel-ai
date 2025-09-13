#!/usr/bin/env python3
"""
IDENTIFY REAL ISSUES AND ROOT CAUSES
Cut through the bullshit and find the actual problems
"""
import json
import os
from collections import defaultdict
class RealIssueIdentifier:
    def __init__(self):
        self.repo_path = "/home/ubuntu/sophia-main"
        self.real_issues = []
        self.root_causes = []
        self.quick_fixes = []
        self.major_fixes = []
    def analyze_secret_exposure_root_cause(self):
        """Find WHY secrets are exposed everywhere"""
        print("🔍 ANALYZING SECRET EXPOSURE ROOT CAUSE...")
        # Load the brutal audit results
        try:
            with open(f"{self.repo_path}/BRUTAL_AUDIT_REPORT.json") as f:
                audit_data = json.load(f)
        except:
            print("❌ Cannot load audit report")
            return
        # Count secret exposures by file type
        secret_issues = [
            issue
            for issue in audit_data["all_issues"]
            if issue["category"] == "EXPOSED_SECRETS"
        ]
        file_types = defaultdict(int)
        for issue in secret_issues:
            if issue.get("file"):
                ext = os.path.splitext(issue["file"])[1]
                file_types[ext] += 1
        print(f"Secret exposures by file type: {dict(file_types)}")
        # ROOT CAUSE ANALYSIS
        if len(secret_issues) > 20:
            self.root_causes.append(
                {
                    "issue": "MASSIVE SECRET EXPOSURE",
                    "root_cause": "No centralized secret management - secrets hardcoded everywhere",
                    "evidence": f"{len(secret_issues)} files with exposed secrets",
                    "fix_type": "MAJOR",
                    "fix_description": "Implement proper Pulumi ESC integration and remove all hardcoded secrets",
                }
            )
        # Check for specific patterns
        md_files_with_secrets = [
            issue
            for issue in secret_issues
            if issue.get("file") and str(issue.get("file", "")).endswith(".md")
        ]
        if len(md_files_with_secrets) > 5:
            self.root_causes.append(
                {
                    "issue": "DOCUMENTATION WITH SECRETS",
                    "root_cause": "Documentation files contain real API keys instead of placeholders",
                    "evidence": f"{len(md_files_with_secrets)} markdown files with secrets",
                    "fix_type": "QUICK",
                    "fix_description": "Replace all real secrets in docs with placeholders",
                }
            )
    def analyze_duplicate_systems(self):
        """Find WHY there are so many duplicate systems"""
        print("🔍 ANALYZING DUPLICATE SYSTEMS...")
        # Find all secret management files
        secret_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if any(
                    keyword in file.lower()
                    for keyword in ["secret", "env", "auth", "key"]
                ):
                    if file.endswith(".py"):
                        secret_files.append(os.path.join(root, file))
        print(f"Found {len(secret_files)} secret-related files")
        if len(secret_files) > 5:
            self.root_causes.append(
                {
                    "issue": "MULTIPLE SECRET MANAGEMENT SYSTEMS",
                    "root_cause": "No single source of truth - multiple implementations created over time",
                    "evidence": f"{len(secret_files)} different secret management files",
                    "fix_type": "MAJOR",
                    "fix_description": "Consolidate to single Pulumi ESC-based system, delete duplicates",
                }
            )
        # Find deployment script chaos
        deploy_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if any(
                    keyword in file.lower()
                    for keyword in ["deploy", "setup", "install"]
                ):
                    if file.endswith((".sh", ".py")):
                        deploy_files.append(os.path.join(root, file))
        print(f"Found {len(deploy_files)} deployment-related files")
        if len(deploy_files) > 8:
            self.root_causes.append(
                {
                    "issue": "DEPLOYMENT SCRIPT CHAOS",
                    "root_cause": "Multiple deployment approaches without consolidation",
                    "evidence": f"{len(deploy_files)} deployment scripts",
                    "fix_type": "MAJOR",
                    "fix_description": "Create single deployment entry point, archive old scripts",
                }
            )
    def analyze_configuration_conflicts(self):
        """Find WHY configurations conflict"""
        print("🔍 ANALYZING CONFIGURATION CONFLICTS...")
        # Find all Docker files
        docker_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if "docker" in file.lower() and file.endswith((".yml", ".yaml")):
                    docker_files.append(os.path.join(root, file))
        if len(docker_files) > 3:
            self.root_causes.append(
                {
                    "issue": "MULTIPLE DOCKER CONFIGURATIONS",
                    "root_cause": "Different Docker setups for different features without consolidation",
                    "evidence": f"{len(docker_files)} Docker compose files",
                    "fix_type": "MAJOR",
                    "fix_description": "Consolidate to single docker-compose.yml with environment overrides",
                }
            )
        # Find environment file chaos
        env_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if ".env" in file or file.startswith("env"):
                    env_files.append(os.path.join(root, file))
        if len(env_files) > 4:
            self.root_causes.append(
                {
                    "issue": "ENVIRONMENT FILE CHAOS",
                    "root_cause": "Multiple environment configurations without clear hierarchy",
                    "evidence": f"{len(env_files)} environment files",
                    "fix_type": "MAJOR",
                    "fix_description": "Standardize on Pulumi ESC with single .env template",
                }
            )
    def identify_quick_wins(self):
        """Find issues that can be fixed quickly"""
        print("🔍 IDENTIFYING QUICK WINS...")
        # Missing ai_router.py - this is a quick fix
        ai_router_path = os.path.join(self.repo_path, "ai_router.py")
        if not os.path.exists(ai_router_path):
            self.quick_fixes.append(
                {
                    "issue": "Missing ai_router.py",
                    "fix": "Copy ai_router.py from another location or recreate it",
                    "effort": "5 minutes",
                    "impact": "HIGH - needed for AI routing functionality",
                }
            )
        # Check for non-executable scripts
        key_scripts = ["sophia.sh", "deploy_multi_instance.sh"]
        for script in key_scripts:
            script_path = os.path.join(self.repo_path, script)
            if os.path.exists(script_path) and not os.access(script_path, os.X_OK):
                self.quick_fixes.append(
                    {
                        "issue": f"{script} not executable",
                        "fix": f"chmod +x {script}",
                        "effort": "1 minute",
                        "impact": "MEDIUM - script won't run without execute permissions",
                    }
                )
        # Check for .gitignore issues
        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                gitignore_content = f.read()
            if "*secrets*" not in gitignore_content:
                self.quick_fixes.append(
                    {
                        "issue": ".gitignore missing secret file patterns",
                        "fix": "Add *secrets*, *.env, *_with_secrets* to .gitignore",
                        "effort": "2 minutes",
                        "impact": "CRITICAL - prevents secret exposure",
                    }
                )
    def identify_major_architectural_issues(self):
        """Find the big architectural problems"""
        print("🔍 IDENTIFYING MAJOR ARCHITECTURAL ISSUES...")
        # The biggest issue: No single source of truth for secrets
        self.major_fixes.append(
            {
                "issue": "NO CENTRALIZED SECRET MANAGEMENT",
                "description": "Secrets are scattered across multiple files and systems",
                "root_cause": "Incremental development without architectural planning",
                "fix_approach": "Implement Pulumi ESC as single source of truth",
                "effort": "2-3 days",
                "impact": "CRITICAL - security and maintainability",
                "steps": [
                    "1. Set up Pulumi ESC properly with GitHub org secrets",
                    "2. Create single secret loading script",
                    "3. Remove all hardcoded secrets from all files",
                    "4. Update all applications to use environment variables",
                    "5. Test deployment with new system",
                ],
            }
        )
        # Second biggest: Too many deployment paths
        self.major_fixes.append(
            {
                "issue": "MULTIPLE DEPLOYMENT SYSTEMS",
                "description": "Multiple ways to deploy with no clear primary path",
                "root_cause": "Feature creep without consolidation",
                "fix_approach": "Create single deployment entry point",
                "effort": "1-2 days",
                "impact": "HIGH - operational complexity",
                "steps": [
                    "1. Choose primary deployment method (recommend docker-compose)",
                    "2. Create single deploy.sh script",
                    "3. Archive or delete old deployment scripts",
                    "4. Update documentation to reference single method",
                    "5. Test deployment path end-to-end",
                ],
            }
        )
        # Third: Documentation chaos
        self.major_fixes.append(
            {
                "issue": "DOCUMENTATION CHAOS",
                "description": "Multiple README files with conflicting information",
                "root_cause": "Documentation created for each feature without consolidation",
                "fix_approach": "Create single source of truth documentation",
                "effort": "1 day",
                "impact": "MEDIUM - user confusion",
                "steps": [
                    "1. Audit all documentation files",
                    "2. Create master README.md",
                    "3. Move detailed docs to docs/ folder",
                    "4. Remove or archive outdated docs",
                    "5. Ensure all docs reference current implementation",
                ],
            }
        )
    def calculate_real_health_score(self):
        """Calculate a realistic health score based on actual issues"""
        print("🔍 CALCULATING REAL HEALTH SCORE...")
        # Load test results
        try:
            with open(f"{self.repo_path}/WHAT_WORKS_REPORT.json") as f:
                test_data = json.load(f)
            working_percentage = test_data["working_percentage"]
        except:
            working_percentage = 50  # Default if can't load
        # Deduct points for major issues
        health_score = working_percentage
        # Major architectural issues hurt a lot
        health_score -= len(self.major_fixes) * 15
        # Root causes hurt moderately
        health_score -= len(self.root_causes) * 10
        # But if basic functionality works, that's worth something
        if working_percentage > 90:
            health_score += 10  # Bonus for working functionality
        # Floor at 0
        health_score = max(0, health_score)
        return health_score
    def generate_real_issues_report(self):
        """Generate the real issues report"""
        print("\\n" + "=" * 70)
        print("🔍 REAL ISSUES AND ROOT CAUSES REPORT")
        print("=" * 70)
        real_health = self.calculate_real_health_score()
        print(f"\\n🎯 REAL HEALTH SCORE: {real_health:.1f}%")
        if real_health >= 70:
            status = "DEPLOYABLE WITH FIXES"
        elif real_health >= 50:
            status = "NEEDS MAJOR WORK"
        elif real_health >= 30:
            status = "SIGNIFICANT PROBLEMS"
        else:
            status = "MAJOR OVERHAUL NEEDED"
        print(f"🎯 REAL STATUS: {status}")
        print(f"\\n🔥 ROOT CAUSES ({len(self.root_causes)}):")
        for i, cause in enumerate(self.root_causes, 1):
            print(f"   {i}. {cause['issue']}")
            print(f"      Root Cause: {cause['root_cause']}")
            print(f"      Evidence: {cause['evidence']}")
            print(f"      Fix Type: {cause['fix_type']}")
            print()
        print(f"\\n⚡ QUICK FIXES ({len(self.quick_fixes)}):")
        for i, fix in enumerate(self.quick_fixes, 1):
            print(f"   {i}. {fix['issue']}")
            print(f"      Fix: {fix['fix']}")
            print(f"      Effort: {fix['effort']}")
            print(f"      Impact: {fix['impact']}")
            print()
        print(f"\\n🏗️ MAJOR FIXES ({len(self.major_fixes)}):")
        for i, fix in enumerate(self.major_fixes, 1):
            print(f"   {i}. {fix['issue']}")
            print(f"      Description: {fix['description']}")
            print(f"      Root Cause: {fix['root_cause']}")
            print(f"      Effort: {fix['effort']}")
            print(f"      Impact: {fix['impact']}")
            print()
        # Save report
        report = {
            "timestamp": "2025-08-09",
            "real_health_score": real_health,
            "status": status,
            "root_causes": self.root_causes,
            "quick_fixes": self.quick_fixes,
            "major_fixes": self.major_fixes,
        }
        with open(f"{self.repo_path}/REAL_ISSUES_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        print("💾 Report saved to: REAL_ISSUES_REPORT.json")
        return real_health, status
    def run_analysis(self):
        """Run the complete real issues analysis"""
        print("🔍 IDENTIFYING REAL ISSUES AND ROOT CAUSES...")
        print("Cutting through the bullshit to find actual problems")
        print("-" * 60)
        self.analyze_secret_exposure_root_cause()
        self.analyze_duplicate_systems()
        self.analyze_configuration_conflicts()
        self.identify_quick_wins()
        self.identify_major_architectural_issues()
        real_health, status = self.generate_real_issues_report()
        print("\\n🎯 BOTTOM LINE:")
        print(f"   Real Health: {real_health:.1f}%")
        print(f"   Status: {status}")
        print(f"   Quick Fixes: {len(self.quick_fixes)}")
        print(f"   Major Fixes: {len(self.major_fixes)}")
        if real_health >= 60:
            print("   💡 VERDICT: Fixable with focused effort")
        else:
            print("   💡 VERDICT: Needs significant architectural work")
        return real_health, status
if __name__ == "__main__":
    analyzer = RealIssueIdentifier()
    real_health, status = analyzer.run_analysis()
    if real_health < 40:
        exit(1)
    else:
        exit(0)
