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
Security Summary Generator
Consolidates all security reports into a comprehensive summary.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
class SecuritySummaryGenerator:
    """Generates comprehensive security summary from all reports."""
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.summary_data = {
            "timestamp": self.timestamp,
            "reports": {},
            "totals": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "recommendations": []
        }
    def load_json_report(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON report if it exists."""
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
    def process_safety_report(self) -> Dict[str, Any]:
        """Process Safety vulnerability report."""
        data = self.load_json_report(Path("safety-reports/safety-report.json"))
        if not data:
            return {"status": "missing", "vulnerabilities": []}
        vulns = data.get("vulnerabilities", [])
        processed_vulns = []
        for vuln in vulns:
            severity = vuln.get("severity", "unknown").lower()
            processed_vuln = {
                "package": vuln.get("package_name", "unknown"),
                "version": vuln.get("installed_version", "unknown"),
                "vulnerability_id": vuln.get("vulnerability_id", "unknown"),
                "severity": severity,
                "description": vuln.get("advisory", "No description available")[:200] + "..."
            }
            processed_vulns.append(processed_vuln)
            # Count by severity
            if severity == "critical":
                self.summary_data["totals"]["critical"] += 1
            elif severity == "high":
                self.summary_data["totals"]["high"] += 1
            elif severity == "medium":
                self.summary_data["totals"]["medium"] += 1
            else:
                self.summary_data["totals"]["low"] += 1
        return {
            "status": "completed",
            "total_vulnerabilities": len(vulns),
            "vulnerabilities": processed_vulns
        }
    def process_bandit_report(self) -> Dict[str, Any]:
        """Process Bandit security linting report."""
        data = self.load_json_report(Path("security-reports/bandit-report.json"))
        if not data:
            return {"status": "missing", "issues": []}
        results = data.get("results", [])
        processed_issues = []
        for result in results:
            severity = result.get("issue_severity", "unknown").lower()
            issue = {
                "sophia_name": result.get("sophia_name", "unknown"),
                "filename": result.get("filename", "unknown"),
                "line_number": result.get("line_number", 0),
                "severity": severity,
                "confidence": result.get("issue_confidence", "unknown"),
                "description": result.get("issue_text", "No description")[:200] + "..."
            }
            processed_issues.append(issue)
            # Count by severity
            if severity == "high":
                self.summary_data["totals"]["high"] += 1
            elif severity == "medium":
                self.summary_data["totals"]["medium"] += 1
            else:
                self.summary_data["totals"]["low"] += 1
        return {
            "status": "completed",
            "total_issues": len(results),
            "issues": processed_issues
        }
    def process_pip_audit_report(self) -> Dict[str, Any]:
        """Process pip-audit dependency report."""
        data = self.load_json_report(Path("dependency-reports/pip-audit-report.json"))
        if not data:
            return {"status": "missing", "vulnerabilities": []}
        vulns = data.get("vulnerabilities", [])
        processed_vulns = []
        for vuln in vulns:
            vulnerability = {
                "package": vuln.get("package", "unknown"),
                "version": vuln.get("installed_version", "unknown"),
                "vulnerability_id": vuln.get("id", "unknown"),
                "description": vuln.get("description", "No description")[:200] + "...",
                "fix_versions": vuln.get("fix_versions", [])
            }
            processed_vulns.append(vulnerability)
            # Most pip-audit findings are medium severity
            self.summary_data["totals"]["medium"] += 1
        return {
            "status": "completed",
            "total_vulnerabilities": len(vulns),
            "vulnerabilities": processed_vulns
        }
    def process_semgrep_report(self) -> Dict[str, Any]:
        """Process Semgrep static analysis report."""
        data = self.load_json_report(Path("security-reports/semgrep-report.json"))
        if not data:
            return {"status": "missing", "findings": []}
        results = data.get("results", [])
        processed_findings = []
        for result in results:
            severity = result.get("extra", {}).get("severity", "INFO")
            finding = {
                "check_id": result.get("check_id", "unknown"),
                "path": result.get("path", "unknown"),
                "line": result.get("start", {}).get("line", 0),
                "severity": severity.lower(),
                "message": result.get("extra", {}).get("message", "No message")[:200] + "..."
            }
            processed_findings.append(finding)
            # Count by severity
            if severity == "ERROR":
                self.summary_data["totals"]["high"] += 1
            elif severity == "WARNING":
                self.summary_data["totals"]["medium"] += 1
            else:
                self.summary_data["totals"]["info"] += 1
        return {
            "status": "completed",
            "total_findings": len(results),
            "findings": processed_findings
        }
    def process_code_quality_reports(self) -> Dict[str, Any]:
        """Process code quality reports (Ruff, MyPy)."""
        ruff_data = self.load_json_report(Path("code-quality-reports/ruff-report.json"))
        quality_summary = {
            "ruff": {"status": "missing", "issues": 0},
            "mypy": {"status": "missing", "errors": 0}
        }
        if ruff_data:
            # Ruff report is typically a list of issues
            issues = ruff_data if isinstance(ruff_data, list) else []
            quality_summary["ruff"] = {
                "status": "completed",
                "issues": len(issues)
            }
            # Most code quality issues are low severity
            self.summary_data["totals"]["low"] += len(issues)
        # Check for MyPy report directory
        mypy_dir = Path("code-quality-reports/mypy-report")
        if mypy_dir.exists():
            quality_summary["mypy"]["status"] = "completed"
        return quality_summary
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        totals = self.summary_data["totals"]
        if totals["critical"] > 0:
            recommendations.append(
                f"🚨 URGENT: Address {totals['critical']} critical vulnerabilities immediately"
            )
        if totals["high"] > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Fix {totals['high']} high-severity security issues"
            )
        if totals["medium"] > 10:
            recommendations.append(
                f"📋 MEDIUM PRIORITY: Review and address {totals['medium']} medium-severity issues"
            )
        # Specific recommendations based on report types
        safety_report = self.summary_data["reports"].get("safety", {})
        if safety_report.get("total_vulnerabilities", 0) > 0:
            recommendations.append(
                "🔄 Update vulnerable packages to latest secure versions"
            )
        bandit_report = self.summary_data["reports"].get("bandit", {})
        if bandit_report.get("total_issues", 0) > 0:
            recommendations.append(
                "🔒 Review and fix security anti-patterns in code"
            )
        if not recommendations:
            recommendations.append("✅ No immediate security actions required")
        return recommendations
    def generate_markdown_summary(self) -> str:
        """Generate markdown summary report."""
        totals = self.summary_data["totals"]
        # Header
        lines = [
            "# 🔒 Security Scan Summary",
            f"*Generated on {datetime.fromisoformat(self.timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            "",
        ]
        # Overall status
        if totals["critical"] > 0:
            lines.append("## 🚨 CRITICAL ISSUES FOUND")
            lines.append("**Build should be blocked until critical issues are resolved.**")
        elif totals["high"] > 5:
            lines.append("## ⚠️ HIGH SEVERITY ISSUES")
            lines.append("**Multiple high-severity issues require attention.**")
        else:
            lines.append("## ✅ Security Status: ACCEPTABLE")
            lines.append("**No critical security issues blocking deployment.**")
        lines.append("")
        # Summary table
        lines.extend([
            "## 📊 Vulnerability Summary",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| 🚨 Critical | {totals['critical']} |",
            f"| ⚠️ High | {totals['high']} |",
            f"| 📋 Medium | {totals['medium']} |",
            f"| 📝 Low | {totals['low']} |",
            f"| ℹ️ Info | {totals['info']} |",
            "",
        ])
        # Report status
        lines.extend([
            "## 🔍 Scan Results",
            "",
        ])
        for tool, report in self.summary_data["reports"].items():
            status = report.get("status", "unknown")
            if status == "completed":
                status_icon = "✅"
            elif status == "missing":
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            lines.append(f"- {status_icon} **{tool.title()}**: {status}")
        lines.append("")
        # Recommendations
        if self.summary_data["recommendations"]:
            lines.extend([
                "## 🎯 Recommendations",
                "",
            ])
            for rec in self.summary_data["recommendations"]:
                lines.append(f"- {rec}")
            lines.append("")
        # Detailed findings (top issues only)
        if totals["critical"] > 0 or totals["high"] > 0:
            lines.extend([
                "## 🔍 Critical/High Severity Findings",
                "",
            ])
            # Show critical Safety vulnerabilities
            safety_report = self.summary_data["reports"].get("safety", {})
            critical_vulns = [
                v for v in safety_report.get("vulnerabilities", [])
                if v.get("severity") == "critical"
            ]
            if critical_vulns:
                lines.append("### 🚨 Critical Vulnerabilities")
                for vuln in critical_vulns[:5]:  # Top 5
                    lines.append(f"- **{vuln['package']}** {vuln['version']}: {vuln['vulnerability_id']}")
                lines.append("")
            # Show high-severity Bandit issues
            bandit_report = self.summary_data["reports"].get("bandit", {})
            high_issues = [
                i for i in bandit_report.get("issues", [])
                if i.get("severity") == "high"
            ]
            if high_issues:
                lines.append("### ⚠️ High-Severity Security Issues")
                for issue in high_issues[:5]:  # Top 5
                    lines.append(f"- **{issue['sophia_name']}** in {issue['filename']}:{issue['line_number']}")
                lines.append("")
        return "\n".join(lines)
    def generate_json_summary(self) -> str:
        """Generate JSON summary report."""
        return json.dumps(self.summary_data, indent=2)
    def run(self) -> int:
        """Run the summary generation."""
        print("🔒 Generating security summary...")
        # Process all reports
        self.summary_data["reports"]["safety"] = self.process_safety_report()
        self.summary_data["reports"]["bandit"] = self.process_bandit_report()
        self.summary_data["reports"]["pip_audit"] = self.process_pip_audit_report()
        self.summary_data["reports"]["semgrep"] = self.process_semgrep_report()
        self.summary_data["reports"]["code_quality"] = self.process_code_quality_reports()
        # Generate recommendations
        self.summary_data["recommendations"] = self.generate_recommendations()
        # Generate reports
        markdown_summary = self.generate_markdown_summary()
        json_summary = self.generate_json_summary()
        # Save reports
        with open("security-summary.md", "w") as f:
            f.write(markdown_summary)
        with open("security-summary.json", "w") as f:
            f.write(json_summary)
        print("✅ Security summary generated:")
        print("  - security-summary.md")
        print("  - security-summary.json")
        # Print summary to console
        print("\n" + "="*60)
        print(markdown_summary)
        return 0
def main():
    """Main entry point."""
    generator = SecuritySummaryGenerator()
    exit_code = generator.run()
    sys.exit(exit_code)
if __name__ == "__main__":
    main()
