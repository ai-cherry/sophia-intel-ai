"""
Execution Store - Task execution history and context memory
Stores task execution logs, workflow states, and operational context
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.unified_memory import (
    MemoryContext,
    MemoryMetadata,
    MemoryPriority,
    unified_memory,
)

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status types"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ExecutionType(Enum):
    """Types of execution contexts"""

    SWARM_TASK = "swarm_task"
    AGENT_ACTION = "agent_action"
    WORKFLOW_STEP = "workflow_step"
    API_CALL = "api_call"
    DATA_PROCESSING = "data_processing"
    ANALYSIS_JOB = "analysis_job"
    SYSTEM_OPERATION = "system_operation"
    USER_REQUEST = "user_request"


@dataclass
class ExecutionContext:
    """Detailed execution context"""

    execution_id: str
    task_name: str
    execution_type: ExecutionType
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Execution details
    agent_id: Optional[str] = None
    swarm_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    child_execution_ids: list[str] = field(default_factory=list)

    # Parameters and results
    input_parameters: dict[str, Any] = field(default_factory=dict)
    output_results: dict[str, Any] = field(default_factory=dict)
    error_details: Optional[dict[str, Any]] = None

    # Performance metrics
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    api_calls_made: int = 0
    tokens_consumed: int = 0
    cost_usd: Optional[float] = None

    # Context and metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    priority: int = 5  # 1-10 scale
    retry_count: int = 0
    max_retries: int = 3


class ExecutionStore:
    """
    Specialized memory store for execution history and context
    Optimized for workflow tracking, debugging, and performance analysis
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.namespace = "execution"

    async def store_execution(
        self, execution: ExecutionContext, domain: Optional[str] = None
    ) -> str:
        """Store execution context and history"""

        # Create comprehensive content for storage
        content = self._format_execution_content(execution)

        # Create metadata with execution-specific attributes
        metadata = MemoryMetadata(
            memory_id=execution.execution_id,
            context=MemoryContext.EXECUTION,
            priority=self._determine_priority(execution),
            tags=execution.tags.union(
                {
                    execution.execution_type.value,
                    execution.status.value,
                    f"agent_{execution.agent_id}" if execution.agent_id else "no_agent",
                    f"swarm_{execution.swarm_id}" if execution.swarm_id else "no_swarm",
                }
            ),
            user_id=execution.user_id,
            session_id=execution.session_id,
            domain=domain,
            source="execution_store",
            ttl_seconds=self._determine_ttl(execution),
        )

        # Store in unified memory
        memory_id = await self.memory_interface.store(content, metadata)

        # Store structured execution data for complex queries
        await self._store_structured_execution(memory_id, execution)

        # Update execution hierarchy if applicable
        await self._update_execution_hierarchy(execution)

        logger.debug(f"Stored execution context: {execution.task_name} ({memory_id})")
        return memory_id

    async def retrieve_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a specific execution context"""
        entry = await self.memory_interface.retrieve(execution_id)
        if not entry:
            return None

        # Get structured data
        structured_data = await self._retrieve_structured_execution(execution_id)

        return {
            "memory_id": execution_id,
            "content": entry.content,
            "metadata": entry.metadata,
            "execution_context": structured_data,
        }

    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        end_time: Optional[datetime] = None,
        output_results: Optional[dict[str, Any]] = None,
        error_details: Optional[dict[str, Any]] = None,
        performance_metrics: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update execution status and results"""

        # Retrieve current execution
        current_execution = await self._retrieve_structured_execution(execution_id)
        if not current_execution:
            logger.warning(f"Execution {execution_id} not found for status update")
            return False

        # Update status and timing
        current_execution["status"] = status.value
        if end_time:
            current_execution["end_time"] = end_time.isoformat()
            start_time = datetime.fromisoformat(current_execution["start_time"])
            duration = (end_time - start_time).total_seconds()
            current_execution["duration_seconds"] = duration

        # Update results and errors
        if output_results:
            current_execution["output_results"] = output_results
        if error_details:
            current_execution["error_details"] = error_details

        # Update performance metrics
        if performance_metrics:
            current_execution.update(performance_metrics)

        # Store updated data
        await self._store_structured_execution(execution_id, None, current_execution)

        # Update content in unified memory
        updated_content = self._format_execution_content_from_dict(current_execution)
        success = await self.memory_interface.update(
            execution_id, content=updated_content
        )

        if success:
            logger.debug(f"Updated execution status: {execution_id} -> {status.value}")

        return success

    async def search_executions(
        self,
        query: str,
        execution_types: Optional[list[ExecutionType]] = None,
        status_filter: Optional[list[ExecutionStatus]] = None,
        agent_filter: Optional[str] = None,
        swarm_filter: Optional[str] = None,
        date_range: Optional[tuple] = None,
        max_results: int = 20,
        domain: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Search execution history with advanced filtering"""

        # Build search tags
        search_tags = set()
        if execution_types:
            search_tags.update([t.value for t in execution_types])
        if status_filter:
            search_tags.update([s.value for s in status_filter])
        if agent_filter:
            search_tags.add(f"agent_{agent_filter}")
        if swarm_filter:
            search_tags.add(f"swarm_{swarm_filter}")

        # Search unified memory
        from app.core.unified_memory import MemoryContext, MemorySearchRequest

        search_request = MemorySearchRequest(
            query=query,
            context_filter=[MemoryContext.EXECUTION],
            tag_filter=search_tags if search_tags else None,
            domain_filter=domain,
            max_results=max_results,
            similarity_threshold=0.6,
        )

        results = await self.memory_interface.search(search_request)

        # Enhance results with structured data and apply date filtering
        enhanced_results = []
        for result in results:
            structured_data = await self._retrieve_structured_execution(
                result.memory_id
            )

            # Apply date range filter
            if date_range and structured_data:
                start_time = datetime.fromisoformat(structured_data["start_time"])
                if not (date_range[0] <= start_time <= date_range[1]):
                    continue

            enhanced_results.append(
                {
                    "memory_id": result.memory_id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "relevance_score": result.relevance_score,
                    "execution_context": structured_data,
                }
            )

        return enhanced_results

    async def get_execution_analytics(
        self, time_period_hours: int = 24, domain: Optional[str] = None
    ) -> dict[str, Any]:
        """Get execution analytics and performance metrics"""

        # Search for recent executions
        cutoff_time = datetime.now(timezone.utc)
        start_time = cutoff_time.replace(hour=cutoff_time.hour - time_period_hours)

        recent_executions = await self.search_executions(
            query="execution analytics",
            date_range=(start_time, cutoff_time),
            max_results=1000,
            domain=domain,
        )

        # Analyze execution patterns
        analytics = {
            "time_period_hours": time_period_hours,
            "total_executions": len(recent_executions),
            "by_status": {status.value: 0 for status in ExecutionStatus},
            "by_type": {exec_type.value: 0 for exec_type in ExecutionType},
            "performance_metrics": {
                "avg_duration_seconds": 0,
                "total_api_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "success_rate": 0,
            },
            "agent_activity": {},
            "swarm_activity": {},
            "error_analysis": {"top_errors": [], "error_rate": 0},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        durations = []
        total_cost = 0
        total_tokens = 0
        total_api_calls = 0
        error_count = 0
        errors = {}

        for execution in recent_executions:
            context = execution.get("execution_context", {})

            # Count by status
            status = context.get("status", "unknown")
            if status in analytics["by_status"]:
                analytics["by_status"][status] += 1

            # Count by type
            exec_type = context.get("execution_type", "unknown")
            if exec_type in analytics["by_type"]:
                analytics["by_type"][exec_type] += 1

            # Collect performance metrics
            if context.get("duration_seconds"):
                durations.append(context["duration_seconds"])

            total_cost += context.get("cost_usd", 0)
            total_tokens += context.get("tokens_consumed", 0)
            total_api_calls += context.get("api_calls_made", 0)

            # Track agent activity
            agent_id = context.get("agent_id")
            if agent_id:
                analytics["agent_activity"][agent_id] = (
                    analytics["agent_activity"].get(agent_id, 0) + 1
                )

            # Track swarm activity
            swarm_id = context.get("swarm_id")
            if swarm_id:
                analytics["swarm_activity"][swarm_id] = (
                    analytics["swarm_activity"].get(swarm_id, 0) + 1
                )

            # Track errors
            if status == "failed":
                error_count += 1
                error_details = context.get("error_details", {})
                error_type = error_details.get("type", "unknown_error")
                errors[error_type] = errors.get(error_type, 0) + 1

        # Calculate performance metrics
        if durations:
            analytics["performance_metrics"]["avg_duration_seconds"] = sum(
                durations
            ) / len(durations)

        analytics["performance_metrics"]["total_api_calls"] = total_api_calls
        analytics["performance_metrics"]["total_tokens"] = total_tokens
        analytics["performance_metrics"]["total_cost_usd"] = round(total_cost, 4)

        if len(recent_executions) > 0:
            success_count = analytics["by_status"].get("completed", 0)
            analytics["performance_metrics"]["success_rate"] = round(
                success_count / len(recent_executions), 3
            )

        # Error analysis
        analytics["error_analysis"]["error_rate"] = (
            round(error_count / len(recent_executions), 3) if recent_executions else 0
        )
        analytics["error_analysis"]["top_errors"] = sorted(
            errors.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return analytics

    async def get_execution_hierarchy(self, root_execution_id: str) -> dict[str, Any]:
        """Get full execution hierarchy tree"""

        root_execution = await self._retrieve_structured_execution(root_execution_id)
        if not root_execution:
            return None

        # Build hierarchy recursively
        hierarchy = await self._build_execution_tree(root_execution_id, root_execution)

        return {
            "root_execution_id": root_execution_id,
            "hierarchy": hierarchy,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def cleanup_old_executions(self, days_old: int = 30) -> int:
        """Clean up old execution records to manage storage"""

        datetime.now(timezone.utc).replace(day=datetime.now().day - days_old)

        # This would be implemented with a more efficient bulk deletion
        # For now, return 0 as placeholder
        return 0

    # Private helper methods

    def _format_execution_content(self, execution: ExecutionContext) -> str:
        """Format execution context into comprehensive text content"""

        content_parts = [
            f"EXECUTION RECORD: {execution.task_name}",
            f"ID: {execution.execution_id}",
            f"TYPE: {execution.execution_type.value}",
            f"STATUS: {execution.status.value}",
            "",
            f"START TIME: {execution.start_time.isoformat()}",
        ]

        if execution.end_time:
            content_parts.extend(
                [
                    f"END TIME: {execution.end_time.isoformat()}",
                    f"DURATION: {execution.duration_seconds:.2f} seconds",
                ]
            )

        if execution.agent_id:
            content_parts.append(f"AGENT: {execution.agent_id}")

        if execution.swarm_id:
            content_parts.append(f"SWARM: {execution.swarm_id}")

        if execution.workflow_id:
            content_parts.append(f"WORKFLOW: {execution.workflow_id}")

        content_parts.append("")

        if execution.input_parameters:
            content_parts.extend(
                ["INPUT PARAMETERS:", str(execution.input_parameters), ""]
            )

        if execution.output_results:
            content_parts.extend(["OUTPUT RESULTS:", str(execution.output_results), ""])

        if execution.error_details:
            content_parts.extend(["ERROR DETAILS:", str(execution.error_details), ""])

        # Performance metrics
        perf_parts = []
        if execution.cpu_usage_percent:
            perf_parts.append(f"CPU: {execution.cpu_usage_percent}%")
        if execution.memory_usage_mb:
            perf_parts.append(f"Memory: {execution.memory_usage_mb}MB")
        if execution.tokens_consumed:
            perf_parts.append(f"Tokens: {execution.tokens_consumed}")
        if execution.cost_usd:
            perf_parts.append(f"Cost: ${execution.cost_usd:.4f}")

        if perf_parts:
            content_parts.extend(["PERFORMANCE METRICS:", " | ".join(perf_parts), ""])

        if execution.child_execution_ids:
            content_parts.extend(
                [f"CHILD EXECUTIONS: {', '.join(execution.child_execution_ids)}", ""]
            )

        return "\n".join(content_parts)

    def _format_execution_content_from_dict(
        self, execution_dict: dict[str, Any]
    ) -> str:
        """Format execution dictionary into content (for updates)"""

        content_parts = [
            f"EXECUTION RECORD: {execution_dict.get('task_name', 'Unknown')}",
            f"ID: {execution_dict.get('execution_id', 'Unknown')}",
            f"TYPE: {execution_dict.get('execution_type', 'unknown')}",
            f"STATUS: {execution_dict.get('status', 'unknown')}",
            "",
            f"START TIME: {execution_dict.get('start_time', 'Unknown')}",
        ]

        if execution_dict.get("end_time"):
            content_parts.extend(
                [
                    f"END TIME: {execution_dict['end_time']}",
                    f"DURATION: {execution_dict.get('duration_seconds', 0):.2f} seconds",
                ]
            )

        return "\n".join(content_parts)

    def _determine_priority(self, execution: ExecutionContext) -> MemoryPriority:
        """Determine memory priority based on execution characteristics"""

        if (
            execution.priority >= 8
            or execution.execution_type == ExecutionType.SYSTEM_OPERATION
        ):
            return MemoryPriority.HIGH
        elif execution.priority >= 6:
            return MemoryPriority.STANDARD
        else:
            return MemoryPriority.LOW

    def _determine_ttl(self, execution: ExecutionContext) -> int:
        """Determine TTL based on execution type and importance"""

        if execution.execution_type in [
            ExecutionType.SYSTEM_OPERATION,
            ExecutionType.WORKFLOW_STEP,
        ]:
            return 86400 * 7  # 7 days for system operations
        elif execution.status == ExecutionStatus.FAILED:
            return 86400 * 30  # 30 days for failed executions (debugging)
        else:
            return 86400 * 3  # 3 days for normal executions

    async def _store_structured_execution(
        self,
        memory_id: str,
        execution: Optional[ExecutionContext],
        execution_dict: Optional[dict[str, Any]] = None,
    ):
        """Store structured execution data for complex queries"""

        if not self.memory_interface.redis_manager:
            return

        if execution:
            structured_data = {
                "execution_id": execution.execution_id,
                "task_name": execution.task_name,
                "execution_type": execution.execution_type.value,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "end_time": (
                    execution.end_time.isoformat() if execution.end_time else None
                ),
                "duration_seconds": execution.duration_seconds,
                "agent_id": execution.agent_id,
                "swarm_id": execution.swarm_id,
                "workflow_id": execution.workflow_id,
                "parent_execution_id": execution.parent_execution_id,
                "child_execution_ids": execution.child_execution_ids,
                "input_parameters": execution.input_parameters,
                "output_results": execution.output_results,
                "error_details": execution.error_details,
                "cpu_usage_percent": execution.cpu_usage_percent,
                "memory_usage_mb": execution.memory_usage_mb,
                "api_calls_made": execution.api_calls_made,
                "tokens_consumed": execution.tokens_consumed,
                "cost_usd": execution.cost_usd,
                "user_id": execution.user_id,
                "session_id": execution.session_id,
                "tags": list(execution.tags),
                "priority": execution.priority,
                "retry_count": execution.retry_count,
                "max_retries": execution.max_retries,
            }
        else:
            structured_data = execution_dict

        key = f"execution_structured:{memory_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, structured_data, ttl=86400 * 7, namespace="execution"  # 7 days
        )

    async def _retrieve_structured_execution(
        self, execution_id: str
    ) -> Optional[dict[str, Any]]:
        """Retrieve structured execution data"""

        if not self.memory_interface.redis_manager:
            return None

        try:
            key = f"execution_structured:{execution_id}"
            data = await self.memory_interface.redis_manager.get(
                key, namespace="execution"
            )

            if data:
                import json

                return json.loads(data.decode() if isinstance(data, bytes) else data)

        except Exception as e:
            logger.warning(
                f"Failed to retrieve structured execution {execution_id}: {e}"
            )

        return None

    async def _update_execution_hierarchy(self, execution: ExecutionContext):
        """Update parent-child execution relationships"""

        if not execution.parent_execution_id:
            return

        # Update parent's child list
        parent_data = await self._retrieve_structured_execution(
            execution.parent_execution_id
        )
        if parent_data:
            child_ids = parent_data.get("child_execution_ids", [])
            if execution.execution_id not in child_ids:
                child_ids.append(execution.execution_id)
                parent_data["child_execution_ids"] = child_ids
                await self._store_structured_execution(
                    execution.parent_execution_id, None, parent_data
                )

    async def _build_execution_tree(
        self, execution_id: str, execution_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively build execution hierarchy tree"""

        tree_node = {
            "execution_id": execution_id,
            "task_name": execution_data.get("task_name", "Unknown"),
            "status": execution_data.get("status", "unknown"),
            "execution_type": execution_data.get("execution_type", "unknown"),
            "start_time": execution_data.get("start_time"),
            "duration_seconds": execution_data.get("duration_seconds"),
            "children": [],
        }

        # Get children
        child_ids = execution_data.get("child_execution_ids", [])
        for child_id in child_ids:
            child_data = await self._retrieve_structured_execution(child_id)
            if child_data:
                child_tree = await self._build_execution_tree(child_id, child_data)
                tree_node["children"].append(child_tree)

        return tree_node


# Global execution store instance
execution_store = ExecutionStore()
