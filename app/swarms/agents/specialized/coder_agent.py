"""
Coder Agent - Specialized for Software Development

Optimized for writing clean, efficient, well-documented code.
Focuses on best practices for security, performance, and maintainability.
"""

from typing import Any

from app.tools.code_search import CodeSearchTool
from app.tools.git_ops import GitOperationsTool
from app.tools.test_ops import TestingTool

from ..base_agent import AgentRole, BaseAgent


class CoderAgent(BaseAgent):
    """
    Specialized agent for software development and code generation.
    
    Features:
    - Code generation with best practices
    - Security-focused development
    - Performance optimization
    - Automated testing integration
    """

    def __init__(
        self,
        agent_id: str = "coder-001",
        programming_languages: list[str] = None,
        enable_reasoning: bool = True,
        max_reasoning_steps: int = 12,
        **kwargs
    ):
        self.programming_languages = programming_languages or [
            "python", "javascript", "typescript", "rust", "go"
        ]

        # Custom tools for coding
        coding_tools = [
            CodeSearchTool(),
            GitOperationsTool(),
            TestingTool()
        ]

        # Initialize with coder-specific configuration
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.CODER,
            enable_reasoning=enable_reasoning,
            max_reasoning_steps=max_reasoning_steps,
            tools=coding_tools,
            model_config={
                "temperature": 0.3,  # Balanced creativity for coding
                "cost_limit_per_request": 0.60
            },
            **kwargs
        )

    async def generate_code(self, specification: dict[str, Any]) -> dict[str, Any]:
        """
        Generate code based on functional specification.
        
        Args:
            specification: Code requirements and specifications
            
        Returns:
            Generated code with documentation and tests
        """

        coding_problem = {
            "query": f"""Generate {specification.get('language', 'python')} code for the following specification:
            
            Function/Class: {specification.get('name', 'untitled')}
            Purpose: {specification.get('purpose', 'No purpose specified')}
            Requirements: {specification.get('requirements', 'No specific requirements')}
            Input: {specification.get('input', 'Not specified')}
            Output: {specification.get('output', 'Not specified')}
            Constraints: {specification.get('constraints', 'None')}
            
            Please provide:
            1. Clean, well-documented code following best practices
            2. Comprehensive docstrings and comments
            3. Error handling and input validation
            4. Unit tests demonstrating usage
            5. Security considerations and recommendations
            """,
            "context": "code_generation",
            "priority": "high"
        }

        result = await self.execute(coding_problem)

        return {
            "generated_code": result["result"],
            "language": specification.get("language", "python"),
            "reasoning_trace": result.get("reasoning_trace", []),
            "quality_score": "high" if result["success"] else "low",
            "coder_id": self.agent_id,
            "code_metadata": {
                "execution_time": result.get("execution_time", 0),
                "estimated_lines": "TBD",  # Would be calculated
                "complexity": "TBD"  # Would be analyzed
            }
        }

    async def review_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Perform comprehensive code review with suggestions.
        
        Args:
            code: Source code to review
            language: Programming language
            
        Returns:
            Code review with suggestions and quality assessment
        """

        review_problem = {
            "query": f"""Perform a comprehensive code review of this {language} code:
            
            ```{language}
            {code}
            ```
            
            Please analyze:
            1. Code quality and readability
            2. Performance optimization opportunities
            3. Security vulnerabilities and concerns
            4. Best practice adherence
            5. Maintainability and extensibility
            6. Test coverage recommendations
            
            Provide specific, actionable feedback with examples.
            """,
            "context": "code_review"
        }

        result = await self.execute(review_problem)

        return {
            "review_results": result["result"],
            "overall_quality": "TBD",  # Would be scored
            "critical_issues": [],  # Would be extracted
            "suggestions": [],  # Would be extracted
            "reviewer_id": self.agent_id,
            "success": result["success"]
        }

    async def optimize_performance(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Analyze and optimize code for performance.
        
        Args:
            code: Source code to optimize
            language: Programming language
            
        Returns:
            Optimized code with performance improvements
        """

        optimization_problem = {
            "query": f"""Analyze and optimize this {language} code for performance:
            
            ```{language}
            {code}
            ```
            
            Please provide:
            1. Performance bottleneck analysis
            2. Optimized version with improvements
            3. Before/after performance comparison
            4. Memory usage considerations
            5. Scalability recommendations
            
            Focus on algorithmic improvements and efficient data structures.
            """,
            "context": "performance_optimization"
        }

        result = await self.execute(optimization_problem)

        return {
            "optimized_code": result["result"],
            "performance_gains": "TBD",  # Would be estimated
            "bottlenecks_identified": [],  # Would be extracted
            "optimization_techniques": [],  # Would be listed
            "optimizer_id": self.agent_id,
            "success": result["success"]
        }
