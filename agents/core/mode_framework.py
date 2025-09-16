#!/usr/bin/env python3
"""
Shared Mode Framework - Base class for all custom Roo modes
Provides common infrastructure for sequential workflows, model routing, and MCP integration
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple

from agents.core.base_agent import AgentCapability, AgentConfig, BaseAgent
from agents.core.workflow_engine import WorkflowEngine
from agents.core.model_router import ModelRouter
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class ModePhase(Enum):
    """Standard phases for mode workflows"""
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    EVALUATION = "evaluation"
    OPTIMIZATION = "optimization"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"


@dataclass
class ModeConfig:
    """Configuration for a specific mode"""
    mode_id: str
    mode_name: str
    version: str = "1.0.0"
    description: str = ""
    category: str = "custom"
    status: str = "active"
    unique_components: str = ""
    workflow_steps: List[str] = field(default_factory=list)
    model_phases: Dict[str, str] = field(default_factory=dict)
    mcp_hooks: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class ModeFramework(BaseAgent, ABC):
    """
    Base class for all custom Roo modes
    Provides shared infrastructure for:
    - Sequential workflow execution
    - Model routing based on phases
    - MCP integration
    - Shared MCP client
    - Workflow engine
    """

    def __init__(self, mode_config: ModeConfig):
        """
        Initialize ModeFramework with mode configuration
        """
        # Base agent config
        agent_config = AgentConfig(
            agent_id=f"{mode_config.mode_id}-mode",
            agent_name=f"{mode_config.mode_name} Mode Agent",
            agent_type=f"{mode_config.mode_id}_mode",
            capabilities=[
                AgentCapability.ANALYSIS,
                AgentCapability.GENERATION,
                AgentCapability.OPTIMIZATION,
                AgentCapability.VALIDATION,
            ],
            max_concurrent_tasks=mode_config.parameters.get("max_concurrent_tasks", 8),
        )

        super().__init__(agent_config)

        # Mode-specific configuration
        self.mode_config = mode_config

        # Shared components
        self.workflow_engine = WorkflowEngine()
        self.model_router = ModelRouter(mode_config.model_phases)
        self.mcp_client = MCPClient(
            memory_url=self.config.get("mcp_memory_url", "http://localhost:8081"),
            filesystem_url=self.config.get("mcp_filesystem_url", "http://localhost:8082"),
            git_url=self.config.get("mcp_git_url", "http://localhost:8084"),
        )

        # Mode-specific state
        self.workflow_state: Dict[str, Any] = {}
        self.phase_results: Dict[str, Any] = {}
        self.mode_history: List[Dict[str, Any]] = []

        # Logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def _initialize_agent_specific(self) -> None:
        """
        Initialize mode-specific components
        Subclasses can override for additional initialization
        """
        try:
            # Initialize workflow engine
            await self.workflow_engine.initialize()

            # Connect to MCP servers
            await self.mcp_client.connect()

            # Load mode-specific components
            await self._load_mode_components()

            # Initialize workflow state
            self.workflow_state = {
                "current_phase": None,
                "phase_progress": {},
                "intermediate_results": {},
            }

            self.logger.info(f"{self.mode_config.mode_name} Mode initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize {self.mode_config.mode_name}: {str(e)}")
            raise

    async def _load_mode_components(self) -> None:
        """
        Load mode-specific components (override in subclasses)
        This is where subclasses load their unique logic
        """
        # Subclasses should implement this to load their specific components
        # For example, GeneticAlgorithmMode would load GA components
        pass

    async def _process_task_impl(
        self, task_id: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process tasks using the mode's workflow
        Routes to workflow engine and model router
        """
        task_type = task_data.get("task_type", "default_workflow")
        workflow_name = task_data.get("workflow", self.mode_config.mode_id)

        # Get workflow definition
        workflow_steps = self._get_workflow_steps(workflow_name)

        # Execute workflow
        result = await self.workflow_engine.execute_workflow(
            workflow_steps,
            task_data,
            model_router=self.model_router,
            mcp_client=self.mcp_client,
        )

        # Store phase results
        self.phase_results[task_id] = result

        # Save to mode history
        self.mode_history.append({
            "task_id": task_id,
            "workflow": workflow_name,
            "result": result,
            "timestamp": asyncio.get_event_loop().time(),
        })

        return {
            "task_type": task_type,
            "mode": self.mode_config.mode_id,
            "workflow_result": result,
            "phase_results": self.phase_results.get(task_id, {}),
        }

    def _get_workflow_steps(self, workflow_name: str) -> List[Dict[str, Any]]:
        """
        Get workflow steps for the specified workflow
        Subclasses can override to provide dynamic workflows
        """
        # Default to mode config workflow
        steps = self.mode_config.workflow_steps
        model_phases = self.mode_config.model_phases

        # Convert to workflow format
        workflow = []
        for i, step in enumerate(steps):
            phase = step if isinstance(step, str) else step.get("phase", f"phase_{i}")
            actions = step.get("actions", [step]) if isinstance(step, dict) else [step]

            workflow.append({
                "phase": phase,
                "model": model_phases.get(phase, "default"),
                "actions": actions,
                "mcp_hooks": self._get_mcp_hooks_for_phase(phase),
            })

        return workflow

    def _get_mcp_hooks_for_phase(self, phase: str) -> List[str]:
        """
        Get MCP hooks for specific phase
        """
        # Default MCP hooks
        base_hooks = ["log_phase", "save_intermediate"]

        # Mode-specific hooks
        mode_hooks = self.mode_config.mcp_hooks if self.mode_config.mcp_hooks else []

        # Phase-specific hooks
        phase_hooks = []
        if phase == "initialization":
            phase_hooks = ["store_initial_state", "backup_original"]
        elif phase == "evaluation":
            phase_hooks = ["run_tests", "measure_performance"]
        elif phase == "synthesis":
            phase_hooks = ["validate_results", "commit_changes"]

        return base_hooks + [h for h in mode_hooks if h not in phase_hooks]

    async def execute_phase(
        self,
        phase: ModePhase,
        input_data: Dict[str, Any],
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a specific phase of the workflow
        """
        try:
            # Route to appropriate model
            model = model_override or self.model_router.get_model_for_phase(phase.value)
            self.logger.info(f"Executing {phase.value} phase with model: {model}")

            # Execute phase actions
            phase_result = await self._execute_phase_actions(phase, input_data)

            # Run MCP hooks
            hooks = self._get_mcp_hooks_for_phase(phase.value)
            for hook in hooks:
                await self.mcp_client.execute_hook(hook, phase_result)

            return {
                "phase": phase.value,
                "model_used": model,
                "input_data": input_data,
                "output": phase_result,
                "success": True,
            }

        except Exception as e:
            self.logger.error(f"Error in {phase.value} phase: {str(e)}")
            return {
                "phase": phase.value,
                "error": str(e),
                "success": False,
            }

    async def _execute_phase_actions(self, phase: ModePhase, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the actions for a specific phase
        Subclasses implement specific actions
        """
        # Default implementation - subclasses override
        if phase == ModePhase.INITIALIZATION:
            return await self._initialize_phase(input_data)
        elif phase == ModePhase.ANALYSIS:
            return await self._analyze_phase(input_data)
        elif phase == ModePhase.GENERATION:
            return await self._generate_phase(input_data)
        elif phase == ModePhase.EVALUATION:
            return await self._evaluate_phase(input_data)
        elif phase == ModePhase.OPTIMIZATION:
            return await self._optimize_phase(input_data)
        elif phase == ModePhase.SYNTHESIS:
            return await self._synthesize_phase(input_data)
        elif phase == ModePhase.VALIDATION:
            return await self._validate_phase(input_data)
        elif phase == ModePhase.DOCUMENTATION:
            return await self._document_phase(input_data)

        raise ValueError(f"Unknown phase: {phase.value}")

    # Phase implementations (subclasses override these)
    async def _initialize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _initialize_phase")

    async def _analyze_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _analyze_phase")

    async def _generate_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generation phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _generate_phase")

    async def _evaluate_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluation phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _evaluate_phase")

    async def _optimize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimization phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _optimize_phase")

    async def _synthesize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesis phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _synthesize_phase")

    async def _validate_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _validate_phase")

    async def _document_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Documentation phase - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _document_phase")

    async def _cleanup_agent_specific(self) -> None:
        """
        Cleanup mode-specific resources
        """
        try:
            # Save mode history to MCP memory
            await self.mcp_client.store(
                key=f"{self.mode_config.mode_id}_history",
                value=self.mode_history
            )

            # Cleanup workflow state
            self.workflow_state.clear()
            self.phase_results.clear()

            # Call superclass cleanup
            await super()._cleanup_agent_specific()

            self.logger.info(f"{self.mode_config.mode_name} cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during {self.mode_config.mode_name} cleanup: {str(e)}")

    def get_mode_config(self) -> ModeConfig:
        """
        Get the mode configuration
        """
        return self.mode_config

    def get_workflow_state(self, task_id: str) -> Dict[str, Any]:
        """
        Get current workflow state for a task
        """
        return self.workflow_state.get(task_id, {})

    def add_phase_result(self, phase: str, result: Any) -> None:
        """
        Add result from a phase to the workflow state
        """
        if "current_task" not in self.workflow_state:
            self.workflow_state["current_task"] = {}

        self.workflow_state["current_task"][phase] = result

    def get_phase_result(self, task_id: str, phase: str) -> Any:
        """
        Get result from a specific phase
        """
        return self.phase_results.get(task_id, {}).get(phase)

    async def save_mode_state(self, task_id: str) -> None:
        """
        Save current mode state to MCP memory
        """
        state_data = {
            "mode_id": self.mode_config.mode_id,
            "task_id": task_id,
            "workflow_state": self.workflow_state,
            "phase_results": self.phase_results,
            "history": self.mode_history[-10:],  # Last 10 entries
        }
        await self.mcp_client.store(
            key=f"{self.mode_config.mode_id}_{task_id}_state",
            value=state_data
        )

    async def load_mode_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load mode state from MCP memory
        """
        state_data = await self.mcp_client.retrieve(
            key=f"{self.mode_config.mode_id}_{task_id}_state"
        )
        if state_data:
            self.workflow_state = state_data.get("workflow_state", {})
            self.phase_results = state_data.get("phase_results", {})
            self.mode_history.extend(state_data.get("history", [])[-10:])
        return state_data

    def validate_mode_config(self) -> bool:
        """
        Validate mode configuration
        """
        required_fields = [
            "mode_id", "mode_name", "workflow_steps", "model_phases"
        ]
        for field in required_fields:
            if not hasattr(self.mode_config, field):
                self.logger.warning(f"Missing required config field: {field}")
                return False
        return True


# Example usage and factory
def create_mode_agent(mode_config: ModeConfig) -> ModeFramework:
    """
    Factory function to create mode agent from configuration
    Subclasses should provide their own factory
    """
    # This is a base implementation - subclasses override
    if mode_config.mode_id == "genetic-algorithm":
        from agents.specialized.genetic_algorithm_agent import GeneticAlgorithmMode
        return GeneticAlgorithmMode(mode_config)
    elif mode_config.mode_id == "prophecy":
        from agents.specialized.prophecy_agent import ProphecyMode
        return ProphecyMode(mode_config)
    elif mode_config.mode_id == "socratic":
        from agents.specialized.socratic_agent import SocraticMode
        return SocraticMode(mode_config)
    else:
        raise ValueError(f"Unknown mode: {mode_config.mode_id}")

# Base workflow utilities
class WorkflowStep:
    """
    Represents a single step in a mode workflow
    """
    def __init__(
        self,
        phase: ModePhase,
        actions: List[str],
        model: str,
        mcp_hooks: List[str] = None
    ):
        self.phase = phase
        self.actions = actions
        self.model = model
        self.mcp_hooks = mcp_hooks or []
        self.input_data = None
        self.output_data = None
        self.execution_time = 0.0
        self.success = False


class ModeFactory:
    """
    Factory for creating and configuring modes
    """
    @staticmethod
    def generate_config(
        mode_id: str,
        mode_name: str,
        workflow_steps: List[str],
        model_phases: Dict[str, str],
        parameters: Dict[str, Any] = None
    ) -> ModeConfig:
        """
        Generate mode configuration
        """
        return ModeConfig(
            mode_id=mode_id,
            mode_name=mode_name,
            workflow_steps=workflow_steps,
            model_phases=model_phases,
            parameters=parameters or {}
        )

    @staticmethod
    def create_from_json(config_path: str) -> ModeFramework:
        """
        Create mode from JSON configuration file
        """
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

        mode_config = ModeConfig(**config_dict)
        return create_mode_agent(mode_config)

    @staticmethod
    def get_recommended_models(phase: ModePhase) -> List[str]:
        """
        Get recommended models for a phase
        """
        recommendations = {
            ModePhase.INITIALIZATION: ["claude-opus-4.1", "chatgpt-5"],
            ModePhase.ANALYSIS: ["llama-scout-4", "deepseek-v3"],
            ModePhase.GENERATION: ["grok-5", "grok-code-fast-1"],
            ModePhase.EVALUATION: ["deepseek-v3", "google-flash-2.5"],
            ModePhase.OPTIMIZATION: ["google-flash-2.5", "grok-5"],
            ModePhase.SYNTHESIS: ["claude-opus-4.1", "chatgpt-5"],
            ModePhase.VALIDATION: ["deepseek-v3"],
            ModePhase.DOCUMENTATION: ["claude-opus-4.1"],
        }
        return recommendations.get(phase, ["default"])


if __name__ == "__main__":
    # Example usage
    config = ModeFactory.generate_config(
        mode_id="example-mode",
        mode_name="Example Mode",
        workflow_steps=["initialization", "analysis", "synthesis"],
        model_phases={
            "initialization": "claude-opus-4.1",
            "analysis": "llama-scout-4",
            "synthesis": "claude-opus-4.1"
        },
        parameters={"max_concurrent_tasks": 4}
    )

    agent = create_mode_agent(config)