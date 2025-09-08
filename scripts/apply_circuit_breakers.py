#!/usr/bin/env python3
"""
Apply circuit breakers to critical external service calls
Part of the resilience improvements from architectural audit
"""

import argparse
import ast
import json
import re
from pathlib import Path

from app.core.ai_logger import logger


class CircuitBreakerApplicator:
    """Apply circuit breakers to external service calls"""

    # Critical functions that need circuit breakers
    CRITICAL_PATTERNS = {
        "llm_calls": [
            (r"openai\.(ChatCompletion|Completion|Embedding)", "llm"),
            (r"anthropic\.(messages|completions)", "llm"),
            (r"chat_with_gpt", "llm"),
            (r"chat_with_claude", "llm"),
            (r"generate_embedding", "llm"),
        ],
        "database_calls": [
            (r"weaviate\.(query|batch|data)", "weaviate"),
            (r"execute_query|search_memory", "database"),
            (r"hybrid_search", "database"),
        ],
        "redis_calls": [
            (r"redis\.(get|set|delete|exists)", "redis"),
            (r"cache\.(get|set|delete)", "redis"),
        ],
        "webhook_calls": [
            (r"webhook|n8n|trigger_workflow", "webhook"),
            (r"requests\.(post|get).*webhook", "webhook"),
        ],
        "external_apis": [
            (r"http(x|s)?://((?!localhost|127\.0\.0\.1))", "external_api"),
            (r"portkey|openrouter", "external_api"),
        ],
    }

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.files_to_update: list[tuple[Path, set[str]]] = []
        self.report = {
            "files_analyzed": 0,
            "files_updated": 0,
            "circuit_breakers_added": {},
            "functions_protected": [],
            "errors": [],
        }

    def scan_directory(self, directory: Path) -> None:
        """Scan directory for functions needing circuit breakers"""
        logger.info(f"🔍 Scanning {directory} for external service calls...")

        for py_file in directory.rglob("*.py"):
            # Skip test files and the circuit breaker module itself
            if any(
                skip in str(py_file)
                for skip in ["test", "__pycache__", ".git", "circuit_breaker.py"]
            ):
                continue

            self.report["files_analyzed"] += 1

            try:
                with open(py_file) as f:
                    content = f.read()

                # Check if already has circuit breakers
                if "@with_circuit_breaker" in content:
                    continue

                breakers_needed = set()

                # Check for each pattern type
                for _category, patterns in self.CRITICAL_PATTERNS.items():
                    for pattern, breaker_type in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            breakers_needed.add(breaker_type)

                if breakers_needed:
                    self.files_to_update.append((py_file, breakers_needed))

            except Exception as e:
                self.report["errors"].append(f"{py_file}: {str(e)}")

    def apply_to_file(self, file_path: Path, breaker_types: set[str]) -> bool:
        """Apply circuit breakers to a file"""
        logger.info(f"  📝 Applying circuit breakers to {file_path.name}...")

        try:
            with open(file_path) as f:
                content = f.read()

            original_content = content

            # Parse the AST to find functions
            tree = ast.parse(content)
            functions_to_protect = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check if function contains external calls
                    func_source = ast.get_source_segment(content, node)
                    if func_source:
                        for breaker_type in breaker_types:
                            if self._needs_protection(func_source, breaker_type):
                                functions_to_protect.append(
                                    (node.name, breaker_type, node.lineno)
                                )
                                break

            if not functions_to_protect:
                return False

            # Add import
            content = self._add_circuit_breaker_import(content)

            # Apply decorators to functions
            for func_name, breaker_type, _line_no in functions_to_protect:
                content = self._add_decorator_to_function(
                    content, func_name, breaker_type
                )
                self.report["functions_protected"].append(
                    f"{file_path.name}:{func_name}"
                )

                # Track breaker types
                if breaker_type not in self.report["circuit_breakers_added"]:
                    self.report["circuit_breakers_added"][breaker_type] = 0
                self.report["circuit_breakers_added"][breaker_type] += 1

            # Write changes if not dry run
            if content != original_content:
                if not self.dry_run:
                    # Backup original
                    backup_path = file_path.with_suffix(".py.bak")
                    with open(backup_path, "w") as f:
                        f.write(original_content)

                    # Write updated content
                    with open(file_path, "w") as f:
                        f.write(content)

                    logger.info(
                        f"    ✅ Protected {len(functions_to_protect)} functions"
                    )
                else:
                    logger.info(
                        f"    🔍 Would protect {len(functions_to_protect)} functions"
                    )

                self.report["files_updated"] += 1
                return True

        except Exception as e:
            self.report["errors"].append(f"{file_path}: {str(e)}")
            logger.info(f"    ❌ Error: {e}")
            return False

        return False

    def _needs_protection(self, func_source: str, breaker_type: str) -> bool:
        """Check if function needs protection based on its content"""
        patterns_to_check = []

        for _category, patterns in self.CRITICAL_PATTERNS.items():
            for pattern, btype in patterns:
                if btype == breaker_type:
                    patterns_to_check.append(pattern)

        return any(
            re.search(pattern, func_source, re.IGNORECASE)
            for pattern in patterns_to_check
        )

    def _add_circuit_breaker_import(self, content: str) -> str:
        """Add circuit breaker import to file"""
        # Check if already imported
        if "from app.core.circuit_breaker import" in content:
            return content

        lines = content.splitlines()

        # Find the last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")) and not line.startswith(
                "from __future__"
            ):
                last_import_idx = i

        # Insert import
        import_line = "from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker"

        if last_import_idx > 0:
            lines.insert(last_import_idx + 1, import_line)
        else:
            lines.insert(0, import_line)

        return "\n".join(lines)

    def _add_decorator_to_function(
        self, content: str, func_name: str, breaker_type: str
    ) -> str:
        """Add circuit breaker decorator to a function"""
        lines = content.splitlines()
        decorator = f'@with_circuit_breaker("{breaker_type}")'

        # Find the function definition
        for i, line in enumerate(lines):
            # Match function definition
            if re.match(rf"^(\s*)(async\s+)?def\s+{re.escape(func_name)}\s*\(", line):
                indent = re.match(r"^(\s*)", line).group(1)

                # Check if previous line is already a decorator
                if i > 0 and lines[i - 1].strip().startswith("@"):
                    # Add after existing decorators
                    lines.insert(i, indent + decorator)
                else:
                    # Add before function definition
                    lines.insert(i, indent + decorator)
                break

        return "\n".join(lines)

    def generate_report(self) -> None:
        """Generate application report"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 CIRCUIT BREAKER APPLICATION REPORT")
        logger.info("=" * 50)

        logger.info(f"Files analyzed: {self.report['files_analyzed']}")
        logger.info(f"Files needing protection: {len(self.files_to_update)}")
        logger.info(f"Files updated: {self.report['files_updated']}")
        logger.info(f"Functions protected: {len(self.report['functions_protected'])}")

        if self.report["circuit_breakers_added"]:
            logger.info("\nCircuit breakers by type:")
            for breaker_type, count in self.report["circuit_breakers_added"].items():
                logger.info(f"  - {breaker_type}: {count}")

        if self.report["errors"]:
            logger.info(f"\n⚠️  Errors encountered: {len(self.report['errors'])}")
            for error in self.report["errors"][:5]:
                logger.info(f"  - {error}")

        # Save detailed report
        report_path = Path("circuit_breaker_application_report.json")
        with open(report_path, "w") as f:
            json.dump(self.report, f, indent=2, default=str)

        logger.info(f"\n📄 Detailed report saved to: {report_path}")

    def run(self, directory: Path) -> None:
        """Run the circuit breaker application process"""
        logger.info("🛡️ Circuit Breaker Application Tool")
        logger.info("=" * 50)

        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode (no changes will be made)")
        else:
            logger.info("⚠️  Running in LIVE mode (files will be modified)")

        # Scan for files needing circuit breakers
        self.scan_directory(directory)

        logger.info(
            f"\n📋 Found {len(self.files_to_update)} files needing circuit breakers"
        )

        # Apply to each file
        for file_path, breaker_types in self.files_to_update:
            self.apply_to_file(file_path, breaker_types)

        # Generate report
        self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description="Apply circuit breakers to external service calls"
    )
    parser.add_argument(
        "--directory", default="app", help="Directory to scan (default: app)"
    )
    parser.add_argument(
        "--live", action="store_true", help="Run in live mode (actually modify files)"
    )

    args = parser.parse_args()

    applicator = CircuitBreakerApplicator(dry_run=not args.live)
    applicator.run(Path(args.directory))


if __name__ == "__main__":
    main()
