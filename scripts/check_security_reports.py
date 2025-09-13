# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:
    pass
#!/usr/bin/env python3
"""
Security Report Checker
Analyzes security scan results and fails CI if critical vulnerabilities are found.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
class SecurityReportChecker:
    """Analyzes security reports and determines if build should fail."""
    def __init__(self):
        self.critical_count = 0
        self.high_count = 0
        self.medium_count = 0
        self.low_count = 0
        self.reports = {}
    def check_safety_report(self, report_path: Path) -> Dict[str, Any]:
        """Check Safety vulnerability report."""
        if not report_path.exists():
            print(f"⚠️  Safety report not found: {report_path}")
            return {"status": "missing", "vulnerabilities": 0}
        try:
            with open(report_path) as f:
                data = json.load(f)
            vulns = data.get("vulnerabilities", [])
            critical_vulns = [v for v in vulns if v.get("severity", "").lower() == "critical"]
            high_vulns = [v for v in vulns if v.get("severity", "").lower() == "high"]
            self.critical_count += len(critical_vulns)
            self.high_count += len(high_vulns)
            print(f"🔍 Safety scan: {len(vulns)} total vulnerabilities")
            if critical_vulns:
                print(f"🚨 CRITICAL: {len(critical_vulns)} critical vulnerabilities found!")
                for vuln in critical_vulns:
                    print(f"   - {vuln.get('package_name', 'unknown')}: {vuln.get('vulnerability_id', 'unknown')}")
            return {
                "status": "completed",
                "total_vulnerabilities": len(vulns),
                "critical": len(critical_vulns),
                "high": len(high_vulns)
            }
        except Exception as e:
            print(f"❌ Error reading Safety report: {e}")
            return {"status": "error", "error": str(e)}
    def check_bandit_report(self, report_path: Path) -> Dict[str, Any]:
        """Check Bandit security linting report."""
        if not report_path.exists():
            print(f"⚠️  Bandit report not found: {report_path}")
            return {"status": "missing", "issues": 0}
        try:
            with open(report_path) as f:
                data = json.load(f)
            results = data.get("results", [])
            high_issues = [r for r in results if r.get("issue_severity", "").lower() == "high"]
            medium_issues = [r for r in results if r.get("issue_severity", "").lower() == "medium"]
            self.high_count += len(high_issues)
            self.medium_count += len(medium_issues)
            print(f"🔍 Bandit scan: {len(results)} security issues")
            if high_issues:
                print(f"🚨 HIGH: {len(high_issues)} high-severity security issues!")
                for issue in high_issues[:5]:  # Show first 5
                    print(f"   - {issue.get('sophia_name', 'unknown')}: {issue.get('filename', 'unknown')}")
            return {
                "status": "completed",
                "total_issues": len(results),
                "high": len(high_issues),
                "medium": len(medium_issues)
            }
        except Exception as e:
            print(f"❌ Error reading Bandit report: {e}")
            return {"status": "error", "error": str(e)}
    def check_pip_audit_report(self, report_path: Path) -> Dict[str, Any]:
        """Check pip-audit dependency report."""
        if not report_path.exists():
            print(f"⚠️  pip-audit report not found: {report_path}")
            return {"status": "missing", "vulnerabilities": 0}
        try:
            with open(report_path) as f:
                data = json.load(f)
            vulns = data.get("vulnerabilities", [])
            print(f"🔍 pip-audit scan: {len(vulns)} dependency vulnerabilities")
            if vulns:
                print(f"⚠️  Found {len(vulns)} vulnerable dependencies")
                for vuln in vulns[:5]:  # Show first 5
                    package = vuln.get("package", "unknown")
                    version = vuln.get("installed_version", "unknown")
                    print(f"   - {package} {version}")
            return {
                "status": "completed",
                "vulnerabilities": len(vulns)
            }
        except Exception as e:
            print(f"❌ Error reading pip-audit report: {e}")
            return {"status": "error", "error": str(e)}
    def check_semgrep_report(self, report_path: Path) -> Dict[str, Any]:
        """Check Semgrep static analysis report."""
        if not report_path.exists():
            print(f"⚠️  Semgrep report not found: {report_path}")
            return {"status": "missing", "findings": 0}
        try:
            with open(report_path) as f:
                data = json.load(f)
            results = data.get("results", [])
            errors = [r for r in results if r.get("extra", {}).get("severity") == "ERROR"]
            warnings = [r for r in results if r.get("extra", {}).get("severity") == "WARNING"]
            self.high_count += len(errors)
            self.medium_count += len(warnings)
            print(f"🔍 Semgrep scan: {len(results)} findings")
            if errors:
                print(f"🚨 ERROR: {len(errors)} error-level findings!")
                for error in errors[:3]:  # Show first 3
                    print(f"   - {error.get('check_id', 'unknown')}: {error.get('path', 'unknown')}")
            return {
                "status": "completed",
                "total_findings": len(results),
                "errors": len(errors),
                "warnings": len(warnings)
            }
        except Exception as e:
            print(f"❌ Error reading Semgrep report: {e}")
            return {"status": "error", "error": str(e)}
    def generate_summary(self) -> str:
        """Generate security summary."""
        summary = []
        summary.append("# 🔒 Security Scan Summary")
        summary.append("")
        if self.critical_count > 0:
            summary.append(f"🚨 **CRITICAL**: {self.critical_count} critical vulnerabilities")
        if self.high_count > 0:
            summary.append(f"⚠️  **HIGH**: {self.high_count} high-severity issues")
        if self.medium_count > 0:
            summary.append(f"ℹ️  **MEDIUM**: {self.medium_count} medium-severity issues")
        if self.low_count > 0:
            summary.append(f"📝 **LOW**: {self.low_count} low-severity issues")
        if self.critical_count == 0 and self.high_count == 0:
            summary.append("✅ **No critical or high-severity vulnerabilities found!**")
        summary.append("")
        summary.append("## Report Details")
        for tool, report in self.reports.items():
            summary.append(f"- **{tool}**: {report.get('status', 'unknown')}")
        return "\n".join(summary)
    def should_fail_build(self) -> bool:
        """Determine if build should fail based on security findings."""
        # Fail on any critical vulnerabilities
        if self.critical_count > 0:
            return True
        # Fail on more than 5 high-severity issues
        if self.high_count > 5:
            return True
        return False
    def run_checks(self) -> int:
        """Run all security checks and return exit code."""
        print("🔒 Running security report analysis...")
        print("=" * 50)
        # Check all security reports
        self.reports["Safety"] = self.check_safety_report(Path("safety-report.json"))
        self.reports["Bandit"] = self.check_bandit_report(Path("bandit-report.json"))
        self.reports["pip-audit"] = self.check_pip_audit_report(Path("pip-audit-report.json"))
        self.reports["Semgrep"] = self.check_semgrep_report(Path("semgrep-report.json"))
        print("\n" + "=" * 50)
        # Generate and save summary
        summary = self.generate_summary()
        print(summary)
        with open("security-summary.md", "w") as f:
            f.write(summary)
        # Determine exit code
        if self.should_fail_build():
            print("\n❌ BUILD FAILED: Critical security issues found!")
            print("Please address the security vulnerabilities before proceeding.")
            return 1
        else:
            print("\n✅ BUILD PASSED: No critical security issues found.")
            return 0
def main():
    """Main entry point."""
    checker = SecurityReportChecker()
    exit_code = checker.run_checks()
    sys.exit(exit_code)
if __name__ == "__main__":
    main()
