# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:

"""
Planner Agent - Intent Decomposition using Semantic Kernel v1.35.0

Decomposes natural language intents into actionable subtasks with:
- Requirements analysis
- Task breakdown
- Dependency mapping
- Success criteria definition
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from semantic_kernel import Kernel
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
    from semantic_kernel.prompt_template.input_variable import InputVariable
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
    from crewai import Agent
except ImportError as e:
    logging.warning(f"Missing dependencies for Planner Agent: {e}")
    Kernel = OpenAIChatCompletion = InputVariable = None
    PromptTemplateConfig = kernel_function = Agent = None

@dataclass
class PlanTask:
    """Individual task in the implementation plan"""
    id: str
    title: str
    description: str
    dependencies: List[str]
    estimated_effort: str
    success_criteria: List[str]
    priority: int
    category: str

@dataclass
class ImplementationPlan:
    """Complete implementation plan"""
    intent: str
    overview: str
    tasks: List[PlanTask]
    architecture: Dict[str, Any]
    requirements: List[str]
    risks: List[str]
    timeline: str

class PlannerAgent:
    """
    Planner Agent using Semantic Kernel v1.35.0

    Responsible for:
    - Analyzing natural language intents
    - Breaking down complex requirements into manageable tasks
    - Identifying dependencies and constraints
    - Creating detailed implementation plans
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize Semantic Kernel
        self.kernel = None
        if Kernel:
            try:
                self.kernel = Kernel()
                self._setup_kernel()
            except Exception as e:
                self.logger.warning(f"Failed to initialize Semantic Kernel: {e}")

        # Agent metadata
        self.agent_id = "artemis_planner"
        self.version = "2.0.0"
        self.status = "initialized"

    def _setup_kernel(self):
        """Setup Semantic Kernel with OpenAI service"""
        if not self.kernel:
            return

        try:
            # Add OpenAI chat completion service
            service_id = "openai_chat"
            self.kernel.add_service(
                OpenAIChatCompletion(
                    service_id=service_id,
                    ai_model_id="gpt-4",
                )
            )

            # Register planning functions
            self._register_planning_functions()

            self.logger.info("Semantic Kernel setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup Semantic Kernel: {e}")

    def _register_planning_functions(self):
        """Register planning functions with the kernel"""
        if not self.kernel:
            return

        @kernel_function(
            description="Analyze and decompose a coding intent into detailed tasks",
            name="decompose_intent"
        )
        def decompose_intent_function(intent: str) -> str:
            """Decompose intent into actionable tasks"""
            return self._create_decomposition_prompt(intent)

        @kernel_function(
            description="Analyze technical requirements and constraints",
            name="analyze_requirements"
        )
        def analyze_requirements_function(intent: str) -> str:
            """Analyze technical requirements"""
            return self._create_requirements_prompt(intent)

        # Add functions to kernel
        self.kernel.add_function(
            plugin_name="planning",
            function=decompose_intent_function
        )
        self.kernel.add_function(
            plugin_name="planning", 
            function=analyze_requirements_function
        )

    async def decompose_intent(self, intent: str) -> Dict[str, Any]:
        """
        Decompose a natural language intent into an implementation plan

        Args:
            intent: Natural language description of what to implement

        Returns:
            Dictionary containing the detailed implementation plan
        """
        self.logger.info(f"Decomposing intent: {intent}")

        try:
            if self.kernel:
                return await self._semantic_kernel_decomposition(intent)
            else:
                return await self._fallback_decomposition(intent)

        except Exception as e:
            self.logger.error(f"Error decomposing intent: {e}")
            return {
                "error": str(e),
                "intent": intent,
                "fallback_plan": await self._emergency_fallback(intent)
            }

    async def _semantic_kernel_decomposition(self, intent: str) -> Dict[str, Any]:
        """Use Semantic Kernel for intent decomposition"""

        # Create decomposition prompt
        decomposition_prompt = f"""
        Analyze this coding intent and create a detailed implementation plan:

        Intent: {intent}

        Please provide:
        1. High-level overview of the solution
        2. Detailed task breakdown with dependencies
        3. Technical architecture considerations
        4. Required technologies and frameworks
        5. Potential risks and mitigation strategies
        6. Success criteria for each task

        Format the response as a structured plan with clear sections.
        """

        # Execute with Semantic Kernel
        result = await self.kernel.invoke_prompt(
            function_name="decompose_intent",
            plugin_name="planning",
            prompt=decomposition_prompt
        )

        # Parse and structure the result
        return self._parse_kernel_result(str(result), intent)

    async def _fallback_decomposition(self, intent: str) -> Dict[str, Any]:
        """Fallback decomposition without Semantic Kernel"""
        self.logger.info("Using fallback decomposition method")

        # Simple rule-based decomposition
        tasks = []

        # Analyze intent for common patterns
        if "api" in intent.lower() or "endpoint" in intent.lower():
            tasks.extend(self._create_api_tasks(intent))
        elif "dashboard" in intent.lower() or "ui" in intent.lower():
            tasks.extend(self._create_ui_tasks(intent))
        elif "database" in intent.lower() or "data" in intent.lower():
            tasks.extend(self._create_data_tasks(intent))
        else:
            tasks.extend(self._create_generic_tasks(intent))

        return {
            "intent": intent,
            "overview": f"Implementation plan for: {intent}",
            "tasks": [task.__dict__ for task in tasks],
            "architecture": self._suggest_architecture(intent),
            "requirements": self._extract_requirements(intent),
            "risks": self._identify_risks(intent),
            "timeline": self._estimate_timeline(len(tasks)),
            "method": "fallback"
        }

    def _create_api_tasks(self, intent: str) -> List[PlanTask]:
        """Create tasks for API development"""
        return [
            PlanTask(
                id="api_design",
                title="API Design and Specification",
                description="Design API endpoints, request/response schemas, and documentation",
                dependencies=[],
                estimated_effort="2-4 hours",
                success_criteria=["OpenAPI spec created", "Endpoints documented"],
                priority=1,
                category="design"
            ),
            PlanTask(
                id="api_implementation",
                title="API Implementation",
                description="Implement API endpoints using FastAPI framework",
                dependencies=["api_design"],
                estimated_effort="4-8 hours",
                success_criteria=["All endpoints implemented", "Basic validation added"],
                priority=2,
                category="development"
            ),
            PlanTask(
                id="api_testing",
                title="API Testing",
                description="Create comprehensive tests for API endpoints",
                dependencies=["api_implementation"],
                estimated_effort="2-4 hours",
                success_criteria=["Unit tests written", "Integration tests pass"],
                priority=3,
                category="testing"
            )
        ]

    def _create_ui_tasks(self, intent: str) -> List[PlanTask]:
        """Create tasks for UI development"""
        return [
            PlanTask(
                id="ui_design",
                title="UI/UX Design",
                description="Design user interface and user experience",
                dependencies=[],
                estimated_effort="3-6 hours",
                success_criteria=["Wireframes created", "Design system defined"],
                priority=1,
                category="design"
            ),
            PlanTask(
                id="ui_implementation",
                title="UI Implementation",
                description="Implement user interface using React/Streamlit",
                dependencies=["ui_design"],
                estimated_effort="6-12 hours",
                success_criteria=["Components implemented", "Responsive design"],
                priority=2,
                category="development"
            )
        ]

    def _create_data_tasks(self, intent: str) -> List[PlanTask]:
        """Create tasks for data-related development"""
        return [
            PlanTask(
                id="data_modeling",
                title="Data Model Design",
                description="Design database schema and data models",
                dependencies=[],
                estimated_effort="2-4 hours",
                success_criteria=["Schema designed", "Relationships defined"],
                priority=1,
                category="design"
            ),
            PlanTask(
                id="data_implementation",
                title="Data Layer Implementation",
                description="Implement database models and data access layer",
                dependencies=["data_modeling"],
                estimated_effort="4-6 hours",
                success_criteria=["Models implemented", "CRUD operations work"],
                priority=2,
                category="development"
            )
        ]

    def _create_generic_tasks(self, intent: str) -> List[PlanTask]:
        """Create generic tasks for unknown intents"""
        return [
            PlanTask(
                id="analysis",
                title="Requirements Analysis",
                description="Analyze and clarify requirements",
                dependencies=[],
                estimated_effort="1-2 hours",
                success_criteria=["Requirements documented", "Scope defined"],
                priority=1,
                category="analysis"
            ),
            PlanTask(
                id="implementation",
                title="Core Implementation",
                description="Implement the main functionality",
                dependencies=["analysis"],
                estimated_effort="4-8 hours",
                success_criteria=["Core features implemented", "Basic testing done"],
                priority=2,
                category="development"
            )
        ]

    def _suggest_architecture(self, intent: str) -> Dict[str, Any]:
        """Suggest technical architecture based on intent"""
        architecture = {
            "pattern": "microservices",
            "technologies": ["Python", "FastAPI"],
            "database": "PostgreSQL",
            "caching": "Redis"
        }

        if "api" in intent.lower():
            architecture["technologies"].extend(["Pydantic", "SQLAlchemy"])
        if "ui" in intent.lower():
            architecture["technologies"].extend(["React", "TypeScript"])
        if "ml" in intent.lower() or "ai" in intent.lower():
            architecture["technologies"].extend(["PyTorch", "Transformers"])

        return architecture

    def _extract_requirements(self, intent: str) -> List[str]:
        """Extract technical requirements from intent"""
        requirements = ["Python 3.11+", "FastAPI framework"]

        if "database" in intent.lower():
            requirements.append("PostgreSQL database")
        if "auth" in intent.lower():
            requirements.append("Authentication system")
        if "api" in intent.lower():
            requirements.append("API documentation")

        return requirements

    def _identify_risks(self, intent: str) -> List[str]:
        """Identify potential risks and challenges"""
        risks = ["Unclear requirements", "Technical complexity"]

        if "auth" in intent.lower():
            risks.append("Security vulnerabilities")
        if "performance" in intent.lower():
            risks.append("Scalability challenges")
        if "integration" in intent.lower():
            risks.append("Third-party API dependencies")

        return risks

    def _estimate_timeline(self, task_count: int) -> str:
        """Estimate implementation timeline"""
        if task_count <= 2:
            return "1-2 days"
        elif task_count <= 4:
            return "3-5 days"
        else:
            return "1-2 weeks"

    def _parse_kernel_result(self, result: str, intent: str) -> Dict[str, Any]:
        """Parse Semantic Kernel result into structured format"""
        # This would parse the LLM response into structured data
        # For now, return a basic structure
        return {
            "intent": intent,
            "overview": result[:200] + "..." if len(result) > 200 else result,
            "raw_analysis": result,
            "method": "semantic_kernel",
            "timestamp": datetime.now().isoformat()
        }

    async def _emergency_fallback(self, intent: str) -> Dict[str, Any]:
        """Emergency fallback when all other methods fail"""
        return {
            "intent": intent,
            "overview": "Basic implementation plan",
            "tasks": [
                {
                    "id": "emergency_task",
                    "title": "Implement basic functionality",
                    "description": f"Implement: {intent}",
                    "priority": 1
                }
            ],
            "method": "emergency_fallback"
        }

    def get_crewai_agent(self) -> Optional[Agent]:
        """Get CrewAI agent representation"""
        if not Agent:
            return None

        return Agent(
            role="Planning Specialist",
            goal="Decompose complex coding intents into actionable implementation plans",
            backstory="""You are an expert software architect and project planner with deep 
            experience in breaking down complex requirements into manageable tasks. You excel 
            at identifying dependencies, estimating effort, and creating clear implementation 
            roadmaps that guide development teams to success.""",
            verbose=True,
            allow_delegation=False
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "status": self.status,
            "kernel_available": self.kernel is not None,
            "capabilities": [
                "intent_decomposition",
                "task_breakdown", 
                "dependency_analysis",
                "risk_assessment"
            ],
            "timestamp": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    async def main():
        planner = PlannerAgent()
        result = await planner.decompose_intent("Create a user authentication API with JWT tokens")
        print(result)

    asyncio.run(main())
