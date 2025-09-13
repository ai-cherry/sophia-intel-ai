#!/usr/bin/env python3
"""
🔒 Sophia AI Security Validation Script
Validates security posture and dependency versions
"""
import json
import subprocess
import sys
from datetime import datetime
from typing import Any
def check_python_version() -> dict[str, Any]:
    """Check Python version for security"""
    version = sys.version_info
    is_secure = version >= (3, 11, 0)  # Python 3.11+ recommended
    return {
        "check": "python_version",
        "status": "pass" if is_secure else "warn",
        "version": f"{version.major}.{version.minor}.{version.micro}",
        "message": (
            "Python version is secure"
            if is_secure
            else "Consider upgrading to Python 3.11+"
        ),
    }
def check_dependencies() -> dict[str, Any]:
    """Check for known vulnerable dependencies"""
    try:
        # Get installed packages
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
        )
        packages = json.loads(result.stdout)
        # Known secure versions (minimum)
        secure_versions = {
            "fastapi": "0.115.0",
            "uvicorn": "0.32.0",
            "requests": "2.32.0",
            "pydantic": "2.11.0",
            "sqlalchemy": "2.0.36",
            "redis": "5.2.0",
        }
        issues = []
        for pkg in packages:
            name = pkg["name"].lower()
            version = pkg["version"]
            if name in secure_versions:
                min_version = secure_versions[name]
                if version < min_version:
                    issues.append(f"{name} {version} < {min_version} (vulnerable)")
        return {
            "check": "dependencies",
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "message": (
                "All dependencies secure"
                if not issues
                else f"{len(issues)} vulnerable dependencies found"
            ),
        }
    except Exception as e:
        return {
            "check": "dependencies",
            "status": "error",
            "message": f"Failed to check dependencies: {str(e)}",
        }
def check_file_permissions() -> dict[str, Any]:
    """Check critical file permissions"""
    import os
    import stat
    critical_files = ["start.sh", "stop.sh", "test.sh", "docker-fix.sh"]
    issues = []
    for file in critical_files:
        if os.path.exists(file):
            file_stat = os.stat(file)
            stat.filemode(file_stat.st_mode)
            # Check if executable by owner
            if not (file_stat.st_mode & stat.S_IXUSR):
                issues.append(f"{file} not executable")
            # Check if world-writable (security risk)
            if file_stat.st_mode & stat.S_IWOTH:
                issues.append(f"{file} world-writable (security risk)")
    return {
        "check": "file_permissions",
        "status": "pass" if not issues else "warn",
        "issues": issues,
        "message": (
            "File permissions secure"
            if not issues
            else f"{len(issues)} permission issues found"
        ),
    }
def check_environment_variables() -> dict[str, Any]:
    """Check for sensitive environment variables"""
    import os
    sensitive_vars = [
        "API_KEY",
        "SECRET_KEY",
        "PASSWORD",
        "TOKEN",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    exposed_vars = []
    for var in os.environ:
        if any(sensitive in var.upper() for sensitive in sensitive_vars):
            exposed_vars.append(var)
    return {
        "check": "environment_variables",
        "status": "warn" if exposed_vars else "pass",
        "exposed_vars": len(exposed_vars),
        "message": (
            "No sensitive vars exposed"
            if not exposed_vars
            else f"{len(exposed_vars)} sensitive environment variables detected"
        ),
    }
def run_security_validation() -> dict[str, Any]:
    """Run comprehensive security validation"""
    print("🔒 Running Sophia AI Security Validation...")
    checks = [
        check_python_version(),
        check_dependencies(),
        check_file_permissions(),
        check_environment_variables(),
    ]
    # Calculate overall status
    statuses = [check["status"] for check in checks]
    if "fail" in statuses:
        overall_status = "fail"
    elif "warn" in statuses:
        overall_status = "warn"
    else:
        overall_status = "pass"
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall_status,
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": len([c for c in checks if c["status"] == "pass"]),
            "warnings": len([c for c in checks if c["status"] == "warn"]),
            "failed": len([c for c in checks if c["status"] == "fail"]),
        },
    }
    return report
def main():
    """Main security validation"""
    report = run_security_validation()
    # Print summary
    print("\n📊 Security Validation Summary:")
    print(f"Overall Status: {report['overall_status'].upper()}")
    print(
        f"Checks: {report['summary']['passed']}/{report['summary']['total_checks']} passed"
    )
    if report["summary"]["warnings"] > 0:
        print(f"⚠️  {report['summary']['warnings']} warnings")
    if report["summary"]["failed"] > 0:
        print(f"❌ {report['summary']['failed']} failures")
    # Print detailed results
    print("\n📋 Detailed Results:")
    for check in report["checks"]:
        status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "error": "🔥"}
        print(
            f"{status_icon.get(check['status'], '?')} {check['check']}: {check['message']}"
        )
        if "issues" in check and check["issues"]:
            for issue in check["issues"]:
                print(f"   - {issue}")
    # Save report
    with open("security_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n📄 Full report saved to: security_validation_report.json")
    # Exit with appropriate code
    if report["overall_status"] == "fail":
        sys.exit(1)
    elif report["overall_status"] == "warn":
        sys.exit(2)
    else:
        sys.exit(0)
if __name__ == "__main__":
    main()
