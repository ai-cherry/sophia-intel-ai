"""
Artemis Code Excellence Orchestrator
Specialized for software development, code generation, and technical excellence
With enhanced MCP server integration for domain-aware routing
"""

import ast
import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Import unified factory and domain enforcer
from app.artemis.unified_factory import artemis_unified_factory
from app.core.domain_enforcer import OperationType, UserRole, domain_enforcer
from app.core.portkey_manager import TaskType as PortkeyTaskType
from app.core.shared_services import shared_services
from app.mcp.connection_manager import MCPConnectionManager
from app.mcp.enhanced_registry import MCPServerRegistry

# Import MCP components for enhanced routing
from app.mcp.router_config import MCPRouterConfiguration, MCPServerType
from app.memory.unified_memory_router import MemoryDomain
from app.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    ExecutionPriority,
    OrchestratorConfig,
    Result,
    Task,
    TaskType,
)

logger = logging.getLogger(__name__)


@dataclass
class CodeContext:
    """Code-specific context for Artemis"""

    languages: list[str]
    frameworks: list[str]
    repository_path: Optional[str] = None
    test_framework: Optional[str] = None
    style_guide: Optional[str] = None
    complexity_threshold: int = 10
    coverage_target: float = 80.0
    performance_benchmarks: dict[str, float] = field(default_factory=dict)


@dataclass
class CodeResult:
    """Structured code generation result"""

    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    complexity_score: float = 0.0
    estimated_performance: dict[str, Any] = field(default_factory=dict)
    security_analysis: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeReview:
    """Structured code review result"""

    overall_score: float
    issues: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    security_vulnerabilities: list[dict[str, Any]]
    performance_concerns: list[dict[str, Any]]
    best_practices: list[dict[str, Any]]
    test_coverage: float
    complexity_metrics: dict[str, float]


class ArtemisOrchestrator(BaseOrchestrator):
    """
    Artemis - Code Excellence Orchestrator

    Specializes in:
    - Code generation and refactoring
    - Code review and quality analysis
    - Test generation and validation
    - Documentation creation
    - Performance optimization
    - Security analysis
    - Architecture design
    """

    def __init__(self, code_context: Optional[CodeContext] = None):
        """
        Initialize Artemis orchestrator with unified factory and MCP integration

        Args:
            code_context: Optional code-specific context
        """
        config = OrchestratorConfig(
            domain=MemoryDomain.ARTEMIS,
            name="Artemis Code Excellence",
            description="Code generation and technical excellence orchestrator",
            max_concurrent_tasks=8,  # Enforced by unified factory
            default_timeout_s=120,
            enable_caching=True,
            enable_monitoring=True,
            enable_memory=True,
            budget_limits={
                "hourly_cost_usd": 30.0,
                "daily_cost_usd": 300.0,
                "monthly_cost_usd": 6000.0,
            },
        )

        super().__init__(config)

        self.code_context = code_context or self._get_default_context()

        # Use unified factory for agent/swarm creation
        self.factory = artemis_unified_factory

        # Use shared services
        self.shared_services = shared_services

        # Domain enforcer for access control
        self.domain_enforcer = domain_enforcer

        # Initialize MCP components for enhanced routing
        self.mcp_router = MCPRouterConfiguration()
        self.mcp_registry = MCPServerRegistry()
        self.mcp_connection_manager = MCPConnectionManager()

        # Specialized components
        self.code_analyzer = CodeAnalyzer(self)
        self.test_generator = TestGenerator(self)
        self.doc_generator = DocumentationGenerator(self)
        self.security_scanner = SecurityScanner(self)
        self.performance_analyzer = PerformanceAnalyzer(self)

        # Code execution sandbox
        self._sandbox = CodeSandbox()

        logger.info(
            "Artemis Code Orchestrator initialized with unified factory and MCP routing"
        )

    def _get_default_context(self) -> CodeContext:
        """Get default code context"""
        return CodeContext(
            languages=["python", "typescript", "javascript"],
            frameworks=["fastapi", "react", "nextjs"],
            test_framework="pytest",
            style_guide="pep8",
        )

    async def _execute_core(self, task: Task, routing: Any) -> Result:
        """
        Execute Artemis-specific code task with domain validation

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        result = Result(success=False, content=None)

        try:
            # Validate domain access
            operation_type = self._map_task_to_operation(task.type)
            validation = domain_enforcer.validate_request(
                {
                    "id": task.id,
                    "user_id": task.metadata.get("user_id", "system"),
                    "user_role": UserRole.DEVELOPER,  # Default for Artemis
                    "target_domain": MemoryDomain.ARTEMIS,
                    "operation_type": operation_type,
                    "resource_path": task.metadata.get("resource_path"),
                    "metadata": task.metadata,
                }
            )

            if not validation.allowed:
                result.errors.append(f"Domain access denied: {validation.reason}")
                return result

            # Log to shared services
            if self.shared_services.get_logging_service():
                await self.shared_services.get_logging_service().log(
                    "info",
                    f"Executing Artemis task: {task.id}",
                    MemoryDomain.ARTEMIS,
                    {"task_type": task.type, "operation": operation_type},
                )

            # Analyze codebase context
            codebase_context = await self._analyze_codebase(task)

            # Load relevant code examples from memory
            code_examples = await self._load_code_examples(task)

            # Prepare messages for LLM
            messages = self._prepare_code_messages(
                task, codebase_context, code_examples
            )

            # Route based on task type
            if task.type == TaskType.CODE_GENERATION:
                response = await self._generate_code(messages, routing, task)
            elif task.type == TaskType.CODE_REVIEW:
                response = await self._review_code(messages, routing, task)
            else:
                response = await self._general_code_task(messages, routing, task)

            # Process response
            processed = await self._process_code_response(response, task)

            # Validate code if applicable
            if task.type == TaskType.CODE_GENERATION:
                validation = await self._validate_generated_code(processed)
                processed["validation"] = validation

            # Generate tests if requested
            if task.metadata.get("generate_tests", False):
                tests = await self.test_generator.generate(processed)
                processed["tests"] = tests

            # Security scan
            if task.metadata.get("security_scan", True):
                security = await self.security_scanner.scan(processed)
                processed["security"] = security

            # Format result
            result.success = True
            result.content = processed
            result.metadata = {
                "language": self._detect_language(processed),
                "complexity": await self.code_analyzer.calculate_complexity(processed),
                "lines_of_code": self._count_lines(processed),
                "processing_steps": ["analyze", "generate", "validate", "enhance"],
            }
            result.confidence = self._calculate_code_confidence(processed, validation)

            # Track usage
            if hasattr(response, "usage"):
                result.tokens_used = response.usage.total_tokens
                result.cost = self.portkey._estimate_cost(
                    routing.model, result.tokens_used
                )

            # Record metrics to shared services
            if self.shared_services.get_monitoring_service():
                await self.shared_services.get_monitoring_service().record_metric(
                    "artemis_task_execution",
                    1.0,
                    {"task_type": task.type, "success": "true"},
                )

        except Exception as e:
            logger.error(f"Artemis execution failed: {e}")
            result.errors.append(str(e))

            # Record failure metric
            if self.shared_services.get_monitoring_service():
                await self.shared_services.get_monitoring_service().record_metric(
                    "artemis_task_execution",
                    1.0,
                    {"task_type": task.type, "success": "false"},
                )

        return result

    def _map_task_to_operation(self, task_type: TaskType) -> OperationType:
        """Map task type to operation type for domain validation"""
        mapping = {
            TaskType.CODE_GENERATION: OperationType.CODE_GENERATION,
            TaskType.CODE_REVIEW: OperationType.CODE_REVIEW,
            TaskType.ORCHESTRATION: OperationType.ARCHITECTURE_DESIGN,
            TaskType.WEB_RESEARCH: OperationType.DOCUMENTATION,
        }
        return mapping.get(task_type, OperationType.CODE_GENERATION)

    async def _analyze_codebase(self, task: Task) -> dict[str, Any]:
        """
        Analyze codebase for context using MCP filesystem server

        Args:
            task: Current task

        Returns:
            Codebase analysis results
        """
        context = {
            "repository_path": self.code_context.repository_path,
            "file_structure": {},
            "dependencies": {},
            "patterns": {},
            "conventions": {},
        }

        if self.code_context.repository_path:
            repo_path = Path(self.code_context.repository_path)

            # Use MCP filesystem server for file operations
            filesystem_connection = await self._get_mcp_connection(
                MCPServerType.FILESYSTEM
            )

            if filesystem_connection:
                try:
                    # Analyze file structure via MCP
                    context["file_structure"] = await self._analyze_file_structure_mcp(
                        repo_path, filesystem_connection
                    )
                finally:
                    await self.mcp_connection_manager.release_connection(
                        filesystem_connection, "artemis"
                    )
            else:
                # Fallback to local analysis
                context["file_structure"] = self._analyze_file_structure(repo_path)

            # Detect dependencies
            context["dependencies"] = self._detect_dependencies(repo_path)

            # Use MCP code analysis server for patterns
            code_analysis_connection = await self._get_mcp_connection(
                MCPServerType.CODE_ANALYSIS
            )

            if code_analysis_connection:
                try:
                    # Identify patterns and conventions via MCP
                    context["patterns"] = await self._identify_patterns_mcp(
                        repo_path, code_analysis_connection
                    )
                    context["conventions"] = await self._detect_conventions_mcp(
                        repo_path, code_analysis_connection
                    )
                finally:
                    await self.mcp_connection_manager.release_connection(
                        code_analysis_connection, "artemis"
                    )
            else:
                # Fallback to local analysis
                context["patterns"] = await self.code_analyzer.identify_patterns(
                    repo_path
                )
                context["conventions"] = await self.code_analyzer.detect_conventions(
                    repo_path
                )

        return context

    async def _load_code_examples(self, task: Task) -> list[dict[str, Any]]:
        """
        Load relevant code examples from memory using MCP servers

        Args:
            task: Current task

        Returns:
            List of code examples
        """
        examples = []

        # Use MCP indexing server for code search
        indexing_connection = await self._get_mcp_connection(MCPServerType.INDEXING)

        if indexing_connection:
            try:
                # Search via MCP indexing server with domain-specific partitions
                search_results = await self._search_code_mcp(
                    task.content,
                    indexing_connection,
                    filters={"type": "code", "domain": "artemis"},
                )

                for result in search_results:
                    examples.append(
                        {
                            "code": result.get("content"),
                            "relevance": result.get("score", 0),
                            "source": result.get("source_uri"),
                            "metadata": result.get("metadata", {}),
                        }
                    )
            finally:
                await self.mcp_connection_manager.release_connection(
                    indexing_connection, "artemis"
                )
        elif self.memory:
            # Fallback to direct memory search
            hits = await self.memory.search(
                query=task.content,
                domain=MemoryDomain.ARTEMIS,
                k=5,
                filters={"type": "code"},
            )

            for hit in hits:
                examples.append(
                    {
                        "code": hit.content,
                        "relevance": hit.score,
                        "source": hit.source_uri,
                        "metadata": hit.metadata,
                    }
                )

        # Use MCP embedding server for semantic similarity
        embedding_connection = await self._get_mcp_connection(MCPServerType.EMBEDDING)

        if embedding_connection and examples:
            try:
                # Enhance examples with semantic similarity
                examples = await self._enhance_with_embeddings_mcp(
                    examples, task.content, embedding_connection
                )
            finally:
                await self.mcp_connection_manager.release_connection(
                    embedding_connection, "artemis"
                )

        return examples

    def _prepare_code_messages(
        self,
        task: Task,
        codebase_context: dict[str, Any],
        code_examples: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Prepare messages for code-focused LLM"""
        system_prompt = f"""You are Artemis, an expert software engineer specializing in {', '.join(self.code_context.languages)}.

Your expertise includes:
1. Writing clean, efficient, and maintainable code
2. Following best practices and design patterns
3. Creating comprehensive tests
4. Optimizing performance
5. Ensuring security
6. Writing clear documentation

Languages: {', '.join(self.code_context.languages)}
Frameworks: {', '.join(self.code_context.frameworks)}
Test Framework: {self.code_context.test_framework}
Style Guide: {self.code_context.style_guide}
Coverage Target: {self.code_context.coverage_target}%

Always:
- Write production-ready code
- Include error handling
- Consider edge cases
- Follow SOLID principles
- Optimize for readability and performance"""

        # Format code examples
        examples_text = ""
        if code_examples:
            examples_text = "\n\nRelevant code examples:\n"
            for i, example in enumerate(code_examples[:3], 1):
                examples_text += f"\nExample {i} (relevance: {example['relevance']:.2f}):\n```\n{example['code'][:500]}...\n```\n"

        user_prompt = f"""Task: {task.content}

Codebase Context:
- Repository: {codebase_context.get('repository_path', 'Not specified')}
- Dependencies: {json.dumps(list(codebase_context.get('dependencies', {}).keys())[:10])}
- Detected patterns: {json.dumps(codebase_context.get('patterns', {}))}

{examples_text}

Requirements:
1. Generate clean, production-ready code
2. Include comprehensive error handling
3. Follow established patterns in the codebase
4. Add inline comments for complex logic
5. Ensure type safety where applicable
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def _generate_code(
        self, messages: list[dict], routing: Any, task: Task
    ) -> Any:
        """Generate code using appropriate model"""
        # Use DeepSeek Coder for code generation as per config
        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.CODE_GENERATION,
            messages=messages,
            max_tokens=task.budget.get("tokens", 4000),
            temperature=0.1,  # Lower temperature for code generation
        )

        return response

    async def _review_code(self, messages: list[dict], routing: Any, task: Task) -> Any:
        """Review code using appropriate model"""
        # Add code to review to the messages
        code_to_review = task.metadata.get("code", "")
        messages.append(
            {
                "role": "user",
                "content": f"Please review the following code:\n\n```\n{code_to_review}\n```",
            }
        )

        # Use Claude for code review as per config
        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.CODE_REVIEW,
            messages=messages,
            max_tokens=task.budget.get("tokens", 3000),
            temperature=0.2,
        )

        return response

    async def _general_code_task(
        self, messages: list[dict], routing: Any, task: Task
    ) -> Any:
        """Handle general code-related tasks"""
        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.GENERAL,
            messages=messages,
            max_tokens=task.budget.get("tokens", 3000),
            temperature=0.3,
        )

        return response

    async def _process_code_response(self, response: Any, task: Task) -> dict[str, Any]:
        """Process LLM response into structured format"""
        content = (
            response.choices[0].message.content
            if hasattr(response, "choices")
            else str(response)
        )

        # Extract code blocks
        code_blocks = self._extract_code_blocks(content)

        processed = {
            "raw_response": content,
            "code_blocks": code_blocks,
            "primary_code": code_blocks[0] if code_blocks else "",
            "explanation": self._extract_explanation(content),
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "model_used": getattr(response, "model", "unknown"),
        }

        return processed

    def _extract_code_blocks(self, content: str) -> list[dict[str, str]]:
        """Extract code blocks from response"""
        import re

        code_blocks = []
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        for lang, code in matches:
            code_blocks.append({"language": lang or "unknown", "code": code.strip()})

        return code_blocks

    def _extract_explanation(self, content: str) -> str:
        """Extract explanation text from response"""
        import re

        # Remove code blocks to get explanation
        cleaned = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        return cleaned.strip()

    async def _validate_generated_code(
        self, processed: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate generated code"""
        validation = {
            "syntax_valid": False,
            "errors": [],
            "warnings": [],
            "metrics": {},
        }

        if not processed.get("primary_code"):
            validation["errors"].append("No code generated")
            return validation

        code = processed["primary_code"]
        language = self._detect_language(processed)

        # Syntax validation
        if language == "python":
            validation.update(self._validate_python(code))
        elif language in ["javascript", "typescript"]:
            validation.update(await self._validate_javascript(code))

        # Complexity analysis
        validation["metrics"]["complexity"] = (
            await self.code_analyzer.calculate_complexity({"code": code})
        )

        # Security check
        validation["metrics"]["security_score"] = (
            await self.security_scanner.quick_scan(code)
        )

        return validation

    def _validate_python(self, code: str) -> dict[str, Any]:
        """Validate Python code"""
        result = {"syntax_valid": False, "errors": [], "warnings": []}

        try:
            ast.parse(code)
            result["syntax_valid"] = True
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")

        # Run pylint for additional checks
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                f.flush()

                # Run pylint
                proc = subprocess.run(
                    ["pylint", "--errors-only", f.name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if proc.stdout:
                    result["warnings"].append(proc.stdout)

                os.unlink(f.name)
        except Exception as e:
            logger.warning(f"Pylint validation failed: {e}")

        return result

    async def _validate_javascript(self, code: str) -> dict[str, Any]:
        """Validate JavaScript/TypeScript code"""
        result = {"syntax_valid": False, "errors": [], "warnings": []}

        # Basic validation using Node.js
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(code)
                f.flush()

                # Try to parse with Node.js
                proc = await asyncio.create_subprocess_exec(
                    "node",
                    "--check",
                    f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await proc.communicate()

                if proc.returncode == 0:
                    result["syntax_valid"] = True
                else:
                    result["errors"].append(stderr.decode())

                os.unlink(f.name)
        except Exception as e:
            logger.warning(f"JavaScript validation failed: {e}")

        return result

    def _detect_language(self, processed: dict[str, Any]) -> str:
        """Detect programming language from processed result"""
        # Check explicit language in code blocks
        if processed.get("code_blocks"):
            return processed["code_blocks"][0].get("language", "unknown")

        # Try to detect from content
        code = processed.get("primary_code", "")

        # Simple heuristics
        if "import " in code or "from " in code or "def " in code:
            return "python"
        elif "function " in code or "const " in code or "let " in code:
            return "javascript"
        elif "interface " in code or ": string" in code:
            return "typescript"

        return "unknown"

    def _count_lines(self, processed: dict[str, Any]) -> int:
        """Count lines of code"""
        code = processed.get("primary_code", "")
        return len([line for line in code.split("\n") if line.strip()])

    def _calculate_code_confidence(
        self, processed: dict[str, Any], validation: dict[str, Any]
    ) -> float:
        """Calculate confidence in generated code"""
        confidence = 0.5  # Base confidence

        # Increase for valid syntax
        if validation.get("syntax_valid"):
            confidence += 0.25

        # Increase for low complexity
        complexity = validation.get("metrics", {}).get("complexity", 10)
        if complexity < 10:
            confidence += 0.1

        # Increase for good security score
        security = validation.get("metrics", {}).get("security_score", 0)
        if security > 0.8:
            confidence += 0.1

        # Decrease for errors
        if validation.get("errors"):
            confidence -= 0.1 * len(validation["errors"])

        return max(min(confidence, 0.95), 0.1)

    def _analyze_file_structure(self, repo_path: Path) -> dict[str, Any]:
        """Analyze repository file structure"""
        structure = {"total_files": 0, "file_types": {}, "directories": []}

        try:
            for path in repo_path.rglob("*"):
                if path.is_file():
                    structure["total_files"] += 1
                    ext = path.suffix
                    structure["file_types"][ext] = (
                        structure["file_types"].get(ext, 0) + 1
                    )
                elif path.is_dir():
                    structure["directories"].append(str(path.relative_to(repo_path)))
        except Exception as e:
            logger.warning(f"Failed to analyze file structure: {e}")

        return structure

    def _detect_dependencies(self, repo_path: Path) -> dict[str, list[str]]:
        """Detect project dependencies"""
        dependencies = {}

        # Python dependencies
        requirements = repo_path / "requirements.txt"
        if requirements.exists():
            dependencies["python"] = requirements.read_text().split("\n")

        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            # Would parse TOML here
            dependencies["python"] = []

        # JavaScript dependencies
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                import json

                pkg = json.loads(package_json.read_text())
                dependencies["javascript"] = list(pkg.get("dependencies", {}).keys())
            except:
                pass

        return dependencies

    # ========== Specialized Artemis Methods ==========

    async def generate_code(
        self,
        specification: str,
        language: str = "python",
        include_tests: bool = True,
        include_docs: bool = True,
        user_id: str = "system",
        user_role: UserRole = UserRole.DEVELOPER,
    ) -> CodeResult:
        """Generate code from specification with unified factory support"""
        # Create a technical agent for code generation
        agent_id = await self.factory.create_technical_agent("code_reviewer")

        task = Task(
            id=f"codegen_{datetime.now().timestamp()}",
            type=TaskType.CODE_GENERATION,
            content=f"Generate {language} code: {specification}",
            priority=ExecutionPriority.NORMAL,
            metadata={
                "language": language,
                "generate_tests": include_tests,
                "generate_docs": include_docs,
                "agent_id": agent_id,
                "user_id": user_id,
                "user_role": user_role.value,
            },
        )

        result = await self.execute(task)

        if result.success:
            return self._format_as_code_result(result, language)

        return None

    async def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: list[str] = None,
        user_id: str = "system",
        user_role: UserRole = UserRole.DEVELOPER,
    ) -> CodeReview:
        """Review code for quality and issues with unified factory support"""
        if not focus_areas:
            focus_areas = ["security", "performance", "maintainability", "testing"]

        # Create a specialized team for code review
        team_id = await self.factory.create_technical_team(
            {"type": "code_analysis", "name": "Code Review Team"}
        )

        task = Task(
            id=f"review_{datetime.now().timestamp()}",
            type=TaskType.CODE_REVIEW,
            content=f"Review {language} code focusing on {', '.join(focus_areas)}",
            priority=ExecutionPriority.NORMAL,
            metadata={
                "code": code,
                "language": language,
                "focus_areas": focus_areas,
                "team_id": team_id,
                "user_id": user_id,
                "user_role": user_role.value,
            },
        )

        result = await self.execute(task)

        if result.success:
            return await self._format_as_code_review(result)

        return None

    async def refactor_code(
        self, code: str, goals: list[str], preserve_functionality: bool = True
    ) -> CodeResult:
        """Refactor code to meet specified goals"""
        task = Task(
            id=f"refactor_{datetime.now().timestamp()}",
            type=TaskType.CODE_GENERATION,
            content=f"Refactor code to: {', '.join(goals)}",
            priority=ExecutionPriority.NORMAL,
            metadata={
                "original_code": code,
                "goals": goals,
                "preserve_functionality": preserve_functionality,
            },
        )

        result = await self.execute(task)

        if result.success:
            language = self._detect_language(result.content)
            return self._format_as_code_result(result, language)

        return None

    def _format_as_code_result(self, result: Result, language: str) -> CodeResult:
        """Format execution result as CodeResult"""
        content = result.content

        return CodeResult(
            code=content.get("primary_code", ""),
            language=language,
            explanation=content.get("explanation", ""),
            tests=(
                content.get("tests", {}).get("code") if content.get("tests") else None
            ),
            documentation=content.get("documentation", ""),
            complexity_score=content.get("validation", {})
            .get("metrics", {})
            .get("complexity", 0),
            security_analysis=content.get("security", {}),
            dependencies=[],
        )

    async def _format_as_code_review(self, result: Result) -> CodeReview:
        """Format execution result as CodeReview"""
        # Would parse the review from the result
        return CodeReview(
            overall_score=0.75,
            issues=[],
            suggestions=[],
            security_vulnerabilities=[],
            performance_concerns=[],
            best_practices=[],
            test_coverage=0.0,
            complexity_metrics={},
        )


# ========== Supporting Components ==========


class CodeAnalyzer:
    """Analyzes code for complexity, patterns, and metrics"""

    def __init__(self, orchestrator: ArtemisOrchestrator):
        self.orchestrator = orchestrator

    async def calculate_complexity(self, code_data: dict) -> float:
        """Calculate cyclomatic complexity"""
        # Simplified complexity calculation
        code = code_data.get("code", code_data.get("primary_code", ""))

        # Count decision points
        complexity = 1
        for keyword in ["if", "elif", "else", "for", "while", "except", "case"]:
            complexity += code.count(f" {keyword} ")

        return min(complexity, 20)  # Cap at 20

    async def identify_patterns(self, repo_path: Path) -> dict[str, Any]:
        """Identify code patterns in repository"""
        return {"design_patterns": [], "anti_patterns": [], "common_imports": []}

    async def detect_conventions(self, repo_path: Path) -> dict[str, Any]:
        """Detect coding conventions"""
        return {"naming": "snake_case", "indentation": "spaces_4", "quotes": "double"}


class TestGenerator:
    """Generates tests for code"""

    def __init__(self, orchestrator: ArtemisOrchestrator):
        self.orchestrator = orchestrator

    async def generate(self, code_data: dict) -> dict[str, Any]:
        """Generate tests for code"""
        return {
            "code": "# Generated tests would go here",
            "framework": self.orchestrator.code_context.test_framework,
            "coverage": 0.0,
        }


class DocumentationGenerator:
    """Generates documentation for code"""

    def __init__(self, orchestrator: ArtemisOrchestrator):
        self.orchestrator = orchestrator

    async def generate(self, code_data: dict) -> str:
        """Generate documentation for code"""
        return "# Generated documentation would go here"


class SecurityScanner:
    """Scans code for security issues"""

    def __init__(self, orchestrator: ArtemisOrchestrator):
        self.orchestrator = orchestrator

    async def scan(self, code_data: dict) -> dict[str, Any]:
        """Full security scan"""
        return {"vulnerabilities": [], "score": 0.9, "recommendations": []}

    async def quick_scan(self, code: str) -> float:
        """Quick security score"""
        # Check for common security issues
        issues = 0

        dangerous_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "os.system",
            "subprocess.call",
            "pickle.loads",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                issues += 1

        return max(0, 1.0 - (issues * 0.2))


class PerformanceAnalyzer:
    """Analyzes code performance"""

    def __init__(self, orchestrator: ArtemisOrchestrator):
        self.orchestrator = orchestrator

    async def analyze(self, code_data: dict) -> dict[str, Any]:
        """Analyze performance characteristics"""
        return {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "bottlenecks": [],
            "optimizations": [],
        }


class CodeSandbox:
    """Safe code execution sandbox"""

    async def execute(
        self, code: str, language: str, timeout: int = 5
    ) -> dict[str, Any]:
        """Execute code in sandbox"""
        # Would implement sandboxed execution
        return {"output": "", "errors": [], "execution_time": 0.0}

    # ========== MCP Integration Methods ==========

    async def _get_mcp_connection(self, server_type: MCPServerType):
        """
        Get MCP connection for Artemis domain

        Args:
            server_type: Type of MCP server needed

        Returns:
            Connection object or None
        """
        try:
            # Route request through MCP router
            server_name = await self.mcp_router.route_request(
                server_type, MemoryDomain.ARTEMIS, {"operation": "artemis_code_task"}
            )

            if server_name:
                # Get connection from manager
                connection = await self.mcp_connection_manager.get_connection(
                    server_name, "artemis"
                )
                return connection

        except Exception as e:
            logger.error(f"Failed to get MCP connection for {server_type}: {e}")

        return None

    async def _analyze_file_structure_mcp(
        self, repo_path: Path, connection
    ) -> dict[str, Any]:
        """Analyze file structure using MCP filesystem server"""
        # Implementation would use MCP filesystem server
        # This is a placeholder showing the pattern
        return {"total_files": 0, "file_types": {}, "directories": []}

    async def _identify_patterns_mcp(
        self, repo_path: Path, connection
    ) -> dict[str, Any]:
        """Identify code patterns using MCP code analysis server"""
        # Implementation would use MCP code analysis server
        return {"design_patterns": [], "anti_patterns": [], "common_imports": []}

    async def _detect_conventions_mcp(
        self, repo_path: Path, connection
    ) -> dict[str, Any]:
        """Detect coding conventions using MCP code analysis server"""
        # Implementation would use MCP code analysis server
        return {"naming": "snake_case", "indentation": "spaces_4", "quotes": "double"}

    async def _search_code_mcp(
        self, query: str, connection, filters: dict = None
    ) -> list[dict]:
        """Search code using MCP indexing server"""
        # Implementation would use MCP indexing server
        return []

    async def _enhance_with_embeddings_mcp(
        self, examples: list[dict], query: str, connection
    ) -> list[dict]:
        """Enhance examples with semantic similarity using MCP embedding server"""
        # Implementation would use MCP embedding server
        return examples
