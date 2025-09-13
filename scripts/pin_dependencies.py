#!/usr/bin/env python3
"""
Dependency Pinning and Management Script
Ensures all dependencies are properly pinned and secure
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import tomllib
# ANSI color codes for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
class DependencyManager:
    """Manages dependency pinning and security checks"""
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.requirements_lock = self.project_root / "requirements-lock.txt"
        self.requirements_dev_lock = self.project_root / "requirements-dev-lock.txt"
    def load_pyproject(self) -> dict:
        """Load pyproject.toml file"""
        with open(self.pyproject_path, "rb") as f:
            return tomllib.load(f)
    def check_unpinned_dependencies(self) -> List[str]:
        """Find dependencies that aren't pinned to exact versions"""
        unpinned = []
        pyproject = self.load_pyproject()
        # Check main dependencies
        for dep in pyproject.get("project", {}).get("dependencies", []):
            if not self._is_pinned(dep):
                unpinned.append(dep)
        # Check optional dependencies
        for group, deps in (
            pyproject.get("project", {}).get("optional-dependencies", {}).items()
        ):
            for dep in deps:
                if not self._is_pinned(dep):
                    unpinned.append(f"{group}: {dep}")
        return unpinned
    def _is_pinned(self, dependency: str) -> bool:
        """Check if a dependency is pinned to exact version"""
        # Extract package name and version spec
        if "[" in dependency:
            # Handle extras like package[extra]==1.0.0
            package_part = dependency.split("[")[0]
            version_part = dependency.split("]")[-1]
        else:
            parts = re.split(r"[><=!~]", dependency, 1)
            if len(parts) < 2:
                return False
            version_part = dependency[len(parts[0]) :]
        # Check for exact version pinning
        return version_part.startswith("==")
    def generate_lock_files(self) -> Tuple[bool, str]:
        """Generate lock files using pip-compile"""
        try:
            # Check if pip-tools is installed
            result = subprocess.run(
                ["pip-compile", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, "pip-tools not installed. Run: pip install pip-tools"
            # Generate main requirements lock
            print(f"{BLUE}Generating requirements-lock.txt...{RESET}")
            result = subprocess.run(
                [
                    "pip-compile",
                    "--generate-hashes",
                    "--resolver=backtracking",
                    "-o",
                    str(self.requirements_lock),
                    str(self.pyproject_path),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False, f"Failed to generate lock file: {result.stderr}"
            # Generate dev requirements lock
            print(f"{BLUE}Generating requirements-dev-lock.txt...{RESET}")
            result = subprocess.run(
                [
                    "pip-compile",
                    "--extra=dev",
                    "--extra=test",
                    "--generate-hashes",
                    "--resolver=backtracking",
                    "-o",
                    str(self.requirements_dev_lock),
                    str(self.pyproject_path),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False, f"Failed to generate dev lock file: {result.stderr}"
            return True, "Lock files generated successfully"
        except Exception as e:
            return False, str(e)
    def check_security_vulnerabilities(self) -> List[Dict]:
        """Check for security vulnerabilities using safety"""
        vulnerabilities = []
        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json"], capture_output=True, text=True
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for vuln in data.get("vulnerabilities", []):
                    vulnerabilities.append(
                        {
                            "package": vuln.get("package_name"),
                            "installed": vuln.get("analyzed_version"),
                            "affected": vuln.get("vulnerable_spec"),
                            "vulnerability": vuln.get("advisory"),
                            "severity": vuln.get("severity", "unknown"),
                        }
                    )
        except subprocess.CalledProcessError:
            print(
                f"{YELLOW}Warning: safety not installed. Run: pip install safety{RESET}"
            )
        except json.JSONDecodeError:
            print(f"{YELLOW}Warning: Could not parse safety output{RESET}")
        return vulnerabilities
    def check_outdated_packages(self) -> List[Dict]:
        """Check for outdated packages"""
        outdated = []
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    outdated.append(
                        {
                            "name": pkg["name"],
                            "current": pkg["version"],
                            "latest": pkg["latest_version"],
                            "type": pkg.get("latest_filetype", "wheel"),
                        }
                    )
        except Exception as e:
            print(f"{YELLOW}Warning: Could not check outdated packages: {e}{RESET}")
        return outdated
    def verify_no_virtualenv(self) -> List[Path]:
        """Check for virtualenv directories in repo"""
        venv_patterns = [
            "venv",
            "env",
            ".venv",
            ".env",
            "virtualenv",
            "pyenv",
            ".pyenv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
        ]
        found_venvs = []
        for pattern in venv_patterns:
            for path in self.project_root.glob(f"**/{pattern}"):
                if path.is_dir() and not str(path).startswith(
                    str(self.project_root / ".git")
                ):
                    found_venvs.append(path)
        return found_venvs
    def update_gitignore(self) -> bool:
        """Ensure gitignore excludes all virtualenv patterns"""
        gitignore_path = self.project_root / ".gitignore"
        venv_patterns = [
            "# Virtual Environments",
            "venv/",
            "env/",
            ".venv/",
            ".env",
            "virtualenv/",
            "pyenv/",
            ".pyenv/",
            "pipenv/",
            ".pipenv/",
            "poetry/",
            ".poetry/",
            "conda-env/",
            ".conda/",
            "",
            "# Python Cache",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            ".coverage",
            "htmlcov/",
            "",
            "# Package Management",
            "pip-log.txt",
            "pip-delete-this-directory.txt",
            ".eggs/",
            "*.egg-info/",
            "*.egg",
            "dist/",
            "build/",
            "wheels/",
            ".installed.cfg",
            "MANIFEST",
        ]
        try:
            # Read existing gitignore
            existing = set()
            if gitignore_path.exists():
                with open(gitignore_path) as f:
                    existing = set(line.strip() for line in f if line.strip())
            # Add missing patterns
            updated = False
            with open(gitignore_path, "a") as f:
                for pattern in venv_patterns:
                    if pattern and pattern not in existing:
                        f.write(f"{pattern}\n")
                        updated = True
            return updated
        except Exception as e:
            print(f"{RED}Error updating .gitignore: {e}{RESET}")
            return False
    def generate_report(self) -> str:
        """Generate comprehensive dependency report"""
        report = []
        report.append("# Dependency Management Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        # Check unpinned dependencies
        unpinned = self.check_unpinned_dependencies()
        if unpinned:
            report.append(f"## {RED}Unpinned Dependencies{RESET}")
            for dep in unpinned:
                report.append(f"  - {dep}")
            report.append("")
        else:
            report.append(f"## {GREEN}All Dependencies Pinned ✓{RESET}")
            report.append("")
        # Check security vulnerabilities
        vulns = self.check_security_vulnerabilities()
        if vulns:
            report.append(f"## {RED}Security Vulnerabilities{RESET}")
            for vuln in vulns:
                report.append(
                    f"  - {vuln['package']} {vuln['installed']}: {vuln['vulnerability']}"
                )
            report.append("")
        else:
            report.append(f"## {GREEN}No Security Vulnerabilities ✓{RESET}")
            report.append("")
        # Check outdated packages
        outdated = self.check_outdated_packages()
        if outdated:
            report.append(f"## {YELLOW}Outdated Packages{RESET}")
            for pkg in outdated[:10]:  # Show top 10
                report.append(f"  - {pkg['name']}: {pkg['current']} → {pkg['latest']}")
            if len(outdated) > 10:
                report.append(f"  ... and {len(outdated) - 10} more")
            report.append("")
        # Check for virtualenvs
        venvs = self.verify_no_virtualenv()
        if venvs:
            report.append(f"## {RED}Virtual Environments Found in Repo{RESET}")
            for venv in venvs[:5]:  # Show first 5
                report.append(f"  - {venv.relative_to(self.project_root)}")
            if len(venvs) > 5:
                report.append(f"  ... and {len(venvs) - 5} more")
            report.append("")
        else:
            report.append(f"## {GREEN}No Virtual Environments in Repo ✓{RESET}")
            report.append("")
        return "\n".join(report)
def main():
    """Main execution function"""
    manager = DependencyManager()
    print(f"{BLUE}=== Dependency Management Tool ==={RESET}")
    print()
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            # Check dependencies
            report = manager.generate_report()
            print(report)
        elif command == "pin":
            # Pin all dependencies
            unpinned = manager.check_unpinned_dependencies()
            if unpinned:
                print(f"{YELLOW}Found {len(unpinned)} unpinned dependencies{RESET}")
                for dep in unpinned:
                    print(f"  - {dep}")
                print(
                    f"\n{RED}Please update pyproject.toml to pin all dependencies{RESET}"
                )
                sys.exit(1)
            else:
                print(f"{GREEN}All dependencies are pinned ✓{RESET}")
        elif command == "lock":
            # Generate lock files
            success, message = manager.generate_lock_files()
            if success:
                print(f"{GREEN}{message}{RESET}")
            else:
                print(f"{RED}{message}{RESET}")
                sys.exit(1)
        elif command == "security":
            # Check security
            vulns = manager.check_security_vulnerabilities()
            if vulns:
                print(f"{RED}Found {len(vulns)} security vulnerabilities:{RESET}")
                for vuln in vulns:
                    print(
                        f"  - {vuln['package']} {vuln['installed']}: {vuln['vulnerability']}"
                    )
                sys.exit(1)
            else:
                print(f"{GREEN}No security vulnerabilities found ✓{RESET}")
        elif command == "clean":
            # Clean virtualenvs
            venvs = manager.verify_no_virtualenv()
            if venvs:
                print(
                    f"{YELLOW}Found {len(venvs)} virtual environment directories{RESET}"
                )
                for venv in venvs:
                    print(f"  - {venv.relative_to(manager.project_root)}")
                print(
                    f"\n{RED}Please remove these directories from the repository{RESET}"
                )
                sys.exit(1)
            else:
                print(f"{GREEN}No virtual environments in repository ✓{RESET}")
        elif command == "update-gitignore":
            # Update gitignore
            if manager.update_gitignore():
                print(f"{GREEN}.gitignore updated with virtualenv patterns ✓{RESET}")
            else:
                print(f"{YELLOW}.gitignore already up to date{RESET}")
        else:
            print(f"{RED}Unknown command: {command}{RESET}")
            print("\nAvailable commands:")
            print("  check          - Generate full dependency report")
            print("  pin            - Check for unpinned dependencies")
            print("  lock           - Generate lock files")
            print("  security       - Check for security vulnerabilities")
            print("  clean          - Check for virtualenvs in repo")
            print("  update-gitignore - Update .gitignore with venv patterns")
            sys.exit(1)
    else:
        # Default: run full check
        report = manager.generate_report()
        print(report)
if __name__ == "__main__":
    main()
