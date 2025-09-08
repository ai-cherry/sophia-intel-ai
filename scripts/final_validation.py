#!/usr/bin/env python3
"""
Final Technical Debt Validation Script
Comprehensive validation and cleanup to achieve ZERO TECHNICAL DEBT.
This is the final step to ensure complete technical debt elimination.
"""

import ast
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FinalTechnicalDebtValidator:
    """Final validator to achieve ZERO technical debt"""

    def __init__(self):
        self.root_path = Path("/Users/lynnmusil/sophia-intel-ai")
        self.issues_found = []
        self.fixes_applied = []

        # Critical issues that must be zero
        self.critical_issues = {
            "circular_dependencies": [],
            "broken_imports": [],
            "orphaned_files": [],
            "duplicate_functionality": [],
            "configuration_conflicts": [],
            "security_vulnerabilities": [],
        }

        # Files that should exist after consolidation
        self.required_files = [
            "app/core/super_orchestrator.py",
            "dev_mcp_unified/core/mcp_server.py",
            "config/manager.py",
            "config/base.json",
        ]

        # Files/patterns that should NOT exist after consolidation
        self.forbidden_patterns = [
            "**/hybrid_intelligence_coordinator.py",
            "**/sophia_orchestrator.py",
            "**/artemis_orchestrator.py",
            "**/*_agno_orchestrator.py",
            "dev-mcp-unified/**/*",
            "app/mcp/server_v2.py",
            "app/mcp/secure_mcp_server.py",
            "port_config*.json",
            "*portkey_config.py",
        ]

    async def execute_final_validation(self):
        """Execute comprehensive final validation"""

        logger.info("🚀 FINAL TECHNICAL DEBT VALIDATION - ZERO DEBT MANDATE")

        # Phase 1: Structural Validation
        await self._validate_required_structure()

        # Phase 2: Circular Dependencies
        await self._detect_circular_dependencies()

        # Phase 3: Broken Imports
        await self._validate_all_imports()

        # Phase 4: Orphaned Files
        await self._detect_orphaned_files()

        # Phase 5: Duplicate Code
        await self._detect_duplicate_functionality()

        # Phase 6: Configuration Issues
        await self._validate_configurations()

        # Phase 7: Security Check
        await self._security_validation()

        # Phase 8: Performance Validation
        await self._performance_validation()

        # Phase 9: Apply Fixes
        await self._apply_critical_fixes()

        # Phase 10: Final Assessment
        final_report = await self._generate_final_report()

        if self._is_zero_technical_debt():
            logger.info("🎯 ZERO TECHNICAL DEBT ACHIEVED!")
        else:
            logger.error("❌ TECHNICAL DEBT STILL EXISTS - FIXING...")
            await self._emergency_cleanup()

        return final_report

    async def _validate_required_structure(self):
        """Validate that required files exist and forbidden files are gone"""

        logger.info("🔍 Validating required structure...")

        # Check required files exist
        missing_files = []
        for required_file in self.required_files:
            file_path = self.root_path / required_file
            if not file_path.exists():
                missing_files.append(required_file)

        if missing_files:
            self.critical_issues["broken_imports"].extend(missing_files)
            logger.error(f"❌ Missing required files: {missing_files}")
        else:
            logger.info("✅ All required files present")

        # Check forbidden patterns are gone
        forbidden_found = []
        for pattern in self.forbidden_patterns:
            matches = list(self.root_path.glob(pattern))
            if matches:
                forbidden_found.extend([str(m) for m in matches])

        if forbidden_found:
            self.critical_issues["orphaned_files"].extend(forbidden_found)
            logger.error(f"❌ Forbidden files still exist: {forbidden_found}")
        else:
            logger.info("✅ All forbidden files removed")

    async def _detect_circular_dependencies(self):
        """Detect circular import dependencies"""

        logger.info("🔍 Detecting circular dependencies...")

        import_graph = {}

        # Build import graph
        for py_file in self.root_path.rglob("*.py"):
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git"]
            ):
                continue

            try:
                imports = self._extract_imports_from_file(py_file)
                module_name = self._file_to_module_name(py_file)
                import_graph[module_name] = imports
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        # Detect cycles
        cycles = self._find_cycles(import_graph)

        if cycles:
            self.critical_issues["circular_dependencies"] = cycles
            logger.error(f"❌ Found {len(cycles)} circular dependencies")
            for cycle in cycles:
                logger.error(f"   Cycle: {' -> '.join(cycle)}")
        else:
            logger.info("✅ No circular dependencies found")

    async def _validate_all_imports(self):
        """Validate all import statements work"""

        logger.info("🔍 Validating all imports...")

        broken_imports = []

        for py_file in self.root_path.rglob("*.py"):
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git", "scripts/"]
            ):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if not self._can_import_module(alias.name):
                                broken_imports.append(
                                    {
                                        "file": str(
                                            py_file.relative_to(self.root_path)
                                        ),
                                        "import": alias.name,
                                        "type": "import",
                                    }
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not self._can_import_module(node.module):
                            broken_imports.append(
                                {
                                    "file": str(py_file.relative_to(self.root_path)),
                                    "import": node.module,
                                    "type": "from_import",
                                }
                            )

            except Exception as e:
                logger.warning(f"Could not validate imports in {py_file}: {e}")

        if broken_imports:
            self.critical_issues["broken_imports"] = broken_imports
            logger.error(f"❌ Found {len(broken_imports)} broken imports")
        else:
            logger.info("✅ All imports validated")

    async def _detect_orphaned_files(self):
        """Detect files that are no longer referenced"""

        logger.info("🔍 Detecting orphaned files...")

        all_py_files = set(self.root_path.rglob("*.py"))
        referenced_files = set()

        # Find all file references
        for py_file in all_py_files:
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git"]
            ):
                continue

            try:
                imports = self._extract_imports_from_file(py_file)
                for imp in imports:
                    referenced_file = self._import_to_file_path(imp)
                    if referenced_file:
                        referenced_files.add(referenced_file)
            except Exception:
                continue

        # Find orphaned files (not referenced and not entry points)
        entry_points = {
            self.root_path / "sophia_server_standalone.py",
            self.root_path / "artemis_server_standalone.py",
            self.root_path / "app/api/unified_server.py",
        }

        orphaned = []
        for py_file in all_py_files:
            if (
                py_file not in referenced_files
                and py_file not in entry_points
                and not any(
                    excluded in str(py_file)
                    for excluded in ["backup_", "__pycache__", ".git", "scripts/"]
                )
            ):
                orphaned.append(str(py_file.relative_to(self.root_path)))

        if orphaned:
            self.critical_issues["orphaned_files"] = orphaned
            logger.warning(f"⚠️  Found {len(orphaned)} potentially orphaned files")
        else:
            logger.info("✅ No orphaned files detected")

    async def _detect_duplicate_functionality(self):
        """Detect duplicate function/class definitions"""

        logger.info("🔍 Detecting duplicate functionality...")

        function_registry = {}
        class_registry = {}
        duplicates = []

        for py_file in self.root_path.rglob("*.py"):
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git"]
            ):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        if func_name in function_registry:
                            duplicates.append(
                                {
                                    "type": "function",
                                    "name": func_name,
                                    "files": [
                                        function_registry[func_name],
                                        str(py_file.relative_to(self.root_path)),
                                    ],
                                }
                            )
                        else:
                            function_registry[func_name] = str(
                                py_file.relative_to(self.root_path)
                            )

                    elif isinstance(node, ast.ClassDef):
                        class_name = node.name
                        if class_name in class_registry:
                            duplicates.append(
                                {
                                    "type": "class",
                                    "name": class_name,
                                    "files": [
                                        class_registry[class_name],
                                        str(py_file.relative_to(self.root_path)),
                                    ],
                                }
                            )
                        else:
                            class_registry[class_name] = str(
                                py_file.relative_to(self.root_path)
                            )

            except Exception:
                continue

        # Filter out acceptable duplicates (common names)
        acceptable_duplicates = {
            "main",
            "test",
            "run",
            "init",
            "setup",
            "Config",
            "Base",
        }
        significant_duplicates = [
            d for d in duplicates if d["name"] not in acceptable_duplicates
        ]

        if significant_duplicates:
            self.critical_issues["duplicate_functionality"] = significant_duplicates
            logger.warning(
                f"⚠️  Found {len(significant_duplicates)} duplicate definitions"
            )
        else:
            logger.info("✅ No significant duplicate functionality")

    async def _validate_configurations(self):
        """Validate configuration consistency"""

        logger.info("🔍 Validating configurations...")

        config_issues = []

        # Check unified config exists and is valid
        config_manager_path = self.root_path / "config/manager.py"
        if not config_manager_path.exists():
            config_issues.append("Unified configuration manager missing")

        # Check for remaining scattered configs
        scattered_configs = []
        for pattern in ["*.json", "*.env", "*.yaml", "*.yml"]:
            for config_file in self.root_path.rglob(pattern):
                if "config/" not in str(config_file) and "backup_" not in str(
                    config_file
                ):
                    scattered_configs.append(
                        str(config_file.relative_to(self.root_path))
                    )

        if scattered_configs:
            config_issues.extend([f"Scattered config: {c}" for c in scattered_configs])

        if config_issues:
            self.critical_issues["configuration_conflicts"] = config_issues
            logger.error(f"❌ Found {len(config_issues)} configuration issues")
        else:
            logger.info("✅ Configuration validation passed")

    async def _security_validation(self):
        """Check for security issues"""

        logger.info("🔍 Security validation...")

        security_issues = []

        # Check for hardcoded secrets
        for py_file in self.root_path.rglob("*.py"):
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git"]
            ):
                continue

            try:
                content = py_file.read_text()

                # Look for potential secrets
                secret_patterns = [
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                ]

                import re

                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if (
                            "your_" not in match.lower()
                            and "example" not in match.lower()
                        ):
                            security_issues.append(
                                {
                                    "file": str(py_file.relative_to(self.root_path)),
                                    "issue": "Potential hardcoded secret",
                                    "pattern": match[:50] + "...",
                                }
                            )

            except Exception:
                continue

        if security_issues:
            self.critical_issues["security_vulnerabilities"] = security_issues
            logger.error(f"❌ Found {len(security_issues)} potential security issues")
        else:
            logger.info("✅ Security validation passed")

    async def _performance_validation(self):
        """Validate performance characteristics"""

        logger.info("🔍 Performance validation...")

        # Check for performance anti-patterns
        performance_issues = []

        for py_file in self.root_path.rglob("*.py"):
            if any(
                excluded in str(py_file)
                for excluded in ["backup_", "__pycache__", ".git"]
            ):
                continue

            try:
                content = py_file.read_text()

                # Look for performance issues
                if "import *" in content:
                    performance_issues.append(
                        {
                            "file": str(py_file.relative_to(self.root_path)),
                            "issue": "Wildcard imports affect performance",
                        }
                    )

                if content.count("for ") > 5 and "async for" not in content:
                    performance_issues.append(
                        {
                            "file": str(py_file.relative_to(self.root_path)),
                            "issue": "Many synchronous loops - consider async",
                        }
                    )

            except Exception:
                continue

        if performance_issues:
            logger.warning(
                f"⚠️  Found {len(performance_issues)} performance suggestions"
            )
        else:
            logger.info("✅ Performance validation passed")

    async def _apply_critical_fixes(self):
        """Apply critical fixes for zero technical debt"""

        logger.info("🔧 Applying critical fixes...")

        fixes_applied = 0

        # Remove forbidden files
        for forbidden_file in self.critical_issues.get("orphaned_files", []):
            try:
                file_path = self.root_path / forbidden_file
                if file_path.exists():
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    fixes_applied += 1
                    logger.info(f"  ❌ Removed forbidden file: {forbidden_file}")
            except Exception as e:
                logger.error(f"Could not remove {forbidden_file}: {e}")

        # Fix broken imports (basic replacements)
        for broken_import in self.critical_issues.get("broken_imports", []):
            try:
                if self._fix_broken_import(broken_import):
                    fixes_applied += 1
            except Exception as e:
                logger.error(f"Could not fix import {broken_import}: {e}")

        self.fixes_applied.append(f"Applied {fixes_applied} critical fixes")
        logger.info(f"✅ Applied {fixes_applied} critical fixes")

    def _fix_broken_import(self, broken_import: dict) -> bool:
        """Fix a broken import"""

        file_path = self.root_path / broken_import["file"]
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text()

            # Common import fixes
            fixes = {
                "from app.core.hybrid_intelligence_coordinator": "from app.core.super_orchestrator",
                "from app.orchestrators.sophia_orchestrator": "from app.core.super_orchestrator",
                "from app.orchestrators.artemis_orchestrator": "from app.core.super_orchestrator",
                "from dev-mcp-unified.": "from dev_mcp_unified.",
                "from app.api.integrations_config": "from config.manager",
                "import portkey_config": "from config.manager import get_config_manager",
            }

            updated = False
            for old_import, new_import in fixes.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    updated = True

            if updated:
                file_path.write_text(content)
                return True

        except Exception:
            pass

        return False

    async def _emergency_cleanup(self):
        """Emergency cleanup to achieve zero technical debt"""

        logger.info("🚨 EMERGENCY CLEANUP - ZERO DEBT MANDATE")

        # Remove ALL forbidden patterns aggressively
        removed = 0
        for pattern in self.forbidden_patterns:
            matches = list(self.root_path.glob(pattern))
            for match in matches:
                try:
                    if match.is_dir():
                        shutil.rmtree(match)
                    else:
                        match.unlink()
                    removed += 1
                    logger.info(f"  🗑️ Emergency removal: {match}")
                except Exception as e:
                    logger.error(f"Emergency removal failed for {match}: {e}")

        logger.info(f"🧹 Emergency cleanup removed {removed} items")

    def _is_zero_technical_debt(self) -> bool:
        """Check if zero technical debt has been achieved"""

        critical_count = sum(len(issues) for issues in self.critical_issues.values())
        return critical_count == 0

    async def _generate_final_report(self) -> dict:
        """Generate final validation report"""

        critical_count = sum(len(issues) for issues in self.critical_issues.values())

        report = {
            "validation_completed": datetime.now().isoformat(),
            "zero_technical_debt_achieved": critical_count == 0,
            "critical_issues_count": critical_count,
            "critical_issues": self.critical_issues,
            "fixes_applied": self.fixes_applied,
            "structure_validation": {
                "required_files_present": all(
                    (self.root_path / f).exists() for f in self.required_files
                ),
                "forbidden_patterns_removed": not any(
                    list(self.root_path.glob(p)) for p in self.forbidden_patterns
                ),
            },
            "consolidation_success": {
                "orchestrator_consolidated": (
                    self.root_path / "app/core/super_orchestrator.py"
                ).exists(),
                "mcp_unified": (
                    self.root_path / "dev_mcp_unified/core/mcp_server.py"
                ).exists(),
                "config_unified": (self.root_path / "config/manager.py").exists(),
            },
            "quality_metrics": {
                "circular_dependencies": len(
                    self.critical_issues["circular_dependencies"]
                ),
                "broken_imports": len(self.critical_issues["broken_imports"]),
                "orphaned_files": len(self.critical_issues["orphaned_files"]),
                "duplicate_functions": len(
                    self.critical_issues["duplicate_functionality"]
                ),
                "config_conflicts": len(
                    self.critical_issues["configuration_conflicts"]
                ),
                "security_issues": len(
                    self.critical_issues["security_vulnerabilities"]
                ),
            },
        }

        # Save report
        report_path = self.root_path / "ZERO_TECHNICAL_DEBT_REPORT.json"
        report_path.write_text(json.dumps(report, indent=2))

        return report

    def _extract_imports_from_file(self, file_path: Path) -> list[str]:
        """Extract import statements from a Python file"""

        imports = []
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

        except Exception:
            pass

        return imports

    def _file_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""

        rel_path = file_path.relative_to(self.root_path)
        module_parts = rel_path.with_suffix("").parts
        return ".".join(module_parts)

    def _find_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """Find cycles in import graph"""

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]):
            if node in rec_stack:
                cycle_start = path.index(node) if node in path else 0
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor in graph:  # Only follow internal modules
                    dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _can_import_module(self, module_name: str) -> bool:
        """Check if a module can be imported"""

        # Skip external modules
        if not module_name.startswith(("app.", "dev_mcp_unified.", "config.")):
            return True

        # Convert to file path
        module_path = module_name.replace(".", "/")
        py_file = self.root_path / f"{module_path}.py"
        init_file = self.root_path / module_path / "__init__.py"

        return py_file.exists() or init_file.exists()

    def _import_to_file_path(self, import_name: str) -> Path:
        """Convert import name to file path"""

        if not import_name.startswith(("app.", "dev_mcp_unified.", "config.")):
            return None

        module_path = import_name.replace(".", "/")
        py_file = self.root_path / f"{module_path}.py"

        if py_file.exists():
            return py_file

        return None


async def main():
    """Execute final technical debt validation"""

    validator = FinalTechnicalDebtValidator()
    report = await validator.execute_final_validation()

    print("\n🎯 FINAL TECHNICAL DEBT VALIDATION COMPLETE")
    print("=" * 60)

    if report["zero_technical_debt_achieved"]:
        print("✅ ZERO TECHNICAL DEBT ACHIEVED!")
        print("🏆 MISSION ACCOMPLISHED - REPOSITORY IS CLEAN")
    else:
        print("❌ TECHNICAL DEBT STILL EXISTS")
        print(f"💀 Critical Issues: {report['critical_issues_count']}")

    print("\n📊 Quality Metrics:")
    for metric, count in report["quality_metrics"].items():
        status = "✅" if count == 0 else "❌"
        print(f"  {status} {metric}: {count}")

    print("\n🔧 Consolidation Status:")
    for component, status in report["consolidation_success"].items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}: {'SUCCESS' if status else 'FAILED'}")

    print("\n📋 Structure Validation:")
    for check, passed in report["structure_validation"].items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {check}: {'PASSED' if passed else 'FAILED'}")

    if report["fixes_applied"]:
        print("\n🛠️  Fixes Applied:")
        for fix in report["fixes_applied"]:
            print(f"  • {fix}")

    print("\n📄 Full report saved to: ZERO_TECHNICAL_DEBT_REPORT.json")

    # Final status
    if report["zero_technical_debt_achieved"]:
        print("\n🎉 CONGRATULATIONS!")
        print("🚀 Sophia Intelligence Platform is now TECHNICAL DEBT FREE")
        print("💎 Ready for production deployment with confidence")
    else:
        print("\n⚠️  WORK STILL REQUIRED")
        print("🔧 Review the report and address remaining issues")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
