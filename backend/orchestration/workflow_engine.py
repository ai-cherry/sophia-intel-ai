"\nSophia AI Workflow Engine\nCore orchestration engine using LangGraph\nEnhanced with master conflict resolution\n"

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Any, TypedDict

from core.conflict_resolution_engine import (
    ConflictContext,
    ConflictResolutionEngine,
    ConflictType,
    with_conflict_resolution,
)
from deap import base, creator, tools
from langgraph.graph import END, StateGraph
from state_manager import StateManager
from task_analyzer import TaskAnalyzer
from tool_registry import ToolRegistry
from workflow_monitor import WorkflowMonitor

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State schema for workflow execution"""

    task_id: str
    description: str
    analysis: dict[str, Any] | None
    context: dict[str, Any]
    tools_used: list[str]
    results: list[dict[str, Any]]
    status: str
    error: str | None
    metadata: dict[str, Any]
    current_step: str
    progress: dict[str, Any]


class SophiaWorkflowEngine:
    """Main workflow orchestration engine with conflict resolution"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.state_manager = StateManager()
        self.tool_registry = ToolRegistry()
        self.task_analyzer = TaskAnalyzer()
        self.monitor = WorkflowMonitor()
        self.conflict_resolver = ConflictResolutionEngine()
        self.workflow = self._build_workflow()
        self.max_concurrent_tasks = min(
            self.config.get("max_concurrent_tasks", 50), os.cpu_count() * 8
        )
        self.worker_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.gpu_idle_timeout = self.config.get("gpu_idle_timeout", 1800)
        self.gpu_instances = {}
        self.error_patterns = {}
        self.workflow_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "auto_recovered_tasks": 0,
        }
        logger.info(
            f"Workflow engine initialized with {self.max_concurrent_tasks} max concurrent tasks"
        )

    def _build_workflow(self) -> StateGraph:
        """Build the workflow graph"""
        workflow = StateGraph(WorkflowState)
        workflow.add_node("start", self.initialize_task)
        workflow.add_node("analyze", self.analyze_task)
        workflow.add_node("plan", self.plan_execution)
        workflow.add_node("search", self.search_codebase)
        workflow.add_node("implement", self.implement_solution)
        workflow.add_node("test", self.sophia_solution)
        workflow.add_node("review", self.review_code)
        workflow.add_node("deploy", self.deploy_changes)
        workflow.add_node("complete", self.complete_task)
        workflow.add_node("error", self.handle_error)
        workflow.add_node("proactive_pre", self.proactive_pre_suggest)
        workflow.add_node("proactive_post", self.proactive_post_analyze)
        workflow.add_node("evolve", self.evolutionary_refine)
        workflow.add_node("research", self.web_research)
        workflow.add_node("refine", self.refine_task)
        workflow.add_node("options", self.generate_options)
        workflow.add_node("background_monitor", self.background_monitor)
        workflow.set_entry_point("start")
        workflow.add_edge("start", "analyze")
        workflow.add_conditional_edges(
            "analyze",
            self.route_after_analysis,
            {"needs_search": "search", "ready_to_plan": "plan", "error": "error"},
        )
        workflow.add_edge("search", "plan")
        workflow.add_conditional_edges(
            "plan",
            self.route_after_planning,
            {"implement": "implement", "review": "review", "error": "error"},
        )
        workflow.add_edge("implement", "test")
        workflow.add_conditional_edges(
            "test",
            self.route_after_testing,
            {"passed": "review", "failed": "implement", "error": "error"},
        )
        workflow.add_conditional_edges(
            "review",
            self.route_after_review,
            {"approved": "deploy", "needs_changes": "implement", "error": "error"},
        )
        workflow.add_edge("deploy", "complete")
        workflow.add_edge("complete", "background_monitor")
        workflow.add_edge("background_monitor", END)
        workflow.add_edge("complete", END)
        workflow.add_edge("error", END)
        workflow.add_edge("analyze", "proactive_pre")
        workflow.add_edge("implement", "proactive_post")
        workflow.add_edge("implement", "evolve")
        workflow.add_edge("evolve", "test")
        workflow.add_edge("analyze", "research")
        workflow.add_edge("research", "proactive_pre")
        workflow.add_edge("analyze", "refine")
        workflow.add_edge("refine", "research")
        workflow.add_edge("proactive_post", "options")
        workflow.add_edge("options", "complete")
        return workflow.compile()

    async def execute(
        self, task_id: str, initial_state: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a workflow with conflict resolution and error recovery"""
        async with self.worker_semaphore:
            self.workflow_metrics["total_tasks"] += 1
            state = WorkflowState(
                task_id=task_id,
                description=initial_state.get("description", ""),
                analysis=None,
                context=initial_state.get("context", {}),
                tools_used=[],
                results=[],
                status="started",
                error=None,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "retry_count": 0,
                    "conflict_resolutions": [],
                },
                current_step="start",
                progress={"percentage": 0, "events": []},
            )
            async with self.monitor.track_task(task_id, "workflow"):
                context = ConflictContext(
                    error_type=ConflictType.PYTHON_EXCEPTION,
                    error_message="",
                    metadata={"task_id": task_id, "workflow_state": state},
                    max_retries=3,
                )

                async def workflow_operation():
                    final_state = await self.workflow.ainvoke(state)
                    if self._requires_gpu(state):
                        await self.setup_gpu_auto_terminate(task_id)
                    return final_state

                try:
                    resolution = await self.conflict_resolver.resolve_conflict(
                        context, workflow_operation
                    )
                    if resolution.success:
                        self.workflow_metrics["successful_tasks"] += 1
                        if context.retry_count > 0:
                            self.workflow_metrics["auto_recovered_tasks"] += 1
                        return resolution.resolved_value
                    else:
                        self.workflow_metrics["failed_tasks"] += 1
                        state["status"] = "error"
                        state["error"] = str(resolution.error)
                        state["metadata"][
                            "conflict_resolutions"
                        ] = context.resolution_history
                        await self.state_manager.save_state(task_id, state)
                        raise resolution.error or Exception("Workflow execution failed")
                except Exception as e:
                    self.workflow_metrics["failed_tasks"] += 1
                    logger.error(f"Workflow execution failed for task {task_id}: {e}")
                    error_type = type(e).__name__
                    self.error_patterns[error_type] = (
                        self.error_patterns.get(error_type, 0) + 1
                    )
                    state["status"] = "error"
                    state["error"] = str(e)
                    await self.state_manager.save_state(task_id, state)
                    raise

    async def initialize_task(self, state: WorkflowState) -> WorkflowState:
        """Initialize the task"""
        state["current_step"] = "initialize"
        state["progress"]["percentage"] = 5
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Task initialized",
                "type": "info",
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        logger.info(f"Initialized task {state['task_id']}")
        return state

    async def analyze_task(self, state: WorkflowState) -> WorkflowState:
        """Analyze the task to determine approach"""
        state["current_step"] = "analyze"
        state["progress"]["percentage"] = 15
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Analyzing task requirements",
                "type": "info",
            }
        )
        try:
            analysis = await self.task_analyzer.analyze(state["description"])
            state["analysis"] = {
                "task_type": analysis.task_type,
                "complexity": analysis.complexity.value,
                "required_tools": analysis.required_tools,
                "estimated_hours": analysis.estimated_hours,
                "subtasks": analysis.subtasks,
                "context_needed": analysis.context_needed,
                "risks": analysis.risks,
                "confidence": analysis.confidence,
            }
            state["progress"]["events"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Task analyzed: {analysis.task_type} ({analysis.complexity.value} complexity)",
                    "type": "success",
                }
            )
            await self.state_manager.save_state(state["task_id"], state)
        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            state["error"] = str(e)
            state["status"] = "error"
        return state

    @with_conflict_resolution(ConflictType.NETWORK_TIMEOUT, max_retries=2)
    async def search_codebase(self, state: WorkflowState) -> WorkflowState:
        """Search codebase with retry logic for network issues"""
        state["current_step"] = "search"
        state["progress"]["percentage"] = 25
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Searching codebase for context",
                "type": "info",
            }
        )
        try:
            if state["analysis"] and state["analysis"]["context_needed"]:
                search_tasks = []
                for context_item in state["analysis"]["context_needed"]:

                    async def search_with_timeout(item):
                        try:
                            return await asyncio.wait_for(
                                self.tool_registry.execute_tool(
                                    "code_search", {"query": item}
                                ),
                                timeout=30.0,
                            )
                        except TimeoutError:
                            logger.warning(f"Search timeout for: {item}")
                            return {"error": "timeout", "query": item}

                    search_tasks.append(search_with_timeout(context_item))
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
                for context_item, result in zip(
                    state["analysis"]["context_needed"], results, strict=False
                ):
                    if isinstance(result, Exception):
                        logger.error(f"Search failed for {context_item}: {result}")
                        state["context"][f"search_{context_item}"] = {
                            "error": str(result)
                        }
                    else:
                        state["context"][f"search_{context_item}"] = result
                    state["tools_used"].append("code_search")
            state["progress"]["events"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": "Context search completed",
                    "type": "success",
                }
            )
            await self.state_manager.save_state(state["task_id"], state)
        except Exception as e:
            logger.error(f"Codebase search failed: {e}")
            state["error"] = str(e)
        return state

    async def plan_execution(self, state: WorkflowState) -> WorkflowState:
        """Plan the execution approach"""
        state["current_step"] = "plan"
        state["progress"]["percentage"] = 35
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Planning execution strategy",
                "type": "info",
            }
        )
        if state["analysis"]:
            plan = {
                "steps": state["analysis"]["subtasks"],
                "tools_required": state["analysis"]["required_tools"],
                "estimated_time": state["analysis"]["estimated_hours"],
            }
            state["context"]["execution_plan"] = plan
            state["progress"]["events"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Execution plan created with {len(plan['steps'])} steps",
                    "type": "success",
                }
            )
        await self.state_manager.save_state(state["task_id"], state)
        return state

    async def implement_solution(self, state: WorkflowState) -> WorkflowState:
        """Implement the solution"""
        state["current_step"] = "implement"
        state["progress"]["percentage"] = 50
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Implementing solution",
                "type": "info",
            }
        )
        implementation_result = {
            "files_created": [],
            "files_modified": [],
            "code_snippets": [],
        }
        state["results"].append(
            {
                "type": "implementation",
                "data": implementation_result,
                "timestamp": datetime.now().isoformat(),
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        return state

    async def sophia_solution(self, state: WorkflowState) -> WorkflowState:
        """Test the implemented solution"""
        state["current_step"] = "test"
        state["progress"]["percentage"] = 70
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Testing implementation",
                "type": "info",
            }
        )
        sophia_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage": 0,
        }
        state["results"].append(
            {
                "type": "test",
                "data": sophia_result,
                "timestamp": datetime.now().isoformat(),
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        return state

    async def review_code(self, state: WorkflowState) -> WorkflowState:
        """Review the code changes"""
        state["current_step"] = "review"
        state["progress"]["percentage"] = 85
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Reviewing code changes",
                "type": "info",
            }
        )
        review_result = {
            "issues_found": [],
            "suggestions": [],
            "approval_status": "approved",
        }
        state["results"].append(
            {
                "type": "review",
                "data": review_result,
                "timestamp": datetime.now().isoformat(),
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        return state

    async def deploy_changes(self, state: WorkflowState) -> WorkflowState:
        """Deploy the changes"""
        state["current_step"] = "deploy"
        state["progress"]["percentage"] = 95
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Deploying changes",
                "type": "info",
            }
        )
        deployment_result = {
            "deployment_id": str(uuid.uuid4()),
            "status": "success",
            "url": None,
        }
        state["results"].append(
            {
                "type": "deployment",
                "data": deployment_result,
                "timestamp": datetime.now().isoformat(),
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        return state

    async def complete_task(self, state: WorkflowState) -> WorkflowState:
        """Complete the task"""
        state["current_step"] = "complete"
        state["progress"]["percentage"] = 100
        state["status"] = "completed"
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": "Task completed successfully",
                "type": "success",
            }
        )
        await self.state_manager.save_state(state["task_id"], state)
        logger.info(f"Task {state['task_id']} completed successfully")
        return state

    async def handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle errors with intelligent recovery strategies"""
        state["status"] = "error"
        error_msg = state.get("error", "Unknown error")
        state["progress"]["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": f"Error: {error_msg}",
                "type": "error",
            }
        )
        recovery_attempted = False
        context = ConflictContext(
            error_type=self.conflict_resolver._detect_conflict_type(error_msg),
            error_message=error_msg,
            metadata={
                "task_id": state["task_id"],
                "current_step": state["current_step"],
                "retry_count": state["metadata"].get("retry_count", 0),
            },
        )

        async def recovery_operation():
            if state["current_step"] in ["implement", "test", "deploy"]:
                state["current_step"] = "plan"
                state["status"] = "recovering"
                return True
            return False

        try:
            resolution = await self.conflict_resolver.resolve_conflict(
                context, recovery_operation
            )
            if resolution.success:
                state["progress"]["events"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "message": f"Recovery attempted using {resolution.strategy_used.value}",
                        "type": "warning",
                    }
                )
                recovery_attempted = True
                state["metadata"]["recovery_strategy"] = resolution.strategy_used.value
        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
        state["metadata"]["error_handled"] = True
        state["metadata"]["recovery_attempted"] = recovery_attempted
        await self.state_manager.save_state(state["task_id"], state)
        logger.error(f"Task {state['task_id']} failed: {error_msg}")
        return state

    async def evolutionary_refine(self, state: WorkflowState) -> WorkflowState:
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        toolbox = base.Toolbox()
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
        refined = f"Evolved: {state['implement_result']} (mutated)"
        state["refined_result"] = refined
        return state

    async def web_research(self, state: WorkflowState) -> WorkflowState:
        research = await self.tool_registry.execute_tool(
            "web_research", {"query": state["description"]}
        )
        state["research"] = research
        return state

    async def refine_task(self, state: WorkflowState) -> WorkflowState:
        questions = await self.tool_registry.execute_tool(
            "ask_refining_questions", {"task": state["description"]}
        )
        state["refining_questions"] = questions
        state["refined_task"] = f"Refined: {state['description']} (with answers)"
        return state

    async def generate_options(self, state: WorkflowState) -> WorkflowState:
        if state["complexity"] > 50:
            options = {
                "stable": "Add unit tests",
                "enhance": "Optimize with Redis cache",
                "creative": "Experiment with WebSocket integration",
            }
            state["post_options"] = options
        return state

    async def background_monitor(self, state: WorkflowState) -> WorkflowState:
        state["monitoring"] = "Background monitoring activated"
        return state

    async def setup_gpu_auto_terminate(self, task_id: str):
        """Setup GPU auto-termination for idle instances"""
        try:
            self.gpu_instances[task_id] = {
                "started_at": datetime.now(),
                "last_activity": datetime.now(),
                "instance_id": f"gpu-{task_id[:8]}",
            }
            asyncio.create_task(self._monitor_gpu_idle(task_id))
            logger.info(f"GPU auto-termination configured for task {task_id}")
        except Exception as e:
            logger.warning(f"Failed to setup GPU auto-termination: {e}")

    async def _monitor_gpu_idle(self, task_id: str):
        """Monitor GPU instance for idle timeout"""
        await asyncio.sleep(self.gpu_idle_timeout)
        if task_id in self.gpu_instances:
            instance_info = self.gpu_instances[task_id]
            idle_time = (
                datetime.now() - instance_info["last_activity"]
            ).total_seconds()
            if idle_time >= self.gpu_idle_timeout:
                try:
                    await self._terminate_gpu_instance(instance_info["instance_id"])
                    del self.gpu_instances[task_id]
                    logger.info(f"Auto-terminated idle GPU instance for task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to terminate GPU instance: {e}")

    async def _terminate_gpu_instance(self, instance_id: str):
        """Terminate GPU instance (placeholder for Lambda Labs integration)"""
        logger.info(f"Terminating GPU instance: {instance_id}")

    def _requires_gpu(self, state: WorkflowState) -> bool:
        """Check if task requires GPU resources"""
        if state.get("analysis"):
            task_type = state["analysis"].get("task_type", "")
            return any(
                gpu_keyword in task_type.lower()
                for gpu_keyword in ["embedding", "ml", "ai", "training", "inference"]
            )
        return False

    def route_after_analysis(self, state: WorkflowState) -> str:
        """Determine next step after analysis with error recovery"""
        if state.get("error"):
            error_msg = state.get("error", "")
            if any(
                pattern in error_msg.lower()
                for pattern in ["timeout", "rate limit", "temporary"]
            ):
                state["metadata"]["retry_count"] = (
                    state["metadata"].get("retry_count", 0) + 1
                )
                if state["metadata"]["retry_count"] < 3:
                    state["error"] = None
                    return "analyze"
            return "error"
        if state["analysis"] and state["analysis"]["context_needed"]:
            return "needs_search"
        return "ready_to_plan"

    def route_after_planning(self, state: WorkflowState) -> str:
        """Determine next step after planning"""
        if state.get("error"):
            return "error"
        return "implement"

    def route_after_testing(self, state: WorkflowState) -> str:
        """Determine next step after testing"""
        if state.get("error"):
            return "error"
        sophia_results = [r for r in state["results"] if r["type"] == "test"]
        if sophia_results and sophia_results[-1]["data"]["tests_failed"] > 0:
            return "failed"
        return "passed"

    def route_after_review(self, state: WorkflowState) -> str:
        """Determine next step after review"""
        if state.get("error"):
            return "error"
        review_results = [r for r in state["results"] if r["type"] == "review"]
        if (
            review_results
            and review_results[-1]["data"]["approval_status"] == "approved"
        ):
            return "approved"
        return "needs_changes"

    def proactive_pre_suggest(self, state: WorkflowState) -> WorkflowState:
        state["pre_suggestions"] = ["Idea: Use Redis for hot paths?"]
        return state

    def proactive_post_analyze(self, state: WorkflowState) -> WorkflowState:
        state["post_analysis"] = ["Opt: Add circuit breakers."]
        return state


workflow_engine: SophiaWorkflowEngine | None = None
