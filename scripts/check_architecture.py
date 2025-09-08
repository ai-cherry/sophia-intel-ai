#!/usr/bin/env python3
"""
Architecture Compliance Checker
Ensures code follows defined architectural patterns and rules
"""

import ast
import sys
from pathlib import Path

import yaml

from app.core.ai_logger import logger


class ArchitectureChecker:
    def __init__(self, config_path: str = ".architecture.yaml"):
        self.config_path = Path(config_path)
        self.violations: list[str] = []
        self.warnings: list[str] = []
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load architecture configuration"""
        if not self.config_path.exists():
            logger.info(f"⚠️  No architecture config found at {self.config_path}")
            return self._get_default_config()

        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.info(f"❌ Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Default architecture rules"""
        return {
            "max_components": {
                "orchestrators": 4,
                "agents": 9,
                "managers": 3,
                "ui_components": 15,
                "docker_files": 1,
            },
            "naming_conventions": {
                "classes": "PascalCase",
                "functions": "snake_case",
                "constants": "UPPER_SNAKE_CASE",
                "files": "snake_case",
            },
            "forbidden_patterns": ["exec(", "eval(", "__import__", "os.system("],
            "required_patterns": {
                "api_endpoints": ["@router", "APIRouter"],
                "react_components": ["React.Component", "useState", "export"],
                "python_classes": ["__init__", "self"],
            },
            "dependency_rules": {
                "max_imports_per_file": 30,
                "forbidden_imports": ["*"],
                "circular_import_check": True,
            },
            "file_structure": {
                "max_file_size_kb": 500,
                "max_lines_per_file": 1000,
                "max_functions_per_file": 20,
                "max_classes_per_file": 5,
            },
        }

    def check_component_limits(self):
        """Check if component counts exceed limits"""
        component_counts = {
            "orchestrators": 0,
            "agents": 0,
            "managers": 0,
            "ui_components": 0,
            "docker_files": 0,
        }

        # Count orchestrators
        for file in Path("app").rglob("*orchestr*.py"):
            component_counts["orchestrators"] += 1

        # Count agents
        for file in Path("app").rglob("*agent*.py"):
            if "orchestr" not in str(file).lower():
                component_counts["agents"] += 1

        # Count managers
        for file in Path("app").rglob("*manager*.py"):
            component_counts["managers"] += 1

        # Count UI components
        for pattern in ["*.jsx", "*.tsx"]:
            for file in Path(".").rglob(pattern):
                if "node_modules" not in file.parts:
                    component_counts["ui_components"] += 1

        # Count Docker files
        component_counts["docker_files"] = len(
            list(Path(".").glob("Dockerfile*"))
        ) + len(list(Path(".").rglob("docker-compose*.y*ml")))

        # Check against limits
        max_components = self.config.get("max_components", {})
        for component_type, count in component_counts.items():
            limit = max_components.get(component_type, float("inf"))
            if count > limit:
                self.violations.append(
                    f"❌ Too many {component_type}: {count} (limit: {limit})"
                )
            elif count > limit * 0.8:  # Warning at 80% of limit
                self.warnings.append(
                    f"⚠️  Approaching limit for {component_type}: {count}/{limit}"
                )

    def check_naming_conventions(self):
        """Check if naming follows conventions"""
        for py_file in Path(".").rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    ".venv",
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
                        if not self._is_pascal_case(node.name):
                            self.warnings.append(
                                f"⚠️  Class '{node.name}' in {py_file} should be PascalCase"
                            )

                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_") and not self._is_snake_case(
                            node.name
                        ):
                            self.warnings.append(
                                f"⚠️  Function '{node.name}' in {py_file} should be snake_case"
                            )

                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                # Check if it's a constant (all caps)
                                if (
                                    target.id.isupper()
                                    and not self._is_upper_snake_case(target.id)
                                ):
                                    self.warnings.append(
                                        f"⚠️  Constant '{target.id}' in {py_file} should be UPPER_SNAKE_CASE"
                                    )

            except Exception:
                pass  # Skip files that can't be parsed

    def check_forbidden_patterns(self):
        """Check for forbidden code patterns"""
        forbidden = self.config.get("forbidden_patterns", [])

        for py_file in Path(".").rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    ".venv",
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

                for pattern in forbidden:
                    if pattern in content:
                        self.violations.append(
                            f"❌ Forbidden pattern '{pattern}' found in {py_file}"
                        )

            except Exception:
                pass

    def check_file_structure(self):
        """Check file size and complexity limits"""
        rules = self.config.get("file_structure", {})

        for py_file in Path(".").rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    ".venv",
                    "__pycache__",
                    "node_modules",
                    ".git",
                    "build",
                    "dist",
                ]
            ):
                continue

            try:
                # Check file size
                size_kb = py_file.stat().st_size / 1024
                max_size = rules.get("max_file_size_kb", 500)
                if size_kb > max_size:
                    self.violations.append(
                        f"❌ File {py_file} is too large: {size_kb:.1f}KB (limit: {max_size}KB)"
                    )

                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Check line count
                line_count = len(lines)
                max_lines = rules.get("max_lines_per_file", 1000)
                if line_count > max_lines:
                    self.violations.append(
                        f"❌ File {py_file} has too many lines: {line_count} (limit: {max_lines})"
                    )

                # Parse and check complexity
                tree = ast.parse("".join(lines))

                class_count = sum(
                    1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                )
                func_count = sum(
                    1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                )

                max_classes = rules.get("max_classes_per_file", 5)
                max_functions = rules.get("max_functions_per_file", 20)

                if class_count > max_classes:
                    self.violations.append(
                        f"❌ File {py_file} has too many classes: {class_count} (limit: {max_classes})"
                    )

                if func_count > max_functions:
                    self.violations.append(
                        f"❌ File {py_file} has too many functions: {func_count} (limit: {max_functions})"
                    )

            except Exception:
                pass

    def check_import_complexity(self):
        """Check import statement complexity"""
        rules = self.config.get("dependency_rules", {})
        max_imports = rules.get("max_imports_per_file", 30)

        for py_file in Path(".").rglob("*.py"):
            if any(
                skip in py_file.parts
                for skip in [
                    "venv",
                    ".venv",
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

                imports = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                ]

                if len(imports) > max_imports:
                    self.violations.append(
                        f"❌ File {py_file} has too many imports: {len(imports)} (limit: {max_imports})"
                    )

                # Check for wildcard imports
                for imp in imports:
                    if isinstance(imp, ast.ImportFrom):
                        for alias in imp.names:
                            if alias.name == "*":
                                self.violations.append(
                                    f"❌ Wildcard import found in {py_file}"
                                )

            except Exception:
                pass

    def _is_pascal_case(self, name: str) -> bool:
        """Check if name is PascalCase"""
        return name[0].isupper() and "_" not in name

    def _is_snake_case(self, name: str) -> bool:
        """Check if name is snake_case"""
        return name.islower() or "_" in name

    def _is_upper_snake_case(self, name: str) -> bool:
        """Check if name is UPPER_SNAKE_CASE"""
        return name.isupper()

    def run(self) -> bool:
        """Run all architecture checks"""
        logger.info("🏗️  Checking architecture compliance...")

        self.check_component_limits()
        self.check_naming_conventions()
        self.check_forbidden_patterns()
        self.check_file_structure()
        self.check_import_complexity()

        # Print results
        if self.violations:
            logger.info("\n❌ ARCHITECTURE VIOLATIONS:")
            for violation in self.violations:
                logger.info(f"\n{violation}")

        if self.warnings:
            logger.info("\n⚠️  ARCHITECTURE WARNINGS:")
            for warning in self.warnings:
                logger.info(f"\n{warning}")

        if not self.violations and not self.warnings:
            logger.info("✅ Architecture compliance check passed!")

        return len(self.violations) == 0


def main():
    checker = ArchitectureChecker()
    success = checker.run()

    if not success:
        logger.info("\n❌ Architecture check failed!")
        logger.info("Please resolve the violations before committing.")
        sys.exit(1)
    else:
        logger.info("\n✅ Architecture check passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
