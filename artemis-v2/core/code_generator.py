"""
Code Generator Module
=====================

Handles all code generation tasks including feature implementation,
refactoring, and optimization.
"""

import ast
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CodeTaskType(Enum):
    """Types of code generation tasks"""

    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"


@dataclass
class CodeRequest:
    """Request model for code generation"""

    task_type: CodeTaskType
    language: str
    framework: Optional[str] = None
    requirements: List[str] = None
    constraints: List[str] = None
    context: Dict[str, Any] = None
    target_file: Optional[str] = None


@dataclass
class CodeResponse:
    """Response model for generated code"""

    code: str
    language: str
    file_path: Optional[str] = None
    dependencies: List[str] = None
    tests_included: bool = False
    documentation: Optional[str] = None
    confidence_score: float = 0.0


class CodeGenerator:
    """
    Main code generation engine for Artemis.
    Handles code creation, modification, and optimization.
    """

    def __init__(self, llm_client=None):
        """Initialize the code generator with optional LLM client"""
        self.llm_client = llm_client
        self.templates = self._load_templates()
        self.validators = {}
        self.parsers = {}

    def _load_templates(self) -> Dict[str, str]:
        """Load code templates for different languages and patterns"""
        templates = {
            "python_class": """class {class_name}:
    \"\"\"
    {description}
    \"\"\"

    def __init__(self{params}):
        {init_body}

    {methods}
""",
            "python_function": """def {function_name}({params}) -> {return_type}:
    \"\"\"
    {description}

    Args:
        {args_description}

    Returns:
        {return_description}
    \"\"\"
    {body}
""",
            "javascript_function": """/**
 * {description}
 * @param {params_jsdoc}
 * @returns {return_jsdoc}
 */
function {function_name}({params}) {{
    {body}
}}
""",
            "typescript_interface": """export interface {interface_name} {{
    {properties}
}}
""",
            "react_component": """import React from 'react';
{imports}

interface {component_name}Props {{
    {props}
}}

export const {component_name}: React.FC<{component_name}Props> = ({{ {props_destructured} }}) => {{
    {hooks}

    return (
        {jsx}
    );
}};
""",
        }
        return templates

    def generate(self, request: CodeRequest) -> CodeResponse:
        """
        Generate code based on the request.

        Args:
            request: Code generation request

        Returns:
            Generated code response
        """
        # Validate request
        if not self._validate_request(request):
            raise ValueError("Invalid code request")

        # Select generation strategy based on task type
        if request.task_type == CodeTaskType.FEATURE:
            return self._generate_feature(request)
        elif request.task_type == CodeTaskType.BUG_FIX:
            return self._generate_bug_fix(request)
        elif request.task_type == CodeTaskType.REFACTOR:
            return self._refactor_code(request)
        elif request.task_type == CodeTaskType.OPTIMIZATION:
            return self._optimize_code(request)
        else:
            return self._generate_documentation(request)

    def _validate_request(self, request: CodeRequest) -> bool:
        """Validate the code generation request"""
        if not request.language:
            return False
        if not request.requirements and request.task_type == CodeTaskType.FEATURE:
            return False
        return True

    def _generate_feature(self, request: CodeRequest) -> CodeResponse:
        """Generate code for a new feature"""
        # Build prompt for LLM
        prompt = self._build_feature_prompt(request)

        # Generate code using LLM or templates
        if self.llm_client:
            code = self._generate_with_llm(prompt, request.language)
        else:
            code = self._generate_with_templates(request)

        # Parse and validate generated code
        validated_code = self._validate_generated_code(code, request.language)

        # Generate tests if needed
        tests = None
        if request.context and request.context.get("include_tests", False):
            tests = self._generate_tests(validated_code, request)

        return CodeResponse(
            code=validated_code,
            language=request.language,
            file_path=request.target_file,
            dependencies=self._extract_dependencies(validated_code, request.language),
            tests_included=tests is not None,
            documentation=self._generate_docs(validated_code, request),
            confidence_score=self._calculate_confidence(validated_code, request),
        )

    def _generate_bug_fix(self, request: CodeRequest) -> CodeResponse:
        """Generate code to fix a bug"""
        # Analyze the bug context
        bug_analysis = self._analyze_bug(request)

        # Generate fix
        fix_code = self._create_fix(bug_analysis, request)

        return CodeResponse(
            code=fix_code,
            language=request.language,
            file_path=request.target_file,
            confidence_score=0.85,
        )

    def _refactor_code(self, request: CodeRequest) -> CodeResponse:
        """Refactor existing code"""
        original_code = request.context.get("original_code", "")

        # Analyze code for refactoring opportunities
        refactor_suggestions = self._analyze_for_refactoring(original_code, request.language)

        # Apply refactoring
        refactored_code = self._apply_refactoring(original_code, refactor_suggestions)

        return CodeResponse(
            code=refactored_code,
            language=request.language,
            file_path=request.target_file,
            documentation=f"Refactored: {', '.join(refactor_suggestions)}",
            confidence_score=0.9,
        )

    def _optimize_code(self, request: CodeRequest) -> CodeResponse:
        """Optimize code for performance"""
        original_code = request.context.get("original_code", "")

        # Analyze performance bottlenecks
        bottlenecks = self._analyze_performance(original_code, request.language)

        # Apply optimizations
        optimized_code = self._apply_optimizations(original_code, bottlenecks)

        return CodeResponse(
            code=optimized_code,
            language=request.language,
            file_path=request.target_file,
            documentation=f"Optimized: {', '.join(bottlenecks)}",
            confidence_score=0.85,
        )

    def _generate_documentation(self, request: CodeRequest) -> CodeResponse:
        """Generate documentation for code"""
        code = request.context.get("code", "")

        # Parse code structure
        structure = self._parse_code_structure(code, request.language)

        # Generate documentation
        docs = self._create_documentation(structure, request.language)

        return CodeResponse(
            code=docs,
            language="markdown",
            documentation="Generated documentation",
            confidence_score=0.95,
        )

    def _build_feature_prompt(self, request: CodeRequest) -> str:
        """Build prompt for feature generation"""
        prompt = f"""Generate {request.language} code for the following feature:

Requirements:
{chr(10).join(f'- {req}' for req in request.requirements or [])}

Constraints:
{chr(10).join(f'- {constraint}' for constraint in request.constraints or [])}

Framework: {request.framework or 'None'}
"""
        return prompt

    def _generate_with_llm(self, prompt: str, language: str) -> str:
        """Generate code using LLM"""
        # This would call the actual LLM
        # For now, return a placeholder
        return f"# Generated {language} code\n# TODO: Implement LLM integration"

    def _generate_with_templates(self, request: CodeRequest) -> str:
        """Generate code using templates"""
        template_key = f"{request.language}_{request.context.get('template_type', 'function')}"
        template = self.templates.get(template_key, "# No template available")

        # Fill in template with request data
        return template.format(**request.context or {})

    def _validate_generated_code(self, code: str, language: str) -> str:
        """Validate generated code for syntax and best practices"""
        if language == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                # Fix syntax errors if possible
                code = self._fix_syntax_errors(code, str(e))

        return code

    def _generate_tests(self, code: str, request: CodeRequest) -> str:
        """Generate tests for the code"""
        test_template = """import pytest

def test_{function_name}():
    # Test implementation
    assert True
"""
        return test_template

    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []

        if language == "python":
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        dependencies.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    dependencies.append(node.module)

        return list(set(dependencies))

    def _generate_docs(self, code: str, request: CodeRequest) -> str:
        """Generate documentation for code"""
        return f"Documentation for {request.task_type.value} in {request.language}"

    def _calculate_confidence(self, code: str, request: CodeRequest) -> float:
        """Calculate confidence score for generated code"""
        score = 0.7  # Base score

        # Adjust based on validation results
        if self._validate_generated_code(code, request.language):
            score += 0.1

        # Adjust based on complexity
        if len(request.requirements or []) < 3:
            score += 0.1

        return min(score, 1.0)

    def _analyze_bug(self, request: CodeRequest) -> Dict[str, Any]:
        """Analyze bug context"""
        return {"type": "syntax", "severity": "medium", "location": request.target_file}

    def _create_fix(self, analysis: Dict, request: CodeRequest) -> str:
        """Create bug fix code"""
        return f"# Bug fix for {analysis['type']} issue"

    def _analyze_for_refactoring(self, code: str, language: str) -> List[str]:
        """Analyze code for refactoring opportunities"""
        suggestions = []

        if language == "python":
            # Check for long functions
            if len(code.split("\n")) > 50:
                suggestions.append("Split long function")

            # Check for duplicate code
            if "# TODO" in code:
                suggestions.append("Address TODO comments")

        return suggestions

    def _apply_refactoring(self, code: str, suggestions: List[str]) -> str:
        """Apply refactoring suggestions"""
        # This would apply actual refactoring
        return f"# Refactored code\n{code}"

    def _analyze_performance(self, code: str, language: str) -> List[str]:
        """Analyze code for performance issues"""
        bottlenecks = []

        if language == "python":
            if "for" in code and "append" in code:
                bottlenecks.append("Use list comprehension")
            if "+" in code and "str" in code:
                bottlenecks.append("Use string formatting")

        return bottlenecks

    def _apply_optimizations(self, code: str, bottlenecks: List[str]) -> str:
        """Apply performance optimizations"""
        # This would apply actual optimizations
        return f"# Optimized code\n{code}"

    def _parse_code_structure(self, code: str, language: str) -> Dict:
        """Parse code structure for documentation"""
        structure = {"functions": [], "classes": [], "variables": []}

        if language == "python":
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    structure["classes"].append(node.name)

        return structure

    def _create_documentation(self, structure: Dict, language: str) -> str:
        """Create documentation from code structure"""
        docs = "# Documentation\n\n"

        if structure["classes"]:
            docs += "## Classes\n"
            for cls in structure["classes"]:
                docs += f"- {cls}\n"

        if structure["functions"]:
            docs += "\n## Functions\n"
            for func in structure["functions"]:
                docs += f"- {func}\n"

        return docs

    def _fix_syntax_errors(self, code: str, error: str) -> str:
        """Attempt to fix syntax errors in code"""
        # Basic syntax fix attempts
        if "unexpected indent" in error:
            # Fix indentation
            lines = code.split("\n")
            fixed_lines = [line.lstrip() for line in lines]
            return "\n".join(fixed_lines)

        return code
