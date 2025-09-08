"""
Base Agent Interfaces

Defines abstract base classes and data structures for AI agents,
including agent lifecycle, capabilities, and interaction patterns.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

from ..memory.base import MemoryManager
from ..models.base import BaseModel as LLMModel
from ..models.base import ConversationHistory
from ..tools.base import ToolExecutionContext, ToolRegistry

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AgentState(str, Enum):
    """Agent lifecycle states."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    COMMUNICATING = "communicating"
    LEARNING = "learning"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AgentCapabilities(BaseModel):
    """
    Defines agent capabilities and limitations.
    """

    # Communication capabilities
    can_communicate: bool = True
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    max_message_length: int = 4000

    # Cognitive capabilities
    can_reason: bool = True
    can_plan: bool = True
    can_learn: bool = True
    can_remember: bool = True

    # Action capabilities
    can_use_tools: bool = True
    can_access_internet: bool = False
    can_modify_files: bool = False
    can_execute_code: bool = False

    # Interaction capabilities
    can_collaborate: bool = True
    can_delegate: bool = False
    can_supervise: bool = False

    # Resource limits
    max_concurrent_tasks: int = 5
    max_memory_entries: int = 1000
    max_tool_calls_per_turn: int = 10
    execution_timeout_seconds: int = 300

    # Specialized capabilities
    domain_expertise: List[str] = Field(default_factory=list)
    supported_file_types: List[str] = Field(default_factory=list)

    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle a specific task type."""
        task_capabilities = {
            "conversation": self.can_communicate,
            "reasoning": self.can_reason,
            "planning": self.can_plan,
            "tool_use": self.can_use_tools,
            "collaboration": self.can_collaborate,
            "learning": self.can_learn,
            "file_modification": self.can_modify_files,
            "code_execution": self.can_execute_code,
            "web_access": self.can_access_internet,
        }

        return task_capabilities.get(task_type, False)


class AgentConfig(BaseModel):
    """
    Agent configuration and initialization parameters.
    """

    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""

    # Model configuration
    model_name: str = "gpt-3.5-turbo"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, gt=0)

    # Behavior configuration
    system_prompt: str = ""
    personality_traits: List[str] = Field(default_factory=list)
    response_style: str = "helpful"  # helpful, creative, analytical, etc.

    # Capabilities
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)

    # Memory configuration
    memory_enabled: bool = True
    memory_types: List[str] = Field(default_factory=lambda: ["working", "episodic"])
    memory_retention_hours: int = 24

    # Tool configuration
    available_tools: List[str] = Field(default_factory=list)
    tool_categories: List[str] = Field(default_factory=list)

    # Performance settings
    response_timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60

    # Context settings
    max_context_messages: int = 20
    context_window_tokens: int = 4000

    def validate_configuration(self) -> List[str]:
        """
        Validate agent configuration and return issues.

        Returns:
            List[str]: List of validation issues
        """
        issues = []

        if not self.name.strip():
            issues.append("Agent name cannot be empty")

        if self.max_tokens > self.context_window_tokens:
            issues.append("max_tokens cannot exceed context_window_tokens")

        if self.response_timeout <= 0:
            issues.append("response_timeout must be positive")

        if self.memory_enabled and not self.memory_types:
            issues.append("memory_enabled but no memory_types specified")

        return issues


class AgentMessage(BaseModel):
    """
    Message sent to or from an agent.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    sender_id: str
    recipient_id: str
    content: str
    message_type: str = "text"  # text, command, query, response

    # Metadata
    priority: int = Field(0, ge=0, le=10)  # 0 = low, 10 = critical
    requires_response: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def set_expiration(self, seconds: int) -> None:
        """Set message expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(seconds=seconds)


class AgentResponse(BaseModel):
    """
    Response from an agent.
    """

    agent_id: str
    response_to: Optional[str] = None  # Message ID being responded to
    content: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)

    # Response metadata
    reasoning: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

    # Performance metrics
    response_time: float = 0.0
    tokens_used: int = 0

    # Follow-up information
    requires_followup: bool = False
    suggested_actions: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentGoal(BaseModel):
    """
    High-level goal for an agent.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    priority: int = Field(5, ge=1, le=10)

    # Goal metadata
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    estimated_effort: Optional[int] = None  # hours

    # Status tracking
    status: str = "active"  # active, completed, cancelled, paused
    progress: float = Field(0.0, ge=0.0, le=1.0)

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # Goal IDs
    blocks: List[str] = Field(default_factory=list)  # Goal IDs

    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        return (
            self.deadline is not None
            and self.status != "completed"
            and datetime.utcnow() > self.deadline
        )

    def mark_completed(self) -> None:
        """Mark goal as completed."""
        self.status = "completed"
        self.progress = 1.0


class AgentTask(BaseModel):
    """
    Specific task for an agent to execute.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    task_type: str  # conversation, tool_use, reasoning, etc.

    # Task parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Status and timing
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution details
    agent_id: Optional[str] = None
    parent_goal_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Results
    result: Optional[Any] = None
    error: Optional[str] = None

    def start_execution(self, agent_id: str) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.agent_id = agent_id
        self.started_at = datetime.utcnow()

    def complete_with_result(self, result: Any) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()

    def fail_with_error(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    @property
    def execution_time(self) -> Optional[float]:
        """Get task execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries


class AgentContext(BaseModel):
    """
    Context information for agent operation.
    """

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None

    # Environment context
    environment: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)

    # Conversation context
    conversation_history: Optional[ConversationHistory] = None
    current_topic: Optional[str] = None

    # Task context
    current_goals: List[str] = Field(default_factory=list)  # Goal IDs
    active_tasks: List[str] = Field(default_factory=list)  # Task IDs

    # Memory context
    relevant_memories: List[str] = Field(default_factory=list)  # Memory IDs
    memory_search_context: Optional[str] = None

    # Timing context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_goal(self, goal_id: str) -> None:
        """Add goal to current goals."""
        if goal_id not in self.current_goals:
            self.current_goals.append(goal_id)

    def remove_goal(self, goal_id: str) -> None:
        """Remove goal from current goals."""
        if goal_id in self.current_goals:
            self.current_goals.remove(goal_id)


# Exception classes
class AgentError(Exception):
    """Base class for agent errors."""

    pass


class AgentInitializationError(AgentError):
    """Raised when agent initialization fails."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.
    """

    def __init__(
        self,
        config: AgentConfig,
        model: Optional[LLMModel] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        """
        Initialize agent with configuration and dependencies.

        Args:
            config: Agent configuration
            model: Language model instance
            memory_manager: Memory system manager
            tool_registry: Tool registry
        """
        # Validate configuration
        config_issues = config.validate_configuration()
        if config_issues:
            raise AgentInitializationError(f"Configuration issues: {config_issues}")

        self.config = config
        self.model = model
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry

        # Agent state
        self.state = AgentState.INITIALIZING
        self.context: Optional[AgentContext] = None

        # Goals and tasks
        self._goals: Dict[str, AgentGoal] = {}
        self._tasks: Dict[str, AgentTask] = {}

        # Performance tracking
        self._message_count = 0
        self._total_response_time = 0.0
        self._error_count = 0

        logger.info(f"Initialized agent {config.name} ({config.agent_id})")

    @abstractmethod
    async def process_message(
        self, message: AgentMessage, context: AgentContext
    ) -> AgentResponse:
        """
        Process an incoming message and generate response.

        Args:
            message: Incoming message
            context: Current agent context

        Returns:
            AgentResponse: Generated response

        Raises:
            AgentExecutionError: If processing fails
        """
        pass

    async def initialize(self) -> None:
        """
        Initialize the agent and prepare for operation.

        Raises:
            AgentInitializationError: If initialization fails
        """
        try:
            self.state = AgentState.INITIALIZING

            # Initialize memory if enabled
            if self.config.memory_enabled and self.memory_manager:
                await self._initialize_memory()

            # Initialize available tools
            if self.config.available_tools and self.tool_registry:
                await self._initialize_tools()

            # Load initial system prompt if model available
            if self.model and self.config.system_prompt:
                await self._initialize_system_prompt()

            self.state = AgentState.IDLE
            logger.info(f"Agent {self.config.name} initialized successfully")

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"Agent {self.config.name} initialization failed: {e}")
            raise AgentInitializationError(f"Initialization failed: {e}")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent.
        """
        try:
            # Cancel active tasks
            for task in self._tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED

            # Save memory state if needed
            if self.memory_manager:
                await self._save_memory_state()

            self.state = AgentState.TERMINATED
            logger.info(f"Agent {self.config.name} shutdown completed")

        except Exception as e:
            logger.error(f"Agent {self.config.name} shutdown error: {e}")
            self.state = AgentState.ERROR

    async def add_goal(self, goal: AgentGoal) -> None:
        """
        Add a goal to the agent.

        Args:
            goal: Goal to add
        """
        self._goals[goal.id] = goal

        if self.context:
            self.context.add_goal(goal.id)

        logger.info(f"Added goal '{goal.title}' to agent {self.config.name}")

    async def complete_goal(self, goal_id: str) -> bool:
        """
        Mark a goal as completed.

        Args:
            goal_id: Goal ID to complete

        Returns:
            bool: True if goal was completed
        """
        if goal_id in self._goals:
            self._goals[goal_id].mark_completed()

            if self.context:
                self.context.remove_goal(goal_id)

            logger.info(f"Completed goal {goal_id} for agent {self.config.name}")
            return True

        return False

    async def add_task(self, task: AgentTask) -> None:
        """
        Add a task to the agent.

        Args:
            task: Task to add
        """
        self._tasks[task.id] = task

        if self.context:
            self.context.active_tasks.append(task.id)

        logger.debug(f"Added task '{task.title}' to agent {self.config.name}")

    async def execute_task(self, task_id: str) -> bool:
        """
        Execute a specific task.

        Args:
            task_id: Task ID to execute

        Returns:
            bool: True if task execution started successfully
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        if task.status != TaskStatus.PENDING:
            return False

        try:
            task.start_execution(self.config.agent_id)
            result = await self._execute_task_implementation(task)
            task.complete_with_result(result)

            logger.info(f"Completed task {task_id} for agent {self.config.name}")
            return True

        except Exception as e:
            task.fail_with_error(str(e))
            logger.error(f"Task {task_id} failed for agent {self.config.name}: {e}")
            return False

    async def _execute_task_implementation(self, task: AgentTask) -> Any:
        """
        Execute task implementation (to be overridden by subclasses).

        Args:
            task: Task to execute

        Returns:
            Any: Task result
        """
        # Default implementation - subclasses should override
        if task.task_type == "conversation":
            return await self._handle_conversation_task(task)
        elif task.task_type == "tool_use":
            return await self._handle_tool_task(task)
        else:
            raise AgentExecutionError(f"Unsupported task type: {task.task_type}")

    async def _handle_conversation_task(self, task: AgentTask) -> str:
        """Handle conversation task."""
        # Simple echo for base implementation
        return f"Processed conversation task: {task.description}"

    async def _handle_tool_task(self, task: AgentTask) -> Any:
        """Handle tool execution task."""
        if not self.tool_registry:
            raise AgentExecutionError("Tool registry not available")

        tool_name = task.parameters.get("tool_name")
        tool_params = task.parameters.get("parameters", {})

        if not tool_name:
            raise AgentExecutionError("Tool name not specified")

        # Create execution context
        exec_context = ToolExecutionContext(
            agent_id=self.config.agent_id,
            session_id=self.context.session_id if self.context else None,
        )

        # Execute tool
        result = await self.tool_registry.execute_tool(
            tool_name, tool_params, exec_context
        )

        return result

    async def _initialize_memory(self) -> None:
        """Initialize memory systems."""
        if not self.memory_manager:
            return

        # Register memory types based on configuration
        for memory_type in self.config.memory_types:
            if memory_type == "working":
                from ..memory.base import WorkingMemory

                working_memory = WorkingMemory(max_entries=100)
                self.memory_manager.register_memory(working_memory)
            elif memory_type == "episodic":
                from ..memory.base import EpisodicMemory

                episodic_memory = EpisodicMemory(max_entries=500)
                self.memory_manager.register_memory(episodic_memory)
            elif memory_type == "semantic":
                from ..memory.base import SemanticMemory

                semantic_memory = SemanticMemory(max_entries=1000)
                self.memory_manager.register_memory(semantic_memory)

        logger.info(f"Initialized memory systems: {self.config.memory_types}")

    async def _initialize_tools(self) -> None:
        """Initialize available tools."""
        if not self.tool_registry:
            return

        available_tools = []
        for tool_name in self.config.available_tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                available_tools.append(tool_name)

        logger.info(f"Initialized tools: {available_tools}")

    async def _initialize_system_prompt(self) -> None:
        """Initialize system prompt in model."""
        # This would be implemented based on specific model interface
        logger.info("Initialized system prompt")

    async def _save_memory_state(self) -> None:
        """Save current memory state."""
        # Implementation depends on memory persistence layer
        logger.debug("Saved memory state")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Dict[str, Any]: Agent status information
        """
        avg_response_time = (
            self._total_response_time / self._message_count
            if self._message_count > 0
            else 0.0
        )

        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "state": self.state.value,
            "capabilities": self.config.capabilities.dict(),
            "goals": {
                "total": len(self._goals),
                "active": len(
                    [g for g in self._goals.values() if g.status == "active"]
                ),
                "completed": len(
                    [g for g in self._goals.values() if g.status == "completed"]
                ),
            },
            "tasks": {
                "total": len(self._tasks),
                "pending": len(
                    [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
                ),
                "running": len(
                    [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
                ),
                "completed": len(
                    [
                        t
                        for t in self._tasks.values()
                        if t.status == TaskStatus.COMPLETED
                    ]
                ),
            },
            "performance": {
                "message_count": self._message_count,
                "average_response_time": avg_response_time,
                "error_count": self._error_count,
            },
        }


class ConversationalAgent(BaseAgent):
    """
    Agent specialized for conversational interactions.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._conversation_history = ConversationHistory()

    async def process_message(
        self, message: AgentMessage, context: AgentContext
    ) -> AgentResponse:
        """Process conversational message."""
        start_time = datetime.utcnow()
        self.state = AgentState.COMMUNICATING

        try:
            # Update context
            self.context = context
            context.update_activity()

            # Store message in conversation history
            from ..models.base import Message, MessageRole

            user_message = Message(
                role=MessageRole.USER,
                content=message.content,
                metadata={"message_id": message.id},
            )
            self._conversation_history.add_message(user_message)

            # Generate response using model
            if self.model:
                response = await self.model.chat(
                    self._conversation_history,
                    # Add model parameters based on config
                )

                response_content = response.content or "I couldn't generate a response."
            else:
                response_content = f"Echo: {message.content}"

            # Create agent response
            response_time = (datetime.utcnow() - start_time).total_seconds()

            agent_response = AgentResponse(
                agent_id=self.config.agent_id,
                response_to=message.id,
                content=response_content,
                response_time=response_time,
            )

            # Update performance metrics
            self._message_count += 1
            self._total_response_time += response_time

            self.state = AgentState.IDLE
            return agent_response

        except Exception as e:
            self._error_count += 1
            self.state = AgentState.ERROR

            logger.error(f"Conversational agent error: {e}")

            return AgentResponse(
                agent_id=self.config.agent_id,
                response_to=message.id,
                content=f"I encountered an error: {str(e)}",
                confidence=0.0,
                response_time=(datetime.utcnow() - start_time).total_seconds(),
            )


class ReactiveTool(BaseAgent):
    """
    Agent that reacts to messages by using tools.
    """

    async def process_message(
        self, message: AgentMessage, context: AgentContext
    ) -> AgentResponse:
        """Process message by determining and using appropriate tools."""
        start_time = datetime.utcnow()
        self.state = AgentState.ACTING

        try:
            # Analyze message to determine needed tools
            tools_to_use = await self._analyze_message_for_tools(message)

            results = []
            for tool_name, params in tools_to_use:
                if self.tool_registry:
                    exec_context = ToolExecutionContext(
                        agent_id=self.config.agent_id, session_id=context.session_id
                    )

                    result = await self.tool_registry.execute_tool(
                        tool_name, params, exec_context
                    )
                    results.append(
                        f"{tool_name}: {result.result if result.success else result.error}"
                    )

            response_content = (
                "Tool results:\n" + "\n".join(results)
                if results
                else "No tools were used."
            )

            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.state = AgentState.IDLE

            return AgentResponse(
                agent_id=self.config.agent_id,
                response_to=message.id,
                content=response_content,
                response_time=response_time,
                tool_calls=[
                    {"tool": tool, "params": params} for tool, params in tools_to_use
                ],
            )

        except Exception as e:
            self._error_count += 1
            self.state = AgentState.ERROR

            return AgentResponse(
                agent_id=self.config.agent_id,
                response_to=message.id,
                content=f"Tool execution failed: {str(e)}",
                confidence=0.0,
                response_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def _analyze_message_for_tools(
        self, message: AgentMessage
    ) -> List[tuple[str, Dict[str, Any]]]:
        """
        Analyze message to determine which tools to use.

        Args:
            message: Message to analyze

        Returns:
            List[tuple[str, Dict[str, Any]]]: Tools and parameters to use
        """
        # Simple keyword-based tool selection for base implementation
        tools_to_use = []

        content_lower = message.content.lower()

        if "weather" in content_lower and self.tool_registry:
            if self.tool_registry.get_tool("get_weather"):
                tools_to_use.append(("get_weather", {"location": "default"}))

        if "search" in content_lower and self.tool_registry:
            if self.tool_registry.get_tool("web_search"):
                tools_to_use.append(("web_search", {"query": message.content}))

        return tools_to_use


class ProactiveAgent(BaseAgent):
    """
    Agent that proactively pursues goals and initiates actions.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._planning_interval = 60  # seconds
        self._last_planning = None

    async def process_message(
        self, message: AgentMessage, context: AgentContext
    ) -> AgentResponse:
        """Process message and potentially trigger proactive planning."""
        # First handle the immediate message
        response = await self._handle_immediate_response(message, context)

        # Then consider proactive actions
        await self._consider_proactive_actions(context)

        return response

    async def _handle_immediate_response(
        self, message: AgentMessage, context: AgentContext
    ) -> AgentResponse:
        """Handle immediate response to message."""
        # Simple acknowledgment for base implementation
        return AgentResponse(
            agent_id=self.config.agent_id,
            response_to=message.id,
            content=f"I've received your message: {message.content[:100]}...",
        )

    async def _consider_proactive_actions(self, context: AgentContext) -> None:
        """Consider whether to take proactive actions."""
        current_time = datetime.utcnow()

        # Check if it's time for planning
        if (
            self._last_planning is None
            or (current_time - self._last_planning).total_seconds()
            > self._planning_interval
        ):

            await self._proactive_planning(context)
            self._last_planning = current_time

    async def _proactive_planning(self, context: AgentContext) -> None:
        """Execute proactive planning cycle."""
        self.state = AgentState.THINKING

        try:
            # Review current goals
            active_goals = [g for g in self._goals.values() if g.status == "active"]

            # Create tasks for goals that need attention
            for goal in active_goals:
                if not self._has_active_tasks_for_goal(goal.id):
                    await self._create_tasks_for_goal(goal)

            logger.info(f"Proactive agent {self.config.name} completed planning cycle")

        except Exception as e:
            logger.error(f"Proactive planning failed: {e}")
        finally:
            self.state = AgentState.IDLE

    def _has_active_tasks_for_goal(self, goal_id: str) -> bool:
        """Check if goal has active tasks."""
        return any(
            t.parent_goal_id == goal_id
            and t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
            for t in self._tasks.values()
        )

    async def _create_tasks_for_goal(self, goal: AgentGoal) -> None:
        """Create tasks to work towards a goal."""
        # Simple task creation for base implementation
        task = AgentTask(
            title=f"Work on goal: {goal.title}",
            description=f"Task to make progress on goal: {goal.description}",
            task_type="reasoning",
            parent_goal_id=goal.id,
        )

        await self.add_task(task)
        logger.info(f"Created task {task.id} for goal {goal.id}")


class AgentRegistry:
    """
    Registry for managing multiple agents.
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        logger.info("Initialized agent registry")

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent.

        Args:
            agent: Agent to register
        """
        agent_id = agent.config.agent_id
        self._agents[agent_id] = agent
        logger.info(f"Registered agent {agent.config.name} ({agent_id})")

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.

        Args:
            agent_id: Agent ID to unregister

        Returns:
            bool: True if agent was unregistered
        """
        if agent_id in self._agents:
            agent = self._agents.pop(agent_id)
            logger.info(f"Unregistered agent {agent.config.name} ({agent_id})")
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Optional[BaseAgent]: Agent if found
        """
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.

        Returns:
            List[str]: Agent IDs
        """
        return list(self._agents.keys())

    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """
        Get agents that have a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List[BaseAgent]: Agents with the capability
        """
        capable_agents = []

        for agent in self._agents.values():
            if agent.config.capabilities.can_handle_task(capability):
                capable_agents.append(agent)

        return capable_agents

    async def broadcast_message(
        self, message: AgentMessage
    ) -> Dict[str, AgentResponse]:
        """
        Broadcast message to all agents.

        Args:
            message: Message to broadcast

        Returns:
            Dict[str, AgentResponse]: Responses by agent ID
        """
        responses = {}

        for agent_id, agent in self._agents.items():
            if agent.state not in [AgentState.TERMINATED, AgentState.ERROR]:
                try:
                    context = AgentContext(session_id=str(uuid4()))
                    response = await agent.process_message(message, context)
                    responses[agent_id] = response
                except Exception as e:
                    logger.error(f"Error broadcasting to agent {agent_id}: {e}")

        return responses

    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get registry status information.

        Returns:
            Dict[str, Any]: Registry status
        """
        agents_by_state = {}
        for agent in self._agents.values():
            state = agent.state.value
            agents_by_state[state] = agents_by_state.get(state, 0) + 1

        return {
            "total_agents": len(self._agents),
            "agents_by_state": agents_by_state,
            "agent_details": {
                agent_id: agent.get_status() for agent_id, agent in self._agents.items()
            },
        }
