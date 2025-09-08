#!/usr/bin/env python3
"""
AI Rules Validation Script
Validates that all AI coding agents follow the established rules
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


class RulesValidator:
    def __init__(self):
        self.rules_dir = Path(".ai")
        self.project_root = Path(".")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.master_rules = self._load_master_rules()

    def _load_master_rules(self) -> dict[str, Any]:
        """Load the master rules configuration"""
        master_path = self.rules_dir / "MASTER_RULES.yaml"
        if not master_path.exists():
            self.errors.append(f"❌ Master rules file not found: {master_path}")
            return {}

        try:
            with open(master_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"❌ Failed to load master rules: {e}")
            return {}

    def check_for_mocks(self) -> None:
        """Check for mock implementations in the codebase"""
        print("🔍 Checking for mock implementations...")

        prohibited = (
            self.master_rules.get("enforcement", {})
            .get("anti_mock_policy", {})
            .get("prohibited_patterns", [])
        )

        for pattern in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file_path in self.project_root.rglob(pattern):
                # Skip test directories and node_modules
                if any(
                    part in str(file_path)
                    for part in [
                        "node_modules",
                        "__pycache__",
                        ".git",
                        "tests/fixtures",
                    ]
                ):
                    continue

                try:
                    content = file_path.read_text()

                    # Check for prohibited patterns
                    for prohibited_pattern in prohibited:
                        # Convert glob pattern to regex
                        regex = prohibited_pattern.replace("*", ".*")
                        if re.search(regex, content, re.IGNORECASE):
                            self.errors.append(
                                f"❌ Mock pattern '{prohibited_pattern}' found in {file_path}"
                            )

                    # Check for specific mock indicators
                    mock_indicators = [
                        r"class\s+Mock\w+",
                        r"class\s+Fake\w+",
                        r"class\s+Stub\w+",
                        r"def\s+mock_\w+",
                        r'return\s+["\']mock["\']',
                        r'console\.log\(["\']simulated',
                    ]

                    for indicator in mock_indicators:
                        if re.search(indicator, content):
                            self.errors.append(
                                f"❌ Mock indicator found in {file_path}: {indicator}"
                            )

                except Exception as e:
                    self.warnings.append(f"⚠️  Could not read {file_path}: {e}")

    def check_for_debris(self) -> None:
        """Check for old files and technical debt"""
        print("🔍 Checking for debris and old files...")

        debris_patterns = [
            "*_old.*",
            "*_backup.*",
            "*_deprecated*",
            "*.backup",
            "*.old",
            "*.tmp",
            "*.temp",
            "scratch.*",
            "test.*",  # Outside of test directories
        ]

        for pattern in debris_patterns:
            debris_files = list(self.project_root.rglob(pattern))
            for file_path in debris_files:
                # Allow test.* files in test directories
                if "test." in str(file_path) and "/test" in str(file_path):
                    continue
                self.errors.append(f"❌ Debris file found: {file_path}")

        # Check for empty files
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size == 0:
                # Allow some empty files like __init__.py
                if file_path.name != "__init__.py":
                    self.warnings.append(f"⚠️  Empty file found: {file_path}")

        # Check for old files (not modified in 30 days)
        max_age = (
            self.master_rules.get("enforcement", {})
            .get("zero_debris", {})
            .get("max_file_age_hours", 720)
        )
        cutoff_time = datetime.now() - timedelta(hours=max_age)

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                # Skip git files and dependencies
                if any(
                    part in str(file_path)
                    for part in [".git", "node_modules", "__pycache__"]
                ):
                    continue

                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time < cutoff_time:
                    self.warnings.append(f"⚠️  Old file (>{max_age}h): {file_path}")

    def check_forbidden_phrases(self) -> None:
        """Check for forbidden phrases in code"""
        print("🔍 Checking for forbidden phrases...")

        forbidden = (
            self.master_rules.get("enforcement", {})
            .get("truth_verification", {})
            .get("forbidden_phrases", [])
        )

        for pattern in ["*.py", "*.ts", "*.tsx", "*.md"]:
            for file_path in self.project_root.rglob(pattern):
                # Skip node_modules and git
                if any(part in str(file_path) for part in ["node_modules", ".git"]):
                    continue

                try:
                    content = file_path.read_text().lower()

                    for phrase in forbidden:
                        if phrase.lower() in content:
                            # Check if it's in a comment or string
                            lines = file_path.read_text().split("\n")
                            for i, line in enumerate(lines, 1):
                                if phrase.lower() in line.lower():
                                    self.errors.append(
                                        f"❌ Forbidden phrase '{phrase}' in {file_path}:{i}"
                                    )

                except Exception as e:
                    self.warnings.append(f"⚠️  Could not read {file_path}: {e}")

    def validate_yaml_files(self) -> None:
        """Validate all YAML configuration files"""
        print("🔍 Validating YAML files...")

        for yaml_file in self.rules_dir.rglob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
                print(f"  ✅ Valid YAML: {yaml_file}")
            except Exception as e:
                self.errors.append(f"❌ Invalid YAML in {yaml_file}: {e}")

        for yaml_file in self.rules_dir.rglob("*.yml"):
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
                print(f"  ✅ Valid YAML: {yaml_file}")
            except Exception as e:
                self.errors.append(f"❌ Invalid YAML in {yaml_file}: {e}")

    def validate_mdc_files(self) -> None:
        """Validate MDC (Markdown with metadata) files"""
        print("🔍 Validating MDC files...")

        for mdc_file in self.rules_dir.rglob("*.mdc"):
            try:
                content = mdc_file.read_text()

                # Check for proper frontmatter
                if not content.startswith("---"):
                    self.errors.append(f"❌ MDC file missing frontmatter: {mdc_file}")
                    continue

                # Extract frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    self.errors.append(f"❌ Invalid MDC format in {mdc_file}")
                    continue

                # Validate frontmatter YAML
                try:
                    metadata = yaml.safe_load(parts[1])
                    required_fields = ["agent", "role", "priority"]

                    for field in required_fields:
                        if field not in metadata:
                            self.errors.append(
                                f"❌ MDC file {mdc_file} missing required field: {field}"
                            )

                    print(f"  ✅ Valid MDC: {mdc_file}")

                except Exception as e:
                    self.errors.append(f"❌ Invalid frontmatter in {mdc_file}: {e}")

            except Exception as e:
                self.errors.append(f"❌ Could not read MDC file {mdc_file}: {e}")

    def check_tech_stack_compliance(self) -> None:
        """Check if only approved technologies are used"""
        print("🔍 Checking tech stack compliance...")

        approved_stack = self.master_rules.get("tech_stack", {}).get("approved", {})

        # Check Python requirements
        req_files = ["requirements.txt", "app/requirements.txt", "pyproject.toml"]
        for req_file in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text()

                    # Check for unapproved packages
                    unapproved = []
                    for line in content.split("\n"):
                        if line and not line.startswith("#"):
                            package = (
                                line.split("==")[0].split(">=")[0].split("<")[0].strip()
                            )

                            # Check if package is in approved list
                            approved = False
                            for category in approved_stack.values():
                                if isinstance(category, list):
                                    for approved_item in category:
                                        if package.lower() in approved_item.lower():
                                            approved = True
                                            break

                            if (
                                not approved
                                and package
                                and package not in ["", "-r", "-e"]
                            ):
                                unapproved.append(package)

                    if unapproved:
                        self.warnings.append(
                            f"⚠️  Potentially unapproved packages in {req_file}: {unapproved}"
                        )

                except Exception as e:
                    self.warnings.append(f"⚠️  Could not read {req_file}: {e}")

        # Check package.json
        package_files = ["package.json", "agent-ui/package.json", "ui/package.json"]
        for package_file in package_files:
            package_path = self.project_root / package_file
            if package_path.exists():
                try:
                    with open(package_path) as f:
                        package_data = json.load(f)

                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }

                    for dep, _version in dependencies.items():
                        # Check major frameworks
                        if dep in ["vue", "angular", "svelte", "ember"]:
                            self.errors.append(
                                f"❌ Unapproved framework in {package_file}: {dep}"
                            )

                except Exception as e:
                    self.warnings.append(f"⚠️  Could not read {package_file}: {e}")

    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("=" * 60)
        print("🚀 AI Rules Validation Starting...")
        print("=" * 60)

        # Run all checks
        self.check_for_mocks()
        self.check_for_debris()
        self.check_forbidden_phrases()
        self.validate_yaml_files()
        self.validate_mdc_files()
        self.check_tech_stack_compliance()

        # Print results
        print("\n" + "=" * 60)
        print("📊 Validation Results")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")
            return True

        return len(self.errors) == 0


def main():
    validator = RulesValidator()
    success = validator.run_validation()

    if not success:
        print("\n❌ Validation failed. Please fix the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Validation successful!")
        sys.exit(0)


if __name__ == "__main__":
    main()
