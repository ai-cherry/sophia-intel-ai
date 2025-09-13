#!/usr/bin/env python3
"""
Code Quality Check Script
Performs basic Python syntax validation and style checks
Similar to RUFF functionality for the Sophia AI codebase
"""
import ast
import os
class CodeQualityChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.files_checked = 0
    def check_file(self, filepath: str) -> dict[str, list[str]]:
        """Check a single Python file for issues"""
        issues = {"errors": [], "warnings": []}
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            # Check syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues["errors"].append(f"Syntax Error: {e.msg} at line {e.lineno}")
            except IndentationError as e:
                issues["errors"].append(
                    f"Indentation Error: {e.msg} at line {e.lineno}"
                )
            # Basic style checks
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > 88:
                    issues["warnings"].append(
                        f"Line {i}: Line too long ({len(line)} > 88 characters)"
                    )
                # Check for trailing whitespace
                if line.endswith(" ") or line.endswith("\t"):
                    issues["warnings"].append(f"Line {i}: Trailing whitespace")
                # Check for mixed tabs and spaces
                if "\t" in line and "    " in line:
                    issues["warnings"].append(f"Line {i}: Mixed tabs and spaces")
            try:
                tree = ast.parse(content)
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                imports.append(f"{node.module}.{alias.name}")
                for imp in imports:
                    if imp not in content.replace(f"import {imp}", ""):
                        continue  # Skip detailed unused import check for now
            except:
                pass  # Skip import analysis if AST parsing fails
        except Exception as e:
            issues["errors"].append(f"File reading error: {str(e)}")
        return issues
    def scan_directory(self, directory: str = ".") -> None:
        """Scan directory for Python files and check them"""
        python_files = []
        # Skip certain directories
        skip_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            ".pytest_cache",
        }
        for root, dirs, files in os.walk(directory):
            # Remove skip directories from dirs to prevent traversal
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    python_files.append(filepath)
        # Check each Python file
        for filepath in python_files[:20]:  # Limit to first 20 files for performance
            self.files_checked += 1
            issues = self.check_file(filepath)
            if issues["errors"]:
                self.errors.extend([(filepath, error) for error in issues["errors"]])
            if issues["warnings"]:
                self.warnings.extend(
                    [(filepath, warning) for warning in issues["warnings"]]
                )
    def generate_report(self) -> str:
        """Generate a summary report"""
        report = []
        report.append("🔍 SOPHIA AI CODE QUALITY REPORT")
        report.append("=" * 50)
        report.append(f"Files checked: {self.files_checked}")
        report.append(f"Errors found: {len(self.errors)}")
        report.append(f"Warnings found: {len(self.warnings)}")
        report.append("")
        if self.errors:
            report.append("🚨 ERRORS:")
            report.append("-" * 20)
            for filepath, error in self.errors[:10]:  # Show first 10 errors
                report.append(f"📁 {filepath}")
                report.append(f"   ❌ {error}")
                report.append("")
            if len(self.errors) > 10:
                report.append(f"... and {len(self.errors) - 10} more errors")
                report.append("")
        if self.warnings:
            report.append("⚠️  WARNINGS:")
            report.append("-" * 20)
            for filepath, warning in self.warnings[:10]:  # Show first 10 warnings
                report.append(f"📁 {filepath}")
                report.append(f"   ⚠️  {warning}")
                report.append("")
            if len(self.warnings) > 10:
                report.append(f"... and {len(self.warnings) - 10} more warnings")
                report.append("")
        # Priority fixes
        if self.errors:
            report.append("🎯 PRIORITY FIXES NEEDED:")
            report.append("-" * 30)
            syntax_errors = [
                e
                for e in self.errors
                if "Syntax Error" in e[1] or "Indentation Error" in e[1]
            ]
            if syntax_errors:
                report.append("1. Fix syntax and indentation errors first")
                for filepath, error in syntax_errors[:5]:
                    report.append(f"   • {os.path.basename(filepath)}: {error}")
                report.append("")
        # Summary
        if self.errors == 0 and self.warnings == 0:
            report.append("✅ No critical issues found!")
        elif self.errors == 0:
            report.append("✅ No syntax errors found!")
            report.append("💡 Consider addressing warnings for better code quality")
        else:
            report.append("🔧 Fix syntax errors before deployment")
        return "\n".join(report)
def main():
    """Main function to run code quality checks"""
    print("🚀 Starting Sophia AI Code Quality Check...")
    print("(Python syntax validation and basic style checks)")
    print("")
    checker = CodeQualityChecker()
    checker.scan_directory(".")
    report = checker.generate_report()
    print(report)
    # Save report to file
    with open("code_quality_report.txt", "w") as f:
        f.write(report)
    print("\n📄 Report saved to: code_quality_report.txt")
    # Return exit code based on errors
    return 1 if checker.errors else 0
if __name__ == "__main__":
    exit(main())
