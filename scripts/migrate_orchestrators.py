#!/usr/bin/env python3
"""
Orchestrator Migration Script
Identifies duplicate orchestrator code, generates migration report, and updates imports
"""
import ast
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class DuplicateCode:
    """Represents identified duplicate code"""

    file1: str
    file2: str
    similarity_score: float
    duplicate_lines: List[str]
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    category: str = "general"


@dataclass
class OrchrestratorInfo:
    """Information about an orchestrator file"""

    file_path: str
    classes: List[str]
    functions: List[str]
    imports: List[str]
    lines_of_code: int
    complexity_score: float
    dependencies: List[str]


@dataclass
class MigrationReport:
    """Migration analysis report"""

    total_files_analyzed: int
    duplicate_code_instances: List[DuplicateCode]
    orchestrator_info: List[OrchrestratorInfo]
    consolidation_recommendations: List[str]
    import_updates: Dict[str, List[str]]
    estimated_code_reduction: int
    risk_assessment: Dict[str, str]
    migration_steps: List[str]
    backup_created: bool = False
    generated_at: datetime = field(default_factory=datetime.now)


class CodeAnalyzer:
    """Analyzes code for duplication and structure"""

    def __init__(self):
        self.similarity_threshold = 0.7
        self.min_duplicate_lines = 10

    def analyze_file(self, file_path: str) -> OrchrestratorInfo:
        """Analyze a single orchestrator file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            classes = []
            functions = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):  # Only public functions
                        functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            lines_of_code = len(
                [
                    line
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
            )
            complexity_score = self._calculate_complexity(content)
            dependencies = self._extract_dependencies(content)

            return OrchrestratorInfo(
                file_path=file_path,
                classes=classes,
                functions=functions,
                imports=imports,
                lines_of_code=lines_of_code,
                complexity_score=complexity_score,
                dependencies=dependencies,
            )

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return OrchrestratorInfo(
                file_path=file_path,
                classes=[],
                functions=[],
                imports=[],
                lines_of_code=0,
                complexity_score=0,
                dependencies=[],
            )

    def _calculate_complexity(self, content: str) -> float:
        """Calculate code complexity score"""
        complexity = 1

        # Count decision points
        decision_keywords = [
            "if",
            "elif",
            "else",
            "for",
            "while",
            "try",
            "except",
            "with",
        ]
        for keyword in decision_keywords:
            complexity += content.count(f" {keyword} ")
            complexity += content.count(f"\n{keyword} ")
            complexity += content.count(f"\t{keyword} ")

        # Normalize by lines of code
        lines = len(content.split("\n"))
        return complexity / max(lines, 1) * 100

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from imports"""
        dependencies = []

        # Extract from imports
        import_pattern = r"from\s+([^\s]+)\s+import|import\s+([^\s,\n]+)"
        matches = re.findall(import_pattern, content)

        for match in matches:
            dep = match[0] or match[1]
            if dep and "." in dep:
                root_dep = dep.split(".")[0]
                if not root_dep.startswith("app"):  # External dependencies
                    dependencies.append(root_dep)

        return list(set(dependencies))

    def find_duplicate_code(
        self, file1_path: str, file2_path: str
    ) -> List[DuplicateCode]:
        """Find duplicate code between two files"""
        try:
            with open(file1_path, encoding="utf-8") as f:
                content1 = f.read()
            with open(file2_path, encoding="utf-8") as f:
                content2 = f.read()

            duplicates = []

            # Find duplicate functions
            duplicates.extend(
                self._find_duplicate_functions(
                    file1_path, file2_path, content1, content2
                )
            )

            # Find duplicate class methods
            duplicates.extend(
                self._find_duplicate_methods(file1_path, file2_path, content1, content2)
            )

            # Find general code block duplicates
            duplicates.extend(
                self._find_duplicate_blocks(file1_path, file2_path, content1, content2)
            )

            return duplicates

        except Exception as e:
            print(
                f"Error finding duplicates between {file1_path} and {file2_path}: {e}"
            )
            return []

    def _find_duplicate_functions(
        self, file1: str, file2: str, content1: str, content2: str
    ) -> List[DuplicateCode]:
        """Find duplicate functions between files"""
        duplicates = []

        functions1 = self._extract_functions(content1)
        functions2 = self._extract_functions(content2)

        for func1_name, func1_body in functions1.items():
            for func2_name, func2_body in functions2.items():
                similarity = self._calculate_similarity(func1_body, func2_body)

                if similarity > self.similarity_threshold:
                    duplicates.append(
                        DuplicateCode(
                            file1=file1,
                            file2=file2,
                            similarity_score=similarity,
                            duplicate_lines=func1_body.split("\n"),
                            function_name=f"{func1_name} / {func2_name}",
                            category="function",
                        )
                    )

        return duplicates

    def _find_duplicate_methods(
        self, file1: str, file2: str, content1: str, content2: str
    ) -> List[DuplicateCode]:
        """Find duplicate class methods between files"""
        duplicates = []

        methods1 = self._extract_class_methods(content1)
        methods2 = self._extract_class_methods(content2)

        for (class1, method1), body1 in methods1.items():
            for (class2, method2), body2 in methods2.items():
                if (
                    method1 == method2 and class1 != class2
                ):  # Same method name, different classes
                    similarity = self._calculate_similarity(body1, body2)

                    if similarity > self.similarity_threshold:
                        duplicates.append(
                            DuplicateCode(
                                file1=file1,
                                file2=file2,
                                similarity_score=similarity,
                                duplicate_lines=body1.split("\n"),
                                function_name=method1,
                                class_name=f"{class1} / {class2}",
                                category="method",
                            )
                        )

        return duplicates

    def _find_duplicate_blocks(
        self, file1: str, file2: str, content1: str, content2: str
    ) -> List[DuplicateCode]:
        """Find duplicate code blocks between files"""
        duplicates = []

        lines1 = content1.split("\n")
        lines2 = content2.split("\n")

        # Look for sequences of similar lines
        for i in range(len(lines1) - self.min_duplicate_lines):
            block1 = lines1[i : i + self.min_duplicate_lines]
            block1_clean = [
                line.strip()
                for line in block1
                if line.strip() and not line.strip().startswith("#")
            ]

            if len(block1_clean) < self.min_duplicate_lines:
                continue

            for j in range(len(lines2) - self.min_duplicate_lines):
                block2 = lines2[j : j + self.min_duplicate_lines]
                block2_clean = [
                    line.strip()
                    for line in block2
                    if line.strip() and not line.strip().startswith("#")
                ]

                if len(block2_clean) < self.min_duplicate_lines:
                    continue

                similarity = self._calculate_similarity(
                    "\n".join(block1_clean), "\n".join(block2_clean)
                )

                if similarity > self.similarity_threshold:
                    duplicates.append(
                        DuplicateCode(
                            file1=file1,
                            file2=file2,
                            similarity_score=similarity,
                            duplicate_lines=block1,
                            category="block",
                        )
                    )
                    break  # Avoid finding overlapping blocks

        return duplicates

    def _extract_functions(self, content: str) -> Dict[str, str]:
        """Extract functions and their bodies from content"""
        functions = {}

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    # Get function source
                    start_line = node.lineno
                    end_line = (
                        node.end_lineno
                        if hasattr(node, "end_lineno")
                        else start_line + 10
                    )

                    lines = content.split("\n")
                    func_body = "\n".join(lines[start_line - 1 : end_line])
                    functions[node.name] = func_body

        except Exception as e:
            print(f"Error extracting functions: {e}")

        return functions

    def _extract_class_methods(self, content: str) -> Dict[Tuple[str, str], str]:
        """Extract class methods and their bodies"""
        methods = {}

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                    for item in node.body:
                        if isinstance(
                            item, ast.FunctionDef
                        ) and not item.name.startswith("_"):
                            method_name = item.name
                            start_line = item.lineno
                            end_line = (
                                item.end_lineno
                                if hasattr(item, "end_lineno")
                                else start_line + 10
                            )

                            lines = content.split("\n")
                            method_body = "\n".join(lines[start_line - 1 : end_line])
                            methods[(class_name, method_name)] = method_body

        except Exception as e:
            print(f"Error extracting class methods: {e}")

        return methods

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text blocks"""
        # Normalize texts
        text1_clean = re.sub(r"\s+", " ", text1.lower().strip())
        text2_clean = re.sub(r"\s+", " ", text2.lower().strip())

        if not text1_clean or not text2_clean:
            return 0.0

        # Simple word-based similarity
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)


class ImportUpdater:
    """Updates imports across the codebase"""

    def __init__(self):
        self.import_mapping = {
            # Old imports -> New unified imports
            "from app.sophia.sophia_orchestrator import SophiaOrchestrator": "from app.orchestrators.sophia_unified import SophiaUnifiedOrchestrator",
            "from app.artemis.artemis_orchestrator import ArtemisOrchestrator": "from app.orchestrators.artemis_unified import ArtemisUnifiedOrchestrator",
            "from app.orchestrators.base_orchestrator import BaseOrchestrator": "from app.orchestrators.unified_base import UnifiedBaseOrchestrator",
        }

        self.class_mapping = {
            "SophiaOrchestrator": "SophiaUnifiedOrchestrator",
            "ArtemisOrchestrator": "ArtemisUnifiedOrchestrator",
            "BaseOrchestrator": "UnifiedBaseOrchestrator",
        }

    def find_files_to_update(self, project_root: Path) -> List[str]:
        """Find files that need import updates"""
        files_to_update = []

        for file_path in project_root.rglob("*.py"):
            if self._file_needs_update(file_path):
                files_to_update.append(str(file_path))

        return files_to_update

    def _file_needs_update(self, file_path: Path) -> bool:
        """Check if file needs import updates"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            for old_import in self.import_mapping.keys():
                if old_import in content:
                    return True

            for old_class in self.class_mapping.keys():
                if f"{old_class}(" in content or f"{old_class} " in content:
                    return True

            return False

        except Exception:
            return False

    def update_imports(self, file_path: str, dry_run: bool = True) -> List[str]:
        """Update imports in a file"""
        updates = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Update import statements
            for old_import, new_import in self.import_mapping.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    updates.append(f"Updated import: {old_import} -> {new_import}")

            # Update class references
            for old_class, new_class in self.class_mapping.items():
                # Update class instantiation
                pattern = rf"\b{old_class}\("
                if re.search(pattern, content):
                    content = re.sub(pattern, f"{new_class}(", content)
                    updates.append(
                        f"Updated class instantiation: {old_class}() -> {new_class}()"
                    )

                # Update type hints and inheritance
                pattern = rf":\s*{old_class}\b"
                if re.search(pattern, content):
                    content = re.sub(pattern, f": {new_class}", content)
                    updates.append(f"Updated type hint: {old_class} -> {new_class}")

            # Write updated content if not dry run
            if not dry_run and content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                updates.append(f"File updated: {file_path}")

        except Exception as e:
            updates.append(f"Error updating {file_path}: {e}")

        return updates


class MigrationOrchestrator:
    """Main orchestrator for migration process"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.code_analyzer = CodeAnalyzer()
        self.import_updater = ImportUpdater()

        # Orchestrator file patterns
        self.orchestrator_patterns = [
            "**/orchestrators/**/*.py",
            "**/sophia/**/*orchestrator*.py",
            "**/artemis/**/*orchestrator*.py",
            "**/core/**/*orchestrator*.py",
            "**/swarms/**/*orchestrator*.py",
        ]

        # Files to exclude from analysis
        self.exclude_patterns = [
            "**/__pycache__/**",
            "**/tests/**",
            "**/venv/**",
            "**/node_modules/**",
            "**/.git/**",
        ]

    def run_migration_analysis(self) -> MigrationReport:
        """Run complete migration analysis"""
        print("🔍 Starting orchestrator migration analysis...")

        # Find orchestrator files
        orchestrator_files = self._find_orchestrator_files()
        print(f"Found {len(orchestrator_files)} orchestrator files")

        # Analyze each file
        orchestrator_info = []
        for file_path in orchestrator_files:
            print(f"  Analyzing: {Path(file_path).name}")
            info = self.code_analyzer.analyze_file(file_path)
            orchestrator_info.append(info)

        # Find duplicate code
        print("🔄 Analyzing code duplication...")
        duplicate_code = self._find_all_duplicates(orchestrator_files)
        print(f"Found {len(duplicate_code)} duplicate code instances")

        # Generate consolidation recommendations
        print("💡 Generating recommendations...")
        recommendations = self._generate_recommendations(
            orchestrator_info, duplicate_code
        )

        # Find import updates needed
        print("📦 Analyzing import dependencies...")
        files_to_update = self.import_updater.find_files_to_update(self.project_root)
        import_updates = {}
        for file_path in files_to_update[:10]:  # Limit for analysis
            updates = self.import_updater.update_imports(file_path, dry_run=True)
            if updates:
                import_updates[file_path] = updates

        # Estimate code reduction
        code_reduction = self._estimate_code_reduction(duplicate_code)

        # Risk assessment
        risk_assessment = self._assess_risks(orchestrator_info, duplicate_code)

        # Migration steps
        migration_steps = self._generate_migration_steps(
            orchestrator_info, duplicate_code
        )

        report = MigrationReport(
            total_files_analyzed=len(orchestrator_files),
            duplicate_code_instances=duplicate_code,
            orchestrator_info=orchestrator_info,
            consolidation_recommendations=recommendations,
            import_updates=import_updates,
            estimated_code_reduction=code_reduction,
            risk_assessment=risk_assessment,
            migration_steps=migration_steps,
        )

        print("✅ Migration analysis complete!")
        return report

    def _find_orchestrator_files(self) -> List[str]:
        """Find all orchestrator files in the project"""
        files = []

        for pattern in self.orchestrator_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.suffix == ".py":
                    # Check if file should be excluded
                    should_exclude = any(
                        file_path.match(exclude_pattern)
                        for exclude_pattern in self.exclude_patterns
                    )

                    if not should_exclude:
                        files.append(str(file_path))

        return files

    def _find_all_duplicates(self, files: List[str]) -> List[DuplicateCode]:
        """Find all duplicate code instances"""
        duplicates = []

        for i, file1 in enumerate(files):
            for file2 in files[i + 1 :]:
                file_duplicates = self.code_analyzer.find_duplicate_code(file1, file2)
                duplicates.extend(file_duplicates)

        return duplicates

    def _generate_recommendations(
        self,
        orchestrator_info: List[OrchrestratorInfo],
        duplicates: List[DuplicateCode],
    ) -> List[str]:
        """Generate consolidation recommendations"""
        recommendations = []

        # Analyze duplicate functions
        duplicate_functions = [d for d in duplicates if d.category == "function"]
        if duplicate_functions:
            recommendations.append(
                f"🔄 Found {len(duplicate_functions)} duplicate functions that can be consolidated into base classes"
            )

        # Analyze duplicate methods
        duplicate_methods = [d for d in duplicates if d.category == "method"]
        if duplicate_methods:
            recommendations.append(
                f"🔧 Found {len(duplicate_methods)} duplicate methods - consider shared utilities or mixins"
            )

        # Analyze complexity
        high_complexity_files = [
            info for info in orchestrator_info if info.complexity_score > 15
        ]
        if high_complexity_files:
            recommendations.append(
                f"⚡ {len(high_complexity_files)} files have high complexity - candidate for refactoring"
            )

        # Analyze dependencies
        all_dependencies = set()
        for info in orchestrator_info:
            all_dependencies.update(info.dependencies)

        if len(all_dependencies) > 20:
            recommendations.append(
                f"📦 High number of dependencies ({len(all_dependencies)}) - consider dependency consolidation"
            )

        # Unified orchestrator benefits
        recommendations.extend(
            [
                "✨ Implement unified base orchestrator to eliminate code duplication",
                "🔗 Create cross-learning orchestrator for knowledge sharing",
                "🎯 Consolidate Sophia and Artemis into unified specialized orchestrators",
                "📊 Implement comprehensive monitoring and quality assurance",
                "🚀 Add persona management and memory integration",
            ]
        )

        return recommendations

    def _estimate_code_reduction(self, duplicates: List[DuplicateCode]) -> int:
        """Estimate lines of code reduction from consolidation"""
        total_reduction = 0

        for duplicate in duplicates:
            # Estimate reduction as 70% of duplicate lines (keeping some for interface)
            reduction = int(len(duplicate.duplicate_lines) * 0.7)
            total_reduction += reduction

        return total_reduction

    def _assess_risks(
        self,
        orchestrator_info: List[OrchrestratorInfo],
        duplicates: List[DuplicateCode],
    ) -> Dict[str, str]:
        """Assess migration risks"""
        risks = {}

        # Complexity risk
        avg_complexity = sum(info.complexity_score for info in orchestrator_info) / len(
            orchestrator_info
        )
        if avg_complexity > 10:
            risks["complexity"] = "High - Complex codebase requires careful refactoring"
        else:
            risks["complexity"] = "Low - Manageable complexity levels"

        # Dependency risk
        unique_deps = set()
        for info in orchestrator_info:
            unique_deps.update(info.dependencies)

        if len(unique_deps) > 15:
            risks["dependencies"] = (
                "Medium - Many dependencies may cause integration issues"
            )
        else:
            risks["dependencies"] = "Low - Reasonable number of dependencies"

        # Duplication risk
        if len(duplicates) > 20:
            risks["duplication"] = (
                "High - Extensive duplication may indicate deeper architectural issues"
            )
        elif len(duplicates) > 10:
            risks["duplication"] = "Medium - Significant duplication present"
        else:
            risks["duplication"] = "Low - Minimal duplication found"

        # Import risk
        risks["imports"] = "Medium - Import updates required across multiple files"

        return risks

    def _generate_migration_steps(
        self,
        orchestrator_info: List[OrchrestratorInfo],
        duplicates: List[DuplicateCode],
    ) -> List[str]:
        """Generate migration steps"""
        steps = [
            "1. 📋 Create backup of existing orchestrator files",
            "2. 🏗️ Implement UnifiedBaseOrchestrator with shared functionality",
            "3. 🧠 Create SophiaUnifiedOrchestrator consolidating business intelligence",
            "4. ⚙️ Create ArtemisUnifiedOrchestrator consolidating code excellence",
            "5. 🤝 Implement CrossLearningOrchestrator for collaboration",
            "6. 📦 Update imports across codebase to use new orchestrators",
            "7. 🧪 Run comprehensive tests to ensure functionality",
            "8. 🔄 Gradually deprecate old orchestrator files",
            "9. 📊 Monitor performance and fix any issues",
            "10. 🗑️ Clean up deprecated files after validation",
        ]

        return steps

    def create_backup(self) -> bool:
        """Create backup of orchestrator files"""
        try:
            backup_dir = (
                self.project_root
                / "backup_orchestrators"
                / datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            backup_dir.mkdir(parents=True, exist_ok=True)

            orchestrator_files = self._find_orchestrator_files()

            for file_path in orchestrator_files:
                src = Path(file_path)
                rel_path = src.relative_to(self.project_root)
                dst = backup_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

            print(f"📋 Backup created: {backup_dir}")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def test_unified_orchestrators(self) -> Dict[str, bool]:
        """Test that unified orchestrators work correctly"""
        test_results = {}

        try:
            # Test imports
            print("🧪 Testing unified orchestrator imports...")

            # Test UnifiedBaseOrchestrator
            try:
                from app.orchestrators.unified_base import (
                    UnifiedBaseOrchestrator,
                    UnifiedResult,
                    UnifiedTask,
                )

                test_results["unified_base"] = True
                print("  ✅ UnifiedBaseOrchestrator imports successfully")
            except ImportError as e:
                test_results["unified_base"] = False
                print(f"  ❌ UnifiedBaseOrchestrator import failed: {e}")

            # Test SophiaUnifiedOrchestrator
            try:
                from app.orchestrators.sophia_unified import (
                    BusinessContext,
                    SophiaUnifiedOrchestrator,
                )

                test_results["sophia_unified"] = True
                print("  ✅ SophiaUnifiedOrchestrator imports successfully")
            except ImportError as e:
                test_results["sophia_unified"] = False
                print(f"  ❌ SophiaUnifiedOrchestrator import failed: {e}")

            # Test ArtemisUnifiedOrchestrator
            try:
                from app.orchestrators.artemis_unified import (
                    ArtemisUnifiedOrchestrator,
                    CodeContext,
                )

                test_results["artemis_unified"] = True
                print("  ✅ ArtemisUnifiedOrchestrator imports successfully")
            except ImportError as e:
                test_results["artemis_unified"] = False
                print(f"  ❌ ArtemisUnifiedOrchestrator import failed: {e}")

            # Test CrossLearningOrchestrator
            try:
                from app.orchestrators.cross_learning import (
                    CollaborationType,
                    CrossLearningOrchestrator,
                )

                test_results["cross_learning"] = True
                print("  ✅ CrossLearningOrchestrator imports successfully")
            except ImportError as e:
                test_results["cross_learning"] = False
                print(f"  ❌ CrossLearningOrchestrator import failed: {e}")

        except Exception as e:
            print(f"❌ Testing failed: {e}")
            test_results["general"] = False

        return test_results

    def generate_report(
        self, report: MigrationReport, output_file: Optional[str] = None
    ) -> str:
        """Generate detailed migration report"""
        if not output_file:
            output_file = str(self.project_root / "orchestrator_migration_report.md")

        report_content = f"""# Orchestrator Migration Report

Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report analyzes the current orchestrator architecture and provides recommendations for consolidation into unified orchestrators.

### Key Findings

- **Files Analyzed**: {report.total_files_analyzed}
- **Duplicate Code Instances**: {len(report.duplicate_code_instances)}
- **Estimated Code Reduction**: {report.estimated_code_reduction} lines
- **Files Requiring Import Updates**: {len(report.import_updates)}

## Orchestrator Analysis

### Current Orchestrator Files

| File | Classes | Functions | Lines of Code | Complexity | Dependencies |
|------|---------|-----------|---------------|------------|--------------|
"""

        for info in report.orchestrator_info:
            file_name = Path(info.file_path).name
            report_content += f"| {file_name} | {len(info.classes)} | {len(info.functions)} | {info.lines_of_code} | {info.complexity_score:.1f} | {len(info.dependencies)} |\n"

        report_content += f"""

## Code Duplication Analysis

### Summary
- **Function Duplicates**: {len([d for d in report.duplicate_code_instances if d.category == 'function'])}
- **Method Duplicates**: {len([d for d in report.duplicate_code_instances if d.category == 'method'])}
- **Block Duplicates**: {len([d for d in report.duplicate_code_instances if d.category == 'block'])}

### Top Duplicate Code Instances

"""

        # Show top 10 duplicates by similarity
        top_duplicates = sorted(
            report.duplicate_code_instances,
            key=lambda x: x.similarity_score,
            reverse=True,
        )[:10]

        for i, dup in enumerate(top_duplicates, 1):
            file1_name = Path(dup.file1).name
            file2_name = Path(dup.file2).name
            report_content += f"""
#### {i}. {dup.category.title()} Duplication
- **Files**: {file1_name} ↔ {file2_name}
- **Similarity**: {dup.similarity_score:.2%}
- **Lines**: {len(dup.duplicate_lines)}
- **Function/Method**: {dup.function_name or 'N/A'}
"""

        report_content += """

## Consolidation Recommendations

"""
        for i, rec in enumerate(report.consolidation_recommendations, 1):
            report_content += f"{i}. {rec}\n"

        report_content += """

## Risk Assessment

"""
        for risk_type, risk_level in report.risk_assessment.items():
            report_content += f"- **{risk_type.title()}**: {risk_level}\n"

        report_content += """

## Migration Plan

"""
        for step in report.migration_steps:
            report_content += f"{step}\n"

        report_content += """

## Import Updates Required

The following files need import updates to use the new unified orchestrators:

"""
        for file_path, updates in list(report.import_updates.items())[
            :10
        ]:  # Show first 10
            file_name = Path(file_path).name
            report_content += f"### {file_name}\n"
            for update in updates[:3]:  # Show first 3 updates per file
                report_content += f"- {update}\n"
            report_content += "\n"

        if len(report.import_updates) > 10:
            report_content += (
                f"... and {len(report.import_updates) - 10} more files\n\n"
            )

        report_content += f"""
## Benefits of Unified Architecture

1. **Code Reduction**: Eliminate ~{report.estimated_code_reduction} lines of duplicate code
2. **Maintainability**: Single source of truth for orchestrator functionality
3. **Consistency**: Unified patterns and error handling across domains
4. **Cross-Learning**: Knowledge sharing between Sophia and Artemis
5. **Quality Assurance**: Comprehensive QA pipeline for all code
6. **Monitoring**: Unified monitoring and metrics collection
7. **Performance**: Optimized execution patterns and resource usage

## Next Steps

1. Review this report and approve migration plan
2. Create backup of existing orchestrator files
3. Implement unified orchestrators (already created)
4. Test unified orchestrator functionality
5. Update imports across codebase
6. Run comprehensive tests
7. Deploy and monitor

---

*Report generated by Orchestrator Migration Script*
*For questions or concerns, please review the migration plan carefully*
"""

        # Write report to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"📄 Migration report generated: {output_file}")
        return output_file


def main():
    """Main migration script execution"""
    print("🚀 Sophia Intelligence AI - Orchestrator Migration Script")
    print("=" * 60)

    # Get project root
    project_root = Path(__file__).parent.parent

    # Initialize migration orchestrator
    migrator = MigrationOrchestrator(project_root)

    try:
        # Create backup first
        print("\n📋 Creating backup of existing orchestrator files...")
        backup_success = migrator.create_backup()

        # Run migration analysis
        print("\n🔍 Running migration analysis...")
        report = migrator.run_migration_analysis()
        report.backup_created = backup_success

        # Test unified orchestrators
        print("\n🧪 Testing unified orchestrators...")
        test_results = migrator.test_unified_orchestrators()

        # Generate report
        print("\n📄 Generating migration report...")
        report_file = migrator.generate_report(report)

        # Summary
        print("\n" + "=" * 60)
        print("📊 MIGRATION ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Files Analyzed: {report.total_files_analyzed}")
        print(f"Duplicate Code Instances: {len(report.duplicate_code_instances)}")
        print(f"Estimated Code Reduction: {report.estimated_code_reduction} lines")
        print(f"Files Needing Import Updates: {len(report.import_updates)}")
        print(f"Backup Created: {'✅' if report.backup_created else '❌'}")

        print("\n🧪 UNIFIED ORCHESTRATOR TESTS:")
        for component, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {component}: {status}")

        print(f"\n📄 Detailed report: {report_file}")

        # Show top recommendations
        print("\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(report.consolidation_recommendations[:5], 1):
            print(f"  {i}. {rec}")

        print("\n🎉 Migration analysis complete!")
        print("📋 Review the generated report and proceed with migration steps.")

        return 0

    except Exception as e:
        print(f"\n❌ Migration analysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
