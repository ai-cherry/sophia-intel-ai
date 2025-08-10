import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional
from loguru import logger
from abc import ABC, abstractmethod

class Status(str, Enum):
    READY = "READY"
    BUSY = "BUSY"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"

class BaseAgent(ABC):
    """
    Base class for all agents in the Sophia platform.
    Provides status tracking, concurrency control, and standardized execution.
    """
    
    def __init__(
        self,
        name: str,
        concurrency: int = 2,
        timeout_seconds: int = 300
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name/identifier
            concurrency: Maximum concurrent tasks (default: 2)
            timeout_seconds: Task timeout in seconds (default: 300)
        """
        self.name = name
        self.concurrency = concurrency
        self.timeout_seconds = timeout_seconds
        
        # Status tracking
        self.status = Status.READY
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tasks_timeout = 0
        self.total_duration = 0.0
        
        # Concurrency control
        self._sem = asyncio.Semaphore(concurrency)
        self._active_tasks = set()

    async def execute(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with proper error handling, timeout, and metrics.
        
        Args:
            task_id: Unique task identifier
            task_data: Task input data
            
        Returns:
            Standardized response with success/failure status
        """
        async with self._sem:
            self._active_tasks.add(task_id)
            start_time = time.time()
            
            try:
                self.status = Status.BUSY
                logger.info(f"Agent {self.name} starting task {task_id}")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._process_task_impl(task_id, task_data),
                    timeout=self.timeout_seconds
                )
                
                duration = time.time() - start_time
                self.tasks_completed += 1
                self.total_duration += duration
                
                logger.info(f"Agent {self.name} completed task {task_id} in {duration:.2f}s")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "result": result,
                    "duration": duration,
                    "agent": self.name
                }
                
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                self.tasks_timeout += 1
                self.status = Status.TIMEOUT
                
                logger.error(f"Agent {self.name} task {task_id} timed out after {duration:.2f}s")
                
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "Task timeout",
                    "error_type": "timeout",
                    "duration": duration,
                    "agent": self.name
                }
                
            except Exception as e:
                duration = time.time() - start_time
                self.tasks_failed += 1
                self.status = Status.ERROR
                
                logger.error(f"Agent {self.name} task {task_id} failed: {e}")
                
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                    "agent": self.name
                }
                
            finally:
                self._active_tasks.discard(task_id)
                # Reset status to READY if no other tasks are running
                if not self._active_tasks:
                    self.status = Status.READY

    @abstractmethod
    async def _process_task_impl(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement task-specific processing logic.
        Must return a dictionary with 'summary' and 'patch' keys for code agents.
        
        Args:
            task_id: Unique task identifier
            task_data: Task input data
            
        Returns:
            Task result dictionary
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        total_tasks = self.tasks_completed + self.tasks_failed + self.tasks_timeout
        avg_duration = self.total_duration / self.tasks_completed if self.tasks_completed > 0 else 0
        
        return {
            "name": self.name,
            "status": self.status.value,
            "concurrency": self.concurrency,
            "timeout_seconds": self.timeout_seconds,
            "active_tasks": len(self._active_tasks),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_timeout": self.tasks_timeout,
            "total_tasks": total_tasks,
            "success_rate": self.tasks_completed / total_tasks if total_tasks > 0 else 0,
            "average_duration": avg_duration,
            "total_duration": self.total_duration
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        return {
            "healthy": self.status != Status.ERROR,
            "status": self.status.value,
            "active_tasks": len(self._active_tasks),
            "stats": self.get_stats()
        }