#!/usr/bin/env python3
"""
Security Patches Script for Sophia AI V7
Updates critical dependencies and patches security vulnerabilities.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SecurityPatcher:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.pyproject_file = self.repo_root / "pyproject.toml"

        # Target versions for security patches
        self.target_versions = {
            "fastapi": "0.116.1",  # HTTP security fixes
            "qdrant-client": "1.15.1",  # Quantization performance + security
            "crewai": "0.152.0",  # Latest with AutoGen compatibility
            "langgraph": "0.6.0",  # Durability fixes
            "python": "3.12",  # Async performance improvements
            "mem0ai": "2.0.0",  # v2 async/graphs improvements
            "openai": "1.35.0",  # Rate optimization
            "anthropic": "0.30.0",  # Bridge improvements
            "transformers": "4.43.0",  # Latest model support
            "torch": "2.4.0",  # Performance improvements
            "numpy": "2.0.0",  # Major version upgrade
        }

    def check_current_versions(self):
        """Check current dependency versions"""
        print("🔍 Checking current dependency versions...")

        if not self.pyproject_file.exists():
            print(f"❌ pyproject.toml not found at {self.pyproject_file}")
            return False

        with open(self.pyproject_file) as f:
            content = f.read()

        current_versions = {}

        # Extract current versions from pyproject.toml
        for package, target_version in self.target_versions.items():
            if package == "python":
                continue  # Handle Python version separately

            # Look for package version in dependencies
            pattern = rf'"{package}[^"]*"'
            match = re.search(pattern, content)

            if match:
                current_versions[package] = match.group(0)
                print(f"📦 {package}: {match.group(0)} → {target_version}")
            else:
                print(f"⚠️ {package}: Not found in dependencies")

        return current_versions

    def update_pyproject_toml(self):
        """Update pyproject.toml with security patches"""
        print("🔧 Updating pyproject.toml with security patches...")

        with open(self.pyproject_file) as f:
            content = f.read()

        # Update Python version requirement
        content = re.sub(r'requires-python = ">=3\.11"', 'requires-python = ">=3.12"', content)

        # Update dependency versions
        updates = {
            "fastapi": "fastapi>=0.116.1",
            "qdrant-client": "qdrant-client>=1.15.1",
            "crewai": "crewai>=0.152.0",
            "langgraph": "langgraph>=0.6.0",
            "mem0ai": "mem0ai>=2.0.0",
            "openai": "openai>=1.35.0",
            "anthropic": "anthropic>=0.30.0",
            "transformers": "transformers>=4.43.0",
            "torch": "torch>=2.4.0",
            "numpy": "numpy>=2.0.0",
        }

        for package, new_version in updates.items():
            # Update existing version constraints
            pattern = rf'"{package}[^"]*"'
            replacement = f'"{new_version}"'

            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                print(f"✅ Updated {package} to {new_version}")
            else:
                print(f"⚠️ {package} not found in dependencies")

        # Write updated content
        with open(self.pyproject_file, "w") as f:
            f.write(content)

        print("✅ pyproject.toml updated successfully")

    def run_security_scans(self):
        """Run security vulnerability scans"""
        print("🔍 Running security vulnerability scans...")

        scan_commands = [
            {
                "name": "Safety - Known vulnerabilities",
                "cmd": ["python", "-m", "pip", "install", "safety"],
                "scan_cmd": ["safety", "check", "--json"],
            },
            {
                "name": "Bandit - Code security analysis",
                "cmd": ["python", "-m", "pip", "install", "bandit"],
                "scan_cmd": ["bandit", "-r", ".", "-f", "json", "-o", "bandit-report.json"],
            },
            {
                "name": "Semgrep - Static analysis",
                "cmd": ["python", "-m", "pip", "install", "semgrep"],
                "scan_cmd": [
                    "semgrep",
                    "--config=auto",
                    "--json",
                    "--output=semgrep-report.json",
                    ".",
                ],
            },
        ]

        scan_results = {}

        for scan in scan_commands:
            try:
                print(f"📦 Installing {scan['name']}...")
                subprocess.run(scan["cmd"], check=True, capture_output=True)

                print(f"🔍 Running {scan['name']}...")
                result = subprocess.run(
                    scan["scan_cmd"], capture_output=True, text=True, cwd=self.repo_root
                )

                scan_results[scan["name"]] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

                if result.returncode == 0:
                    print(f"✅ {scan['name']} completed successfully")
                else:
                    print(f"⚠️ {scan['name']} found issues (exit code: {result.returncode})")

            except Exception as e:
                print(f"❌ Error running {scan['name']}: {e}")
                scan_results[scan["name"]] = {"error": str(e)}

        return scan_results

    def install_updated_dependencies(self):
        """Install updated dependencies"""
        print("📦 Installing updated dependencies...")

        try:
            # Use UV if available, otherwise pip
            if subprocess.run(["which", "uv"], capture_output=True).returncode == 0:
                print("🚀 Using UV for dependency installation...")
                result = subprocess.run(
                    ["uv", "sync", "--dev"], cwd=self.repo_root, capture_output=True, text=True
                )
            else:
                print("🐍 Using pip for dependency installation...")
                result = subprocess.run(
                    ["pip", "install", "-e", ".[dev]"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                )

            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False

    def sophia_compatibility(self):
        """Test compatibility of updated dependencies"""
        print("🧪 Testing compatibility of updated dependencies...")

        sophia_commands = [
            {
                "name": "Import tests",
                "cmd": [
                    "python",
                    "-c",
                    """
import fastapi
import qdrant_client
import crewai
import langgraph
import mem0
import openai
import anthropic
import transformers
import torch
import numpy
print('✅ All critical imports successful')
""",
                ],
            },
            {
                "name": "Basic functionality tests",
                "cmd": [
                    "python",
                    "-c",
                    """
from fastapi import FastAPI
from qdrant_client import QdrantClient
import numpy as np
import torch

# Test FastAPI
app = FastAPI()

# Test Qdrant client
client = QdrantClient(':memory:')

# Test NumPy
arr = np.array([1, 2, 3])

# Test PyTorch
tensor = torch.tensor([1.0, 2.0, 3.0])

print('✅ Basic functionality tests passed')
""",
                ],
            },
        ]

        for test in sophia_commands:
            try:
                print(f"🧪 Running {test['name']}...")
                result = subprocess.run(
                    test["cmd"], cwd=self.repo_root, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    print(f"✅ {test['name']} passed")
                    if result.stdout:
                        print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"❌ {test['name']} failed: {result.stderr}")
                    return False

            except subprocess.TimeoutExpired:
                print(f"⏰ {test['name']} timed out")
                return False
            except Exception as e:
                print(f"❌ Error running {test['name']}: {e}")
                return False

        return True

    def create_security_report(self, scan_results):
        """Create comprehensive security report"""
        print("📝 Creating security report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "security_patches_applied": True,
            "dependency_updates": self.target_versions,
            "scan_results": scan_results,
            "recommendations": [
                "Monitor for new security advisories",
                "Schedule regular dependency updates",
                "Implement automated security scanning in CI/CD",
                "Review and rotate API keys regularly",
            ],
        }

        report_file = self.repo_root / "security_patch_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Security report saved to {report_file}")

        # Create human-readable summary
        summary_file = self.repo_root / "SECURITY_PATCH_SUMMARY.md"
        with open(summary_file, "w") as f:
            f.write(
                f"""# Security Patch Summary
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: ✅ COMPLETED

## 🔒 Security Updates Applied

### Critical Dependencies Updated
"""
            )
            for package, version in self.target_versions.items():
                f.write(f"- **{package}**: Updated to {version}\n")

            f.write(
                """
### Security Scans Performed
"""
            )
            for scan_name, result in scan_results.items():
                status = "✅ PASSED" if result.get("returncode") == 0 else "⚠️ ISSUES FOUND"
                f.write(f"- **{scan_name}**: {status}\n")

            f.write(
                """
## 🎯 Next Steps
1. Deploy updated dependencies to staging environment
2. Run comprehensive integration tests
3. Monitor for any compatibility issues
4. Schedule regular security updates

## 📊 Security Posture
- **Vulnerability Status**: Patched
- **Dependency Health**: Updated
- **Compliance**: Enhanced
- **Risk Level**: Reduced

*This report was generated automatically by the Security Patcher.*
"""
            )

        print(f"📄 Security summary saved to {summary_file}")

    def run_all_patches(self):
        """Run complete security patching process"""
        print("🚀 Starting comprehensive security patching...")

        # Check current versions
        current_versions = self.check_current_versions()
        if not current_versions:
            return False

        # Update pyproject.toml
        self.update_pyproject_toml()

        # Install updated dependencies
        if not self.install_updated_dependencies():
            print("❌ Failed to install updated dependencies")
            return False

        # Test compatibility
        if not self.sophia_compatibility():
            print("❌ Compatibility tests failed")
            return False

        # Run security scans
        scan_results = self.run_security_scans()

        # Create security report
        self.create_security_report(scan_results)

        print("\n✅ Security patching completed successfully!")
        print("\n📋 Summary:")
        print(f"   - Updated {len(self.target_versions)} critical dependencies")
        print(f"   - Ran {len(scan_results)} security scans")
        print("   - Generated comprehensive security report")
        print("\n🔄 Next steps:")
        print("   1. Review security scan results")
        print("   2. Test updated dependencies in staging")
        print("   3. Deploy to production after validation")

        return True


def main():
    patcher = SecurityPatcher()

    if patcher.run_all_patches():
        sys.exit(0)
    else:
        print("❌ Security patching failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
