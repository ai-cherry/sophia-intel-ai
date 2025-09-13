"""
Task Analyzer for Sophia AI Orchestration
Analyzes tasks to determine complexity, required tools, and approach
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)
class TaskComplexity(Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"  # < 30 min
    SIMPLE = "simple"  # 30 min - 2 hours
    MODERATE = "moderate"  # 2 - 8 hours
    COMPLEX = "complex"  # 1 - 3 days
    EPIC = "epic"  # > 3 days
@dataclass
class TaskAnalysis:
    """Result of task analysis"""
    task_type: str
    complexity: TaskComplexity
    required_tools: list[str]
    estimated_hours: float
    subtasks: list[dict[str, Any]]
    context_needed: list[str]
    risks: list[str]
    confidence: float
class TaskAnalyzer:
    """Analyzes development tasks to determine optimal approach"""
    def __init__(self, openrouter_service=None, ai_memory_service=None):
        self.openrouter = openrouter_service
        self.ai_memory = ai_memory_service
        # Task patterns for heuristic analysis
        self.task_patterns = {
            "bugfix": {
                "keywords": ["fix", "bug", "error", "issue", "broken", "crash"],
                "typical_complexity": TaskComplexity.SIMPLE,
                "typical_tools": ["code_search", "github", "git"],
                "typical_hours": 2.0,
            },
            "feature": {
                "keywords": ["add", "implement", "create", "new feature", "build"],
                "typical_complexity": TaskComplexity.MODERATE,
                "typical_tools": ["code_search", "github", "linear"],
                "typical_hours": 6.0,
            },
            "refactor": {
                "keywords": [
                    "refactor",
                    "restructure",
                    "reorganize",
                    "optimize",
                    "clean up",
                ],
                "typical_complexity": TaskComplexity.MODERATE,
                "typical_tools": ["code_search", "git"],
                "typical_hours": 4.0,
            },
            "test": {
                "keywords": [
                    "test",
                    "testing",
                    "unit test",
                    "integration test",
                    "coverage",
                ],
                "typical_complexity": TaskComplexity.SIMPLE,
                "typical_tools": ["code_search", "github"],
                "typical_hours": 3.0,
            },
            "documentation": {
                "keywords": ["document", "docs", "readme", "guide", "tutorial"],
                "typical_complexity": TaskComplexity.SIMPLE,
                "typical_tools": ["notion", "github"],
                "typical_hours": 2.0,
            },
            "deployment": {
                "keywords": ["deploy", "release", "production", "staging"],
                "typical_complexity": TaskComplexity.MODERATE,
                "typical_tools": ["github", "slack"],
                "typical_hours": 2.0,
            },
        }
    async def analyze(self, task_description: str) -> TaskAnalysis:
        """Analyze a task description to determine approach"""
        # Start with heuristic analysis
        heuristic_result = self._heuristic_analysis(task_description)
        # If AI services are available, enhance with AI analysis
        if self.openrouter:
            try:
                ai_result = await self._ai_analysis(task_description)
                # Merge results, preferring AI when confident
                if ai_result and ai_result.get("confidence", 0) > 0.7:
                    return self._merge_analyses(heuristic_result, ai_result)
            except Exception as e:
                logger.warning(f"AI analysis failed, using heuristic only: {e}")
        return heuristic_result
    def _heuristic_analysis(self, task_description: str) -> TaskAnalysis:
        """Perform heuristic analysis based on patterns"""
        description_lower = task_description.lower()
        # Determine task type
        task_type = "general"
        for pattern_type, pattern_info in self.task_patterns.items():
            if any(
                keyword in description_lower for keyword in pattern_info["keywords"]
            ):
                task_type = pattern_type
                break
        pattern = self.task_patterns.get(task_type, {})
        # Estimate complexity based on certain indicators
        complexity = pattern.get("typical_complexity", TaskComplexity.MODERATE)
        if any(
            word in description_lower for word in ["simple", "quick", "minor", "small"]
        ):
            complexity = TaskComplexity.SIMPLE
        elif any(
            word in description_lower
            for word in ["complex", "major", "large", "entire", "system"]
        ):
            complexity = TaskComplexity.COMPLEX
        elif any(
            word in description_lower
            for word in ["epic", "massive", "complete rewrite"]
        ):
            complexity = TaskComplexity.EPIC
        # Determine required tools
        required_tools = pattern.get("typical_tools", ["code_search", "github"])
        if "api" in description_lower or "endpoint" in description_lower:
            required_tools.append("openrouter")
        if "database" in description_lower or "sql" in description_lower:
            required_tools.append("ai_memory")
        if "deploy" in description_lower:
            required_tools.append("slack")
        # Estimate hours based on complexity
        hours_map = {
            TaskComplexity.TRIVIAL: 0.5,
            TaskComplexity.SIMPLE: 2.0,
            TaskComplexity.MODERATE: 6.0,
            TaskComplexity.COMPLEX: 16.0,
            TaskComplexity.EPIC: 40.0,
        }
        estimated_hours = hours_map.get(complexity, pattern.get("typical_hours", 4.0))
        # Generate subtasks based on task type
        subtasks = self._generate_subtasks(task_type, task_description)
        # Determine context needed
        context_needed = []
        if "fix" in description_lower or "bug" in description_lower:
            context_needed.append("Error logs and stack traces")
            context_needed.append("Recent changes to affected code")
        if "api" in description_lower:
            context_needed.append("API documentation and schemas")
        if "refactor" in description_lower:
            context_needed.append("Current code structure and dependencies")
        # Identify risks
        risks = []
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC]:
            risks.append("May require breaking changes")
        if "database" in description_lower:
            risks.append("Data migration may be needed")
        if "api" in description_lower:
            risks.append("May affect external integrations")
        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            required_tools=list(set(required_tools)),  # Remove duplicates
            estimated_hours=estimated_hours,
            subtasks=subtasks,
            context_needed=context_needed,
            risks=risks,
            confidence=0.6,  # Heuristic confidence
        )
    def _generate_subtasks(
        self, task_type: str, description: str
    ) -> list[dict[str, Any]]:
        """Generate subtasks based on task type"""
        subtask_templates = {
            "bugfix": [
                {"name": "Reproduce the issue", "estimated_minutes": 30},
                {"name": "Identify root cause", "estimated_minutes": 60},
                {"name": "Implement fix", "estimated_minutes": 60},
                {"name": "Test the fix", "estimated_minutes": 30},
                {"name": "Update documentation", "estimated_minutes": 15},
            ],
            "feature": [
                {"name": "Design the feature", "estimated_minutes": 60},
                {"name": "Implement core functionality", "estimated_minutes": 180},
                {"name": "Add tests", "estimated_minutes": 60},
                {"name": "Update documentation", "estimated_minutes": 30},
                {"name": "Code review", "estimated_minutes": 30},
            ],
            "refactor": [
                {"name": "Analyze current code structure", "estimated_minutes": 45},
                {"name": "Plan refactoring approach", "estimated_minutes": 30},
                {"name": "Implement refactoring", "estimated_minutes": 120},
                {"name": "Update tests", "estimated_minutes": 45},
                {"name": "Verify no regressions", "estimated_minutes": 30},
            ],
            "test": [
                {"name": "Identify test scenarios", "estimated_minutes": 30},
                {"name": "Write test cases", "estimated_minutes": 90},
                {"name": "Run tests and fix issues", "estimated_minutes": 30},
                {"name": "Update test documentation", "estimated_minutes": 15},
            ],
            "documentation": [
                {"name": "Gather information", "estimated_minutes": 30},
                {"name": "Create outline", "estimated_minutes": 20},
                {"name": "Write content", "estimated_minutes": 60},
                {"name": "Review and edit", "estimated_minutes": 20},
            ],
            "deployment": [
                {"name": "Prepare release notes", "estimated_minutes": 20},
                {"name": "Run pre-deployment checks", "estimated_minutes": 15},
                {"name": "Deploy to staging", "estimated_minutes": 30},
                {"name": "Run smoke tests", "estimated_minutes": 20},
                {"name": "Deploy to production", "estimated_minutes": 30},
                {"name": "Monitor deployment", "estimated_minutes": 30},
            ],
        }
        return subtask_templates.get(
            task_type,
            [
                {"name": "Analyze requirements", "estimated_minutes": 30},
                {"name": "Implement solution", "estimated_minutes": 120},
                {"name": "Test implementation", "estimated_minutes": 30},
                {"name": "Document changes", "estimated_minutes": 20},
            ],
        )
    async def _ai_analysis(self, task_description: str) -> dict[str, Any] | None:
        """Perform AI-powered analysis"""
        if not self.openrouter:
            return None
        try:
            # Use OpenRouter to get analysis
            # This is a placeholder - actual implementation would use the service
            result = {
                "task_type": "feature",
                "complexity": "moderate",
                "required_tools": ["code_search", "github", "linear"],
                "estimated_hours": 6.0,
                "subtasks": [
                    {"name": "Design API", "estimated_minutes": 60},
                    {"name": "Implement endpoint", "estimated_minutes": 180},
                    {"name": "Add tests", "estimated_minutes": 60},
                ],
                "context_needed": ["Existing API patterns", "Authentication flow"],
                "risks": ["May affect existing endpoints"],
                "confidence": 0.85,
            }
            return result
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None
    def _merge_analyses(
        self, heuristic: TaskAnalysis, ai_result: dict[str, Any]
    ) -> TaskAnalysis:
        """Merge heuristic and AI analyses"""
        # Convert AI complexity string to enum
        complexity_map = {
            "trivial": TaskComplexity.TRIVIAL,
            "simple": TaskComplexity.SIMPLE,
            "moderate": TaskComplexity.MODERATE,
            "complex": TaskComplexity.COMPLEX,
            "epic": TaskComplexity.EPIC,
        }
        ai_complexity = complexity_map.get(
            ai_result.get("complexity", "moderate"), heuristic.complexity
        )
        # Merge tools lists
        all_tools = set(heuristic.required_tools + ai_result.get("required_tools", []))
        # Average the hour estimates
        avg_hours = (
            heuristic.estimated_hours
            + ai_result.get("estimated_hours", heuristic.estimated_hours)
        ) / 2
        return TaskAnalysis(
            task_type=ai_result.get("task_type", heuristic.task_type),
            complexity=ai_complexity,
            required_tools=list(all_tools),
            estimated_hours=avg_hours,
            subtasks=ai_result.get("subtasks", heuristic.subtasks),
            context_needed=ai_result.get("context_needed", heuristic.context_needed),
            risks=ai_result.get("risks", heuristic.risks),
            confidence=ai_result.get("confidence", 0.85),
        )
    async def search_similar_tasks(self, task_description: str) -> list[dict[str, Any]]:
        """Search for similar historical tasks"""
        if not self.ai_memory:
            return []
        # This would use the AI memory service to find similar tasks
        # Production implementation implementation
        return []
