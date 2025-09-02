import ast
import logging
import os
from typing import Any

import numpy as np
import radon.complexity as radon_cc
import radon.metrics as radon_mi

from app.observability.prometheus_metrics import (
    code_complexity_metrics,
    code_quality_metrics,
    code_smells_detected,
)

logger = logging.getLogger(__name__)

class CodeQualityAnalyzer:
    """Comprehensive code quality analysis and improvement suggestion system"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.quality_metrics = {
            "average_complexity": 0.0,
            "average_maintainability": 0.0,
            "code_smells": [],
            "recalculated_metrics": {}
        }

    def analyze_complexity(self, file_path: str) -> dict[str, Any]:
        """Analyze cyclomatic complexity of a file"""
        try:
            with open(file_path) as f:
                module = ast.parse(f.read())

            # Get all functions/classes for complexity analysis
            functions = [node for node in ast.walk(module) if isinstance(node, ast.FunctionDef)]

            # Calculate complexity for each function
            complexity_scores = []
            for func in functions:
                func_ast = ast.get_source_segment(open(file_path).read(), func)
                complexity = radon_cc.cc_visit(func_ast)
                complexity_scores.append(complexity)

            # Calculate overall complexity
            if complexity_scores:
                complexity_avg = np.mean(complexity_scores)
                self.quality_metrics["average_complexity"] = complexity_avg
                code_complexity_metrics.observe(complexity_avg)

                # Categorize complexity level
                complexity_level = self._categorize_complexity(complexity_avg)
                logger.info(f"File {file_path} complexity: {complexity_avg:.2f} ({complexity_level})")

                return {
                    "file": file_path,
                    "average_complexity": complexity_avg,
                    "complexity_level": complexity_level,
                    "functions": [{
                        "name": func.name,
                        "complexity": self._get_function_complexity(func),
                        "type": "function" if isinstance(func, ast.FunctionDef) else "class"
                    } for func in functions]
                }
            return {}
        except Exception as e:
            logger.error(f"Complexity analysis failed for {file_path}: {str(e)}")
            return {"error": str(e)}

    def analyze_maintainability(self, file_path: str) -> dict[str, Any]:
        """Analyze maintainability index of a file"""
        try:
            with open(file_path) as f:
                source = f.read()

            # Calculate maintainability
            mi = radon_mi.mi_visit(source)

            # Calculate maintainability index with own calculations
            maintainability = 100 - 10 * mi

            self.quality_metrics["average_maintainability"] = maintainability
            code_quality_metrics.observe(maintainability)

            # Categorize maintainability
            mi_level = self._categorize_maintainability(maintainability)
            logger.info(f"File {file_path} maintainability: {maintainability:.2f} ({mi_level})")

            return {
                "file": file_path,
                "maintainability": maintainability,
                "maintainability_level": mi_level,
                "complexity": "similar to complexity analysis"
            }
        except Exception as e:
            logger.error(f"Maintainability analysis failed for {file_path}: {str(e)}")
            return {"error": str(e)}

    def find_code_smells(self, file_path: str) -> list[dict[str, Any]]:
        """Identify potential code smells using heuristics"""
        smells = []

        try:
            with open(file_path) as f:
                lines = f.readlines()

            # Look for common code smells
            for i, line in enumerate(lines):
                # Long method smell
                if len(line.strip()) > 120 and not line.strip().startswith("#"):
                    smells.append({
                        "smell_type": "LongMethod",
                        "line_number": i + 1,
                        "description": "Method exceeds recommended line length (120 characters)"
                    })

                # Duplicate code smell
                if "COPYPASTE" in line or "DUPLICATE" in line:
                    smells.append({
                        "smell_type": "DuplicateCode",
                        "line_number": i + 1,
                        "description": "Potential duplicate code section"
                    })

                # Magic number smell
                if re.search(r'\b\d+\b', line) and not re.search(r'\b((2|3|4|5)\d)\b', line):
                    smells.append({
                        "smell_type": "MagicNumber",
                        "line_number": i + 1,
                        "description": "Unexplained numeric literal"
                    })

            self.quality_metrics["code_smells"] = smells
            code_smells_detected.set(len(smells))

            return smells
        except Exception as e:
            logger.error(f"Code smell detection failed for {file_path}: {str(e)}")
            return []

    def identify_complex_files(self, threshold: int = 10) -> list[dict[str, Any]]:
        """Identify files with complex code based on threshold"""
        complex_files = []

        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        complexity = self.analyze_complexity(file_path)
                        if complexity.get('average_complexity', 0) > threshold:
                            complex_files.append({
                                "file": file_path,
                                "complexity": complexity['average_complexity'],
                                "level": complexity['complexity_level']
                            })
                    except Exception as e:
                        logger.error(f"Failed to analyze {file_path}: {str(e)}")

        return complex_files

    def _categorize_complexity(self, complexity: float) -> str:
        """Categorize complexity level based on common standards"""
        if complexity < 5:
            return "Low"
        elif 5 <= complexity < 10:
            return "Medium"
        elif 10 <= complexity < 15:
            return "High"
        else:
            return "Critical"

    def _categorize_maintainability(self, maintainability: float) -> str:
        """Categorize maintainability index"""
        if maintainability >= 80:
            return "Excellent"
        elif 70 <= maintainability < 80:
            return "Good"
        elif 60 <= maintainability < 70:
            return "Fair"
        elif 50 <= maintainability < 60:
            return "Poor"
        else:
            return "Critical"

    def _get_function_complexity(self, func: ast.AST) -> tuple[str, list[str]]:
        """Get complexity details for a function"""
        complexity = radon_cc.cc_visit(ast.unparse(func))
        return complexity, [f"Complexity: {complexity}"]

    def suggest_improvements(self, analysis_result: dict[str, Any]) -> list[str]:
        """Generate specific improvement suggestions"""
        suggestions = []

        # Suggest breaking up complex functions
        if analysis_result.get('average_complexity', 0) > 10:
            suggestions.append(
                "Break down complex functions into smaller, focused methods to reduce cognitive load."
            )
            suggestions.append(
                "Refactor to implement the Single Responsibility Principle for better maintainability."
            )

        # Suggest improving maintainability
        if analysis_result.get('maintainability', 0) < 70:
            suggestions.append(
                "Add documentation and type hints to improve code readability."
            )
            suggestions.append(
                "Consider refactoring decision structures to improve maintainability."
            )

        # Suggest code smell fixes
        if analysis_result.get('code_smells', []):
            suggestions.append(
                "Address code smells: potential duplicate code, magic numbers, and long methods."
            )

        return suggestions

# Example usage
if __name__ == "__main__":
    analyzer = CodeQualityAnalyzer(project_root="app")

    # Analyze a specific file
    file_analysis = analyzer.analyze_complexity("app/api/unified_gateway.py")
    print("File Complexity Analysis:", file_analysis)

    # Analyze code smells
    smells = analyzer.find_code_smells("app/api/unified_gateway.py")
    print("Code Smells Found:", smells)

    # Generate improvement suggestions
    print("Improvement Suggestions:", analyzer.suggest_improvements(file_analysis))

    # Identify complex files
    complex_files = analyzer.identify_complex_files(threshold=8)
    print("Complex Files:", complex_files)
