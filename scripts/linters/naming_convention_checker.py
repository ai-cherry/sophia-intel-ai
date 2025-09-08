#!/usr/bin/env python3
"""
Comprehensive Naming Convention Checker
Enforces PEP 8 and Sophia AI naming standards
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


class NamingConventionChecker(ast.NodeVisitor):
    """AST visitor to check naming conventions"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_ClassDef(self, node):
        """Check class naming (PascalCase)"""
        class_name = node.name

        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", class_name):
            self.violations.append(
                {
                    "type": "class_naming",
                    "line": node.lineno,
                    "name": class_name,
                    "issue": "Class name should be PascalCase (e.g., MyClass)",
                    "suggestion": self._to_pascal_case(class_name),
                }
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Check function naming (snake_case)"""
        func_name = node.name

        # Skip magic methods
        if func_name.startswith("__") and func_name.endswith("__"):
            self.generic_visit(node)
            return

        if not re.match(r"^[a-z_][a-z0-9_]*$", func_name):
            self.violations.append(
                {
                    "type": "function_naming",
                    "line": node.lineno,
                    "name": func_name,
                    "issue": "Function name should be snake_case (e.g., my_function)",
                    "suggestion": self._to_snake_case(func_name),
                }
            )

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Check variable naming (snake_case)"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                # Skip constants (SCREAMING_SNAKE_CASE is allowed)
                if re.match(r"^[A-Z_][A-Z0-9_]*$", var_name):
                    continue

                # Check for snake_case
                if not re.match(r"^[a-z_][a-z0-9_]*$", var_name):
                    self.violations.append(
                        {
                            "type": "variable_naming",
                            "line": node.lineno,
                            "name": var_name,
                            "issue": "Variable name should be snake_case (e.g., my_variable)",
                            "suggestion": self._to_snake_case(var_name),
                        }
                    )

        self.generic_visit(node)

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        # Handle snake_case to PascalCase
        if "_" in name:
            parts = name.split("_")
            return "".join(word.capitalize() for word in parts)

        # Handle camelCase to PascalCase
        if name and name[0].islower():
            return name[0].upper() + name[1:]

        return name

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        # Handle PascalCase/camelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def check_environment_variables(file_path: str) -> List[Dict[str, Any]]:
    """Check environment variable naming conventions"""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Find environment variable references
        env_patterns = [
            r'os\.getenv\(["\']([^"\']+)["\']',
            r'os\.environ\[["\']([^"\']+)["\']\]',
            r'getenv\(["\']([^"\']+)["\']',
        ]

        for pattern in env_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                env_var = match.group(1)

                # Check for SCREAMING_SNAKE_CASE
                if not re.match(r"^[A-Z_][A-Z0-9_]*$", env_var):
                    line_num = content[: match.start()].count("\n") + 1
                    violations.append(
                        {
                            "type": "env_var_naming",
                            "line": line_num,
                            "name": env_var,
                            "issue": "Environment variable should be SCREAMING_SNAKE_CASE",
                            "suggestion": env_var.upper().replace("-", "_"),
                        }
                    )

    except Exception as e:
        print(f"Error checking environment variables in {file_path}: {e}")

    return violations


def check_file_naming(file_path: Path) -> List[Dict[str, Any]]:
    """Check file naming conventions"""
    violations = []

    file_name = file_path.name

    # Python files should be snake_case
    if file_path.suffix == ".py":
        name_without_ext = file_path.stem

        if not re.match(r"^[a-z_][a-z0-9_]*$", name_without_ext):
            violations.append(
                {
                    "type": "file_naming",
                    "file": str(file_path),
                    "name": file_name,
                    "issue": "Python file should be snake_case.py",
                    "suggestion": re.sub(r"([A-Z])", r"_\1", name_without_ext)
                    .lower()
                    .lstrip("_")
                    + ".py",
                }
            )

    return violations


def check_mcp_naming(file_path: str) -> List[Dict[str, Any]]:
    """Check MCP server naming compliance"""
    violations = []

    if "mcp" not in file_path.lower():
        return violations

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for MCP class naming patterns
        mcp_class_pattern = r"class\s+([a-z_][a-z0-9_]*mcp[a-z0-9_]*)\s*:"
        matches = re.finditer(mcp_class_pattern, content, re.IGNORECASE)

        for match in matches:
            class_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # MCP classes should be PascalCase ending with 'MCPServer'
            if not re.match(r"^[A-Z][a-zA-Z0-9]*MCPServer$", class_name):
                violations.append(
                    {
                        "type": "mcp_naming",
                        "line": line_num,
                        "name": class_name,
                        "issue": "MCP class should be PascalCase ending with MCPServer",
                        "suggestion": class_name.replace("mcp", "MCP").replace("_", "")
                        + "Server",
                    }
                )

    except Exception as e:
        print(f"Error checking MCP naming in {file_path}: {e}")

    return violations


def main():
    """Main function to run all naming convention checks"""
    all_violations = []

    print("🔍 Running Sophia AI Naming Convention Checker...")

    # Check all Python files
    for py_file in Path(".").rglob("*.py"):
        if any(
            skip in str(py_file)
            for skip in [".git", "node_modules", "__pycache__", ".venv"]
        ):
            continue

        file_path = str(py_file)

        # AST-based checks
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            checker = NamingConventionChecker(file_path)
            checker.visit(tree)

            for violation in checker.violations:
                all_violations.append({"file": file_path, **violation})

        except Exception as e:
            print(f"Warning: Could not parse {py_file}: {e}")
            continue

        # Environment variable checks
        env_violations = check_environment_variables(file_path)
        for violation in env_violations:
            all_violations.append({"file": file_path, **violation})

        # MCP naming checks
        mcp_violations = check_mcp_naming(file_path)
        for violation in mcp_violations:
            all_violations.append({"file": file_path, **violation})

        # File naming checks
        file_violations = check_file_naming(py_file)
        for violation in file_violations:
            all_violations.append(violation)

    # Report results
    if all_violations:
        print(f"\n❌ Found {len(all_violations)} naming convention violations:")

        # Group by type
        by_type = {}
        for violation in all_violations:
            vtype = violation["type"]
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(violation)

        for vtype, violations in by_type.items():
            print(f"\n📋 {vtype.replace('_', ' ').title()} Issues ({len(violations)}):")
            for v in violations[:10]:  # Show first 10 of each type
                file_info = v.get("file", "N/A")
                line_info = f":{v['line']}" if "line" in v else ""
                print(f"  {file_info}{line_info}")
                print(f"    ❌ {v['name']} - {v['issue']}")
                if "suggestion" in v:
                    print(f"    ✅ Suggested: {v['suggestion']}")
                print()

            if len(violations) > 10:
                print(f"    ... and {len(violations) - 10} more")

        print("\n📊 Summary:")
        print(f"  Total violations: {len(all_violations)}")
        print(
            f"  Files affected: {len(set(v.get('file', '') for v in all_violations))}"
        )

        # Calculate compliance rate
        total_files = len(list(Path(".").rglob("*.py")))
        affected_files = len(set(v.get("file", "") for v in all_violations))
        compliance_rate = ((total_files - affected_files) / total_files) * 100

        print(f"  Compliance rate: {compliance_rate:.1f}%")

        if compliance_rate < 95:
            print("\n⚠️  Compliance rate below 95% target")
            sys.exit(1)
        else:
            print("\n✅ Compliance rate meets 95% target")
    else:
        print("\n✅ All naming conventions are compliant!")
        print("🎉 100% compliance rate achieved")


if __name__ == "__main__":
    main()
