#!/usr/bin/env python3
"""
Duplicate Detection Script for Pre-commit Hooks
Prevents code duplication and architectural conflicts
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from app.core.ai_logger import logger


class DuplicateDetector:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.classes: dict[str, list[str]] = defaultdict(list)
        self.functions: dict[str, list[str]] = defaultdict(list)
        self.components: dict[str, list[str]] = defaultdict(list)
        self.endpoints: dict[str, list[str]] = defaultdict(list)
        self.docker_services: dict[str, list[str]] = defaultdict(list)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def scan_python_files(self):
        """Scan Python files for duplicate classes and functions"""
        for py_file in self.root_path.rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    "__pycache__",
                    "node_modules",
                    ".git",
                    "build",
                    "dist",
                ]
            ):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self.classes[node.name].append(str(py_file))
                    elif isinstance(node, ast.FunctionDef):
                        # Only track top-level functions to avoid method duplicates
                        if not any(
                            isinstance(parent, ast.ClassDef)
                            for parent in ast.walk(tree)
                        ):
                            self.functions[node.name].append(str(py_file))
            except Exception as e:
                self.warnings.append(f"⚠️  Could not parse {py_file}: {e}")

    def scan_react_components(self):
        """Scan for duplicate React components"""
        patterns = ["*.jsx", "*.tsx"]
        for pattern in patterns:
            for component_file in self.root_path.rglob(pattern):
                if any(
                    skip in component_file.parts
                    for skip in ["node_modules", ".git", "build", "dist", ".next"]
                ):
                    continue

                try:
                    with open(component_file, encoding="utf-8") as f:
                        content = f.read()

                    # Extract component names (simplified)
                    import re

                    # Function components
                    func_pattern = r"(?:export\s+)?(?:const|function)\s+(\w+)\s*[:=]?\s*(?:\([^)]*\)|<[^>]*>)?\s*(?:=>|{)"
                    for match in re.finditer(func_pattern, content):
                        component_name = match.group(1)
                        if component_name[
                            0
                        ].isupper():  # React components start with capital
                            self.components[component_name].append(str(component_file))

                    # Class components
                    class_pattern = r"class\s+(\w+)\s+extends\s+(?:React\.)?Component"
                    for match in re.finditer(class_pattern, content):
                        self.components[match.group(1)].append(str(component_file))

                except Exception as e:
                    self.warnings.append(f"⚠️  Could not parse {component_file}: {e}")

    def scan_api_endpoints(self):
        """Scan for duplicate API endpoints"""
        for py_file in self.root_path.rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    "__pycache__",
                    "node_modules",
                    ".git",
                    "build",
                    "dist",
                ]
            ):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                import re

                # FastAPI/Flask endpoints
                patterns = [
                    r'@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@(?:app|router)\.route\s*\(\s*["\']([^"\']+)["\']',
                ]

                for pattern in patterns:
                    for match in re.finditer(pattern, content):
                        endpoint = match.group(1)
                        self.endpoints[endpoint].append(str(py_file))

            except Exception as e:
                self.warnings.append(f"⚠️  Could not scan endpoints in {py_file}: {e}")

    def scan_docker_services(self):
        """Scan docker-compose files for duplicate services"""
        docker_files = list(self.root_path.rglob("docker-compose*.yml")) + list(
            self.root_path.rglob("docker-compose*.yaml")
        )

        for docker_file in docker_files:
            try:
                with open(docker_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if config and "services" in config:
                    for service in config["services"]:
                        self.docker_services[service].append(str(docker_file))

            except Exception as e:
                self.warnings.append(f"⚠️  Could not parse {docker_file}: {e}")

    def check_for_duplicates(self):
        """Check all scanned items for duplicates"""
        # Check Python classes
        for class_name, locations in self.classes.items():
            if len(locations) > 1:
                self.errors.append(
                    f"❌ Duplicate class '{class_name}' found in:\n"
                    + "\n".join(f"    - {loc}" for loc in locations)
                )

        # Check React components
        for component_name, locations in self.components.items():
            if len(locations) > 1:
                self.errors.append(
                    f"❌ Duplicate React component '{component_name}' found in:\n"
                    + "\n".join(f"    - {loc}" for loc in locations)
                )

        # Check API endpoints
        for endpoint, locations in self.endpoints.items():
            if len(locations) > 1:
                self.errors.append(
                    f"❌ Duplicate API endpoint '{endpoint}' found in:\n"
                    + "\n".join(f"    - {loc}" for loc in locations)
                )

        # Check Docker services
        for service, locations in self.docker_services.items():
            if len(locations) > 1:
                self.warnings.append(
                    f"⚠️  Duplicate Docker service '{service}' found in:\n"
                    + "\n".join(f"    - {loc}" for loc in locations)
                )

    def check_naming_conflicts(self):
        """Check for similar names that might cause confusion"""
        # Check for similar class names
        class_names = list(self.classes.keys())
        for i, name1 in enumerate(class_names):
            for name2 in class_names[i + 1 :]:
                if name1.lower() == name2.lower() and name1 != name2:
                    self.warnings.append(
                        f"⚠️  Similar class names found: '{name1}' and '{name2}'"
                    )
                elif self._is_similar(name1, name2):
                    self.warnings.append(
                        f"⚠️  Potentially confusing class names: '{name1}' and '{name2}'"
                    )

    def _is_similar(self, s1: str, s2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar using Levenshtein distance"""
        if len(s1) < 3 or len(s2) < 3:
            return False

        # Simple similarity check
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
        return similarity > threshold

    def run(self) -> bool:
        """Run all checks and return success status"""
        logger.info("🔍 Scanning for duplicates and conflicts...")

        self.scan_python_files()
        self.scan_react_components()
        self.scan_api_endpoints()
        self.scan_docker_services()

        self.check_for_duplicates()
        self.check_naming_conflicts()

        # Print results
        if self.errors:
            logger.info("\n❌ ERRORS FOUND:")
            for error in self.errors:
                logger.info(f"\n{error}")

        if self.warnings:
            logger.info("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.info(f"\n{warning}")

        if not self.errors and not self.warnings:
            logger.info("✅ No duplicates or conflicts found!")

        # Print statistics
        logger.info("\n📊 Statistics:")
        logger.info(f"  - Python classes: {len(self.classes)}")
        logger.info(f"  - React components: {len(self.components)}")
        logger.info(f"  - API endpoints: {len(self.endpoints)}")
        logger.info(f"  - Docker services: {len(self.docker_services)}")

        return len(self.errors) == 0


def main():
    detector = DuplicateDetector()
    success = detector.run()

    if not success:
        logger.info("\n❌ Pre-commit check failed due to duplicates!")
        logger.info("Please resolve the issues above before committing.")
        sys.exit(1)
    else:
        logger.info("\n✅ Pre-commit check passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
